#!/usr/bin/env python
"""Três classificações da MESMA população contra o MESMO gabarito.

  legado           — o que produziu o dado auditado (classificador exploratório)
  produção/cortado — classificador atual, digest de produção (25 mensagens)
  produção/full    — classificador atual, transcrição completa

O par que testa a hipótese do digest é o segundo contra o terceiro: mesmo
classificador, mesmo prompt, mesma população, mesmo gabarito. Só o insumo muda.
McNemar pareado, porque as amostras não são independentes — são os mesmos registros.
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
gab = json.loads((AUD / "gabarito.json").read_text(encoding="utf-8"))


def carregar(padrao):
    o = {}
    for p in glob.glob(str(AUD / "respostas" / padrao)):
        for k, v in json.loads(Path(p).read_text(encoding="utf-8")).items():
            o[str(k)] = v
    return o


def tema_de(rot):
    return rot if rot in ESPECIAIS else SUB_TEMA.get(rot)


av1, av2 = carregar("av1_B_*.json"), carregar("av2_B_*.json")
cortado, full = carregar("PROD_B_*.json"), carregar("FULL_B_*.json")

linhas = []
for k, m in gab.items():
    if m["camada"] != "B":
        continue
    rid = k.split("|")[2]
    a, b = av1.get(rid), av2.get(rid)
    if a is None or b is None or a != b:
        continue
    if rid not in cortado or rid not in full:
        continue
    linhas.append((rid, a, m["tema"], tema_de(cortado[rid]), tema_de(full[rid])))

n = len(linhas)
print("=" * 74)
print("HIPÓTESE DO DIGEST — mesma população, mesmo gabarito, só o insumo muda")
print("=" * 74)
print(f"\nregistros com consenso dos auditores e as três respostas: {n}")
if not n:
    raise SystemExit(1)


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0, c - h), min(1, c + h)


def mcnemar(pares):
    b = sum(1 for x, y in pares if x and not y)
    c = sum(1 for x, y in pares if y and not x)
    if b + c == 0:
        return b, c, 0.0, 1.0
    chi = (abs(b - c) - 1) ** 2 / (b + c)
    return b, c, chi, math.erfc(math.sqrt(chi / 2))


acertos = {
    "legado (produziu o dado)": [old == cons for _, cons, old, _, _ in linhas],
    "produção / digest cortado": [cur == cons for _, cons, _, cur, _ in linhas],
    "produção / transcrição full": [fl == cons for _, cons, _, _, fl in linhas],
}
for nome, v in acertos.items():
    p, lo, hi = wilson(sum(v), n)
    print(f"  {nome:30} {p*100:5.1f}%  IC95 [{lo*100:.1f} – {hi*100:.1f}]  ({sum(v)}/{n})")

print(f"\nMcNemar — cortado x full (o teste da hipótese):")
b, c, chi, pv = mcnemar(list(zip(acertos["produção / digest cortado"],
                                 acertos["produção / transcrição full"])))
print(f"  só o cortado acertou: {b}   só o full acertou: {c}")
print(f"  chi2 = {chi:.2f}   p = {pv:.4f}", end="   ")
print("-> SIGNIFICANTE" if pv < 0.05 else "-> NÃO significante")

# o efeito, se existe, tem que estar concentrado em quem excedia o corte
mudou = [(r, cur, fl) for r, cons, _, cur, fl in linhas if cur != fl]
print(f"\n  registros em que a resposta MUDOU com a transcrição completa: {len(mudou)}"
      f"  ({len(mudou)/n*100:.1f}%)")
if mudou:
    mm = sum(1 for r, cons, _, cur, fl in linhas if cur != fl and fl == cons)
    pp = sum(1 for r, cons, _, cur, fl in linhas if cur != fl and cur == cons)
    print(f"    dessas, o full acertou {mm} e o cortado acertou {pp}"
          f" (o resto: ambos errados, {len(mudou)-mm-pp})")

print("\nVeredito:")
if pv < 0.05 and c > b:
    print("  A transcrição completa é melhor. Vale remover o corte de 25 mensagens.")
elif pv < 0.05 and b > c:
    print("  A transcrição completa é PIOR — mais texto virou mais ruído.")
else:
    print("  Empate. O corte de 25 mensagens NÃO é causa do erro; remover não compra")
    print("  acurácia e custaria mais tokens por registro em toda execução futura.")
