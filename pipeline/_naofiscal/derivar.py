#!/usr/bin/env python
"""Deriva a taxonomia dos chamados NÃO-fiscais.

A taxonomia fiscal fica congelada e intocada: misturar as duas quebraria a
comparabilidade entre execuções do relatório fiscal, que é o princípio da skill.
Esta vive num arquivo próprio e só encontra a outra na hora de gerar a planilha.

Amostra grande de propósito (a de P7/P8 usou 16% e a auditoria mediu 16% de erro
nelas; a de P10-P13 usou 36-66% e saiu melhor).
"""
import json, random, sys, io, collections, re
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
STORE = RAIZ / "data" / "store"
DE, ATE = "2026-05-01", "2026-08-08"
N = 260

TAG = re.compile(r"\s*\[([^\]]{1,30})\]")
pool, tags = [], collections.Counter()
with (STORE / "base_historica.jsonl").open(encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        if r["tipo"] != "chamado" or r["fiscal"] or not (DE <= r["data"] <= ATE):
            continue
        t = ((r.get("titulo") or "") + "\n" + (r.get("texto") or "")).strip()
        if len(t) > 60:
            pool.append(t[:1100])
        m = TAG.match(r.get("titulo") or "")
        tags[m.group(1).strip() if m else "(sem tag)"] += 1

sel = random.Random(808).sample(pool, min(N, len(pool)))
(AQUI / "amostra.json").write_text(json.dumps(sel, ensure_ascii=False, indent=1), encoding="utf-8")

dist = "\n".join(f"- [{k}] — {v} chamados" for k, v in tags.most_common(10))
prompt = f"""# Derivar a taxonomia dos chamados NÃO-fiscais — Ultracar (ERP automotivo)

O lote traz {len(sel)} chamados reais de suporte que **não são fiscais** — já foram
separados dos que tratam de nota, imposto, certificado ou SEFAZ. Sua tarefa é derivar a
subdivisão deles.

Contexto útil: o Bitrix já grava uma categoria entre colchetes no título. A distribuição
no universo completo é esta:

{dist}

**Não copie essas tags como resposta.** Elas são grosseiras e misturam coisas ("[Erro]"
não diz erro de quê, "[Melhoria]" não diz de qual módulo). Use-as como pista de onde o
volume está, e derive temas que digam a CAUSA.

## O que produzir

Entre **7 e 10 temas** que cubram o material. Para cada um:

- `nome` — curto e concreto, descrevendo a causa. Ruim: "Problemas de cadastro".
  Bom: "Cadastro de peça/serviço não reflete no orçamento".
- `descricao` — 2 a 4 frases: o que acontece, por quê, e o que o cliente vê.
- `fronteira` — **obrigatório**: com qual outro tema desta lista ele mais se confunde e
  qual critério decide entre os dois, aplicável lendo só o texto do chamado.
- `n_estimado` — quantos itens do lote você colocaria nele.

## Regras que vêm de erro já cometido neste projeto

- **Nenhum tema acima de ~30% do lote.** Balde grande esconde decisões opostas.
- **Nenhum abaixo de ~3%.**
- **Separe DEFEITO de PEDIDO.** Bug e solicitação de melhoria são respostas de produto
  opostas e não podem dividir o mesmo tema.
- **Separe DEFEITO de DÚVIDA** pelo mesmo motivo.
- **Não crie "Outros"** — o classificador já terá uma saída genérica.

## Saída
APENAS um bloco JSON:
```json
{{"temas": [{{"nome": "...", "descricao": "...", "fronteira": "...", "n_estimado": 0}}]}}
```
Nada além do JSON.
"""
(AQUI / "prompt_derivar.md").write_text(prompt, encoding="utf-8")
print(f"universo: {sum(tags.values())} chamados não-fiscais")
print(f"amostra:  {len(sel)} ({len(sel)/len(pool)*100:.0f}% dos que têm texto)")
print(f"arquivos: {AQUI/'amostra.json'}")
