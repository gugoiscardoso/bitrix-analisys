#!/usr/bin/env python
"""Migração da dissolução de P9 (bump de taxonomia 2026-08-07b).

P9 não era uma frente: eram 7 temas sem relação somados num balde. Os 4 maiores
(93% do volume) viram frentes próprias; a cauda segue em P9.

É REMAPEAMENTO, não reclassificação: o tema de cada registro não muda, só a frente
a que ele pertence. Zero chamada de IA. Entradas com fonte='manual' são migradas
também — a curadoria humana foi sobre o TEMA, e o tema é preservado.

Idempotente: rodar duas vezes não muda nada além da primeira.
"""
import json, sys, io, collections, shutil
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[2]
STORE = RAIZ / "data" / "store"
sys.path.insert(0, str(RAIZ / "pipeline"))
from consolidar_store import TEMA_PARA_FRENTE, FRENTES

caminho = STORE / "classificacao.json"
cache = json.loads(caminho.read_text(encoding="utf-8"))

antes = collections.Counter()
depois = collections.Counter()
movidos = collections.Counter()
for chave in ("chamados", "conversas"):
    for rid, d in cache[chave].items():
        antes[d.get("frente")] += 1
        nova = TEMA_PARA_FRENTE.get(d["tema"], d.get("frente"))
        if nova != d.get("frente"):
            movidos[(d.get("frente"), nova, d["tema"])] += 1
            d["frente"] = nova
        depois[d["frente"]] += 1

if not movidos:
    print("Nada a migrar — o cache já está na taxonomia nova.")
    raise SystemExit(0)

shutil.copy(caminho, caminho.with_suffix(".json.pre_p9"))
cache["taxonomia_versao"] = "2026-08-07b"
caminho.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")

print("MIGRAÇÃO P9 → P10..P13\n")
print(f"{'de':5} -> {'para':5} {'n':>6}  tema")
for (de, para, tema), n in sorted(movidos.items(), key=lambda x: -x[1]):
    print(f"{str(de):5} -> {str(para):5} {n:6}  {tema[:58]}")

print(f"\n{'frente':6} {'antes':>7} {'depois':>7}  título")
for f in sorted(set(antes) | set(depois), key=lambda f: (f is None, str(f))):
    if antes[f] == depois[f] and f not in ("P9",):
        continue
    print(f"{str(f):6} {antes[f]:7} {depois[f]:7}  {FRENTES.get(f, '(sem frente)')[:50]}")

total = sum(antes.values())
assert total == sum(depois.values()), "perdeu registro na migração"
print(f"\ntotal preservado: {total} registros")
print(f"backup: {caminho.with_suffix('.json.pre_p9').name}")
