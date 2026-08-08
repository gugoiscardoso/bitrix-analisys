#!/usr/bin/env python
"""Classificador de PRODUÇÃO atual x classificador EXPLORATÓRIO legado,
na mesma população e contra o mesmo gabarito.

População: os 201 registros da camada B. Gabarito: o consenso dos dois auditores
daquela camada — só onde eles concordaram entre si existe verdade de referência.

Isto é o teste pareado que o "experimento natural" anterior não era: a população é
idêntica e o gabarito é idêntico, então a única coisa que muda é qual classificador
produziu o rótulo. Responde: vale reclassificar as 1.409 conversas de 'Rejeição'?
"""
import json, sys, io, glob, math, collections
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AUD = Path(__file__).resolve().parent
STORE = AUD.parents[1] / "data" / "store"

tax = json.loads((STORE / "taxonomia.json").read_text(encoding="utf-8"))
SUB_TEMA = {s["nome"]: s.get("tema") for s in tax["subgrupos"]}
ESPECIAIS = {"Outro / não se encaixa", "Conversa vazia / sem conteúdo útil",
             "Não fiscal (falso positivo)"}
cls = json.loads((STORE / "classificacao.json").read_text(encoding="utf-8"))
gab = json.loads((AUD / "gabarito.json").read_text(encoding="utf-8"))


def carregar(padrao):
    o = {}
    for p in glob.glob(str(AUD / "respostas" / padrao)):
        for k, v in json.loads(Path(p).read_text(encoding="utf-8")).items():
            o[str(k)] = v
    return o


av1, av2 = carregar("av1_B_*.json"), carregar("av2_B_*.json")
prod = carregar("PROD_B_*.json")

def tema_de(rotulo):
    if rotulo in ESPECIAIS:
        return rotulo
    return SUB_TEMA.get(rotulo)


linhas = []
for k, m in gab.items():
    if m["camada"] != "B":
        continue
    rid = k.split("|")[2]
    a, b = av1.get(rid), av2.get(rid)
    if a is None or b is None or a != b:
        continue                       # sem consenso = sem verdade de referência
    novo_rot = prod.get(rid)
    if novo_rot is None:
        continue
    linhas.append((rid, a, m["tema"], tema_de(novo_rot), novo_rot))

n = len(linhas)
if not n:
    print("Sem dados suficientes.")
    raise SystemExit(1)

legado = sum(1 for _, cons, old, _, _ in linhas if old == cons)
novo = sum(1 for _, cons, _, new, _ in linhas if new == cons)
outro = sum(1 for _, _, _, _, rot in linhas if rot.startswith("Outro"))
naomap = sum(1 for _, _, _, new, rot in linhas if new is None)


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0, c - h), min(1, c + h)


# McNemar pareado: só discordâncias entre os dois classificadores importam
so_legado = sum(1 for _, cons, old, new, _ in linhas if old == cons and new != cons)
so_novo = sum(1 for _, cons, old, new, _ in linhas if new == cons and old != cons)
b_, c_ = so_legado, so_novo
if b_ + c_ > 0:
    chi = (abs(b_ - c_) - 1) ** 2 / (b_ + c_)
    pval = math.erfc(math.sqrt(chi / 2))
else:
    chi, pval = 0.0, 1.0

print("=" * 74)
print("PRODUÇÃO (atual) x EXPLORATÓRIO (legado) — mesma população, mesmo gabarito")
print("=" * 74)
print(f"\nregistros com consenso dos auditores e resposta nova: {n}")
p, lo, hi = wilson(legado, n)
print(f"  acerto do LEGADO   : {p*100:5.1f}%  IC95 [{lo*100:.1f} – {hi*100:.1f}]  ({legado}/{n})")
p, lo, hi = wilson(novo, n)
print(f"  acerto da PRODUÇÃO : {p*100:5.1f}%  IC95 [{lo*100:.1f} – {hi*100:.1f}]  ({novo}/{n})")
print(f"\n  produção respondeu 'Outro' (nunca casa com o gabarito): {outro}")
if naomap:
    print(f"  rótulos sem tema derivável: {naomap}")

print(f"\nTeste de McNemar (pareado):")
print(f"  só o legado acertou : {b_}")
print(f"  só a produção acertou: {c_}")
print(f"  chi2 = {chi:.2f}   p = {pval:.4f}", end="   ")
if pval < 0.05:
    print("-> diferença SIGNIFICANTE")
else:
    print("-> NÃO significante")

print("\nVeredito:")
if pval < 0.05 and c_ > b_:
    print("  A produção é melhor. Reclassificar as 1.409 de 'Rejeição' se justifica.")
elif pval < 0.05 and b_ > c_:
    print("  A produção é PIOR. NÃO reclassificar — pioraria o dado.")
else:
    print("  Empate estatístico. Reclassificar custa tokens e não compra acurácia;")
    print("  o ganho teria que vir de outra mudança (taxonomia, digest), não do classificador.")
