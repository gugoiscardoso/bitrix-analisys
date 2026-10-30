# -*- coding: utf-8 -*-
"""
Fila de leitura do relatório único: assunto e módulo do que ainda falta.

    python pipeline/ler_pendentes.py preparar --de 2026-01-01 --ate 2026-10-30
    python pipeline/ler_pendentes.py absorver            # todas as respostas da fila
    python pipeline/ler_pendentes.py status

Escreve em `data/store/leitura_completa.json` e NÃO toca nos caches existentes
(`classificacao.json`, os dois não-fiscais, `classificacao_v3.json`). Eles sustentam as
séries históricas de outros relatórios; um bug aqui não pode contaminá-las. O gerador
lê este arquivo com prioridade para módulo e como complemento para tema.

Quatro tipos de lote, cada um com seu vocabulário — misturar listas num prompt só é o
jeito mais rápido de receber rótulo de uma lista aplicado a registro de outra:

    A  conversa não-fiscal sem classificação   -> tema (12 opções) + módulo
    B  chamado  não-fiscal sem classificação   -> tema (11 opções) + módulo
    C  registro fiscal sem classificação       -> tema fiscal (23) + módulo
    D  registro já classificado                -> só módulo

O grupo D existe porque o tema desses registros abrange vários módulos POR DEFINIÇÃO —
"não sabe executar a rotina na OS, no orçamento, no estoque ou no cadastro" nomeia
quatro. Derivar um seria inventar; por isso são relidos, só para o módulo.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import sys
from datetime import date, datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
STORE = RAIZ / "data" / "store"
FILA = STORE / "_fila" / "leitura"
SAIDA = STORE / "leitura_completa.json"
TAM_LOTE = 250
TETO_TEXTO = 1200

sys.stdout.reconfigure(encoding="utf-8")


def ler(p: Path, vazio=None):
    if not p.exists():
        return vazio if vazio is not None else {}
    return json.loads(p.read_text(encoding="utf-8-sig"))


def gravar(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def hash_texto(t: str) -> str:
    import re
    return hashlib.sha1(re.sub(r"\s+", " ", (t or "")).strip().lower()
                        .encode()).hexdigest()[:12]


def base():
    with (STORE / "base_historica.jsonl").open(encoding="utf-8") as fh:
        for linha in fh:
            yield json.loads(linha)


def vocabularios() -> dict:
    mapa = ler(STORE / "modulo_por_rotulo.json")
    return {
        "modulos": mapa["modulos_validos"],
        "conversa": [t["nome"] for t in ler(STORE / "taxonomia_nao_fiscal_conv.json")["temas"]],
        "chamado": [t["nome"] for t in ler(STORE / "taxonomia_nao_fiscal.json")["temas"]],
        "fiscal": [t["nome"] for t in ler(STORE / "taxonomia.json")["temas"]],
    }


# ─────────────────────── o que falta ───────────────────────

def pendencias(de: str, ate: str):
    """(grupo, registro) para tudo que precisa de leitura na janela.

    Já classificado = aparece em qualquer um dos caches existentes. Esse registro só
    precisa de módulo, nunca de tema: reescrever o tema dele mudaria a série histórica
    que outros relatórios publicam.
    """
    feito = ler(SAIDA, {"chamados": {}, "conversas": {}})
    fis = ler(STORE / "classificacao.json")
    v3 = ler(STORE / "classificacao_v3.json")
    nf = {"chamado": ler(STORE / "classificacao_nao_fiscal.json"),
          "conversa": ler(STORE / "classificacao_nao_fiscal_conv.json")}
    mapa = ler(STORE / "modulo_por_rotulo.json")
    derivaveis = (set(mapa["colchete_do_titulo"]) | set(mapa["tema_chamado"])
                  | set(mapa["tema_conversa"]) | set(mapa["tema_sem_assunto"]))

    out = collections.defaultdict(list)
    for r in base():
        if not (de <= r["data"] <= ate):
            continue
        chv = "chamados" if r["tipo"] == "chamado" else "conversas"
        idt = str(r["id"])
        texto = (r.get("titulo", "") + " " + r.get("texto", "")).strip()[:TETO_TEXTO]
        h = hash_texto(texto)
        ja = feito[chv].get(idt)
        if ja and ja.get("hash") == h:
            continue

        classificado = (idt in fis.get(chv, {}) or idt in v3.get(chv, {})
                        or idt in nf[r["tipo"]])
        if classificado:
            # Só precisa de módulo — e só se nenhum rótulo já resolver.
            tema = (fis[chv].get(idt, {}).get("tema")
                    or nf[r["tipo"]].get(idt, {}).get("tema") or "")
            if r.get("versao") == "V3" or tema in derivaveis or r.get("fiscal"):
                # V3 já tem módulo lido; tema derivável e fiscal confirmado saem do mapa.
                # O fiscal lido como falso positivo NÃO cai aqui: o tema dele não é
                # derivável, então segue para a fila.
                if not (r.get("fiscal") and tema == "Não fiscal (falso positivo)"):
                    continue
            out["D"].append({"id": r["id"], "tipo": r["tipo"], "t": texto, "h": h})
            continue

        grupo = "C" if r.get("fiscal") else ("A" if r["tipo"] == "conversa" else "B")
        out[grupo].append({"id": r["id"], "tipo": r["tipo"], "t": texto, "h": h})
    return out


# ─────────────────────── prompts ───────────────────────

CABECA = """Você está classificando registros do suporte da Ultracar, uma empresa de
software para oficinas mecânicas. Cada registro é um chamado ou uma conversa de
atendimento.

