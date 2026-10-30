# -*- coding: utf-8 -*-
"""
Relatório único de suporte Ultracar: V2 e V3 no mesmo arquivo.

    python pipeline/gerar_relatorio_completo.py --de 2026-01-01 --ate 2026-10-30
    python pipeline/gerar_relatorio_completo.py --de 2026-01-01 --ate 2026-10-30 --amostra 1500

Nasce de uma restrição que não se contorna escrevendo código: existem QUATRO
vocabulários de classificação nesta base, e eles não se cruzam.

    Fiscal V2             13 frentes (P1..P13) -> temas -> subgrupos
    Não-fiscal chamados   11 temas planos
    Não-fiscal conversas  12 temas planos, lista DIFERENTE da de chamados
    V3                    frentes R1..R6 (+ módulo)

Por isso o Resumo é em camadas, não uma tabela só. Juntar os quatro numa coluna
única exigiria inventar um mapeamento entre eles; o número sairia mais simples e
seria ficção.

As duas primeiras camadas — versão, e natureza fiscal/não-fiscal dentro dela —
saem de campos que o coletor grava, não de leitura. Elas já são FINAIS mesmo com a
classificação incompleta. Só a terceira camada, a das categorias, depende de ter
lido o registro, e a aba Cobertura diz quanto de cada bloco já foi lido.
"""
from __future__ import annotations
import argparse
import collections
import json
import re
import sys
import unicodedata
from datetime import date, datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sanitizar import mascarar_credenciais

RAIZ = Path(__file__).resolve().parent.parent
STORE = RAIZ / "data" / "store"
REPORT = RAIZ / "report"

HDR = PatternFill("solid", fgColor="1F4E79")
HF = Font(color="FFFFFF", bold=True, size=11)
GRP = PatternFill("solid", fgColor="EAF0F6")
AVISO = PatternFill("solid", fgColor="FDF2CF")
CHAM = PatternFill("solid", fgColor="2E6B3E")
CONV = PatternFill("solid", fgColor="6B4E8F")
BORDA = Border(bottom=Side(style="thin", color="D5DEE6"))

# Rótulo do vocabulário que classificou o registro. Vai numa coluna própria porque
# comparar categoria entre vocabulários diferentes não significa nada, e quem abre a
# planilha precisa ver isso sem ler a legenda.
VOC_FISCAL = "Fiscal V2 (P1–P13)"
VOC_NAOFIS = "Não-fiscal V2 (temas)"
VOC_V3 = "V3 (R1–R6)"
VOC_NADA = "— não lido"

sys.stdout.reconfigure(encoding="utf-8")


TAG_TITULO = re.compile(r"\s*\[([^\]]{1,40})\]")
SEM_MODULO = "(a determinar na leitura)"


def ler(p: Path):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def chave(s: str) -> str:
    """Sem acento e sem caixa: [ESTOQUE] e [Gestão de pátio] têm de bater com o mapa."""
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c)).strip().lower()


def pct(parte: int, todo: int) -> str:
    """Percentual com vírgula decimal — a planilha é lida em português."""
    return f"{parte / todo * 100:.1f}".replace(".", ",") + "%" if todo else "—"


def barra(p: float) -> str:
    return "█" * min(max(1, round(p / 4)), 12) + f"  {p:.0f}%"


# ─────────────────────── carga ───────────────────────

class Modulos:
    """Resolve o eixo módulo — 'onde no produto' — para os registros da V2.

    É o único eixo que atravessa V2 e V3: os quatro vocabulários discordam sobre QUE
    TIPO de fricção é, mas concordam sobre ONDE ela acontece. Nada aqui é heurística
    sobre o registro; é propriedade do rótulo, então todo registro com aquele rótulo
    recebe o mesmo módulo e o resultado é auditável em modulo_por_rotulo.json.
    """

    def __init__(self):
        m = ler(STORE / "modulo_por_rotulo.json")
        self.versao = m["versao"]
        self.validos = m["modulos_validos"]
        self.colchete = {chave(k): v for k, v in m["colchete_do_titulo"].items()}
        self.por_tema = {"chamado": {chave(k): v for k, v in m["tema_chamado"].items()},
                         "conversa": {chave(k): v for k, v in m["tema_conversa"].items()}}
        self.vazios = {chave(x) for x in m["tema_sem_assunto"]}
        self.falso_fiscal = chave(m["tema_falso_positivo_fiscal"])
        self.desacordo = 0

    def resolver(self, r: dict, tema: str, fiscal_lido: bool) -> tuple[str, str]:
        """(módulo, de onde veio). Vazio quando só a leitura resolve.

        `fiscal_lido` diz se a classificação fiscal confirmou o registro. Campo fiscal
        ligado mas lido como falso positivo NÃO vira módulo Fiscal: inflaria o maior
        bloco do relatório com registro que o próprio classificador desmentiu.
        """
        if chave(tema) in self.vazios:
            return "(sem assunto)", "tema vazio"
        if r.get("fiscal") and fiscal_lido:
            return "Fiscal", "definição"
        por_colchete = None
        if r["tipo"] == "chamado":
            m = TAG_TITULO.match(r.get("titulo") or "")
            if m:
                por_colchete = self.colchete.get(chave(m.group(1)))
        por_tema = self.por_tema[r["tipo"]].get(chave(tema))
        if por_colchete and por_tema and por_colchete != por_tema:
            self.desacordo += 1
        if por_colchete:
            return por_colchete, "colchete do título"
        if por_tema:
            return por_tema, "tema"
        return "", ""


