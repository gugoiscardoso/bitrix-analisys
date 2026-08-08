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

## Fase 8 — Auditoria de classificação ✅

Auditoria cega, estratificada, com dois avaliadores independentes sobre a amostra
inteira. 801 itens, 1.602 julgamentos. Relatório completo em
[`docs/auditoria_classificacao.md`](auditoria_classificacao.md); artefatos reprodutíveis
em `pipeline/_auditoria/` (semente `20260807`).

| Camada | n | Erro (consenso) | IC95 | Ambiguidade | Kappa |
|---|---:|---:|---|---:|---:|
| tema de chamado | 144 | 10,4% | ±4,3pp | 7,6% | 0,917 |
| tema de conversa | 201 | **21,9%** | ±5,6pp | 9,0% | 0,903 |
| subgrupo de conversa (condicional) | 150 | 13,3% | ±5,4pp | 9,3% | 0,903 |

Erro composto do subgrupo de conversa: `0,781 × 0,867` = **~32%**.

**Quatro conclusões que mudam decisão:**

1. **O filtro fiscal de chamado era circular** (`fiscal = tid in tema_chamado`) e o regex
   nunca foi aplicado a chamados. Como `classificar.py` só enfileira o que é fiscal,
   **nenhum chamado novo jamais seria classificado**. O teste de idempotência da Fase 2
   ("6.895 reusados, 0 a classificar") é exatamente o que esse bug produz — ele não
   distingue "nada novo" de "incapaz de ver o novo".
2. **O filtro de conversa perde 15,3%** do que descarta (~1.059 conversas fiscais).
3. **O erro é direcional, não aleatório.** `Rejeição/erro de validação` é um atrator:
   perde ~1/3 do próprio volume nas duas fontes e quase não recebe nada. É o tema âncora
   de P1 — o erro inflou sistematicamente a prioridade nº 1.
4. **A taxonomia tem defeito estrutural**: `CFOP/CST incompatíveis` existe em P1 (411) e
   em P7 (120) com nomes diferentes; e o subgrupo nº 1 de P7 é um problema de cálculo de
   imposto, que é a definição de P3. Kappa alto (0,90–0,92) prova que o problema é
   execução e desenho, não inconsistência entre lotes.

**Impacto na priorização:** P1 cai de 1º para 2º (−29,6%), P6 sobe de 5º para 3º (+38,3%),
P8 cai de 3º para 5º. P9 aparece em 1º, mas é balde residual (0% de subgrupos) — sinal de
dívida de taxonomia, não prioridade.

---

## Fase 9 — Correções pós-auditoria

**A ordem não é negociável:** taxonomia → filtro → reclassificação. Reclassificar antes
do bump de taxonomia compra 32% de erro de subgrupo de novo, com dinheiro novo.

### 9.1 Filtro fiscal de chamado ✅

- [x] `consolidar_store.py` — `fiscal` passa a usar `FISCAL_RE` sobre título+descrição,
      com `or tid in tema_chamado` para blindar o que já está classificado
- [x] Semeadura do cache condicionada a `tid in tema_chamado` — um chamado fiscal sem
      classificação agora fica **fora** do cache, que é o que faz o classificador pegá-lo
- [x] `classificar.py` — `"Não fiscal (falso positivo)"` passa a ser oferecido também a
      chamado. Sem isso, os ~55% não-fiscais que o regex traz a mais seriam empurrados à
      força para alguma categoria fiscal
- [x] Verificado ponta a ponta: `preparar` saiu de **0** para **897 a classificar**
      (96 chamados, 801 conversas), com 6.895 reusados do cache

### 9.2 Ampliação do filtro fiscal ✅

Construído como **superconjunto estrito** do padrão anterior — regressão impossível por
construção. Validado nos três critérios em `pipeline/_auditoria/testar_filtro.py`:

| Critério | Resultado |
|---|---|
| Regressão (perde algo já classificado?) | **0** chamados, **0** conversas |
| Ganho (recupera falso negativo da auditoria?) | **20 de 23** (87%) |
| Custo (falso positivo introduzido) | **2 de 123** (1,6%) |

Buracos fechados: `\bnf\b` sozinho (a forma que o chat usa — maior lacuna isolada),
`certificado` sem exigir "digital", `sintegra`/`sped`, verbo conjugado + objeto
(`emitindo uma nota`, que o infinitivo `emitir nota` não pegava) e as naturezas de
operação faltantes (`nota de garantia|retorno|remessa|...`).

