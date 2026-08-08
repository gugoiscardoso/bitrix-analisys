#!/usr/bin/env python
"""Camadas C (subgrupo condicional) e D (falsos negativos do filtro fiscal)."""
import json, sys, io, glob, os, math, collections
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AUD = Path(__file__).resolve().parent
RAIZ = AUD.parents[1]
gab = json.loads((AUD / "gabarito.json").read_text(encoding="utf-8"))


def carregar(padrao):
    out = {}
    for p in glob.glob(str(AUD / "respostas" / padrao)):
        try:
            for k, v in json.loads(Path(p).read_text(encoding="utf-8")).items():
                out[str(k)] = v
        except Exception as e:
            print(f"  !! {os.path.basename(p)}: {e}")
    return out


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, max(0, c - h), min(1, c + h))


def fpc(n, N):
    return math.sqrt((N - n) / (N - 1)) if N > n else 0.0


def kappa(pares):
    if not pares:
        return float("nan")
    n = len(pares)
    po = sum(1 for a, b in pares if a == b) / n
    ca, cb = collections.Counter(a for a, _ in pares), collections.Counter(b for _, b in pares)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return (po - pe) / (1 - pe) if pe != 1 else float("nan")


# ───────────────────────── camada C ─────────────────────────
print("=" * 78)
print("CAMADA C — subgrupo de conversa (CONDICIONAL a frente correta)")
print("=" * 78)
sub_gab = {k.split("|")[2]: v for k, v in gab.items() if v["camada"] == "C"}
tot_lin, por_frente = [], collections.defaultdict(list)
for frente in ["P1", "P2", "P3", "P4", "P6", "P7", "P8"]:
    a = carregar(f"av1_C{frente}_*.json")
    b = carregar(f"av2_C{frente}_*.json")
    for rid, meta in sub_gab.items():
        if meta["frente"] != frente or rid not in a or rid not in b:
            continue
        row = (rid, meta["subgrupo"], a[rid], b[rid], frente)
        tot_lin.append(row)
        por_frente[frente].append(row)

if tot_lin:
    n = len(tot_lin)
    ca = sum(1 for _, arm, ra, _, _ in tot_lin if ra == arm)
    cb = sum(1 for _, arm, _, rb, _ in tot_lin if rb == arm)
    ab = sum(1 for _, _, ra, rb, _ in tot_lin if ra == rb)
    err = [(r, arm, ra) for r, arm, ra, rb, _ in tot_lin if ra == rb and ra != arm]
    amb = [(r, ra, rb) for r, _, ra, rb, _ in tot_lin if ra != rb]
    print(f"\nn={n}  universo=4.535")
    for nome, k in (("av1 x armazenado", ca), ("av2 x armazenado", cb), ("av1 x av2", ab)):
        p, lo, hi = wilson(k, n)
        print(f"  {nome:20} {p*100:5.1f}%   IC95 ±{(hi-lo)/2*fpc(n,4535)*100:.1f}pp")
    print(f"  kappa (av1 x av2)    {kappa([(ra,rb) for _,_,ra,rb,_ in tot_lin]):5.3f}")
    p, lo, hi = wilson(len(err), n)
    print(f"  ERRO por consenso    {p*100:5.1f}%  ±{(hi-lo)/2*fpc(n,4535)*100:.1f}pp"
          f"  -> ~{round(p*4535)} de 4.535")
    print(f"  AMBIGUIDADE (av1≠av2) {len(amb)/n*100:5.1f}%")

    print(f"\n  Por frente:")
    print(f"  {'frente':7} {'n':>4} {'erro':>7} {'ambig':>7} {'kappa':>7}")
    for f in sorted(por_frente):
        L = por_frente[f]
        e = sum(1 for _, arm, ra, rb, _ in L if ra == rb and ra != arm)
        am = sum(1 for _, _, ra, rb, _ in L if ra != rb)
        print(f"  {f:7} {len(L):4} {e/len(L)*100:6.1f}% {am/len(L)*100:6.1f}% "
              f"{kappa([(ra,rb) for _,_,ra,rb,_ in L]):7.3f}")

    troca = collections.Counter((arm, ra) for _, arm, ra in err)
    print(f"\n  Subgrupos mais trocados (armazenado -> consenso):")
    for (de, para), q in troca.most_common(10):
        print(f"    {q:3}x  {(de or '(vazio)')[:40]:40} -> {para[:40]}")
else:
    print("\n  SEM RESPOSTAS")

# ───────────────────────── camada D ─────────────────────────
for cam, universo, rotulo in (("D1", 718, "chamados descartados pelo filtro (no periodo)"),
                              ("D2", 6906, "conversas descartadas pelo filtro")):
    print("\n" + "=" * 78)
    print(f"CAMADA {cam} — FALSO NEGATIVO: {rotulo}")
    print("=" * 78)
    a, b = carregar(f"av1_{cam}_*.json"), carregar(f"av2_{cam}_*.json")
    itens = {k.split("|")[2]: v for k, v in gab.items() if v["camada"] == cam}
    estratos = collections.defaultdict(list)
    for rid, meta in itens.items():
        if rid in a and rid in b:
            estratos[meta.get("estrato", "-")].append((rid, a[rid], b[rid]))
    if not estratos:
        print("  SEM RESPOSTAS")
        continue
    tot = sum(len(v) for v in estratos.values())
    print(f"\n  n={tot}")
    print(f"  {'estrato':16} {'n':>4} {'fiscal(consenso)':>17} {'duvidoso':>9} {'kappa':>7}")
    resumo = {}
    for est, L in estratos.items():
        fis = sum(1 for _, x, y in L if x == "fiscal" and y == "fiscal")
        duv = sum(1 for _, x, y in L if "duvidoso" in (x, y))
        k = kappa([(x, y) for _, x, y in L])
        p, lo, hi = wilson(fis, len(L))
        resumo[est] = (fis, len(L), p)
        print(f"  {est:16} {len(L):4} {p*100:14.1f}% "
              f"[{lo*100:.0f}-{hi*100:.0f}] {duv/len(L)*100:8.1f}% {k:7.3f}")

    # reponderacao para o universo (D1 tem oversample do estrato regex_bate)
    if cam == "D1":
        N_bate, N_naobate = 76, 642
        pb = resumo.get("regex_bate", (0, 1, 0))[2]
        pn = resumo.get("regex_nao_bate", (0, 1, 0))[2]
        est_total = pb * N_bate + pn * N_naobate
        print(f"\n  Reponderado ao universo (76 batem no regex + 642 nao batem):")
        print(f"    fiscais perdidos estimados: {est_total:.0f} de {universo}"
              f"  ({est_total/universo*100:.1f}% dos descartados)")
        print(f"    -> os 522 chamados fiscais deveriam ser ~{522+est_total:.0f}"
              f"  (+{est_total/522*100:.0f}%)")
    else:
        fis = sum(v[0] for v in resumo.values())
        p, lo, hi = wilson(fis, tot)
        print(f"\n  Extrapolado ao universo de {universo} descartadas:")
        print(f"    fiscais perdidas estimadas: {p*universo:.0f}"
              f"  [{lo*universo:.0f}-{hi*universo:.0f}]")
        print(f"    -> as 6.376 conversas fiscais deveriam ser ~{6376+p*universo:.0f}"
              f"  (+{p*universo/6376*100:.0f}%)")
