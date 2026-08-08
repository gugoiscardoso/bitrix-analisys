#!/usr/bin/env python
"""Auditoria dos registros classificados COM o prompt destruncado.

Experimento natural: a Fase 8 mediu 21,9% de erro de tema em conversa (n=201,
kappa 0,90) com o prompt que truncava a descrição dos subgrupos em 300 chars —
38 dos 69 vinham cortados. Estes registros são os primeiros classificados com a
descrição inteira. Se a taxa cair, o truncamento era causa; se não cair, o problema
está noutro lugar (candidato: o corte de 25 mensagens no digest).

Para a comparação valer, o desenho tem que ser IDÊNTICO ao da camada B:
  - mesmo prompt de tema (22 temas, sem o P5 que nunca foi oferecido a conversa)
  - dois avaliadores independentes, ordens diferentes
  - cego: o lote não leva o rótulo atual
  - mesma métrica: erro por consenso (A==B≠armazenado)
A única coisa que muda é qual prompt gerou o rótulo sob auditoria.
"""
import json, random, sys, io, collections
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AUD = Path(__file__).resolve().parent
RAIZ = AUD.parents[1]
STORE = RAIZ / "data" / "store"
SEMENTE = 20260807
N_ALVO = 120

cls = json.loads((STORE / "classificacao.json").read_text(encoding="utf-8"))
base = {}
with (STORE / "base_historica.jsonl").open(encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        base[(r["tipo"], str(r["id"]))] = r


def texto_de(tipo, rid):
    r = base[(tipo, rid)]
    if tipo == "chamado":
        return ((r.get("titulo") or "") + "\n" + (r.get("texto") or "")).strip()
    return (r.get("texto") or "").strip()

# "novos" = classificados hoje, ou seja, os que entraram pela correção do filtro.
# O campo `em` do cache é a data de absorção.
antigos = json.loads((AUD / "gabarito.json").read_text(encoding="utf-8"))
ja_auditados = {k.split("|")[2] for k in antigos}

# Duas amostras separadas, porque respondem a perguntas diferentes:
#   conversa (N) -> o prompt destruncado baixou os 21,9% da Fase 8?
#   chamado  (M) -> os 63,5% de "fiscal" que o classificador declarou nos 96 novos
#                   se sustentam? A camada D1 mediu 38,3% no estrato equivalente.
TAM = 60
plano = []
for camada, chave, tipo in (("N", "conversas", "conversa"), ("M", "chamados", "chamado")):
    novos = [(rid, d) for rid, d in cls[chave].items()
             if d.get("em", "") >= "2026-08-07" and rid not in ja_auditados
             and (tipo, rid) in base]
    if not novos:
        print(f"camada {camada}: nenhum registro novo. Rode `classificar.py absorver`.")
        continue
    alvo = N_ALVO if camada == "N" else len(novos)   # os 96 chamados vão inteiros
    rng = random.Random(SEMENTE)
    grupos = collections.defaultdict(list)
    for rid, d in novos:
        grupos[str(d.get("frente"))].append((rid, d))
    sel = []
    for g, membros in grupos.items():
        n = min(len(membros), max(3, round(alvo * len(membros) / len(novos))))
        sel += rng.sample(membros, n)
    plano.append((camada, tipo, novos, grupos, sel))

gab = {}
for camada, tipo, novos, grupos, sel in plano:
    for rid, d in sel:
        gab[f"{camada}|{tipo}|{rid}"] = {
            "camada": camada, "tipo": tipo, "id": rid, "tema": d["tema"],
            "subgrupo": d.get("subgrupo", ""), "frente": d["frente"],
            "fonte": d.get("fonte")}
(AUD / "gabarito_novos.json").write_text(
    json.dumps(gab, ensure_ascii=False, indent=1), encoding="utf-8")

for camada, tipo, novos, grupos, sel in plano:
    for av, semente in (("av1", SEMENTE + 11), ("av2", SEMENTE + 22)):
        itens = sel[:]
        random.Random(semente).shuffle(itens)
        for i in range(0, len(itens), TAM):
            bloco = [{"id": rid, "tipo": tipo, "texto": texto_de(tipo, rid)[:2500]}
                     for rid, _ in itens[i:i + TAM]]
            (AUD / "lotes" / f"{av}_{camada}_{i//TAM+1:02d}.json").write_text(
                json.dumps(bloco, ensure_ascii=False, indent=1), encoding="utf-8")
    n_lotes = (len(sel) + TAM - 1) // TAM
    print(f"camada {camada} ({tipo}): universo novo {len(novos)}, amostra {len(sel)}"
          f"  -> {n_lotes} lotes x2 = {n_lotes*2} agentes")
    for g, n in collections.Counter(str(d['frente']) for _, d in sel).most_common(6):
        print(f"    {g:6} {n:4}  (universo: {len(grupos[g])})")

print("\ncomparar contra:")
print("  camada N -> Fase 8, camada B: 21,9% de erro por consenso (n=201)")
print("  camada M -> Fase 8, camada D1: 38,3% de fiscal no estrato regex_bate (n=60)")