Responda APENAS com um objeto JSON, sem texto antes ou depois, no formato:

{{"<id>": {{"tema": "<valor exato da lista TEMA>", "modulo": "<valor exato da lista MÓDULO>"}}}}

Regras que não podem ser quebradas:
- Use SOMENTE valores exatos das listas abaixo, copiados caractere a caractere.
- Responda para TODOS os ids recebidos, nenhum a mais.
- Na dúvida entre dois temas, escolha o que descreve o que o CLIENTE queria, não o que
  o atendente fez.
{extra}
LISTA TEMA (escolha um):
{temas}

LISTA MÓDULO — onde no produto a fricção acontece (escolha um):
{modulos}

Orientação de módulo:
- Cadastros cobre cliente, veículo, peça e serviço — inclusive "cadastro de cliente".
- Transversal é para o que não é de módulo nenhum: cobrança de prazo, sistema fora do
  ar, pedido de treinamento.
- Fiscal é nota, imposto, SPED, prefeitura, certificado digital.
- Conversa sem assunto identificável: escolha o tema próprio dela e, no módulo,
  responda o que lhe parecer mais próximo — o módulo dessas é corrigido depois, por
  regra, e não depende da sua escolha.

REGISTROS:
"""

CABECA_D = """Você está classificando registros do suporte da Ultracar, uma empresa de
software para oficinas mecânicas. Estes registros JÁ têm assunto definido; falta apenas
dizer EM QUE PARTE DO PRODUTO a fricção acontece.

Responda APENAS com um objeto JSON, sem texto antes ou depois, no formato:

{{"<id>": {{"modulo": "<valor exato da lista MÓDULO>"}}}}

Regras:
- Use SOMENTE valores exatos da lista, copiados caractere a caractere.
- Responda para TODOS os ids recebidos, nenhum a mais.

LISTA MÓDULO (escolha um):
{modulos}

Orientação:
- Cadastros cobre cliente, veículo, peça e serviço.
- Transversal é para o que não é de módulo nenhum: cobrança de prazo, sistema fora do
  ar, pedido de treinamento, conversa sem assunto.
- Fiscal é nota, imposto, SPED, prefeitura, certificado digital.
- Muitos destes registros falam de mais de um módulo. Escolha aquele em que o problema
  ACONTECE, não os que são citados de passagem.

