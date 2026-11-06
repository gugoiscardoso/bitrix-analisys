# -*- coding: utf-8 -*-
"""
Descobre quem falou cada mensagem das conversas, para a transcrição do relatório.

    python pipeline/enriquecer_autores.py            # só o que falta
    python pipeline/enriquecer_autores.py --tudo     # refaz do zero

Existe porque o exportador em C# perde essa informação: ele lê `author_id`, `AUTHOR_ID`
e `id_user`, e o campo que `imopenlines.session.history.get` devolve chama-se
**`senderid`**. Resultado: `AuthorType=System` em 100% das 296 mil mensagens de todos os
exports. A correção no C# é de uma linha, mas só entra nos dados recoletando tudo —
este script pega apenas o que falta, direto da API, sem mexer na coleta.

O papel NÃO é adivinhado pelo texto. O bloco `users` do histórico traz o flag
`connector`, que o Bitrix liga para quem entrou pelo canal externo: é o cliente. Sem
flag e com id real, é atendente. Sem id (ou id 0), é mensagem de plataforma.

Escreve `data/store/remetentes.json` = {sessionId: {messageId: papel}}. `consolidar_store`
usa esse arquivo ao montar as transcrições; sem ele, a transcrição sai sem rótulo.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
STORE = RAIZ / "data" / "store"
SAIDA = STORE / "remetentes.json"
POR_LOTE = 50          # teto do batch do Bitrix
PAUSA = 0.4            # respiro entre lotes; a API limita por segundo
TENTATIVAS = 3

sys.stdout.reconfigure(encoding="utf-8")


def webhook() -> str:
    cfg = json.loads((RAIZ / "Ultracar-Support-Bitrix-Analisys" / "appsettings.json")
                     .read_text(encoding="utf-8-sig"))

    def achar(o):
        if isinstance(o, dict):
            for v in o.values():
                if isinstance(v, str) and "bitrix24.com/rest/" in v:
                    return v
                if (r := achar(v)):
                    return r
        return None

    url = achar(cfg)
    if not url:
        raise SystemExit("Não achei o webhook em appsettings.json.")
    return url.rstrip("/")


def datas_das_conversas() -> dict[str, str]:
    """Sessão -> data de início (AAAA-MM-DD), do export mais recente que a contenha.

    Serve para saber o que é recente, e recente é o que precisa ser rebuscado: a
    conversa de hoje foi mapeada com as mensagens que tinha na hora da coleta, e cresceu
    depois.

    **Por que uma janela de dias, e não um detector exato.** Tentei dois:

    1. Comparar o tamanho do mapa com o total de mensagens da base. Inútil: o mapa exclui
       mensagem de sistema de propósito e a mediana da razão é 0,48 — qualquer corte
       nessa escala parte a distribuição no meio em vez de achar defeito.
    2. Comparar com `OperatorMessages` do export, que seria exato. Mas o exportador C#
       classifica **100% das mensagens como sistema** (mesmo bug de autor que motivou
       este script), então `OperatorMessages` é 0 em todas as 554 sessões do último
       export. O campo existe e não vale nada.

    O único detector exato seria perguntar à API, que é o que se quer evitar. Então:
    janela. Medido por amostragem de 20 sessões por mês, mapa contra API — março, julho e
    outubro deram 0 desatualizadas; novembro, 11 de 20. O que separa não é razão nenhuma,
    é a conversa ter sido coletada enquanto ainda estava aberta.
    """
    import pandas as pd
    fora: dict[str, str] = {}
    for arq in sorted((RAIZ / "data" / "raw").glob("conversations_export_*.xlsx")):
        try:
            df = pd.read_excel(arq, sheet_name="Conversations",
                               usecols=["SessionId", "StartedAt"])
        except Exception as e:
            print(f"  aviso: sem StartedAt em {arq.name} ({type(e).__name__}); "
                  "as sessões dele só serão rebuscadas se estiverem ausentes do mapa")
            continue
        for sid, quando in zip(df["SessionId"], df["StartedAt"]):
            if pd.isna(sid) or pd.isna(quando):
                continue
            fora[str(int(sid))] = str(quando)[:10]
    return fora


def sessoes_da_base() -> list[str]:
    """Ids de sessão, dos exports CRUS e da base consolidada.

    Precisa ler os exports, não só a base: a base só ganha as conversas novas depois
    do `consolidar_store.py`, então rodar este script logo após a coleta — que é a
    ordem natural e a documentada — não encontrava nada para buscar. Lendo os dois,
    ele funciona antes ou depois da consolidação.
    """
    ids = set()
    for arq in sorted((RAIZ / "data" / "raw").glob("conversations_export_*.xlsx")):
        try:
            import pandas as pd
            col = pd.read_excel(arq, sheet_name="Conversations", usecols=["SessionId"])
            ids.update(str(int(x)) for x in col["SessionId"].dropna())
        except Exception as e:
            print(f"  aviso: não li {arq.name} ({type(e).__name__})")
    base = STORE / "base_historica.jsonl"
    if base.exists():
        with base.open(encoding="utf-8") as fh:
            for linha in fh:
                r = json.loads(linha)
                if r["tipo"] == "conversa":
                    ids.add(str(r["id"]))
    return sorted(ids, key=int)


def papel_de(sender: str, users: dict) -> str:
    """Quem é o remetente. Vazio ou '0' é a própria plataforma falando."""
    if sender in ("", "0", "None"):
        return "sistema"
    u = users.get(sender) if isinstance(users, dict) else None
    if u is None:
        return "sistema"
    if u.get("connector"):
        return "Cliente"
    if u.get("bot"):
        return "Robô"
    nome = (u.get("name") or "").strip()
    return f"Atendente ({nome})" if nome else "Atendente"


def buscar_lote(base: str, ids: list[str]) -> dict[str, dict[str, str]]:
    cmds = {f"h{i}": f"imopenlines.session.history.get?SESSION_ID={s}"
            for i, s in enumerate(ids)}
    corpo = urllib.parse.urlencode({f"cmd[{k}]": v for k, v in cmds.items()}).encode()
    for tentativa in range(1, TENTATIVAS + 1):
        try:
            req = urllib.request.Request(f"{base}/batch", data=corpo)
            with urllib.request.urlopen(req, timeout=180) as resp:
                j = json.loads(resp.read().decode("utf-8"))
            break
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            if tentativa == TENTATIVAS:
                print(f"  lote falhou em definitivo ({type(e).__name__}); segue adiante")
                return {}
            time.sleep(2 * tentativa)

    res = (j.get("result") or {}).get("result") or {}
    out = {}
    for chave, hist in res.items():
        if not isinstance(hist, dict):
            continue
        sid = ids[int(chave[1:])]
        users = hist.get("users") or {}
        msgs = hist.get("message") or {}
        it = msgs.values() if isinstance(msgs, dict) else msgs
        # Grava só o que não é sistema: é ~45% das mensagens, e o arquivo fica menos
        # da metade. Mensagem ausente do mapa é tratada como plataforma na leitura.
        mapa = {}
        for m in it:
            papel = papel_de(str(m.get("senderid") or ""), users)
            if papel != "sistema":
                mapa[str(m.get("id"))] = papel
        out[sid] = mapa
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tudo", action="store_true",
                    help="refaz todas as sessões em vez de só as que faltam")
    ap.add_argument("--dias-frescos", type=int, default=10,
                    help="quantos dias para trás são rebuscados mesmo já mapeados")
    ap.add_argument("--limite", type=int, default=0,
                    help="para depois de N sessões; para testar sem gastar a janela toda")
    a = ap.parse_args()

    base = webhook()
    feito = {} if a.tudo else (json.loads(SAIDA.read_text(encoding="utf-8"))
                               if SAIDA.exists() else {})
    todas = sessoes_da_base()
    # Sessão AUSENTE do mapa precisa ser buscada. Sessão RECENTE também, mesmo já
    # mapeada, porque ela cresceu depois de ter sido mapeada.
    #
    # Isto era `[s for s in todas if s not in feito]`, e o efeito foi grave: a coleta da
    # manhã pega o dia corrente com as conversas ainda abertas, então uma conversa
    # iniciada às 9h era mapeada com 1 ou 2 mensagens e as 48 seguintes ficavam sem autor
    # PARA SEMPRE. Na transcrição viram "(sistema)", e a contagem de atendimento feita
    # sobre elas subcontou — chegou a dizer que o suporte atendeu 37% em 05/11 quando
    # atendeu 97%. Ver a seção retratada em tasks/incidentes_detectados.md.
    #
    # Por que a janela de dias e não um detector mais fino: tentei comparar o tamanho do
    # mapa com a contagem de mensagens da base, mas o mapa exclui mensagem de sistema de
    # propósito e a mediana da razão é 0,48 — qualquer corte nessa escala parte a
    # distribuição no meio em vez de achar defeito. Medindo mapa contra API por
    # amostragem: março, julho e outubro deram 0 de 20 desatualizados; novembro, 11 de
    # 20. O que distingue não é razão nenhuma, é a conversa ter sido coletada enquanto
    # ainda estava aberta. Logo: rebusca a janela recente, e pronto.
    corte = (dt.date.today() - dt.timedelta(days=a.dias_frescos)).isoformat()
    datas = datas_das_conversas()
    recentes = {s for s in todas if datas.get(s, "9999") >= corte}
    ausentes = [s for s in todas if s not in feito]
    rebusca = [s for s in todas if s in feito and s in recentes]
    faltam = ausentes + rebusca
    print(f"  ausentes do mapa: {len(ausentes)} · recentes a rebuscar: {len(rebusca)} "
          f"(desde {corte}; conversa recente cresce depois de ser mapeada)")
    if a.limite:
        faltam = faltam[:a.limite]
    print(f"{len(todas)} conversas na base | {len(feito)} já mapeadas | "
          f"{len(faltam)} a buscar")
    if not faltam:
        print("Nada a fazer.")
        return 0

    t0 = time.time()
    for i in range(0, len(faltam), POR_LOTE):
        lote = faltam[i:i + POR_LOTE]
        feito.update(buscar_lote(base, lote))
        if (i // POR_LOTE) % 20 == 0 or i + POR_LOTE >= len(faltam):
            pronto = i + len(lote)
            decorrido = time.time() - t0
            resta = decorrido / max(pronto, 1) * (len(faltam) - pronto)
            print(f"  {pronto}/{len(faltam)}  ({decorrido/60:.1f} min decorridos, "
                  f"~{resta/60:.0f} min restantes)")
            # Grava no caminho: 100 minutos é tempo demais para perder tudo num erro.
            SAIDA.write_text(json.dumps(feito, ensure_ascii=False), encoding="utf-8")
        time.sleep(PAUSA)

    SAIDA.write_text(json.dumps(feito, ensure_ascii=False), encoding="utf-8")
    com_autor = sum(1 for v in feito.values() if v)
    msgs = sum(len(v) for v in feito.values())
    print(f"\nremetentes.json  {len(feito)} sessões, {com_autor} com mensagem de gente, "
          f"{msgs} mensagens rotuladas")
    print(f"tempo total: {(time.time()-t0)/60:.1f} min")
    print("\nAgora rode: python pipeline/consolidar_store.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
