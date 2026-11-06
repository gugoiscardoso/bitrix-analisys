# -*- coding: utf-8 -*-
"""Pergunta ao Bitrix o status ATUAL dos chamados que ainda não fecharam.

O problema que isto resolve: o merge do `consolidar_store.py` faz o export mais novo
sobrescrever o mais velho, então o status de um chamado é o do dia em que ele foi
coletado pela última vez. A janela diária pega dois dias. Chamado de agosto que fechou
em setembro continua "em andamento" na planilha para sempre.

Medido em 05/11/2026: uma amostra de 88 chamados que a base dizia abertos sugeriu 3%
de deriva, e o sweep completo dos 1.051 achou **84 já fechados — 8%**. A amostra era
pequena demais, e fica o registro de que foi a medição completa, não a estimativa, que
deu a resposta.

A coluna Status é a única do relatório que descreve o presente e não o passado; se ela
mentir, mente sem avisar. Custa ~20 chamadas de API para zerar.

**Por que um arquivo próprio e não um patch na base:** `base_historica.jsonl` é derivado
e o `consolidar_store.py` o reconstrói inteiro a cada rodada. Patch aplicado nele se
perde na rodada seguinte. Então gravamos `data/store/status_chamados.json`, que é
versionado, pequeno e auditável, e o consolidador o aplica como override.

**Por que lê os exports crus e não a base:** para que a ordem seja
`coletar → atualizar_status → consolidar → gerar`, numa passada só. Ler a base exigiria
consolidar antes e depois — foi exatamente o erro que o `enriquecer_autores.py` cometeu
quando lia só a base consolidada.

Uso:
    python pipeline/atualizar_status.py              # só os que não fecharam
    python pipeline/atualizar_status.py --todos      # reconfere todo mundo
"""
from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RAW = RAIZ / "data" / "raw"
STORE = RAIZ / "data" / "store"
DESTINO = STORE / "status_chamados.json"
CONFIG = RAIZ / "Ultracar-Support-Bitrix-Analisys" / "appsettings.json"

# Os mesmos códigos que o consolidar_store.py traduz. Duplicar o dicionário seria
# convidar as duas cópias a divergirem, então importamos de lá.
sys.path.insert(0, str(RAIZ / "pipeline"))
from consolidar_store import STATUS  # noqa: E402

FINAIS = {"concluída", "recusada"}
POR_LOTE = 50          # teto do endpoint `batch` do Bitrix
PAUSA = 0.4            # segundos entre lotes; o Bitrix limita por segundo


def webhook() -> str:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    return cfg["Bitrix"]["WebhookUrl"].rstrip("/")


def status_dos_exports() -> dict[str, str]:
    """Id -> status, tomando o export mais novo, igual ao consolidar_store.py."""
    atual: dict[str, str] = {}
    for arq in sorted(RAW.glob("bitrix_export_*.json")):
        try:
            dados = json.loads(arq.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  AVISO: {arq.name} ilegível ({type(e).__name__}), ignorado")
            continue
        # Mesma estrutura que o consolidar_store.py lê: cada item de "tasks" é um
        # envelope com a tarefa em ["task"] e as tags ao lado dela.
        for td in dados.get("tasks", []):
            t = (td or {}).get("task") or {}
            tid = t.get("id")
            if tid is None:
                continue
            bruto = t.get("status")
            atual[str(tid)] = STATUS.get(str(bruto), str(bruto))
    return atual


def consultar(base: str, ids: list[str]) -> dict[str, str]:
    """Status atual de cada id, via o endpoint `batch` (50 por chamada)."""
    fora: dict[str, str] = {}
    for i in range(0, len(ids), POR_LOTE):
        fatia = ids[i:i + POR_LOTE]
        campos = {"halt": "0"}
        for tid in fatia:
            campos[f"cmd[t{tid}]"] = f"tasks.task.get?taskId={tid}&select[]=STATUS"
        corpo = urllib.parse.urlencode(campos).encode()
        req = urllib.request.Request(f"{base}/batch", data=corpo)
        try:
            with urllib.request.urlopen(req, timeout=60) as f:
                resposta = json.load(f)
        except Exception as e:
            print(f"  ERRO no lote {i // POR_LOTE + 1}: {type(e).__name__}: {e}")
            print("  Nada foi gravado. Rode de novo; o arquivo anterior está intacto.")
            sys.exit(1)
        res = (resposta.get("result") or {}).get("result") or {}
        for chave, valor in res.items():
            tid = chave[1:]                       # tira o "t" do prefixo
            tarefa = (valor or {}).get("task") or {}
            bruto = tarefa.get("status")
            if bruto is not None:
                fora[tid] = STATUS.get(str(bruto), str(bruto))
        print(f"  {min(i + POR_LOTE, len(ids))}/{len(ids)}")
        time.sleep(PAUSA)
    return fora


def main() -> None:
    todos = "--todos" in sys.argv
    base = webhook()

    dos_exports = status_dos_exports()
    print(f"chamados nos exports: {len(dos_exports)}")

    # O que já está num status final não muda mais, e não vale uma chamada de API.
    # Com --todos ignoramos essa economia, para o caso de um chamado ser reaberto.
    ja_sabido = json.loads(DESTINO.read_text(encoding="utf-8")) if DESTINO.exists() else {}
    confirmado_final = {
        i for i, v in ja_sabido.get("status", {}).items() if v in FINAIS
    }

    alvo = [
        i for i, s in dos_exports.items()
        if todos or (s not in FINAIS and i not in confirmado_final)
    ]
    print(f"a consultar no Bitrix: {len(alvo)}"
          + ("" if todos else f" (pulando {len(dos_exports) - len(alvo)} já finais)"))
    if not alvo:
        print("nada a fazer.")
        return

    novos = consultar(base, alvo)

    # Só gravamos o que DIVERGE do export. O arquivo é override, não cópia da base:
    # guardar o que já está igual faria dele uma segunda fonte de verdade para o
    # mesmo dado, e aí uma teria de ganhar da outra.
    override = dict(ja_sabido.get("status", {}))
    mudou = 0
    for i, s in novos.items():
        if s != dos_exports.get(i):
            if override.get(i) != s:
                mudou += 1
            override[i] = s
        else:
            override.pop(i, None)

    DESTINO.write_text(
        json.dumps({"em": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "consultados": len(alvo),
                    "status": dict(sorted(override.items(), key=lambda kv: int(kv[0])))},
                   ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8", newline="\n")

    fechou = sum(1 for i, s in override.items() if s in FINAIS)
    print(f"\n{DESTINO.name}: {len(override)} override(s), {mudou} novo(s) nesta rodada")
    print(f"  dos quais {fechou} são chamados que fecharam depois da última coleta")
    print("\nAgora rode: python pipeline/consolidar_store.py")


if __name__ == "__main__":
    main()