REGISTROS:
"""

EXTRA = {
    "A": "- Conversa só com saudação, ou abandonada, é \"Conversa sem assunto "
         "identificável (saudação, chat abandonado ou resolvido fora do chat)\".\n",
    "B": "- Pedido de coisa que o sistema não tem é \"Pedido de campo, filtro ou regra "
         "configurável que o sistema não oferece\".\n",
    "C": "- Estes registros foram marcados como fiscais por palavra-chave. Se o assunto "
         "NÃO for fiscal, use \"Não fiscal (falso positivo)\".\n",
}

LISTA_TEMA = {"A": "conversa", "B": "chamado", "C": "fiscal"}


def montar_prompt(grupo: str, voc: dict) -> str:
    mods = "\n".join(f"  - {m}" for m in voc["modulos"])
    if grupo == "D":
        return CABECA_D.format(modulos=mods)
    temas = "\n".join(f"  - {t}" for t in voc[LISTA_TEMA[grupo]])
    return CABECA.format(extra=EXTRA[grupo], temas=temas, modulos=mods)


# ─────────────────────── comandos ───────────────────────

NOMES = {"A": "conversa não-fiscal (tema + módulo)",
         "B": "chamado não-fiscal (tema + módulo)",
         "C": "fiscal (tema + módulo)",
         "D": "já classificado (só módulo)"}


def cmd_preparar(a) -> int:
    restos = sorted(FILA.glob("resp_*.json")) if FILA.exists() else []
    if restos and not a.forcar:
        print(f"RECUSADO: {len(restos)} resposta(s) não absorvida(s) em "
              f"{FILA.relative_to(RAIZ)}.")
        print("Rode `absorver` antes — preparar apaga a fila. Se for lixo: --forcar")
        return 1

    voc = vocabularios()
    grupos = pendencias(a.de, a.ate)
    FILA.mkdir(parents=True, exist_ok=True)
    for velho in list(FILA.glob("*.json")) + list(FILA.glob("*.md")):
        velho.unlink()

    total, lotes = 0, 0
    for g in ("A", "B", "C", "D"):
        itens = grupos.get(g) or []
        if not itens:
            continue
        total += len(itens)
        (FILA / f"prompt_{g}.md").write_text(montar_prompt(g, voc), encoding="utf-8")
        for i in range(0, len(itens), TAM_LOTE):
            lotes += 1
            gravar(FILA / f"lote_{g}_{i // TAM_LOTE + 1:03d}.json", itens[i:i + TAM_LOTE])
        print(f"  {g}  {len(itens):>6}  {NOMES[g]}")

    print(f"\n{total} registros a ler em {lotes} lote(s) de até {TAM_LOTE}.")
    print(f"Fila: {FILA.relative_to(RAIZ)}")
    print("Cada lote_X_NNN.json é lido com o prompt_X.md do mesmo grupo.")
    print("Grave a resposta como resp_X_NNN.json e rode `absorver`.")
    return 0 if total else 0


def cmd_absorver(a) -> int:
    voc = vocabularios()
    validos_mod = set(voc["modulos"])
    validos_tema = {g: set(voc[LISTA_TEMA[g]]) for g in ("A", "B", "C")}
    feito = ler(SAIDA, {"chamados": {}, "conversas": {}})
    hoje = date.today().isoformat()
    # Conversa vazia recebe "(sem assunto)", nunca um módulo de produto. A regra já
    # vale no caminho derivado (modulo_por_rotulo.json) e precisa valer aqui, senão o
    # mesmo tipo de registro cai em baldes diferentes conforme tenha sido derivado ou
    # lido. Aplicada em código e não no prompt: é determinística, e pedir ao leitor que
    # a respeite seria confiar numa instrução quando existe uma regra.
    vazios = {x for x in ler(STORE / "modulo_por_rotulo.json")["tema_sem_assunto"]}
    n_forcado = 0

    respostas = sorted(FILA.glob("resp_*.json"))
    if not respostas:
        print(f"Nenhuma resposta em {FILA.relative_to(RAIZ)}.")
        return 1

    n_ok, n_erro, erros = 0, 0, []
    for arq in respostas:
        grupo = arq.stem.split("_")[1]
        lote = ler(FILA / f"lote_{grupo}_{arq.stem.split('_')[2]}.json", [])
        por_id = {str(i["id"]): i for i in lote}
        try:
            resp = ler(arq)
        except json.JSONDecodeError as e:
            erros.append(f"{arq.name}: JSON inválido ({e})")
            n_erro += len(por_id)
            continue

        faltando = set(por_id) - set(map(str, resp))
        sobrando = set(map(str, resp)) - set(por_id)
        if faltando or sobrando:
            erros.append(f"{arq.name}: {len(faltando)} sem resposta, "
                         f"{len(sobrando)} id estranho ao lote")
        for rid, v in resp.items():
            item = por_id.get(str(rid))
            if not item:
                n_erro += 1
                continue
            mod = (v or {}).get("modulo", "")
            if mod not in validos_mod:
                erros.append(f"{arq.name}/{rid}: módulo fora da lista: {mod!r}")
                n_erro += 1
                continue
            reg = {"modulo": mod, "fonte": "leitura", "hash": item["h"], "em": hoje}
            if grupo != "D":
                tema = (v or {}).get("tema", "")
                if tema not in validos_tema[grupo]:
                    erros.append(f"{arq.name}/{rid}: tema fora da lista: {tema!r}")
                    n_erro += 1
                    continue
                reg["tema"] = tema
                if tema in vazios:
                    reg["modulo"] = "(sem assunto)"
                    n_forcado += 1
            chv = "chamados" if item["tipo"] == "chamado" else "conversas"
            feito[chv][str(rid)] = reg
            n_ok += 1

    if erros:
        print(f"PROBLEMAS ({len(erros)}), os 10 primeiros:")
        for e in erros[:10]:
            print("   ", e)
        print()
    if n_erro and not a.parcial:
        print(f"RECUSADO: {n_erro} registro(s) com problema. Nada foi gravado.")
        print("Corrija as respostas, ou use --parcial para gravar só o que está válido.")
        return 1

    feito["atualizado_em"] = datetime.now().isoformat(timespec="seconds")
    gravar(SAIDA, feito)
    for arq in respostas:
        arq.unlink()
        lote = FILA / f"lote_{arq.stem.split('_')[1]}_{arq.stem.split('_')[2]}.json"
        lote.unlink(missing_ok=True)
    if n_forcado:
        print(f"{n_forcado} conversa(s) sem assunto tiveram o módulo trocado para "
              "'(sem assunto)', como manda a regra.")
    print(f"Absorvidos {n_ok} registros ({n_erro} recusados). "
          f"Total em {SAIDA.name}: "
          f"{len(feito['chamados']) + len(feito['conversas'])}")
    return 0


def cmd_status(a) -> int:
    grupos = pendencias(a.de, a.ate)
    feito = ler(SAIDA, {"chamados": {}, "conversas": {}})
    print(f"Janela {a.de} a {a.ate}")
    print(f"  já lidos neste arquivo: "
          f"{len(feito['chamados']) + len(feito['conversas'])}")
    falta = 0
    for g in ("A", "B", "C", "D"):
        n = len(grupos.get(g) or [])
        falta += n
        if n:
            print(f"  {g}  {n:>6}  {NOMES[g]}")
    print(f"  FALTA LER: {falta}")
    restos = sorted(FILA.glob("resp_*.json")) if FILA.exists() else []
    if restos:
        print(f"  respostas na fila esperando absorver: {len(restos)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("preparar")
    p.add_argument("--de", required=True)
    p.add_argument("--ate", default=date.today().isoformat())
    p.add_argument("--forcar", action="store_true")
    p.set_defaults(fn=cmd_preparar)
    p = sub.add_parser("absorver")
    p.add_argument("--parcial", action="store_true",
                   help="grava o que está válido em vez de recusar o arquivo inteiro")
    p.set_defaults(fn=cmd_absorver)
    p = sub.add_parser("status")
    p.add_argument("--de", default="2026-01-01")
    p.add_argument("--ate", default=date.today().isoformat())
    p.set_defaults(fn=cmd_status)
    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
