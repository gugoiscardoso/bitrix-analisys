# -*- coding: utf-8 -*-
"""Consolida a classificação das conversas fiscais: ranking do balcão + horas por tema."""
import json, sys, io, os, collections
import pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

SCRATCH = r"C:\Users\Lucas\AppData\Local\Temp\claude\C--Dev-Qigger-Ultracar-bitrix-analisys\a9f3de17-99fb-4920-8408-48ea262b563e\scratchpad"

# ---- carrega classificações ----
cls = {}
faltando = []
for i in range(1, 17):
    f = os.path.join(SCRATCH, f"class_conv_{i}.json")
    if not os.path.exists(f):
        faltando.append(i)
        continue
    for k, v in json.load(open(f, encoding="utf-8")).items():
        cls[int(k)] = v
print(f"Classificações: {len(cls)} conversas | lotes faltando: {faltando if faltando else 'nenhum'}")

# ---- base das conversas ----
conv = pd.DataFrame(json.load(open(os.path.join(SCRATCH, "conv_fiscais.json"), encoding="utf-8")))
conv["tema"] = conv["SessionId"].map(cls)
conv = conv[conv["tema"].notna()].copy()
conv["dur"] = pd.to_numeric(conv["DurationMinutes"], errors="coerce").fillna(0)
conv["msgs"] = pd.to_numeric(conv["TotalMessages"], errors="coerce").fillna(0)
conv["cli_msgs"] = pd.to_numeric(conv["CustomerMessages"], errors="coerce").fillna(0)
conv["mes"] = conv["StartedAt"].astype(str).str[:7]

# Duração é janela da sessão (inclui ociosidade/auto-close). Usamos duração truncada
# no p90 como estimativa conservadora de tempo de atendimento.
P90 = conv["dur"].quantile(0.90)
conv["dur_cap"] = conv["dur"].clip(upper=P90)
print(f"Corte p90 de duração: {P90:.0f} min | horas brutas {conv['dur'].sum()/60:.0f} h | horas truncadas {conv['dur_cap'].sum()/60:.0f} h")

BALCAO = {
    "Dúvida de uso / orientação (how-to fiscal)",
    "Configuração assistida pelo suporte",
    "Acompanhamento de chamado já aberto",
    "Instabilidade geral / lentidão do sistema",
    "Conversa vazia / sem conteúdo útil",
    "Não fiscal (falso positivo)",
}
DESCARTE = {"Conversa vazia / sem conteúdo útil", "Não fiscal (falso positivo)"}

uteis = conv[~conv["tema"].isin(DESCARTE)].copy()
print(f"\nConversas fiscais úteis: {len(uteis)} (descartadas {len(conv)-len(uteis)} vazias/falso-positivo)")

# ---- tabela por tema ----
g = uteis.groupby("tema").agg(
    conversas=("SessionId", "count"),
    horas=("dur_cap", lambda s: round(s.sum() / 60)),
    med_min=("dur_cap", "median"),
    msgs=("msgs", "sum"),
    com_chamado=("tem_chamado", "sum"),
).reset_index()
g["sem_chamado"] = g["conversas"] - g["com_chamado"]
g["pct_balcao"] = (g["sem_chamado"] / g["conversas"] * 100).round(0)
g["h_mes"] = (g["horas"] / 3.2).round(0)   # ~3,2 meses de janela (01/05 a 14/07 no export)
g = g.sort_values("horas", ascending=False)

print("\n=== TEMAS POR HORAS DE ATENDIMENTO (truncado p90) ===")
print(f"{'tema':62s} {'conv':>5} {'horas':>6} {'h/mês':>6} {'med':>5} {'s/chamado':>10} {'%balcão':>8}")
for _, r in g.iterrows():
    print(f"{r['tema'][:60]:62s} {r['conversas']:5d} {r['horas']:6.0f} {r['h_mes']:6.0f} "
          f"{r['med_min']:5.0f} {r['sem_chamado']:10d} {r['pct_balcao']:7.0f}%")

tot_h = g["horas"].sum()
bal_h = g[g["tema"].isin(BALCAO)]["horas"].sum()
print(f"\nTotal: {g['conversas'].sum()} conversas, {tot_h:.0f} h ({tot_h/3.2:.0f} h/mês)")
print(f"Categorias de balcão puro: {bal_h:.0f} h ({bal_h/tot_h*100:.0f}% do total)")

sem_ticket = uteis[~uteis["tem_chamado"]]
print(f"Conversas sem chamado vinculado: {len(sem_ticket)} ({len(sem_ticket)/len(uteis)*100:.0f}%), "
      f"{sem_ticket['dur_cap'].sum()/60:.0f} h")

# ---- mapeamento tema -> proposta ----
MAP = {
    "Rejeição/erro de validação (schema XML, E0xxx, tags, campos, IE)": "P1",
    "Status dessincronizado sistema x prefeitura/SEFAZ": "P2",
    "Nota travada em processamento/transmissão sem retorno": "P2",
    "Numeração/duplicidade (pulos, RPS, DPS, inutilização)": "P2",
    "Cálculo/exibição de impostos errada (PIS/COFINS/ICMS/ISS/IBS/CBS/retenções)": "P3",
    "PDF/DANFE/impressão (não gera, dados fora do lugar)": "P4",
    "Particularidade municipal de NFS-e (layout, homologação, instabilidade da prefeitura)": "P6",
    "Certificado digital (cadastro, vencimento, atualização)": "P6",
}
uteis["proposta"] = uteis["tema"].map(MAP).fillna("—")
p = uteis.groupby("proposta").agg(conversas=("SessionId", "count"),
                                  horas=("dur_cap", lambda s: round(s.sum() / 60))).reset_index()
p["h_mes"] = (p["horas"] / 3.2).round(0)
print("\n=== HORAS POR PROPOSTA ===")
for _, r in p.sort_values("horas", ascending=False).iterrows():
    print(f"  {r['proposta']:4s} {r['conversas']:5d} conversas  {r['horas']:6.0f} h  {r['h_mes']:5.0f} h/mês")

# ---- série mensal ----
print("\n=== VOLUME MENSAL (conversas fiscais úteis) ===")
print(uteis.groupby("mes")["SessionId"].count().to_string())

out = {
    "por_tema": g.to_dict(orient="records"),
    "por_proposta": p.to_dict(orient="records"),
    "totais": {
        "conversas_classificadas": int(len(conv)),
        "uteis": int(len(uteis)),
        "horas_total": float(tot_h),
        "horas_mes": float(round(tot_h / 3.2)),
        "sem_chamado": int(len(sem_ticket)),
        "horas_sem_chamado": float(round(sem_ticket["dur_cap"].sum() / 60)),
        "p90_min": float(P90),
        "lotes_faltando": faltando,
    },
    "mensal": uteis.groupby("mes")["SessionId"].count().to_dict(),
}
json.dump(out, open(os.path.join(SCRATCH, "balcao_stats.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1, default=str)
print("\nSalvo balcao_stats.json")
