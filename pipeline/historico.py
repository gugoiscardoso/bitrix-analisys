# -*- coding: utf-8 -*-
"""Histórico COMPLETO de sessões de openlines, paginado, em lote.

Existe porque `imopenlines.session.history.get` devolve **só 50 mensagens** e avisa com
`hasNextPage`/`nextId`. Quem ignora isso lê a conversa pela metade — e a metade que vem
é a MAIS NOVA, então o que se perde é o começo, onde o atendente entra.

Custou três correções publicadas do mesmo número antes de alguém (eu) ler a resposta
inteira do endpoint. Ver `tasks/lessons.md`.

Como paginar: a primeira chamada traz as 50 mais novas e `nextId` = a mais antiga delas.
`LAST_ID=<nextId>` traz as anteriores a essa. Repete enquanto `hasNextPage`.

Tudo vai pelo endpoint `batch`, 50 comandos por chamada, porque sessão por sessão não
termina: são 45 mil sessões.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request

POR_LOTE = 50
MAX_PAGINAS = 40          # 40 × 50 = 2.000 mensagens; nenhuma conversa real chega perto


def _lote(base: str, pedidos: dict[str, str]) -> dict:
    """pedidos: {chave: querystring}. Devolve {chave: result}."""
    campos = {"halt": "0"}
    for chave, qs in pedidos.items():
        campos[f"cmd[{chave}]"] = qs
    req = urllib.request.Request(f"{base}/batch",
                                 data=urllib.parse.urlencode(campos).encode())
    with urllib.request.urlopen(req, timeout=300) as f:
        return ((json.load(f).get("result") or {}).get("result") or {})


def _mensagens(res: dict) -> list[dict]:
    msgs = res.get("message") or {}
    return list(msgs.values()) if isinstance(msgs, dict) else list(msgs)


def completo(base: str, ids: list[str], progresso=None) -> dict[str, dict]:
    """{session_id: {"message": [...], "users": {...}}} com TODAS as páginas.

    `message` sai como **lista**, não dict, porque juntar páginas num dict indexado por
    id convidaria a sobrescrever silenciosamente. A lista vem ordenada por id.
    """
    fora: dict[str, dict] = {}
    pendente: dict[str, str] = {}          # sid -> LAST_ID da próxima página

    for i in range(0, len(ids), POR_LOTE):
        fatia = ids[i:i + POR_LOTE]
        res = _lote(base, {f"s{s}": f"imopenlines.session.history.get?SESSION_ID={s}"
                           for s in fatia})
        for chave, v in res.items():
            sid, v = chave[1:], (v or {})
            fora[sid] = {"message": _mensagens(v), "users": dict(v.get("users") or {})}
            if v.get("hasNextPage") and v.get("nextId"):
                pendente[sid] = str(v["nextId"])
        if progresso:
            progresso(min(i + POR_LOTE, len(ids)), len(ids))

    # agora as páginas seguintes, só das sessões que avisaram ter mais
    pagina = 0
    while pendente and pagina < MAX_PAGINAS:
        pagina += 1
        alvo = list(pendente.items())
        if progresso:
            progresso(len(ids), len(ids), extra=f"página {pagina + 1}: "
                                                f"{len(alvo)} sessões ainda têm mais")
        pendente = {}
        for i in range(0, len(alvo), POR_LOTE):
            fatia = dict(alvo[i:i + POR_LOTE])
            res = _lote(base, {
                f"s{s}": f"imopenlines.session.history.get?SESSION_ID={s}&LAST_ID={lid}"
                for s, lid in fatia.items()})
            for chave, v in res.items():
                sid, v = chave[1:], (v or {})
                novas = _mensagens(v)
                if not novas:
                    continue
                fora[sid]["message"] += novas
                fora[sid]["users"].update(v.get("users") or {})
                if v.get("hasNextPage") and v.get("nextId"):
                    pendente[sid] = str(v["nextId"])

    if pendente:
        print(f"  AVISO: {len(pendente)} sessões ainda tinham páginas após "
              f"{MAX_PAGINAS} rodadas. Isso não deveria acontecer — alguma conversa "
              "tem mais de 2.000 mensagens, ou a paginação não está avançando.")

    for v in fora.values():
        v["message"].sort(key=lambda m: int(m.get("id") or 0))
    return fora
