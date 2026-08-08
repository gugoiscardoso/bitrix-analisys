#!/usr/bin/env python
"""Compara o erro dos registros classificados COM o prompt destruncado contra o
baseline da Fase 8, medido com o prompt truncado.

A pergunta não é "qual a taxa", é "a taxa CAIU?". Duas proporções com intervalos
que se sobrepõem não sustentam a conclusão de melhora, então aqui vai teste z de
diferença entre proporções independentes, com o IC da diferença.

Baselines da Fase 8 (mesmo desenho: cego, dois avaliadores, erro por consenso):
  conversa (camada B) : 21,9%  n=201
  chamado  (camada A) : 10,4%  n=144
"""
import json, sys, io, glob, math, collections
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AUD = Path(__file__).resolve().parent
gab = json.loads((AUD / "gabarito_novos.json").read_text(encoding="utf-8"))

BASE = {"N": ("conversa", "camada B", 0.219, 201),
        "M": ("chamado", "camada A", 0.104, 144)}


def carregar(av, cam):
    o = {}
    for p in glob.glob(str(AUD / "respostas" / f"{av}_{cam}_*.json")):
        for k, v in json.loads(Path(p).read_text(encoding="utf-8")).items():
            o[str(k)] = v
    return o


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, max(0, c - h), min(1, c + h))


def kappa(pares):
    if not pares:
        return float("nan")
    n = len(pares)
    po = sum(1 for a, b in pares if a == b) / n
    ca, cb = collections.Counter(a for a, _ in pares), collections.Counter(b for _, b in pares)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return (po - pe) / (1 - pe) if pe != 1 else float("nan")


def z_duas_proporcoes(k1, n1, k2, n2):
    """H0: p1 == p2. Retorna (diferenca, z, p_valor_bicaudal, ic95_da_diferenca)."""
    p1, p2 = k1 / n1, k2 / n2
    pool = (k1 + k2) / (n1 + n2)
    se0 = math.sqrt(pool * (1 - pool) * (1 / n1 + 1 / n2))
    z = (p1 - p2) / se0 if se0 else 0.0
    # p-valor bicaudal pela aproximação normal (erf da libm)
    pval = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    se = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    d = p1 - p2
    return d, z, pval, (d - 1.96 * se, d + 1.96 * se)


print("=" * 76)
print("EXPERIMENTO: o prompt destruncado baixou o erro?")
print("=" * 76)

for cam, (tipo, nome_base, p_base, n_base) in BASE.items():
    itens = [(k.split("|")[2], m) for k, m in gab.items() if m["camada"] == cam]
    a, b = carregar("av1", cam), carregar("av2", cam)
    linhas = [(rid, m["tema"], a[rid], b[rid]) for rid, m in itens
              if rid in a and rid in b]
    if not linhas:
        print(f"\n### Camada {cam} ({tipo}) — SEM RESPOSTAS")
        continue
    n = len(linhas)
    err = [(r, arm, ra) for r, arm, ra, rb in linhas if ra == rb and ra != arm]
    amb = sum(1 for _, _, ra, rb in linhas if ra != rb)
    k = kappa([(ra, rb) for _, _, ra, rb in linhas])
    p, lo, hi = wilson(len(err), n)

    print(f"\n### Camada {cam} — tema de {tipo}   (n={n})")
    print(f"  erro por consenso  : {p*100:5.1f}%   IC95 [{lo*100:.1f} – {hi*100:.1f}]")
    print(f"  baseline Fase 8    : {p_base*100:5.1f}%   ({nome_base}, n={n_base})")
    print(f"  ambiguidade (A≠B)  : {amb/n*100:5.1f}%")
    print(f"  kappa              : {k:5.3f}")

    d, z, pv, (dlo, dhi) = z_duas_proporcoes(len(err), n, round(p_base * n_base), n_base)
    sinal = "QUEDA" if d < 0 else "ALTA"
    print(f"\n  diferença vs baseline: {d*100:+.1f}pp  ({sinal})")
    print(f"    IC95 da diferença  : [{dlo*100:+.1f} ; {dhi*100:+.1f}] pp")
    print(f"    z = {z:.2f}   p = {pv:.3f}", end="   ")
    if pv < 0.05:
        print("-> diferença ESTATISTICAMENTE SIGNIFICANTE")
    else:
        print("-> NÃO significante: os dados não sustentam que mudou")

    if err:
        troca = collections.Counter((arm, ra) for _, arm, ra in err)
        print(f"\n  pares mais trocados:")
        for (de, para), q in troca.most_common(6):
            print(f"    {q:3}x  {de[:40]:40} -> {para[:40]}")
