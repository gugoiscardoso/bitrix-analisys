# Análise de Chamados Fiscais — Suporte Ultracar/Portocar

**Fonte:** Bitrix24, grupo 139 (Chamados Ultracar e Portocar) + conversas de Open Lines
**Período:** 2026-05-01 a 2026-08-04
**Exports:** `bitrix_export_139_20260804_200226.json` (1.227 chamados) · `conversations_export_20260805_134927.xlsx` (13.282 conversas / 379 mil mensagens)
**Planilha detalhada:** `chamados_fiscais_2026-08-04.xlsx` · **Navegador:** `chamados_fiscais_2026-08-04.html`
**Versão:** consolidada (v2) — 2026-08-05

## Como esta versão foi construída (confiabilidade)

1. Filtro fiscal por ~40 termos → **522 de 1.227 chamados (43%)**.
2. A classificação inicial por regras foi **auditada em amostra de 30 (20% de erro)** e por isso descartada como fonte final.
3. **Todos os 522 foram reclassificados por leitura completa (LLM)** da descrição, em 6 lotes com taxonomia fechada de 17 categorias (72% de concordância com a versão por regras — o ranking mudou em pontos relevantes).
4. Os 78 sem causa na descrição foram **cruzados com as conversas de Open Lines** (telefone/e-mail/nome/CNPJ + janela de data): 22 casaram, **17 tiveram a causa recuperada do chat**.
5. Comentários de tarefa do Bitrix: verificados via API, **vazios em 100% dos chamados** — não são fonte.

Resultado: **461 chamados (88%) com causa classificada** e 61 (12%) genuinamente sem diagnóstico registrado.

## Ranking final de dores (classificação v2)

