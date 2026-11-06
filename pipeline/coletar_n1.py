# -*- coding: utf-8 -*-
"""Coleta as conversas do robô de suporte N1 da planilha que o CronJob do N1 alimenta.

O N1 (`ultracar-support-ai`) guarda conversa em MongoDB sem API de listagem, mas um
CronJob exporta cada conversa ENCERRADA para a planilha `Ultracar - Conversation Report
- PROD`. Esta é a única porta de entrada prática, e ela é melhor do que parece: o Cron
já grava a conversa classificada pelo próprio N1 (resultado, precisão, lacuna de
conhecimento), então aqui não se classifica nada de novo — só se normaliza.

Credencial: a MESMA conta de serviço do relatório (`ultracar-report-chat-ai@…`), que já
é Editor da planilha do N1. `credencial()` vem de `publicar_relatorio` de propósito, para
existir um só lugar que sabe ler `local/sheets.env`.

## A coluna I guarda duas coisas diferentes, e a data decide qual

Na aba de prod o cabeçalho de I é "Ticket", mas o código do N1 escreve ali
`escalatedToN2 ? "Encaminhado ao N2" : "N/A"`
(`Infrastructure.ThirdParties/GoogleSheets/GoogleSheetsReportService.cs`). O cabeçalho
nunca foi atualizado. A virada está no DADO, não na documentação:

| Período | Coluna I |
|---|---|
| 27/08 a 06/10/2026 | número do chamado que o robô abriu no Bitrix, ou "N/A" |
| 06/10/2026 em diante | flag de escalação: "Encaminhado ao N2" ou "N/A" |

06/10 é o dia da virada — tem as duas formas. Por isso `VIRADA_FLAG` é 07/10, o primeiro
dia inteiro de flag: antes dele `escalou_n2` fica **None**, não False. Ler "N/A" de
setembro como "não escalou" inventaria um denominador que não existe e puxaria a taxa de
escalação para baixo. Com o corte certo a taxa de outubro é 54,9%; com 01/10, 47,5%.

## Por que um store à parte, e não `base_historica.jsonl`

Conversa do N1 é fricção que NÃO chegou ao suporte humano. Somar às humanas moveria o
denominador da série já publicada em +21,8% sem que nada tivesse mudado no mundo real
(decisão de 06/11/2026, em `tasks/n1_no_relatorio.md`). Então o N1 tem store próprio e
eixo próprio no relatório.

A transcrição vai em arquivo separado pelo mesmo motivo que em `transcricoes.json`: o
store é percorrido linha a linha e não deve engordar com o texto que só a aba lê.

Uso:
    python pipeline/coletar_n1.py            # incremental (só o que mudou)
    python pipeline/coletar_n1.py --tudo     # reescreve o store do zero
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))

from googleapiclient.discovery import build
from google.oauth2 import service_account

from publicar_relatorio import com_repeticao, credencial

RAIZ = Path(__file__).resolve().parent.parent
CONFIG = RAIZ / "Ultracar-Support-Bitrix-Analisys" / "appsettings.json"
STORE = RAIZ / "data" / "store"
ARQ_STORE = STORE / "n1_conversas.jsonl"
ARQ_TRANSCRICOES = STORE / "n1_transcricoes.json"
ARQ_COLETA = STORE / "coleta_n1.json"

ESCOPO = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
ABA = "Conversas"

# Primeiro dia inteiro em que a coluna I é flag de escalação. Ver docstring.
VIRADA_FLAG = "2026-10-07"

FLAG_ESCALOU = "Encaminhado ao N2"
FLAG_NAO = "N/A"


def servico():
    cred = service_account.Credentials.from_service_account_info(
        credencial(), scopes=ESCOPO)
    return build("sheets", "v4", credentials=cred, cache_discovery=False)


def id_planilha() -> str:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))["GoogleSheets"]
    sid = cfg.get("N1SpreadsheetId")
    if not sid:
        raise SystemExit(
            "Falta GoogleSheets.N1SpreadsheetId no appsettings.json.\n"
            "  É o id da planilha do CronJob do N1 (não é segredo, por isso versionado).")
    return sid


def ler_planilha(svc, sid: str) -> list[list]:
    req = svc.spreadsheets().values().get(
        spreadsheetId=sid, range=f"'{ABA}'",
        valueRenderOption="UNFORMATTED_VALUE",
        dateTimeRenderOption="FORMATTED_STRING")
    return com_repeticao(req, "ler planilha do N1").get("values", [])


def duracao_segundos(texto: str) -> int | None:
    """'91m 53s' -> 5513. O Cron grava minutos e segundos, nunca horas."""
    if not texto:
        return None
    m = re.findall(r"(\d+)\s*([hms])", texto.lower())
    if not m:
        return None
    peso = {"h": 3600, "m": 60, "s": 1}
    return sum(int(n) * peso[u] for n, u in m)


def precisao_fracao(texto: str) -> float | None:
    """'80 %' -> 0.8."""
    m = re.search(r"(\d+)", str(texto or ""))
    return int(m.group(1)) / 100 if m else None


def coluna_i(valor: str, data: str) -> tuple[str | None, bool | None]:
    """Devolve (chamado_id, escalou_n2) resolvendo as duas semânticas da coluna I."""
    valor = (valor or "").strip()
    if re.match(r"^\d{4,}", valor):
        # Número de chamado: a integração do robô com o Bitrix, que caiu em 30/09.
        return re.match(r"^(\d+)", valor).group(1), None

    # Antes da virada a coluna não fala de escalação, então `escalou_n2` fica None para
    # TODA linha anterior — inclusive as 16 que já traziam "Encaminhado ao N2" em 06/10,
    # o dia em que as duas formas convivem. Aproveitá-las e descartar os "N/A" do mesmo
    # dia contaria escalação sem contar o seu contrário, e a taxa subiria por viés de
    # seleção (56,8% em vez de 56,3%). Melhor o campo ter um só significado: medido sob
    # o regime estável.
    if data < VIRADA_FLAG:
        return None, None
    if valor == FLAG_ESCALOU:
        return None, True
    if valor == FLAG_NAO:
        return None, False
    return None, None


def normalizar(linha: list, idx: dict[str, int]) -> dict | None:
    def g(nome: str) -> str:
        i = idx.get(nome)
        if i is None or i >= len(linha):
            return ""
        return str(linha[i]).strip()

    cid = g("ID Conversa")
    if not cid:
        return None

    data = g("Data")
    hora = g("Hora")
    chamado_id, escalou = coluna_i(g("Ticket"), data)

    assunto, problema, resumo = g("Assunto"), g("Problema"), g("Resumo")
    # O texto que a classificação lê. Transcrição fica fora: a mediana é 1.104 caracteres
    # contra 270 destes três campos, e o assunto/problema/resumo já é o destilado que o
    # próprio N1 produziu.
    texto = "\n".join(p for p in (assunto, problema, resumo) if p)

    mensagens = g("Mensagens")
    return {
        "tipo": "conversa_n1",
        "id": cid,
        "data": data,
        "criado_em": f"{data}T{hora}" if data and hora else None,
        "assunto_n1": assunto,
        "problema": problema,
        "resumo": resumo,
        "texto": texto,
        "resultado": g("Resultado"),
        "analise_resultado": g("Analise resultado"),
        "precisao": precisao_fracao(g("Precisão")),
        "lacuna_kb": g("Lacunas (base de conhecimento)"),
        "chamado_id": chamado_id,
        "escalou_n2": escalou,
        "mensagens": int(mensagens) if str(mensagens).isdigit() else None,
        "duracao_seg": duracao_segundos(g("Duração")),
        "foi_util": {"Sim": True, "Não": False}.get(g("Foi útil?")),
        "matriz_id": g("Matrix ID"),
        "user_id": g("User ID"),
        "versao": g("Versão do ERP") or None,
        "cliente": g("Cliente"),
    }


def carregar_store() -> dict[str, dict]:
    if not ARQ_STORE.exists():
        return {}
    registros = {}
    for linha in ARQ_STORE.read_text(encoding="utf-8").splitlines():
        if linha.strip():
            r = json.loads(linha)
            registros[r["id"]] = r
    return registros


def gravar_store(registros: dict[str, dict]) -> None:
    ordenados = sorted(registros.values(), key=lambda r: (r.get("data") or "", r["id"]))
    with ARQ_STORE.open("w", encoding="utf-8", newline="\n") as f:
        for r in ordenados:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser(description="Coleta as conversas do robô N1.")
    ap.add_argument("--tudo", action="store_true",
                    help="reescreve o store do zero, em vez de mesclar")
    args = ap.parse_args()

    STORE.mkdir(parents=True, exist_ok=True)
    svc = servico()
    sid = id_planilha()

    print(f"Lendo a aba '{ABA}' da planilha do N1…")
    valores = ler_planilha(svc, sid)
    if not valores:
        raise SystemExit("A planilha voltou vazia.")
    cabecalho, *linhas = valores
    idx = {h: i for i, h in enumerate(cabecalho)}
    for obrigatoria in ("ID Conversa", "Data", "Resultado"):
        if obrigatoria not in idx:
            raise SystemExit(f"A aba mudou: não achei a coluna '{obrigatoria}'.")

    novos = {}
    transcricoes = {}
    for linha in linhas:
        r = normalizar(linha, idx)
        if r is None:
            continue
        novos[r["id"]] = r
        i = idx.get("Transcrição")
        if i is not None and i < len(linha) and str(linha[i]).strip():
            transcricoes[r["id"]] = str(linha[i])

    antes = {} if args.tudo else carregar_store()
    ineditos = [k for k in novos if k not in antes]
    # O N1 reconcilia linhas já escritas (ReconcileReportUseCase), então uma conversa
    # conhecida pode ter mudado de resultado. Mesclar sem comparar esconderia isso.
    mudados = [k for k in novos if k in antes and novos[k] != antes[k]]

    registros = {**antes, **novos}
    gravar_store(registros)

    if args.tudo or not ARQ_TRANSCRICOES.exists():
        antigas = {}
    else:
        antigas = json.loads(ARQ_TRANSCRICOES.read_text(encoding="utf-8"))
    antigas.update(transcricoes)
    ARQ_TRANSCRICOES.write_text(
        json.dumps(antigas, ensure_ascii=False), encoding="utf-8")

    datas = [r["data"] for r in registros.values() if r.get("data")]
    com_flag = [r for r in registros.values() if r.get("escalou_n2") is not None]
    escalaram = [r for r in com_flag if r["escalou_n2"]]
    ARQ_COLETA.write_text(json.dumps({
        "em": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "planilha": sid,
        "registros": len(registros),
        "novos": len(ineditos),
        "atualizados": len(mudados),
        "de": min(datas) if datas else None,
        "ate": max(datas) if datas else None,
        "virada_flag": VIRADA_FLAG,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"  {len(registros)} conversas no store "
          f"({len(ineditos)} novas, {len(mudados)} atualizadas)")
    print(f"  janela: {min(datas)} a {max(datas)}" if datas else "  sem datas")
    print(f"  com chamado no Bitrix: "
          f"{sum(1 for r in registros.values() if r.get('chamado_id'))}")
    if com_flag:
        print(f"  escalação medível em {len(com_flag)} conversas "
              f"(de {VIRADA_FLAG}): {len(escalaram)} escalaram "
              f"({100 * len(escalaram) / len(com_flag):.1f}%)")
    print(f"  → {ARQ_STORE}")
    print(f"  → {ARQ_TRANSCRICOES}")


if __name__ == "__main__":
    main()
