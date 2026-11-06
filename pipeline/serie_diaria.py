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

Desde 06/11/2026 ele também vigia o robô N1 (`n1_conversas`, `n1_modulos`), mas em outra
categoria: **avisa e segue, sem parar o pipeline**. O motivo está em `VIGIADOS_N1` lá
embaixo — o N1 é fonte externa com licença para falhar, e um portão duro aqui desfaria
essa licença pelas costas. O que não podia continuar é a fonte não ser olhada por
ninguém, que era o caso até então.

Campo ausente não é queda a zero: sem store do N1 a medida simplesmente não existe, e as
linhas gravadas antes de 06/11/2026 não têm esses campos. Os dois casos imprimem o
estado em vez de inventar alarme.

**Roda duas vezes, e a ordem importa:**

    python pipeline/serie_diaria.py                 # logo após consolidar: só confere,
                                                    # sai 1 se regrediu, para o pipeline
    python pipeline/serie_diaria.py --registrar     # no fim, depois da leitura: grava

Na primeira versão isto rodava uma vez só, com `--registrar`, logo após a consolidação —
antes do passo de leitura. Resultado: o campo `leituras` gravava o valor de *antes* de
ler, ficando sempre uma execução atrasado. Em 06/11 a série dizia 18.716 quando o arquivo
tinha 18.791. O portão não ficava falso para `registros` e `conversas_v3`, que vêm da
consolidação, mas para `leituras` uma queda real seria mascarada por um dia de leitura
normal. Conferir antes e gravar depois resolve os dois lados.
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

# O N1 é vigiado, mas NÃO para o pipeline. Os dois motivos:
#
# 1. É fonte externa — uma planilha que um CronJob de outro projeto alimenta. O passo do
#    N1 tem licença explícita para falhar sem parar o job (ver a skill, passo 7), porque
#    é eixo lateral: derrubar o relatório do suporte humano porque a planilha de outro
#    sistema está fora do ar seria trocar o entregável pelo acessório. Um portão duro
#    aqui desfaria essa licença pelas costas.
# 2. O store dele é refeito do zero a cada coleta, e não se acumula como a base. Se o N1
#    algum dia podar linhas antigas da planilha, o espelho encolhe — e isso é notícia,
#    não corrupção.
#
# Então: queda aqui imprime AVISO e segue. O que não pode é passar em silêncio, que era
# o caso até 06/11/2026 — a série não olhava para esta fonte.
VIGIADOS_N1 = {"n1_conversas": 0, "n1_modulos": 0}

# Campos que podem faltar legitimamente, e cuja ausência NÃO é queda a zero: sem store
# do N1 não há medida, e tratar "não medido" como "caiu para zero" inventaria um alarme
# toda vez que a coleta do N1 falhasse ou num clone novo, onde o espelho não é versionado.
OPCIONAIS = set(VIGIADOS_N1)

CAMPOS_IMPRESSOS = ("registros", "chamados", "conversas", "conversas_v3", "leituras",
                    "n1_conversas", "n1_modulos")


def medir_n1() -> dict:
    """Volume e cobertura de leitura do robô N1, ou {} se não houver store.

    Devolver {} em vez de zeros é deliberado: zero e "não medido" são coisas
    diferentes, e só a segunda é o estado normal de quem não coletou o N1.
    """
    origem = STORE / "n1_conversas.jsonl"
    if not origem.exists():
        return {}
    n = sum(1 for linha in origem.open(encoding="utf-8") if linha.strip())
    cls = STORE / "classificacao_n1.json"
    lidos = 0
    if cls.exists():
        lidos = len(json.loads(cls.read_text(encoding="utf-8"))["conversas"])
    return {"n1_conversas": n, "n1_modulos": lidos}


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
        **medir_n1(),
    }


def resumir(linha: dict) -> str:
    """Só os campos que a linha tem: as linhas gravadas antes de 06/11/2026 não têm N1."""
    return " · ".join(f"{k}={linha[k]}" for k in CAMPOS_IMPRESSOS if k in linha)


def carregar() -> list[dict]:
    if not SERIE.exists():
        return []
    return json.loads(SERIE.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registrar", action="store_true",
                    help="grava a linha de hoje depois de comparar. Rode SEM isto logo "
                         "após consolidar (o portão, que pode parar o pipeline) e COM "
                         "isto no fim, depois da leitura — senão o campo `leituras` "
                         "fica sempre uma execução atrasado")
    a = ap.parse_args()

    agora = medir()
    serie = carregar()
    anterior = serie[-1] if serie else None

    print("hoje:  " + resumir(agora))
    if "n1_conversas" not in agora:
        print("       (sem store do N1 — rode `python pipeline/coletar_n1.py`; "
              "não é erro, o N1 é opcional)")
    if not anterior:
        print("\nNão há execução anterior registrada — nada a comparar.")
        print("Esta primeira linha passa a ser a linha de base das próximas.")
    else:
        print(f"última ({anterior['em'][:16]}): " + resumir(anterior))
        quedas, avisos = [], []
        for campo, tol in {**TOLERANCIA, **VIGIADOS_N1}.items():
            if campo not in agora:
                print(f"  {campo:14} não medido")
                continue
            if campo not in anterior:
                print(f"  {campo:14} sem linha de base (primeira execução com "
                      f"este campo)")
                continue
            delta = agora[campo] - anterior[campo]
            seta = "+" if delta >= 0 else ""
            print(f"  {campo:14} {seta}{delta}")
            if delta < -tol:
                queixa = f"{campo} caiu {-delta} (tolerância {tol})"
                (avisos if campo in VIGIADOS_N1 else quedas).append(queixa)
        if avisos:
            # Alto, e sem mudar o código de saída: ver VIGIADOS_N1 lá em cima.
            print("\nAVISO — o robô N1 encolheu (não para o pipeline):")
            for q in avisos:
                print(f"  - {q}")
            print("  O espelho da planilha do N1 só cresce em operação normal. Queda")
            print("  significa coleta pela metade ou linha podada na planilha de")
            print("  origem. O relatório humano não é afetado; a aba do N1, sim.")
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
