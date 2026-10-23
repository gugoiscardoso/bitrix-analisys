# -*- coding: utf-8 -*-
"""
Relatório da V3 — chamados e conversas da nova versão, sem filtro por módulo.

    python pipeline/gerar_relatorio_v3.py --de 2026-09-01 --ate 2026-10-23

Produz um arquivo em report/, com quatro abas:
    Resumo                   frente e módulo, chamados x conversas
    Chamados                 os registros versao=V3, linha a linha
    Conversas                idem
    Melhorias V2 para a V3   os versao=V3-backlog, fora da contagem principal

Um arquivo só porque são dezenas de registros. Separar executivo de base nessa escala
produz dois arquivos que o leitor abre e fecha.

Janela pura, igual ao relatório fiscal: só entra registro com data dentro de [de, ate].
"""
from __future__ import annotations
import argparse
import collections
import json
import re
import sys
from datetime import date
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

RAIZ = Path(__file__).resolve().parent.parent
STORE = RAIZ / "data" / "store"
REPORT = RAIZ / "report"

HDR = PatternFill("solid", fgColor="1F4E79")
HF = Font(color="FFFFFF", bold=True, size=11)
GRP = PatternFill("solid", fgColor="EAF0F6")

# Nome das colunas do board do grupo 139, para o leitor não ver só o id.
# Id desconhecido cai no próprio número — nada é descartado por não estar na lista.
COLUNAS = {
    "1445": "Chamados Concluídos", "1573": "Nível 1 - Suporte", "1731": "Validação com clientes",
    "1733": "Retorno com erro Devs", "1739": "Aguardando Suporte/CS", "1837": "TecnoSpeed",
    "2301": "Análise de Melhoria", "2727": "Pré-Análise", "2917": "Off-Sprint",
    "2993": "Retornar ao Cliente", "3043": "Backlog Futuras Sprints", "3097": "Ativação CORe",
    "3167": "Pronto para Produção", "3357": "Nova Versão", "3407": "Sprint 29/10",
    "3409": "Chamados Suporte - Ação Setembro", "3441": "Rollout - Nova Versão",
    "3443": "Validação com cliente - Rollout", "3483": "Chamados Concluídos - Nova Versão",
    "3501": "Sprint 12/11",
}

BITRIX = "https://ultracar.bitrix24.com/workgroups/group/139/tasks/task/view/{}/"

sys.stdout.reconfigure(encoding="utf-8")


def ler(p: Path, padrao=None):
    if not p.exists():
        return padrao
    return json.loads(p.read_text(encoding="utf-8-sig"))


def carregar(de: str, ate: str):
    """V3 obedece a janela pura. O backlog obedece só o 'ate', de propósito.

    O backlog é melhoria pedida sobre a V2 e endereçada para a nova versão: por
    natureza ela nasce antes do rollout. Cortar pelo 'de' esconderia justamente as
    mais antigas, que são contexto do relatório e não medida dele.
    """
    v3, backlog = [], []
    with (STORE / "base_historica.jsonl").open(encoding="utf-8") as fh:
        for linha in fh:
            r = json.loads(linha)
            if r.get("versao") == "V3" and de <= r["data"] <= ate:
                v3.append(r)
            elif r.get("versao") == "V3-backlog" and r["data"] <= ate:
                backlog.append(r)
    return v3, backlog


def rotulo(c: dict) -> str:
    """'R3 Lacuna de paridade'. Rótulo de serviço tem código igual ao nome, não repete."""
    cod, nome = c.get("frente", ""), c.get("frente_nome", "")
    return nome if cod == nome else f"{cod} {nome}".strip()


