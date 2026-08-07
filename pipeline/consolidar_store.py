# -*- coding: utf-8 -*-
"""
Consolida os 45 arquivos herdados da análise exploratória em TRÊS arquivos canônicos
dentro de data/store/. É o passo que torna o relatório reproduzível.

    taxonomia.json        frentes, temas e subgrupos — congelados e versionados
    classificacao.json    id -> {tema, subgrupo, fonte, hash, em} — o cache que evita reclassificar
    base_historica.jsonl  um registro por chamado/conversa, com os campos usados nas métricas

Roda de qualquer lugar: todos os caminhos são relativos à raiz do repositório.
Reconstrói tudo a partir de data/raw/ + os arquivos de classificação legados.
"""
from __future__ import annotations
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
RAW = RAIZ / "data" / "raw"
STORE = RAIZ / "data" / "store"
VERSAO_TAXONOMIA = "2026-08-07"

sys.stdout.reconfigure(encoding="utf-8")


def ler_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def arquivos(padrao: str) -> list[Path]:
    """Todos os exports que casam, em ordem cronológica pelo nome.
    A coleta é incremental: cada execução gera um arquivo novo com o delta,
    então o store precisa MESCLAR todos — o mais recente vence por id."""
    achados = sorted(RAW.glob(padrao))
    if not achados:
        raise FileNotFoundError(f"nenhum arquivo casa com {padrao} em {RAW}")
    return achados


def hash_texto(t: str) -> str:
    norm = re.sub(r"\s+", " ", (t or "")).strip().lower()
    return hashlib.sha1(norm.encode("utf-8")).hexdigest()[:12]


# ─────────────────────────── taxonomia ───────────────────────────

FRENTES = {
    "P1": "Pré-validação da nota antes da transmissão",
    "P2": "Job de reconciliação com SEFAZ e prefeituras",
    "P3": "Pacote de conformidade tributária (IBS/CBS)",
    "P4": "Robustez de PDF/DANFE e impressão",
    "P5": "Triagem com evidência obrigatória",
    "P6": "Homologação municipal + certificado digital",
    "P7": "Fluxo guiado de devolução, garantia e remessa",
    "P8": "Autonomia do cliente (self-service)",
    "P9": "Frentes complementares",
}

TEMA_PARA_FRENTE = {
    "Rejeição/erro de validação (schema XML, E0xxx, tags, campos, IE)": "P1",
    "Status dessincronizado sistema x prefeitura/SEFAZ": "P2",
    "Nota travada em processamento/transmissão sem retorno": "P2",
    "Numeração/duplicidade (pulos, RPS, DPS, inutilização)": "P2",
    "Cálculo/exibição de impostos errada (PIS/COFINS/ICMS/ISS/IBS/CBS/retenções)": "P3",
    "PDF/DANFE/impressão (não gera, dados fora do lugar)": "P4",
    "Sem causa identificável na descrição": "P5",
    "Particularidade municipal de NFS-e (layout, homologação, instabilidade da prefeitura)": "P6",
    "Certificado digital (cadastro, vencimento, atualização)": "P6",
    "Nota de devolução/garantia/remessa/complemento": "P7",
    "Dúvida de uso / orientação (how-to fiscal)": "P8",
    "Configuração assistida pelo suporte": "P8",
    "Acompanhamento de chamado já aberto": "P8",
    "Instabilidade geral / lentidão do sistema": "P8",
    "Cadastro/config fiscal (NCM, CFOP, CST, cód. serviço, SPED, regime)": "P9",
    "Integração financeiro/estoque/OS com a nota": "P9",
    "Cancelamento/exclusão de nota": "P9",
    "Relatórios fiscais divergentes": "P9",
    "XML de compra / importação / manifestação do destinatário": "P9",
    "Envio de nota por e-mail falha": "P9",
    "NFS-e interna / API interna": "P9",
    "Conversa vazia / sem conteúdo útil": None,
    "Não fiscal (falso positivo)": None,
}

# nomes que mudaram ao longo da análise
NORM_TEMA = {
    "Certificado digital": "Certificado digital (cadastro, vencimento, atualização)",
    "Particularidade municipal de NFS-e (layout, homologação, prefeitura)":
        "Particularidade municipal de NFS-e (layout, homologação, instabilidade da prefeitura)",
}