def carregar(de: str, ate: str):
    """Anexa a cada registro da janela o rótulo do vocabulário que o classificou.

    Prioridade V3 -> fiscal -> não-fiscal. A `natureza` vem SEMPRE do campo fiscal da
    base, nunca do arquivo em que a classificação foi parar: os dois discordam em
    algumas dezenas de registros, e a base é quem manda. A aba Cobertura conta a
    divergência em vez de escondê-la.
    """
    fis = ler(STORE / "classificacao.json")
    v3 = ler(STORE / "classificacao_v3.json")
    nf = {"chamado": ler(STORE / "classificacao_nao_fiscal.json"),
          "conversa": ler(STORE / "classificacao_nao_fiscal_conv.json")}
    tax = ler(STORE / "taxonomia.json")
    tax_v3 = ler(STORE / "taxonomia_v3.json")
    mods = Modulos()

    subs_por_frente = collections.defaultdict(set)
    for s in tax["subgrupos"]:
        subs_por_frente[s["frente"]].add(s["nome"])

    regs = []
    with (STORE / "base_historica.jsonl").open(encoding="utf-8") as fh:
        for linha in fh:
            r = json.loads(linha)
            if not (de <= r["data"] <= ate):
                continue
            # `chv`, não `chave`: esse nome é a função de normalização lá em cima, e
            # sombreá-la aqui deixaria uma armadilha para a próxima edição.
            chv = "chamados" if r["tipo"] == "chamado" else "conversas"
            idt = str(r["id"])
            r["natureza"] = "Fiscal" if r.get("fiscal") else "Não-fiscal"
            r |= {"vocab": VOC_NADA, "categoria": "", "categoria_nome": "",
                  "tema": "", "subgrupo": "", "modulo": "", "modulo_fonte": "",
                  "divergente": False}

            c = v3[chv].get(idt) if r.get("versao") == "V3" else None
            if c:
                frente = c.get("frente", "")
                r |= {"vocab": VOC_V3, "categoria": frente,
                      "categoria_nome": c.get("frente_nome", frente),
                      "tema": c.get("frente_nome", ""), "modulo": c.get("modulo", ""),
                      "modulo_fonte": "leitura (V3)"}
                regs.append(r)
                continue

            c = fis[chv].get(idt)
            if c:
                sub = c.get("subgrupo", "")
                # Frente de tema único: o subgrupo é o próprio tema. Derivado da
                # taxonomia, não de "== P9" fixo — ver gerar_relatorio.py.
                if not sub and c["tema"] in subs_por_frente.get(c.get("frente"), ()):
                    sub = c["tema"]
                fr = c.get("frente") or ""
                r |= {"vocab": VOC_FISCAL, "categoria": fr, "categoria_nome": fr,
                      "tema": c["tema"], "subgrupo": sub,
                      "divergente": not r.get("fiscal")}
                # Só conta como fiscal confirmado quem o classificador não desmentiu.
                mod, fonte = mods.resolver(
                    r, c["tema"], chave(c["tema"]) != mods.falso_fiscal)
                r |= {"modulo": mod, "modulo_fonte": fonte}
                regs.append(r)
                continue

            c = nf[r["tipo"]].get(idt)
            if c:
                r |= {"vocab": VOC_NAOFIS, "categoria": c["tema"],
                      "categoria_nome": c["tema"], "tema": c["tema"],
                      "divergente": bool(r.get("fiscal"))}
            # Não lido também passa aqui: o colchete do título resolve o módulo de
            # muitos chamados sem custo de leitura nenhum. `c is None` significa que
            # nada contradiz o campo fiscal da base — ter caído na classificação
            # não-fiscal é o que o contradiz.
            mod, fonte = mods.resolver(r, r["tema"], fiscal_lido=c is None)
            r |= {"modulo": mod, "modulo_fonte": fonte}
            regs.append(r)
    return regs, tax, tax_v3, mods


