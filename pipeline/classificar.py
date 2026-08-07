# -*- coding: utf-8 -*-
"""
Classificador incremental — o coração da consistência do relatório.

Regra central: quem já está em data/store/classificacao.json com o MESMO texto não é
reclassificado — o resultado vem do cache. Entram na fila apenas os registros novos e
aqueles cujo texto mudou desde a última classificação. Entradas com fonte 'manual'
(curadoria humana) nunca são refeitas.

Uso:
    python pipeline/classificar.py preparar --de 2026-05-01 --ate 2026-08-05
        Separa o que falta classificar, escreve os lotes e o prompt em data/store/_fila/.
        O prompt é GERADO da taxonomia, então é idêntico em toda execução.

    python pipeline/classificar.py absorver
        Lê as respostas dos lotes e grava no cache, lote a lote (resiste a queda no meio).

    python pipeline/classificar.py status [--de ... --ate ...]
        Cobertura do cache e monitor de deriva.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
STORE = RAIZ / "data" / "store"
FILA = STORE / "_fila"
LIMITE_DERIVA = 10.0            # % em "Outro" acima do qual a taxonomia precisa de revisão
TAM_LOTE = 250

OUTRO = "Outro / não se encaixa"
VAZIA = "Conversa vazia / sem conteúdo útil"
FALSO = "Não fiscal (falso positivo)"
ESPECIAIS = {OUTRO, VAZIA, FALSO}

sys.stdout.reconfigure(encoding="utf-8")


def ler(p: Path):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def gravar(p: Path, obj):
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def hash_texto(t: str) -> str:
    return hashlib.sha1(re.sub(r"\s+", " ", (t or "")).strip().lower().encode()).hexdigest()[:12]


def base_historica():
    with (STORE / "base_historica.jsonl").open(encoding="utf-8") as fh:
        for linha in fh:
            yield json.loads(linha)


# ─────────────────────── taxonomia → prompt ───────────────────────

def enriquecer_taxonomia() -> dict:
    """Deriva o tema de cada subgrupo a partir do que já está classificado no cache.
    Assim o classificador só precisa escolher o subgrupo; tema e frente saem dele."""
    tax = ler(STORE / "taxonomia.json")
    cache = ler(STORE / "classificacao.json")
    votos = collections.defaultdict(collections.Counter)
    for tipo in ("chamados", "conversas"):
        for v in cache[tipo].values():
            if v.get("subgrupo"):
                votos[v["subgrupo"]][v["tema"]] += 1
    faltando = []
    for sg in tax["subgrupos"]:
        c = votos.get(sg["nome"])
        if sg["frente"] == "P9":
            sg["tema"] = sg["nome"]          # em P9 o subgrupo é o próprio tema
        elif c:
            sg["tema"] = c.most_common(1)[0][0]
        elif sg["nome"].startswith("Outro"):
            sg["tema"] = OUTRO
        else:
            sg.setdefault("tema", None)
            faltando.append(sg["nome"])
    gravar(STORE / "taxonomia.json", tax)
    if faltando:
        print(f"  aviso: {len(faltando)} subgrupos sem tema derivável (nunca usados): "
              f"{faltando[:3]}{'...' if len(faltando) > 3 else ''}")
    return tax


def montar_prompt(tax: dict, tipo: str) -> str:
    """Gerado da taxonomia — idêntico em toda execução, o que mantém a IA estável."""
    rotulo = "chamado de suporte" if tipo == "chamado" else "conversa de chat"
    campo = "título e descrição" if tipo == "chamado" else "transcrição"
    L = [f"# Classificação fiscal — {rotulo}s (Ultracar)",
         "",
         f"Cada item tem `id` e `t` ({campo}). Atribua a CADA item EXATAMENTE UM subgrupo",
         "da lista abaixo, usando a string EXATA do nome. Não invente categorias novas.",
         ""]
    por_frente = collections.defaultdict(list)
    for sg in tax["subgrupos"]:
        por_frente[sg["frente"]].append(sg)
    titulos = {f["tag"]: f["titulo"] for f in tax["frentes"]}
    for tag in sorted(por_frente):
        if tipo == "chamado" and tag == "P8":
            continue                      # P8 só existe no chat
        L.append(f"## {tag} — {titulos.get(tag, '')}")
        for sg in por_frente[tag]:
            if sg["nome"].startswith("Outro"):
                continue
            L.append(f'- "{sg["nome"]}"')
            d = (sg.get("descricao") or "").strip()
            if d:
                L.append(f"  {d[:300]}")
        L.append("")
    L += ["## Casos especiais", ""]
    if tipo == "conversa":
        L += [f'- "{VAZIA}" — sem assunto identificável: só saudação, chat abandonado, '
              "atendimento resolvido sem descrever o problema.",
              f'- "{FALSO}" — o assunto real não é fiscal (financeiro puro, estoque, acesso); '
              "o termo fiscal apareceu de passagem.", ""]
    L += [f'- "{OUTRO}" — é fiscal e tem assunto claro, mas não cabe em NENHUM subgrupo acima. '
          "Use com parcimônia: é o sinal de que a taxonomia precisa crescer.", "",
          "## Regras",
          "- Classifique pela CAUSA CENTRAL, não por palavras soltas.",
          "- Se o item toca dois subgrupos, escolha o que dominou o atendimento.",
          "- Na dúvida entre um subgrupo específico e 'Outro', prefira o específico.",
          "",
          "## Eficiência",
          "Leia o lote UMA vez e escreva a saída UMA vez. Não releia o arquivo nem imprima o conteúdo.",
          "",
          "## Saída",
          'Escreva `resp_<nome-do-lote>.json` no mesmo diretório: JSON UTF-8 sem BOM, '
          '{"<id>": "<nome exato do subgrupo>", ...}, cobrindo TODOS os ids do lote.',
          "Resposta final: apenas a contagem por subgrupo e a confirmação de escrita."]
    return "\n".join(L)


# ─────────────────────── preparar ───────────────────────

def preparar(de: str, ate: str) -> int:
    tax = enriquecer_taxonomia()
    cache = ler(STORE / "classificacao.json")
    if cache.get("taxonomia_versao") != tax["versao"]:
        print(f"  AVISO: cache foi feito com a taxonomia {cache.get('taxonomia_versao')}, "
              f"atual é {tax['versao']}. Classificações antigas são mantidas.")

    FILA.mkdir(exist_ok=True)
    for velho in FILA.glob("*.json"):
        velho.unlink()

    pendentes = {"chamado": [], "conversa": []}
    ja, reclassificar = 0, []
    for r in base_historica():
        if not r["fiscal"] or not (de <= r["data"] <= ate):
            continue
        chave = "chamados" if r["tipo"] == "chamado" else "conversas"
        anterior = cache[chave].get(str(r["id"]))
        texto = (r.get("titulo", "") + " " + r.get("texto", "")).strip()
        if anterior:
            mudou = anterior.get("hash") and anterior["hash"] != hash_texto(texto)
            if not mudou or anterior.get("fonte") == "manual":
                ja += 1                      # curadoria humana nunca é refeita
                continue
            reclassificar.append(r["id"])    # texto mudou: reclassifica
        pendentes[r["tipo"]].append({"id": r["id"], "t": texto[:1200]})

    total = sum(len(v) for v in pendentes.values())
    print(f"Janela {de} a {ate}")
    print(f"  já classificados (reusados do cache): {ja}")
    print(f"  a classificar:                        {total} "
          f"({len(pendentes['chamado'])} chamados, {len(pendentes['conversa'])} conversas)")
    if reclassificar:
        print(f"  destes, {len(reclassificar)} são RECLASSIFICAÇÕES "
              f"(texto mudou desde a última vez; ids em _fila/reclassificados.json)")
        gravar(FILA / "reclassificados.json", reclassificar)

    if not total:
        print("\nNada a classificar. O relatório sai 100% do cache.")
        return 0

    lotes = 0
    for tipo, itens in pendentes.items():
        if not itens:
            continue
        (FILA / f"prompt_{tipo}.md").write_text(montar_prompt(tax, tipo), encoding="utf-8")
        for i in range(0, len(itens), TAM_LOTE):
            lotes += 1
            nome = f"lote_{tipo}_{i // TAM_LOTE + 1}"
            gravar(FILA / f"{nome}.json", itens[i:i + TAM_LOTE])
    print(f"\n{lotes} lote(s) escritos em {FILA.relative_to(RAIZ)}")
    print("Prompts: " + ", ".join(p.name for p in sorted(FILA.glob('prompt_*.md'))))
    return 0


# ─────────────────────── absorver ───────────────────────

def absorver() -> int:
    tax = ler(STORE / "taxonomia.json")
    por_nome = {sg["nome"]: sg for sg in tax["subgrupos"]}
    cache = ler(STORE / "classificacao.json")
    hoje = date.today().isoformat()

    textos = {}
    for lote in FILA.glob("lote_*.json"):
        tipo = "chamado" if "_chamado_" in lote.name else "conversa"
        for it in ler(lote):
            textos[(tipo, str(it["id"]))] = it["t"]

    respostas = sorted(FILA.glob("resp_lote_*.json"))
    if not respostas:
        print("Nenhuma resposta encontrada em _fila/. Rode os classificadores primeiro.")
        return 1

    novos, invalidos, absorvidos_lotes = 0, [], 0
    for resp in respostas:
        tipo = "chamado" if "_chamado_" in resp.name else "conversa"
        chave = "chamados" if tipo == "chamado" else "conversas"
        for rid, nome in ler(resp).items():
            rid = str(rid)
            if cache[chave].get(rid, {}).get("fonte") == "manual":
                continue                                  # curadoria humana é intocável
            if nome in ESPECIAIS:
                tema, frente, sub = nome, None, ""
            elif nome in por_nome:
                sg = por_nome[nome]
                tema, frente, sub = sg.get("tema") or nome, sg["frente"], nome
            else:
                invalidos.append((rid, nome))
                continue
            cache[chave][rid] = {"tema": tema, "subgrupo": sub, "frente": frente,
                                 "fonte": "llm", "hash": hash_texto(textos.get((tipo, rid), "")),
                                 "em": hoje}
            novos += 1
        # grava a cada lote: uma queda no meio não perde o que já foi feito
        gravar(STORE / "classificacao.json", cache)
        absorvidos_lotes += 1

    print(f"{absorvidos_lotes} lote(s) absorvidos, {novos} registros novos no cache")
    if invalidos:
        print(f"  {len(invalidos)} rótulos fora da taxonomia foram IGNORADOS: "
              f"{sorted({n for _, n in invalidos})[:3]}")
    for f in list(FILA.glob("lote_*.json")) + list(FILA.glob("resp_lote_*.json")):
        f.unlink()
    return 0


# ─────────────────────── status ───────────────────────

def status(de: str | None, ate: str | None) -> int:
    cache = ler(STORE / "classificacao.json")
    tax = ler(STORE / "taxonomia.json")
    print(f"Taxonomia {tax['versao']} · cache gerado sob {cache.get('taxonomia_versao')}")
    print(f"Cache: {len(cache['chamados'])} chamados, {len(cache['conversas'])} conversas")

    dentro = sem_cache = descartados = em_outro = com_subgrupo = 0
    for r in base_historica():
        if not r["fiscal"]:
            continue
        if de and ate and not (de <= r["data"] <= ate):
            continue
        dentro += 1
        chave = "chamados" if r["tipo"] == "chamado" else "conversas"
        v = cache[chave].get(str(r["id"]))
        if not v:
            sem_cache += 1
        elif v["tema"] in (VAZIA, FALSO):
            descartados += 1
        elif v["tema"] == OUTRO or (not v.get("subgrupo") and v.get("frente") != "P9"):
            em_outro += 1          # tem tema mas nenhum subgrupo coube: é o sinal de deriva
        else:
            com_subgrupo += 1
    janela = f"{de} a {ate}" if de and ate else "toda a base"
    classificaveis = dentro - descartados
    print(f"\nJanela: {janela}")
    print(f"  registros fiscais:        {dentro}")
    print(f"  descartados (vazia/falso positivo): {descartados}")
    print(f"  classificáveis:           {classificaveis}")
    print(f"    com tema/subgrupo:      {com_subgrupo}")
    print(f"    sem classificação:      {sem_cache}")
    print(f"    sem subgrupo ('Outro'): {em_outro}")
    pct = em_outro / classificaveis * 100 if classificaveis else 0
    print(f"\n  deriva (com tema, sem subgrupo que encaixe): {pct:.1f}%")
    if pct > LIMITE_DERIVA:
        print(f"  ⚠ acima de {LIMITE_DERIVA}%: a taxonomia provavelmente precisa de subgrupos "
              f"novos — revise os casos em 'Outro' antes da próxima rodada.")
    fontes = collections.Counter(v["fonte"] for t in ("chamados", "conversas")
                                 for v in cache[t].values())
    print(f"\nOrigem: {dict(fontes)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("preparar"); p.add_argument("--de", required=True); p.add_argument("--ate")
    sub.add_parser("absorver")
    s = sub.add_parser("status"); s.add_argument("--de"); s.add_argument("--ate")
    a = ap.parse_args()
    hoje = date.today().isoformat()
    if a.cmd == "preparar":
        return preparar(a.de, a.ate or hoje)
    if a.cmd == "absorver":
        return absorver()
    return status(a.de, a.ate)


if __name__ == "__main__":
    raise SystemExit(main())
