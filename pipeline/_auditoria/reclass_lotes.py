#!/usr/bin/env python
"""Reclassificação dos 6.898 legados — etapa 1 (tema).

Escopo deliberadamente menor que "refazer tudo": a etapa 2 roda depois SÓ para os
registros cujo tema mudar. Quem manteve o tema mantém um subgrupo que continua válido,
e os subgrupos de P7 e P10–P13 acabaram de ser refeitos — reclassificá-los de novo
seria pagar duas vezes pela mesma coisa.

Não usa `classificar.py preparar` porque preparar só enfileira quem está FORA do cache,
e apagar as entradas para forçar a fila destruiria justamente o trabalho de subgrupo
que se quer preservar.
"""
import json, sys, io, collections
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AUD = Path(__file__).resolve().parent
RAIZ = AUD.parents[1]
STORE = RAIZ / "data" / "store"
sys.path.insert(0, str(RAIZ / "pipeline"))
from classificar import montar_prompt_tema

LOTE = 250
DEST = AUD / "reclass"
DEST.mkdir(exist_ok=True)
for f in DEST.glob("*"):
    f.unlink()

tax = json.loads((STORE / "taxonomia.json").read_text(encoding="utf-8"))
cls = json.loads((STORE / "classificacao.json").read_text(encoding="utf-8"))
base = {}
with (STORE / "base_historica.jsonl").open(encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        base[(r["tipo"], str(r["id"]))] = r

alvo = collections.defaultdict(list)
for chave, tipo in (("chamados", "chamado"), ("conversas", "conversa")):
    for rid, d in cls[chave].items():
        if d.get("em", "") >= "2026-08-07" or d.get("fonte") == "manual":
            continue                     # já é da geração nova, ou é curadoria humana
        r = base.get((tipo, rid))
        if not r:
            continue
        t = ((r.get("titulo") or "") + " " + (r.get("texto") or "")).strip()[:1200]
        alvo[tipo].append({"id": rid, "t": t})

n_lotes = 0
for tipo, itens in alvo.items():
    (DEST / f"prompt_tema_{tipo}.md").write_text(
        montar_prompt_tema(tax, tipo), encoding="utf-8")
    for i in range(0, len(itens), LOTE):
        n_lotes += 1
        (DEST / f"R_{tipo}_{i // LOTE + 1:02d}.json").write_text(
            json.dumps(itens[i:i + LOTE], ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{tipo:9}: {len(itens):5} registros -> {-(-len(itens)//LOTE)} lotes")

chars = sum(len(x["t"]) for v in alvo.values() for x in v)
print(f"\ntotal: {sum(len(v) for v in alvo.values())} registros, {n_lotes} lotes")
print(f"conteudo: {chars} chars (~{chars/3.5:.0f} tok)")
print(f"lotes em {DEST.relative_to(RAIZ)}")
