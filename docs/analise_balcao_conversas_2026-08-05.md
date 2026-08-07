# Análise do Balcão — O que o chat mostra e os chamados escondem

**Fonte:** Open Lines do Bitrix24 (WhatsApp, LiveChat, Telegram) — `conversations_export_20260805_134927.xlsx`
**Período:** 2026-05-01 a 2026-08-05 · 13.282 conversas / 379 mil mensagens
**Complementa:** `analise_chamados_fiscais_2026-08-04.md` (análise dos 522 chamados fiscais)
**Gerado em:** 2026-08-05

## Por que esta análise existe

A análise anterior mediu apenas o que virou **tarefa no Bitrix** (522 chamados fiscais). Mas a maior parte do atendimento acontece e termina no **chat**, sem gerar ticket. Este documento classifica as conversas com a mesma taxonomia dos chamados, mais categorias específicas de balcão, para responder duas perguntas que os tickets não respondem:

1. Qual o **tamanho real** de cada dor, contando o que é resolvido no balcão?
2. Que dores existem **só no chat** e estavam completamente invisíveis?

**Método:** filtro fiscal por palavra-chave sobre o digest de cada conversa → 6.376 conversas fiscais (48% de todo o chat); classificação por leitura de todas elas (16 lotes, taxonomia de 22 categorias); descarte de 401 conversas vazias ou falso-positivo → **5.975 conversas fiscais úteis**.

## O número que muda a régua: índice iceberg 11,4×

**Para cada chamado fiscal aberto, existem 11,4 conversas fiscais no chat.** E **75% das conversas fiscais nunca viraram chamado** — foram resolvidas, contornadas ou abandonadas no balcão.

Isso significa que a priorização anterior, feita só com tickets, enxergava menos de 10% da demanda fiscal real.

## Ranking por carga de atendimento

"Carga" = participação do tema no total de mensagens trocadas em conversas fiscais (métrica robusta — ver ressalva metodológica no fim). "Iceberg" = conversas por chamado do mesmo tema.

| Tema | Conversas | Carga | Chamados | Iceberg | % sem ticket |
|---|---|---|---|---|---|
| Rejeição/erro de validação (schema, E0xxx, tags, IE) | 1.409 | 21,7% | 80 | 17,6× | 80% |
| **Nota de devolução/garantia/remessa/complemento** | **861** | **15,3%** | 24 | **35,9×** | 80% |
| Cálculo/exibição de impostos (PIS/COFINS/ICMS/ISS/IBS/CBS) | 377 | 7,2% | 38 | 9,9× | 76% |
| **Dúvida de uso / orientação (how-to fiscal)** | **497** | **7,2%** | — | *novo* | 79% |
| Particularidade municipal de NFS-e | 379 | 6,8% | 20 | 18,9× | 74% |
| Cadastro/config fiscal (NCM, CFOP, CST, cód. serviço) | 350 | 6,5% | 40 | 8,8× | 78% |
| Cancelamento/exclusão de nota | 287 | 4,6% | 19 | 15,1× | 81% |
| Numeração/duplicidade (RPS, DPS, inutilização) | 236 | 4,5% | 35 | 6,7× | 63% |
| **Configuração assistida pelo suporte** | **226** | **4,5%** | — | *novo* | 73% |
| Certificado digital | 263 | 3,8% | 20 | 13,2× | 85% |
| XML de compra / manifestação do destinatário | 214 | 3,5% | 12 | 17,8× | 69% |
| Nota travada em processamento sem retorno | 203 | 3,4% | 23 | 8,8× | 74% |
| Integração financeiro/estoque/OS com a nota | 159 | 3,0% | 26 | 6,1× | 58% |
| **Acompanhamento de chamado já aberto** | **134** | **2,1%** | — | *novo* | 28% |
| PDF/DANFE/impressão | 132 | 2,0% | 42 | **3,1×** | 60% |
| **Instabilidade geral / lentidão do sistema** | **137** | **1,6%** | — | *novo* | 74% |
| Status dessincronizado sistema × prefeitura/SEFAZ | 60 | 1,1% | 51 | **1,2×** | 42% |
| Relatórios fiscais divergentes | 33 | 0,8% | 12 | 2,8× | 48% |
| Envio de nota por e-mail | 15 | 0,3% | 11 | 1,4× | 33% |
| NFS-e interna / API interna | 3 | 0,0% | 8 | 0,4× | 33% |

