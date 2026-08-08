#!/usr/bin/env python
"""9.3.2 — escreve a regra de fronteira entre os dois subgrupos de CFOP/CST.

P1 e P7 tinham o mesmo subgrupo com nomes diferentes. O critério que de fato os
separa já operava na prática (P7 é 99,2% devolução; P1, 23,9%) mas nunca foi escrito,
e por isso o classificador escorregava na fronteira.

Regra: o discriminador é a FINALIDADE DO DOCUMENTO, não o erro.

Idempotente: reescreve o mesmo texto se rodar de novo.
"""
import json, sys, io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
STORE = Path(__file__).resolve().parents[2] / "data" / "store"

MARCA = "FRONTEIRA COM"

REGRA_P1 = (
    " FRONTEIRA COM P7: use este subgrupo apenas quando o documento em questão é uma nota "
    "de VENDA, serviço ou operação comum. Se o erro de CFOP/CST está acontecendo na emissão "
    "de uma nota de DEVOLUÇÃO, GARANTIA, REMESSA ou RETORNO, o subgrupo correto é "
    "'CFOP, CST/CSOSN e regime tributário incompatíveis' (P7), mesmo que a mensagem de "
    "rejeição seja idêntica. O discriminador é a finalidade do documento, não o erro."
)
REGRA_P7 = (
    " FRONTEIRA COM P1: use este subgrupo apenas quando o documento em questão é uma nota "
    "de DEVOLUÇÃO, GARANTIA, REMESSA ou RETORNO. Se o erro de CFOP/CST está acontecendo numa "
    "nota de VENDA ou serviço comum, o subgrupo correto é 'CFOP/CST incompatíveis com a "
    "operação ou regime (devolução, idDest, grupos de imposto)' (P1), mesmo que a mensagem "
    "de rejeição seja idêntica. O discriminador é a finalidade do documento, não o erro."
)

alvos = [
    ("propostas.json", "CFOP/CST incompatíveis com a operação", REGRA_P1),
    ("sub_p7.json", "CFOP, CST/CSOSN e regime tributário", REGRA_P7),
]

for arquivo, chave, regra in alvos:
    p = STORE / arquivo
    dados = json.loads(p.read_text(encoding="utf-8"))
    grupos = (dados["subgrupos"] if "subgrupos" in dados
              else [sg for v in dados.values() for sg in v["subgrupos"]])
    n = 0
    for sg in grupos:
        if chave in sg["nome"]:
            base = sg["descricao"].split(MARCA)[0].rstrip()
            sg["descricao"] = base + regra
            n += 1
    p.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{arquivo:16} {n} subgrupo(s) atualizado(s)")

print("\nRode `python pipeline/consolidar_store.py` para propagar à taxonomia.")
