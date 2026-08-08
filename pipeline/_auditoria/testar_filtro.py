#!/usr/bin/env python
"""Mede o filtro fiscal novo contra o atual, nos tres criterios que importam:

  1. nao pode perder nenhum dos 6.376 + 522 ja classificados (regressao)
  2. tem que recuperar os falsos negativos que a auditoria encontrou (ganho)
  3. nao pode inchar de falso positivo (custo)

Sem os tres, trocar o regex e chute.
"""
import json, re, sys, io, glob
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[2]
AUD = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "pipeline"))
from consolidar_store import FISCAL_RE as ATUAL

# SUPERCONJUNTO ESTRITO do filtro atual: o padrao antigo inteiro, mais os termos
# que a auditoria mostrou faltando. Assim nenhum registro ja classificado pode cair.
ADICOES = (
    # a forma abreviada que o chat de fato usa — maior buraco isolado
    r"\bnf\b|\bnfs\b|\bnfd\b|"
    # certificado sem exigir a palavra 'digital'
    r"certificado|"
    # obrigacao acessoria
    r"sintegra|\bsped\b|"
    # verbo conjugado + objeto (o atual so pegava infinitivo: 'emitir nota')
    r"(?:emit|transmit|cancel|inutiliz|denegad|rejeit|manifest)\w*"
    r"(?:\W+\w+){0,3}\W+(?:nota|notas|cupom)|"
    r"(?:nota|notas)(?:\W+\w+){0,3}\W+"
    r"(?:emitid|transmitid|cancelad|rejeitad|denegad|autorizad|inutilizad)\w*|"
    # naturezas de operacao que faltavam na alternancia 'nota de (...)'
    r"nota de (?:garantia|retorno|remessa|complement|entrada|sa[ií]da|"
    r"m[aã]o de obra|conserto|transfer[eê]ncia)|"
    r"\bcc-?e\b|chave de acesso|substitui[cç][aã]o trib"
)
NOVO = re.compile(ATUAL.pattern + "|" + ADICOES, re.IGNORECASE)


def texto_de(r):
    return ((r.get("titulo") or "") + " " + (r.get("texto") or "")).strip()


base = {"chamado": {}, "conversa": {}}
with (RAIZ / "data/store/base_historica.jsonl").open(encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        base[r["tipo"]][str(r["id"])] = r

cls = json.loads((RAIZ / "data/store/classificacao.json").read_text(encoding="utf-8"))
gab = json.loads((AUD / "gabarito.json").read_text(encoding="utf-8"))


def carregar(padrao):
    o = {}
    for p in glob.glob(str(AUD / "respostas" / padrao)):
        for k, v in json.loads(Path(p).read_text(encoding="utf-8")).items():
            o[str(k)] = v
    return o


print("=" * 72)
print("1. REGRESSAO — o filtro novo mantem tudo que ja esta classificado?")
print("=" * 72)
for tipo, chave in (("chamado", "chamados"), ("conversa", "conversas")):
    ids = [i for i in cls[chave] if i in base[tipo]]
    perde_a = [i for i in ids if not ATUAL.search(texto_de(base[tipo][i]))]
    perde_n = [i for i in ids if not NOVO.search(texto_de(base[tipo][i]))]
    print(f"  {tipo:9} {len(ids):5} classificados | atual perde {len(perde_a):3} | novo perde {len(perde_n):3}")
    if perde_n:
        print(f"    ids perdidos: {perde_n[:8]}")

print()
print("=" * 72)
print("2. GANHO — recupera os falsos negativos que a auditoria confirmou?")
print("=" * 72)
for cam, tipo, uni_nao in (("D1", "chamado", 718), ("D2", "conversa", 6906)):
    a, b = carregar(f"av1_{cam}_*.json"), carregar(f"av2_{cam}_*.json")
    fn = [k.split("|")[2] for k, m in gab.items() if m["camada"] == cam
          and a.get(k.split("|")[2]) == "fiscal" and b.get(k.split("|")[2]) == "fiscal"]
    nfis = [k.split("|")[2] for k, m in gab.items() if m["camada"] == cam
            and a.get(k.split("|")[2]) == "nao_fiscal" and b.get(k.split("|")[2]) == "nao_fiscal"]
    pega_a = sum(1 for i in fn if ATUAL.search(texto_de(base[tipo][i])))
    pega_n = sum(1 for i in fn if NOVO.search(texto_de(base[tipo][i])))
    fp_a = sum(1 for i in nfis if ATUAL.search(texto_de(base[tipo][i])))
    fp_n = sum(1 for i in nfis if NOVO.search(texto_de(base[tipo][i])))
    print(f"  {cam} ({tipo}):")
    print(f"    fiscais perdidos na amostra: {len(fn):3}"
          f" | atual recupera {pega_a:3} | NOVO recupera {pega_n:3}")
    print(f"    nao-fiscais na amostra:      {len(nfis):3}"
          f" | atual pega   {fp_a:3} | NOVO pega    {fp_n:3}  (falso positivo)")

print()
print("=" * 72)
print("3. CUSTO — quanto o universo cresce (registros a classificar)")
print("=" * 72)
DE, ATE = "2026-05-01", "2026-08-05"
for tipo in ("chamado", "conversa"):
    per = [r for r in base[tipo].values() if DE <= r["data"] <= ATE]
    na = sum(1 for r in per if ATUAL.search(texto_de(r)))
    nn = sum(1 for r in per if NOVO.search(texto_de(r)))
    atualmente = sum(1 for r in per if r["fiscal"])
    print(f"  {tipo:9} no periodo {len(per):6} | hoje marcado fiscal {atualmente:5}"
          f" | regex atual {na:5} | regex NOVO {nn:5}  ({nn-atualmente:+5})")