## Os cinco achados que mudam decisão

### 1. Devolução/garantia é a segunda maior dor do produto — e estava praticamente invisível
861 conversas contra 24 chamados: **índice iceberg de 35,9×, o maior de todos**. Era 4,6% dos chamados; é 15,3% da carga do chat. As conversas mostram que quase nunca é bug — é **fluxo mal desenhado**.

> **Correção (censo de 05/08):** a primeira leitura, feita por amostra, atribuía a dor principal ao cliente não saber que precisa importar o XML da compra antes de emitir a devolução. Classificando as 861 conversas uma a uma, isso é apenas ~11% dos casos. A causa dominante é outra: **o sistema não herda os tributos do XML da compra** (204 conversas, 24%). O fornecedor exige que BC ICMS, ST, IPI e frete batam com o espelho dele até o centavo; o cliente digita item a item sem saber em qual campo, e o botão "calcular tributos" ainda sobrescreve o que ele preencheu.

**Ação:** proposta própria (P7) — herdar automaticamente os tributos da compra de origem item a item, pré-preenchidos e editáveis, com comparação lado a lado contra o espelho do fornecedor. O fluxo guiado de primeira devolução continua valendo, mas é a segunda prioridade dentro da frente, não a primeira.

### 2. PDF/DANFE deve cair na prioridade
Nos chamados era a dor nº 3 (42 chamados, 8%). No chat é apenas 2% da carga, com **iceberg de 3,1× — um dos mais baixos**. Interpretação: quando o PDF falha, o cliente abre chamado (é bloqueante e não tem contorno no balcão), mas o volume real é pequeno. A proposta P4 estava superdimensionada pelo viés de ticket.

### 3. Status dessincronizado é o oposto: quase tudo já virava ticket
Iceberg de 1,2× — a dor mais fielmente representada nos chamados. Faz sentido: o operador não consegue resolver no chat (precisa de dev para reconciliar), então escala. **A P2 (reconciliação) mantém a prioridade**, e o número de tickets já era o tamanho real dela.

### 4. Um quarto da carga do balcão não é defeito — é lacuna de autonomia
Somando how-to (497), configuração assistida (226), acompanhamento de chamado (134) e instabilidade (137): **994 conversas, 15,4% da carga**, sem nenhum equivalente em chamados. Dentro disso, dois padrões concretos:

- **"Me passa seu AnyDesk"** — o operador entra na máquina do cliente para ajustar um parâmetro. Certificado digital (iceberg 13,2×, 85% sem ticket) e o `regEspTrib` do Simples Nacional são os campeões: dezenas de conversas idênticas resolvidas com o mesmo clique.
- **Acompanhamento de chamado (134 conversas, único com 28% sem ticket)** — clientes usando o chat como canal de status porque não têm visibilidade do próprio chamado.

**Ações:** self-service de certificado; valor padrão correto de `regEspTrib` por regime no cadastro; página de status do chamado para o cliente.

### 5. Três incidentes concentrados inflam as estatísticas — e devem ser lidos à parte
Identificados na leitura, todos com assinatura textual isolável:
- **Surto PIS/COFINS obrigatório** (chamado 101927): dezenas de conversas com o mesmo erro de base de cálculo, contornadas com o paliativo "zerar alíquotas".
- **Queda da integradora fiscal em 25/06** (chamados 103967/103969): 28 conversas em bloco, SEFAZ SP/MG/GO.
- **Importação de XML de compras desativada pelo desenvolvimento**: um cluster único responde pela maior parte da categoria naquele período.

Não são demanda recorrente; são eventos. Ao dimensionar equipe ou backlog, descontar.

## Impacto nas propostas P1–P6

| Proposta | Chamados | Conversas | Carga do chat | Veredito |
|---|---|---|---|---|
| P1 Pré-validação | 80 | 1.409 | 21,7% | **Confirmada como nº 1** nos dois canais |
| P2 Reconciliação | 109 | 499 | 8,0% | Mantida — tamanho já era fiel |
| P3 Impostos | 38 | 377 | 7,2% | Mantida — cresce com IBS/CBS |
| P4 PDF/DANFE | 42 | 132 | 2,0% | **Rebaixar** — superdimensionada |
| P5 Triagem | 61 | — | — | Mantida (problema de processo) |
| P6 Municipal + certificado | 40 | 642 | 10,6% | **Subir** — 2,6× maior do que parecia |
| **P7 (nova) Devolução guiada** | 24 | 861 | 15,3% | **Criar** — 2ª maior dor real |
| **P8 (nova) Autonomia/self-service** | — | 994 | 15,4% | **Criar** — invisível nos tickets |

