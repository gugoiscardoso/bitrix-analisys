# Classificação não-fiscal — CONVERSAS (08/08/2026)

Terceira taxonomia do projeto, e ela existe por um número: **59% do volume de chat cai em
temas que a taxonomia de CHAMADO não tem** — conversa sem assunto, cobrança de prazo,
pedido de treinamento, acesso bloqueado por mensalidade. Ninguém abre ticket para isso.
Reaproveitar a de chamado jogaria mais da metade das 6.377 em "Outro".

| arquivo | o quê |
|---|---|
| `data/store/taxonomia_nao_fiscal_conv.json` | 12 temas |
| `data/store/classificacao_nao_fiscal_conv.json` | 6.377 conversas |
| `pipeline/gerar_conversas.py` | junta com a taxonomia fiscal na planilha |

## Derivação

Dois agentes independentes sobre a mesma amostra de 400 (7% das 6.068 com texto), sem ver
o resultado um do outro. **Convergiram em 11 de 11 temas** — convergência maior que a dos
chamados (8 de 10). Base: derivação B, acrescido o tema de relatório que só a A separou
de financeiro.

## ⚠️ Sem auditoria de acurácia

Como a dos chamados, esta classificação tem só a convergência das derivações como sinal,
que é indício e não medição. A fiscal tem 13,6% de erro medido por amostragem cega com
dois avaliadores; esta não tem número. Antes de virar decisão, rode o desenho de
`pipeline/auditar.py` sobre ela.

## Uso único

`absorver.py` é idempotente e pode rodar de novo. Os lotes e respostas estão no
`.gitignore` — regeráveis pelo script de derivação com semente fixa 909.
