# -*- coding: utf-8 -*-
"""
Relatório da V3 — chamados e conversas da nova versão, sem filtro por módulo.

    python pipeline/gerar_relatorio_v3.py --de 2026-09-01 --ate 2026-10-23
    python pipeline/gerar_relatorio_v3.py --de 2026-10-29T08:00 --ate agora

Produz um arquivo em report/, com quatro abas:
    Resumo                   frente, módulo e canal, chamados x conversas
    Chamados                 os registros versao=V3, linha a linha
    Conversas                idem
    Melhorias V2 para a V3   os versao=V3-backlog, fora da contagem principal

Um arquivo só porque são dezenas de registros. Separar executivo de base nessa escala
produz dois arquivos que o leitor abre e fecha.

Janela pura, igual ao relatório fiscal: só entra registro com instante de criação
dentro de [de, ate]. --de e --ate aceitam data (dia inteiro) ou data com hora, sempre
em horário de Brasília; 'agora' no --ate vale o momento da geração.
"""
from __future__ import annotations
import argparse
import collections
import json
import re
import sys
from datetime import date, datetime, timedelta, timezone
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

# Os nomes que o solicitante usa ("zap, bitrix, chat") mapeados nos nomes do store.
# Chamado não tem campo de canal de entrada — o canal dele É o Bitrix.
CANAL = {"LiveChat": "Chat (site)", "WhatsApp": "WhatsApp"}
CANAL_CHAMADO = "Bitrix (chamado)"

# O store guarda os dois tipos em fusos diferentes. Chamado vem do Bitrix com offset
# -03:00, hora de Brasília. Conversa é gravada em UTC: JsonReadHelpers converte com
# DateTimeStyles.AdjustToUniversal, e o Bitrix devolve as atividades em +03:00.
# Confirmado no histograma de criação da base: chamado pica entre 08h e 18h, conversa
# entre 11h e 21h — as mesmas três horas de diferença. Para janela de dia inteiro isso
# só desloca a virada da meia-noite; para janela com hora, erra a janela toda.
TZ_BR = timezone(timedelta(hours=-3))

sys.stdout.reconfigure(encoding="utf-8")


def ler(p: Path, padrao=None):
    if not p.exists():
        return padrao
    return json.loads(p.read_text(encoding="utf-8-sig"))


def momento_br(r: dict) -> datetime:
    """Instante de criação do registro em horário de Brasília, ingênuo."""
    bruto = (r.get("criado_em") or "").strip()
    try:
        dt = datetime.fromisoformat(bruto)
    except ValueError:
        return datetime.fromisoformat(r["data"] + "T00:00:00")
    if dt.tzinfo is not None:  # chamado: já vem com o offset de Brasília
        return dt.astimezone(TZ_BR).replace(tzinfo=None)
    return dt + TZ_BR.utcoffset(None)  # conversa: gravada em UTC


def instante(valor: str, fim_do_dia: bool) -> datetime:
    """'2026-10-29', '2026-10-29T08:00' ou 'agora'. Sem hora, a borda do dia."""
    if valor == "agora":
        return datetime.now()
    if "T" in valor:
        return datetime.fromisoformat(valor)
    return datetime.fromisoformat(valor + ("T23:59:59" if fim_do_dia else "T00:00:00"))


def rotulo_janela(dt: datetime, com_hora: bool) -> str:
    return dt.strftime("%d/%m/%Y %H:%M" if com_hora else "%d/%m/%Y")


