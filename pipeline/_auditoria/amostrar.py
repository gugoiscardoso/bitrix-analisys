#!/usr/bin/env python
"""Sorteia as amostras da auditoria de classificacao.

Amostragem aleatoria estratificada, semente fixa (reprodutivel).
Escreve os lotes CEGOS (sem o rotulo atual) em _auditoria/lotes/
e o gabarito (com o rotulo atual) em _auditoria/gabarito.json.

Camadas:
  A  tema de chamado          (universo 522)
  B  tema de conversa         (universo 6.376)
  C  subgrupo de conversa     (universo 4.535 com subgrupo atribuido)
  D1 falso negativo chamado   (universo 718 nao-fiscais no periodo)
  D2 falso negativo conversa  (universo 6.906 descartadas pelo filtro)
"""
import json, random, sys, io
from pathlib import Path
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[2]
STORE = RAIZ / "data" / "store"
OUT = Path(__file__).resolve().parent
(OUT / "lotes").mkdir(parents=True, exist_ok=True)

DE, ATE = "2026-05-01", "2026-08-05"
SEMENTE = 20260807

cls = json.loads((STORE / "classificacao.json").read_text(encoding="utf-8"))
base = {}
with (STORE / "base_historica.jsonl").open(encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        base[(r["tipo"], str(r["id"]))] = r


def texto_de(tipo, rid):
    r = base.get((tipo, str(rid)))
    if not r:
        return ""
    if tipo == "chamado":
        return ((r.get("titulo") or "") + "\n" + (r.get("texto") or "")).strip()
    return (r.get("texto") or "").strip()


def estratificar(itens, chave, n, rng):
    """Alocacao proporcional com minimo de 5 por estrato (ou tudo, se menor)."""
    grupos = defaultdict(list)
    for it in itens:
        grupos[chave(it)].append(it)
    total = len(itens)
    aloc, sel = {}, []
    for g, membros in grupos.items():
        aloc[g] = min(len(membros), max(5, round(n * len(membros) / total)))
    # ajusta para bater o n alvo
    while sum(aloc.values()) > n:
        g = max(aloc, key=lambda g: (aloc[g] / len(grupos[g]), aloc[g]))
        if aloc[g] <= 5:
            break
        aloc[g] -= 1
    while sum(aloc.values()) < n:
        g = min(aloc, key=lambda g: (aloc[g] / len(grupos[g]), aloc[g]))
        if aloc[g] >= len(grupos[g]):
            break
        aloc[g] += 1
    for g, membros in grupos.items():
        sel += rng.sample(membros, aloc[g])
    return sel


rng = random.Random(SEMENTE)
gabarito, lotes = {}, {}

# ---------- A: tema de chamado ----------
A = [{"camada": "A", "tipo": "chamado", "id": k, "tema": v["tema"],
      "subgrupo": v.get("subgrupo", ""), "frente": v["frente"], "fonte": v.get("fonte")}
     for k, v in cls["chamados"].items()]
selA = estratificar(A, lambda it: it["frente"], 150, rng)

# ---------- B: tema de conversa ----------
B = [{"camada": "B", "tipo": "conversa", "id": k, "tema": v["tema"],
      "subgrupo": v.get("subgrupo", ""), "frente": v["frente"], "fonte": v.get("fonte")}
     for k, v in cls["conversas"].items()]
selB = estratificar(B, lambda it: str(it["frente"]), 200, rng)

# ---------- C: subgrupo de conversa ----------
C = [dict(it, camada="C") for it in B
     if it["subgrupo"] and not str(it["subgrupo"]).startswith("Outro")]
selC = estratificar(C, lambda it: str(it["frente"]), 150, rng)

# ---------- D1: falso negativo em chamado ----------
import re
sys.path.insert(0, str(RAIZ / "pipeline"))
from consolidar_store import FISCAL_RE

nao_fiscal_ch = [r for (tp, rid), r in base.items()
                 if tp == "chamado" and not r["fiscal"] and DE <= r["data"] <= ATE]
bate = [r for r in nao_fiscal_ch if FISCAL_RE.search((r["titulo"] or "") + " " + (r["texto"] or ""))]
nao_bate = [r for r in nao_fiscal_ch if r not in bate]
# oversample deliberado do estrato que bate no regex (onde o falso negativo se concentra)
selD1 = ([{"camada": "D1", "tipo": "chamado", "id": str(r["id"]), "estrato": "regex_bate"}
          for r in rng.sample(bate, min(60, len(bate)))] +
         [{"camada": "D1", "tipo": "chamado", "id": str(r["id"]), "estrato": "regex_nao_bate"}
          for r in rng.sample(nao_bate, 90)])

# ---------- D2: falso negativo em conversa ----------
nao_fiscal_cv = [r for (tp, rid), r in base.items()
                 if tp == "conversa" and not r["fiscal"] and DE <= r["data"] <= ATE
                 and len((r.get("texto") or "").strip()) >= 40]
selD2 = [{"camada": "D2", "tipo": "conversa", "id": str(r["id"]), "estrato": "descartada"}
         for r in rng.sample(nao_fiscal_cv, 150)]

todos = selA + selB + selC + selD1 + selD2
for it in todos:
    it["texto"] = texto_de(it["tipo"], it["id"])
    gabarito[f'{it["camada"]}|{it["tipo"]}|{it["id"]}'] = {
        k: v for k, v in it.items() if k != "texto"}

(OUT / "gabarito.json").write_text(
    json.dumps(gabarito, ensure_ascii=False, indent=1), encoding="utf-8")

# ---------- escreve os lotes cegos, embaralhados ----------
def escrever(nome, itens, tam, ordem_semente):
    r2 = random.Random(ordem_semente)
    itens = itens[:]
    r2.shuffle(itens)
    n = 0
    for i in range(0, len(itens), tam):
        bloco = itens[i:i + tam]
        payload = [{"id": it["id"], "tipo": it["tipo"], "texto": (it["texto"] or "")[:2500]}
                   for it in bloco]
        p = OUT / "lotes" / f"{nome}_{i//tam+1:02d}.json"
        p.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
        n += 1
    return n


plano = [("A", selA, 50), ("B", selB, 50), ("C", selC, 50), ("D1", selD1, 50), ("D2", selD2, 50)]
print(f"semente {SEMENTE}  |  universo: 522 chamados / 6376 conversas")
print()
for nome, sel, tam in plano:
    # avaliador 1 e avaliador 2 recebem ordens diferentes -> lotes nao correlacionados
    n1 = escrever(f"av1_{nome}", sel, tam, SEMENTE + 1)
    n2 = escrever(f"av2_{nome}", sel, tam, SEMENTE + 2)
    print(f"camada {nome:2}  n={len(sel):4}  -> {n1} lotes x2 avaliadores")
print()
print(f"total de itens amostrados : {len(todos)}")
print(f"total de julgamentos (x2) : {len(todos)*2}")
print(f"gabarito                  : {OUT/'gabarito.json'}")
