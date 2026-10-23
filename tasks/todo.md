# Separar V2 de V3 — análise e plano

Data da análise: 23/10/2026. Fonte: API do Bitrix (leitura direta), 2.978 chamados
criados em 2026 no grupo 139 e 3.414 sessões de canal aberto criadas desde 01/10.

## O que encontrei

### Chamados — três marcas, uma confiável

| Sinal | Como ler | Cobertura em 2026 |
|---|---|---|
| Tag `novaversao` | `task.item.getdata` → `TAGS` | 39 chamados |
| Colunas de rollout | `STAGE_ID` ∈ 3441 / 3443 / 3483 | 17 chamados, todos já com a tag |
| Título | `[Nova Versão…]`, `V3`, `V3.0`, `[V.3]` | 18 chamados, 1 sem a tag |
| URL `sistema3.ultracar.com.br` na descrição | regex na descrição | 1 chamado |

União = **40 chamados**. Primeiro deles em 04/09/2026.

Detalhes que mudam a regra:

- `TAGS` **não existe** em `tasks.task.list` nem em `tasks.task.get`. Só o endpoint
  legado `task.item.getdata` devolve. O coletor C# hoje não traz esse campo.
- A coluna **3357 "Nova Versão" não serve**: existe desde 09/02/2026 e guarda melhoria
  de V2 destinada à próxima release. Das 28 ocupantes, 19 não têm nada de V3.
  As colunas de V3 são as três criadas em set/out: **3441 Rollout - Nova Versão**,
  **3443 Validação com cliente - Rollout Nova Versão**, **3483 Chamados Concluídos - Nova Versão**.
- Coluna é posição no board, muda com o tempo: 10 dos 39 chamados com a tag já estão em
  "Chamados Concluídos" (1445). A tag é fixa; a coluna não.
- `patio.ultracar.com.br` **não** é V3 — é o produto Gestão de Pátio, com chamados desde
  fevereiro. Não usar como sinal.
- Os campos `UF_ULTRACAR_CONVERSATION_ID` / `UF_ULTRACAR_USER_ID` (696 chamados, abr–out)
  são do chat interno do sistema **V2**, não marcam V3.

### Conversas — o canal resolve

`imopenlines.config.list.get` lista 6 canais. O link `/online/suportev3` corresponde ao
**LINE_ID 17 — "Atendimento V3 Ultracar"**. O V2 é o LINE_ID 7 — "Suporte Ultracar".

O coletor já extrai esse id: `UserCodeParser` lê `livechat|<LINE_ID>|...` do `entity_id`
e grava em `LineId` na aba Conversations. **O dado já existe no XLSX e é perdido no
`consolidar_store.py`.**

Das 3.414 sessões desde 01/10: 3.394 na linha 7, **20 na linha 17** (a primeira em
19/10/2026).

Duas bordas, medidas:

- **9 sessões** entraram pela linha 7 e foram transferidas para a fila V3 (mensagem de
  sistema "redirecionou a conversa da fila Suporte Ultracar para a fila Atendimento V3
  Ultracar"), todas em 22–23/10. São V3 e o `LineId` não as pega.
- **15 sessões** têm `entity_data_1[7] == 17` sem transferência: é o chat do cliente que
  hoje está vinculado à linha V3, e isso reetiqueta conversas antigas (ex.: Alinha Certo
  em 06/10, antes de a linha V3 existir). **Não usar** — quebra a série temporal.

## Regra proposta

**Chamado é V3 se** tem a tag `novaversao`, **ou** está numa das colunas 3441/3443/3483,
**ou** o título casa `\[\s*nova\s+versão[^\]]*\]|\bv3\b|\[\s*v\s*\.?\s*3\s*\]`,
**ou** a descrição cita `sistema3.ultracar.com.br`.

`\bv3\b` em vez de `v3\.0`: pega 18 títulos, nenhum falso positivo em 2.978, e recupera
o 106419 (SR Motors, "Cadastro do Usuario no sistema novo … Ultracar V3").

**Conversa é V3 se** `LineId == 17`, **ou** o histórico tem mensagem de transferência para
a fila "Atendimento V3 Ultracar".

Tudo que não for V3 é V2. O campo `versao` entra na base como coluna, não como filtro
embutido — assim os dois relatórios saem da mesma base.

## A decisão que é sua

Dos 40 chamados, **25 têm marca explícita de V3** (título ou coluna de rollout) e
**15 só têm a tag `novaversao`** — todos no template `[Melhoria] | Funcionalidade`, de
clientes V2, e quatro deles criados entre abril e agosto, antes de a V3 existir para
cliente. Lendo as descrições (107125, 106965, 107167, 107303), são pedidos de melhoria do
V2 **que serão entregues na nova versão** — não chamados abertos *na* V3.

A tag tem dois sentidos. Opções:

- **A — conservadora:** V3 = marca explícita (25 chamados). A tag sozinha vira
  "melhoria prevista para a V3" e fica fora do relatório V3.
- **B — ampla:** V3 = união (40 chamados), como na regra acima.
- **C — separada:** reportar as duas faixas, "V3 confirmado" e "melhoria para a V3".

Minha recomendação é **C**: a base ganha a coluna `versao` com três valores
(`V2`, `V3`, `V3-backlog`), e o `V3-backlog` **conta como V2** nos números.

Onde cada faixa entra, medido:

| Faixa | Chamados 2026 | Fiscais | Relatório |
|---|---|---|---|
| V2 | 2.938 | 1.510 | V2 (filtrado por fiscal) |
| V3-backlog | 15 | 1 | V2, e como anexo do V3 |
| V3 | 25 | 3 | V3 |

O motivo de o backlog ficar no V2: o cliente está no V2 e a fricção aconteceu no V2.
"Sai na nova versão" é destino da correção, não origem da queixa.

O corte quase não mexe no relatório V2 — só 1 dos 15 passa no filtro fiscal, contra 1.510.
A coluna existe para proteger o relatório V3, onde 25 e 40 são números bem diferentes.

**O corte não precisa ser decidido agora.** A coluna guarda as três faixas; qual delas
entra no relatório V3 é um filtro de uma linha, trocável depois de ver os dois números.
No V3 o backlog entra como tabela à parte, "melhorias do V2 que a V3 já endereça",
fora da contagem principal.

## Buracos de coleta que travam os dois relatórios

- **Conversas só existem desde 01/05/2026** na base local. Para "desde janeiro" faltam
  ~18.100 sessões (jan 5.174, fev 3.850, mar 4.603, abr 4.498) mais ~7.950 de set/out.
- **Chamados de abril**: a base tem 42, a API tem 230. Faltam 188.
- **Chamados de set/out**: 491 ainda não coletados.
- O coletor precisa passar a trazer `TAGS` (via `task.item.getdata`) e o
  `consolidar_store.py` precisa propagar `LineId` para a conversa.

## Plano de ação

Decidido em 23/10: `V3-backlog` conta como **V2** nos números, mas mantém marca própria
para virar anexo do relatório V3.

### Fase 1 — código (nada roda contra o Bitrix ainda)

- [x] `TaskCollectorService.cs`: somar `task.item.getdata?TASKID=` ao batch, que é o único
      endpoint que devolve `TAGS`. São 7 endpoints por chamado, então o chunk cai de 8
      para 7 tarefas (7×7=49, limite 50).
- [x] `consolidar_store.py`: gravar quatro campos novos no registro — `versao`, `tags`,
      `stage` (chamado) e `linha` (conversa).
      - chamado: `V3` se tag `novaversao` + marca explícita; `V3-backlog` se só a tag;
        senão `V2`
      - conversa: `V3` se `LineId == 17` ou se a aba Messages tem a mensagem de sistema
        de transferência para a fila "Atendimento V3 Ultracar"; senão `V2`
      - a detecção de transferência fica no pipeline, lendo o XLSX que já existe —
        não precisa mexer no exportador C#
- [x] Rodar `consolidar_store.py` sobre o `data/raw/` atual e provar que nada mudou:
      2.908 chamados e 16.669 conversas, só com os campos a mais.

Exports antigos não têm `TAGS`. Isso não atrapalha: todo chamado anterior a setembro é V2
de qualquer jeito, e os de set/out virão na coleta nova já com a tag.

**Fase 1 fechada em 23/10.** Verificação: coleta de teste de 2 dias trouxe `tags` no JSON,
e `consolidar_store` rodado sobre o `data/raw/` inteiro deu **0 campos antigos alterados**,
+7 chamados (os do teste) e os quatro campos novos em 100% dos 19.584 registros. A coleta de
teste foi desfeita de `coleta.json` — como marco de retomada ela diria que o delta começa em
22/10, quando set e out inteiros ainda faltam.

**Achado da coleta de teste:** `--to` é exclusivo. `--to 2026-10-23` vira
`<=CREATED_DATE 2026-10-23 00:00:00` e deixa o próprio dia 23 de fora. Na coleta mês a mês,
passar o primeiro dia do mês seguinte — `--from 2026-01-01 --to 2026-02-01` — senão some
o último dia de cada mês.

### Fase 2 — relatório V3 (barato, sai primeiro)

- [x] Coletar set e out: saiu 496 chamados e 7.961 conversas
- [x] Consolidar e conferir: 29 chamados V3 e 31 conversas V3 (os 4 e 2 a mais são
      registros criados depois da análise, não reclassificação)
      (20 que entraram pela linha 17 + 9 transferidas para a fila V3)
- [x] Classificar os 60 e gerar o relatório

**Fase 2 fechada em 23/10.** `report/relatorio_v3_2026-09-01_2026-10-23.xlsx`, quatro abas.
A maior frente é lacuna de paridade com a V2 (13 de 55, 23,6%), e Ordem de Serviço concentra
18 dos 55 registros. Os códigos das frentes são R1..R6 — V1..V6 colidia com V2/V3, que no
relatório são as versões do sistema.

### Fase 3 — relatório V2 fiscal desde janeiro (é o grosso)

- [x] Chamados de jan a ago recoletados com tags (2.487) — abril fechou em 230, como a API
- [ ] Conversas de jan a abr, **um mês por vez**: 18.125 sessões
- [ ] Consolidar
- [ ] Classificar: ~14.000 registros novos (53,5% das conversas passam no filtro fiscal),
      o que dá ~58 lotes na etapa 1 mais ~58 na etapa 2
- [ ] Gerar o relatório fiscal de 01/01 até hoje

### Classificação da V3

Os 54 registros são classificados — entregar lista crua não é opção. O que muda em relação
ao fluxo fiscal:

- **A taxonomia sai dos próprios registros, não da fiscal.** Dois eixos que o time de
  suporte já escreve hoje, mais um terceiro derivado da leitura:

  | Eixo | De onde vem | Distribuição nos 25 chamados |
  |---|---|---|
  | Módulo | colchete do título | OS 4, Financeiro 3, Auto-guias 2, Fiscal 2, Checklist, Cadastro, Visão Geral, Orçamentos & Serviços, NFSe, e 8 sem colchete (módulo no corpo do título) |
  | Natureza | tag do chamado | melhoria 13, erro 7, orientação 1, 4 sem tag |
  | Subgrupo | leitura dos 54 | a definir ao ler |

  Conversa não tem título nem tag, então os dois primeiros eixos saem da leitura do texto.

- **Roda numa passada só, sem a fila de lotes.** O pipeline fiscal quebra em lotes de 250
  porque lida com milhares; 54 registros cabem numa leitura. A máquina de `_fila/` continua
  existindo para o fiscal e não é tocada.

- **Grava com o mesmo contrato das outras**, em `data/store/classificacao_v3.json`:
  tema, subgrupo, frente, fonte e hash do texto. Isso importa porque o relatório V3 vai ser
  regerado conforme o rollout cresce, e o que já foi classificado não pode ser reclassificado.

- A taxonomia nasce congelada e versionada em `data/store/taxonomia_v3.json`, como as outras.
  Alterar exige bump de versão.

### Entregáveis

Hoje `report/` tem cinco arquivos porque a rodada não fiscal de 31/08 somou três ao
formato canônico. O que a skill produz de verdade são dois: um agrupado e um linha a linha.

Proposta para esta rodada — **três arquivos**:

| Arquivo | Conteúdo |
|---|---|
| `relatorio_executivo_fiscal_2026-01-01_<hoje>.xlsx` | V2 agrupado: frente → subgrupo, chamados e conversas lado a lado, tempo total, tempo tech, última incidência e recência |
| `base_unificada_fiscal_2026-01-01_<hoje>.xlsx` | V2 linha a linha, chamados e conversas na mesma aba com coluna `Tipo`, agora mais a coluna `Versao` (`V2` / `V3-backlog`) |
| `relatorio_v3_<de>_<hoje>.xlsx` | V3 inteiro num arquivo só, 4 abas: `Resumo`, `Chamados`, `Conversas`, `Melhorias V2 para a V3` |

Por que a V3 cabe em um arquivo: são 54 registros (25 chamados + 29 conversas). Separar
executivo de base nessa escala cria dois arquivos que o leitor abre e fecha. O agrupamento
da aba `Resumo` sai da taxonomia V3, não da fiscal.

As abas de chamado ganham link direto para o chamado no board (confirmar o formato da URL
do grupo 139 na hora de montar). Conversa não tem URL estável, então fica só o id da sessão.

### O que eu já sei que vai incomodar

- **O relatório V3 é pequeno:** 25 chamados e 29 conversas, com conversa só a partir de
  19/10. Vai sair classificado e agrupado como qualquer outro, mas quatro dias de canal
  não viram série temporal — gráfico de tendência ali seria enfeite.
- **A fase 3 custa ~1,6x tudo que já foi classificado no projeto** (o cache tem 8.910
  conversas hoje). Não cabe numa sessão.
- Taxonomia V3: **os 54 registros vão ser classificados**, como todo o resto. O que muda
  em relação ao fluxo fiscal é de onde vem a taxonomia e como ela roda, não se há rótulo.