## Ressalva metodológica sobre "horas"

A intenção original era medir horas de atendente por tema. **O dado não sustenta um número absoluto confiável:** a duração registrada é a janela da sessão (abertura até fechamento/auto-close), que inclui ociosidade e espera. Somando as janelas, mesmo truncadas no percentil 90, chega-se a ~2.500 h/mês — acima da capacidade total dos 12 operadores (~1.920 h/mês), o que prova a superestimação; os operadores também atendem várias conversas em paralelo.

Por isso o ranking usa **participação na carga de mensagens**, que é robusta: as três métricas possíveis (nº de conversas, janela truncada e mensagens) produzem praticamente a mesma ordenação, com desvios abaixo de 4 pontos percentuais. Para obter horas reais seria necessário um campo de tempo de atendimento efetivo, que o export do Bitrix não fornece.


## Atualização — censo por subgrupo (05/08, pós-publicação)

As frentes P1, P7 e P8 tiveram **100% das conversas classificadas por subgrupo** (3.264 conversas, sem falha de cobertura), substituindo as estimativas por amostra. Três correções relevantes:

### O censo desmentiu parte da amostra
Em P7 e P8, subgrupos mudaram de tamanho o suficiente para alterar prioridade interna: "Compra não elegível" caiu de 22% para 11%, "Garantia/remessa sem operação nativa" subiu de 8% para 14%, e "Cliente sem visibilidade do status" subiu de 20% para 28%. O topo de P7 se manteve — "Destaque manual de impostos" com 204 conversas (24%).

### P1: CFOP/CST era o 6º validador e é o 1º
Este é o achado que mais muda decisão. Classificando as 1.409 conversas de rejeição:

| Validador | Chamados | Conversas | Iceberg |
|---|---|---|---|
| **CFOP/CST incompatíveis com a operação ou regime** | 7 | **411** | **59×** |
| Cadastro do destinatário/tomador incompleto | 13 | 221 | 17× |
| Códigos do item/serviço (NCM, GTIN, cód. municipal) | 13 | 193 | 15× |
| Falha de schema XML na geração | 12 | 162 | 14× |
| Regime/alíquota de ISSQN | 15 | 126 | 8× |
| Consistência de pagamento/fatura | 5 | 46 | 9× |
| Série/numeração de RPS e habilitação do emissor | 12 | 31 | 3× |

Pela ótica de chamados, ISSQN liderava e CFOP/CST era o penúltimo. Pela carga real de atendimento é o oposto. A explicação está nas conversas: erro de CFOP o atendente resolve na hora, então raramente vira ticket — mas é o que mais consome atendimento. Agrava que **o suporte tem política de não indicar CFOP** (responsabilidade da contabilidade), o que deixa o cliente em ping-pong com o contador. **Sugestão automática de CFOP por operação/UF/finalidade é a ação de maior alavancagem de toda a P1.**

Ressalva: parte do volume de CFOP/CST vem da onda pontual de erro de PIS/COFINS (chamado 101927) já identificada como incidente concentrado. Mesmo descontando, a liderança se mantém.

### "Ciclo de vida da nota" foi dividido em dois
Com os 224 casos reais, o bloco de correção pós-emissão se mostrou coeso e separável: **65 conversas** tratam especificamente dos limites da carta de correção e do prazo de cancelamento — o cliente descobre depois de transmitir que a CC-e não altera CFOP, ou procura a opção em NFS-e e não encontra. Virou subgrupo próprio, com assistente de correção como ação. As 159 restantes seguem em "não sabe concluir a emissão e não vê o erro".

### Um bloco novo apareceu em P7
12% das conversas de devolução (106) não couberam em nenhum subgrupo, e dentro delas há dois padrões que a amostra não tinha revelado: **erros de IBS/CBS especificamente em devolução** (`cMunFGIBS`, `Grupo de Devolução do IBS`) e **erro no campo de condição de pagamento** ("sem pagamento" / valor 0,00) na nota de devolução. Candidatos a subgrupo próprio na próxima iteração.


