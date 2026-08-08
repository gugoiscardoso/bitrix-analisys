#!/usr/bin/env python
"""Auditoria de amostra a cada execução do relatório.

Por que existe: em 07/08/2026 uma auditoria cega mediu 21,9% de erro de tema em
conversa e 10,4% em chamado — números que ninguém tinha porque ninguém media. O
buraco não foi a classificação ter erro; foi não haver como saber que tinha.

Desenho, herdado daquela auditoria:
  - amostra aleatória estratificada por frente, semente derivada da janela
    (mesmo período -> mesma amostra, então o número é comparável entre execuções)
  - CEGA: o lote não leva o rótulo atual, para não ancorar
  - DOIS avaliadores independentes, com os lotes embaralhados por sementes diferentes
  - a métrica é o erro por CONSENSO (os dois concordam entre si e contra o rótulo).
    Onde os dois discordam ENTRE SI, o problema é a fronteira da taxonomia, não a
    execução — por isso ambiguidade é reportada em separado, e não somada ao erro.

Uso:
    python pipeline/auditar.py preparar --de <de> --ate <ate> [--n 50]
    python pipeline/auditar.py medir    --de <de> --ate <ate>
"""
import argparse, collections, json, math, random, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
STORE = RAIZ / "data" / "store"
AUD = STORE / "_auditoria"
sys.path.insert(0, str(RAIZ / "pipeline"))
from classificar import montar_prompt_tema, ler, gravar

sys.stdout.reconfigure(encoding="utf-8")

LIMITE_ERRO = 30.0        # % acima do qual o relatório não deve virar decisão sem revisão
LIMITE_KAPPA = 0.75       # abaixo disso a taxonomia está ambígua demais para confiar


def base_no_periodo(de, ate):
    cls = ler(STORE / "classificacao.json")
    regs = []
    with (STORE / "base_historica.jsonl").open(encoding="utf-8") as fh:
        for linha in fh:
            r = json.loads(linha)
            if not r["fiscal"] or not (de <= r["data"] <= ate):
                continue
            chave = "chamados" if r["tipo"] == "chamado" else "conversas"
            c = cls[chave].get(str(r["id"]))
            if not c:
                continue
            texto = ((r.get("titulo") or "") + " " + (r.get("texto") or "")).strip()
            regs.append({"id": str(r["id"]), "tipo": r["tipo"], "texto": texto[:2500],
                         "tema": c["tema"], "frente": c.get("frente"),
                         "fonte": c.get("fonte")})
    return regs


def preparar(de, ate, n):
    AUD.mkdir(parents=True, exist_ok=True)
    for f in AUD.glob("*"):
        f.unlink()
    regs = base_no_periodo(de, ate)
    if len(regs) < n:
        print(f"Só há {len(regs)} registros classificados na janela; auditando todos.")
        n = len(regs)

    # fonte 'chat' fica de fora: a causa daqueles veio da conversa cruzada, que o
    # avaliador não vê. Contar como erro mediria a cegueira do auditor, não o dado.
    regs = [r for r in regs if r.get("fonte") != "chat"]
    rng = random.Random(hash((de, ate)) % (2**31))
    grupos = collections.defaultdict(list)
    for r in regs:
        grupos[(r["tipo"], str(r["frente"]))].append(r)
    sel = []
    for g, membros in grupos.items():
        k = min(len(membros), max(1, round(n * len(membros) / len(regs))))
        sel += rng.sample(membros, k)

    tax = ler(STORE / "taxonomia.json")
    gravar(AUD / "gabarito.json", {f'{r["tipo"]}|{r["id"]}': r for r in sel})
    for tipo in ("chamado", "conversa"):
        itens = [r for r in sel if r["tipo"] == tipo]
        if not itens:
            continue
        (AUD / f"prompt_{tipo}.md").write_text(
            montar_prompt_tema(tax, tipo), encoding="utf-8")
        for av, semente in (("av1", 11), ("av2", 22)):
            emb = itens[:]
            random.Random(semente).shuffle(emb)
            gravar(AUD / f"lote_{av}_{tipo}.json",
                   [{"id": r["id"], "t": r["texto"]} for r in emb])

    print(f"amostra: {len(sel)} de {len(regs)} classificados na janela")
    for (tp, fr), m in sorted(collections.Counter(
            (r["tipo"], str(r["frente"])) for r in sel).items()):
        print(f"  {tp:9} {fr:6} {m:3}")
    print(f"\nlotes cegos em {AUD.relative_to(RAIZ)} — dois avaliadores, ordens diferentes")
    print("Classifique cada lote_<av>_<tipo>.json com prompt_<tipo>.md e grave")
    print("resp_<mesmo nome>.json. Depois rode `medir`.")
    return 0