def carregar(ini: datetime, fim: datetime, por_conteudo: dict):
    """V3 obedece a janela pura. O backlog é o caso especial.

    O backlog é melhoria pedida sobre a V2 e endereçada para a nova versão: por
    natureza ela nasce antes do rollout, então cortar pelo 'de' esconderia justamente
    as mais antigas, que são contexto do relatório e não medida dele. Numa janela de
    um dia, porém, o relatório é retrato do agora: despejar ali o backlog inteiro do
    ano afogaria o que o leitor abriu o arquivo para ver. Por isso a janela curta
    também recorta o backlog, e a aba diz qual das duas regras valeu.
    """
    v3, backlog, suspeitas = [], [], []
    intradia = ini.date() == fim.date()
    marcados = por_conteudo.get("conversas", {})
    with (STORE / "base_historica.jsonl").open(encoding="utf-8") as fh:
        for linha in fh:
            r = json.loads(linha)
            versao = r.get("versao")
            if versao not in ("V3", "V3-backlog") and str(r["id"]) not in marcados:
                continue
            t = momento_br(r)
            dentro = ini <= t <= fim
            if versao == "V3":
                if dentro:
                    v3.append(r)
            elif versao == "V3-backlog":
                if dentro if intradia else (t <= fim):
                    backlog.append(r)
            elif dentro and r["tipo"] == "conversa":
                suspeitas.append(r)
    return v3, backlog, suspeitas


def canal_de(r: dict) -> str:
    if r["tipo"] == "chamado":
        return CANAL_CHAMADO
    bruto = r.get("canal") or ""
    return CANAL.get(bruto, bruto or "(não identificado)")


def em_andamento(r: dict) -> bool:
    """Conversa ainda aberta na hora da extração.

    Numa janela de poucas horas isso é a maioria, e muda como se lê o arquivo: duração,
    contagem de mensagens e assunto saem incompletos.

    O sinal é o campo `encerrada`, que vem do COMPLETED da activity. Não dá para usar
    `fechado_em`: o coletor o preenche com o timestamp da última mensagem, então ele
    nunca vem vazio e dizia que toda conversa estava encerrada. Registro antigo tem
    `encerrada` None — coletado antes do campo existir — e aí a resposta é não, porque
    conversa de meses atrás não está em andamento agora.
    """
    return r["tipo"] == "conversa" and r.get("encerrada") is False


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


def aba_resumo(wb, v3, cls, tax, janela, servico, extracao, suspeitas):
    ws = wb.active
    ws.title = "Resumo"
    frentes = {v["codigo"]: v for v in
               next(e for e in tax["eixos"] if e["nome"] == "frente")["valores"]}

    def rot(r):
        grupo = "chamados" if r["tipo"] == "chamado" else "conversas"
        return cls[grupo].get(str(r["id"]), {})

    uteis = [r for r in v3 if rot(r).get("frente") not in servico]
    fora = [r for r in v3 if rot(r).get("frente") in servico]

    ws.append([f"Relatório V3 — {janela}"])
    ws["A1"].font = Font(bold=True, size=14)
    ws.append([f"Extraído em {extracao.strftime('%d/%m/%Y %H:%M')} (horário de Brasília)."])
    ws["A2"].font = Font(italic=True, size=10)
    ws.append([])
    ws.append(["Chamados", sum(1 for r in uteis if r["tipo"] == "chamado"),
               "Conversas", sum(1 for r in uteis if r["tipo"] == "conversa")])
    for c in ("A4", "C4"):
        ws[c].font = Font(bold=True)
    rotulados = collections.Counter(rot(r).get("frente") for r in fora)
    ws.append(["Fora da contagem", "; ".join(f"{k}: {v}" for k, v in sorted(rotulados.items()))
                                   or "nenhum"])
    ws[f"A{ws.max_row}"].font = Font(bold=True)

    abertas = [r for r in v3 if em_andamento(r)]
    if abertas:
        ws.append([])
        ws.append([f"Atenção: {len(abertas)} das "
                   f"{sum(1 for r in v3 if r['tipo'] == 'conversa')} conversas ainda estavam "
                   "em andamento na hora da extração. Nelas a duração, a contagem de mensagens "
                   "e o assunto saem incompletos, e parte cai em 'Sem conteúdo útil' só por "
                   "não ter tido tempo de virar assunto. A coluna 'Em andamento' da aba "
                   "Conversas marca quais são."])
        cel = ws[f"A{ws.max_row}"]
        cel.font = Font(italic=True)
        cel.alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[ws.max_row].height = 46

    if suspeitas:
        ws.append([])
        canais = collections.Counter(canal_de(r) for r in suspeitas)
        ws.append([f"Ponto cego: outras {len(suspeitas)} conversas da janela são da V3 pelo "
                   "conteúdo, mas não passaram pela fila da V3, então a regra automática não "
                   "as enxerga e elas NÃO estão nos números acima "
                   f"({'; '.join(f'{k}: {v}' for k, v in canais.most_common())}). "
                   "Estão listadas uma por uma, com a evidência, na aba "
                   "'Possível V3 fora da regra'."])
        cel = ws[f"A{ws.max_row}"]
        cel.font = Font(italic=True)
        cel.alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[ws.max_row].height = 46

    ws.append([])
    linha = ws.max_row + 1
    ws.append(["Canal", "", "Registros", "Em andamento", "", ""])
    for c in ws[linha]:
        c.fill, c.font = HDR, HF
    # Volume por canal conta também "Sem conteúdo útil" — a taxonomia manda: esse rótulo
    # "entra na contagem de volume, fica fora da leitura por frente". Só "Teste interno"
    # fica fora de tudo. Sem isso o canal com uma conversa só, e ela vazia, desaparece da
    # tabela, e a pergunta aqui é quanto entrou por onde, não sobre o quê.
    volume = [r for r in v3 if rot(r).get("frente") != "Teste interno"]
    por_canal = collections.Counter(canal_de(r) for r in volume)
    abertas_canal = collections.Counter(canal_de(r) for r in volume if em_andamento(r))
    for nome, n in sorted(por_canal.items(), key=lambda x: -x[1]):
        ws.append([nome, "", n, abertas_canal[nome] or "", "", ""])

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


