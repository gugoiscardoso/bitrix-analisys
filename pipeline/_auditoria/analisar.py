#!/usr/bin/env python
"""Consolida as respostas dos avaliadores e mede a qualidade da classificacao.

Metricas por camada:
  - concordancia de CADA avaliador com o rotulo armazenado (proxy de acuracia)
  - concordancia ENTRE avaliadores + kappa de Cohen  (mede ambiguidade da taxonomia)
  - veredito por consenso: A==B!=armazenado  -> erro provavel do armazenado
                           A!=B              -> fronteira ambigua (culpa do desenho)
  - matriz de confusao dos pares mais trocados
  - impacto na priorizacao: reponderacao das frentes pelas taxas medidas
"""
import json, sys, io, glob, os, math, collections
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AUD = Path(__file__).resolve().parent
RAIZ = AUD.parents[1]

gab = json.loads((AUD / "gabarito.json").read_text(encoding="utf-8"))
tax = json.loads((RAIZ / "data/store/taxonomia.json").read_text(encoding="utf-8"))
TEMA_FRENTE = {t["nome"]: t["frente"] for t in tax["temas"]}
SUB_FRENTE = {s["nome"]: s["frente"] for s in tax["subgrupos"]}


def carregar(av, cam):
    out = {}
    for p in glob.glob(str(AUD / "respostas" / f"{av}_{cam}_*.json")):
        try:
            d = json.loads(Path(p).read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  !! {os.path.basename(p)}: {e}")
            continue
        for k, v in d.items():
            out[str(k)] = v
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
    """correcao de populacao finita para a meia-largura"""
    return math.sqrt((N - n) / (N - 1)) if N > n else 0.0


def kappa(pares):
    if not pares:
        return float("nan")
    n = len(pares)
    po = sum(1 for a, b in pares if a == b) / n
    ca = collections.Counter(a for a, _ in pares)
    cb = collections.Counter(b for _, b in pares)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return (po - pe) / (1 - pe) if pe != 1 else float("nan")


def analisar(cam, campo, universo, rotulo, excluir_chat=True):
    """excluir_chat: itens com fonte='chat' tiveram a causa recuperada da conversa
    cruzada por telefone/CNPJ. Os avaliadores da auditoria veem SO o texto do
    chamado, entao discordam por construcao. Contar isso como erro mediria a
    minha propria cegueira, nao a qualidade do dado."""
    a, b = carregar("av1", cam), carregar("av2", cam)
    itens = [(k.split("|")[2], v) for k, v in gab.items() if v["camada"] == cam]
    linhas, n_chat = [], 0
    for rid, meta in itens:
        arm = meta.get(campo, "")
        ra, rb = a.get(rid), b.get(rid)
        if ra is None or rb is None:
            continue
        if excluir_chat and meta.get("fonte") == "chat":
            n_chat += 1
            continue
        linhas.append((rid, arm, ra, rb, meta.get("frente")))
    if n_chat:
        print(f"\n  [{n_chat} itens fonte='chat' excluidos: causa veio do chat, "
              f"invisivel para o avaliador]")
    if not linhas:
        print(f"\n### Camada {cam} — SEM RESPOSTAS\n")
        return None
    n = len(linhas)
    ca = sum(1 for _, arm, ra, _, _ in linhas if ra == arm)
    cb = sum(1 for _, arm, _, rb, _ in linhas if rb == arm)
    ab = sum(1 for _, _, ra, rb, _ in linhas if ra == rb)
    kap = kappa([(ra, rb) for _, _, ra, rb, _ in linhas])
    consenso_erro = [(r, arm, ra) for r, arm, ra, rb, _ in linhas if ra == rb and ra != arm]
    ambiguo = [(r, arm, ra, rb) for r, arm, ra, rb, _ in linhas if ra != rb]
    ok = [(r, arm) for r, arm, ra, rb, _ in linhas if ra == rb == arm]

    print(f"\n### Camada {cam} — {rotulo}  (n={n}, universo={universo})")
    for nome, k in (("avaliador 1 x armazenado", ca), ("avaliador 2 x armazenado", cb),
                    ("avaliador 1 x avaliador 2", ab)):
        p, lo, hi = wilson(k, n)
        m = (hi - lo) / 2 * fpc(n, universo)
        print(f"  {nome:26} {p*100:5.1f}%   IC95 ±{m*100:.1f}pp (com FPC)")
    print(f"  kappa de Cohen (av1 x av2) {kap:5.3f}")
    p, lo, hi = wilson(len(consenso_erro), n)
    m = (hi - lo) / 2 * fpc(n, universo)
    print(f"  ERRO por consenso (A==B≠armazenado) {p*100:5.1f}%  ±{m*100:.1f}pp"
          f"   -> ~{round(p*universo)} registros no universo")
    p2, _, _ = wilson(len(ambiguo), n)
    print(f"  AMBIGUIDADE (A≠B)                   {p2*100:5.1f}%"
          f"   -> fronteira mal definida, nao erro de execucao")
    print(f"  concordancia tripla (A==B==armazenado) {len(ok)/n*100:5.1f}%")

    # pares mais trocados (so onde os dois avaliadores concordam contra o armazenado)
    troca = collections.Counter((arm, ra) for _, arm, ra in consenso_erro)
    if troca:
        print(f"\n  Pares mais trocados (armazenado -> consenso dos avaliadores):")
        for (de, para), q in troca.most_common(8):
            print(f"    {q:3}x  {de[:44]:44} -> {para[:44]}")
    # ambiguidade: pares em que os avaliadores divergem entre si
    amb = collections.Counter(tuple(sorted((ra, rb))) for _, _, ra, rb in ambiguo)
    if amb:
        print(f"\n  Fronteiras ambiguas (av1 x av2 discordam entre si):")
        for (x, y), q in amb.most_common(8):
            print(f"    {q:3}x  {x[:42]:42} <-> {y[:42]}")
    return {"cam": cam, "n": n, "linhas": linhas, "universo": universo,
            "erro": len(consenso_erro) / n, "amb": len(ambiguo) / n, "kappa": kap}


def impacto_frente(res, mapa, universo_por_frente, titulo):
    """Reponderacao: para cada frente, quanto entra e quanto sai segundo o consenso."""
    if not res:
        return
    print(f"\n### Impacto na priorizacao — {titulo}")
    n = res["n"]
    fluxo = collections.Counter()
    base_amostra = collections.Counter()
    for _, arm, ra, rb, _ in res["linhas"]:
        fa = mapa.get(arm)
        base_amostra[fa] += 1
        if ra == rb and ra != arm:
            fluxo[(fa, mapa.get(ra))] += 1
    saldo = collections.Counter()
    for (de, para), q in fluxo.items():
        saldo[de] -= q
        saldo[para] += q
    print(f"  {'frente':8} {'atual':>8} {'saldo%':>8} {'estimado':>9}  {'variacao':>9}")
    for f in sorted(universo_por_frente, key=lambda f: -universo_por_frente[f]):
        na = base_amostra.get(f, 0)
        if na == 0 and saldo.get(f, 0) == 0:
            continue
        taxa = saldo.get(f, 0) / n
        atual = universo_por_frente[f]
        est = atual + round(taxa * sum(universo_por_frente.values()))
        var = (est - atual) / atual * 100 if atual else 0
        print(f"  {str(f):8} {atual:8} {taxa*100:+7.1f}% {est:9} {var:+8.1f}%")


if __name__ == "__main__":
    cls = json.loads((RAIZ / "data/store/classificacao.json").read_text(encoding="utf-8"))
    uni_ch = collections.Counter(d["frente"] for d in cls["chamados"].values())
    uni_cv = collections.Counter(d["frente"] for d in cls["conversas"].values())

    print("=" * 78)
    print("AUDITORIA DE CLASSIFICACAO — resultados")
    print("=" * 78)
    rA = analisar("A", "tema", 522, "tema de chamado")
    rB = analisar("B", "tema", 6376, "tema de conversa")
    rC = analisar("C", "subgrupo", 4535, "subgrupo de conversa")
    impacto_frente(rA, TEMA_FRENTE, uni_ch, "chamados (522)")
    impacto_frente(rB, TEMA_FRENTE, uni_cv, "conversas (6.376)")