### 9.3 Bump de taxonomia — **em andamento**

**Correção da Fase 8:** a auditoria afirmou que `Destaque manual de impostos para bater
com o espelho do fornecedor` era problema de cálculo e pertencia a P3. **Está errado.**
Amostrando os 204 registros, são dúvidas e erros de imposto *dentro da emissão de uma
devolução* ("dúvida do que colocar no IPI da nota de devolução"). O defeito é o sistema
não trazer os valores da compra de origem — isso é P7. O problema do subgrupo é outro:
ele virou catch-all de "imposto + devolução", e por isso é o maior de P7.

#### 9.3.1 Dissolver P9 ✅

P9 não era uma frente: 7 temas sem relação entre si somados num balde. Como a soma cresce
quanto mais heterogêneo o balde, ele subia no ranking por ser bagunçado, não por ser
importante — foi assim que apareceu em 1º na Fase 8.

- [x] `FRENTES` e `TEMA_PARA_FRENTE` — os 4 temas maiores (93%) viram frentes próprias
- [x] Migração do cache por `pipeline/_auditoria/migrar_p9.py` — **remapeamento, zero IA**
- [x] `montar_taxonomia`, `enriquecer_taxonomia` e `gerar_relatorio` deixaram de tratar
      P9 por nome fixo; a regra "frente de tema único → subgrupo = tema" passou a ser
      derivada da taxonomia, então um bump futuro não precisa lembrar de editar os três

| Nova frente | n |
|---|---:|
| P10 Cadastro fiscal mestre (NCM, CFOP, CST, código de serviço, regime) | 390 |
| P11 Ciclo de cancelamento de nota | 306 |
| P12 Entrada: XML de compra e manifestação do destinatário | 226 |
| P13 Integração ERP × nota (financeiro, estoque, OS) | 185 |
| P9 (cauda: relatórios, e-mail, API interna) | 82 |

**P10 é o achado:** 390 registros, mais que o dobro de P4 (174), que já figurava como
frente própria no relatório. Estava invisível diluído no balde.

**Defeito grave encontrado no caminho:** `gerar_relatorio.py` tinha a ordem das frentes
**hardcoded** (`ordem = ["P1",...,"P8"]`). Criar frente nova fazia as linhas dela serem
descartadas do relatório executivo **sem erro nenhum** — P10–P13 perderam 1.107 registros
assim. A lista curada foi mantida, mas agora recebe no fim qualquer frente da taxonomia
que não esteja nela. Verificado: 74 linhas e as 13 frentes presentes no xlsx.

#### 9.3.2 Disjuntar CFOP/CST entre P1 e P7 ✅

O critério **já operava na prática, só nunca foi escrito**: o subgrupo de P7 é 99,2%
devolução/garantia/remessa; o de P1, 23,9%. Fundir seria errado — devolveria a P1 o
volume que a auditoria mostrou inflado e apagaria uma distinção real de produto
(pré-validar campo ≠ guiar escolha de CFOP de devolução, que o suporte se recusa a
fazer, com razão).

- [x] Regra escrita nas descrições dos dois subgrupos, em `propostas.json` e `sub_p7.json`
      (fonte da verdade), propagada à taxonomia: **o discriminador é a finalidade do
      documento, não a mensagem de erro** — a mesma rejeição da SEFAZ aparece nos dois casos
- [x] 538 registros reavaliados por dois avaliadores independentes, só o consenso aplicado

**Resultado — e o número que mais informa é o zero:**

| Votos | n | Leitura |
|---|---:|---|
| consenso, rótulo atual confirmado | 352 | — |
| consenso, **movido P1 → P7** | **84** | |
| **discordância P1 × P7** | **0** | a regra é nítida quando o texto tem a informação |
| um ou ambos marcaram `?` | 168 | o texto não diz a finalidade — **mantido o atual** |
| sem resposta | 1 | |

Efeito: o subgrupo de P1 vai de 418 para 334, o de P7 de 120 para 204. Frente, subgrupo
e tema migram juntos (o tema de P1 é `Rejeição/erro de validação`; o de P7,
`Nota de devolução/garantia/remessa/complemento`). No cache: P1 1.489 → 1.405,
P7 885 → 969.