def aba_chamados(wb, v3, cls, fim: datetime):
    ws = wb.create_sheet("Chamados")
    cols = ["Id", "Abrir no Bitrix", "Canal", "Aberto em", "Frente", "Módulo", "Status",
            "Coluna do board", "Cliente", "CNPJ", "Fiscal", "Dias em aberto", "Tags", "Título"]
    cabecalho(ws, cols, (9, 16, 17, 17, 26, 24, 14, 30, 34, 20, 8, 13, 40, 95))
    hoje = fim.date()
    for r in sorted((x for x in v3 if x["tipo"] == "chamado"), key=momento_br):
        c = cls["chamados"].get(str(r["id"]), {})
        abertos = (hoje - date.fromisoformat(r["data"])).days if not r.get("fechado_em") else None
        ws.append([r["id"], "abrir", canal_de(r),
                   momento_br(r).strftime("%d/%m %H:%M"),
                   rotulo(c),
                   c.get("modulo", ""), r.get("status", ""),
                   COLUNAS.get(str(r.get("stage")), str(r.get("stage") or "")),
                   r.get("cliente", ""), r.get("cnpj", ""),
                   "Sim" if r.get("fiscal") else "", abertos,
                   ", ".join(r.get("tags") or []),
                   mascarar_credenciais(re.sub(r"\s+", " ", r.get("titulo", "")))[:300]])
        cel = ws.cell(row=ws.max_row, column=2)
        cel.hyperlink = BITRIX.format(r["id"])
        cel.font = Font(color="0563C1", underline="single")
    finalizar(ws, len(cols))