### P3: IBS/CBS não é tendência, é uma curva explodindo agora
Classificando as 377 conversas de impostos, o resultado imediato surpreende: **ISS/ISSQN (102) e ICMS (93) dominam o volume**, e IBS/CBS aparece só em 3º (79). Pelos chamados, IBS/CBS era o maior subgrupo da frente. Interpretação: ISS e ICMS são dor crônica que o atendente resolve no chat; IBS/CBS vira chamado porque é problema novo, sem contorno conhecido.

Mas a distribuição no tempo muda tudo:

| Semana | Conversas de IBS/CBS |
|---|---|
| 04/05 a 22/06 (7 semanas) | 17 no total |
| 13/07 | 2 |
| 20/07 | 8 |
| 27/07 | 6 |
| **03/08 (3 dias úteis)** | **46** |

**62% de todo o volume de IBS/CBS do trimestre aconteceu nos últimos 7 dias.** Em agosto, 84% das conversas de impostos são de IBS/CBS, contra 2,5% em junho. Os erros são concretos e repetidos: `ibscbs.municipio.aliquota - Preenchimento obrigatório`, NFS-e Nacional exigindo CST/cClassTrib, e empresas do Simples Nacional destacando IBS/CBS quando não deveriam.

**Consequência para a priorização:** a P3 não deve ser dimensionada pelo volume acumulado do trimestre (79 conversas parecem pouco), e sim pela taxa atual. Se a curva das últimas semanas se mantiver, IBS/CBS sozinho passa qualquer outro subgrupo fiscal em poucas semanas. É a única frente da análise com dinâmica de urgência — as demais são estáveis.

### Blocos sem subgrupo encontrados no censo de P3
35 conversas (9%) não couberam nos subgrupos existentes, e dentro delas há um padrão nítido de **IPI** (código de enquadramento, CST de IPI, base de cálculo, IPI não destacado) e alguns casos de **IRRF**. Nenhum dos dois tem subgrupo previsto — candidatos para a próxima iteração.


### P2 e P6: as duas últimas frentes também inverteram
Com o censo concluído nas 6 frentes, P2 e P6 mostraram o mesmo padrão de inversão já visto em P1.

**P2 — a fase 1 do job de reconciliação deve mudar de ordem.** "Refletir autorização", que era a maior função por chamados (26), tem apenas 22 conversas — iceberg 1×, ou seja, sempre vira ticket. As duas funções realmente demandadas são **destravar nota presa sem retorno (207 conversas)** e **realinhar contador de numeração / duplicidade de DPS (184, iceberg 13×)**. Recomenda-se reordenar a fase 1 para começar por essas duas.

**P6 — certificado digital é a maior dor da frente, e a migração ao Emissor Nacional é a mais urgente.** Somando os quatro subgrupos de certificado: **247 conversas**, sendo os maiores "cliente não conclui a instalação sozinho" (131) e "renovação não reconhecida pelo sistema" (90) — um problema de self-service e um bug de cache, não complexidade fiscal. Já a migração para o Emissor Nacional tem apenas 3 chamados mas **136 conversas (iceberg 45×)**.

### A onda do Emissor Nacional é muito maior que o previsto
A definição original do subgrupo citava Limeira-SP, Rio Grande-RS e Itajaí. O censo revelou uma migração em curso em dezenas de praças, com datas: **Joinville-SC (desde 20/07)**, Guarulhos, São Luís, Blumenau, Barueri, Anápolis, Goiânia, Primavera do Leste-MT, Santa Maria de Jetibá-ES, Mossoró, Chapecó, Laranjal Paulista, **Contagem-MG (01/09)**, **Limeira-SP (01/09)** e **São Paulo (setembro)**.

Somado à curva de IBS/CBS da P3 — 62% do volume do trimestre nos últimos 7 dias —, o quadro é de **uma janela de risco concentrada em setembro de 2026**, em que a reforma tributária e a migração municipal batem juntas. Esta é a conclusão mais urgente de toda a análise.

### Um bloco novo: pendências no portal que bloqueiam a emissão
Cerca de 20 conversas tratam de bloqueios administrativos no portal municipal (L097-DTE/ISS.net, L147/L039 de autorização de RPS, CEP com final 000 rejeitado, token, permissão de acesso). Ficaram acomodadas em "Campo/regra municipal" por falta de bucket melhor. Não é defeito do ERP, mas o cliente aciona o suporte — candidato a subgrupo próprio, com solução de diagnóstico e orientação em vez de correção de código.

