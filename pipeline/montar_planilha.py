# -*- coding: utf-8 -*-
"""Monta todas as abas da planilha de acompanhamento, como linhas prontas para escrever.

Não fala com o Google: ele grava um JSON com `{nome da aba: [[linha], ...]}`, e quem
publica é o conector do Sheets. Separar assim deixa o cálculo testável sem rede e
permite reescrever a planilha inteira a partir de um arquivo, se preciso.

A fila vem do `fila_agora.py` (ao vivo, da API). As abas de atendimento vêm do
`gerar_atendimento.py` — **importadas, não copiadas**: as mesmas funções que geram o
Excel. Duplicar a contagem aqui criaria duas respostas para "quantas conversas o João
atendeu ontem", e uma delas estaria errada sem ninguém saber qual.

Uso:
    python pipeline/montar_planilha.py --saida abas.json
    python pipeline/montar_planilha.py --saida abas.json --dia 2026-11-05
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "pipeline"))

from fila_agora import BRT, ler_fila                                    # noqa: E402
from gerar_atendimento import (carregar, chamados_por_pessoa,           # noqa: E402
                               metricas_do_dia)

VAZIO = ""


def aba_agora(f: dict) -> list[list]:
    em = dt.datetime.fromisoformat(f["em"])
    l: list[list] = [
        ["Fila de atendimento — retrato do momento"],
        [f"Atualizado em {em:%d/%m/%Y %H:%M}"],
        [VAZIO],
        ["ESPERANDO (ninguém do suporte respondeu ainda)", f["esperando"]],
        ["Em andamento (alguém já respondeu, sessão aberta)", f["andamento"]],
        ["Abertas no total", f["abertas"]],
        [VAZIO],
        ["Mais antiga esperando", f"{f['espera_max_min'] / 60:.1f} h"],
        ["Mediana de espera", f"{f['espera_mediana_min']} min"],
        [VAZIO],
        ["Quem está esperando, por tempo de espera"],
    ]
    l += [[f"   {nome}", q] for nome, q in f["faixas_espera"]]
    l += [
        [VAZIO],
        ["Esperando que entrou ontem ou antes", f["esperando_de_ontem"]],
        ["Esperando que entrou hoje", f["esperando_de_hoje"]],
        [VAZIO],
        ["Hoje: entraram", f["entraram_hoje"]],
        ["Hoje: fechadas", f["fechadas_hoje"]],
        ["Ontem: entraram", f["entraram_ontem"]],
        ["Ontem: fechadas", f["fechadas_ontem"]],
        ["Ontem: seguem abertas", f["abertas_de_ontem"]],
        [VAZIO],
        ["ESPERANDO é o número para agir: é cliente olhando a tela sem resposta. "
         "Em andamento costuma ser sessão que ninguém encerrou, não cliente esperando."],
        [f"A fila é lida ao vivo da API do Bitrix, janela de {f['janela_dias']} dias. "
         "Não depende do relatório diário nem de classificação."],
    ]
    return l


def aba_hora(f: dict) -> list[list]:
    """Uma linha por execução. O cabeçalho só vai na primeira vez."""
    em = dt.datetime.fromisoformat(f["em"])
    return [[
        f"{em:%d/%m/%Y %H:%M}", f["entraram_na_hora"], f["fechadas_na_hora"],
        f["esperando"], f["andamento"], round(f["espera_max_min"] / 60, 1),
        f["esperando_de_ontem"], f["esperando_de_hoje"],
        f["entraram_hoje"], f["fechadas_hoje"], f["chamados_abertos"],
    ]]


CAB_HORA = [["Momento", "Entraram na hora", "Fechadas na hora", "Esperando",
             "Em andamento", "Mais antiga esperando (h)", "Esperando de ontem",
             "Esperando de hoje", "Entraram hoje", "Fechadas hoje",
             "Chamados abertos"]]


def aba_backlog(f: dict) -> list[list]:
    l: list[list] = [
        ["Backlog de chamados — outro relógio"],
        [f"Atualizado em {dt.datetime.fromisoformat(f['em']):%d/%m/%Y %H:%M}"],
        [VAZIO],
        ["Chamados não concluídos", f["chamados_abertos"]],
        ["Idade mediana", f"{f['chamados_mediana_dias']} dias"],
        ["Mais antigo", f"{f['chamados_max_dias']} dias"],
        [VAZIO],
        ["Por idade"],
    ]
    l += [[f"   {nome}", q] for nome, q in f["faixas_chamados"]]
    l += [
        [VAZIO],
        ["Isto NÃO é fila de atendimento. A fila de conversas se move em minutos; este "
         "backlog se move em meses, e é de desenvolvimento, não de suporte."],
        ["Por isso fica em aba separada e não entra no acompanhamento de hora em hora: "
         "de uma hora para outra ele não muda."],
    ]
    return l


def abas_atendimento(dia: str, compara: int) -> dict[str, list[list]]:
    conv, tr = carregar()
    chamados = chamados_por_pessoa()
    dias_com_dado = sorted({r["data"][:10] for r in conv.values()
                            if r["data"][:10] <= dia})
    anteriores = [d for d in dias_com_dado if d < dia][-compara:]
    m = metricas_do_dia(dia, conv, tr)
    antes = {d: metricas_do_dia(d, conv, tr) for d in anteriores}
    ch_dia = chamados.get(dia, {})
    abriu = ch_dia.get("abriu", {})

    rot = f"{dia[8:]}/{dia[5:7]}/{dia[:4]}"
    pessoas = sorted(set(m["atendeu"]) | set(abriu),
                     key=lambda n: (-(m["atendeu"][n] + abriu.get(n, 0)), n))
    por_pessoa: list[list] = [
        [f"Conversas por pessoa — {rot}"],
        [f"{m['total']} conversas abertas no dia · {m['atendidas']} atendidas · "
         f"{m['abertas_sem_atend']} ficaram abertas sem ninguém atender"],
        ["Atendeu = escreveu na conversa OU pegou a conversa da fila. Conversa "
         "transferida para quem nunca a pegou não conta para essa pessoa."],
        # Sem esta linha, quem lê vê o cabeçalho dizer 262 e o TOTAL dizer 267 e
        # conclui que um dos dois está errado. A diferença é proposital.
        [f"A soma da coluna ({sum(m['atendeu'].values())}) passa do total do dia "
         f"({m['atendidas']}) porque conversa transferida conta para as duas pessoas "
         "que a atenderam — é atendimento das duas."],
        ["Pessoa", "Conversas atendidas", "Das quais escreveu", "Mensagens enviadas",
         "Chamados abertos"],
    ]
    for n in pessoas:
        por_pessoa.append([n, m["atendeu"][n], m["falou"][n], m["msgs"][n],
                           abriu.get(n, 0)])
    por_pessoa.append(["TOTAL", sum(m["atendeu"].values()), sum(m["falou"].values()),
                       sum(m["msgs"].values()), sum(abriu.values())])

    metr = ["concluiu", "moveu_fluxo", "mexeu_status", "abriu", "tocou"]
    quem = {n for k in metr for n in ch_dia.get(k, {})}
    ordem = sorted(quem, key=lambda n: (-ch_dia.get("tocou", {}).get(n, 0), n))
    cham: list[list] = [
        [f"Chamados por pessoa — {rot}"],
        ["Trabalho feito NO chamado. Abrir é registrar o problema; mover e concluir é "
         "resolvê-lo, e em geral são pessoas diferentes."],
        ["Conta chamados distintos, não eventos. Não há coluna de 'respondeu': "
         "comentário em chamado acabou em 27/11/2025 e a resposta migrou para o chat."],
        [VAZIO],
        ["Pessoa", "Concluiu", "Moveu no fluxo", "Mexeu no status", "Abriu",
         "Chamados que tocou"],
    ]
    for n in ordem:
        cham.append([n] + [ch_dia.get(k, {}).get(n, 0) for k in metr])
    cham.append(["TOTAL (por pessoa, soma)"]
                + [sum(ch_dia.get(k, {}).values()) for k in metr])

    dias = anteriores + [dia]
    comp: list[list] = [
        ["Conversas atendidas por pessoa, por dia"],
        ["Serve para ler o dia: número baixo pode ser dia fraco da pessoa ou dia em que "
         "ela não estava na fila. As linhas de total, embaixo, dizem qual dos dois."],
        [VAZIO],
        ["Pessoa"] + [f"{d[8:]}/{d[5:7]}" for d in dias],
    ]
    todas = {n for d in dias for n in (antes.get(d) or m)["atendeu"]}
    for n in sorted(todas, key=lambda x: -m["atendeu"][x]):
        comp.append([n] + [(m if d == dia else antes[d])["atendeu"][n] or VAZIO
                           for d in dias])
    for rotulo, chave in (("TOTAL atendidas", "atendidas"),
                          ("Conversas abertas no dia", "total"),
                          ("Receberam aviso de fila cheia", "com_aviso"),
                          ("Dessas, atendidas", "aviso_atendido")):
        comp.append([rotulo] + [(m if d == dia else antes[d])[chave] for d in dias])

    return {"Por pessoa": por_pessoa, "Chamados por pessoa": cham,
            "Comparativo": comp}


def aba_legenda(f: dict, dia: str) -> list[list]:
    return [
        ["Legenda — de onde vem cada número"],
        [VAZIO],
        ["Aba", "O que é", "Com que frequência muda"],
        ["Agora", "A fila neste instante, lida ao vivo da API do Bitrix. Não depende do "
         "relatório diário nem de classificação por IA.", "A cada execução"],
        ["Fila por hora", "Uma linha por execução, para ver a fila subindo e descendo "
         "ao longo do dia.", "A cada execução (uma linha nova)"],
        ["Por pessoa", f"Conversas atendidas por pessoa em {dia[8:]}/{dia[5:7]}, o "
         "último dia fechado. Mesmo cálculo do arquivo Excel.", "Uma vez por dia"],
        ["Chamados por pessoa", "Trabalho feito nos chamados no mesmo dia: quem "
         "concluiu, moveu e abriu.", "Uma vez por dia"],
        ["Comparativo", "As conversas atendidas por pessoa nos dias anteriores, para "
         "dar contexto ao dia.", "Uma vez por dia"],
        ["Backlog de chamados", "Chamados não concluídos e suas idades. Fila de "
         "desenvolvimento, não de atendimento.", "Uma vez por dia"],
        [VAZIO],
        ["Os dois números que mais se confundem"],
        ["ESPERANDO", "Sessão aberta e NINGUÉM do suporte falou ainda. É cliente "
         "olhando a tela agora. É o número para agir."],
        ["Em andamento", "Sessão aberta, mas alguém já respondeu. Boa parte é sessão "
         "que ninguém encerrou, não cliente esperando."],
        [VAZIO],
        ["Por que um total pode passar do outro"],
        [VAZIO, "Nas abas por pessoa, conversa transferida conta para as duas pessoas "
         "que a atenderam, então a soma da coluna passa do total de conversas do dia. "
         "É proposital: o atendimento foi das duas."],
        [VAZIO],
        ["O que esta planilha NÃO mede"],
        [VAZIO, "Tempo de atendimento, dificuldade do caso e qualidade. Conversa de uma "
         "pergunta e caso fiscal de duas horas contam igual."],
        [VAZIO, "Assunto. Para saber do que o cliente reclamou, é o relatório completo, "
         "que classifica por tema e por módulo."],
        [VAZIO, "A idade da conversa é desde que ela ENTROU, não desde a última "
         "mensagem do cliente."],
        [VAZIO, f"Conversa aberta há mais de {f['janela_dias']} dias, que é a janela da "
         "consulta."],
    ]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", required=True)
    ap.add_argument("--dia", help="dia fechado das abas de atendimento (padrão: ontem)")
    ap.add_argument("--compara", type=int, default=10)
    a = ap.parse_args()

    agora = dt.datetime.now(BRT)
    dia = a.dia or (agora.date() - dt.timedelta(days=1)).isoformat()

    print("lendo a fila ao vivo...")
    f = ler_fila(agora)
    print(f"  esperando {f['esperando']} · em andamento {f['andamento']} · "
          f"chamados abertos {f['chamados_abertos']}")
    print(f"montando as abas de atendimento de {dia}...")
    abas = abas_atendimento(dia, a.compara)
    abas["Agora"] = aba_agora(f)
    abas["Backlog de chamados"] = aba_backlog(f)
    abas["Legenda"] = aba_legenda(f, dia)

    saida = {"em": f["em"], "dia_atendimento": dia,
             "cabecalho_hora": CAB_HORA, "linha_hora": aba_hora(f), "abas": abas}
    Path(a.saida).write_text(json.dumps(saida, ensure_ascii=False, indent=1) + "\n",
                             encoding="utf-8", newline="\n")
    for nome, linhas in abas.items():
        print(f"  {nome:24} {len(linhas)} linhas")
    print(f"\ngravado em {a.saida}")


if __name__ == "__main__":
    main()
