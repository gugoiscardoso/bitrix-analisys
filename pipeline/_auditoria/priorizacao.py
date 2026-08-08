#!/usr/bin/env python
"""Reordenacao das frentes segundo as taxas medidas na auditoria.

Combina chamados + conversas, aplica o saldo liquido medido por consenso
em cada camada e mostra se o ranking muda. Nao inclui os falsos negativos
do filtro (camada D) porque os avaliadores julgaram so 'e fiscal ou nao',
sem atribuir frente — o destino deles e desconhecido e isso e dito no relatorio.
"""
import json, sys, io, glob, collections
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AUD = Path(__file__).resolve().parent
RAIZ = AUD.parents[1]
gab = json.loads((AUD / "gabarito.json").read_text(encoding="utf-8"))
tax = json.loads((RAIZ / "data/store/taxonomia.json").read_text(encoding="utf-8"))
cls = json.loads((RAIZ / "data/store/classificacao.json").read_text(encoding="utf-8"))
TF = {t["nome"]: t["frente"] for t in tax["temas"]}
TIT = {f["tag"]: f["titulo"] for f in tax["frentes"]}


def carregar(padrao):
    out = {}
    for p in glob.glob(str(AUD / "respostas" / padrao)):
        for k, v in json.loads(Path(p).read_text(encoding="utf-8")).items():
            out[str(k)] = v
    return out


atual = collections.Counter()
for d in cls["chamados"].values():
    atual[d["frente"]] += 1
for d in cls["conversas"].values():
    atual[d["frente"]] += 1

saldo = collections.Counter()
for cam, universo in (("A", 522), ("B", 6376)):
    a, b = carregar(f"av1_{cam}_*.json"), carregar(f"av2_{cam}_*.json")
    linhas = []
    for k, m in gab.items():
        if m["camada"] != cam:
            continue
        rid = k.split("|")[2]
        if rid not in a or rid not in b:
            continue
        if cam == "A" and m.get("fonte") == "chat":
            continue
        linhas.append((m["tema"], a[rid], b[rid]))
    n = len(linhas)
    for arm, ra, rb in linhas:
        if ra == rb and ra != arm:
            saldo[TF.get(arm)] -= universo / n
            saldo[TF.get(ra)] += universo / n

print("=" * 76)
print("REORDENACAO DAS FRENTES  (chamados + conversas, apos correcao por consenso)")
print("=" * 76)
est = {f: atual[f] + saldo.get(f, 0) for f in atual}
ord_atual = [f for f, _ in atual.most_common()]
ord_novo = sorted(est, key=lambda f: -est[f])

print(f"\n{'#':>2} {'atual':6} {'n':>6}    {'#':>2} {'estimado':8} {'n':>6}  {'var':>7}  titulo")
for i in range(len(ord_atual)):
    fa, fn = ord_atual[i], ord_novo[i]
    var = (est[fn] - atual[fn]) / atual[fn] * 100 if atual[fn] else 0
    mv = ""
    if fa != fn:
        mv = "  <-- MUDOU"
    print(f"{i+1:2} {str(fa):6} {atual[fa]:6}    {i+1:2} {str(fn):8} {est[fn]:6.0f}  {var:+6.1f}%  "
          f"{TIT.get(fn,'(sem frente)')[:38]}{mv}")

print("\nMudancas de posicao:")
for f in atual:
    pa, pn = ord_atual.index(f), ord_novo.index(f)
    if pa != pn:
        print(f"  {str(f):5} {pa+1} -> {pn+1}   ({atual[f]} -> {est[f]:.0f})"
              f"  {TIT.get(f,'(sem frente)')[:44]}")
if ord_atual == ord_novo:
    print("  nenhuma — o ranking se sustenta")
