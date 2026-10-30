# Surtos detectados durante a leitura de 30/10/2026

Registrados conforme os lotes reportam. Não são medição sistemática — são o que
apareceu à vista de quem leu. Vale uma varredura própria depois, por data e tema.

## Indisponibilidade (tema "Sistema inteiro fora do ar")
- lote A_019: 89 registros num lote só — o maior surto visto até agora
- lote A_023: faixa 220437–220549
- lote A_025: 222931, 222933, 222937, 222971
- lote A_027: 225197, 225213, 225235, 225297 (mesma manhã, sem confirmação do atendente)

## Defeito específico em massa — mais interessante que a indisponibilidade
Três regressões distintas na MESMA manhã, faixa 225851–226177 (lote A_028). Isso tem
cara de release ruim, e nenhum relatório atual mostra esse padrão:

1. **Erro "endereço principal" no cadastro de cliente** (~30 clientes):
   225851, 225855, 225883, 225887, 225891, 225903–225941, 225963–225969, 226005,
   226011, 226055, 226063, 226093, 226107, 226117, 226133, 226151
2. **Comissão que não salva** (chamados 100423 / 100427, ~14 clientes):
   225463, 225879, 225919, 225945, 225957, 225981, 225985, 225991, 226061, 226123,
   226139, 226175, 226283, 226335
3. **"Impossibilidade de envio / parcela já alterada o status" na baixa do financeiro**
   (chamado 100429, ~12 clientes):
   225861, 225947, 225979, 225997, 226009, 226083, 226085, 226087, 226113, 226177,
   226193, 226215

## Por que isso importa
O relatório conta fricção por categoria e por módulo, e nessas tabelas um surto de 30
clientes no mesmo defeito vira 30 linhas espalhadas em "erro de função / Cadastros".
Some com o ruído de fundo. Um eixo de "incidente" — agrupar por defeito e por dia —
mostraria o que a categoria esconde. Fica como proposta, não foi pedido.