def grupo_versao(r: dict) -> str:
    """V3-backlog conta como V2 nos blocos de categoria.

    É melhoria pedida por cliente que ainda está na V2 — a convenção já vale em
    gerar_relatorio.py. A camada 1 do Resumo mostra os três valores separados, para
    que a soma continue auditável.
    """
    return "V3" if r.get("versao") == "V3" else "V2"


# ─────────────────────── Resumo ───────────────────────

def rotulo(r: dict, titulos: dict) -> str:
    """Como a categoria do registro aparece no Resumo.

    Fiscal sem frente NÃO é "sem categoria": tem tema, e é o tema que informa. A maior
    fatia ali é conversa vazia — 3.9 mil registros que virariam um balde anônimo e
    sumiriam da leitura de quem decide."""
    if r["vocab"] == VOC_V3:
        # Rótulo de serviço ("Sem conteúdo útil") tem código igual ao nome: não é
        # frente, é marcação. Repetir os dois daria "Sem conteúdo útil — Sem conteúdo útil".
        if not r["categoria"] or r["categoria"] == r["categoria_nome"]:
            return r["categoria_nome"] or r["categoria"]
        return f"{r['categoria']} — {r['categoria_nome']}"
    if r["vocab"] == VOC_FISCAL:
        if r["categoria"]:
            return f"{r['categoria']} — {titulos.get(r['categoria'], '')}"
        return f"(sem frente) {r['tema']}" if r["tema"] else "(sem categoria)"
    return r["categoria"] or "(sem categoria)"


