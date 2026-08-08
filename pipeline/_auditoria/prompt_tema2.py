#!/usr/bin/env python
"""Prompt de tema REESCRITO e REORDENADO, para o teste de complexidade da decisão.

O gabarito da camada B foi produzido pelo prompt de tema original. Reusá-lo aqui
inflaria a concordância por viés compartilhado. Este prompt cobre exatamente os
mesmos 22 assuntos, mas com redação diferente e ordem embaralhada por semente fixa,
para reduzir (não eliminar) essa herança.
"""
import json, random, sys, io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AUD = Path(__file__).resolve().parent
tax = json.loads((AUD.parents[1] / "data/store/taxonomia.json").read_text(encoding="utf-8"))

temas = [t for t in tax["temas"] if t["frente"] != "P5"]   # P5 nunca valeu para conversa
random.Random(4242).shuffle(temas)

L = ["# Triagem de atendimento fiscal por ASSUNTO — Ultracar (ERP automotivo)", "",
     "Cada item traz `id` e `t`, a transcrição de um chat de suporte.",
     "Escolha para cada item UM assunto da lista, copiando a string exatamente.", "",
     "## Lista de assuntos", ""]
for t in temas:
    L.append(f'- "{t["nome"]}"')

L += ["", "## Como decidir",
      "- Pergunte-se: qual foi o motivo pelo qual o cliente procurou o suporte?",
      "- Ignore termos que aparecem de passagem; vale o que ocupou o atendimento.",
      "- Se o cliente trouxe dois motivos, fique com o que consumiu o atendimento.",
      "- Julgue apenas pelo que está escrito. Não complete o que falta.", "",
      "## Saída",
      "Responda APENAS com um objeto JSON, id -> assunto exato, por exemplo:",
      '{"240185": "Cancelamento/exclusão de nota", "240189": "Conversa vazia / sem conteúdo útil"}',
      "Todo id do lote deve aparecer. Nada além do JSON.", "",
      "## Eficiência",
      "Leia o lote UMA vez e escreva a saída UMA vez. Não releia o arquivo."]

p = "\n".join(L)
(AUD / "prompts" / "tema2_conversa.md").write_text(p, encoding="utf-8")
print(f"prompt: {len(p)} chars (~{len(p)/3.5:.0f} tok), {len(temas)} assuntos")
print("ordem embaralhada — primeiros 3:")
for t in temas[:3]:
    print("   -", t["nome"][:64])
print("\ncomparar contra: produção 69 subgrupos = 72,7% (133/183)")
