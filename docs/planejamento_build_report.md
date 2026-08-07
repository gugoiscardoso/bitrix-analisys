# Planejamento — skill `/build-report`

Documento de acompanhamento. Cada item é marcado conforme concluído.

**Objetivo:** transformar a análise exploratória de fricção fiscal num processo padronizado e repetível, executável por uma skill que recebe um período e devolve sempre a mesma resposta para o mesmo período.

---

## Decisões de design (fechadas)

| Questão | Decisão |
|---|---|
| Parâmetros | `--de <data>` e `--ate <data>` (default: hoje) |
| Saída | Dois arquivos em `report/`, com o período no nome |
| Coluna "Plano de ação" | **Fora** do relatório automático — continua em `docs/` como artefato curado |
| Leitura do período | **Janela pura**: tudo considera só registros dentro de `--de`/`--ate`; recência relativa ao `--ate`, não à data de execução |
| Coleta | A skill chama o coletor C# sozinha |
| Custo de tokens | Aceito. Classifica só o que é novo; a primeira carga de 3 meses coube no plano |
| Fonte da verdade | `data/store/` (JSONL + JSON), nunca o `.xlsx` |
| Consistência | Cache de classificação + taxonomia congelada + monitor de deriva |
| Texto alterado após classificar | **Reclassifica** — acurácia sobre estabilidade, exceto curadoria manual |

**Saída oficial:**
```
report/relatorio_executivo_<de>_<ate>.xlsx
report/base_unificada_<de>_<ate>.xlsx
```

---

## Fase 0 — Reorganização ✅

- [x] Criar estrutura `data/raw`, `data/store`, `report`, `docs`, `pipeline`
- [x] Mover exports, artefatos curados e scripts para os lugares certos
- [x] Documentar a estrutura e a regra de escrita em `ESTRUTURA.md`
- [x] Descartar entregáveis superados

## Fase 1 — Store canônico ✅

- [x] `taxonomia.json` — 9 frentes, 23 temas, 69 subgrupos, versionada
- [x] `classificacao.json` — 6.898 entradas com tema, subgrupo, frente, origem e hash
- [x] `base_historica.jsonl` — 14.509 registros com os campos das métricas
- [x] `pipeline/consolidar_store.py` reconstrói os três a partir de `data/raw/`, com caminhos relativos
- [x] Validação: filtro fiscal refeito do zero bate exatamente com as 6.376 conversas já classificadas; zero subgrupos órfãos
- [x] Legado isolado em `data/store/_legado/` (38 arquivos, descartáveis)

## Fase 2 — Classificador incremental ✅

O coração da consistência. Implementado em `pipeline/classificar.py`, com três comandos:
`preparar` (separa o que falta e escreve os lotes), `absorver` (grava as respostas no cache)
e `status` (cobertura e deriva).

- [x] Prompt gerado **a partir de** `taxonomia.json` — 22 mil caracteres, idêntico em toda execução
- [x] Ler o cache e separar: já classificado (reusa) × novo (classifica)
- [x] Lotes de 250 itens, prompts separados para chamado e conversa (P8 só existe no chat)
- [x] `fonte: manual` é imune a reprocessamento
- [x] Hash divergente: **reclassifica** (decisão de 07/08) e registra os ids em `_fila/reclassificados.json`; `fonte: manual` segue imune
- [x] Rótulo fora da taxonomia é ignorado, não gravado — a IA não consegue inventar categoria
- [x] Gravação lote a lote: queda de cota no meio não perde o que já foi absorvido
- [x] Monitor de deriva separando três coisas: descartados, sem classificação e sem subgrupo
- [x] **Teste de idempotência:** com o cache cheio, 6.895 reusados e **0 a classificar**

**Deriva atual: 6,2%** (403 registros fiscais com tema mas sem subgrupo que encaixe), abaixo do
limite de 10%. Em junho isolado é 7,3%. É o número a acompanhar: quando passar do limite, a
taxonomia precisa de subgrupos novos.

Dois defeitos que o próprio teste expôs e foram corrigidos: em P9 o subgrupo é o próprio tema
(o vínculo nunca era derivável do cache) e a métrica de deriva somava descartados com "Outro",
disparando alarme falso de 28,9%.

## Fase 3 — Pipeline de produção ✅

**Decisão de arquitetura:** em vez de consertar os 8 scripts exploratórios, escrevi um gerador
novo e limpo. Aqueles scripts nasceram como ferramenta de análise — dependem da ordem de execução
da sessão e acumularam remendos. Reaproveitá-los custaria mais que reescrever, e deixaria dívida.

- [x] `pipeline/gerar_relatorio.py` — lê o store canônico, aceita `--de`/`--ate`, produz os dois arquivos
- [x] Janela pura aplicada a tudo: contagens, peso, tempos, última incidência e recência
- [x] Recência relativa ao fim da janela, não à data de execução
- [x] Legenda gerada junto, com os campos do Bitrix explicitados
- [x] Caminhos relativos à raiz — roda de qualquer máquina
- [x] Scripts exploratórios isolados em `pipeline/_exploratorio/` com LEIA-ME explicando o escopo

