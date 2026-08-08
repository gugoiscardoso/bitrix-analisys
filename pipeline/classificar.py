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
    # Frentes de tema único (P9 e as que saíram dele) têm o subgrupo == o próprio tema.
    # Derivado da taxonomia em vez de listado à mão: assim um bump futuro que crie ou
    # dissolva frentes desse tipo não precisa lembrar de editar aqui.
    nomes_tema = {t["nome"] for t in tax["temas"]}
    for sg in tax["subgrupos"]:
        c = votos.get(sg["nome"])
        if sg["nome"] in nomes_tema:
            sg["tema"] = sg["nome"]
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
                # SEM truncar. O corte em 300 chars silenciava metade da taxonomia: 38 dos
                # 69 subgrupos têm descrição maior, então o classificador nunca via a
                # definição completa deles — e as regras de fronteira, que ficam no fim
                # da descrição, nunca chegavam. Custo de mandar inteiro: ~2k tokens.
                L.append(f"  {d}")
        L.append("")
    L += ["## Casos especiais", ""]
    if tipo == "conversa":
        L += [f'- "{VAZIA}" — sem assunto identificável: só saudação, chat abandonado, '
              "atendimento resolvido sem descrever o problema."]
    # "Não fiscal" vale para os DOIS tipos. Antes só a conversa tinha essa saída, porque
    # o filtro de chamado era circular e por definição não trazia falso positivo. Agora
    # que o chamado passa pelo regex, ~55% do que ele traz a mais NÃO é fiscal; sem esta
    # opção esses registros seriam empurrados à força para alguma categoria fiscal.
    L += [f'- "{FALSO}" — o assunto real não é fiscal (financeiro puro, estoque, acesso); '
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


def frentes_com_quebra(tax: dict) -> dict:
    """Frentes que têm subgrupos de verdade — as únicas que precisam da etapa 2.

    Numa frente de tema único (P9 e as que saíram dela) o subgrupo É o tema, então
    perguntar de novo seria gastar tokens para receber a resposta que já se tem.
    """
    por_frente = collections.defaultdict(list)
    nomes_tema = {t["nome"] for t in tax["temas"]}
    for sg in tax["subgrupos"]:
        if not sg["nome"].startswith("Outro") and sg["nome"] not in nomes_tema:
            por_frente[sg["frente"]].append(sg)
    return {f: v for f, v in por_frente.items() if len(v) > 1}


def montar_prompt_tema(tax: dict, tipo: str) -> str:
    """ETAPA 1 — escolher o TEMA entre ~22 opções.

    Medido em 07/08/2026, no mesmo gabarito e mesma população: uma escolha entre 22
    acerta 83,6%, contra 72,7% de uma escolha única entre os 69 subgrupos (McNemar
    p=0,013). Duas decisões fáceis erram menos que uma difícil. Custa ~1,7x mais
    tokens porque o texto é lido duas vezes; a troca foi aceita de propósito.
    """
    rotulo = "chamado de suporte" if tipo == "chamado" else "conversa de chat"
    campo = "título e descrição" if tipo == "chamado" else "transcrição"
    L = [f"# Etapa 1 — assunto do atendimento ({rotulo}s, Ultracar)", "",
         f"Cada item tem `id` e `t` ({campo}). Atribua a CADA item EXATAMENTE UM assunto",
         "da lista, copiando a string EXATA. Não invente categorias.", "",
         "## Assuntos", ""]
    for t in tax["temas"]:
        if t["nome"] in (VAZIA, FALSO):
            continue
        if tipo == "chamado" and t["frente"] == "P8":
            continue                       # P8 só existe no chat
        if tipo == "conversa" and t["frente"] == "P5":
            continue                       # 'sem causa' é conceito de chamado
        L.append(f'- "{t["nome"]}"')
    L += ["", "## Casos especiais", ""]
    if tipo == "conversa":
        L.append(f'- "{VAZIA}" — sem assunto identificável: só saudação, chat abandonado, '
                 "atendimento resolvido sem descrever o problema.")
    L += [f'- "{FALSO}" — o assunto real não é fiscal (financeiro puro, estoque, acesso); '
          "o termo fiscal apareceu de passagem.", "",
          "## Regras",
          "- Vale o motivo pelo qual o cliente procurou o suporte, não termos soltos.",
          "- Se houver dois motivos, fique com o que consumiu o atendimento.",
          "- Julgue só pelo que está escrito. Não complete o que falta.", "",
          "## Saída",
          "Escreva `resp_<nome-do-lote>.json` no mesmo diretório: JSON UTF-8 sem BOM,",
          '{"<id>": "<assunto exato>", ...}, cobrindo TODOS os ids do lote.', "",
          "## Eficiência",
          "Leia o lote UMA vez e escreva a saída UMA vez. Não releia o arquivo."]
    return "\n".join(L)


def montar_prompt_subgrupo(tax: dict, frente: str) -> str:
    """ETAPA 2 — escolher o subgrupo DENTRO da frente já decidida na etapa 1."""
    titulos = {f["tag"]: f["titulo"] for f in tax["frentes"]}
    subs = frentes_com_quebra(tax)[frente]
    L = [f"# Etapa 2 — subgrupo dentro de {frente} — {titulos.get(frente, '')}", "",
         f"Todos os itens abaixo JÁ pertencem à frente {frente}; isso está decidido e não",
         "deve ser reavaliado. Atribua a CADA item EXATAMENTE UM subgrupo da lista,",
         "copiando a string EXATA.", ""]
    for sg in subs:
        L.append(f'- "{sg["nome"]}"')
        d = (sg.get("descricao") or "").strip()
        if d:
            L.append(f"  {d}")
    L += ["", f'- "{OUTRO}" — é de {frente} mas não cabe em nenhum subgrupo acima.',
          "  Use com parcimônia: é o sinal de que a taxonomia precisa crescer.", "",
          "## Regras",
          "- Classifique pela CAUSA CENTRAL, não por palavras soltas.",
          "- Se o item toca dois subgrupos, escolha o que dominou o atendimento.",
          "- Na dúvida entre um subgrupo específico e 'Outro', prefira o específico.", "",
          "## Saída",
          "Escreva `resp_<nome-do-lote>.json` no mesmo diretório: JSON UTF-8 sem BOM,",
          '{"<id>": "<subgrupo exato>", ...}, cobrindo TODOS os ids do lote.', "",
          "## Eficiência",
          "Leia o lote UMA vez e escreva a saída UMA vez. Não releia o arquivo."]
    return "\n".join(L)


# ─────────────────────── preparar ───────────────────────

def preparar(de: str, ate: str) -> int:
    tax = enriquecer_taxonomia()
    cache = ler(STORE / "classificacao.json")
    if cache.get("taxonomia_versao") != tax["versao"]:
        print(f"  AVISO: cache foi feito com a taxonomia {cache.get('taxonomia_versao')}, "
              f"atual é {tax['versao']}. Classificações antigas são mantidas.")

    FILA.mkdir(exist_ok=True)
    # limpa também os .md: um prompt de execução anterior sobrando na fila é pior que
    # inútil — o classificador pode ler o antigo e responder no formato errado.
    for velho in list(FILA.glob("*.json")) + list(FILA.glob("*.md")):
        velho.unlink()

    pendentes = {"chamado": [], "conversa": []}
    ja, reclassificar = 0, []
    for r in base_historica():
        if not r["fiscal"] or not (de <= r["data"] <= ate):
            continue
        chave = "chamados" if r["tipo"] == "chamado" else "conversas"
        anterior = cache[chave].get(str(r["id"]))
        # O hash tem que ser do MESMO texto que vai ao classificador — ou seja, do
        # truncado. Antes `preparar` hasheava o texto inteiro e `absorver` gravava o
        # hash do truncado: para todo registro acima de 1200 chars os dois nunca
        # batiam, e ele era reclassificado a cada execução, indefinidamente.
        texto = (r.get("titulo", "") + " " + r.get("texto", "")).strip()[:1200]
        if anterior:
            mudou = anterior.get("hash") and anterior["hash"] != hash_texto(texto)
            if not mudou or anterior.get("fonte") == "manual":
                ja += 1                      # curadoria humana nunca é refeita
                continue
            reclassificar.append(r["id"])    # texto mudou: reclassifica
        pendentes[r["tipo"]].append({"id": r["id"], "t": texto})

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
        (FILA / f"prompt_tema_{tipo}.md").write_text(
            montar_prompt_tema(tax, tipo), encoding="utf-8")
        for i in range(0, len(itens), TAM_LOTE):
            lotes += 1
            gravar(FILA / f"lote_tema_{tipo}_{i // TAM_LOTE + 1}.json",
                   itens[i:i + TAM_LOTE])
    gravar(FILA / "etapa.json", {"etapa": 1})
    print(f"\nETAPA 1 de 2 (assunto): {lotes} lote(s) em {FILA.relative_to(RAIZ)}")
    print("Prompts: " + ", ".join(p.name for p in sorted(FILA.glob('prompt_*.md'))))
    print("Depois de classificar, rode `absorver` — ele grava a etapa 1 e prepara a 2.")
    return 0


# ─────────────────────── absorver ───────────────────────

def absorver() -> int:
    """Absorve a etapa corrente. Na etapa 1 grava tema/frente e já prepara a etapa 2
    para as frentes que têm quebra; na etapa 2 preenche o subgrupo."""
    tax = ler(STORE / "taxonomia.json")
    cache = ler(STORE / "classificacao.json")
    hoje = date.today().isoformat()
    etapa = ler(FILA / "etapa.json").get("etapa", 1) if (FILA / "etapa.json").exists() else 1
    com_quebra = frentes_com_quebra(tax)
    tema_frente = {t["nome"]: t["frente"] for t in tax["temas"]}
    por_nome = {sg["nome"]: sg for sg in tax["subgrupos"]}

    # Na etapa 2 o lote é nomeado pela FRENTE (lote_sub_P1_1.json), não pelo tipo, então
    # deduzir o tipo do nome do arquivo manda todo chamado para cache["conversas"] e ele
    # some como "rótulo inválido". Por isso o item carrega o próprio tipo desde a etapa 1.
    textos, tipo_de = {}, {}
    for lote in FILA.glob("lote_*.json"):
        padrao = "chamado" if "_chamado_" in lote.name else "conversa"
        for it in ler(lote):
            tp = it.get("tipo", padrao)
            textos[(tp, str(it["id"]))] = it["t"]
            tipo_de[str(it["id"])] = tp

    respostas = sorted(FILA.glob("resp_lote_*.json"))
    if not respostas:
        print("Nenhuma resposta encontrada em _fila/. Rode os classificadores primeiro.")
        return 1

    novos, invalidos, absorvidos_lotes, movidos = 0, [], 0, 0
    pendentes_sub = collections.defaultdict(list)   # frente -> itens para a etapa 2

    for resp in respostas:
        padrao = "chamado" if "_chamado_" in resp.name else "conversa"
        for rid, nome in ler(resp).items():
            rid = str(rid)
            tipo = tipo_de.get(rid, padrao)
            chave = "chamados" if tipo == "chamado" else "conversas"
            if cache[chave].get(rid, {}).get("fonte") == "manual":
                continue                                  # curadoria humana é intocável

            if etapa == 1:
                if nome in ESPECIAIS:
                    tema, frente, sub = nome, None, ""
                elif nome in tema_frente:
                    tema, frente = nome, tema_frente[nome]
                    # frente de tema único: o subgrupo é o próprio tema, sem etapa 2
                    sub = "" if frente in com_quebra else nome
                else:
                    invalidos.append((rid, nome))
                    continue
                cache[chave][rid] = {
                    "tema": tema, "subgrupo": sub, "frente": frente, "fonte": "llm",
                    "hash": hash_texto(textos.get((tipo, rid), "")), "em": hoje}
                if frente in com_quebra:
                    pendentes_sub[frente].append(
                        {"id": rid, "tipo": tipo, "t": textos.get((tipo, rid), "")})
            else:
                d = cache[chave].get(rid)
                if not d:
                    invalidos.append((rid, nome))
                    continue
                if nome.startswith("Outro"):
                    d["subgrupo"] = ""          # fica sem subgrupo e conta como deriva
                elif nome in por_nome and por_nome[nome]["frente"] == d.get("frente"):
                    d["subgrupo"] = nome
                elif nome in por_nome:
                    # Subgrupo de OUTRA frente. Não é erro: as cláusulas FRONTEIRA
                    # mandam explicitamente atravessar (ex.: erro de CFOP numa nota de
                    # devolução é P7, não P1). Rejeitar deixaria o registro sem subgrupo
                    # e perderia uma correção da etapa 1 — então move a frente inteira.
                    sg = por_nome[nome]
                    d["frente"] = sg["frente"]
                    d["tema"] = sg.get("tema") or d["tema"]
                    d["subgrupo"] = nome
                    movidos += 1
                else:
                    invalidos.append((rid, nome))
                    continue
            novos += 1
        gravar(STORE / "classificacao.json", cache)   # queda no meio não perde o feito
        absorvidos_lotes += 1

    print(f"ETAPA {etapa}: {absorvidos_lotes} lote(s) absorvidos, {novos} registros")
    if movidos:
        print(f"  {movidos} mudaram de frente na etapa 2 (cláusula FRONTEIRA corrigindo a etapa 1)")
    if invalidos:
        print(f"  {len(invalidos)} rótulos inválidos IGNORADOS: "
              f"{sorted({n for _, n in invalidos})[:3]}")

    for f in list(FILA.glob("lote_*.json")) + list(FILA.glob("resp_lote_*.json")):
        f.unlink()
    for f in FILA.glob("prompt_*.md"):
        f.unlink()

    if etapa == 1 and pendentes_sub:
        lotes = 0
        for frente, itens in sorted(pendentes_sub.items()):
            (FILA / f"prompt_sub_{frente}.md").write_text(
                montar_prompt_subgrupo(tax, frente), encoding="utf-8")
            for i in range(0, len(itens), TAM_LOTE):
                lotes += 1
                gravar(FILA / f"lote_sub_{frente}_{i // TAM_LOTE + 1}.json",
                       itens[i:i + TAM_LOTE])
        gravar(FILA / "etapa.json", {"etapa": 2})
        pulou = novos - sum(len(v) for v in pendentes_sub.values())
        print(f"\nETAPA 2 de 2 (subgrupo): {lotes} lote(s) em "
              f"{len(pendentes_sub)} frente(s)")
        print(f"  {pulou} registros pularam a etapa 2 (caso especial ou frente de tema único)")
        print("  Classifique e rode `absorver` de novo para fechar.")
    elif etapa == 1:
        gravar(FILA / "etapa.json", {"etapa": 2})
        print("\nNada para a etapa 2.")
    else:
        (FILA / "etapa.json").unlink(missing_ok=True)
        print("\nClassificação completa nas duas etapas.")
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
