# -*- coding: utf-8 -*-
"""Quantas conversas e chamados cada pessoa atendeu, por dia.

Responde a uma pergunta diferente da do relatório principal. O relatório conta
**fricção do cliente**: o que doeu e onde. Este conta **trabalho da equipe**: quem
atendeu quanto. Por isso é arquivo separado — misturar os dois numa planilha convida a
ler um pelo outro, e o número de atendimentos por pessoa não diz nada sobre produto.

## Como se sabe quem atendeu

Três fontes na transcrição, em ordem de força:

1. `[HH:MM] Atendente (Nome):` — a pessoa escreveu. Prova direta.
2. `(sistema): Nome picked conversation` — a pessoa pegou a conversa. Conta como
   atendimento: ela assumiu o atendimento, e em conversa transferida o autor das
   mensagens seguintes se perde (vira `(sistema)`), então exigir a fala descartaria
   atendimento real. Medido em 05/11: 105 das 218 conversas atendidas só têm o nome aqui.
3. `transferida para Nome` **sem** pick e **sem** fala — NÃO conta. A conversa foi
   encaminhada para a pessoa e ela nunca a pegou; creditar o atendimento a ela seria
   premiar o roteamento, não o trabalho.

O campo `operador` da base **não serve** para esta pergunta: ele é quem está atribuído,
não quem atendeu. Em 05/11 ele aponta Tarik Ferraz em 360 conversas e Bruno Alvarenga em
118 — são a primeira linha da fila —, e em 371 dessas ninguém falou.

Uso:
    python pipeline/gerar_atendimento.py                      # hoje
    python pipeline/gerar_atendimento.py --dia 2026-11-05
    python pipeline/gerar_atendimento.py --dia 2026-11-05 --compara 10
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import glob
import json
import re
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

RAIZ = Path(__file__).resolve().parent.parent
STORE = RAIZ / "data" / "store"
RAW = RAIZ / "data" / "raw"
SAIDA = RAIZ / "report"

FALA = re.compile(r"^\[\d\d:\d\d\] Atendente \(([^)]+)\):", re.M)
PICK = re.compile(r"^\[\d\d:\d\d\] \(sistema\): (.+?) picked conversation", re.M)
AVISO_FILA = "fila de atendimento está maior que o esperado"

AZUL = PatternFill("solid", fgColor="1F3864")
CINZA = PatternFill("solid", fgColor="F2F2F2")
BRANCO_N = Font(color="FFFFFF", bold=True)


def carregar() -> tuple[dict, dict]:
    conv = {}
    for linha in (STORE / "base_historica.jsonl").open(encoding="utf-8"):
        r = json.loads(linha)
        if r["tipo"] == "conversa":
            conv[str(r["id"])] = r
    tr = json.loads((STORE / "transcricoes.json").read_text(encoding="utf-8"))
    return conv, tr


def chamados_por_pessoa() -> dict[str, collections.Counter]:
    """dia -> {pessoa: chamados que ela abriu}. O creator é o analista que atendeu
    o cliente; o responsible é sempre a mesma pessoa (a gestora), então não serve."""
    vistos = {}
    for arq in sorted(glob.glob(str(RAW / "bitrix_export_*.json"))):
        for td in json.loads(Path(arq).read_text(encoding="utf-8"))["tasks"]:
            t = td.get("task") or {}
            if t.get("id") is not None:
                vistos[str(t["id"])] = t
    por_dia: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for t in vistos.values():
        d = (t.get("createdDate") or "")[:10]
        nome = (t.get("creator") or {}).get("name")
        if d and nome:
            por_dia[d][nome] += 1
    return por_dia


def metricas_do_dia(dia: str, conv: dict, tr: dict) -> dict:
    atendeu: collections.Counter = collections.Counter()   # falou OU pegou
    falou: collections.Counter = collections.Counter()
    msgs: collections.Counter = collections.Counter()
    total = atendidas = abertas_sem_atend = com_aviso = aviso_atendido = 0

    for i, r in conv.items():
        if r["data"][:10] != dia:
            continue
        total += 1
        t = tr.get(i, "")
        nomes_fala = FALA.findall(t)
        nomes_pick = PICK.findall(t)
        donos = {n.strip() for n in nomes_fala} | {n.strip() for n in nomes_pick}
        for n in donos:
            atendeu[n] += 1
        for n in {x.strip() for x in nomes_fala}:
            falou[n] += 1
        for n in nomes_fala:
            msgs[n.strip()] += 1
        if donos:
            atendidas += 1
        elif not r.get("encerrada"):
            abertas_sem_atend += 1
        if AVISO_FILA in t:
            com_aviso += 1
            if donos:
                aviso_atendido += 1

    return {"atendeu": atendeu, "falou": falou, "msgs": msgs, "total": total,
            "atendidas": atendidas, "abertas_sem_atend": abertas_sem_atend,
            "com_aviso": com_aviso, "aviso_atendido": aviso_atendido}


def cabecalho(ws, cols: list[str], linha: int = 1) -> None:
    for j, c in enumerate(cols, 1):
        cel = ws.cell(row=linha, column=j, value=c)
        cel.fill, cel.font = AZUL, BRANCO_N
        cel.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.freeze_panes = ws.cell(row=linha + 1, column=1)


def larguras(ws, larg: list[int]) -> None:
    for j, w in enumerate(larg, 1):
        ws.column_dimensions[get_column_letter(j)].width = w


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dia", default=dt.date.today().isoformat())
    ap.add_argument("--compara", type=int, default=10,
                    help="quantos dias úteis anteriores entram no comparativo")
    a = ap.parse_args()

    conv, tr = carregar()
    chamados = chamados_por_pessoa()

    dias_com_dado = sorted({r["data"][:10] for r in conv.values() if r["data"][:10] <= a.dia})
    anteriores = [d for d in dias_com_dado if d < a.dia][-a.compara:]

    hoje = metricas_do_dia(a.dia, conv, tr)
    antes = {d: metricas_do_dia(d, conv, tr) for d in anteriores}

    wb = Workbook()

    # ---------- aba 1: o dia ----------
    ws = wb.active
    ws.title = "Por pessoa"
    ws["A1"] = f"Atendimento por pessoa — {a.dia[8:]}/{a.dia[5:7]}/{a.dia[:4]}"
    ws["A1"].font = Font(size=14, bold=True)
    ws["A2"] = (f"{hoje['total']} conversas abertas no dia · {hoje['atendidas']} atendidas"
                f" · {hoje['abertas_sem_atend']} ainda abertas sem ninguém ter atendido")
    ws["A3"] = ("Atendeu = a pessoa escreveu na conversa OU pegou a conversa da fila. "
                "Conversa transferida para alguém que nunca a pegou não conta para ela.")
    ws["A3"].font = Font(italic=True, color="595959")

    # Quem costuma atender e hoje não atendeu. Vai no topo do arquivo de propósito:
    # uma coluna de volume por pessoa, lida sozinha, faz parecer que quem ficou
    # produziu pouco — quando o que explica o dia é quem não estava na fila.
    habituais = [n for n in {x for d in anteriores for x in antes[d]["atendeu"]}
                 if sum(1 for d in anteriores if antes[d]["atendeu"][n] >= 15) >= 2]
    fora = sorted(n for n in habituais if hoje["atendeu"][n] <= 2)
    if fora:
        pico = {n: max(antes[d]["atendeu"][n] for d in anteriores) for n in fora}
        # O volume do dia comparado aos anteriores, medido e não afirmado: dizer
        # "o maior volume do período" sem conferir já saiu errado uma vez.
        uteis = sorted(antes[d]["total"] for d in anteriores if antes[d]["total"] >= 50)
        if uteis and hoje["total"] > max(uteis):
            vol = f"O dia teve o maior volume do período ({hoje['total']} conversas)"
        elif uteis:
            mediana = uteis[len(uteis) // 2]
            rel = ("acima" if hoje["total"] > mediana else
                   "abaixo" if hoje["total"] < mediana else "na")
            vol = (f"O dia teve {hoje['total']} conversas, {rel} "
                   f"{'da' if rel == 'na' else 'd'}a mediana dos dias úteis "
                   f"anteriores ({mediana})")
        else:
            vol = f"O dia teve {hoje['total']} conversas"
        ws["A4"] = (f"Fora da fila em {a.dia[8:]}/{a.dia[5:7]}, entre quem costuma "
                    "atender: "
                    + ", ".join(f"{n} (pico de {pico[n]}/dia)" for n in fora)
                    + f". {vol}, com menos gente na fila — leia a coluna de volume com "
                      "isso em mente.")
        ws["A4"].font = Font(italic=True, color="9C0006")

    cols = ["Pessoa", "Conversas atendidas", "Das quais escreveu",
            "Mensagens enviadas", "Chamados abertos", "Total (conversas + chamados)"]
    cabecalho(ws, cols, linha=6)
    pessoas = sorted(set(hoje["atendeu"]) | set(chamados.get(a.dia, {})),
                     key=lambda n: (-(hoje["atendeu"][n] + chamados.get(a.dia, {}).get(n, 0)), n))
    r = 7
    for n in pessoas:
        ch = chamados.get(a.dia, {}).get(n, 0)
        ws.cell(row=r, column=1, value=n)
        ws.cell(row=r, column=2, value=hoje["atendeu"][n])
        ws.cell(row=r, column=3, value=hoje["falou"][n])
        ws.cell(row=r, column=4, value=hoje["msgs"][n])
        ws.cell(row=r, column=5, value=ch)
        ws.cell(row=r, column=6, value=hoje["atendeu"][n] + ch)
        r += 1
    for j, v in ((1, "TOTAL"), (2, sum(hoje["atendeu"].values())),
                 (3, sum(hoje["falou"].values())), (4, sum(hoje["msgs"].values())),
                 (5, sum(chamados.get(a.dia, {}).values())),
                 (6, sum(hoje["atendeu"].values()) + sum(chamados.get(a.dia, {}).values()))):
        cel = ws.cell(row=r, column=j, value=v)
        cel.font, cel.fill = Font(bold=True), CINZA
    larguras(ws, [26, 20, 18, 18, 16, 20])

    # ---------- aba 2: comparativo ----------
    ws2 = wb.create_sheet("Comparativo")
    ws2["A1"] = "Conversas atendidas por pessoa, por dia"
    ws2["A1"].font = Font(size=14, bold=True)
    ws2["A2"] = ("Serve para ler o dia: um número baixo pode ser dia fraco da pessoa ou "
                 "dia em que ela não estava. A linha de baixo mostra o total do dia.")
    ws2["A2"].font = Font(italic=True, color="595959")
    dias = anteriores + [a.dia]
    cabecalho(ws2, ["Pessoa"] + [f"{d[8:]}/{d[5:7]}" for d in dias], linha=4)
    todas = {n for d in dias for n in (antes.get(d) or hoje)["atendeu"]}
    ordem = sorted(todas, key=lambda n: -hoje["atendeu"][n])
    r = 5
    for n in ordem:
        ws2.cell(row=r, column=1, value=n)
        for j, d in enumerate(dias, 2):
            m = hoje if d == a.dia else antes[d]
            ws2.cell(row=r, column=j, value=m["atendeu"][n] or None)
        r += 1
    for rot, chave in (("TOTAL atendidas", "atendidas"),
                       ("Conversas abertas no dia", "total"),
                       ("Receberam aviso de fila cheia", "com_aviso"),
                       ("Dessas, atendidas", "aviso_atendido")):
        ws2.cell(row=r, column=1, value=rot).font = Font(bold=True)
        ws2.cell(row=r, column=1).fill = CINZA
        for j, d in enumerate(dias, 2):
            m = hoje if d == a.dia else antes[d]
            cel = ws2.cell(row=r, column=j, value=m[chave])
            cel.font, cel.fill = Font(bold=True), CINZA
        r += 1
    larguras(ws2, [30] + [10] * len(dias))

    # ---------- aba 3: legenda ----------
    ws3 = wb.create_sheet("Legenda")
    ws3["A1"] = "Como cada número é obtido"
    ws3["A1"].font = Font(size=14, bold=True)
    texto = [
        ("Conversas atendidas",
         "Conversas em que a pessoa escreveu alguma mensagem OU pegou a conversa da fila. "
         "Uma conversa pode contar para mais de uma pessoa quando houve transferência: é "
         "atendimento das duas, e por isso a soma da coluna passa do total de conversas."),
        ("Das quais escreveu",
         "Subconjunto em que há mensagem escrita por ela. A diferença em relação à coluna "
         "anterior é conversa que ela pegou e cujo texto das mensagens seguintes perdeu o "
         "autor — um defeito conhecido da base: depois de uma transferência o autor vira "
         "'(sistema)'. O atendimento aconteceu; só o nome se perdeu."),
        ("Mensagens enviadas",
         "Linhas de mensagem atribuídas a ela. Pela mesma razão acima, é um piso."),
        ("Chamados abertos",
         "Chamados criados por ela no dia. Vem do campo 'creator' do Bitrix, que é o "
         "analista que atendeu o cliente. O campo 'responsible' não serve: é sempre a "
         "mesma pessoa, a gestora da fila de desenvolvimento."),
        ("Por que não usamos o campo 'operador'",
         "'Operador' é quem está atribuído à conversa, não quem atendeu. Ele aponta a "
         "primeira linha da fila em quase toda conversa, inclusive nas que ninguém "
         "respondeu."),
        ("Conversa aberta sem atendimento",
         "Conversa que ninguém escreveu nem pegou e que seguia aberta no momento da "
         "coleta. É cliente esperando na fila."),
        ("Aviso de fila cheia",
         "Mensagem automática que o sistema manda quando a fila passa do esperado. A linha "
         "'Dessas, atendidas' é a métrica de atendimento mais direta que a base oferece: "
         "ficou entre 97% e 100% de junho a outubro."),
        ("O que este arquivo NÃO mede",
         "Tempo de atendimento, dificuldade do caso e qualidade. Conversa de uma pergunta "
         "e caso fiscal de duas horas contam igual. Comparar pessoas por volume sem olhar "
         "o que cada uma pegou leva a conclusão errada."),
    ]
    r = 3
    for titulo, corpo in texto:
        c = ws3.cell(row=r, column=1, value=titulo)
        c.font = Font(bold=True)
        c2 = ws3.cell(row=r, column=2, value=corpo)
        c2.alignment = Alignment(wrap_text=True, vertical="top")
        ws3.row_dimensions[r].height = 46
        r += 1
    larguras(ws3, [34, 110])

    SAIDA.mkdir(exist_ok=True)
    destino = SAIDA / f"atendimento_por_pessoa_{a.dia}.xlsx"
    wb.save(destino)
    print(f"{a.dia}: {hoje['total']} conversas, {hoje['atendidas']} atendidas, "
          f"{hoje['abertas_sem_atend']} abertas sem atendimento")
    print(f"  aviso de fila: {hoje['com_aviso']} conversas, "
          f"{hoje['aviso_atendido']} atendidas")
    print(f"\n  {destino}")


if __name__ == "__main__":
    main()