Os `?` não são falha: exemplo típico é *"Rejeição 374 - CFOP incompatível com grupo de
tributação"*, que é erro de CFOP sem dizer se a nota é de venda ou devolução. Onde os
avaliadores não conseguem decidir, o rótulo fica — trocar com um voto só é ruído com
aparência de correção. Casos sinalizados em `pipeline/_auditoria/cfop_sinalizados.json`.

**Defeito encontrado no caminho:** `montar_prompt` truncava a descrição de cada subgrupo
em 300 caracteres, e **38 dos 69 subgrupos têm descrição maior** — o classificador nunca
viu a definição completa de mais da metade da taxonomia, e regras de fronteira (que ficam
no fim da descrição) jamais chegavam. Truncamento removido; o prompt subiu de 22,4k para
28,5k chars (~1,7k tokens por lote).

> **Correção (mesma sessão):** cheguei a registrar aqui que esse truncamento era
> "candidato plausível a causa dos 21,9% da Fase 8". **Está errado e a afirmação foi
> retirada.** Os 6.376 rótulos de tema de conversa têm `em: 2026-08-05` e vieram de
> `class_conv_*.json`, a classificação exploratória legada semeada pelo
> `consolidar_store` — eles nunca passaram por `montar_prompt`. O truncamento estava num
> código que ainda não havia classificado aqueles registros, então não pode explicar o
> erro deles. Corrigi-lo continua certo (afeta tudo que for classificado daqui pra
> frente), mas não é retroativo.

**Segunda fragilidade corrigida:** `consolidar_store.py` regenerava `taxonomia.json` do
zero e zerava o campo `tema` dos 69 subgrupos, que é derivado do cache por
`classificar.enriquecer_taxonomia()`. Qualquer coisa que dependesse desse campo via `None`
até alguém rodar o classificador. A regeneração agora carrega o valor anterior.

#### 9.3.3 Quebrar o catch-all de P7 ✅

`Destaque manual de impostos para bater com o espelho do fornecedor` era o maior subgrupo
de P7 (218, 20,1%) e misturava duas coisas com respostas de produto opostas. Dividido em:

- **`Espelho do fornecedor: valores da compra de origem não são herdados`** — o defeito
- **`Dúvida de preenchimento de imposto na devolução (IPI, PIS/COFINS, ICMS, frete)`** — how-to

As descrições trazem a fronteira explícita nos dois sentidos, como se fez em 9.3.2: há
espelho a ser reproduzido → defeito; não há, é desconhecimento da regra → dúvida.

Reatribuídos 338 registros (os 218 do subgrupo antigo mais 120 que já estavam sem
subgrupo em P7). O `(vazio)` de P7 caiu de 11,1% para **2,6%**.

**A resposta que o balde escondia:**

| | n | % de P7 |
|---|---:|---:|
| Dúvida de preenchimento (documentação) | 133 | 12,3% |
| Espelho do fornecedor (defeito) | 112 | 10,3% |

Estava 54/46 entre documentação e feature. **Metade do maior subgrupo de P7 não era
defeito de software** — era cliente sem saber o que preencher. Enquanto os dois estavam
juntos, os 218 pareciam um único item de engenharia de 20% da frente.

#### 9.3.4 Subgrupos de P10–P13 ✅

P10–P13 saíram de dentro de P9 sem quebra própria: subgrupo = tema, ou seja, diziam que
havia um problema mas não qual. P10 sozinha tem 411 registros, mais que P4, que é frente
própria desde o início.

**Duas lições anteriores aplicadas na derivação, não como remendo depois:**

1. A taxonomia de P7/P8 veio de 300 conversas aplicadas a 1.855 (16%), e a auditoria mediu
   16,0% e 15,6% de erro de subgrupo nelas — acima da média. Aqui a amostra foi de
   **36% a 66%** do universo de cada frente.
2. Os defeitos de fronteira de P1×P7 e do catch-all de P7 existiam porque o critério de
   desempate nunca foi escrito. O prompt de derivação **exigiu `fronteira` obrigatória**
   em cada subgrupo, e ela vai anexada à descrição — que é o que chega ao classificador.
   Regra de fronteira que não entra no prompt não serve para nada.

Restrições impostas e verificadas: nenhum subgrupo acima de 35% nem abaixo de 3%, separar
defeito de dúvida, proibido criar "Outros". **As quatro derivações passaram nas três.**

