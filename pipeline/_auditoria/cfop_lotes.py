#!/usr/bin/env python
"""9.3.2 — lotes para reaplicar a fronteira P1 × P7 nos registros de CFOP/CST.

Decisão focada: dado que o registro JÁ é um caso de CFOP/CST, a finalidade do
documento é de venda (P1) ou de devolução/garantia/remessa (P7)?

Dois avaliadores independentes, ordens diferentes. Só o consenso é aplicado —
onde discordarem, o rótulo atual fica e o caso é sinalizado. É a lição da auditoria:
onde dois leitores independentes não convergem, o problema é a fronteira, e trocar
o rótulo com base em um voto só é ruído com aparência de correção.
"""
import json, random, sys, io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AUD = Path(__file__).resolve().parent
RAIZ = AUD.parents[1]
STORE = RAIZ / "data" / "store"
(AUD / "lotes").mkdir(exist_ok=True)

SUB_P1 = "CFOP/CST incompatíveis com a operação ou regime (devolução, idDest, grupos de imposto)"
SUB_P7 = "CFOP, CST/CSOSN e regime tributário incompatíveis"

cls = json.loads((STORE / "classificacao.json").read_text(encoding="utf-8"))
base = {}
with (STORE / "base_historica.jsonl").open(encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        base[(r["tipo"], str(r["id"]))] = r

alvo = []
for chave, tipo in (("chamados", "chamado"), ("conversas", "conversa")):
    for rid, d in cls[chave].items():
        if d.get("subgrupo") in (SUB_P1, SUB_P7):
            r = base.get((tipo, rid))
            if not r:
                continue
            txt = ((r.get("titulo") or "") + "\n" + (r.get("texto") or "")).strip()
            alvo.append({"id": rid, "tipo": tipo, "atual": d["subgrupo"],
                         "frente_atual": d["frente"], "texto": txt[:2200]})

(AUD / "cfop_gabarito.json").write_text(
    json.dumps({f'{i["tipo"]}|{i["id"]}': {k: v for k, v in i.items() if k != "texto"}
                for i in alvo}, ensure_ascii=False, indent=1), encoding="utf-8")

PROMPT = """# Fronteira P1 × P7 — casos de CFOP/CST

Todos os itens abaixo são atendimentos sobre **CFOP, CST/CSOSN ou regime tributário
incompatíveis**. Isso já está estabelecido; não reavalie.

A única decisão é: **qual é a finalidade do documento fiscal envolvido?**

- `"P1"` — o documento é uma nota de **venda, serviço ou operação comum**.
- `"P7"` — o documento é uma nota de **devolução, garantia, remessa ou retorno**.
- `"?"` — o texto não é sobre CFOP/CST, ou não dá para dizer a finalidade.

**O discriminador é a finalidade do documento, não a mensagem de erro.** A mesma
rejeição da SEFAZ (CFOP inválido, CST para Simples Nacional, CSOSN incompatível)
aparece nos dois casos — ela não decide nada.

Cuidado com duas armadilhas:
- Mencionar a palavra "devolução" de passagem não faz o documento ser de devolução.
  O cliente pode citar o CFOP 5949 "que uso em devolução" enquanto emite uma venda.
- Uma venda para cliente que devolveu a peça continua sendo venda, se a nota em
  questão é a de venda.

Cada item tem `id` e `texto`.

## Saída
APENAS um bloco JSON, id -> "P1" | "P7" | "?":
```json
{"240283": "P7", "241753": "P1"}
```
Todo id do lote deve aparecer. Nada além do JSON.

## Eficiência
Leia o lote UMA vez e escreva a saída UMA vez. Não releia o arquivo.
"""
(AUD / "prompts" / "cfop.md").write_text(PROMPT, encoding="utf-8")

TAM = 90
for av, semente in (("av1", 771), ("av2", 772)):
    itens = alvo[:]
    random.Random(semente).shuffle(itens)
    for i in range(0, len(itens), TAM):
        bloco = [{"id": x["id"], "texto": x["texto"]} for x in itens[i:i + TAM]]
        (AUD / "lotes" / f"{av}_CFOP_{i//TAM+1:02d}.json").write_text(
            json.dumps(bloco, ensure_ascii=False, indent=1), encoding="utf-8")

n_lotes = (len(alvo) + TAM - 1) // TAM
chars = sum(len(x["texto"]) for x in alvo)
print(f"registros alvo: {len(alvo)}")
print(f"  hoje em P1: {sum(1 for x in alvo if x['atual'] == SUB_P1)}")
print(f"  hoje em P7: {sum(1 for x in alvo if x['atual'] == SUB_P7)}")
print(f"lotes: {n_lotes} x 2 avaliadores = {n_lotes*2} agentes")
print(f"conteudo: {chars} chars (~{chars/3.5:.0f} tok) x2 = ~{chars/3.5*2:.0f} tok")
