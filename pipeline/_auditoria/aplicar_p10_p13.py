#!/usr/bin/env python
"""9.3.4 — grava os subgrupos derivados de P10..P13 na fonte da verdade.

A `fronteira` que cada subgrupo declara vai ANEXADA à descrição, não guardada num
campo à parte: o prompt do classificador é montado a partir da descrição, e uma regra
de fronteira que não chega ao prompt não serve para nada. Foi exatamente esse o defeito
de P1×P7 — o critério existia na cabeça de quem analisou e não no texto.
"""
import json, sys, io, shutil
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AUD = Path(__file__).resolve().parent
STORE = AUD.parents[1] / "data" / "store"
FRENTES = ["P10", "P11", "P12", "P13"]

saida = {}
total = 0
for fr in FRENTES:
    d = json.loads((AUD / "respostas" / f"DERIV_{fr}.json").read_text(encoding="utf-8"))
    subs = []
    for sg in d["subgrupos"]:
        desc = (sg.get("descricao") or "").strip()
        fron = (sg.get("fronteira") or "").strip()
        if fron:
            desc = f"{desc} FRONTEIRA: {fron}"
        subs.append({"nome": sg["nome"].strip(), "descricao": desc})
    saida[fr] = {"subgrupos": subs}
    total += len(subs)
    print(f"{fr}: {len(subs)} subgrupos")

p = STORE / "sub_p10_p13.json"
p.write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"\n{total} subgrupos gravados em {p.name}")

# Os registros dessas frentes carregam subgrupo = tema (herança de quando eram frentes
# de tema único). Esse nome deixa de ser subgrupo válido agora que há quebra de verdade,
# então precisa ser limpo para o classificador reatribuir.
cp = STORE / "classificacao.json"
cache = json.loads(cp.read_text(encoding="utf-8"))
shutil.copy(cp, cp.with_suffix(".json.pre_p10p13"))
n = 0
for chave in ("chamados", "conversas"):
    for d in cache[chave].values():
        if d.get("frente") in FRENTES and d.get("subgrupo"):
            d["subgrupo"] = ""
            n += 1
cp.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"{n} registros de P10–P13 tiveram o subgrupo limpo para reatribuição")
