# -*- coding: utf-8 -*-
"""Publica o relatório completo (.xlsx) numa planilha do Google.

Por que um script e não o conector do Sheets: o conector recebe os valores dentro da
mensagem de quem o chama, e a aba Conversas tem ~35 MB de texto. Com a conta de serviço
o dado vai do disco para o Google direto, sem passar por ninguém no meio.

A conta é a mesma do relatório do N1 (`ultracar-report-chat-ai@…`), reusada por decisão
do usuário em 06/11/2026; a planilha precisa estar compartilhada com ela como Editor.

## Três coisas que o código do N1 já tinha aprendido, e que valem aqui

1. **`values.update` numa faixa calculada, não `values.append`.** O append deixa o
   Google adivinhar onde a tabela termina, e ele erra quando há linhas em branco.
2. **A grade cresce antes da escrita.** Uma aba nova tem 1.000 linhas; `values.update`
   além da grade falha. As Conversas têm 45 mil linhas, então a grade é esticada com
   `appendDimension` antes de qualquer valor.
3. **`USER_ENTERED`**, para data virar data e número virar número em vez de texto.

## E uma deste projeto

A escrita vai em blocos. O limite prático de uma requisição do Sheets é de alguns MB, e
um bloco único de 35 MB é recusado com um 400 que não diz o motivo. `LINHAS_POR_BLOCO`
é conservador de propósito: a diferença de tempo entre 2 mil e 10 mil linhas por bloco é
pequena, e o modo de falha do bloco grande é obscuro.

Uso:
    python pipeline/publicar_relatorio.py                       # o .xlsx mais recente
    python pipeline/publicar_relatorio.py --arquivo <caminho>
    python pipeline/publicar_relatorio.py --sem-transcricao     # sem a coluna pesada
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import sys
import time
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from openpyxl import load_workbook

RAIZ = Path(__file__).resolve().parent.parent
CONFIG = RAIZ / "Ultracar-Support-Bitrix-Analisys" / "appsettings.json"
ESCOPO = ["https://www.googleapis.com/auth/spreadsheets"]
LINHAS_POR_BLOCO = 2000
TENTATIVAS = 4
COLUNA_PESADA = "Conversa"     # ~90% do peso do arquivo


ENV_LOCAL = RAIZ / "local" / "sheets.env"
VAR = "GOOGLE_SHEETS_CREDENTIALS_JSON"


def credencial() -> dict:
    """A chave da conta de serviço, do ambiente ou de `local/sheets.env`.

    Fora do repositório de propósito: é chave PRIVADA, e quem a tem escreve em toda
    planilha compartilhada com a conta — hoje a do relatório e a do N1. O id da
    planilha, que não é segredo, fica no appsettings versionado.

    O nome da variável é o mesmo que o `ultracar-support-ai` usa, para quem já conhece
    um projeto reconhecer o outro.
    """
    bruto = os.environ.get(VAR)
    if not bruto and ENV_LOCAL.exists():
        for linha in ENV_LOCAL.read_text(encoding="utf-8").splitlines():
            linha = linha.strip()
            if linha.startswith(f"{VAR}="):
                bruto = linha[len(VAR) + 1:]
                break
    if not bruto:
        raise SystemExit(
            f"Não achei a credencial.\n"
            f"  Esperava {VAR} no ambiente ou em {ENV_LOCAL}.\n"
            f"  O arquivo não é versionado; num clone novo, copie o valor de\n"
            f"  ultracar-support-ai/Infrastructure.EndInactiveConversations.Job/\n"
            f"  Properties/launchSettings.json")
    try:
        return json.loads(bruto)
    except json.JSONDecodeError as e:
        raise SystemExit(f"{VAR} não é JSON válido: {e}")


def servico():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))["GoogleSheets"]
    cred = service_account.Credentials.from_service_account_info(
        credencial(), scopes=ESCOPO)
    return build("sheets", "v4", credentials=cred, cache_discovery=False), cfg


def com_repeticao(req, oque: str):
    """O Sheets devolve 429 e 503 sob carga; os dois passam na segunda tentativa."""
    for t in range(1, TENTATIVAS + 1):
        try:
            return req.execute()
        except HttpError as e:
            if e.resp.status in (429, 500, 503) and t < TENTATIVAS:
                espera = 2 ** t
                print(f"    {oque}: HTTP {e.resp.status}, repetindo em {espera}s")
                time.sleep(espera)
                continue
            raise


def ler_xlsx(caminho: Path, sem_transcricao: bool) -> dict[str, list[list]]:
    wb = load_workbook(caminho, data_only=True, read_only=True)
    abas: dict[str, list[list]] = {}
    for nome in wb.sheetnames:
        ws = wb[nome]
        linhas = []
        descartar = None
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i == 0 and sem_transcricao and COLUNA_PESADA in row:
                descartar = row.index(COLUNA_PESADA)
            if descartar is not None:
                row = row[:descartar] + row[descartar + 1:]
            # datetime não é serializável em JSON e o Sheets entende a string ISO
            linhas.append([
                v.strftime("%Y-%m-%d %H:%M") if isinstance(v, dt.datetime)
                else v.isoformat() if isinstance(v, dt.date)
                else "" if v is None else v
                for v in row])
        abas[nome] = linhas
    wb.close()
    return abas


def preparar_abas(svc, sid: str, abas: dict[str, list[list]]) -> dict[str, int]:
    """Cria o que falta, apaga o que sobra e estica a grade. Devolve nome -> sheetId."""
    meta = com_repeticao(
        svc.spreadsheets().get(spreadsheetId=sid, fields="sheets.properties"), "get")
    atual = {s["properties"]["title"]: s["properties"] for s in meta["sheets"]}

    pedidos = []
    for nome, linhas in abas.items():
        n_lin, n_col = len(linhas) + 50, max(len(l) for l in linhas) + 2
        if nome not in atual:
            pedidos.append({"addSheet": {"properties": {
                "title": nome,
                "gridProperties": {"rowCount": n_lin, "columnCount": n_col}}}})
        else:
            g = atual[nome].get("gridProperties", {})
            # A grade só cresce aqui. Encolher apagaria dados antes de escrever os
            # novos, e se a escrita falhasse no meio a planilha ficaria pela metade.
            if g.get("rowCount", 0) < n_lin or g.get("columnCount", 0) < n_col:
                pedidos.append({"updateSheetProperties": {
                    "properties": {"sheetId": atual[nome]["sheetId"],
                                   "gridProperties": {
                                       "rowCount": max(g.get("rowCount", 0), n_lin),
                                       "columnCount": max(g.get("columnCount", 0), n_col)}},
                    "fields": "gridProperties.rowCount,gridProperties.columnCount"}})
    if pedidos:
        com_repeticao(svc.spreadsheets().batchUpdate(
            spreadsheetId=sid, body={"requests": pedidos}), "grade")
        meta = com_repeticao(
            svc.spreadsheets().get(spreadsheetId=sid, fields="sheets.properties"), "get")
        atual = {s["properties"]["title"]: s["properties"] for s in meta["sheets"]}
    return {n: p["sheetId"] for n, p in atual.items()}


def escrever(svc, sid: str, nome: str, linhas: list[list]) -> None:
    com_repeticao(svc.spreadsheets().values().clear(
        spreadsheetId=sid, range=f"'{nome}'"), f"limpar {nome}")
    enviadas = 0
    for i in range(0, len(linhas), LINHAS_POR_BLOCO):
        bloco = linhas[i:i + LINHAS_POR_BLOCO]
        faixa = f"'{nome}'!A{i + 1}"
        com_repeticao(svc.spreadsheets().values().update(
            spreadsheetId=sid, range=faixa, valueInputOption="USER_ENTERED",
            body={"values": bloco}), f"{nome} linha {i + 1}")
        enviadas += len(bloco)
        print(f"    {enviadas}/{len(linhas)}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arquivo")
    ap.add_argument("--sem-transcricao", action="store_true",
                    help=f"descarta a coluna '{COLUNA_PESADA}', que é ~90% do peso")
    ap.add_argument("--abas", help="só estas abas, separadas por vírgula")
    ap.add_argument("--sem-formatar", action="store_true",
                    help="só os valores; útil para republicar rápido sem mexer no visual")
    a = ap.parse_args()

    caminho = Path(a.arquivo) if a.arquivo else Path(
        sorted(glob.glob(str(RAIZ / "report" / "relatorio_completo_*.xlsx")))[-1])
    print(f"lendo {caminho.name} ({caminho.stat().st_size / 1e6:.1f} MB)")
    abas = ler_xlsx(caminho, a.sem_transcricao)
    if a.abas:
        quer = {x.strip() for x in a.abas.split(",")}
        abas = {k: v for k, v in abas.items() if k in quer}
    for nome, linhas in abas.items():
        print(f"  {nome:12} {len(linhas):7d} linhas")

    svc, cfg = servico()
    sid = cfg["ReportSpreadsheetId"]
    print(f"\npreparando a grade em {sid}")
    preparar_abas(svc, sid, abas)

    inicio = time.time()
    for nome, linhas in abas.items():
        print(f"  escrevendo {nome}...")
        escrever(svc, sid, nome, linhas)

    # A formatação vem junto de propósito: separada, viraria um segundo comando que
    # alguém esquece de rodar, e a planilha ficaria com dado novo em visual nenhum.
    # Importado aqui dentro porque o formatador importa deste módulo.
    if not a.sem_formatar:
        print("\n  formatando...")
        import formatar_planilha
        formatar_planilha.aplicar(svc, sid, caminho, list(abas))

    print(f"\npronto em {(time.time() - inicio) / 60:.1f} min")
    print(f"https://docs.google.com/spreadsheets/d/{sid}/edit")


if __name__ == "__main__":
    main()