def aba_conversas(wb, v3, cls):
    ws = wb.create_sheet("Conversas")
    cols = ["Id", "Canal", "Início", "Em andamento", "Frente", "Módulo", "Linha de entrada",
            "Duração (min)", "Mensagens", "Operador", "Cliente", "Fiscal",
            "Resumo da conversa"]
    cabecalho(ws, cols, (10, 17, 17, 14, 26, 24, 17, 13, 11, 20, 32, 8, 110))
    aberta = Font(color="9C5700")
    for r in sorted((x for x in v3 if x["tipo"] == "conversa"), key=momento_br):
        c = cls["conversas"].get(str(r["id"]), {})
        entrada = "V3 (linha 17)" if str(r.get("linha")) == "17" else "V2 (transferida)"
        ws.append([r["id"], canal_de(r), momento_br(r).strftime("%d/%m %H:%M"),
                   "Sim" if em_andamento(r) else "",
                   rotulo(c),
                   c.get("modulo", ""), entrada,
                   r.get("duracao_min"), r.get("mensagens"), r.get("operador", ""),
                   r.get("cliente", ""), "Sim" if r.get("fiscal") else "",
                   mascarar_credenciais(re.sub(r"\s+", " ", r.get("texto", "")))[:600]])
        if em_andamento(r):
            ws.cell(row=ws.max_row, column=4).font = aberta
    finalizar(ws, len(cols))