| frente | universo | amostra | subgrupos | maior subgrupo |
|---|---:|---:|---:|---:|
| P10 Cadastro fiscal mestre | 411 | 150 (36%) | 8 | 22,0% |
| P11 Ciclo de cancelamento | 362 | 150 (41%) | 8 | 22,0% |
| P12 Entrada: XML de compra | 276 | 150 (54%) | 8 | 20,0% |
| P13 Integração ERP × nota | 228 | 150 (66%) | 8 | 19,4% |

Gravadas em `data/store/sub_p10_p13.json`, lidas por `montar_taxonomia`. A taxonomia foi
de 70 para **98 subgrupos**, e 1.278 registros foram reclassificados nas novas divisões.

- [x] Derivar subgrupos próprios para P10–P13
- [x] Bump de `versao` em `classificacao.json` para `2026-08-07b`
- [ ] Avaliar subgrupo para P7 em chamado (24 registros) — volume baixo, não move ranking

### 9.4 Reclassificação — feita em parte, e o resto CANCELADO por medição

- [x] Classificar o backlog de 897 (96 chamados + 801 conversas) e absorver
- [x] Regerar `report/` — a base fiscal foi de 6.895 para **7.792** registros
- [x] Testar se reclassificar valeria a pena — **a resposta é não**
- [ ] ~~Reclassificar as 1.409 conversas de `Rejeição/erro de validação`~~ **cancelado**

**Onde caíram as conversas recuperadas** — era a maior incerteza aberta do relatório de
auditoria. Resposta: espalhadas, não concentradas, e o ranking não mudou de ordem. Mas o
padrão relativo corrobora a auditoria por um caminho independente: **P1 foi a frente
grande que menos cresceu (+6,5%) e P6 a que mais cresceu (+20,7%)** — exatamente a
direção que a reclassificação cega já apontava. Duas evidências sem mecanismo em comum
chegando ao mesmo lugar.

**Teste pareado: produção atual × exploratório legado.** Mesma população (os 201 da
camada B), mesmo gabarito (consenso dos dois auditores; 183 com verdade de referência).
É o teste que o "experimento natural" anterior não era, porque ali a população mudava junto.

| | acerto | IC95 |
|---|---:|---|
| classificador legado (que produziu o dado auditado) | 76,0% | [69,3 – 81,6] |
| classificador de produção atual (prompt destruncado) | 72,7% | [65,8 – 78,6] |

McNemar: só o legado acertou 28, só a produção acertou 22, **p = 0,48 — empate estatístico**.

**Conclusão:** reclassificar não compra acurácia. Os ~24% de erro não são atribuíveis ao
classificador — trocar de classificador reproduz o mesmo patamar. Gastar tokens
reclassificando as 1.409 produziria dado *diferente*, não *melhor*.

**Onde o erro pode estar, então.** Sobraram duas hipóteses:

1. ~~**Corte de 25 mensagens no digest**~~ — **testada e REFUTADA, na direção oposta.**
2. **Ambiguidade da taxonomia** — já quantificada: 9,0% na camada B (onde os dois
   auditores discordam *entre si*). Explica parte do erro, não o todo.

#### 9.4.1 Teste do digest ✅ — o corte AJUDA

Mesma população (201 da camada B), mesmo gabarito, mesmo prompt de produção. Só o insumo
muda: digest de produção (25 mensagens, 200 chars cada) × transcrição completa
reconstruída do XLSX bruto. A reprodução do digest foi conferida: bate **201/201** com
`base_historica.jsonl`, então a comparação é limpa.

| classificação | acerto | IC95 |
|---|---:|---|
| legado (produziu o dado auditado) | 76,0% | [69,3 – 81,6] |
| produção / digest cortado | 72,7% | [65,8 – 78,6] |
| **produção / transcrição completa** | **66,7%** | [59,6 – 73,1] |

McNemar cortado × full: só o cortado acertou **15**, só o full acertou **4**,
**p = 0,022 — significante**. A resposta mudou em 28 registros (15,3%); nesses, o digest
cortado acertou 15 e a transcrição completa 4.

**Mais texto piorou o resultado.** O corte de 25 mensagens não é defeito, é filtro de
ruído: as primeiras mensagens carregam o problema, e a cauda traz resolução, cordialidade
e assunto novo que puxam o classificador para o lado errado. **Não remover o corte** —
custaria mais tokens por registro em toda execução futura para comprar erro.