def montar_taxonomia() -> dict:
    propostas = ler_json(STORE / "propostas.json")
    p7 = ler_json(STORE / "sub_p7.json")
    p8 = ler_json(STORE / "sub_p8.json")
    tag_de = {"prop1": "P1", "prop2": "P2", "prop3": "P3",
              "prop4": "P4", "prop5": "P5", "prop6": "P6"}

    subgrupos = []
    for pk, p in propostas.items():
        for sg in p["subgrupos"]:
            subgrupos.append({"frente": tag_de[pk], "nome": sg["nome"],
                              "descricao": sg.get("descricao", "")})
    for tag, j in (("P7", p7), ("P8", p8)):
        for sg in j["subgrupos"]:
            subgrupos.append({"frente": tag, "nome": sg["nome"],
                              "descricao": sg.get("descricao", "")})
    # P9: o subgrupo é o próprio tema
    for tema, frente in TEMA_PARA_FRENTE.items():
        if frente == "P9":
            subgrupos.append({"frente": "P9", "nome": tema,
                              "descricao": "Tema completo; em P9 o subgrupo equivale ao tema."})

    return {
        "versao": VERSAO_TAXONOMIA,
        "observacao": ("Congelada. O classificador recebe exatamente estes nomes e nunca inventa "
                       "categoria: o que não encaixa vai para 'Outro'. Alterar exige bump de versão."),
        "frentes": [{"tag": t, "titulo": v} for t, v in FRENTES.items()],
        "temas": [{"nome": t, "frente": f} for t, f in TEMA_PARA_FRENTE.items()],
        "subgrupos": subgrupos,
    }


# ─────────────────────────── conversas ───────────────────────────

BOILER = re.compile(
    r"^(conversation #|conversa #|bem[- ]vindo|nosso hor|enquiry assigned|consulta atribu|dados recebidos|"
    r"\[b\]data received|data received|new (deal|contact) created|form completed|link do formul|"
    r"informa[cç][oõ]es de contato|contact information saved|deal attached|negócio anexado|order attached|"
    r"lead attached|diga-nos como|a ultracar agradece|conversa fechada|conversation closed|"
    r".*(aceitou a conversa|picked conversation|transfered|transferiu)|obrigad|pesquisa de satisfa|"
    r"basta enviar 1|\[user=|no momento,? nossa fila|percebemos o chat|the conversation is assigned|"
    r"qualquer d[uú]vida estamos|poxa! vi que n[aã]o tive)", re.IGNORECASE)

FISCAL_RE = re.compile(
    r"nota fiscal|notas fiscais|\bnf-?e\b|\bnfc-?e\b|\bnfs-?e?\b|\bnfse\b|\bnfce\b|\bnfe\b|sefaz|"
    r"\bfiscal\b|fiscais|imposto|tribut|\bicms\b|\bcfop\b|\bncm\b|\bcst\b|csosn|\bpis\b|cofins|"
    r"\bdanfe\b|\biss\b|issqn|\bmdf-?e\b|\bct-?e\b|certificado digital|carta de corre|inutiliza|"
    r"conting[eê]ncia|simples nacional|regime tribut|emitir nota|emiss[aã]o de nota|cancelar nota|"
    r"rejei[cç]|denegad|al[ií]quota|aliquota|\bdps\b|\brps\b|prefeitura|emissor nacional|"
    r"\bxml\b|manifesta[cç]|emitir uma nota|nota de (pe[cç]a|servi[cç]o|devolu[cç])", re.IGNORECASE)


def limpar(t) -> str:
    t = re.sub(r"\[/?[A-Za-z][^\]]*\]", "", str(t or "")).strip()
    return re.sub(r"\\n", " ", t)


def montar_digests(msgs: pd.DataFrame) -> dict[int, str]:
    """Mesma lógica do conv_pipeline original — o digest precisa ser idêntico
    para que os hashes do cache continuem batendo."""
    out = {}
    for sid, g in msgs.groupby("SessionId"):
        linhas = []
        for t in g.sort_values("Timestamp")["TextContent"]:
            t = limpar(t)
            if not t or t.lower() == "nan" or BOILER.match(t):
                continue
            linhas.append(t[:200])
            if len(linhas) >= 25:
                break
        out[int(sid)] = "\n".join(linhas)[:2200]
    return out


# ─────────────────────────── base + cache ───────────────────────────

CNPJ_RE = re.compile(r"\b(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})\b")
STATUS = {"1": "nova", "2": "pendente", "3": "em andamento",
          "4": "aguard. controle", "5": "concluída", "6": "adiada", "7": "recusada"}


