# -*- coding: utf-8 -*-
"""A fila de atendimento AGORA, lida direto da API, mais as abas de atendimento.

Responde a uma terceira pergunta, diferente das outras duas do projeto:

- `gerar_relatorio_completo.py` → o que dói, por assunto, no ano. Retrospectivo.
- `gerar_atendimento.py`        → quem atendeu quanto, por dia. Retrospectivo.
- este                          → **quem está esperando agora.** Ao vivo.

**Não passa pelo pipeline e não classifica nada.** Lê a fila direto do Bitrix em
segundos, sem custo de IA — é isso que torna viável rodar de hora em hora. O pipeline
diário leva minutos e paga leitura; isto não.

## O corte que dá sentido ao número

"Não concluído" e "não atendido" são coisas diferentes, e quem lê age diferente em cada:

- **Esperando**: a sessão está aberta e **ninguém do suporte falou ainda**. É gente
  olhando a tela agora. Medido em 06/11 10:37: 120 conversas, mediana de 100 min.
- **Em andamento**: aberta, mas alguém já respondeu. São 129, e a maioria com mais de
  4 h — conversa que fica aberta porque ninguém encerra, não porque ninguém atendeu.

Entregar só "abertas" (249) junta as duas e esconde a urgente.

## Dois relógios, em abas separadas de propósito

A fila de conversas se move em minutos. O backlog de chamados se move em meses: 1.152
abertos, mediana de 98 dias, 904 com mais de 30 dias. Misturar os dois na mesma tabela
faria a fila parecer saudável ou o backlog parecer urgente, e nenhum dos dois é verdade.

## Campos da API que já me enganaram

- O histórico vem em `result["message"]`, **não** `messages`, e é **dict** indexado por
  id de mensagem, não lista. Lendo `messages` eu tive "0 de 247 atendidas", que é
  absurdo e só não foi publicado porque conversa aberta há 25 h sem resposta não existe.
- `tasks.task.list` devolve `{"result": {"tasks": [...]}}` com o total em `total`. Lendo
  `result` direto eu contei 24 chamados abertos quando são 1.152.
- No bloco `users` do histórico, `connector=True` marca o **cliente**. `senderid == "0"`
  é mensagem de sistema (boas-vindas, transferência) e não conta como atendimento.

Uso:
    python pipeline/fila_agora.py                     # imprime o retrato
    python pipeline/fila_agora.py --json saida.json   # grava para publicar na planilha
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CONFIG = RAIZ / "Ultracar-Support-Bitrix-Analisys" / "appsettings.json"
BRT = dt.timezone(dt.timedelta(hours=-3))
PROVIDER = "IMOPENLINES_SESSION"
CONCLUIDA = "5"
JANELA_DIAS = 7          # sessões abertas mais antigas que isto não entram no retrato
POR_LOTE = 50            # teto do endpoint `batch`

FAIXAS = [("menos de 15 min", 0, 15), ("15 a 60 min", 15, 60), ("1 a 4 h", 60, 240),
          ("4 a 24 h", 240, 1440), ("mais de 24 h", 1440, float("inf"))]
FAIXAS_DIAS = [("aberto hoje", 0, 1), ("1 a 7 dias", 1, 8), ("8 a 30 dias", 8, 31),
               ("mais de 30 dias", 31, float("inf"))]

sys.path.insert(0, str(RAIZ / "pipeline"))


def cfg() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))["Bitrix"]


def get(base: str, metodo: str, params: dict) -> dict:
    url = f"{base}/{metodo}?" + urllib.parse.urlencode(params, doseq=True)
    with urllib.request.urlopen(url, timeout=120) as f:
        return json.load(f)


def paginar(base: str, metodo: str, params: dict, chave: str | None = None) -> list:
    fora, start = [], 0
    while True:
        q = dict(params)
        q["start"] = start
        j = get(base, metodo, q)
        res = j.get("result")
        if chave:
            res = (res or {}).get(chave) or []
        res = res or []
        fora += res
        prox = j.get("next")
        if not prox or not res:
            return fora
        start = prox          # sem esta linha o laço refaz a página 1 para sempre


def atendida(hist: dict) -> bool:
    """Alguém do suporte falou nesta sessão?

    `message` é dict por id. `senderid == "0"` é o sistema. No bloco `users`,
    `connector=True` é o cliente — qualquer outro autor humano é do suporte.
    """
    msgs = hist.get("message") or {}
    itens = list(msgs.values()) if isinstance(msgs, dict) else list(msgs)
    users = hist.get("users") or {}
    for m in itens:
        quem = str(m.get("senderid") or "")
        if quem in ("", "0", "None"):
            continue
        if not (users.get(quem) or {}).get("connector"):
            return True
    return False


def faixas(minutos: list[float], tabela) -> list[tuple[str, int]]:
    return [(nome, sum(1 for x in minutos if lo <= x < hi)) for nome, lo, hi in tabela]


def ler_fila(agora: dt.datetime) -> dict:
    c = cfg()
    base = c["WebhookUrl"].rstrip("/")
    desde = (agora - dt.timedelta(days=JANELA_DIAS)).strftime("%Y-%m-%dT%H:%M:%S%z")

    ses = paginar(base, "crm.activity.list", {
        "filter[PROVIDER_ID]": PROVIDER, "filter[>CREATED]": desde,
        "select[]": ["ID", "CREATED", "COMPLETED", "END_TIME",
                     "ASSOCIATED_ENTITY_ID"],
        "order[CREATED]": "ASC"})

    hoje, ontem = agora.date(), agora.date() - dt.timedelta(days=1)
    por_dia = collections.defaultdict(collections.Counter)
    abertas = {}
    # A HORA CORRENTE ATÉ AGORA: do topo da hora até este instante. Às 08:50 isso é
    # 08:00-08:50, e a coluna "Hora medida" declara essa janela, então a linha nunca
    # mente sobre o que contém.
    #
    # Era a hora ANTERIOR completa, e fazia sentido quando a execução era de hora em
    # hora. Com execução de 10 em 10 minutos atualizando a mesma linha, a hora anterior
    # daria o mesmo número seis vezes seguidas e a atualização não faria nada. O preço
    # desta escolha é que a linha de uma hora em curso está sempre incompleta — e é por
    # isso que a janela medida vai escrita ao lado.
    entraram_hora = fechadas_hora = 0
    ini_hora = agora.replace(minute=0, second=0, microsecond=0)
    fim_hora = agora

    for a in ses:
        criada = dt.datetime.fromisoformat(a["CREATED"]).astimezone(BRT)
        aberta = str(a.get("COMPLETED", "")).upper() != "Y"
        rot = ("hoje" if criada.date() == hoje
               else "ontem" if criada.date() == ontem else "antes")
        por_dia[rot]["entraram"] += 1
        por_dia[rot]["abertas" if aberta else "fechadas"] += 1
        if ini_hora <= criada < fim_hora:
            entraram_hora += 1
        # Fechadas NA hora é quando a sessão foi encerrada, não quando entrou. END_TIME
        # marca o encerramento (bate com LAST_UPDATED nas fechadas); nas abertas ele vem
        # igual ao CREATED, e o filtro por COMPLETED já as exclui.
        if not aberta and a.get("END_TIME"):
            fim = dt.datetime.fromisoformat(a["END_TIME"]).astimezone(BRT)
            if ini_hora <= fim < fim_hora:
                fechadas_hora += 1
        sid = a.get("ASSOCIATED_ENTITY_ID")
        if aberta and sid:
            abertas[str(sid)] = (criada, rot)

    # Histórico só das abertas, PAGINADO: a chamada simples traz as 50 mensagens mais
    # novas, e o atendente costuma falar no começo. Sem paginar, conversa longa aberta
    # aparece como "ninguém respondeu", que é o número mais grave desta planilha.
    from historico import completo
    esperando, andamento = [], []
    espera_por_dia = collections.Counter()
    ids = list(abertas)
    for sid, v in completo(base, ids).items():
        if sid not in abertas:
            continue
        criada, rot = abertas[sid]
        idade = (agora - criada).total_seconds() / 60
        if atendida(v):
            andamento.append(idade)
        else:
            esperando.append(idade)
            espera_por_dia[rot] += 1

    # chamados: outro relógio, aba própria
    tot = get(base, "tasks.task.list", {"filter[GROUP_ID]": c["GroupId"],
                                        "filter[!STATUS]": CONCLUIDA,
                                        "select[]": ["ID"]}).get("total")
    ch = paginar(base, "tasks.task.list", {
        "filter[GROUP_ID]": c["GroupId"], "filter[!STATUS]": CONCLUIDA,
        "select[]": ["ID", "CREATED_DATE", "STATUS"]}, chave="tasks")
    dias = sorted((agora - dt.datetime.fromisoformat(t["createdDate"]).astimezone(BRT)).days
                  for t in ch if t.get("createdDate"))

    esperando.sort()
    andamento.sort()
    return {
        "em": agora.isoformat(timespec="seconds"),
        "janela_dias": JANELA_DIAS,
        "esperando": len(esperando),
        "andamento": len(andamento),
        "abertas": len(esperando) + len(andamento),
        "espera_max_min": round(esperando[-1]) if esperando else 0,
        "espera_mediana_min": round(esperando[len(esperando) // 2]) if esperando else 0,
        "faixas_espera": faixas(esperando, FAIXAS),
        "esperando_de_ontem": espera_por_dia["ontem"] + espera_por_dia["antes"],
        "esperando_de_hoje": espera_por_dia["hoje"],
        "entraram_hoje": por_dia["hoje"]["entraram"],
        "fechadas_hoje": por_dia["hoje"]["fechadas"],
        "entraram_ontem": por_dia["ontem"]["entraram"],
        "fechadas_ontem": por_dia["ontem"]["fechadas"],
        "abertas_de_ontem": por_dia["ontem"]["abertas"] + por_dia["antes"]["abertas"],
        "entraram_na_hora": entraram_hora,
        "fechadas_na_hora": fechadas_hora,
        "hora_medida": f"{ini_hora:%H:%M}-{fim_hora:%H:%M}",
        "chamados_abertos": tot,
        "chamados_mediana_dias": dias[len(dias) // 2] if dias else 0,
        "chamados_max_dias": dias[-1] if dias else 0,
        "faixas_chamados": faixas(dias, FAIXAS_DIAS),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="grava o retrato num arquivo, para publicar")
    a = ap.parse_args()

    agora = dt.datetime.now(BRT)
    f = ler_fila(agora)

    print(f"FILA EM {agora:%d/%m/%Y %H:%M}\n")
    print(f"  esperando (ninguém respondeu):  {f['esperando']}")
    print(f"  em andamento (já respondidas):  {f['andamento']}")
    print(f"  mais antiga esperando:          {f['espera_max_min'] / 60:.1f} h")
    print(f"  mediana de espera:              {f['espera_mediana_min']} min")
    print("\n  quem está esperando, por tempo:")
    for nome, q in f["faixas_espera"]:
        print(f"    {nome:18} {q}")
    print(f"\n  esperando que entrou ontem ou antes: {f['esperando_de_ontem']}")
    print(f"  esperando que entrou hoje:           {f['esperando_de_hoje']}")
    print(f"\n  hoje:  {f['entraram_hoje']} entraram, {f['fechadas_hoje']} fechadas")
    print(f"  ontem: {f['entraram_ontem']} entraram, {f['fechadas_ontem']} fechadas, "
          f"{f['abertas_de_ontem']} seguem abertas")
    print(f"\n  CHAMADOS não concluídos: {f['chamados_abertos']} "
          f"(mediana {f['chamados_mediana_dias']} dias, "
          f"mais antigo {f['chamados_max_dias']})")
    for nome, q in f["faixas_chamados"]:
        print(f"    {nome:18} {q}")

    if a.json:
        Path(a.json).write_text(json.dumps(f, ensure_ascii=False, indent=2) + "\n",
                                encoding="utf-8", newline="\n")
        print(f"\ngravado em {a.json}")


if __name__ == "__main__":
    main()