*Ressalva do teste:* a versão "completa" removeu o corte de 25 mensagens **e** subiu o
corte por mensagem de 200 para 600 chars. O teste mostra que "mais texto é pior", mas não
isola qual dos dois cortes é o responsável. Para a decisão prática — manter como está —
isso não muda nada.

#### 9.4.2 O que sobrou sem explicação

Três alavancas foram testadas e nenhuma explica os ~24%: trocar de classificador (empate),
destruncar as descrições da taxonomia (não retroativo) e dar a transcrição completa (pior).

O que ainda não foi testado é **complexidade da decisão**. Os dois auditores usaram um
prompt de **22 temas** (~700 tokens) e convergiram entre si em 91% (kappa 0,90). O
classificador de produção escolhe entre **69 subgrupos** num prompt de ~8.000 tokens e
bate no gabarito em 72,7%. O legado, que era de duas etapas (tema primeiro, subgrupo
depois dentro da frente), fez 76,0%.

Hipótese: **duas decisões fáceis erram menos que uma difícil.**

#### 9.4.3 Teste de complexidade da decisão ✅ — confirmado

| classificação | acerto | IC95 |
|---|---:|---|
| legado — 2 etapas | 76,0% | [69,3 – 81,6] |
| produção — 1 escolha entre **69** | 72,7% | [65,8 – 78,6] |
| **prompt simples — 1 escolha entre 22** | **83,6%** | [77,6 – 88,3] |

McNemar 69 × 22: 19 contra **39**, **p = 0,013**.

*Leitura assimétrica, por desenho:* o gabarito é o consenso de auditores que também
escolhiam entre 22, então um resultado positivo carrega viés compartilhado e a
**magnitude não é confiável**. Mitigação aplicada: o prompt do teste foi reescrito e
reordenado (semente 4242). A **direção** se sustenta por caminho independente — o
classificador legado, de duas etapas, também superou a produção (76,0% × 72,7%).

#### 9.4.4 Classificador de duas etapas ✅ — implementado

`montar_prompt` (escolha única entre 69) foi substituído por duas etapas:

- **Etapa 1** `montar_prompt_tema` — assunto entre 22 opções (~505–582 tokens)
- **Etapa 2** `montar_prompt_subgrupo` — subgrupo dentro da frente já decidida (~1,4k tokens)

`preparar` escreve a etapa 1; `absorver` grava a etapa 1 **e já prepara a etapa 2**;
`absorver` de novo fecha. O estado fica em `_fila/etapa.json`.

**Otimização:** frentes de tema único (P9–P13) e os casos especiais pulam a etapa 2 —
ali o subgrupo é o próprio tema, perguntar de novo seria pagar para receber o que já se
tem. Efeito colateral bom: P10–P13 deixam de sair com subgrupo vazio.

**Custo assumido:** ~1,7x mais tokens, porque o texto é lido nas duas etapas. Foi uma
troca deliberada — acurácia acima de custo, decisão registrada.

**Três defeitos que o teste de integração expôs** (`_auditoria/teste_duas_etapas.py`,
que simula as respostas e não gasta IA):

1. **O hash existia em três versões incompatíveis.** `consolidar_store` gravava o hash do
   texto cru e completo, `absorver` o do texto truncado em 1200, e `preparar` comparava
   com o do texto completo. Todo registro acima de 1200 chars caía numa dessas frestas e
   era marcado como "texto mudou" — **reclassificado a cada execução, indefinidamente,
   pagando IA sem nada ter mudado**. Eram 477 registros. Unificado numa regra só (hash do
   texto exatamente como vai ao classificador) e o cache migrado por `migrar_hash.py`.
2. `preparar` limpava só os `.json` da fila, deixando prompts de execuções anteriores —
   o classificador podia ler o prompt errado. Passa a limpar os `.md` também.
3. O teste inicial acusou falha em registros fora da janela e em frentes de tema único;
   os dois eram expectativa errada do teste, não do código, e foram corrigidos lá.

**Idempotência real:** `preparar` agora devolve **7.792 reusados, 0 a classificar**, e
segue em 0 depois de reconsolidar. Diferente do zero da Fase 2, este é um zero
verificável — o filtro enxerga registro novo, então "0" significa "nada novo", não
"incapaz de ver".

#### 9.4.5 Escopo da reclassificação: 897, não 7.792

A pergunta natural depois de 9.4.4 é "então reclassificar tudo com o desenho novo?".
**Não.** O cache tem duas gerações e só uma delas usou o desenho ruim:

