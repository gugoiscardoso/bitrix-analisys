#!/usr/bin/env python
"""9.3.4 — amostras para derivar subgrupos de P10..P13.

Essas frentes saíram de dentro de P9 e têm subgrupo = tema, ou seja, granularidade
zero: dizem que existe um problema, não qual. P10 sozinha tem 411 registros, mais que
P4, que é frente própria há tempos.

Duas lições das rodadas anteriores aplicadas aqui:

1. A taxonomia de P7/P8 foi derivada de 300 conversas e aplicada a 1.855; a auditoria
   mediu 16,0% e 15,6% de erro de subgrupo nelas, acima da média. Aqui a amostra é
   fração muito maior do universo (36%–65%), justamente para não repetir isso.
2. Os defeitos de fronteira de P1×P7 e do catch-all de P7 existiam porque ninguém
   escreveu o critério de desempate. O prompt exige FRONTEIRA explícita entre pares
   adjacentes desde a origem, não como remendo depois.
"""
import json, random, sys, io, collections
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AUD = Path(__file__).resolve().parent
RAIZ = AUD.parents[1]
STORE = RAIZ / "data" / "store"
(AUD / "lotes").mkdir(exist_ok=True)
(AUD / "prompts").mkdir(exist_ok=True)

ALVO = {"P10": "Cadastro fiscal mestre (NCM, CFOP, CST, código de serviço, regime)",
        "P11": "Ciclo de cancelamento de nota",
        "P12": "Entrada: XML de compra e manifestação do destinatário",
        "P13": "Integração ERP × nota (financeiro, estoque, OS)"}
N = 150

cls = json.loads((STORE / "classificacao.json").read_text(encoding="utf-8"))
base = {}
with (STORE / "base_historica.jsonl").open(encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        base[(r["tipo"], str(r["id"]))] = r

for frente, titulo in ALVO.items():
    pool = []
    for chave, tipo in (("chamados", "chamado"), ("conversas", "conversa")):
        for rid, d in cls[chave].items():
            if d.get("frente") != frente:
                continue
            r = base.get((tipo, rid))
            if not r:
                continue
            t = ((r.get("titulo") or "") + " " + (r.get("texto") or "")).strip()
            if len(t) > 60:
                pool.append(t[:900])
    sel = random.Random(hash(frente) % 9999).sample(pool, min(N, len(pool)))
    (AUD / "lotes" / f"DERIV_{frente}.json").write_text(
        json.dumps(sel, ensure_ascii=False, indent=1), encoding="utf-8")

    p = f"""# Derivar subgrupos da frente {frente} — {titulo}

O arquivo do lote traz {len(sel)} atendimentos reais de suporte fiscal da Ultracar (ERP
automotivo), todos já classificados nesta frente. Hoje a frente não tem subdivisão: ela
diz que existe um problema, não qual. Sua tarefa é **derivar a subdivisão**.

## O que produzir

Entre **5 e 8 subgrupos** que cubram o material. Para cada um:

- `nome` — curto e concreto, descrevendo a CAUSA, não o sintoma genérico.
  Ruim: "Problemas de cadastro". Bom: "NCM inválido ou ausente bloqueia a emissão".
- `descricao` — 2 a 4 frases: o que acontece, por que acontece, e o que o cliente vê.
- `fronteira` — **obrigatório**: com qual outro subgrupo desta lista ele mais se confunde,
  e qual é o critério que decide entre os dois. Escreva o critério de forma que dê para
  aplicar lendo só o texto do atendimento.
- `n_estimado` — quantos dos itens do lote você colocaria nele.

## Regras que vêm de erro já cometido neste projeto

- **Nenhum subgrupo pode passar de ~35% do lote.** Um balde grande esconde decisões
  opostas: um subgrupo de P7 tinha 20% da frente e, ao ser dividido, revelou-se metade
  defeito de software e metade falta de documentação — respostas de produto opostas.
- **Nenhum abaixo de ~3%.** Granularidade demais não é acionável.
- **Separe DEFEITO de DÚVIDA.** Se um mesmo assunto aparece nas duas formas, são dois
  subgrupos, porque um vira engenharia e o outro vira documentação.
- **Não crie "Outros".** O classificador já tem uma saída genérica; se você criar outra,
  ela vira o balde.
- Os nomes não podem repetir nem parafrasear subgrupos de outras frentes.

## Saída
APENAS um bloco JSON:
```json
{{"subgrupos": [{{"nome": "...", "descricao": "...", "fronteira": "...", "n_estimado": 0}}]}}
```
Nada além do JSON.
"""
    (AUD / "prompts" / f"deriv_{frente}.md").write_text(p, encoding="utf-8")
    print(f"{frente}: universo {len(pool)}, amostra {len(sel)} ({len(sel)/len(pool)*100:.0f}%)"
          f"  -> lotes/DERIV_{frente}.json")
