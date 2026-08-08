#!/usr/bin/env python
"""Recalcula o hash de todo o cache pela regra única.

O hash existia em três versões incompatíveis: consolidar_store gravava o do texto
cru completo, absorver o do texto truncado em 1200, e preparar comparava com o do
texto completo. Qualquer registro acima de 1200 chars caía numa dessas frestas e era
reclassificado a cada execução — IA paga de novo, para sempre, sem nada mudar.

Isto NÃO altera classificação: só regrava a impressão digital do texto que já foi
classificado, usando exatamente o cálculo de classificar.preparar.
"""
import json, sys, io, shutil
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[2]
STORE = RAIZ / "data" / "store"
sys.path.insert(0, str(RAIZ / "pipeline"))
from classificar import hash_texto

base = {}
with (STORE / "base_historica.jsonl").open(encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        base[(r["tipo"], str(r["id"]))] = r

caminho = STORE / "classificacao.json"
cache = json.loads(caminho.read_text(encoding="utf-8"))

mudados, iguais, sem_base = 0, 0, 0
for chave, tipo in (("chamados", "chamado"), ("conversas", "conversa")):
    for rid, d in cache[chave].items():
        r = base.get((tipo, rid))
        if not r:
            sem_base += 1
            continue
        # cópia exata do cálculo de preparar
        texto = ((r.get("titulo") or "") + " " + (r.get("texto") or "")).strip()[:1200]
        novo = hash_texto(texto)
        if d.get("hash") == novo:
            iguais += 1
        else:
            d["hash"] = novo
            mudados += 1

print(f"hashes já corretos : {iguais}")
print(f"hashes corrigidos  : {mudados}")
print(f"sem registro na base: {sem_base}")

if mudados:
    shutil.copy(caminho, caminho.with_suffix(".json.pre_hash"))
    caminho.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"gravado (backup em {caminho.with_suffix('.json.pre_hash').name})")