| geração | n | desenho usado |
|---|---:|---|
| `em = 2026-08-05` | 6.898 | exploratório — **já era de duas etapas** (tema, depois subgrupo por frente) |
| `em = 2026-08-07` | 897 | `montar_prompt` — a escolha única entre 69, medida em 72,7% |

Os 6.898 originais nunca passaram pela escolha única. Reclassificá-los seria refazer com
o mesmo desenho que já os produziu e esperar resultado diferente — custo alto, ganho
esperado próximo de zero.

A regressão da Fase 2 atingiu **exatamente os 897 classificados em 07/08**, que são
também os registros marginais recuperados pela correção do filtro, onde a camada N mediu
28% de erro. Reclassificados com as duas etapas. É a intervenção que casa a alavanca
medida com a população que a sofreu.

**O que isso implica para os ~24% do relatório:** eles vêm do desenho de duas etapas e
não são explicados por nenhuma alavanca testada. Continuam valendo como barra de erro
declarada.

**Enquanto isso não fechar, o relatório deve andar com barra de erro declarada** em vez
de precisão fingida: tema de conversa tem ~22% de erro medido, e isso vale para qualquer
leitura de volume por frente.

### 9.6.1 Incidente: o teste de integração apagou a fila de produção

Rodei `teste_duas_etapas.py` com 14 lotes da etapa 2 em andamento. O `finally` do teste
limpava `data/store/_fila/` **incondicionalmente** — apagou os lotes no meio do voo e as
respostas já gravadas. Oito subagentes encontraram a pasta vazia; cinco lotes de trabalho
já concluído foram perdidos e tiveram de ser refeitos.

**O que salvou:** o teste restaura `classificacao.json` do próprio backup, então a etapa 1
(os 6.898 temas) sobreviveu intacta. E os subagentes se recusaram a inventar respostas
para arquivos inexistentes — todos reportaram o problema em vez de gravar lixo.

**Correção:** o teste agora copia `_fila/` inteira antes de rodar e a devolve no `finally`.
A fila é área compartilhada com a produção; um teste que a limpa sem olhar é destrutivo.

**Efeito colateral bom:** ao reconstruir os lotes, entraram também 305 registros que já
estavam sem subgrupo de rodadas anteriores. O universo da etapa 2 foi de 1.413 para 1.573.

**Uma armadilha evitada na recuperação:** o lote original de P6 tinha sido apagado, mas a
resposta dele sobreviveu. Absorver assim faria `absorver` calcular o hash sobre string
vazia — e esses 145 registros seriam reclassificados a cada execução, para sempre, pelo
mesmo mecanismo do defeito de hash já corrigido em 9.4.4. O lote foi reconstruído casando
com os ids da resposta antes de absorver.

### 9.6 Reclassificação dos 6.898 — **INTERROMPIDA, retomável**

Parou por limite de cota da sessão no meio da onda 1. **Nada foi perdido e nada foi
gravado**: o cache está intacto, e as respostas já obtidas estão em disco.

| | |
|---|---|
| escopo | tema dos 6.898 legados (etapa 1); etapa 2 só para quem mudar de tema |
| feito | **2.022 de 6.898** (29%) — os 522 chamados **completos**, 1.500 conversas |
| falta | 20 lotes de conversa (`R_conversa_03` e `08`–`26`) |
| estado do cache | **não modificado** — `reclass_aplicar.py` só rodou em `--dry-run` |

**Como retomar:** classificar os 20 lotes que faltam em `pipeline/_auditoria/reclass/`
(cada `R_conversa_NN.json` com `prompt_tema_conversa.md`, gravando `resp_R_conversa_NN.json`),
depois `python pipeline/_auditoria/reclass_aplicar.py` — sem `--dry-run` — que grava os
temas novos e enfileira a etapa 2 só dos que mudaram.

**Prévia com os 29% já classificados:** 22,9% dos temas mudaram, praticamente igual aos
~24% que a auditoria estimou de erro. É confirmação independente daquela medida.

**Defeito encontrado e corrigido no caminho:** um subagente gravou a resposta com
encoding errado (UTF-8 relido como Latin-1), e 217 rótulos **semanticamente corretos**
seriam descartados como inválidos — 10,7% do lote voltaria ao tema antigo sem ninguém
notar. `reclass_aplicar.py` passou a reparar mojibake antes de validar; reparar é melhor
que reclassificar de novo, que seria pagar IA por um erro de codificação.

