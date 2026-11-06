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

from fila_agora import BRT, POR_LOTE, cfg, paginar  # noqa: E402

import urllib.parse  # noqa: E402
import urllib.request  # noqa: E402

ETIQUETA = re.compile(r"\[USER=(\d+)[^\]]*\]([^\[]+)\[/USER\]")
ACEITE = ("aceitou a conversa", "picked conversation", "aceitó la conversación")


def limpar(n: str) -> str:
    return re.sub(r"\s+", " ", (n or "").strip())


def quem_atendeu(hist: dict) -> tuple[set[str], set[str], collections.Counter]:
    """(atendeu, falou, mensagens por pessoa) de uma sessão."""
    msgs = hist.get("message") or {}
    itens = list(msgs.values()) if isinstance(msgs, dict) else msgs
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

    atendeu = collections.Counter()
    falou = collections.Counter()
    msgs = collections.Counter()
    n_atendidas = n_sem = 0
    for i in range(0, len(ids), POR_LOTE):
        campos = {"halt": "0"}
        for s in ids[i:i + POR_LOTE]:
            campos[f"cmd[s{s}]"] = f"imopenlines.session.history.get?SESSION_ID={s}"
        req = urllib.request.Request(f"{base}/batch",
                                     data=urllib.parse.urlencode(campos).encode())
        with urllib.request.urlopen(req, timeout=300) as f:
            res = ((json.load(f).get("result") or {}).get("result") or {})
        for chave, val in res.items():
            sid = chave[1:]
            a, fa, m = quem_atendeu(val or {})
            for n in a:
                atendeu[n] += 1
            for n in fa:
                falou[n] += 1
            msgs.update(m)
            if a:
                n_atendidas += 1
            elif not fechada.get(sid, True):
                n_sem += 1
        print(f"  {min(i + POR_LOTE, len(ids))}/{len(ids)}", flush=True)

    return {"dia": dia, "em": agora.isoformat(timespec="seconds"),
            "total": len(ids), "atendidas": n_atendidas, "abertas_sem_atend": n_sem,
            "atendeu": dict(atendeu), "falou": dict(falou), "msgs": dict(msgs)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dia")
    ap.add_argument("--json")
    a = ap.parse_args()
    agora = dt.datetime.now(BRT)
    dia = a.dia or agora.date().isoformat()
    print(f"lendo o atendimento de {dia} ao vivo...")
    r = ler(dia, agora)
    print(f"\n{r['total']} conversas · {r['atendidas']} atendidas · "
          f"{r['abertas_sem_atend']} abertas sem atendimento\n")
    print(f"{'pessoa':24}{'atendeu':>9}{'falou':>8}{'msgs':>7}")
    for n, q in sorted(r["atendeu"].items(), key=lambda kv: -kv[1]):
        print(f"{n[:23]:24}{q:9d}{r['falou'].get(n, 0):8d}{r['msgs'].get(n, 0):7d}")
    if a.json:
        Path(a.json).write_text(json.dumps(r, ensure_ascii=False, indent=1) + "\n",
                                encoding="utf-8", newline="\n")
        print(f"\ngravado em {a.json}")


if __name__ == "__main__":
    main()