**Teste de determinismo:** gerado duas vezes o mesmo período, comparado célula a célula —
**0 divergências** em 87 linhas do relatório executivo e 6.920 da base unificada.

O pipeline de produção agora são três scripts: `consolidar_store.py`, `classificar.py`
e `gerar_relatorio.py`.

## Fase 4 — Coletor C# incremental ✅

- [x] `--to` no `CliArgs` e no filtro (`<=CREATED_DATE`), para chamados e conversas
- [x] `--changed-since` usando `>=CHANGED_DATE` — traz numa consulta só os chamados novos **e** os que mudaram de status
- [x] Validação de data com formato exato e cultura invariante
- [x] Saída passa a ser `data/raw/` em vez de `output/`
- [x] `data/store/coleta.json` registra cada coleta (quando, arquivo, quantos, parâmetros)
- [x] `consolidar_store.py` **mescla** todos os exports por id — requisito da coleta incremental
- [x] Teste real: janela de 3 dias trouxe 26 chamados e registrou a coleta corretamente

**Dois defeitos encontrados e corrigidos durante a fase:**

A validação de data aceitava `01-05-2026` porque `DateOnly.TryParse` usa a cultura da máquina
(pt-BR). Uma janela silenciosamente errada é pior que um erro — passou a usar `TryParseExact`
com `InvariantCulture`.

Mais grave: `consolidar_store.py` reconstruía o cache de classificação a partir dos arquivos
legados a cada execução. Como o legado tinha sido movido para `_legado/`, uma reexecução
**zerou as 6.376 conversas do cache** — exatamente o que ele deveria proteger. O cache passou
a ser preservado por padrão e só é semeado do legado quando ainda não existe. Reexecutar o
script agora é inofensivo, e isso foi verificado.

## Fase 5 — Geradores de saída ✅

Absorvida pela Fase 3 — o gerador já produz os dois arquivos no formato final.

- [x] `relatorio_executivo_<de>_<ate>.xlsx` — 74 linhas de subgrupo, **sem** coluna de plano de ação
- [x] `base_unificada_<de>_<ate>.xlsx` — 6.895 registros classificados, com aba de resumo por tema
- [x] Métricas na janela: contagens, peso, tempo total, tempo tech, última incidência, recência
- [x] Legenda gerada junto

## Fase 6 — A skill ✅

- [x] `.claude/skills/build-report/SKILL.md`
- [x] Orquestra: coletar (cheio ou incremental, decidido por `coleta.json`) → consolidar → classificar o novo → gerar saída
- [x] Resumo ao final com volume, quanto veio do cache, deriva e onde ficaram os arquivos
- [x] Falha parcial: no máximo 6 subagentes por onda, absorção lote a lote, relançar só o lote que caiu
- [x] Regras explícitas: nunca reclassificar o que está em cache, nunca inventar subgrupo, nunca escrever em `docs/`

## Fase 7 — Validação de consistência ✅

- [x] **Mesmo período, duas execuções:** 83 linhas comparadas célula a célula, **0 divergências**
- [x] **Aditividade entre janelas:** junho (2.107) + julho (2.451) = jun–jul (4.558), exato
- [x] **Recência acompanha a janela:** com fim em 30/06 tudo é "Ativa"; com fim em 05/08 aparecem
      3 subgrupos em "Atenção". O mesmo subgrupo mostra última incidência 25/06 numa janela e
      28/07 na outra — comportamento correto de janela pura
- [x] **Idempotência do classificador:** 6.895 reusados, 0 classificados
- [x] **Reexecução do consolidador é inofensiva** (verificado após a correção do cache)

---

## Riscos conhecidos

**Custo por execução.** Cerca de 170 chamados e 2.000 conversas fiscais por mês, o que dá aproximadamente 850 mil tokens numa execução mensal. Mitigação possível, se virar problema: classificação em dois estágios, com regras resolvendo os casos de assinatura inequívoca e IA só no resto.

**Apodrecimento da taxonomia.** Como ela é congelada, o que é novo cai em "Outro". Foi assim que apareceram IPI, pendência no portal e devolução com IBS/CBS. O monitor de deriva existe para que isso seja detectado, não descoberto por acaso.

**Falha parcial por cota.** Aconteceu na análise original: 12 de 16 lotes caíram. O cache precisa ser gravado incrementalmente, lote a lote, para que uma queda não obrigue a refazer tudo.

---

## Pendências com o time

- `output/problemas_2026-08-05.xlsx` não foi gerado pelo pipeline e ficou onde estava. Definir destino.
- Nada foi commitado no git ainda, por decisão. Ao commitar, avaliar `.gitignore` para `data/raw/` (68 MB regeneráveis).