def aba_resumo(wb, regs, tax, de, ate, extracao, amostra):
    ws = wb.active
    ws.title = "Resumo"
    titulos = {f["tag"]: f["titulo"] for f in tax["frentes"]}
    fmt = lambda d: datetime.fromisoformat(d).strftime("%d/%m/%Y")  # noqa: E731

    ws.append([f"Suporte Ultracar — {fmt(de)} a {fmt(ate)}"])
    ws["A1"].font = Font(bold=True, size=14, color="1F4E79")
    ws.append([f"Extraído em {extracao}. Chamados, conversas do chat e WhatsApp, "
               "V2 e V3 no mesmo arquivo."])

    nao_lidos = sum(1 for r in regs if r["vocab"] == VOC_NADA)
    if nao_lidos:
        ws.append([])
        ws.append([f"PRÉVIA — {nao_lidos} dos {len(regs)} registros ({pct(nao_lidos, len(regs))}) "
                   "ainda não foram classificados. As camadas 1 e 2 abaixo já são FINAIS: "
                   "versão e natureza vêm do coletor, não de leitura. A camada 3, das "
                   "categorias, é a que muda quando a leitura terminar — a aba Cobertura "
                   "mostra quanto falta em cada bloco."])
        cel = ws[f"A{ws.max_row}"]
        cel.font = Font(bold=True, color="8A4E10")
        cel.fill = AVISO
        cel.alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[ws.max_row].height = 46
    if amostra:
        ws.append([f"As abas de detalhe trazem uma AMOSTRA de {amostra} linhas cada, "
                   "distribuída por todo o período, só para validar o formato. "
                   "A execução final traz todas as linhas."])
        cel = ws[f"A{ws.max_row}"]
        cel.font = Font(bold=True, color="9C2119")
        cel.fill = AVISO
        cel.alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[ws.max_row].height = 30

    def titulo(txt):
        ws.append([])
        ws.append([txt])
        ws[f"A{ws.max_row}"].font = Font(bold=True, size=12, color="1F4E79")

    def cabecalho(cols):
        ws.append(cols)
        for c in ws[ws.max_row]:
            if c.value is not None:
                c.fill, c.font = HDR, HF

    def conta(sel):
        ch = sum(1 for r in sel if r["tipo"] == "chamado")
        return ch, len(sel) - ch

    # ── camada 1: versão ──
    titulo("1 — Versão   (final: vem do coletor, não depende de leitura)")
    cabecalho(["Versão", "Chamados", "Conversas", "Total", "% do período"])
    for v in ("V2", "V3-backlog", "V3"):
        sel = [r for r in regs if r.get("versao") == v]
        if not sel:
            continue
        ch, cv = conta(sel)
        ws.append([v, ch, cv, len(sel), pct(len(sel), len(regs))])
    ch, cv = conta(regs)
    ws.append(["TOTAL", ch, cv, len(regs), "100,0%"])
    for c in ws[ws.max_row]:
        c.font = Font(bold=True)
        c.fill = GRP

    # ── camada 2: natureza dentro da versão ──
    titulo("2 — Natureza, dentro de cada versão   (final, mesma razão)")
    cabecalho(["Versão", "Natureza", "Chamados", "Conversas", "Total", "% da versão"])
    for g in ("V2", "V3"):
        base = [r for r in regs if grupo_versao(r) == g]
        for nat in ("Fiscal", "Não-fiscal"):
            sel = [r for r in base if r["natureza"] == nat]
            if not sel:
                continue
            ch, cv = conta(sel)
            ws.append([g, nat, ch, cv, len(sel), pct(len(sel), len(base))])
    ws.append(["", "V3-backlog está somado em V2: é melhoria pedida por cliente que "
                   "ainda está na V2.", "", "", "", ""])
    ws[f"B{ws.max_row}"].font = Font(italic=True, size=9, color="606060")

    # ── camada 3: módulo, a única tabela que atravessa V2 e V3 ──
    titulo("3 — Módulo: onde no produto   (V2 e V3 na mesma tabela)")
    com_mod = [r for r in regs if r["modulo"]]
    ws.append([f"{len(com_mod)} dos {len(regs)} registros ({pct(len(com_mod), len(regs))}) "
               "já têm módulo. O resto está em '(a determinar na leitura)'. Esta é a "
               "única camada em que V2 e V3 são comparáveis categoria a categoria: os "
               "vocabulários discordam sobre QUE TIPO de fricção é, mas concordam sobre "
               "ONDE ela acontece."])
    ws[f"A{ws.max_row}"].font = Font(italic=True, size=9, color="606060")
    ws[f"A{ws.max_row}"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[ws.max_row].height = 42
    cabecalho(["Módulo", "V2 chamados", "V2 conversas", "V3", "Total", "% do período"])
    agg = collections.defaultdict(lambda: [0, 0, 0])
    for r in regs:
        m = r["modulo"] or SEM_MODULO
        if grupo_versao(r) == "V3":
            agg[m][2] += 1
        else:
            agg[m][0 if r["tipo"] == "chamado" else 1] += 1
    ordenado = sorted(agg.items(), key=lambda x: -sum(x[1]))
    for m, (a, b, c3) in ordenado:
        tot = a + b + c3
        ws.append([m, a, b, c3, tot, pct(tot, len(regs))])
        if m in (SEM_MODULO, "(sem assunto)"):
            for cel in ws[ws.max_row]:
                cel.font = Font(italic=True, color="808080")

    # ── camada 4: categoria, um bloco por vocabulário ──
    titulo("4 — Categoria   (um bloco por vocabulário; não compare entre blocos)")
    blocos = [
        ("V2 · Fiscal — frentes P1 a P13",
         [r for r in regs if grupo_versao(r) == "V2" and r["natureza"] == "Fiscal"],
         VOC_FISCAL),
        ("V2 · Não-fiscal — temas de CHAMADO",
         [r for r in regs if grupo_versao(r) == "V2" and r["natureza"] == "Não-fiscal"
          and r["tipo"] == "chamado"], VOC_NAOFIS),
        ("V2 · Não-fiscal — temas de CONVERSA  (lista própria, não é a de chamado)",
         [r for r in regs if grupo_versao(r) == "V2" and r["natureza"] == "Não-fiscal"
          and r["tipo"] == "conversa"], VOC_NAOFIS),
        ("V3 — frentes R1 a R6",
         [r for r in regs if grupo_versao(r) == "V3"], VOC_V3),
    ]
    for nome, sel, voc in blocos:
        lidos = [r for r in sel if r["vocab"] == voc]
        # "Teste interno" é conversa aberta pelo próprio time da Ultracar para testar o
        # canal. A taxonomia da V3 manda deixá-la fora de toda contagem, e o relatório
        # diário já faz isso — aqui segue a mesma regra, para os dois baterem.
        teste = sum(1 for r in lidos if r["categoria_nome"] == "Teste interno")
        lidos = [r for r in lidos if r["categoria_nome"] != "Teste interno"]
        ws.append([])
        ws.append([nome])
        ws[f"A{ws.max_row}"].font = Font(bold=True)
        ws[f"A{ws.max_row}"].fill = GRP
        # O teste interno sai do denominador também: contá-lo como "falta ler" diria
        # que resta trabalho onde não resta — ele foi lido e excluído por regra.
        no_bloco = len(sel) - teste
        nota = (f"{no_bloco} registros no bloco · {len(lidos)} lidos "
                f"({pct(len(lidos), no_bloco)}) · os percentuais abaixo são sobre os lidos")
        if teste:
            nota += (f" · {teste} conversa(s) de teste interno do time Ultracar ficaram "
                     "fora, como manda a taxonomia")
        ws.append([nota])
        ws[f"A{ws.max_row}"].font = Font(italic=True, size=9, color="606060")
        if not lidos:
            ws.append(["(nada lido ainda neste bloco)"])
            continue
        cabecalho(["Categoria", "Chamados", "Conversas", "Total", "% do bloco lido"])
        agg = collections.defaultdict(lambda: [0, 0])
        for r in lidos:
            agg[rotulo(r, titulos)][0 if r["tipo"] == "chamado" else 1] += 1
        for rot, (a, b) in sorted(agg.items(), key=lambda x: -(x[1][0] + x[1][1])):
            p = (a + b) / len(lidos) * 100
            ws.append([rot, a, b, a + b, barra(p)])
            ws[f"E{ws.max_row}"].font = Font(name="Consolas", size=10, bold=p >= 15,
                                             color="1F4E79" if p >= 15 else "3D83B8")

    for col, w in (("A", 72), ("B", 12), ("C", 12), ("D", 10), ("E", 16), ("F", 14)):
        ws.column_dimensions[col].width = w
    for row in ws.iter_rows(min_col=1, max_col=1):
        if row[0].value and not row[0].alignment.wrap_text:
            row[0].alignment = Alignment(vertical="top")


# ─────────────────────── abas de detalhe ───────────────────────

COLS_CH = ["Id", "Versão", "Natureza", "Módulo", "Origem do módulo", "Vocabulário",
           "Categoria", "Tema", "Subgrupo", "Data", "Mês", "Canal", "Status",
           "Cliente", "CNPJ", "Título"]
COLS_CV = ["Id", "Versão", "Natureza", "Módulo", "Origem do módulo", "Vocabulário",
           "Categoria", "Tema", "Subgrupo", "Data", "Mês", "Canal", "Duração (min)",
           "Mensagens", "Operador", "Cliente", "Texto"]


def amostrar(sel: list[dict], n: int) -> list[dict]:
    """Amostra espalhada pelo período inteiro, não as N mais recentes.

    O objetivo é validar formato: uma fatia só de outubro não mostraria como fica
    janeiro, nem a variedade de vocabulário."""
    if not n or len(sel) <= n:
        return sel
    passo = len(sel) / n
    return [sel[int(i * passo)] for i in range(n)]


def aba_detalhe(wb, regs, tipo, amostra):
    sel = sorted((r for r in regs if r["tipo"] == tipo),
                 key=lambda x: (x["data"], x["id"]), reverse=True)
    total = len(sel)
    sel = amostrar(sel, amostra)
    nome = {"chamado": "Chamados", "conversa": "Conversas"}[tipo]
    if amostra and len(sel) < total:
        nome += " (amostra)"
    ws = wb.create_sheet(nome)
    cols = COLS_CH if tipo == "chamado" else COLS_CV
    ws.append(cols)
    for i, c in enumerate(cols, 1):
        cel = ws.cell(row=1, column=i)
        cel.font = HF
        cel.fill = CHAM if tipo == "chamado" else CONV
        if c in ("Versão", "Natureza", "Módulo", "Origem do módulo", "Vocabulário",
                 "Categoria"):
            cel.fill = HDR

    for r in sel:
        comum = [r["id"], r.get("versao", "V2"), r["natureza"],
                 r["modulo"] or SEM_MODULO, r["modulo_fonte"] or "—", r["vocab"],
                 r["categoria"] or "—", r["tema"], r["subgrupo"],
                 r["data"], r["data"][:7], r.get("canal", "")]
        if tipo == "chamado":
            ws.append(comum + [r.get("status", ""), r.get("cliente", ""),
                               r.get("cnpj", ""),
                               mascarar_credenciais(r.get("titulo") or "")[:900]])
        else:
            ws.append(comum + [r.get("duracao_min", ""), r.get("mensagens", ""),
                               r.get("operador", ""), r.get("cliente", ""),
                               mascarar_credenciais(r.get("texto") or "")[:900]])

    larg = {"Id": 10, "Versão": 12, "Natureza": 12, "Vocabulário": 20, "Categoria": 13,
            "Tema": 48, "Subgrupo": 44, "Módulo": 24, "Origem do módulo": 17,
            "Data": 11, "Mês": 9, "Canal": 14,
            "Status": 13, "Cliente": 28, "CNPJ": 18, "Título": 70,
            "Duração (min)": 12, "Mensagens": 11, "Operador": 18, "Texto": 70}
    for i, c in enumerate(cols, 1):
        ws.column_dimensions[get_column_letter(i)].width = larg[c]
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{ws.max_row}"
    return len(sel), total


# ─────────────────────── Cobertura ───────────────────────

def aba_cobertura(wb, regs, mods_desacordo):
    """Onde a classificação está completa e onde não está.

    É esta aba que impede o relatório de mentir enquanto a leitura não termina: sem
    ela, um percentual calculado sobre 60% do bloco parece tão firme quanto um sobre
    100%."""
    ws = wb.create_sheet("Cobertura")
    ws.append(["Quanto de cada bloco já foi classificado"])
    ws["A1"].font = Font(bold=True, size=12, color="1F4E79")
    ws.append(["Camadas 1 e 2 do Resumo não aparecem aqui porque não dependem de "
               "leitura — elas já estão completas."])
    ws["A2"].font = Font(italic=True, size=9, color="606060")
    ws.append([])

    ws.append(["Versão", "Natureza", "Tipo", "Total", "Lidos", "Falta", "% lido"])
    for c in ws[ws.max_row]:
        c.fill, c.font = HDR, HF
    agg = collections.defaultdict(lambda: [0, 0])
    for r in regs:
        k = (grupo_versao(r), r["natureza"],
             "chamado" if r["tipo"] == "chamado" else "conversa")
        agg[k][0] += 1
        if r["vocab"] != VOC_NADA:
            agg[k][1] += 1
    for k in sorted(agg):
        tot, lid = agg[k]
        ws.append([k[0], k[1], k[2], tot, lid, tot - lid, pct(lid, tot)])
        if lid < tot:
            ws[f"G{ws.max_row}"].font = Font(bold=True, color="9C2119")

    ws.append([])
    ws.append(["Falta ler, por mês"])
    ws[f"A{ws.max_row}"].font = Font(bold=True, size=12, color="1F4E79")
    ws.append(["Mês", "Chamados", "Conversas", "Total"])
    for c in ws[ws.max_row]:
        c.fill, c.font = HDR, HF
    pm = collections.defaultdict(lambda: [0, 0])
    for r in regs:
        if r["vocab"] == VOC_NADA:
            pm[r["data"][:7]][0 if r["tipo"] == "chamado" else 1] += 1
    for m in sorted(pm):
        a, b = pm[m]
        ws.append([m, a, b, a + b])

    ws.append([])
    ws.append(["Eixo módulo: de onde veio"])
    ws[f"A{ws.max_row}"].font = Font(bold=True, size=12, color="1F4E79")
    ws.append(["Origem", "Registros", "Custo"])
    for c in ws[ws.max_row]:
        c.fill, c.font = HDR, HF
    origem = collections.Counter(r["modulo_fonte"] or "— falta determinar" for r in regs)
    # O que ainda não foi classificado vai ser lido de qualquer jeito; o módulo sai
    # junto, sem passo extra. O custo NOVO é só o do que já está lido e mesmo assim
    # ficou sem módulo — é esse número que decide se o eixo vale a pena.
    falta_novo = sum(1 for r in regs if not r["modulo"] and r["vocab"] != VOC_NADA)
    falta_junto = sum(1 for r in regs if not r["modulo"] and r["vocab"] == VOC_NADA)
    for k, v in origem.most_common():
        ws.append([k, v, "grátis" if k != "— falta determinar" else ""])
    ws.append(["   destes, saem junto com a leitura já prevista", falta_junto,
               "sem custo extra"])
    ws[f"A{ws.max_row}"].font = Font(italic=True, size=9, color="606060")
    ws.append(["   destes, são releitura de registro já classificado", falta_novo,
               "CUSTO NOVO"])
    ws[f"A{ws.max_row}"].font = Font(italic=True, size=9, color="9C2119")
    ws[f"C{ws.max_row}"].font = Font(bold=True, color="9C2119")

    ws.append([])
    ws.append([f"Colchete do título e tema discordaram sobre o módulo em "
               f"{mods_desacordo} chamados. Nesses o colchete venceu: ele nomeia o "
               "módulo, enquanto o tema só o revela de passagem."])
    ws[f"A{ws.max_row}"].font = Font(italic=True, size=9, color="606060")
    ws[f"A{ws.max_row}"].alignment = Alignment(wrap_text=True, vertical="top")

    div = sum(1 for r in regs if r["divergente"])
    ws.append([])
    ws.append([f"Divergência base x classificador: {div} registros têm o campo fiscal "
               "da base em desacordo com o arquivo em que a classificação foi parar. "
               "A coluna Natureza segue a base. Número pequeno e conhecido; fica "
               "registrado para não ser descoberto como surpresa."])
    ws[f"A{ws.max_row}"].font = Font(italic=True, size=9, color="606060")
    ws[f"A{ws.max_row}"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[ws.max_row].height = 30

    for col, w in (("A", 26), ("B", 16), ("C", 14), ("D", 12), ("E", 12), ("F", 12),
                   ("G", 12)):
        ws.column_dimensions[col].width = w


# ─────────────────────── Legenda ───────────────────────

def aba_legenda(wb, tax, tax_v3, de, ate, regs):
    ws = wb.create_sheet("Legenda")
    nf_ch = ler(STORE / "taxonomia_nao_fiscal.json")
    nf_cv = ler(STORE / "taxonomia_nao_fiscal_conv.json")
    itens = [
        ("Período", f"{de} a {ate}. Janela pura: toda contagem considera apenas "
                    "registros com data dentro do período."),
        ("Por que o Resumo é em camadas",
         "Existem quatro vocabulários de classificação nesta base e eles não se cruzam. "
         "Uma tabela única exigiria inventar um mapeamento entre categorias que foram "
         "derivadas separadamente — o número ficaria mais simples de ler e seria "
         "ficção. As camadas 1 e 2 são comparáveis entre V2 e V3; a camada 3 só é "
         "comparável dentro do próprio bloco."),
        ("Versão", "Vem do coletor. V2 e V3 são as versões do sistema Ultracar. "
                   "V3-backlog é melhoria pedida por cliente que ainda está na V2: "
                   "aparece separada na camada 1 e soma em V2 nas demais."),
        ("Natureza", "Fiscal x Não-fiscal, do campo fiscal da base. Não depende de "
                     "leitura por IA."),
        ("Natureza 'Fiscal' x frente R6",
         "São medidas diferentes e os números NÃO batem de propósito. Natureza vem de "
         "regra do coletor sobre o registro; R6 vem da leitura do conteúdo. Um chamado "
         "pode ser marcado fiscal pelo coletor e ser lido como erro funcional da V3, e "
         "vice-versa. Compare cada um com o seu par, nunca um com o outro."),
        ("Módulo", "Onde no produto a fricção acontece: Ordem de Serviço, Orçamentos & "
                   "Serviços, Financeiro, Fiscal, Cadastros (cliente, veículo, peça, "
                   "serviço), Peças & Estoque, Gestão de Pátio, Relatórios, Acesso e "
                   "login, entre outros. É o ÚNICO eixo comparável entre V2 e V3: os "
                   "vocabulários discordam sobre que tipo de fricção é, mas concordam "
                   "sobre onde ela acontece. Mesma lista do eixo módulo da V3, de "
                   "propósito — uma segunda lista tornaria os dois incomparáveis."),
        ("Origem do módulo",
         "Como o módulo foi atribuído. 'definição': registro fiscal, o módulo é Fiscal. "
         "'colchete do título': o analista já nomeou o módulo no chamado ([Orçamento], "
         "[Financeiro]...). 'tema': o tema da classificação só existe dentro de um "
         "módulo (ex. 'Gestão de Pátio não abre'). 'leitura (V3)': lido registro a "
         "registro. Nada aqui é palpite sobre o registro — é propriedade do rótulo, "
         "auditável em data/store/modulo_por_rotulo.json. "
         "'(a determinar na leitura)' é o que nenhum rótulo resolve: temas que "
         "abrangem vários módulos por definição, como 'não sabe executar a rotina na "
         "OS, no orçamento, no estoque ou no cadastro', que nomeia quatro."),
        ("Vocabulário", "Qual das quatro taxonomias classificou aquele registro. "
                        "Não compare Categoria entre vocabulários diferentes."),
        (VOC_FISCAL, f"{len(tax['frentes'])} frentes, {len(tax['temas'])} temas e "
                     f"{len(tax['subgrupos'])} subgrupos. Taxonomia {tax['versao']}, "
                     "congelada. É a única das quatro com três níveis."),
        (VOC_NAOFIS, f"Duas listas planas e distintas: {len(nf_ch['temas'])} temas para "
                     f"chamado e {len(nf_cv['temas'])} para conversa. Foram derivadas "
                     "de amostras independentes, então não se somam entre si — por "
                     "isso aparecem em blocos separados no Resumo."),
        (VOC_V3, f"Eixo frente (R1 a R6) mais eixo módulo. Taxonomia {tax_v3['versao']}, "
                 "derivada do zero: não reaproveita a da V2 de propósito, porque a "
                 "fricção de rollout não tem a mesma natureza da fricção de operação."),
        ("Ponto cego do WhatsApp na V3",
         "A regra automática marca conversa como V3 pela linha de entrada (17) ou por "
         "transferência explícita. O WhatsApp entra todo pela linha 7, da V2, então "
         "conversa de oficina migrada só conta se o atendente transferiu — e poucos "
         "transferem. Medido em 29/10: a regra achou 2 conversas de WhatsApp no dia e a "
         "leitura achou outras 22. Logo, o bloco da V3 SUBCONTA o WhatsApp. A V3 só "
         "existe desde setembro e só virou volume em 29/10, então a fatia é pequena e "
         "enviesada por natureza."),
        ("Texto / Título", "Mascarado: valor que vem depois de 'senha:' é trocado por "
                           "[SENHA REMOVIDA]. O rótulo fica visível de propósito, para "
                           "que o problema seja corrigido na origem."),
        ("Reprodutibilidade", "A classificação vem de cache. Registro já lido não é "
                              "reprocessado, então rodar o mesmo período duas vezes dá "
                              "o mesmo resultado."),
    ]
    for k, v in itens:
        ws.append([k, v])
    ws.column_dimensions["A"].width = 30
    ws.column_dimensions["B"].width = 118
    for row in ws.iter_rows():
        row[0].font = Font(bold=True)
        row[0].alignment = Alignment(vertical="top")
        row[1].alignment = Alignment(wrap_text=True, vertical="top")


# ─────────────────────── main ───────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--de", required=True)
    ap.add_argument("--ate", default=date.today().isoformat())
    ap.add_argument("--amostra", type=int, default=0,
                    help="limita as abas de detalhe a N linhas espalhadas pelo período, "
                         "para validar o formato sem gerar um arquivo de dezenas de MB. "
                         "0 (padrão) traz tudo.")
    a = ap.parse_args()
    REPORT.mkdir(exist_ok=True)

    regs, tax, tax_v3, mods = carregar(a.de, a.ate)
    if not regs:
        print(f"Nenhum registro em {a.de}..{a.ate}.")
        return 1

    extracao = datetime.now().strftime("%d/%m/%Y %H:%M")
    wb = Workbook()
    aba_resumo(wb, regs, tax, a.de, a.ate, extracao, a.amostra)
    n_ch, t_ch = aba_detalhe(wb, regs, "chamado", a.amostra)
    n_cv, t_cv = aba_detalhe(wb, regs, "conversa", a.amostra)
    aba_cobertura(wb, regs, mods.desacordo)
    aba_legenda(wb, tax, tax_v3, a.de, a.ate, regs)

    sufixo = "_PREVIA" if a.amostra else ""
    saida = REPORT / f"relatorio_completo_{a.de}_{a.ate}{sufixo}.xlsx"
    wb.save(saida)

    lidos = sum(1 for r in regs if r["vocab"] != VOC_NADA)
    print(f"Janela {a.de} a {a.ate}")
    print(f"  {len(regs)} registros: {t_ch} chamados, {t_cv} conversas")
    print(f"  classificados: {lidos} ({pct(lidos, len(regs))}) | "
          f"falta: {len(regs) - lidos}")
    if a.amostra:
        print(f"  AMOSTRA: abas de detalhe com {n_ch} e {n_cv} linhas")
    print(f"\n  {saida.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
