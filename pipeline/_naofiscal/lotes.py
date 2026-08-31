#!/usr/bin/env python
"""Lotes + prompt para classificar os chamados não-fiscais."""
import json, sys, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
STORE = AQUI.parents[1] / "data" / "store"
DE, ATE = "2026-05-01", "2026-08-08"
OUTRO = "Outro / não se encaixa"

tax = json.loads((STORE / "taxonomia_nao_fiscal.json").read_text(encoding="utf-8"))
L = ["# Classificação de chamados NÃO fiscais — Ultracar (ERP automotivo)", "",
     "Cada item tem `id` e `t` (título e descrição de um chamado de suporte).",
     "Atribua a CADA item EXATAMENTE UM tema da lista, com a string EXATA.", "",
     "Estes chamados já foram separados: **não** tratam de nota fiscal, imposto,",
     "certificado ou SEFAZ. Se algum parecer fiscal, ainda assim escolha o tema",
     "não-fiscal que melhor descreve o pedido.", "", "## Temas", ""]
for t in tax["temas"]:
    L.append(f'- "{t["nome"]}"')
    if t.get("descricao"):
        L.append(f'  {t["descricao"]}')
L += ["", f'- "{OUTRO}" — não cabe em nenhum acima. Use com parcimônia: é o sinal de que',
      "  a taxonomia precisa crescer.", "",
      "## Regras",
      "- Classifique pela CAUSA CENTRAL, não por palavras soltas.",
      "- **DEFEITO x PEDIDO**: sistema faz errado é defeito; sistema não tem o recurso é",
      "  pedido. São temas diferentes e a distinção é a mais importante desta lista.",
      "- Se tocar dois temas, escolha o que dominou o atendimento.",
      "- As cláusulas FRONTEIRA nas descrições decidem os casos ambíguos.", "",
      "## Saída",
      "APENAS um objeto JSON, id -> nome exato do tema. Todo id do lote deve aparecer.", "",
      "## Eficiência",
      "Leia o lote UMA vez e escreva a saída UMA vez. Não releia o arquivo."]
(AQUI / "prompt.md").write_text("\n".join(L), encoding="utf-8")

itens = []
with (STORE / "base_historica.jsonl").open(encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        if r["tipo"] == "chamado" and not r["fiscal"] and DE <= r["data"] <= ATE:
            t = ((r.get("titulo") or "") + " " + (r.get("texto") or "")).strip()[:1200]
            itens.append({"id": str(r["id"]), "t": t})
for i in range(0, len(itens), 220):
    (AQUI / f"lote_{i//220+1}.json").write_text(
        json.dumps(itens[i:i+220], ensure_ascii=False, indent=1), encoding="utf-8")
p = (AQUI / "prompt.md").read_text(encoding="utf-8")
print(f"{len(itens)} chamados -> {-(-len(itens)//220)} lotes | prompt {len(p)} chars")
