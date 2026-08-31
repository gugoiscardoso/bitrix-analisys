# Derivar a taxonomia das CONVERSAS não-fiscais — Ultracar (ERP automotivo)

O lote traz 400 transcrições reais de chat de suporte (WhatsApp e chat do site) que
**não são fiscais** — já foram separadas das que tratam de nota, imposto, certificado ou
SEFAZ. Sua tarefa é derivar a subdivisão delas.

Isto é **chat**, não chamado formal. Espere a forma do material: saudação, o cliente
descrevendo em linguagem solta, o atendente pedindo AnyDesk, sessão que termina sem
conclusão. Uma parte não terá assunto identificável nenhum.

## O que produzir

Entre **7 e 11 temas** que cubram o material. Para cada um:

- `nome` — curto e concreto, descrevendo a CAUSA ou o pedido. Ruim: "Dúvidas gerais".
  Bom: "Cliente não consegue lançar a peça na OS".
- `descricao` — 2 a 4 frases: o que acontece, por quê, e o que o cliente diz.
- `fronteira` — **obrigatório**: com qual outro tema desta lista ele mais se confunde e
  qual critério decide entre os dois, aplicável lendo só a transcrição.
- `n_estimado` — quantos itens do lote você colocaria nele.

## Regras que vêm de erro já cometido neste projeto

- **Nenhum tema acima de ~30% do lote.** Balde grande esconde decisões opostas.
- **Nenhum abaixo de ~3%.**
- **Separe DEFEITO de PEDIDO de melhoria**, e **DEFEITO de DÚVIDA de uso**. São respostas
  de produto opostas e não podem dividir o mesmo tema.
- Se houver volume relevante de conversa **sem assunto identificável** (só saudação, chat
  abandonado, atendimento resolvido sem descrever o problema), crie um tema para isso —
  é informação, não lixo.
- **Não crie "Outros"** — o classificador terá uma saída genérica própria.

## Saída
APENAS um bloco JSON:
```json
{"temas": [{"nome": "...", "descricao": "...", "fronteira": "...", "n_estimado": 0}]}
```
Nada além do JSON.
