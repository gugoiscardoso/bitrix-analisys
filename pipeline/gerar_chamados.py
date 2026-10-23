#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Planilha com TODOS os chamados da janela — fiscais e não-fiscais.

    python pipeline/gerar_chamados.py --de 2026-05-01 --ate 2026-08-08

As duas taxonomias vivem separadas e só se encontram aqui, numa coluna 'Escopo':

    Fiscal      -> frente/tema/subgrupo de taxonomia.json (congelada, comparável
                   entre execuções — é o que a skill /build-report produz)
    Não fiscal  -> tema de taxonomia_nao_fiscal.json

Fundir os dois arquivos de taxonomia seria mais simples e estaria errado: quebraria a
comparabilidade do relatório fiscal entre execuções, que é o princípio da skill.
"""
from __future__ import annotations
import argparse, collections, json, re, sys
from datetime import date, datetime
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sanitizar import mascarar_credenciais

RAIZ = Path(__file__).resolve().parent.parent
STORE = RAIZ / "data" / "store"
REPORT = RAIZ / "report"
HDR = PatternFill("solid", fgColor="1F4E79")
FIS = PatternFill("solid", fgColor="2E6B3E")
NAO = PatternFill("solid", fgColor="8A4E10")
HF = Font(color="FFFFFF", bold=True, size=11)
TAG = re.compile(r"\s*\[([^\]]{1,30})\]")
sys.stdout.reconfigure(encoding="utf-8")


def ler(p):
    return json.loads(p.read_text(encoding="utf-8-sig")) if p.exists() else {}


def dias(a, b):
    if not a or not b:
        return None
    try:
        d = (datetime.fromisoformat(b).date() - datetime.fromisoformat(a).date()).days
    except (ValueError, TypeError):
        return None
    return d if d >= 0 else None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--de", required=True)
    ap.add_argument("--ate", default=date.today().isoformat())
    a = ap.parse_args()

    cls = ler(STORE / "classificacao.json")
    nf = ler(STORE / "classificacao_nao_fiscal.json")
    tax = ler(STORE / "taxonomia.json")
    titulos = {f["tag"]: f["titulo"] for f in tax.get("frentes", [])}
    subs_por_frente = collections.defaultdict(set)
    for s in tax.get("subgrupos", []):
        subs_por_frente[s["frente"]].add(s["nome"])

    linhas, sem_cls = [], 0
    with (STORE / "base_historica.jsonl").open(encoding="utf-8") as fh:
        for l in fh:
            r = json.loads(l)
            if r["tipo"] != "chamado" or not (a.de <= r["data"] <= a.ate):
                continue
            m = TAG.match(r.get("titulo") or "")
            tag = m.group(1).strip() if m else ""
            if r["fiscal"]:
                c = cls.get("chamados", {}).get(str(r["id"]))
                if not c:
                    sem_cls += 1
                    continue
                sub = c.get("subgrupo") or ""
                if not sub and c["tema"] in subs_por_frente.get(c.get("frente"), ()):
                    sub = c["tema"]
                fr = c.get("frente")
                linhas.append((r, "Fiscal", tag,
                               f"{fr} — {titulos.get(fr, '')}" if fr else "—",
                               c["tema"], sub))
            else:
                c = nf.get(str(r["id"]))
                if not c:
                    sem_cls += 1
                    linhas.append((r, "Não fiscal", tag, "—", "", ""))
                else:
                    linhas.append((r, "Não fiscal", tag, "—", c["tema"], ""))

    wb = Workbook()
    ws = wb.active
    ws.title = "Chamados"
    COLS = ["Id", "Data", "Mes", "Escopo", "Categoria", "Frente", "Tema", "Subgrupo",
            "Status", "Canal", "TempoTotalDias", "TempoTechDias", "FechadoEm",
            "Cliente", "CNPJ", "Titulo"]
    ws.append(COLS)
    for i, c in enumerate(COLS, 1):
        cel = ws.cell(row=1, column=i)
        cel.font, cel.fill = HF, HDR
        cel.alignment = Alignment(vertical="center", wrap_text=True)
    ws.row_dimensions[1].height = 28

    for r, escopo, tag, frente, tema, sub in sorted(linhas, key=lambda x: x[0]["data"],
                                                    reverse=True):
        ws.append([r["id"], r["data"], r["data"][:7], escopo, tag, frente, tema, sub,
                   r["status"], r["canal"],
                   dias(r.get("criado_em"), r.get("fechado_em")),
                   dias(r.get("inicio_dev"), r.get("alterado_em")),
                   (r.get("fechado_em") or "")[:10],
                   r.get("cliente", ""), r.get("cnpj", ""),
                   mascarar_credenciais(r.get("titulo") or "")[:300]])
        ws.cell(row=ws.max_row, column=4).fill = FIS if escopo == "Fiscal" else NAO
        ws.cell(row=ws.max_row, column=4).font = Font(color="FFFFFF", bold=True)

    larg = {"Id": 10, "Data": 11, "Mes": 9, "Escopo": 12, "Categoria": 15, "Frente": 34,
            "Tema": 46, "Subgrupo": 42, "Status": 15, "Canal": 14, "TempoTotalDias": 12,
            "TempoTechDias": 12, "FechadoEm": 12, "Cliente": 32, "CNPJ": 20, "Titulo": 70}
    for i, c in enumerate(COLS, 1):
        ws.column_dimensions[get_column_letter(i)].width = larg.get(c, 14)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(COLS))}{ws.max_row}"

    ws2 = wb.create_sheet("Resumo")
    ws2.append(["Escopo", "Tema", "Chamados", "% do escopo"])
    for c in ws2[1]:
        c.font, c.fill = HF, HDR
    agg = collections.Counter((e, t or "(sem classificação)") for _, e, _, _, t, _ in linhas)
    tot = collections.Counter(e for e, _ in agg.elements() if True)
    tot = collections.Counter()
    for (e, _), n in agg.items():
        tot[e] += n
    for (e, t), n in sorted(agg.items(), key=lambda x: (x[0][0], -x[1])):
        ws2.append([e, t, n, f"{n/tot[e]*100:.1f}%"])
    for i, w in enumerate([14, 60, 12, 12], 1):
        ws2.column_dimensions[get_column_letter(i)].width = w
    ws2.freeze_panes = "A2"

    REPORT.mkdir(exist_ok=True)
    saida = REPORT / f"chamados_completo_{a.de}_{a.ate}.xlsx"
    wb.save(saida)
    nfis = sum(1 for _, e, _, _, _, _ in linhas if e == "Fiscal")
    print(f"Janela {a.de} a {a.ate}")
    print(f"  {len(linhas)} chamados ({nfis} fiscais, {len(linhas)-nfis} não-fiscais)")
    if sem_cls:
        print(f"  {sem_cls} ainda sem classificação")
    print(f"\n  {saida.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
