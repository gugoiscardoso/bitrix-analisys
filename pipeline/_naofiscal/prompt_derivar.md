# Derivar a taxonomia dos chamados NÃO-fiscais — Ultracar (ERP automotivo)

O lote traz 260 chamados reais de suporte que **não são fiscais** — já foram
separados dos que tratam de nota, imposto, certificado ou SEFAZ. Sua tarefa é derivar a
subdivisão deles.

Contexto útil: o Bitrix já grava uma categoria entre colchetes no título. A distribuição
no universo completo é esta:

- [Melhoria] — 155 chamados
- [Orçamento] — 126 chamados
- [Erro] — 90 chamados
- [Outros] — 62 chamados
- [Cadastro] — 55 chamados
- [Relatório] — 45 chamados
- [Financeiro] — 36 chamados
- [Dados] — 34 chamados
- [(sem tag)] — 6 chamados
- [Gestão de Pátio] — 4 chamados

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
{"temas": [{"nome": "...", "descricao": "...", "fronteira": "...", "n_estimado": 0}]}
```
Nada além do JSON.
