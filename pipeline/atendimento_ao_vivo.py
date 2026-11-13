# -*- coding: utf-8 -*-
"""Atendimento por pessoa lido AO VIVO da API, para o dia corrente.

Por que existe, se `gerar_atendimento.py` já faz isso: ele lê a base consolidada, que
só é reconstruída pelo job das 9h. Num painel que atualiza de hora em hora, as abas por
pessoa mostrariam o dia anterior a manhã inteira. Este módulo responde a mesma pergunta
contra a API, então vale para **hoje, agora**.

## As duas contas podem divergir para o MESMO dia, e isso é esperado

O número da base muda depois, porque conversa de ontem que recebeu mensagem hoje volta
na coleta seguinte e cresce. Medido: em 05/11 à noite a base dava 85 conversas para o
João Brum; na manhã de 06/11, com a coleta nova, dava 97. A leitura ao vivo do dia 05
dá o valor **daquele instante**.

Regra para não enlouquecer quem compara: **ao vivo manda para hoje; a base manda para
dia fechado.** A planilha diz qual está mostrando.

## Como se sabe quem atendeu, na API

- `users[senderid].connector` → `True` é o **cliente**. `False` é gente do suporte.
- `senderid == "0"` é mensagem de sistema.
- O aceite da conversa é uma mensagem de sistema com a etiqueta
  `[USER=47515 REPLACE]Fellipe Freires[/USER] aceitou a conversa` (ou `picked
  conversation`, em inglês). **Aceitar conta como atender**, porque numa conversa
  transferida o autor das mensagens seguintes às vezes se perde.
- `Enquiry transferred to [USER=...]` **não** conta: encaminhar para alguém que nunca
  aceitou não é atendimento dela.

Uso:
    python pipeline/atendimento_ao_vivo.py                  # hoje
    python pipeline/atendimento_ao_vivo.py --dia 2026-11-05 # para conferir contra a base
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "pipeline"))

from fila_agora import BRT, cfg, paginar  # noqa: E402
from historico import completo  # noqa: E402

import urllib.parse  # noqa: E402
import urllib.request  # noqa: E402

ETIQUETA = re.compile(r"\[USER=(\d+)[^\]]*\]([^\[]+)\[/USER\]")
ACEITE = ("aceitou a conversa", "picked conversation", "aceitó la conversación")


def limpar(n: str) -> str:
    return re.sub(r"\s+", " ", (n or "").strip())


def quem_atendeu(hist: dict) -> tuple[set[str], set[str], collections.Counter]:
    """(atendeu, falou, mensagens por pessoa) de uma sessão."""
    msgs = hist.get("message") or []
    itens = list(msgs.values()) if isinstance(msgs, dict) else list(msgs)
    users = hist.get("users") or {}
    falou: set[str] = set()
    aceitou: set[str] = set()
    msg = collections.Counter()
    for m in itens:
        quem = str(m.get("senderid") or "")
        texto = m.get("text") or ""
        if quem in ("", "0", "None"):
            # mensagem de sistema: só interessa se é o aceite
            if any(s in texto for s in ACEITE):
                for _uid, nome in ETIQUETA.findall(texto):
                    aceitou.add(limpar(nome))
            continue
        u = users.get(quem) or {}
        if u.get("connector"):
            continue                      # cliente
        nome = limpar(u.get("name") or "")
        if nome:
            falou.add(nome)
            msg[nome] += 1
    return falou | aceitou, falou, msg


def ler(dia: str, agora: dt.datetime) -> dict:
    c = cfg()
    base = c["WebhookUrl"].rstrip("/")
    d0 = dt.datetime.fromisoformat(dia).replace(tzinfo=BRT)
    d1 = d0 + dt.timedelta(days=1)
    ses = paginar(base, "crm.activity.list", {
        "filter[PROVIDER_ID]": "IMOPENLINES_SESSION",
        "filter[>=CREATED]": d0.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "filter[<CREATED]": d1.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "select[]": ["ID", "CREATED", "COMPLETED", "ASSOCIATED_ENTITY_ID"],
        "order[CREATED]": "ASC"})
    ids = [str(a["ASSOCIATED_ENTITY_ID"]) for a in ses if a.get("ASSOCIATED_ENTITY_ID")]
    fechada = {str(a["ASSOCIATED_ENTITY_ID"]): str(a.get("COMPLETED", "")).upper() == "Y"
               for a in ses if a.get("ASSOCIATED_ENTITY_ID")}

    atendeu = collections.Counter()      # total, aberta ou fechada
    atendendo = collections.Counter()    # sessão AINDA ABERTA em que a pessoa falou
    concluiu = collections.Counter()     # sessão FECHADA em que a pessoa falou
    falou = collections.Counter()
    msgs = collections.Counter()
    n_atendidas = n_sem = n_fila = 0

    def eco(feito, total, extra=""):
        print(f"  {feito}/{total} {extra}", flush=True)

    # Paginado: a chamada simples devolve só as 50 mensagens MAIS NOVAS, e o atendente
    # costuma entrar no começo da conversa. Sem paginar, conversa longa aparece como
    # não atendida.
    hist = completo(base, ids, progresso=eco)
    for sid, v in hist.items():
        a, fa, m = quem_atendeu(v)
        esta_fechada = fechada.get(sid, False)
        for n in a:
            atendeu[n] += 1
            (concluiu if esta_fechada else atendendo)[n] += 1
        for n in fa:
            falou[n] += 1
        msgs.update(m)
        if a:
            n_atendidas += 1
        else:
            n_sem += 1
            if not esta_fechada:
                n_fila += 1       # ninguém falou E segue aberta: é cliente na fila

    return {"dia": dia, "em": agora.isoformat(timespec="seconds"),
            "total": len(ids), "atendidas": n_atendidas,
            "sem_atendimento": n_sem, "na_fila": n_fila,
            # nome antigo, que o montador da planilha ainda usa
            "abertas_sem_atend": n_fila,
            "atendeu": dict(atendeu), "atendendo": dict(atendendo),
            "concluiu": dict(concluiu), "falou": dict(falou), "msgs": dict(msgs)}


CACHE = RAIZ / "data" / "store" / "atendimento_por_dia.json"


def definitivo(r: dict, dia: str) -> bool:
    """A leitura guardada foi feita DEPOIS de o dia acabar?

    Leitura feita no próprio dia é retrato parcial. O 06/11/2026 foi guardado às 12:33
    daquele dia, com 194 conversas onde os vizinhos têm 470, e como a regra era só "não
    é hoje e está no arquivo", o retrato parcial ficou no Comparativo como definitivo.
    """
    try:
        return dt.datetime.fromisoformat(r["em"]).date().isoformat() > dia
    except (KeyError, TypeError, ValueError):
        return False


def com_cache(dia: str, agora: dt.datetime, hoje: str) -> dict:
    """Leitura de um dia, reaproveitando dias já lidos.

    Dia fechado não muda mais, então é lido uma vez e guardado. **Hoje é sempre relido**,
    porque é o único que ainda se move, e o mesmo vale para dia guardado antes de
    terminar (ver `definitivo`). Sem o cache, montar o comparativo de dez dias a cada
    execução levaria dez minutos em vez de um.

    O arquivo NÃO é versionado. Quem o preenche é o `montar_planilha.py`, a cada
    execução da tarefa agendada, e arquivo versionado que muda todo dia deixaria o
    repositório sujo para uma tarefa que promete não tocar nele. Um clone novo o
    reconstrói sozinho na primeira execução, ao custo de um minuto por dia da janela.
    """
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    if dia != hoje and dia in cache and definitivo(cache[dia], dia):
        return cache[dia]
    r = ler(dia, agora)
    cache[dia] = r
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1) + "\n",
                     encoding="utf-8", newline="\n")
    return r


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dia")
    ap.add_argument("--json")
    ap.add_argument("--cache", action="store_true",
                    help="guarda o resultado em atendimento_por_dia.json e reaproveita "
                         "dias já lidos; hoje é sempre relido")
    ap.add_argument("--ate", help="com --cache: lê de --dia até --ate, um dia por vez")
    a = ap.parse_args()
    agora = dt.datetime.now(BRT)
    dia = a.dia or agora.date().isoformat()
    hoje = agora.date().isoformat()
    if a.ate:
        d, fim = dt.date.fromisoformat(dia), dt.date.fromisoformat(a.ate)
        while d <= fim:
            print(f"lendo {d}...")
            com_cache(d.isoformat(), agora, hoje)
            d += dt.timedelta(days=1)
        print(f"\ncache em {CACHE}")
        return
    print(f"lendo o atendimento de {dia} ao vivo...")
    r = com_cache(dia, agora, hoje) if a.cache else ler(dia, agora)
    print(f"\n{r['total']} conversas · {r['atendidas']} atendidas · "
          f"{r['na_fila']} clientes na fila sem ninguém\n")
    print(f"{'pessoa':24}{'atendendo':>11}{'concluiu':>10}{'total':>7}{'msgs':>7}")
    for n, q in sorted(r["atendeu"].items(), key=lambda kv: -kv[1]):
        print(f"{n[:23]:24}{r['atendendo'].get(n, 0):11d}"
              f"{r['concluiu'].get(n, 0):10d}{q:7d}{r['msgs'].get(n, 0):7d}")
    if a.json:
        Path(a.json).write_text(json.dumps(r, ensure_ascii=False, indent=1) + "\n",
                                encoding="utf-8", newline="\n")
        print(f"\ngravado em {a.json}")


if __name__ == "__main__":
    main()
