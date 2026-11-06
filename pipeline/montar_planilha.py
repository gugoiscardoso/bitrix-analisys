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

import atendimento_ao_vivo                                             # noqa: E402
import chamados_ao_vivo                                                # noqa: E402
from fila_agora import BRT, ler_fila                                    # noqa: E402

VAZIO = ""


def aba_agora(f: dict) -> list[list]:
    em = dt.datetime.fromisoformat(f["em"])
    l: list[list] = [
        ["Fila de atendimento — retrato do momento"],
        ["Última execução", f"{em:%d/%m/%Y %H:%M}"],
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
        f"{em:%d/%m/%Y %H:%M}", f.get("hora_medida", ""),
        f["entraram_na_hora"], f["fechadas_na_hora"],
        f["esperando"], f["andamento"], round(f["espera_max_min"] / 60, 1),
        f["esperando_de_ontem"], f["esperando_de_hoje"],
        f["entraram_hoje"], f["fechadas_hoje"], f["chamados_abertos"],
    ]]


CAB_HORA = [["Momento", "Hora medida", "Entraram na hora", "Fechadas na hora",
             "Esperando",
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


def abas_atendimento(dia: str, compara: int, dia_vivo: str, f: dict,
                     so_api: bool = False) -> dict[str, list[list]]:
    """As três abas de atendimento, todas da API.

    Nenhuma lê mais `base_historica.jsonl` nem `transcricoes.json`. A base está limitada
    na origem — o coletor C# guarda no máximo 50 mensagens por sessão —, então toda
    contagem de atendimento feita sobre ela subconta conversa longa, que é justamente a
    mais atendida. Com as três na API, o parâmetro `so_api` perdeu o sentido: a passada
    completa já custa cerca de um minuto, e a horária monta tudo.
    """
    # A aba por pessoa vem da API, NÃO da base. A base está limitada na origem: o
    # coletor C# guarda no máximo 50 mensagens por sessão, então a transcrição nasce
    # truncada e a contagem de atendimento subconta conversa longa — justamente a mais
    # atendida. A API, paginada, não tem esse teto.
    vivo = atendimento_ao_vivo.ler(dia_vivo, dt.datetime.now(BRT))
    rotv = f"{dia_vivo[8:]}/{dia_vivo[5:7]}/{dia_vivo[:4]}"
    # Os sumarizadores em linhas próprias, cada número na coluna B, para poderem ser
    # formatados grandes. Em frase corrida ninguém acha o número que importa.
    por_pessoa: list[list] = [
        [f"Atendimentos por pessoa — AO VIVO, {rotv}"],
        # Mesmo carimbo e MESMO número de fila da aba Agora. Antes cada aba calculava
        # o seu, com minutos de diferença, e a planilha mostrava 17 num lugar e 15 no
        # outro — num painel, dois números para a mesma coisa viram desconfiança nos
        # dois.
        ["Última execução", f"{dt.datetime.fromisoformat(f['em']):%d/%m/%Y %H:%M}"],
        [VAZIO],
        ["CLIENTES NA FILA SEM NINGUÉM", f["esperando"]],
        ["Atendendo agora", sum(vivo["atendendo"].values())],
        ["Concluídas hoje", sum(vivo["concluiu"].values())],
        ["Conversas no dia", vivo["total"]],
        ["Pessoas atendendo", len(vivo["atendeu"])],
        [VAZIO],
        ["Lido direto da API do Bitrix, com paginação completa do histórico. Não "
         "depende do relatório diário."],
        ["ATENDENDO = conversa ainda aberta em que a pessoa falou. CONCLUIU = conversa "
         "já encerrada em que ela falou. Quem transferiu e nunca falou não conta."],
        [VAZIO],
        ["Pessoa", "Atendendo agora", "Concluiu", "Total atendidas",
         "Mensagens enviadas"],
    ]
    for n, q in sorted(vivo["atendeu"].items(), key=lambda kv: (-kv[1], kv[0])):
        por_pessoa.append([n, vivo["atendendo"].get(n, 0), vivo["concluiu"].get(n, 0),
                           q, vivo["msgs"].get(n, 0)])
    por_pessoa += [
        ["TOTAL (soma por pessoa)", sum(vivo["atendendo"].values()),
         sum(vivo["concluiu"].values()), sum(vivo["atendeu"].values()),
         sum(vivo["msgs"].values())],
        [VAZIO],
        [f"{len(vivo['atendeu'])} pessoas atenderam alguma conversa. Conversa "
         "transferida conta para as duas pessoas que falaram nela, então a soma por "
         "pessoa pode passar do total do dia."],
        ["Para 'quem NÃO atendeu': compare com a aba Comparativo, que mostra quem "
         "costuma aparecer. Quem atende todo dia e não está aqui, não pegou conversa."],
    ]

    # Chamados AO VIVO, pelo mesmo motivo das conversas: a base só é atualizada pela
    # coleta diária, e a aba congelava no dia anterior.
    chv = chamados_ao_vivo.ler(dia_vivo, dt.datetime.now(BRT))
    metr = ["concluiu", "moveu_fluxo", "mexeu_status", "abriu", "tocou"]
    quem = {n for k in metr for n in chv.get(k, {})}
    ordem = sorted(quem, key=lambda n: (-chv.get("tocou", {}).get(n, 0), n))
    cham: list[list] = [
        [f"Chamados por pessoa — AO VIVO, {rotv}"],
        ["Última execução", f"{dt.datetime.fromisoformat(f['em']):%d/%m/%Y %H:%M}"],
        [VAZIO],
        ["Chamados mexidos hoje", chv.get("chamados_mexidos", 0)],
        [VAZIO],
        ["Trabalho feito NO chamado. Abrir é registrar o problema; mover e concluir é "
         "resolvê-lo, e em geral são pessoas diferentes."],
        ["Conta chamados distintos, não eventos. Não há coluna de 'respondeu': "
         "comentário em chamado acabou em 27/11/2025 e a resposta migrou para o chat."],
        [VAZIO],
        ["Pessoa", "Concluiu", "Moveu no fluxo", "Mexeu no status", "Abriu",
         "Chamados que tocou"],
    ]
    for n in ordem:
        cham.append([n] + [chv.get(k, {}).get(n, 0) for k in metr])
    cham.append(["TOTAL (por pessoa, soma)"]
                + [sum(chv.get(k, {}).values()) for k in metr])

    # Comparativo do cache de leituras ao vivo, não da base. Dia fechado é lido uma vez
    # e guardado em atendimento_por_dia.json; hoje vem da leitura desta execução.
    cache = {}
    if atendimento_ao_vivo.CACHE.exists():
        cache = json.loads(atendimento_ao_vivo.CACHE.read_text(encoding="utf-8"))
    cache[dia_vivo] = vivo
    dias = sorted(cache)[-(compara + 1):]
    comp: list[list] = [
        ["Conversas atendidas por pessoa, por dia"],
        ["Última execução", f"{dt.datetime.fromisoformat(f['em']):%d/%m/%Y %H:%M}"],
        ["Todos os dias são lidos da API, com paginação completa — inclusive os "
         "fechados. O último dia é o de hoje, ainda em andamento."],
        [VAZIO],
        ["Pessoa"] + [f"{d[8:]}/{d[5:7]}" for d in dias],
    ]
    atend = {d: (cache[d].get("atendeu") or {}) for d in dias}
    todas = {n for d in dias for n in atend[d]}
    for n in sorted(todas, key=lambda x: -atend[dia_vivo].get(x, 0)):
        comp.append([n] + [atend[d].get(n) or VAZIO for d in dias])
    for rotulo, chave in (("TOTAL atendidas", "atendidas"),
                          ("Conversas no dia", "total"),
                          ("Nunca atendidas", "sem_atendimento")):
        comp.append([rotulo] + [cache[d].get(chave, VAZIO) for d in dias])

    return {"Por pessoa": por_pessoa, "Chamados por pessoa": cham,
            "Comparativo": comp}


def _nada():
    return None


def aba_legenda(f: dict, dia: str) -> list[list]:
    return [
        ["Legenda — de onde vem cada número"],
        [VAZIO],
        ["Aba", "O que é", "Com que frequência muda"],
        ["Agora", "A fila neste instante, lida ao vivo da API do Bitrix. Não depende do "
         "relatório diário nem de classificação por IA.", "A cada execução"],
        ["Fila por hora", "Uma linha por execução, para ver a fila subindo e descendo "
         "ao longo do dia.", "A cada execução (uma linha nova)"],
        ["Atendimentos por pessoa", "Quem está atendendo e quem concluiu HOJE, lido ao "
         "vivo da API. Não é o mesmo número do arquivo Excel: o Excel vem da base, que "
         "guarda no máximo 50 mensagens por conversa e por isso subconta conversa "
         "longa.", "A cada execução"],
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


def retangular(linhas: list[list]) -> list[list]:
    """Completa toda linha com "" até a largura da mais larga.

    O `values.update` do Sheets **não apaga** célula que a linha não menciona: linha de
    uma coluna deixa B..E com o conteúdo da escrita anterior. Na primeira publicação os
    números da versão antiga ficaram vazando à direita dos sumarizadores, e isso num
    painel que a gestão lê é pior que célula vazia.
    """
    largura = max((len(l) for l in linhas), default=1)
    return [list(l) + [""] * (largura - len(l)) for l in linhas]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", required=True)
    ap.add_argument("--dia", help="dia fechado das abas de atendimento (padrão: ontem)")
    ap.add_argument("--compara", type=int, default=10)
    ap.add_argument("--horario", "--so-fila", dest="horario", action="store_true",
                    help="aceito por compatibilidade; não muda mais o que é montado. "
                         "Todas as abas vêm da API desde que a base se mostrou limitada "
                         "a 50 mensagens por conversa, e a passada completa custa cerca "
                         "de um minuto")
    a = ap.parse_args()

    agora = dt.datetime.now(BRT)
    dia = a.dia or (agora.date() - dt.timedelta(days=1)).isoformat()

    print("lendo a fila ao vivo...")
    f = ler_fila(agora)
    print(f"  esperando {f['esperando']} · em andamento {f['andamento']} · "
          f"chamados abertos {f['chamados_abertos']}")
    print("montando as abas de atendimento (tudo da API)...")
    abas = abas_atendimento(dia, a.compara, agora.date().isoformat(), f,
                            so_api=False)
    abas["Agora"] = aba_agora(f)
    abas["Backlog de chamados"] = aba_backlog(f)
    if not a.horario:
        abas["Legenda"] = aba_legenda(f, dia)

    abas = {nome: retangular(linhas) for nome, linhas in abas.items()}

    # Onde ficou cada linha que precisa de formatação própria. O número de pessoas muda
    # todo dia, então a linha de TOTAL anda — e formatação aplicada a um índice fixo
    # acaba na linha errada, que foi exatamente como a planilha ficou feia depois da
    # primeira republicação. Quem publica usa estes índices em vez de adivinhar.
    def achar(nome: str, prefixo: str) -> int | None:
        for i, l in enumerate(abas.get(nome, []), start=1):
            if str(l[0]).startswith(prefixo):
                return i
        return None

    formato = {
        nome: {k: v for k, v in (
            ("cabecalho", achar(nome, "Pessoa")),
            ("total", achar(nome, "TOTAL")),
            ("ultima_linha", len(linhas)),
        ) if v}
        for nome, linhas in abas.items()
    }
    saida = {"em": f["em"], "dia_atendimento": dia, "formato": formato,
             "cabecalho_hora": CAB_HORA, "linha_hora": aba_hora(f), "abas": abas}
    Path(a.saida).write_text(json.dumps(saida, ensure_ascii=False, indent=1) + "\n",
                             encoding="utf-8", newline="\n")
    for nome, linhas in abas.items():
        print(f"  {nome:24} {len(linhas)} linhas")
    print(f"\ngravado em {a.saida}")


if __name__ == "__main__":
    main()