def cabecalho(ws, cols, larguras):
    ws.append(cols)
    for c in ws[1]:
        c.fill, c.font = HDR, HF
        c.alignment = Alignment(vertical="center", wrap_text=True)
    for i, w in enumerate(larguras, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A2"


def finalizar(ws, n_cols):
    ws.auto_filter.ref = f"A1:{get_column_letter(n_cols)}{ws.max_row}"


def aba_resumo(wb, v3, cls, tax, de, ate, servico):
    ws = wb.active
    ws.title = "Resumo"
    frentes = {v["codigo"]: v for v in
               next(e for e in tax["eixos"] if e["nome"] == "frente")["valores"]}

    def rot(r):
        grupo = "chamados" if r["tipo"] == "chamado" else "conversas"
        return cls[grupo].get(str(r["id"]), {})

    uteis = [r for r in v3 if rot(r).get("frente") not in servico]
    fora = [r for r in v3 if rot(r).get("frente") in servico]

    ws.append([f"Relatório V3 — {de} a {ate}"])
    ws["A1"].font = Font(bold=True, size=14)
    ws.append([])
    ws.append(["Chamados", sum(1 for r in uteis if r["tipo"] == "chamado"),
               "Conversas", sum(1 for r in uteis if r["tipo"] == "conversa")])
    for c in ("A3", "C3"):
        ws[c].font = Font(bold=True)
    rotulados = collections.Counter(rot(r).get("frente") for r in fora)
    ws.append(["Fora da contagem", "; ".join(f"{k}: {v}" for k, v in sorted(rotulados.items()))
                                   or "nenhum"])
    ws["A4"].font = Font(bold=True)
    ws.append([])

    linha = ws.max_row + 1
    ws.append(["Frente", "O que é", "Chamados", "Conversas", "Total", "Peso"])
    for c in ws[linha]:
        c.fill, c.font = HDR, HF
        c.alignment = Alignment(vertical="center", wrap_text=True)

    por_frente = collections.Counter((rot(r).get("frente"), r["tipo"]) for r in uteis)
    total = len(uteis)
    for cod in sorted(frentes):
        nc = por_frente[(cod, "chamado")]
        nv = por_frente[(cod, "conversa")]
        if not (nc or nv):
            continue
        ws.append([f"{cod} {frentes[cod]['nome']}", frentes[cod]["definicao"],
                   nc, nv, nc + nv, round((nc + nv) / total, 3) if total else 0])
        ws.cell(row=ws.max_row, column=6).number_format = "0.0%"
        ws.cell(row=ws.max_row, column=2).alignment = Alignment(wrap_text=True, vertical="top")

    ws.append([])
    linha = ws.max_row + 1
    ws.append(["Módulo", "", "Chamados", "Conversas", "Total", ""])
    for c in ws[linha]:
        c.fill, c.font = HDR, HF
    por_mod = collections.Counter((rot(r).get("modulo"), r["tipo"]) for r in uteis)
    mods = sorted({m for m, _ in por_mod},
                  key=lambda m: -(por_mod[(m, "chamado")] + por_mod[(m, "conversa")]))
    for m in mods:
        nc, nv = por_mod[(m, "chamado")], por_mod[(m, "conversa")]
        ws.append([m, "", nc, nv, nc + nv, ""])

    for col, w in zip("ABCDEF", (38, 78, 11, 11, 9, 9)):
        ws.column_dimensions[col].width = w


def aba_chamados(wb, v3, cls, de, ate):
    ws = wb.create_sheet("Chamados")
    cols = ["Id", "Abrir no Bitrix", "Data", "Frente", "Módulo", "Status", "Coluna do board",
            "Cliente", "CNPJ", "Fiscal", "Dias em aberto", "Tags", "Título"]
    cabecalho(ws, cols, (9, 16, 11, 26, 24, 14, 30, 34, 20, 8, 13, 40, 95))
    hoje = date.fromisoformat(ate)
    for r in sorted((x for x in v3 if x["tipo"] == "chamado"), key=lambda x: x["data"]):
        c = cls["chamados"].get(str(r["id"]), {})
        abertos = (hoje - date.fromisoformat(r["data"])).days if not r.get("fechado_em") else None
        ws.append([r["id"], "abrir", r["data"],
                   rotulo(c),
                   c.get("modulo", ""), r.get("status", ""),
                   COLUNAS.get(str(r.get("stage")), str(r.get("stage") or "")),
                   r.get("cliente", ""), r.get("cnpj", ""),
                   "Sim" if r.get("fiscal") else "", abertos,
                   ", ".join(r.get("tags") or []),
                   re.sub(r"\s+", " ", r.get("titulo", ""))[:300]])
        cel = ws.cell(row=ws.max_row, column=2)
        cel.hyperlink = BITRIX.format(r["id"])
        cel.font = Font(color="0563C1", underline="single")
    finalizar(ws, len(cols))


def aba_conversas(wb, v3, cls):
    ws = wb.create_sheet("Conversas")
    cols = ["Id", "Data", "Frente", "Módulo", "Canal", "Linha de entrada", "Duração (min)",
            "Mensagens", "Operador", "Cliente", "Fiscal", "Resumo da conversa"]
    cabecalho(ws, cols, (10, 11, 26, 24, 11, 15, 13, 11, 20, 32, 8, 110))
    for r in sorted((x for x in v3 if x["tipo"] == "conversa"), key=lambda x: x["criado_em"]):
        c = cls["conversas"].get(str(r["id"]), {})
        entrada = "V3 (linha 17)" if str(r.get("linha")) == "17" else "V2 (transferida)"
        ws.append([r["id"], r["data"],
                   rotulo(c),
                   c.get("modulo", ""), r.get("canal", ""), entrada,
                   r.get("duracao_min"), r.get("mensagens"), r.get("operador", ""),
                   r.get("cliente", ""), "Sim" if r.get("fiscal") else "",
                   re.sub(r"\s+", " ", r.get("texto", ""))[:600]])
    finalizar(ws, len(cols))


def aba_backlog(wb, backlog, ate):
    ws = wb.create_sheet("Melhorias V2 para a V3")
    ws.append(["Chamado de cliente da V2 marcado com a tag novaversao: a melhoria foi pedida "
               "sobre a versão antiga e está endereçada para a nova. Conta como V2 nos números "
               "e aparece aqui só como contexto. Esta aba ignora a data inicial da janela, "
               "porque esse tipo de pedido nasce antes do rollout."])
    ws["A1"].font = Font(italic=True)
    ws.append([])
    linha = ws.max_row + 1
    cols = ["Id", "Abrir no Bitrix", "Data", "Status", "Coluna do board", "Cliente", "Título"]
    ws.append(cols)
    for c in ws[linha]:
        c.fill, c.font = HDR, HF
    hoje = date.fromisoformat(ate)
    for r in sorted(backlog, key=lambda x: x["data"]):
        ws.append([r["id"], "abrir", r["data"], r.get("status", ""),
                   COLUNAS.get(str(r.get("stage")), str(r.get("stage") or "")),
                   r.get("cliente", ""),
                   re.sub(r"\s+", " ", r.get("titulo", ""))[:300]])
        cel = ws.cell(row=ws.max_row, column=2)
        cel.hyperlink = BITRIX.format(r["id"])
        cel.font = Font(color="0563C1", underline="single")
    for col, w in zip("ABCDEFG", (9, 16, 11, 14, 30, 34, 95)):
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "A4"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--de", required=True)
    ap.add_argument("--ate", default=date.today().isoformat())
    a = ap.parse_args()

    tax = ler(STORE / "taxonomia_v3.json")
    cls = ler(STORE / "classificacao_v3.json", {"chamados": {}, "conversas": {}})
    servico = {r["nome"] for r in tax["rotulos_de_servico"]}

    v3, backlog = carregar(a.de, a.ate)

    falta = [r for r in v3
             if str(r["id"]) not in cls["chamados" if r["tipo"] == "chamado" else "conversas"]]
    if falta:
        print(f"ABORTADO: {len(falta)} registro(s) V3 sem classificação. "
              f"Rode classificar_v3.py antes. Ex: {[r['id'] for r in falta[:5]]}")
        return 1

    print(f"Janela {a.de} a {a.ate}")
    print(f"  {len(v3)} registros V3 "
          f"({sum(1 for r in v3 if r['tipo'] == 'chamado')} chamados, "
          f"{sum(1 for r in v3 if r['tipo'] == 'conversa')} conversas)")
    print(f"  {len(backlog)} melhorias V2 endereçadas para a V3")

    wb = Workbook()
    aba_resumo(wb, v3, cls, tax, a.de, a.ate, servico)
    aba_chamados(wb, v3, cls, a.de, a.ate)
    aba_conversas(wb, v3, cls)
    aba_backlog(wb, backlog, a.ate)

    REPORT.mkdir(exist_ok=True)
    saida = REPORT / f"relatorio_v3_{a.de}_{a.ate}.xlsx"
    wb.save(saida)
    print(f"\n  {saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
