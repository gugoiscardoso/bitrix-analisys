#!/usr/bin/env python
"""9.3.3 — divide o catch-all de P7 em defeito × dúvida.

`Destaque manual de impostos para bater com o espelho do fornecedor` é o maior
subgrupo de P7 (218, 20,1%) e virou balde de "imposto + devolução": mistura o defeito
específico e caro (o sistema não herda os valores da compra de origem) com a massa de
how-to (o cliente não sabe qual campo preencher). Enquanto estiverem juntos não dá para
separar "falta feature" de "falta documentação", que é a decisão que P7 exige agora que
subiu para 2º lugar.

Este script só mexe na TAXONOMIA e limpa o subgrupo dos 218 afetados. A reatribuição
é feita pelo classificador, em lote dedicado com as duas opções novas.
"""
import json, sys, io, shutil
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[2]
STORE = RAIZ / "data" / "store"
ANTIGO = "Destaque manual de impostos para bater com o espelho do fornecedor"

NOVOS = [
    {"nome": "Espelho do fornecedor: valores da compra de origem não são herdados",
     "descricao":
        "DEFEITO DE SISTEMA. O fornecedor manda espelho/autorização de devolução exigindo "
        "BC ICMS, ICMS, ICMS ST, IPI, frete e outras despesas idênticos aos da nota de "
        "compra, e recusa se divergir — às vezes por um centavo. O sistema não traz esses "
        "valores da compra de origem, mesmo já sabendo qual é a NF-e de compra e tendo os "
        "dados no XML importado; o cliente digita item a item, e o botão 'calcular tributos' "
        "sobrescreve o que ele preencheu à mão. Use quando o atendimento mostra o cliente "
        "TENTANDO bater valores com um espelho/nota de origem, ou perdendo o que digitou. "
        "FRONTEIRA: se o cliente apenas não sabe qual campo preencher ou o que é cada "
        "imposto, sem espelho a bater, use o subgrupo de dúvida de preenchimento."},
    {"nome": "Dúvida de preenchimento de imposto na devolução (IPI, PIS/COFINS, ICMS, frete)",
     "descricao":
        "FALTA DE ORIENTAÇÃO, não defeito. O cliente está emitindo devolução ou garantia e "
        "pergunta o que colocar em IPI, PIS/COFINS, ICMS ou frete — não sabe se inclui, se "
        "zera, qual CST usar no imposto, onde fica o campo. Não há espelho do fornecedor a "
        "ser replicado nem valor perdido: é desconhecimento da regra fiscal ou da tela. "
        "FRONTEIRA: se o cliente está tentando REPRODUZIR valores de uma nota de origem, ou "
        "se o sistema apagou o que ele digitou, use o subgrupo do espelho do fornecedor."},
]

p = STORE / "sub_p7.json"
dados = json.loads(p.read_text(encoding="utf-8"))
antigo = next((sg for sg in dados["subgrupos"] if sg["nome"] == ANTIGO), None)
if not antigo:
    print(f"'{ANTIGO}' não está mais em sub_p7.json — nada a fazer.")
    raise SystemExit(0)

shutil.copy(p, p.with_suffix(".json.pre_divisao"))
idx = dados["subgrupos"].index(antigo)
herdado = {k: v for k, v in antigo.items() if k not in ("nome", "descricao")}
dados["subgrupos"][idx:idx + 1] = [dict(herdado, **novo) for novo in NOVOS]
p.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"sub_p7.json: '{ANTIGO[:40]}...' -> 2 subgrupos")
for n in NOVOS:
    print(f"  + {n['nome']}")

cp = STORE / "classificacao.json"
cache = json.loads(cp.read_text(encoding="utf-8"))
shutil.copy(cp, cp.with_suffix(".json.pre_divisao"))
n = 0
for chave in ("chamados", "conversas"):
    for d in cache[chave].values():
        if d.get("subgrupo") == ANTIGO:
            d["subgrupo"] = ""      # fica sem subgrupo até o classificador reatribuir
            n += 1
cp.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"\n{n} registros ficaram sem subgrupo, aguardando reatribuição")
print("Rode consolidar_store.py para propagar a taxonomia.")