### Cobertura atual
**Censo concluído: as 4.914 conversas de todas as frentes (P1 a P8) foram classificadas por subgrupo**, uma a uma, sem falha de cobertura. Na base unificada, 4.914 das 6.376 conversas fiscais têm subgrupo; as 1.462 restantes são de P9 (onde o subgrupo equivale ao próprio tema) e as descartadas como vazias ou falso-positivo.

## Revisão dos planos de ação (05/08)

Os planos de ação foram revisados por Lucas diretamente na planilha executiva. A versão revisada passou a ser a fonte da verdade (`analysis/acoes_user.json`) e tem precedência sobre o texto gerado. Principais decisões registradas na revisão:

- **Dois subgrupos renomeados** para linguagem mais direta: "Primeira devolução: cliente aprende por PDF, não pelo sistema" (P7) e "Emissão não conclui: falta clicar Transmitir e o erro fica escondido em Consultar Situação" (P8).
- **Viabilidade técnica marcada como pendente** em seis ações que dependem de API/endpoint de terceiros: validação de cTribMun contra lista municipal, alíquota de ISSQN por município, credenciamento do emissor, consulta do último número autorizado na SEFAZ, monitoramento de webservices municipais e busca automática de notas contra o CNPJ (manifestação do destinatário). Nenhuma delas deve entrar em roadmap antes dessa checagem.
- **Ações removidas por decisão de escopo:** instrumentação do retorno bruto da SEFAZ (P1), diagnóstico automático do job (P2), detecção de chamados duplicados na abertura (P5), formulário estruturado de alteração (P5) e monitoramento de entregabilidade de e-mail (P9).
- **Dois casos rebaixados para investigação antes de ação:** "nota emitida na SEFAZ não aparece no sistema" (P2) e "nota cancelada na prefeitura permanece autorizada" (P2) — neste, a observação é que é preciso entender primeiro o motivo do cancelamento direto na SEFAZ.
- **Consolidação reconhecida:** a função de refletir autorização (P2) foi marcada como resolvida pelo job proposto no subgrupo de nota presa, confirmando o insight de mecanismo compartilhado.
- **Ideias novas incorporadas:** tradução de mensagens de erro por IA (P1) e portal do contador com configuração de todos os parâmetros (P8), este substituindo o formulário por link.
- **Uso do sinal de recência:** em "consistência de pagamento/fatura" (P1), a revisão anotou que a última incidência é antiga e que vale confirmar se o problema ainda existe antes de investir.

## Correção da coluna de última incidência (05/08)

A coluna "Última incidência" considerava **apenas os chamados**, porque foi calculada antes de existir classificação de conversa por subgrupo. Recalculada sobre as duas fontes, **44 dos 69 subgrupos mudaram de data** e o quadro de recência ficou bem mais quente: agora são 66 subgrupos ativos (últimos 30 dias), 3 em atenção e nenhum antigo.

**Isso derruba a hipótese anterior de que algo já teria sido corrigido.** O caso "Certificado: atualização quebrou a emissão" era o único marcado como antigo (última em 01/06) e eu havia sugerido confirmar com o time se já estava resolvido. Com as conversas, a última incidência é **28/07** — o problema continua ativo, só não gerava mais chamado. Os laranjas anteriores (CFOP/CST em 01/07, consistência de pagamento em 30/06, valor líquido em 24/06, entre outros) também se mostraram ativos: quase todos tiveram conversa nos últimos dias do período.

Os únicos três que permanecem fora da faixa ativa são os buckets "Outros/heterogêneos" de P1, P2 e P3 — resíduos sem padrão, o que é esperado.

**Lição para o método:** medir recência só por ticket subestima sistematicamente o que está vivo, porque a maior parte da dor é absorvida no chat sem virar chamado. Qualquer acompanhamento futuro deve usar as duas fontes.

## Dados e reprodução

Classificação completa em `analysis/` no repositório (`sub_conv_final.json` com o subgrupo de cada conversa, `balcao_final.json`, `balcao_stats.json`): tema por sessão, contagens, carga, iceberg e vínculo com chamado. O filtro fiscal, o digest e o vínculo conversa↔chamado estão em `conv_pipeline.py`; a consolidação em `consolida_balcao.py`.
