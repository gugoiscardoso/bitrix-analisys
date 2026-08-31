#!/usr/bin/env python
"""Grava as respostas em data/store/classificacao_nao_fiscal.json.

Cache SEPARADO do fiscal de propósito. O relatório fiscal precisa ser reproduzível e
comparável entre execuções; encostar no cache dele para acomodar um escopo novo é
exatamente o tipo de mistura que a skill proíbe.
"""
import json, sys, io, glob, collections
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
STORE = AQUI.parents[1] / "data" / "store"
OUTRO = "Outro / não se encaixa"

tax = json.loads((STORE / "taxonomia_nao_fiscal.json").read_text(encoding="utf-8"))
VALIDOS = {t["nome"] for t in tax["temas"]} | {OUTRO}


def desmojibake(s):
    """Mesmo reparo do reclass_aplicar: um subagente já gravou UTF-8 relido como
    Latin-1 e 217 rótulos corretos seriam descartados. Reparar custa zero."""
    if s in VALIDOS:
        return s
    try:
        c = s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s
    return c if c in VALIDOS else s


lotes = {}
for p in glob.glob(str(AQUI / "lote_*.json")):
    for it in json.loads(Path(p).read_text(encoding="utf-8")):
        lotes[str(it["id"])] = it["t"]

cache, inval, rep = {}, [], 0
for p in sorted(glob.glob(str(AQUI / "resp_*.json"))):
    for rid, nome in json.loads(Path(p).read_text(encoding="utf-8")).items():
        limpo = desmojibake(nome)
        if limpo != nome:
            rep += 1
        if limpo in VALIDOS:
            cache[str(rid)] = {"tema": limpo, "fonte": "llm", "em": "2026-08-08"}
        else:
            inval.append(limpo)

falta = set(lotes) - set(cache)
print(f"lotes: {len(lotes)} ids | respostas válidas: {len(cache)}")
if rep:
    print(f"  {rep} rótulos reparados de mojibake")
if inval:
    print(f"  {len(inval)} inválidos: {sorted(set(inval))[:3]}")
if falta:
    print(f"  {len(falta)} SEM RESPOSTA — relance os lotes correspondentes")
(STORE / "classificacao_nao_fiscal.json").write_text(
    json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"\ngravado: {len(cache)} chamados em classificacao_nao_fiscal.json")
c = collections.Counter(v["tema"] for v in cache.values())
for k, v in c.most_common():
    print(f"  {v:4} ({v/max(1,len(cache))*100:4.1f}%)  {k[:62]}")
