#!/usr/bin/env python
"""Teste da hipótese do digest: o corte de 25 mensagens causa erro de classificação?

O digest de produção guarda só as 25 primeiras mensagens não-boilerplate, cada uma
cortada em 200 chars, com teto de 2.200. 59,8% das conversas fiscais têm mais de 25
mensagens. A Fase 8 mediu isso como exposição, nunca como erro.

Desenho pareado, idêntico ao que fechou 9.4: mesma população (os 201 da camada B),
mesmo gabarito (consenso dos dois auditores), mesmo prompt de produção. A ÚNICA
coisa que muda é o insumo — digest cortado x transcrição completa.
"""
import json, sys, io, re, statistics
from pathlib import Path
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AUD = Path(__file__).resolve().parent
RAIZ = AUD.parents[1]
sys.path.insert(0, str(RAIZ / "pipeline"))
from consolidar_store import BOILER, limpar

gab = json.loads((AUD / "gabarito.json").read_text(encoding="utf-8"))
alvo = {int(k.split("|")[2]) for k, m in gab.items() if m["camada"] == "B"}
print(f"alvo: {len(alvo)} conversas da camada B")

partes = []
for arq in sorted((RAIZ / "data" / "raw").glob("conversations_export_*.xlsx")):
    df = pd.read_excel(arq, sheet_name="Messages",
                       usecols=["SessionId", "Timestamp", "TextContent"])
    partes.append(df[df["SessionId"].isin(alvo)])
    print(f"  lido {arq.name}")
msgs = pd.concat(partes, ignore_index=True).drop_duplicates()

cortado, completo, n_msgs = {}, {}, {}
for sid, g in msgs.groupby("SessionId"):
    linhas = []
    for t in g.sort_values("Timestamp")["TextContent"]:
        t = limpar(t)
        if not t or t.lower() == "nan" or BOILER.match(t):
            continue
        linhas.append(t)
    n_msgs[int(sid)] = len(linhas)
    # reprodução exata do digest de produção
    cortado[int(sid)] = "\n".join(x[:200] for x in linhas[:25])[:2200]
    # completo: sem corte de mensagem, per-mensagem generoso, teto alto
    completo[int(sid)] = "\n".join(x[:600] for x in linhas)[:8000]

ids = sorted(set(cortado) & alvo)
lc = [len(cortado[i]) for i in ids]
ll = [len(completo[i]) for i in ids]
excede = sum(1 for i in ids if n_msgs[i] > 25)
print(f"\nconversas reconstruídas: {len(ids)}")
print(f"  com mais de 25 mensagens: {excede} ({excede/len(ids)*100:.1f}%)")
print(f"  digest cortado  : mediana {int(statistics.median(lc)):5} chars, máx {max(lc)}")
print(f"  transcrição full: mediana {int(statistics.median(ll)):5} chars, máx {max(ll)}")
print(f"  ganho de conteúdo: {sum(ll)/sum(lc):.1f}x")

# checagem de sanidade: o digest reproduzido bate com o que está na base?
base = {}
with (RAIZ / "data/store/base_historica.jsonl").open(encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        if r["tipo"] == "conversa" and int(r["id"]) in alvo:
            base[int(r["id"])] = re.sub(r"\s+", " ", r["texto"] or "")
igual = sum(1 for i in ids if re.sub(r"\s+", " ", cortado[i]) == base.get(i, ""))
print(f"\n  sanidade: digest reproduzido == base_historica em {igual}/{len(ids)}")
if igual < len(ids) * 0.95:
    print("  AVISO: reprodução divergente. O teste compara insumos, então isso importa.")

itens = [{"id": str(i), "t": completo[i]} for i in ids]
TAM = 50
for n in range(0, len(itens), TAM):
    (AUD / "lotes" / f"FULL_B_{n//TAM+1:02d}.json").write_text(
        json.dumps(itens[n:n + TAM], ensure_ascii=False, indent=1), encoding="utf-8")
n_lotes = (len(itens) + TAM - 1) // TAM
chars = sum(len(x["t"]) for x in itens)
print(f"\n{n_lotes} lotes escritos | conteúdo {chars} chars (~{chars/3.5:.0f} tok)")
