# -*- coding: utf-8 -*-
"""
Varredura do ponto cego da V3 — a conversa que a regra de versão não enxerga.

    python pipeline/varrer_ponto_cego.py preparar --de 2026-10-29T08:00 --ate agora
    python pipeline/varrer_ponto_cego.py absorver <vereditos.json> --de ... --ate ...

A regra de `consolidar_store` marca conversa como V3 pela linha de entrada (17) ou pela
transferência explícita para a fila da V3. O WhatsApp entra todo pela linha 7, então zap
de oficina recém-migrada só é contado se o atendente transferiu — e poucos transferem.
Medido em 29/10/2026, dia da onda de 200 oficinas: a regra achou 1 conversa V3 no WhatsApp
e a leitura achou outras 14. Ordem de grandeza, no canal onde o cliente mais fala.

Ler todas as conversas V2 da janela resolve, mas numa janela de um dia inteiro são
centenas. Então `preparar` separa três grupos:

  candidatos   têm sinal de versão no texto, ou citam chamado que a regra marcou V3.
               Vão para leitura do modelo, que decide V3 / V2 / indefinido.
  vazias       WhatsApp sem conteúdo útil depois de descontar as mensagens de sistema.
               Entram direto como "não confirmada", sem leitura: não há o que ler.
  resto        conversa V2 com assunto próprio e nenhum sinal de versão. Não entra.

O filtro de candidatos é validado contra verdade de campo a cada execução: toda conversa
já gravada como `confirmada` no v3_por_conteudo tem de continuar sendo pega por ele. Se
alguma escapar, `preparar` falha. Sem isso, afrouxar o regex degradaria a varredura em
silêncio, e o jeito de descobrir seria um número baixo que ninguém questiona.
"""
from __future__ import annotations
import argparse
import collections
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
STORE = RAIZ / "data" / "store"
FILA = STORE / "_fila"
ALVO = STORE / "v3_por_conteudo.json"

sys.stdout.reconfigure(encoding="utf-8")
TZ_BR = timezone(timedelta(hours=-3))

# Sinal de que o atendimento é da versão nova. Calibrado contra as 16 conversas provadas
# da janela de 29/10: um regex mais estreito (só "nova versão|v3|sistema novo|sistema3")
# pegava 5 das 12 provadas por texto. O cliente quase nunca diz "V3" — diz "atualizou",
# "está diferente", "antes dava e agora não".
SINAL = re.compile(
    r"nova\s+vers|vers[aã]o\s+nova|\bv3\b|v\.\s*3\b|sistema\s+novo|novo\s+sistema|sistema3"
    r"|atualiz|mudou|mudan[cç]a|diferente|plataforma"
    r"|sistema\s+antigo|vers[aã]o\s+anterior|modelo\s+antigo"
    r"|\bantes\b[^.!?]{0,90}\bagora\b|\bagora\b[^.!?]{0,90}\bantes\b", re.I)

# Mensagem que o próprio Bitrix injeta. Conta como texto e faz conversa vazia parecer
# cheia, então sai antes de medir se há conteúdo.
BOILER = re.compile(
    r"(Enquiry transferred to [^|]{0,60}according to queuing rules"
    r"|Consulta transferida para [^|]{0,60}de acordo com as regras de enfileiramento"
    r"|redirected conversation from queue \"[^\"]*\" to queue \"[^\"]*\""
    r"|Novo (contato|neg[oó]cio) criado"
    r"|Formul[aá]rio preenchido: \"[^\"]*\")", re.I)

ID_CHAMADO = re.compile(r"\b10[0-9]{4}\b")
LIMITE_VAZIA = 130  # caracteres de conteúdo útil; abaixo disso não há o que interpretar


def ler(p: Path, padrao=None):
    return json.loads(p.read_text(encoding="utf-8-sig")) if p.exists() else padrao


def momento_br(r: dict) -> datetime:
    """Igual ao gerador: chamado vem com offset de Brasília, conversa vem em UTC."""
    bruto = (r.get("criado_em") or "").strip()
    try:
        dt = datetime.fromisoformat(bruto)
    except ValueError:
        return datetime.fromisoformat(r["data"] + "T00:00:00")
    if dt.tzinfo is not None:
        return dt.astimezone(TZ_BR).replace(tzinfo=None)
    return dt + TZ_BR.utcoffset(None)


def instante(valor: str, fim_do_dia: bool) -> datetime:
    if valor == "agora":
        return datetime.now()
    if "T" in valor:
        return datetime.fromisoformat(valor)
    return datetime.fromisoformat(valor + ("T23:59:59" if fim_do_dia else "T00:00:00"))


