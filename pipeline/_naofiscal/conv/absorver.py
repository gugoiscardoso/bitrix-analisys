#!/usr/bin/env python
"""Grava as respostas em data/store/classificacao_nao_fiscal_conv.json.

Terceiro cache do projeto, e cada um existe por um motivo:
  classificacao.json                    fiscal (chamado + conversa), taxonomia congelada
  classificacao_nao_fiscal.json         chamados não-fiscais
  classificacao_nao_fiscal_conv.json    conversas não-fiscais  <- este

Conversa e chamado não compartilham taxonomia porque 59% do volume de chat cai em temas
que a de chamado não tem — conversa sem assunto, cobrança de prazo, pedido de
treinamento, acesso bloqueado por mensalidade. Ninguém abre ticket para isso.
"""
import json, sys, io, glob, collections
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
STORE = AQUI.parents[2] / "data" / "store"
OUTRO = "Outro / não se encaixa"

tax = json.loads((STORE / "taxonomia_nao_fiscal_conv.json").read_text(encoding="utf-8"))
VALIDOS = {t["nome"] for t in tax["temas"]} | {OUTRO}


def desmojibake(s):
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
        lotes[str(it["id"])] = 1

cache, inval, rep = {}, [], 0
for p in sorted(glob.glob(str(AQUI / "resp_*.json"))):
    try:
        d = json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception as e:
        print(f"  !! {Path(p).name}: {e.__class__.__name__}")
        continue
    for rid, nome in d.items():
        limpo = desmojibake(nome)
        if limpo != nome:
            rep += 1
        if limpo in VALIDOS:
            cache[str(rid)] = {"tema": limpo, "fonte": "llm", "em": "2026-08-08"}
        else:
            inval.append(limpo)

falta = sorted(set(lotes) - set(cache))
print(f"lotes: {len(lotes)} ids | respostas válidas: {len(cache)}")
if rep:
    print(f"  {rep} rótulos reparados de mojibake")
if inval:
    print(f"  {len(inval)} inválidos: {sorted(set(inval))[:3]}")
if falta:
    resp = {p.split('resp_')[1][:2] for p in glob.glob(str(AQUI / 'resp_*.json'))}
    todos = {p.split('lote_')[1][:2] for p in glob.glob(str(AQUI / 'lote_*.json'))}
    print(f"  {len(falta)} sem resposta — lotes faltando: {sorted(todos - resp)}")
(STORE / "classificacao_nao_fiscal_conv.json").write_text(
    json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"\ngravado: {len(cache)} conversas")
c = collections.Counter(v["tema"] for v in cache.values())
for k, v in c.most_common():
    print(f"  {v:5} ({v/max(1,len(cache))*100:4.1f}%)  {k[:64]}")
