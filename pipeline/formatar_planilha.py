# -*- coding: utf-8 -*-
"""Dá à planilha do Google o mesmo visual do .xlsx.

Lê a formatação **do próprio arquivo** célula a célula e traduz para a API do Sheets,
em vez de repetir as cores aqui. O motivo é manutenção: as cores e os negritos moram no
`gerar_relatorio_completo.py`, e qualquer mudança lá apareceria na planilha sozinha. Uma
segunda cópia das regras divergiria no primeiro ajuste.

As abas de detalhe são a exceção. Formatar 45 mil linhas célula a célula seriam 640 mil
requisições; nelas o visual é estrutural e vem de regras: cabeçalho, largura de coluna,
painel congelado, filtro e quebra de linha na transcrição.

Uso:
    python pipeline/formatar_planilha.py
    python pipeline/formatar_planilha.py --arquivo <caminho.xlsx>
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "pipeline"))
from publicar_relatorio import com_repeticao, servico  # noqa: E402

# Abas pequenas: formatação fiel, célula a célula. Grandes: por regra.
FIEL = {"Resumo", "Legenda"}
MAX_POR_LOTE = 400          # requisições por batchUpdate; acima disso o Sheets recusa
LARGURA_PADRAO = 7          # o "width" do openpyxl é em caracteres, o Sheets em pixels


def cor(rgb) -> dict | None:
    """'FF1F4E79' ou '1F4E79' -> {red,green,blue} de 0 a 1."""
    if not rgb or not isinstance(rgb, str):
        return None
    h = rgb[-6:]
    if len(h) != 6:
        return None
    try:
        r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    except ValueError:
        return None
    return {"red": round(r, 4), "green": round(g, 4), "blue": round(b, 4)}


def formato_da_celula(c) -> dict | None:
    """O que esta célula tem de diferente do padrão, no vocabulário do Sheets."""
    f: dict = {}
    texto: dict = {}
    if c.font:
        if c.font.bold:
            texto["bold"] = True
        if c.font.italic:
            texto["italic"] = True
        if c.font.size and float(c.font.size) != 11:
            texto["fontSize"] = int(float(c.font.size))
        if c.font.name and "Consolas" in str(c.font.name):
            # as barras do Resumo (█) só alinham em fonte monoespaçada
            texto["fontFamily"] = "Roboto Mono"
        rgb = getattr(c.font.color, "rgb", None) if c.font.color else None
        v = cor(rgb)
        # openpyxl devolve preto para "sem cor"; mandar preto explícito é inofensivo,
        # mas enche o lote à toa
        if v and v != {"red": 0.0, "green": 0.0, "blue": 0.0}:
            texto["foregroundColorStyle"] = {"rgbColor": v}
    if texto:
        f["textFormat"] = texto
    if c.fill and c.fill.fill_type == "solid":
        v = cor(getattr(c.fill.fgColor, "rgb", None))
        if v and v != {"red": 1.0, "green": 1.0, "blue": 1.0}:
            f["backgroundColorStyle"] = {"rgbColor": v}
    if c.alignment:
        if c.alignment.wrap_text:
            f["wrapStrategy"] = "WRAP"
        if c.alignment.vertical == "top":
            f["verticalAlignment"] = "TOP"
        if c.alignment.horizontal in ("center", "right", "left"):
            f["horizontalAlignment"] = c.alignment.horizontal.upper()
    return f or None


def pedidos_fieis(ws, sheet_id: int) -> list[dict]:
    """Uma requisição por célula formatada. Só para abas pequenas."""
    fora = []
    for linha in ws.iter_rows():
        for c in linha:
            f = formato_da_celula(c)
            if not f:
                continue
            fora.append({"repeatCell": {
                "range": {"sheetId": sheet_id,
                          "startRowIndex": c.row - 1, "endRowIndex": c.row,
                          "startColumnIndex": c.column - 1, "endColumnIndex": c.column},
                "cell": {"userEnteredFormat": f},
                "fields": "userEnteredFormat(" + ",".join(f) + ")"}})
    return fora


def pedidos_estruturais(ws, sheet_id: int, n_col: int, n_lin: int) -> list[dict]:
    """Cabeçalho, larguras, painel congelado, filtro e quebra na transcrição."""
    cab = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
    fora: list[dict] = [
        # o cabeçalho é a única linha com formatação própria nas abas grandes
        {"repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1,
                      "startColumnIndex": 0, "endColumnIndex": n_col},
            "cell": {"userEnteredFormat": {
                "textFormat": {"bold": True,
                               "foregroundColorStyle": {"rgbColor": cor("FFFFFF")}},
                "backgroundColorStyle": {"rgbColor": cor("1F4E79")},
                "verticalAlignment": "MIDDLE"}},
            "fields": "userEnteredFormat(textFormat,backgroundColorStyle,"
                      "verticalAlignment)"}},
        # mesmo congelamento do Excel (freeze_panes = "B2"): linha 1 e coluna A
        {"updateSheetProperties": {
            "properties": {"sheetId": sheet_id,
                           "gridProperties": {"frozenRowCount": 1,
                                              "frozenColumnCount": 1}},
            "fields": "gridProperties.frozenRowCount,gridProperties.frozenColumnCount"}},
        {"setBasicFilter": {"filter": {"range": {
            "sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": n_lin,
            "startColumnIndex": 0, "endColumnIndex": n_col}}}},
    ]
    for i in range(1, n_col + 1):
        larg = ws.column_dimensions[get_column_letter(i)].width
        if larg:
            fora.append({"updateDimensionProperties": {
                "range": {"sheetId": sheet_id, "dimension": "COLUMNS",
                          "startIndex": i - 1, "endIndex": i},
                "properties": {"pixelSize": int(float(larg) * LARGURA_PADRAO)},
                "fields": "pixelSize"}})
    if "Conversa" in cab:
        j = cab.index("Conversa")
        # No Excel a transcrição tem wrap e o programa calcula a altura. No Sheets,
        # wrap numa coluna de 45 mil linhas deixa a rolagem pesada e cada linha vira um
        # bloco — CLIP mostra uma régua, e quem quer ler clica na célula.
        fora.append({"repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": 1,
                      "startColumnIndex": j, "endColumnIndex": j + 1},
            "cell": {"userEnteredFormat": {"wrapStrategy": "CLIP",
                                           "verticalAlignment": "TOP"}},
            "fields": "userEnteredFormat(wrapStrategy,verticalAlignment)"}})
    return fora


def aplicar(svc, sid: str, caminho: Path, so_abas: list[str] | None = None) -> int:
    """Formata a planilha a partir do .xlsx. Devolve quantas requisições mandou."""
    meta = com_repeticao(
        svc.spreadsheets().get(spreadsheetId=sid, fields="sheets.properties"), "get")
    ids = {s["properties"]["title"]: s["properties"]["sheetId"] for s in meta["sheets"]}

    wb = load_workbook(caminho, data_only=True)   # sem read_only: precisa dos estilos
    print(f"    formatando a partir de {caminho.name}")
    todos: list[dict] = []
    for nome in wb.sheetnames:
        if so_abas and nome not in so_abas:
            continue
        if nome not in ids:
            print(f"    {nome}: não existe na planilha, pulando")
            continue
        ws = wb[nome]
        if nome in FIEL:
            p = pedidos_fieis(ws, ids[nome])
            print(f"    {nome:12} {len(p):5d} células (fiel ao arquivo)")
        else:
            p = pedidos_estruturais(ws, ids[nome], ws.max_column, ws.max_row)
            print(f"    {nome:12} {len(p):5d} regras (cabeçalho, larguras, filtro)")
        todos += p
    wb.close()

    for i in range(0, len(todos), MAX_POR_LOTE):
        com_repeticao(svc.spreadsheets().batchUpdate(
            spreadsheetId=sid, body={"requests": todos[i:i + MAX_POR_LOTE]}),
            f"lote {i // MAX_POR_LOTE + 1}")
    return len(todos)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arquivo")
    a = ap.parse_args()
    caminho = Path(a.arquivo) if a.arquivo else Path(
        sorted(glob.glob(str(RAIZ / "report" / "relatorio_completo_*.xlsx")))[-1])
    svc, cfg = servico()
    n = aplicar(svc, cfg["ReportSpreadsheetId"], caminho)
    print(f"\n{n} requisições aplicadas")
    print(f"https://docs.google.com/spreadsheets/d/{cfg['ReportSpreadsheetId']}/edit")


if __name__ == "__main__":
    main()
