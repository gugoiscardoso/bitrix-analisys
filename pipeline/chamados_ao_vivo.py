# -*- coding: utf-8 -*-
"""Trabalho feito nos chamados HOJE, lido ao vivo da API.

O `gerar_atendimento.py` lê o histórico dos chamados dos exports, que só são
atualizados pela coleta diária — então a aba congela no dia anterior. Este lê a API.

Duas chamadas: `tasks.task.list` filtrando por `CHANGED_DATE` traz os chamados mexidos
hoje, e `tasks.task.history.list` (em lote) traz os eventos de cada um. Os eventos são
filtrados pelo dia em Brasília; o histórico vem no fuso do servidor, `+03:00`, seis
horas à frente.

Conta **chamados distintos**, não eventos: mover o mesmo chamado cinco vezes é um
chamado movido.

Uso:
    python pipeline/chamados_ao_vivo.py
    python pipeline/chamados_ao_vivo.py --dia 2026-11-05
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
sys.path.insert(0, str(RAIZ / "pipeline"))

from fila_agora import BRT, cfg, get, paginar  # noqa: E402

CONCLUIDA = "5"
POR_LOTE = 50


def limpar(n: str) -> str:
    import re
    return re.sub(r"\s+", " ", (n or "").strip())


def ler(dia: str, agora: dt.datetime) -> dict:
    c = cfg()
    base = c["WebhookUrl"].rstrip("/")
    d0 = dt.datetime.fromisoformat(dia).replace(tzinfo=BRT)
    d1 = d0 + dt.timedelta(days=1)

    # Chamados mexidos no dia. CHANGED_DATE pega quem recebeu qualquer evento; quem foi
    # criado hoje também aparece, porque criar é mudar.
    tarefas = paginar(base, "tasks.task.list", {
        "filter[GROUP_ID]": c["GroupId"],
        "filter[>=CHANGED_DATE]": d0.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "filter[<CHANGED_DATE]": d1.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "select[]": ["ID", "CREATED_DATE", "CREATED_BY", "STATUS"]}, chave="tasks")
    ids = [str(t["id"]) for t in tarefas]
    print(f"  {len(ids)} chamados mexidos em {dia}")

    # Quem abriu: o creator do chamado criado no dia. Vem de tasks.task.get em lote,
    # porque o list não devolve o nome, só o id.
    por: dict[str, dict[str, set]] = collections.defaultdict(
        lambda: collections.defaultdict(set))

    for i in range(0, len(ids), POR_LOTE):
        fatia = ids[i:i + POR_LOTE]
        campos = {"halt": "0"}
        for t in fatia:
            campos[f"cmd[h{t}]"] = f"tasks.task.history.list?taskId={t}"
        req = urllib.request.Request(f"{base}/batch",
                                     data=urllib.parse.urlencode(campos).encode())
        with urllib.request.urlopen(req, timeout=300) as f:
            res = ((json.load(f).get("result") or {}).get("result") or {})
        for chave, v in res.items():
            tid = chave[1:]
            for h in ((v or {}).get("list") or []):
                quando = h.get("createdDate")
                u = h.get("user") or {}
                quem = limpar(f"{u.get('name') or ''} {u.get('lastName') or ''}")
                if not quando or not quem:
                    continue
                # O histórico vem em +03:00; sem converter, o fim da tarde cai no dia
                # seguinte e o número do dia fica errado nas duas pontas.
                if not (d0 <= dt.datetime.fromisoformat(quando).astimezone(BRT) < d1):
                    continue
                campo = h.get("field")
                por["tocou"][quem].add(tid)
                if campo == "NEW":
                    por["abriu"][quem].add(tid)
                elif campo == "STAGE":
                    por["moveu_fluxo"][quem].add(tid)
                elif campo == "STATUS":
                    if str((h.get("value") or {}).get("to")) == CONCLUIDA:
                        por["concluiu"][quem].add(tid)
                    else:
                        por["mexeu_status"][quem].add(tid)
        print(f"  {min(i + POR_LOTE, len(ids))}/{len(ids)}", flush=True)

    return {"dia": dia, "em": agora.isoformat(timespec="seconds"),
            "chamados_mexidos": len(ids),
            **{k: {n: len(s) for n, s in v.items()} for k, v in por.items()}}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dia")
    ap.add_argument("--json")
    a = ap.parse_args()
    agora = dt.datetime.now(BRT)
    dia = a.dia or agora.date().isoformat()
    print(f"lendo os chamados de {dia} ao vivo...")
    r = ler(dia, agora)
    metr = ["concluiu", "moveu_fluxo", "mexeu_status", "abriu", "tocou"]
    print(f"\n{'pessoa':24}" + "".join(f"{m[:12]:>14}" for m in metr))
    for n in sorted(r.get("tocou", {}), key=lambda x: -r["tocou"][x]):
        print(f"{n[:23]:24}" + "".join(f"{r.get(m, {}).get(n, 0):>14}" for m in metr))
    if a.json:
        Path(a.json).write_text(json.dumps(r, ensure_ascii=False, indent=1) + "\n",
                                encoding="utf-8", newline="\n")
        print(f"\ngravado em {a.json}")


if __name__ == "__main__":
    main()
