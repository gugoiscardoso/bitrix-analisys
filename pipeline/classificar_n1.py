# -*- coding: utf-8 -*-
"""
Eixo módulo das conversas do robô N1 — o que torna o N1 comparável ao suporte humano.

    python pipeline/classificar_n1.py preparar
    python pipeline/classificar_n1.py absorver
    python pipeline/classificar_n1.py status

Escreve em `data/store/classificacao_n1.json` e não toca em nenhum outro cache.

## Por que só módulo, e não um tema novo

O N1 já entrega o assunto classificado por ele mesmo: `Resultado` (resolvido, lacuna de
conhecimento, encaminhado ao N2…) e um `Assunto` em texto livre. O que falta para o
relatório é o eixo que atravessa tudo: **em que parte do produto a fricção acontece**.

Criar um quinto vocabulário de tema seria o erro que a `SKILL.md` já documenta — os
quatro vocabulários existentes não se cruzam, e comparar categoria entre vocabulários
diferentes não significa nada. O módulo é o único eixo comum a V2, V3 e agora N1, e por
isso a lista aqui é a MESMA `modulos_validos` de `modulo_por_rotulo.json`, importada, não
copiada.

Pelo mesmo motivo o prompt é o `CABECA_D` de `ler_pendentes.py`, reusado inteiro: o
grupo D é exatamente este caso — "estes registros JÁ têm assunto definido; falta apenas
dizer em que parte do produto a fricção acontece". Reusar garante que N1 e humano sejam
lidos com o mesmo critério, inclusive os critérios de fronteira de
`criterios_leitura.md`. Duas cópias do prompt divergiriam na primeira edição.

## O que é "pendente"

Conversa cujo `texto` (assunto + problema + resumo) tem hash diferente do gravado, ou
que nunca foi lida. O hash é o mesmo `hash_texto` dos outros pipelines, importado — o
cálculo já quebrou duas vezes neste projeto por ter cópia divergente.

O N1 reconcilia linhas já escritas na planilha (`ReconcileReportUseCase`), então uma
conversa conhecida pode mudar de resumo e voltar para a fila. É o comportamento
desejado: o texto mudou, a leitura vale de novo.

`"fonte": "manual"` nunca é refeito, como nos outros caches.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ler_pendentes import (CABECA_D, TAM_LOTE, TETO_TEXTO, criterios, gravar,
                           hash_texto, ler, vocabularios)

RAIZ = Path(__file__).resolve().parent.parent
STORE = RAIZ / "data" / "store"
FILA = STORE / "_fila" / "n1"
ORIGEM = STORE / "n1_conversas.jsonl"
SAIDA = STORE / "classificacao_n1.json"

sys.stdout.reconfigure(encoding="utf-8")


def conversas():
    if not ORIGEM.exists():
        raise SystemExit(
            f"Não achei {ORIGEM.relative_to(RAIZ)}.\n"
            f"  Rode antes: python pipeline/coletar_n1.py")
    with ORIGEM.open(encoding="utf-8") as fh:
        for linha in fh:
            if linha.strip():
                yield json.loads(linha)


def cache() -> dict:
    return ler(SAIDA, {"conversas": {}, "atualizado_em": None})


def pendencias() -> list[dict]:
    """As conversas que precisam de leitura, com o texto já truncado."""
    ja = cache()["conversas"]
    fila = []
    for r in conversas():
        texto = (r.get("texto") or "").strip()[:TETO_TEXTO]
        if not texto:
            # Sem assunto, problema e resumo não há o que ler. São 12 conversas com
            # "⚠ Erro ao processar resumo"; o módulo delas fica vazio e a aba mostra
            # isso em vez de inventar um rótulo.
            continue
        visto = ja.get(r["id"])
        if visto and visto.get("fonte") == "manual":
            continue
        if visto and visto.get("hash") == hash_texto(texto):
            continue
        fila.append({"id": r["id"], "texto": texto})
    return fila


def cmd_preparar(a) -> int:
    restos = sorted(FILA.glob("resp_*.json")) if FILA.exists() else []
    if restos and not a.forcar:
        print(f"RECUSADO: {len(restos)} resposta(s) não absorvida(s) em "
              f"{FILA.relative_to(RAIZ)}.")
        print("Rode `absorver` antes — preparar apaga a fila. Se for lixo: --forcar")
        return 1

    fila = pendencias()
    FILA.mkdir(parents=True, exist_ok=True)
    for velho in list(FILA.glob("*.json")) + list(FILA.glob("*.md")):
        velho.unlink()

    if not fila:
        print("Nada pendente: toda conversa do N1 já tem módulo lido.")
        return 0

    mods = "\n".join(f"  - {m}" for m in vocabularios()["modulos"])
    (FILA / "prompt_N1.md").write_text(
        CABECA_D.format(modulos=mods, criterios=criterios()), encoding="utf-8")

    lotes = 0
    for i in range(0, len(fila), TAM_LOTE):
        lotes += 1
        gravar(FILA / f"lote_N1_{i // TAM_LOTE + 1:03d}.json", fila[i:i + TAM_LOTE])

    print(f"{len(fila)} conversa(s) do N1 a ler em {lotes} lote(s) de até {TAM_LOTE}.")
    print(f"Fila: {FILA.relative_to(RAIZ)}")
    print("Cada lote_N1_NNN.json é lido com o prompt_N1.md.")
    print("Grave a resposta como resp_N1_NNN.json e rode `absorver`.")
    return 0


def cmd_absorver(a) -> int:
    validos = set(vocabularios()["modulos"])
    respostas = sorted(FILA.glob("resp_*.json")) if FILA.exists() else []
    if not respostas:
        print(f"Nenhuma resp_*.json em {FILA.relative_to(RAIZ)}.")
        return 1

    dados = cache()
    textos = {}
    for r in conversas():
        textos[r["id"]] = (r.get("texto") or "").strip()[:TETO_TEXTO]

    agora = datetime.now().isoformat(timespec="seconds")
    gravados, recusados = 0, 0
    for arq in respostas:
        try:
            resp = json.loads(arq.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as e:
            print(f"  {arq.name}: JSON inválido ({e}) — arquivo inteiro recusado")
            recusados += 1
            continue

        erros, aceitos = [], {}
        for cid, v in resp.items():
            modulo = (v or {}).get("modulo") if isinstance(v, dict) else v
            if cid not in textos:
                erros.append(f"id desconhecido: {cid}")
            elif modulo not in validos:
                erros.append(f"{cid}: módulo inválido {modulo!r}")
            else:
                aceitos[cid] = modulo
        if erros and not a.parcial:
            print(f"  {arq.name}: {len(erros)} erro(s) — arquivo inteiro recusado")
            for e in erros[:5]:
                print(f"      {e}")
            print("      (use --parcial para gravar só o que é válido)")
            recusados += 1
            continue

        for cid, modulo in aceitos.items():
            dados["conversas"][cid] = {
                "modulo": modulo,
                "fonte": "leitura",
                "hash": hash_texto(textos[cid]),
                "em": agora,
            }
        gravados += len(aceitos)
        if erros:
            print(f"  {arq.name}: {len(aceitos)} gravado(s), {len(erros)} pulado(s)")
        arq.unlink()

    dados["atualizado_em"] = agora
    dados["modulos_versao"] = ler(STORE / "modulo_por_rotulo.json").get("versao")
    gravar(SAIDA, dados)
    print(f"{gravados} conversa(s) do N1 com módulo gravado"
          + (f", {recusados} arquivo(s) recusado(s)" if recusados else ""))
    print(f"  → {SAIDA.resolve()}")
    return 1 if recusados else 0


def cmd_status(a) -> int:
    import collections
    ja = cache()["conversas"]
    todas = list(conversas())
    com_texto = [r for r in todas if (r.get("texto") or "").strip()]
    fila = pendencias()
    print(f"conversas do N1:        {len(todas)}")
    print(f"  com texto para ler:   {len(com_texto)}")
    print(f"  com módulo gravado:   {len(ja)}")
    print(f"  pendentes:            {len(fila)}")
    if ja:
        cont = collections.Counter(v["modulo"] for v in ja.values())
        print("\nmódulos:")
        for m, n in cont.most_common():
            print(f"  {n:5d}  {m}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("preparar")
    p.add_argument("--forcar", action="store_true",
                   help="apaga respostas não absorvidas em vez de recusar")
    p.set_defaults(fn=cmd_preparar)
    p = sub.add_parser("absorver")
    p.add_argument("--parcial", action="store_true",
                   help="grava os registros válidos de um arquivo com erros")
    p.set_defaults(fn=cmd_absorver)
    p = sub.add_parser("status")
    p.set_defaults(fn=cmd_status)
    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