def extrair_cnpj(titulo: str) -> str:
    m = CNPJ_RE.search(titulo.replace(" ", ""))
    if m:
        return m.group(1)
    m = re.search(r"\[filial:\s*(\d{14})\]", titulo, re.IGNORECASE)
    return m.group(1) if m else ""


def extrair_cliente(titulo: str) -> str:
    m = re.search(r"cliente\s*:?\s*(.+?)(?:\s*[-–]\s*(?:id|cnpj)|\s*cnpj|$)", titulo, re.IGNORECASE)
    if m:
        c = m.group(1).strip(" -–:|")
        if 2 < len(c) < 90 and not CNPJ_RE.match(c):
            return c
    return ""


def main() -> int:
    STORE.mkdir(parents=True, exist_ok=True)

    # ---------- taxonomia ----------
    tax = montar_taxonomia()
    (STORE / "taxonomia.json").write_text(
        json.dumps(tax, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"taxonomia.json      {len(tax['frentes'])} frentes, "
          f"{len(tax['temas'])} temas, {len(tax['subgrupos'])} subgrupos")

    # ---------- cache de classificação ----------
    # O cache é a fonte da verdade e NUNCA é reconstruído por cima: só é semeado
    # a partir do legado na primeira vez. Reexecutar este script não pode perder
    # classificação (foi assim que o cache de conversas foi zerado uma vez).
    cache_existente = {}
    caminho_cache = STORE / "classificacao.json"
    if caminho_cache.exists():
        cache_existente = ler_json(caminho_cache)
        n_ch = len(cache_existente.get("chamados", {}))
        n_cv = len(cache_existente.get("conversas", {}))
        if n_ch or n_cv:
            print(f"cache existente     {n_ch} chamados, {n_cv} conversas — PRESERVADO")

    LEGADO = STORE / "_legado"
    def legado(nome: str) -> Path:
        return LEGADO / nome if (LEGADO / nome).exists() else STORE / nome

    tema_chamado = {k: NORM_TEMA.get(v, v)
                    for k, v in ler_json(STORE / "class_final_v2.json")["final"].items()}
    fonte_chamado = ler_json(STORE / "class_final_v2.json")["fonte"]
    sub_chamado = {}
    for p in ler_json(STORE / "propostas.json").values():
        for sg in p["subgrupos"]:
            for i in sg.get("ids", []):
                sub_chamado[i] = sg["nome"]

    tema_conversa = {}
    for i in range(1, 17):
        f = legado(f"class_conv_{i}.json")
        if f.exists():
            for k, v in ler_json(f).items():
                tema_conversa[int(k)] = NORM_TEMA.get(v, v)
    sub_conversa = {}
    for frente in ler_json(STORE / "sub_conv_final.json").values():
        for k, v in frente.items():
            if not v.startswith("Outro"):
                sub_conversa[int(k)] = v

    # ---------- chamados ----------
    por_id = {}
    fontes = arquivos("bitrix_export_*.json")
    for arq in fontes:                       # ordem cronológica: o mais novo sobrescreve
        for t in ler_json(arq)["tasks"]:
            por_id[t["task"]["id"]] = t["task"]
    tarefas = list(por_id.values())
    print(f"chamados            {len(tarefas)} mesclados de {len(fontes)} export(s): "
          + ", ".join(a.name.replace('bitrix_export_139_', '') for a in fontes))

    registros = []
    cache = {"chamados": dict(cache_existente.get("chamados", {})),
             "conversas": dict(cache_existente.get("conversas", {}))}
    for t in tarefas:
        tid = t["id"]
        titulo = t.get("title") or ""
        desc = re.sub(r"\[/?[A-Za-z][^\]]*\]", "", t.get("description") or "").strip()
        fiscal = tid in tema_chamado
        registros.append({
            "tipo": "chamado", "id": tid,
            "data": (t.get("createdDate") or "")[:10],
            "criado_em": t.get("createdDate"), "fechado_em": t.get("closedDate"),
            "inicio_dev": t.get("dateStart"), "alterado_em": t.get("changedDate"),
            "status": STATUS.get(str(t.get("status")), str(t.get("status"))),
            "canal": "Matrix (bot)" if re.search(r"\[matrix", titulo, re.I) else "Analista",
            "cliente": extrair_cliente(titulo), "cnpj": extrair_cnpj(titulo),
            "fiscal": fiscal,
            "titulo": re.sub(r"\s+", " ", titulo)[:500],
            "texto": desc[:4000],
        })
        if fiscal and tid not in cache["chamados"]:
            cache["chamados"][tid] = {
                "tema": tema_chamado[tid],
                "subgrupo": sub_chamado.get(tid, ""),
                "frente": TEMA_PARA_FRENTE.get(tema_chamado[tid]),
                "fonte": "chat" if fonte_chamado.get(tid) == "chat Open Lines" else "llm",
                "hash": hash_texto(titulo + " " + desc),
                "em": "2026-08-05",
            }

    # ---------- conversas ----------
    fontes_conv = arquivos("conversations_export_*.xlsx")
    partes_conv, partes_msg = [], []
    for arq in fontes_conv:
        partes_conv.append(pd.read_excel(arq, sheet_name="Conversations"))
        partes_msg.append(pd.read_excel(arq, sheet_name="Messages",
                                        usecols=["SessionId", "Timestamp", "TextContent"]))
    conv = (pd.concat(partes_conv, ignore_index=True)
              .drop_duplicates(subset="SessionId", keep="last"))
    msgs = pd.concat(partes_msg, ignore_index=True).drop_duplicates()
    print(f"conversas           {len(conv)} mescladas de {len(fontes_conv)} export(s)")
    digests = montar_digests(msgs)

    n_fiscal = 0
    for _, r in conv.iterrows():
        sid = int(r["SessionId"])
        dig = digests.get(sid, "")
        fiscal = bool(FISCAL_RE.search(dig))
        n_fiscal += fiscal
        registros.append({
            "tipo": "conversa", "id": sid,
            "data": str(r["StartedAt"])[:10],
            "criado_em": str(r["StartedAt"]), "fechado_em": str(r.get("EndedAt") or "")[:19] or None,
            "inicio_dev": None, "alterado_em": None,
            "status": "", "canal": r.get("Channel") or "",
            "cliente": r.get("CustomerName") or "", "cnpj": "",
            "fiscal": fiscal,
            "duracao_min": int(r.get("DurationMinutes") or 0),
            "mensagens": int(r.get("TotalMessages") or 0),
            "operador": r.get("OperatorName") or "",
            "titulo": "", "texto": re.sub(r"\s+", " ", dig)[:4000],
        })
        if sid in tema_conversa and str(sid) not in cache["conversas"]:
            tema = tema_conversa[sid]
            cache["conversas"][str(sid)] = {
                "tema": tema,
                "subgrupo": sub_conversa.get(sid, ""),
                "frente": TEMA_PARA_FRENTE.get(tema),
                "fonte": "llm",
                "hash": hash_texto(dig),
                "em": "2026-08-05",
            }

    # ---------- grava ----------
    with (STORE / "base_historica.jsonl").open("w", encoding="utf-8") as fh:
        for r in registros:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    cache["taxonomia_versao"] = VERSAO_TAXONOMIA
    cache["consolidado_em"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    (STORE / "classificacao.json").write_text(
        json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\nbase_historica.jsonl {len(registros)} registros "
          f"({sum(1 for r in registros if r['tipo']=='chamado')} chamados, "
          f"{sum(1 for r in registros if r['tipo']=='conversa')} conversas; "
          f"{sum(1 for r in registros if r['fiscal'])} fiscais)")
    print(f"classificacao.json   {len(cache['chamados'])} chamados, "
          f"{len(cache['conversas'])} conversas em cache")

    # ---------- validação ----------
    print("\nVALIDAÇÃO")
    sem_sub_ch = sum(1 for v in cache["chamados"].values() if not v["subgrupo"])
    sem_sub_cv = sum(1 for v in cache["conversas"].values() if not v["subgrupo"])
    print(f"  chamados fiscais sem subgrupo: {sem_sub_ch} (esperado 152: P7 e P9)")
    print(f"  conversas com tema mas sem subgrupo: {sem_sub_cv}")
    nomes_validos = {s["nome"] for s in tax["subgrupos"]}
    orfaos = {v["subgrupo"] for v in list(cache["chamados"].values()) + list(cache["conversas"].values())
              if v["subgrupo"] and v["subgrupo"] not in nomes_validos}
    print(f"  subgrupos fora da taxonomia: {len(orfaos)}"
          + (f" -> {sorted(orfaos)[:3]}" if orfaos else ""))
    fiscais_base = {r["id"] for r in registros if r["tipo"] == "conversa" and r["fiscal"]}
    print(f"  conversas fiscais recalculadas: {n_fiscal} "
          f"(cache tem {len(cache['conversas'])}; diferença = "
          f"{len(fiscais_base - {int(k) for k in cache['conversas']})} sem classificação)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
