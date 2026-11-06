# -*- coding: utf-8 -*-
"""Guarda os números de cada execução, para que as conferências tenham com o que comparar.

Duas verificações do pipeline eram inexecutáveis por falta de linha de base:

- "o total de registros tem de ter crescido" — crescido em relação a quê? `base_historica.jsonl`
  está no .gitignore, e o consolidador imprime só o total de hoje.
- "as conversas da V3 só crescem; se despencaram, pare" — este é o portão do bug do
  `str(17.0)`, que apagou a marcação V3 de 164 conversas e quase passou. Numa sessão
  nova às 9h da manhã não existe o número de ontem, então o portão nunca disparava.

Um portão que nunca dispara é pior que portão nenhum: ele dá a sensação de cobertura.

Este script grava uma linha por execução em `data/store/serie_diaria.json`, que é
versionado (poucos KB por ano) e serve de linha de base para a execução seguinte.

    python pipeline/serie_diaria.py --registrar     # grava a linha de hoje
    python pipeline/serie_diaria.py                 # compara com a última e sai 1 se regrediu
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
STORE = RAIZ / "data" / "store"
SERIE = STORE / "serie_diaria.json"

# Quedas acima destes limites param o pipeline. Não é zero porque recoleta pode
# reclassificar um punhado de registros de fronteira; é apertado porque os bugs que
# isto pega (tipo de coluna do pandas) derrubam centenas de uma vez.
TOLERANCIA = {"registros": 0, "conversas_v3": 0, "leituras": 0}


def medir() -> dict:
    tipos = collections.Counter()
    v3 = 0
    for linha in (STORE / "base_historica.jsonl").open(encoding="utf-8"):
        r = json.loads(linha)
        tipos[r["tipo"]] += 1
        if r["tipo"] == "conversa" and r.get("versao") == "V3":
            v3 += 1
    leitura = json.loads((STORE / "leitura_completa.json").read_text(encoding="utf-8"))
    return {
        "em": dt.datetime.now().isoformat(timespec="seconds"),
        "registros": sum(tipos.values()),
        "chamados": tipos["chamado"],
        "conversas": tipos["conversa"],
        "conversas_v3": v3,
        "leituras": len(leitura["chamados"]) + len(leitura["conversas"]),
    }


def carregar() -> list[dict]:
    if not SERIE.exists():
        return []
    return json.loads(SERIE.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registrar", action="store_true",
                    help="grava a linha de hoje depois de comparar")
    a = ap.parse_args()

    agora = medir()
    serie = carregar()
    anterior = serie[-1] if serie else None

    print("hoje:  " + " · ".join(f"{k}={agora[k]}" for k in
                                 ("registros", "chamados", "conversas", "conversas_v3",
                                  "leituras")))
    if not anterior:
        print("\nNão há execução anterior registrada — nada a comparar.")
        print("Esta primeira linha passa a ser a linha de base das próximas.")
    else:
        print(f"última ({anterior['em'][:16]}): "
              + " · ".join(f"{k}={anterior[k]}" for k in
                           ("registros", "chamados", "conversas", "conversas_v3",
                            "leituras")))
        quedas = []
        for campo, tol in TOLERANCIA.items():
            delta = agora[campo] - anterior[campo]
            seta = "+" if delta >= 0 else ""
            print(f"  {campo:14} {seta}{delta}")
            if delta < -tol:
                quedas.append(f"{campo} caiu {-delta} (tolerância {tol})")
        if quedas:
            print("\nREGREDIU:")
            for q in quedas:
                print(f"  - {q}")
            print("\nNão entregue. Estes números só crescem; queda é sinal de que algo")
            print("quebrou a montagem da base — ver `str(17.0)` em tasks/lessons.md.")
            return 1

    if a.registrar:
        serie.append(agora)
        SERIE.write_text(json.dumps(serie, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8", newline="\n")
        print(f"\nregistrado em {SERIE.name} ({len(serie)} execuções)")
    else:
        print("\n(não gravei; use --registrar para incluir esta execução na série)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
