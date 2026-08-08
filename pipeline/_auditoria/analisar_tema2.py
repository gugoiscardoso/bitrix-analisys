#!/usr/bin/env python
"""Complexidade da decisão: 22 assuntos x 69 subgrupos, mesma população e gabarito.

Leitura ASSIMÉTRICA, e isso é parte do desenho:
  - o gabarito é o consenso de dois auditores que usaram um prompt de tema. Um
    classificador de tema herda parte do viés desse desenho, então um resultado
    POSITIVO é ambíguo — parte do ganho pode ser viés compartilhado.
  - um resultado NULO, por outro lado, é forte: nem com essa vantagem o prompt
    simples superou o de 69 opções.
Mitigação aplicada: o prompt de tema aqui é reescrito e reordenado (semente 4242).
"""
import json, sys, io, glob, math, collections
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AUD = Path(__file__).resolve().parent
STORE = AUD.parents[1] / "data" / "store"
tax = json.loads((STORE / "taxonomia.json").read_text(encoding="utf-8"))
SUB_TEMA = {s["nome"]: s.get("tema") for s in tax["subgrupos"]}
ESP = {"Outro / não se encaixa", "Conversa vazia / sem conteúdo útil",
       "Não fiscal (falso positivo)"}
gab = json.loads((AUD / "gabarito.json").read_text(encoding="utf-8"))


def carregar(padrao):
    o = {}
    for p in glob.glob(str(AUD / "respostas" / padrao)):
        for k, v in json.loads(Path(p).read_text(encoding="utf-8")).items():
            o[str(k)] = v
    return o


av1, av2 = carregar("av1_B_*.json"), carregar("av2_B_*.json")
sub69, tema22 = carregar("PROD_B_*.json"), carregar("T2_B_*.json")
tema_de = lambda r: r if r in ESP else SUB_TEMA.get(r)

linhas = []
for k, m in gab.items():
    if m["camada"] != "B":
        continue
    rid = k.split("|")[2]
    a, b = av1.get(rid), av2.get(rid)
    if a is None or b is None or a != b or rid not in sub69 or rid not in tema22:
        continue
    linhas.append((rid, a, m["tema"], tema_de(sub69[rid]), tema22[rid]))

n = len(linhas)
print("=" * 74)
print("COMPLEXIDADE DA DECISÃO — 69 subgrupos x 22 assuntos")
print("=" * 74)
print(f"\nregistros com consenso e as duas respostas: {n}")
if not n:
    raise SystemExit(1)


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0, c - h), min(1, c + h)


acerto_legado = [old == cons for _, cons, old, _, _ in linhas]
acerto_69 = [x == cons for _, cons, _, x, _ in linhas]
acerto_22 = [y == cons for _, cons, _, _, y in linhas]
for nome, v in (("legado (2 etapas, produziu o dado)", acerto_legado),
                ("produção: 1 escolha entre 69", acerto_69),
                ("prompt simples: 1 escolha entre 22", acerto_22)):
    p, lo, hi = wilson(sum(v), n)
    print(f"  {nome:36} {p*100:5.1f}%  IC95 [{lo*100:.1f} – {hi*100:.1f}]  ({sum(v)}/{n})")

b = sum(1 for x, y in zip(acerto_69, acerto_22) if x and not y)
c = sum(1 for x, y in zip(acerto_69, acerto_22) if y and not x)
chi = (abs(b - c) - 1) ** 2 / (b + c) if b + c else 0.0
pv = math.erfc(math.sqrt(chi / 2)) if b + c else 1.0
print(f"\nMcNemar — 69 x 22:")
print(f"  só o de 69 acertou: {b}   só o de 22 acertou: {c}")
print(f"  chi2 = {chi:.2f}   p = {pv:.4f}", end="   ")
print("-> SIGNIFICANTE" if pv < 0.05 else "-> NÃO significante")

print("\nVeredito:")
if pv < 0.05 and c > b:
    print("  O prompt simples vence — MAS o resultado é ambíguo por viés compartilhado")
    print("  com o gabarito. Direção plausível; magnitude não confiável.")
    print("  Ação sugerida: voltar montar_prompt para duas etapas (tema, depois subgrupo).")
elif pv < 0.05 and b > c:
    print("  O prompt de 69 vence, apesar da vantagem que o de 22 tinha. Hipótese refutada.")
else:
    print("  Empate. Como o desenho FAVORECIA o prompt de 22, um empate é evidência")
    print("  contra a hipótese: reduzir opções não compra acurácia.")

erros22 = collections.Counter((cons, y) for _, cons, _, _, y in linhas if y != cons)
if erros22:
    print("\n  pares mais errados pelo prompt de 22 (gabarito -> resposta):")
    for (g, r), q in erros22.most_common(5):
        print(f"    {q:3}x  {str(g)[:38]:38} -> {str(r)[:38]}")
