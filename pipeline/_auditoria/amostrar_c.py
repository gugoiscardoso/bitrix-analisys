#!/usr/bin/env python
"""Camada C: lotes e prompts de subgrupo POR FRENTE.

Replica as condicoes em que o rotulo foi produzido: o classificador original
rodou 'lotes por frente', escolhendo entre os ~8 subgrupos daquela frente.
Dar as 69 opcoes mediria uma tarefa mais dificil que a original e inflaria o erro.
O resultado e, portanto, acuracia CONDICIONAL: dado que a frente esta certa,
o subgrupo esta certo? A acuracia da frente vem da camada B.
"""
import json, random, sys, io, collections
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AUD = Path(__file__).resolve().parent
RAIZ = AUD.parents[1]
(AUD / "lotes").mkdir(exist_ok=True)
(AUD / "prompts").mkdir(exist_ok=True)

tax = json.loads((RAIZ / "data/store/taxonomia.json").read_text(encoding="utf-8"))
gab = json.loads((AUD / "gabarito.json").read_text(encoding="utf-8"))
titulos = {f["tag"]: f["titulo"] for f in tax["frentes"]}
por_frente = collections.defaultdict(list)
for s in tax["subgrupos"]:
    por_frente[s["frente"]].append(s)

base = {}
with (RAIZ / "data/store/base_historica.jsonl").open(encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        if r["tipo"] == "conversa":
            base[str(r["id"])] = r

itens = collections.defaultdict(list)
for k, m in gab.items():
    if m["camada"] != "C":
        continue
    rid = k.split("|")[2]
    itens[m["frente"]].append({"id": rid, "texto": (base[rid]["texto"] or "")[:2500]})

SAIDA = """
## Saída
APENAS um bloco JSON, id -> nome exato do subgrupo:
```json
{"240185": "<nome exato>"}
```
Todo id do lote deve aparecer. Nada além do JSON.

## Eficiência
Leia o lote UMA vez e escreva a saída UMA vez. Não releia o arquivo.
"""

print(f"{'frente':8} {'itens':>6} {'subgrupos':>10}  prompt")
for frente, lst in sorted(itens.items()):
    subs = por_frente[frente]
    L = [f"# Subgrupo dentro da frente {frente} — {titulos.get(frente,'')}", "",
         "Cada item tem `id` e `texto` (transcrição de um chat de suporte).",
         f"Todos os itens JÁ pertencem à frente {frente}. Atribua a CADA item",
         "EXATAMENTE UM subgrupo da lista abaixo, usando a string EXATA.", ""]
    for s in subs:
        if s["nome"].startswith("Outro"):
            continue
        L.append(f'- "{s["nome"]}"')
        d = (s.get("descricao") or "").strip()
        if d:
            L.append(f"  {d[:300]}")
    L += ["", f'- "Outro" — é da frente {frente} mas não cabe em nenhum subgrupo acima.',
          "  Use com parcimônia.", "",
          "## Regras",
          "- Classifique pela CAUSA CENTRAL, não por palavras soltas.",
          "- Se tocar dois subgrupos, escolha o que dominou o atendimento.",
          "- Na dúvida entre um subgrupo específico e 'Outro', prefira o específico.",
          SAIDA]
    p = AUD / "prompts" / f"sub_{frente}.md"
    p.write_text("\n".join(L), encoding="utf-8")
    for av, semente in (("av1", 101), ("av2", 202)):
        r = random.Random(semente + hash(frente) % 1000)
        emb = lst[:]
        r.shuffle(emb)
        (AUD / "lotes" / f"{av}_C{frente}_01.json").write_text(
            json.dumps(emb, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{frente:8} {len(lst):6} {len(subs):10}  {p.name} ({len(p.read_text(encoding='utf-8'))} chars)")
print(f"\ntotal itens: {sum(len(v) for v in itens.values())}")
print(f"agentes: {len(itens)*2}")
