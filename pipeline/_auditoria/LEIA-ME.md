# Auditoria de classificação — 07/08/2026

Trilha do que produziu os números de [`docs/auditoria_classificacao.md`](../../docs/auditoria_classificacao.md)
e das correções registradas nas fases 9.x de [`docs/planejamento_build_report.md`](../../docs/planejamento_build_report.md).

**Isto é histórico, não pipeline.** O pipeline de produção são quatro scripts em
`pipeline/`: `consolidar_store.py`, `classificar.py`, `gerar_relatorio.py` e `auditar.py`.
Nada aqui é chamado pela skill `/build-report`.

Os lotes e respostas (8,5 MB de JSON) estão no `.gitignore` — são regeneráveis pelos
scripts abaixo com a semente fixa `20260807`. Os **gabaritos** ficam versionados: são
800 itens julgados por dois avaliadores cegos e é a única coisa aqui que não se
reproduz de graça.

---

## ⚠️ Uso único — JÁ EXECUTADOS, não rode de novo

Estes mutaram `data/store/`. Rodar outra vez é, na melhor hipótese, inofensivo; na pior,
corrompe. `dividir_p7.py`, por exemplo, procura um subgrupo que não existe mais desde que
ele próprio o dividiu.

| script | o que fez |
|---|---|
| `migrar_p9.py` | dissolveu P9 em P10–P13 (remapeamento, sem IA) |
| `migrar_hash.py` | unificou as três regras de hash conflitantes; recalculou 477 |
| `regra_cfop.py` | escreveu a regra de fronteira P1×P7 nas descrições |
| `cfop_aplicar.py` | aplicou o consenso da fronteira; moveu 84 registros P1→P7 |
| `dividir_p7.py` | quebrou o catch-all de P7 em defeito × dúvida |
| `aplicar_p10_p13.py` | gravou os subgrupos derivados de P10–P13 |
| `reclass_aplicar.py` | aplicou a reclassificação dos 6.898 temas |

## Reutilizáveis

| script | para quê |
|---|---|
| `testar_filtro.py` | valida mudanças no `FISCAL_RE` nos três critérios: regressão, ganho e falso positivo. **Rode antes de mexer no filtro fiscal.** |
| `amostrar.py` | sorteia amostra estratificada cega, semente fixa |
| `analisar.py` | erro por consenso, ambiguidade, kappa e matriz de confusão |

Para auditoria recorrente use `pipeline/auditar.py`, que já está plugado na skill —
estes aqui são a versão exploratória que deu origem a ele.

## Gabaritos (versionados)

| arquivo | conteúdo |
|---|---|
| `gabarito.json` | 801 itens das camadas A/B/C/D1/D2, com o rótulo que estava armazenado |
| `gabarito_novos.json` | amostra dos registros recuperados pela correção do filtro |
| `cfop_gabarito.json` | os 538 registros da fronteira P1×P7 |
| `cfop_sinalizados.json` | 168 casos em que o texto não diz a finalidade do documento |

São a régua para medir qualquer classificador futuro contra o mesmo material.

## Geradores de lote e análises pontuais

`amostrar_c.py`, `amostrar_novos.py`, `analisar_cd.py`, `analisar_novos.py`,
`analisar_prod.py`, `analisar_digest.py`, `analisar_tema2.py`, `prompts.py`,
`prompt_tema2.py`, `cfop_lotes.py`, `derivar_p10_p13.py`, `reclass_lotes.py`,
`digest_completo.py`, `priorizacao.py`.

Cada um responde a uma pergunta específica daquela sessão. Os experimentos pareados que
decidiram o desenho do classificador estão em `analisar_prod.py` (produção × legado,
empate), `analisar_digest.py` (transcrição completa é **pior**, p=0,022) e
`analisar_tema2.py` (22 opções × 69, p=0,013 — origem do classificador de duas etapas).

## Onde foi parar o que tinha valor permanente

- `teste_duas_etapas.py` → `pipeline/testes/` (teste de regressão do classificador)
- a auditoria recorrente → `pipeline/auditar.py`, chamada no passo 4b da skill