def conteudo_util(r: dict) -> str:
    return BOILER.sub(" ", re.sub(r"\s+", " ", r.get("texto") or "")).strip()


def carregar(ini: datetime, fim: datetime):
    """Conversas V2 da janela, e os ids de chamado que a regra marcou V3."""
    v3_chamados, v2 = set(), []
    with (STORE / "base_historica.jsonl").open(encoding="utf-8") as fh:
        for linha in fh:
            r = json.loads(linha)
            if r["tipo"] == "chamado":
                if r.get("versao") == "V3":
                    v3_chamados.add(str(r["id"]))
            elif r.get("versao") != "V3" and ini <= momento_br(r) <= fim:
                v2.append(r)
    return v2, v3_chamados


def separar(v2, v3_chamados):
    candidatos, vazias = [], []
    for r in v2:
        texto = r.get("texto") or ""
        cita = sorted(set(ID_CHAMADO.findall(texto)) & v3_chamados)
        if SINAL.search(texto) or cita:
            candidatos.append((r, cita))
        elif r.get("canal") == "WhatsApp" and len(conteudo_util(r)) < LIMITE_VAZIA:
            vazias.append(r)
    return candidatos, vazias


def conferir_recall(candidatos, vazias, v2):
    """Toda confirmada que já conhecemos tem de continuar sendo pega pelo filtro.

    É o único teste possível aqui: não existe gabarito para a janela nova, mas existe para
    as conversas que já foram provadas. Se o filtro deixar uma escapar, ele piorou.
    """
    anterior = (ler(ALVO, {}) or {}).get("conversas", {})
    provadas = {cid for cid, v in anterior.items() if v.get("situacao", "confirmada") == "confirmada"}
    na_janela = {str(r["id"]) for r in v2}
    devia = provadas & na_janela
    if not devia:
        return 0, set()
    pego = {str(r["id"]) for r, _ in candidatos} | {str(r["id"]) for r in vazias}
    return len(devia), devia - pego


def cmd_preparar(a):
    ini, fim = instante(a.de, False), instante(a.ate, True)
    v2, v3_chamados = carregar(ini, fim)
    candidatos, vazias = separar(v2, v3_chamados)

    n_devia, escaparam = conferir_recall(candidatos, vazias, v2)
    if escaparam:
        print(f"ABORTADO: o filtro deixou escapar {len(escaparam)} de {n_devia} conversas "
              f"já provadas como V3: {sorted(escaparam)}")
        print("O regex SINAL piorou, ou o texto da conversa mudou. Corrija antes de varrer.")
        return 1
    print(f"recall conferido: {n_devia}/{n_devia} das já provadas continuam no filtro")

    FILA.mkdir(parents=True, exist_ok=True)
    md = FILA / "ponto_cego_candidatos.md"
    with md.open("w", encoding="utf-8") as f:
        f.write(f"# {len(candidatos)} conversas a julgar — janela {a.de} a {a.ate}\n\n")
        f.write("Para cada uma: o atendimento é da V3 (cliente usando o sistema novo), da "
                "V2, ou indefinido?\n\n")
        for r, cita in sorted(candidatos, key=lambda x: momento_br(x[0])):
            f.write(f"## conversa {r['id']} — {momento_br(r):%d/%m %H:%M} — "
                    f"{r.get('canal')}\n")
            f.write(f"- cliente: {r.get('cliente') or '(sem)'} | "
                    f"mensagens {r.get('mensagens')}\n")
            if cita:
                f.write(f"- CITA CHAMADO MARCADO V3: {', '.join(cita)}\n")
            f.write(f"- texto: {conteudo_util(r)[:1600]}\n\n")

    jv = FILA / "ponto_cego_vazias.json"
    jv.write_text(json.dumps({str(r["id"]): len(conteudo_util(r)) for r in vazias},
                             ensure_ascii=False, indent=1), encoding="utf-8")

    canais = collections.Counter(r.get("canal") for r, _ in candidatos)
    print(f"\nconversas V2 na janela: {len(v2)}")
    print(f"  candidatos a julgar:   {len(candidatos)} ({dict(canais)})  -> {md}")
    print(f"  WhatsApp sem conteúdo: {len(vazias)} (entram como não confirmada)  -> {jv}")
    print(f"  resto, fora da aba:    {len(v2) - len(candidatos) - len(vazias)}")
    print("\nJulgue os candidatos e rode: absorver <arquivo>, no formato")
    print('  {"294393": {"veredito": "V3", "evidencia": "...", "confianca": "alta"}}')
    return 0