### 9.5 Auditoria permanente ✅

`pipeline/auditar.py`, com `preparar` e `medir`, plugado no passo 4b da skill. Sorteia 50
registros da janela estratificados por frente, escreve lotes **cegos** para dois
avaliadores independentes e mede erro por consenso, ambiguidade e kappa. Semente derivada
da janela, então o mesmo período dá a mesma amostra e o número é comparável entre execuções.
Registros com `fonte: chat` ficam de fora — a causa deles veio da conversa cruzada, que o
avaliador não vê, e contá-los mediria a cegueira do auditor.

Dispara `ATENÇÃO` acima de 30% de erro ou abaixo de 0,75 de kappa, e a skill é instruída a
repassar o aviso ao usuário junto com o relatório.

**Primeira execução, janela 01/05–05/08:**

| | n | erro | ambiguidade | kappa |
|---|---:|---:|---:|---:|
| chamado | 13 | 7,7% [1–33] | 7,7% | 0,916 |
| conversa | 46 | 37,0% [25–51] | 8,7% | 0,900 |
| **total** | 59 | **30,5%** [20–43] | 8,5% | 0,906 |

Alerta disparado logo de cara. Duas ressalvas de leitura: n=59 é pequeno e o IC é largo; e
a amostra **mistura as duas gerações** — 897 registros com o desenho de duas etapas e 6.898
com o antigo. O 37,0% em conversa não contradiz os 21,9% da Fase 8, mas também não é
comparável a eles: aquele mediu só o núcleo original, este inclui os marginais recuperados,
que a camada N já mostrou serem mais difíceis.

### 9.5.1 (histórico do item)

- [ ] Embutir no `/build-report` uma amostra fixa de ~50 itens com dupla avaliação cega,
      reportando erro por consenso e kappa junto com a deriva. O buraco aqui não foi a
      classificação ter erro — foi ninguém ter como saber que tinha

### Fora de escopo (medido, não move ranking)

- Os 401 falsos positivos já marcados pela IA não foram reavaliados
- Subgrupos de chamado em P9 e P7 (100% vazios, nada a auditar)
- Corte de 25 mensagens no digest: 59,8% das conversas fiscais excedem. Medido como
  exposição, não como erro. Não perde o problema (aparece cedo), pode perder a causa raiz

### Incerteza que permanece

Os avaliadores de falso negativo julgaram só "é fiscal ou não", **sem atribuir frente**.
Não se sabe onde as ~1.059 conversas recuperadas cairão. Se estiverem concentradas numa
frente, o ranking da Fase 8 muda mais ainda. É a maior incerteza aberta, e ela se resolve
sozinha ao executar 9.4.

---

## Pendências com o time

Resolvidas em 07/08/2026:

- ~~`output/problemas_2026-08-05.xlsx` sem destino definido~~ — a pasta `output/` não
  existe mais; a saída oficial é `report/`.
- ~~Nada commitado; avaliar `.gitignore` para `data/raw/`~~ — commitado, e `data/raw/`
  ignorado junto com `base_historica.jsonl` e as áreas de trabalho de fila e auditoria.

Em aberto, e nenhuma delas bloqueia uso:

- **Subgrupo de P7 em chamado** (24 registros). Volume baixo, não move ranking.
- **P13 tem 22 registros em "Outro"** concentrados em quatro assuntos que a taxonomia não
  cobre: preço de custo/margem não atualizado pela compra, integração TEF/maquininha,
  integração com o Cilia, e o vínculo NF ↔ OS. É candidato natural ao próximo bump —
  foi o próprio classificador que apontou.
- **Os 543 registros sem frente** (`Não fiscal` + `Conversa vazia`) nunca foram
  reavaliados. São o custo declarado do filtro ampliado.

## Como ler o resultado

O relatório **não sustenta ranking exato**. O topo — P1 (1.580), P8 (1.136), P7 (1.042) —
é empate estatístico: a diferença entre eles é menor que a barra de erro medida. Ele
sustenta leitura **por bloco**: existe um bloco de ~1.000–1.600 no topo, outro de ~700–900,
e o resto.

Erro medido pela auditoria de amostra após a reclassificação: **13,6%** no total
(0,0% em chamado, 17,4% em conversa; n=59, kappa 0,872).
