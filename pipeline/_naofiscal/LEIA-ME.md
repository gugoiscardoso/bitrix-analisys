# Classificação não-fiscal — 08/08/2026

Taxonomia e classificação dos chamados que **não** são fiscais. Vive separada da fiscal
de propósito: fundir as duas quebraria a comparabilidade do relatório fiscal entre
execuções, que é o princípio da skill `/build-report`.

| arquivo | o quê |
|---|---|
| `data/store/taxonomia_nao_fiscal.json` | 11 temas, derivados de amostra de 40% (260 de 645) |
| `data/store/classificacao_nao_fiscal.json` | 645 chamados classificados |
| `pipeline/gerar_chamados.py` | junta as duas taxonomias na planilha final |

## Como a taxonomia foi derivada

Dois agentes independentes sobre a mesma amostra, sem ver o resultado um do outro.
**Convergiram em 8 dos 10 temas** — é isso que dá confiança de que o material tem
estrutura real, e não de que um modelo inventou uma. Base: derivação B; acrescido o tema
que só a A enxergou (`peça/insumo cadastrado não é encontrado`, 27 registros que iriam
para "Outro").

## ⚠️ O que NÃO foi feito

**Esta classificação não tem auditoria de acurácia.** A fiscal tem 13,6% de erro medido
por amostragem cega com dois avaliadores; esta tem só a convergência das derivações, que
é indício e não medição. Antes de virar decisão de roadmap, rode o mesmo desenho de
`pipeline/auditar.py` sobre ela.

## Uso único

`derivar.py`, `lotes.py` e `absorver.py` foram executados em 08/08/2026. `absorver.py` é
idempotente; os outros dois regeram material que já está em `data/store/`.