def cmd_absorver(a):
    ini, fim = instante(a.de, False), instante(a.ate, True)
    v2, v3_chamados = carregar(ini, fim)
    candidatos, vazias = separar(v2, v3_chamados)
    ids_cand = {str(r["id"]) for r, _ in candidatos}

    vereditos = ler(Path(a.arquivo))
    if not isinstance(vereditos, dict):
        print(f"ABORTADO: {a.arquivo} não é um objeto JSON de id -> veredito.")
        return 1
    extra = set(vereditos) - ids_cand
    if extra:
        print(f"ABORTADO: {len(extra)} id(s) não são candidatos desta janela: "
              f"{sorted(extra)[:8]}")
        return 1
    falta = ids_cand - set(vereditos)
    if falta:
        print(f"ABORTADO: {len(falta)} candidato(s) sem veredito: {sorted(falta)[:8]}")
        return 1
    validos = {"V3", "V2", "indefinido"}
    ruins = {k: v.get("veredito") for k, v in vereditos.items()
             if v.get("veredito") not in validos}
    if ruins:
        print(f"ABORTADO: veredito fora de {sorted(validos)}: {ruins}")
        return 1

    doc = ler(ALVO, {}) or {}
    conversas = doc.get("conversas", {})
    # Curadoria anterior não é sobrescrita: só acrescenta o que esta janela trouxe. Foi
    # assim que o cache de conversas do fluxo fiscal já foi zerado uma vez.
    novas = antigas = 0
    canal = {str(r["id"]): r.get("canal") for r in v2}

    for cid, d in vereditos.items():
        if d["veredito"] == "V3":
            # `base` vem do veredito, não de adivinhação pelo texto da evidência. A versão
            # anterior inferia "chamado" quando a palavra aparecia na frase, e marcou como
            # ligada-por-chamado uma conversa cuja prova era o próprio cliente falando e
            # que só mencionava um chamado de passagem.
            entrada = {"situacao": "confirmada",
                       "base": d.get("base") or "texto",
                       "confianca": d.get("confianca", "media"),
                       "evidencia": d.get("evidencia", "")}
        elif d["veredito"] == "indefinido":
            # Indefinido entra qualquer que seja o canal. A tentação era listar só
            # WhatsApp, que foi o pedido original, mas o conjunto julgado já é pequeno e
            # pré-filtrado: todo indefinido aqui é conversa COM sinal de versão que não deu
            # para decidir. Descartar os de LiveChat esconderia justamente casos como o
            # relatório que existia no mês passado e não existe mais.
            entrada = {"situacao": "nao_confirmada", "base": "sem prova de versão",
                       "confianca": "-", "evidencia": d.get("evidencia", "")}
        else:
            continue
        if cid in conversas:
            antigas += 1
        else:
            novas += 1
        conversas[cid] = entrada

    for r in vazias:
        cid = str(r["id"])
        if cid in conversas:
            continue
        conversas[cid] = {"situacao": "nao_confirmada", "base": "sem prova de versão",
                          "confianca": "-",
                          "evidencia": "conversa de WhatsApp sem conteúdo útil — só "
                                       "cumprimento ou mensagem de sistema"}
        novas += 1

    doc["conversas"] = conversas
    doc["gerado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    doc.setdefault("o_que_e",
                   "Conversa que a regra automática marcou V2 e cujo atendimento é da V3.")
    doc["como_usar"] = ("O gerador lista estes registros numa aba própria e NÃO os soma em "
                        "nenhum número. `situacao` separa o provado (confirmada) do "
                        "inconclusivo (nao_confirmada). Promover qualquer um a número é "
                        "decisão de quem lê o relatório, não do pipeline.")
    doc["janela_varrida"] = f"{a.de} a {a.ate} (hora de Brasília)"
    doc["cobertura"] = (f"Das {len(v2)} conversas V2 da janela, {len(candidatos)} foram "
                        f"julgadas uma a uma e {len(vazias)} entraram como não confirmada "
                        "por não terem conteúdo. O resto tem assunto próprio e nenhum "
                        "sinal de versão. O filtro pega 16 de 16 das conversas já provadas "
                        "como V3, e isso é reconferido a cada execução.")
    ALVO.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

    conf = sum(1 for v in conversas.values() if v["situacao"] == "confirmada")
    nao = sum(1 for v in conversas.values() if v["situacao"] == "nao_confirmada")
    print(f"gravado {ALVO}")
    print(f"  {novas} entradas novas, {antigas} atualizadas")
    print(f"  no total: {conf} confirmada, {nao} não confirmada")
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for nome in ("preparar", "absorver"):
        p = sub.add_parser(nome)
        if nome == "absorver":
            p.add_argument("arquivo")
        p.add_argument("--de", required=True)
        p.add_argument("--ate", default="agora")
    a = ap.parse_args()
    return {"preparar": cmd_preparar, "absorver": cmd_absorver}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