def kappa(pares):
    if not pares:
        return float("nan")
    n = len(pares)
    po = sum(1 for a, b in pares if a == b) / n
    ca, cb = collections.Counter(a for a, _ in pares), collections.Counter(b for _, b in pares)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return (po - pe) / (1 - pe) if pe != 1 else float("nan")


def wilson(k, n, z=1.96):
    if not n:
        return 0.0, 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0, c - h), min(1, c + h)


def medir(de, ate):
    gab = ler(AUD / "gabarito.json")
    resp = {}
    for av in ("av1", "av2"):
        resp[av] = {}
        for p in AUD.glob(f"resp_lote_{av}_*.json"):
            for k, v in ler(p).items():
                resp[av][str(k)] = v
    if not resp["av1"] or not resp["av2"]:
        print("Faltam respostas dos dois avaliadores em", AUD)
        return 1

    linhas = []
    for chave, m in gab.items():
        rid = m["id"]
        a, b = resp["av1"].get(rid), resp["av2"].get(rid)
        if a and b:
            linhas.append((m["tipo"], m["tema"], a, b))
    if not linhas:
        print("Nenhum id cruzou entre gabarito e respostas.")
        return 1

    print(f"AUDITORIA DE AMOSTRA — janela {de} a {ate}\n")
    alerta = []
    for tipo in ("chamado", "conversa", "TOTAL"):
        L = linhas if tipo == "TOTAL" else [x for x in linhas if x[0] == tipo]
        if not L:
            continue
        n = len(L)
        err = sum(1 for _, arm, a, b in L if a == b and a != arm)
        amb = sum(1 for _, _, a, b in L if a != b)
        k = kappa([(a, b) for _, _, a, b in L])
        p, lo, hi = wilson(err, n)
        print(f"  {tipo:9} n={n:4}  erro {p*100:5.1f}% [{lo*100:.0f}–{hi*100:.0f}]"
              f"   ambiguidade {amb/n*100:5.1f}%   kappa {k:5.3f}")
        if tipo == "TOTAL":
            if p * 100 > LIMITE_ERRO:
                alerta.append(f"erro {p*100:.1f}% acima do limite de {LIMITE_ERRO}%")
            if k == k and k < LIMITE_KAPPA:
                alerta.append(f"kappa {k:.3f} abaixo de {LIMITE_KAPPA} — taxonomia ambígua")

    troca = collections.Counter((arm, a) for _, arm, a, b in linhas if a == b and a != arm)
    if troca:
        print("\n  pares mais trocados (armazenado -> consenso):")
        for (d, p_), q in troca.most_common(5):
            print(f"    {q:3}x  {str(d)[:38]:38} -> {str(p_)[:38]}")

    if alerta:
        print("\n  ATENÇÃO: " + "; ".join(alerta))
        print("  O relatório desta janela não deve virar decisão de roadmap sem revisão.")
    else:
        print("\n  Dentro dos limites. O relatório sustenta leitura por bloco de frentes.")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for nome in ("preparar", "medir"):
        s = sub.add_parser(nome)
        s.add_argument("--de", required=True)
        s.add_argument("--ate", required=True)
        if nome == "preparar":
            s.add_argument("--n", type=int, default=50)
    a = ap.parse_args()
    return preparar(a.de, a.ate, a.n) if a.cmd == "preparar" else medir(a.de, a.ate)


if __name__ == "__main__":
    raise SystemExit(main())
