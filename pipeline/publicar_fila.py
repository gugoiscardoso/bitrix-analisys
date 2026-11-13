# -*- coding: utf-8 -*-
"""Publica a planilha da fila de atendimento com a conta de serviço.

Lê o JSON que o `montar_planilha.py` gravou e escreve as sete abas direto na API do
Google, do mesmo jeito que o `publicar_relatorio.py` faz com o relatório completo.

Por que um script e não o conector do Sheets: em 13/11/2026 o conector devolveu HTTP 500
das 10h às 11h55. Nove execuções seguidas não publicaram, a linha das 10h da aba
`Fila por hora` se perdeu, e a execução das 09:59 caiu no meio — três abas com o carimbo
novo e quatro com o velho, por quase duas horas, sem nada na planilha que avisasse.

## O que este script garante, e o conector não garantia

1. **Tudo ou nada.** As sete abas vão num único `values.batchUpdate`, que o Google
   aplica inteiro ou recusa inteiro. Planilha pela metade deixa de existir.
2. **Repetição em 429, 500 e 503**, com a mesma espera do relatório completo.
3. **Aba que encolhe não deixa resto.** Sai uma pessoa, a aba fica uma linha mais curta,
   e a última linha antiga continuaria lá embaixo. As linhas que sobram são escritas em
   branco no mesmo envio.
4. **A linha da hora é decidida aqui**, não por quem chama: mesma data e mesma hora de
   início da janela sobrescreve, qualquer outra coisa vai para a linha seguinte. Linha
   de hora anterior nunca é tocada.

A planilha precisa estar compartilhada com a conta de serviço como Editor.

Uso:
    python pipeline/publicar_fila.py --entrada abas.json
    python pipeline/publicar_fila.py --entrada abas.json --simular   # não escreve
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from googleapiclient.errors import HttpError

from publicar_relatorio import com_repeticao, servico

ABA_HORA = "Fila por hora"
AZUL = {"red": 0.12, "green": 0.22, "blue": 0.39}
CINZA = {"red": 0.93, "green": 0.93, "blue": 0.93}
BRANCO = {"red": 1, "green": 1, "blue": 1}


def coluna(n: int) -> str:
    """1 -> A, 12 -> L. As abas daqui não passam de Z."""
    return chr(ord("A") + n - 1)


def linha_da_hora(existentes: list[list], nova: list) -> int:
    """Em que linha (1 = cabeçalho) a medição desta hora deve ficar.

    A identidade da linha é a data mais a hora de INÍCIO da janela. Não a janela
    inteira: ela cresce ao longo da hora ("11:00-11:20", depois "11:00-11:50"), e
    comparar o texto todo duplicaria a linha a cada execução. E não a hora do Momento:
    uma execução das 09:19 que mediu "08:00-09:00" pertence à janela das 08h.
    """
    def chave(l: list) -> tuple[str, str]:
        momento = str(l[0]) if l else ""
        janela = str(l[1]) if len(l) > 1 else ""
        return momento[:10], janela[:5]

    if len(existentes) > 1 and chave(existentes[-1]) == chave(nova):
        return len(existentes)
    return len(existentes) + 1


def pedidos_de_formato(formato: dict, ids: dict[str, int],
                       larguras: dict[str, int]) -> list[dict]:
    """Cabeçalho azul, TOTAL cinza, e branco sem negrito entre os dois.

    Vai em toda execução, e não só quando o TOTAL anda: é um pedido só, idempotente, e
    comparar com a execução anterior era a parte frágil do processo manual.
    """
    def faixa(nome: str, de: int, ate: int) -> dict:
        return {"sheetId": ids[nome], "startRowIndex": de - 1, "endRowIndex": ate,
                "startColumnIndex": 0, "endColumnIndex": larguras[nome]}

    def pintar(nome: str, de: int, ate: int, fundo: dict, negrito: bool,
               cabecalho: bool = False) -> dict:
        fmt = {"textFormat": {"bold": negrito},
               "backgroundColorStyle": {"rgbColor": fundo}}
        campos = "userEnteredFormat.textFormat.bold,userEnteredFormat.backgroundColorStyle"
        if cabecalho:
            fmt["textFormat"]["foregroundColorStyle"] = {"rgbColor": BRANCO}
            fmt["horizontalAlignment"] = "CENTER"
            campos += (",userEnteredFormat.textFormat.foregroundColorStyle"
                       ",userEnteredFormat.horizontalAlignment")
        return {"repeatCell": {"range": faixa(nome, de, ate),
                               "cell": {"userEnteredFormat": fmt}, "fields": campos}}

    pedidos = []
    for nome, f in formato.items():
        cab, total = f.get("cabecalho"), f.get("total")
        if not cab or not total or nome not in ids:
            continue
        pedidos.append(pintar(nome, cab, cab, AZUL, True, cabecalho=True))
        if total - cab > 1:
            pedidos.append(pintar(nome, cab + 1, total - 1, BRANCO, False))
        pedidos.append(pintar(nome, total, total, CINZA, True))
    return pedidos


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", required=True, help="o JSON do montar_planilha.py")
    ap.add_argument("--simular", action="store_true",
                    help="lê a planilha e mostra o que escreveria, sem escrever")
    a = ap.parse_args()

    dados = json.loads(Path(a.entrada).read_text(encoding="utf-8"))
    abas: dict[str, list[list]] = dados["abas"]
    nova = dados["linha_hora"][0]

    svc, cfg = servico()
    sid = cfg["FilaSpreadsheetId"]
    planilha = svc.spreadsheets()

    # Uma leitura só: a grade de cada aba, a coluna A das abas sobrescritas (para saber
    # até onde ia a versão anterior) e as duas primeiras colunas da aba por hora.
    try:
        meta = com_repeticao(planilha.get(
            spreadsheetId=sid, fields="sheets.properties"), "get")
    except HttpError as e:
        if e.resp.status == 403:
            raise SystemExit(
                f"A conta de serviço não tem acesso à planilha {sid}.\n"
                f"  Compartilhe a planilha com ela como Editor.")
        raise
    props = {s["properties"]["title"]: s["properties"] for s in meta["sheets"]}
    faltam = [n for n in [*abas, ABA_HORA] if n not in props]
    if faltam:
        raise SystemExit(f"Aba que não existe na planilha: {', '.join(faltam)}")
    ids = {n: p["sheetId"] for n, p in props.items()}

    nomes = list(abas)
    lido = com_repeticao(planilha.values().batchGet(
        spreadsheetId=sid,
        ranges=[f"'{n}'!A:A" for n in nomes] + [f"'{ABA_HORA}'!A:B"]), "ler")
    faixas = lido["valueRanges"]
    altura_antiga = {n: len(faixas[i].get("values", [])) for i, n in enumerate(nomes)}
    horas = faixas[-1].get("values", [])

    n_hora = linha_da_hora(horas, nova)
    acao = "sobrescreve" if n_hora <= len(horas) else "linha nova"

    envio = []
    larguras = {}
    for nome, linhas in abas.items():
        largura = len(linhas[0])
        larguras[nome] = largura
        sobra = max(0, altura_antiga[nome] - len(linhas))
        corpo = linhas + [[""] * largura] * sobra
        envio.append({"range": f"'{nome}'!A1:{coluna(largura)}{len(corpo)}",
                      "values": corpo})
    envio.append({"range": f"'{ABA_HORA}'!A{n_hora}:{coluna(len(nova))}{n_hora}",
                  "values": [nova]})

    print(f"planilha {sid}")
    for e in envio:
        print(f"  {e['range']:34} {len(e['values'])} linhas")
    print(f"  {ABA_HORA}: {acao} (linha {n_hora}, janela {nova[1]})")
    if a.simular:
        print("\nsimulação: nada foi escrito")
        return

    # A aba por hora cresce uma linha por hora; a grade tem de existir antes do valor.
    falta_grade = n_hora - props[ABA_HORA]["gridProperties"]["rowCount"]
    if falta_grade > 0:
        com_repeticao(planilha.batchUpdate(spreadsheetId=sid, body={"requests": [
            {"appendDimension": {"sheetId": ids[ABA_HORA], "dimension": "ROWS",
                                 "length": falta_grade + 500}}]}), "grade")

    # RAW: número do JSON continua número, e texto continua o texto que o script
    # montou. USER_ENTERED transformaria "13/11/2026 11:56" em data, e a comparação da
    # linha da hora passaria a depender do formato de exibição da célula.
    com_repeticao(planilha.values().batchUpdate(spreadsheetId=sid, body={
        "valueInputOption": "RAW", "data": envio}), "escrever")

    formato = pedidos_de_formato(dados.get("formato", {}), ids, larguras)
    if formato:
        com_repeticao(planilha.batchUpdate(
            spreadsheetId=sid, body={"requests": formato}), "formatar")

    # Conferência: o carimbo e a fila têm de ser os mesmos nas duas abas, e os de agora.
    volta = com_repeticao(planilha.values().batchGet(
        spreadsheetId=sid, ranges=["'Agora'!B2:B4", "'Por pessoa'!B2:B4"],
        valueRenderOption="UNFORMATTED_VALUE"), "conferir")["valueRanges"]
    agora, pessoa = ([l[0] if l else "" for l in v.get("values", [])] for v in volta)
    esperado = [abas["Agora"][1][1], abas["Agora"][3][1]]
    if [agora[0], agora[2]] != esperado or [pessoa[0], pessoa[2]] != esperado:
        print(f"\nCONFERÊNCIA FALHOU: esperava {esperado}, "
              f"Agora tem {[agora[0], agora[2]]}, Por pessoa tem {[pessoa[0], pessoa[2]]}")
        sys.exit(1)

    print(f"\npublicado e conferido: carimbo {esperado[0]}, "
          f"{esperado[1]} na fila sem ninguém nas duas abas")
    print(f"https://docs.google.com/spreadsheets/d/{sid}/edit")


if __name__ == "__main__":
    main()