def aba_suspeitas(wb, suspeitas, por_conteudo):
    """O que a regra de versão não pega: conversa de V3 que nunca passou pela fila V3.

    A regra marca V3 pela linha de entrada (17) ou pela transferência explícita para a
    fila da V3. O WhatsApp entra todo pela linha 7, então zap de oficina recém-migrada
    só é contado se o atendente transferiu — e boa parte não transfere. Estes registros
    ficam FORA de toda contagem do relatório, de propósito: a regra é a regra. Esta aba
    existe para o leitor ver o tamanho do que a regra deixa passar, com a evidência de
    cada caso, em vez de o número chegar baixo sem explicação.
    """
    ws = wb.create_sheet("Possível V3 fora da regra")
    ws.append(["Conversa que a regra automática marcou como V2, mas cujo conteúdo é da V3: "
               "o cliente está usando o sistema novo e o atendimento não passou pela fila da "
               "V3, então a regra não enxerga. NÃO entra em nenhum número deste relatório — "
               "está aqui para dimensionar o ponto cego. O canal onde isso acontece é "
               "principalmente o WhatsApp, que entra todo pela linha da V2."])
    ws["A1"].font = Font(italic=True)
    ws["A1"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[1].height = 60
    ws.append([])
    linha = ws.max_row + 1
    cols = ["Id", "Canal", "Início", "Em andamento", "Cliente", "Base da evidência",
            "Confiança", "Por que parece V3", "Resumo da conversa"]
    ws.append(cols)
    for c in ws[linha]:
        c.fill, c.font = HDR, HF
    base = {"texto": "O cliente disse", "chamado": "Cita chamado V3"}
    marcados = por_conteudo.get("conversas", {})
    for r in sorted(suspeitas, key=momento_br):
        m = marcados.get(str(r["id"]), {})
        ws.append([r["id"], canal_de(r), momento_br(r).strftime("%d/%m %H:%M"),
                   "Sim" if em_andamento(r) else "", r.get("cliente", ""),
                   base.get(m.get("base"), m.get("base", "")), m.get("confianca", ""),
                   m.get("evidencia", ""),
                   mascarar_credenciais(re.sub(r"\s+", " ", r.get("texto", "")))[:600]])
    for col, w in zip("ABCDEFGHI", (10, 17, 17, 14, 32, 18, 11, 60, 110)):
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "A4"


def aba_backlog(wb, backlog, intradia: bool):
    ws = wb.create_sheet("Melhorias V2 para a V3")
    corte = ("Numa janela de um dia esta aba segue a mesma janela, para o retrato do dia "
             "não vir afogado no backlog do ano inteiro."
             if intradia else
             "Esta aba ignora a data inicial da janela, porque esse tipo de pedido nasce "
             "antes do rollout.")
    ws.append(["Chamado de cliente da V2 marcado com a tag novaversao: a melhoria foi pedida "
               "sobre a versão antiga e está endereçada para a nova. Conta como V2 nos números "
               "e aparece aqui só como contexto. " + corte])
    ws["A1"].font = Font(italic=True)
    ws.append([])
    linha = ws.max_row + 1
    cols = ["Id", "Abrir no Bitrix", "Data", "Status", "Coluna do board", "Cliente", "Título"]
    ws.append(cols)
    for c in ws[linha]:
        c.fill, c.font = HDR, HF
    for r in sorted(backlog, key=lambda x: x["data"]):
        ws.append([r["id"], "abrir", r["data"], r.get("status", ""),
                   COLUNAS.get(str(r.get("stage")), str(r.get("stage") or "")),
                   r.get("cliente", ""),
                   mascarar_credenciais(re.sub(r"\s+", " ", r.get("titulo", "")))[:300]])
        cel = ws.cell(row=ws.max_row, column=2)
        cel.hyperlink = BITRIX.format(r["id"])
        cel.font = Font(color="0563C1", underline="single")
    for col, w in zip("ABCDEFG", (9, 16, 11, 14, 30, 34, 95)):
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "A4"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--de", required=True, help="2026-09-01 ou 2026-10-29T08:00")
    ap.add_argument("--ate", default="agora", help="data, data com hora, ou 'agora'")
    a = ap.parse_args()

    tax = ler(STORE / "taxonomia_v3.json")
    cls = ler(STORE / "classificacao_v3.json", {"chamados": {}, "conversas": {}})
    servico = {r["nome"] for r in tax["rotulos_de_servico"]}

    extracao = datetime.now()
    ini, fim = instante(a.de, False), instante(a.ate, True)
    if fim <= ini:
        print(f"ABORTADO: janela vazia — {a.ate} não é depois de {a.de}.")
        return 1
    com_hora = "T" in a.de or "T" in a.ate or a.ate == "agora"
    intradia = ini.date() == fim.date()
    janela = f"{rotulo_janela(ini, com_hora)} a {rotulo_janela(fim, com_hora)}"

    por_conteudo = ler(STORE / "v3_por_conteudo.json", {"conversas": {}})
    v3, backlog, suspeitas = carregar(ini, fim, por_conteudo)

    falta = [r for r in v3
             if str(r["id"]) not in cls["chamados" if r["tipo"] == "chamado" else "conversas"]]
    if falta:
        print(f"ABORTADO: {len(falta)} registro(s) V3 sem classificação. "
              f"Rode classificar_v3.py antes. Ex: {[r['id'] for r in falta[:5]]}")
        return 1

    print(f"Janela {janela} (horário de Brasília)")
    print(f"  {len(v3)} registros V3 "
          f"({sum(1 for r in v3 if r['tipo'] == 'chamado')} chamados, "
          f"{sum(1 for r in v3 if r['tipo'] == 'conversa')} conversas)")
    por_canal = collections.Counter(canal_de(r) for r in v3)
    print(f"  por canal: {dict(por_canal)}")
    print(f"  {sum(1 for r in v3 if em_andamento(r))} conversas ainda em andamento")
    print(f"  {len(suspeitas)} possíveis V3 fora da regra (não contadas)")
    print(f"  {len(backlog)} melhorias V2 endereçadas para a V3")

    wb = Workbook()
    aba_resumo(wb, v3, cls, tax, janela, servico, extracao, suspeitas)
    aba_chamados(wb, v3, cls, fim)
    aba_conversas(wb, v3, cls)
    if suspeitas:
        aba_suspeitas(wb, suspeitas, por_conteudo)
    aba_backlog(wb, backlog, intradia)

    REPORT.mkdir(exist_ok=True)
    sufixo = (ini.strftime("%Y-%m-%d_%Hh%M") + "_a_" + fim.strftime("%Hh%M")
              if intradia and com_hora else f"{ini.date()}_{fim.date()}")
    saida = REPORT / f"relatorio_v3_{sufixo}.xlsx"
    wb.save(saida)
    print(f"\n  {saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