| # | Dor | Qtde | % | Em aberto | Mediana resolução | Σ dias tratativa | Clientes |
|---|---|---|---|---|---|---|---|
| 1 | Rejeição/erro de validação (schema XML, E0xxx, tags, campos, IE) | 80 | 15% | 12 | 14 d | 1.097 | 73 |
| 2 | Status dessincronizado sistema × prefeitura/SEFAZ | 51 | 10% | 12 | 8 d | 496 | 45 |
| 3 | PDF/DANFE/impressão (não gera, dados fora do lugar) | 42 | 8% | 10 | 15 d | 660 | 37 |
| 4 | Cadastro/config fiscal (NCM, CFOP, CST, cód. serviço, SPED, regime) | 40 | 8% | 14 | 8 d | 371 | 36 |
| 5 | Cálculo/exibição de impostos errada (PIS/COFINS/ICMS/ISS/**IBS/CBS**) | 38 | 7% | 14 | **24 d** | 605 | 32 |
| 6 | Numeração/duplicidade (pulos, RPS, DPS, inutilização) | 35 | 7% | 6 | 8 d | 319 | 30 |
| 7 | Integração financeiro/estoque/OS com a nota | 26 | 5% | 9 | 12 d | 297 | 22 |
| 8 | Nota de devolução/garantia/remessa/complemento | 24 | 5% | 2 | 14 d | 369 | 23 |
| 9 | Nota travada em "processando" sem retorno | 23 | 4% | 5 | 13 d | 316 | 22 |
| 10 | Particularidade municipal de NFS-e | 20 | 4% | 8 | 20 d | 261 | 19 |
| 11 | Certificado digital | 20 | 4% | 3 | 12 d | 240 | 19 |
| 12 | Cancelamento/exclusão de nota | 19 | 4% | 2 | 7 d | 180 | 15 |
| 13 | Relatórios fiscais divergentes | 12 | 2% | 3 | **28 d** | 240 | 11 |
| 14 | XML de compra / manifestação do destinatário | 12 | 2% | 3 | 9 d | 161 | 9 |
| 15 | Envio de nota por e-mail | 11 | 2% | 4 | 21 d | 127 | 9 |
| 16 | NFS-e interna / API interna | 8 | 2% | 1 | 5 d | 94 | 8 |
| — | Sem causa identificável | 61 | 12% | 9 | 14 d | 916 | 53 |

Mediana geral de resolução: **13 dias**. Volume: ~170 chamados fiscais/mês, estável (mai 149 · jun 199 · jul 157).

## Leituras principais

### 1. Rejeições de validação são a dor nº 1 por volume e por custo (1.097 dias de tratativa)
80 chamados, 73 clientes distintos — problema de produto, não de configuração pontual. Schema XML (E1235), códigos E0xxx, IE, campos obrigatórios, tags municipais. Quase tudo detectável **antes** da transmissão. As conversas confirmam o padrão: o suporte descobre a causa lendo a mensagem crua da SEFAZ/prefeitura e corrige config na mão (ex.: `regEspTrib` do Simples corrigido em atendimento após "atualização do governo").

### 2. O cluster "reconciliação de estado com o fisco" soma ~21%
Status dessincronizado (51) + nota travada em processando (23) + numeração/duplicidade (35, majoritariamente DPS/chave já usada na SEFAZ) = **109 chamados**. Mesma raiz técnica: o sistema não reconsulta/reconcilia o protocolo com a prefeitura/SEFAZ. Caso ilustrativo do chat: cliente com rejeição por "duplicidade de chave" causada por numeração usada **em 2011** — o suporte só descobriu consultando a integradora. Resolve-se com job de reconciliação + consulta de numeração na SEFAZ.

### 3. Impostos: menor volume do que parecia, mas o pior backlog
A releitura derrubou o grupo de 57 para 38 (o regex capturava qualquer "tribut..."). Porém é o grupo com **pior tempo de resolução entre os grandes (mediana 24 dias)** e 14 em aberto. O bloco IBS/CBS (reforma tributária) é o motor: base de cálculo com retenções, CST 515, config para Simples. Dor menor em volume, alta em custo e crescendo.

### 4. PDF/DANFE é a dor subestimada
42 chamados (8%, nº 3 do ranking) — não gera PDF, dados no lugar errado, quilometragem/informações complementares ausentes. Mediana 15 dias para resolver algo que o cliente percebe como "o sistema não me dá o documento".

### 5. Qualidade de triagem: os 12% invisíveis são um problema de processo, não de análise
Dos 61 sem causa, a grande maioria vem do canal automatizado `[Matrix]` (frase genérica, sem print/erro) — e o cruzamento provou que **a tratativa desses chamados não acontece no chat de Open Lines** (só 28% tinham conversa correspondente), ou seja, hoje não há NENHUM registro textual da causa. Exigir a mensagem de erro/print na abertura Matrix é pré-requisito para enxergar esse quarto do problema.

### 6. Todas as dores são de produto
Nenhum grupo tem concentração relevante por cliente (máx. ~1,2 chamado/cliente; maior cliente = 7 chamados). Consertar produto/processo, não configuração de clientes específicos.

## Recomendações priorizadas (impacto × esforço, com custo em dias de suporte)

1. **Pré-validação da nota antes da transmissão** com mensagens acionáveis — ataca nº 1 (80 chamados/1.097 dias) e parte dos sem causa. Inclui validar campos municipais obrigatórios (NBS, cTribMun, UF de consumo, regEspTrib) por município/regime.
2. **Job de reconciliação de status + consulta de numeração na SEFAZ/prefeitura** — ataca o cluster de ~21% (109 chamados) e elimina o trabalho manual de "alterar status".
3. **Pacote IBS/CBS** (cálculo, CSTs novos, Simples) — menor volume, pior tempo de resolução, tendência de alta garantida pela reforma.
4. **Robustez de PDF/DANFE** (geração + posicionamento de dados adicionais/quilometragem) — dor nº 3, subestimada até esta análise.
5. **Triagem Matrix com evidência obrigatória** (mensagem de erro/print) — destrava os 12% invisíveis e acelera a tratativa.
6. **Homologação municipal contínua + alertas de certificado** — menores, baratas, efeito imediato.

## Propostas detalhadas — subgrupos e incidências

Cada proposta foi quebrada em subvariações lendo os chamados do(s) grupo(s) correspondente(s). "Ab." = ainda em aberto; "Σd" = soma de dias de tratativa dos concluídos (proxy de custo de suporte); "Última" = data do chamado mais recente do subgrupo (ref. 04/08/2026): 🔴 últimos 30 dias (dor ativa) · 🟠 30–60 dias · 🟡 +60 dias (possivelmente já corrigido). As 6 propostas cobrem **370 dos 522 chamados fiscais (71%)**.


> **Atualização de 05/08 — a ordem interna da P1 mudou.** As 1.409 conversas de chat dessa frente foram classificadas por subgrupo e inverteram o ranking: **CFOP/CST incompatíveis**, que aparecia em 6º com 7 chamados, é o maior com **411 conversas** (iceberg 59×), enquanto Regime/alíquota de ISSQN cai de 1º para 6º. A tabela abaixo mantém a contagem de chamados; para a ordem de implementação, use a coluna Conversas da planilha executiva. Detalhes em `analise_balcao_conversas_2026-08-05.md`.

### P1 — Pré-validação da nota antes da transmissão (80 chamados · 12 ab. · Σ 1.097 d)

Cada subgrupo equivale a um validador implementável de forma independente, na ordem de retorno:

| Validador | Qtde | Ab. | Σd | Última |
|---|---|---|---|---|
| Regime/alíquota de ISSQN inválidos (regEspTrib, E0175/E0178, tributação de serviço) | 15 | 1 | 181 | 🔴 03/08 |
| Códigos fiscais do item/serviço inexistentes ou faltantes (NCM, código de barras, cód. tributação municipal/nacional, UF de consumo) | 13 | 2 | 201 | 🔴 03/08 |
| Cadastro do destinatário/tomador incompleto ou inválido (IE, CEP, endereço, documento, razão social) | 13 | 4 | 132 | 🔴 04/08 |
| Série/numeração de RPS e habilitação/configuração do emissor (série numérica, nDPS, credenciamento, padrão municipal, ambiente) | 12 | 4 | 81 | 🔴 28/07 |
| Falha de schema XML na geração (caracteres/conteúdo inválido em tags, informações complementares, tags fora de ordem) | 12 | 1 | 178 | 🔴 09/07 |
| CFOP/CST incompatíveis com a operação ou regime (devolução, idDest, grupos de imposto) | 7 | 0 | 166 | 🟠 01/07 |
| Consistência de pagamento/fatura e campos condicionais da NF-e (troco, grupo Fatura, intermediador, transporte) | 5 | 0 | 83 | 🟠 30/06 |
| Outros/heterogêneos | 3 | 0 | 75 | 🟠 12/06 |

### P2 — Job de reconciliação com SEFAZ/prefeituras (109 chamados · 23 ab. · Σ 1.131 d)

Funções independentes do job, por incidência. As 3 primeiras (70 chamados) usam a mesma mecânica — consulta de protocolo/chave + atualização de status — e formam a fase 1:

| Função | Qtde | Ab. | Σd | Última |
|---|---|---|---|---|
| Nota autorizada no portal continua em digitação/processando no sistema | 26 | 6 | 159 | 🔴 30/07 |
| Nota presa em processando/transmitindo sem retorno da prefeitura | 23 | 6 | 307 | 🔴 03/08 |
| Nota cancelada na prefeitura permanece autorizada no sistema | 21 | 5 | 282 | 🔴 29/07 |
| Duplicidade de DPS/RPS/chave por contador de numeração dessincronizado (E0014/E2404) | 14 | 3 | 148 | 🔴 04/08 |
| Lacunas na sequência de numeração (números pulados sem emissão) | 11 | 3 | 102 | 🔴 21/07 |
| Nota emitida na SEFAZ não aparece no sistema | 10 | 0 | 59 | 🔴 09/07 |
| Outros/heterogêneos | 4 | 0 | 74 | 🟠 25/06 |

### P3 — Pacote de conformidade tributária (38 chamados · 14 ab. · Σ 605 d)

IBS/CBS concentra 6 dos 14 abertos da proposta — é a frente que mais cresce:

| Frente | Qtde | Ab. | Σd | Última |
|---|---|---|---|---|
| IBS/CBS — reforma tributária (base de cálculo, alíquota, CST 515, Simples Nacional) | 12 | 6 | 156 | 🔴 04/08 |
| PIS/COFINS — retenções, CST e valores zerados/divergentes | 6 | 2 | 104 | 🔴 24/07 |
| Valor líquido / base de cálculo divergente na nota | 6 | 0 | 193 | 🟠 24/06 |
| ISS/ISSQN — retenção e alíquota na NFS-e | 5 | 1 | 54 | 🔴 30/07 |
| ICMS — diferimento, destaque e devolução | 5 | 3 | 60 | 🔴 24/07 |
| Cálculo de tributos em Compras | 2 | 2 | 0 | 🔴 24/07 |
| Outros/heterogêneos | 2 | 0 | 38 | 🟠 19/06 |

### P4 — Robustez de PDF/DANFE e impressão (42 chamados · 10 ab. · Σ 660 d)

Confiabilidade + fidelidade (2 primeiras frentes) = 55% da proposta:

| Frente | Qtde | Ab. | Σd | Última |
|---|---|---|---|---|
| PDF não gera / não baixa / erro ou lentidão na geração | 12 | 1 | 187 | 🔴 24/07 |
| Valores e campos fiscais incorretos ou ausentes no PDF | 11 | 4 | 192 | 🔴 28/07 |
| Dados adicionais / informações complementares no lugar errado ou ausentes | 9 | 3 | 130 | 🔴 28/07 |
| Layout de impressão não atende necessidades do cliente (logo, 58mm, DANFE de compra) | 5 | 2 | 84 | 🟠 02/07 |
| Campos operacionais da OS ausentes (quilometragem, sinistro, data/assinatura) | 3 | 0 | 40 | 🟠 03/07 |
| Layout / paginação quebrada | 2 | 0 | 27 | 🔴 08/07 |

### P5 — Triagem com evidência obrigatória (61 chamados · 9 ab. · Σ 916 d)

90% vem do canal Matrix. O fluxo precisa de 3 mecanismos: captura obrigatória de erro+nota para falhas; bifurcação dúvida×erro; campos estruturados para alterações. Os casos de analista mostram que template sem validação de preenchimento não basta:

| Padrão de abertura | Qtde | Ab. | Σd | Última |
|---|---|---|---|---|
| Matrix — 'erro/dificuldade ao emitir' sem nenhuma evidência | 38 | 6 | 585 | 🔴 21/07 |
| Matrix — pedido de assistência/how-to sem problema definido | 8 | 1 | 155 | 🔴 03/08 |
| Analista — formulário fiscal com campos de evidência em branco | 6 | 2 | 26 | 🔴 03/08 |
| Matrix — mensagem de erro genérica citada, sem identificação da nota | 5 | 0 | 110 | 🔴 13/07 |
| Matrix — solicitação de alteração/ajuste em nota sem especificar o quê | 4 | 0 | 40 | 🔴 14/07 |

### P6 — Homologação municipal + certificado digital (40 chamados · 11 ab. · Σ 501 d)

Atenção ao prazo: **Limeira-SP torna o Emissor Nacional obrigatório em 01/09/2026** — item com data:

| Frente | Qtde | Ab. | Σd | Última |
|---|---|---|---|---|
| Instabilidade / webservice da prefeitura fora do ar | 8 | 2 | 137 | 🔴 29/07 |
| Mudança de layout / re-homologação municipal | 7 | 3 | 57 | 🔴 04/08 |
| Certificado: cliente não conclui a instalação sozinho e pede que o suporte faça | 7 | 2 | 53 | 🔴 29/07 |
| Certificado: falha no cadastro/upload do arquivo | 6 | 0 | 65 | 🔴 23/07 |
| Certificado: vencido / renovação não reconhecida pelo sistema | 4 | 1 | 45 | 🔴 24/07 |
| Migração para Emissor Nacional / Reforma Tributária | 3 | 2 | 3 | 🔴 23/07 |
| Certificado: atualização quebrou a emissão | 3 | 0 | 77 | 🟡 01/06 |
| Campo/regra municipal específica não suportada | 2 | 1 | 64 | 🔴 23/07 |
## Artefatos

- `chamados_fiscais_2026-08-04.xlsx` — 522 chamados, 1 linha cada: link Bitrix, datas, status, tempo de resolução, canal de abertura, cliente/CNPJ, `ClassificacaoFinal` + `FonteClassificacao` (descrição LLM ou chat) + classificação regex inicial para auditoria, descrição completa. Abas Resumo (com mediana de resolução e clientes distintos por grupo) e Metodologia.
- `chamados_fiscais_2026-08-04.html` — navegador offline: grupos → chamados → detalhe, busca e filtro de status (todos os 1.227 chamados, fiscais classificados).
- Dados brutos: exports JSON/XLSX em `output/`.
