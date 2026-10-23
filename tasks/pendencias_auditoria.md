# Pendências da auditoria — rodada de 23/10/2026

Escrito durante a classificação, lote a lote, a partir do que os subagentes relataram.
O scratchpad da sessão é temporário, por isso isto vive aqui.

## Fronteira P1 -> P7 não atravessada
Registros com erro de CFOP/CST em nota de DEVOLUÇÃO/RETORNO que deveriam ter ido para o
subgrupo de P7 ('CFOP, CST/CSOSN e regime tributário incompatíveis') e foram para "Outro",
porque meu briefing dizia "use somente os nomes da lista" e a string de P7 aparece só no
texto da cláusula FRONTEIRA, não na lista formal.
- lote_sub_P1_5: 210623, 213257
- lote_sub_P1_2: 286283, 287779, 289557
Briefing corrigido a partir do lote P1_8.

## Lacuna de taxonomia: rejeição 506
"Data de Saída menor que a Data de Emissão" e variações de data/hora de emissão são
massivas em P1 e não têm subgrupo próprio. Foram mapeadas para "Série/numeração de RPS e
habilitação/configuração do emissor", único item que cita validação de data de emissão.
~35 registros só no lote P1_2. Candidato a subgrupo novo num bump de taxonomia.

## SINTEGRA
Ver tasks/todo.md: registros que citam SINTEGRA foram rotulados antes do critério 3.
Menção não é assunto — conferir antes de concluir que há erro.

## Dois episódios de indisponibilidade
Lote conversa_38 (68 registros) e conversa_62 (166). Isolar as datas e reportar como
evento, não diluído na frente de instabilidade.

## Fronteira P1 -> P7 (continuação dos ids)
- lote_sub_P1_6: 216121, 216479
- lote_sub_P1_3: 290979, 292405, 277449
Total conhecido: 10 registros, nos lotes P1 de 1 a 6. A partir do P1_9 o briefing
nomeia a string de P7 e manda atravessar, então os lotes 9 em diante não têm o problema.
Os lotes 7 e 8 foram lançados antes da correção completa.

## Convenções fechadas a partir do P1_9 (conferir se os lotes 1-8 batem)
- cluster de datas (saída < emissão) -> 'Série/numeração de RPS e habilitação/config do emissor'
- IBPT / carga tributária aproximada / totTrib -> 'Falha de schema XML na geração'
- devolução: só CFOP/CST atravessa para P7; imposto/tag -> subgrupo de P1 pela mensagem;
  IE/endereço do tomador -> cadastro do destinatário
- lote_sub_P1_7: ~16 registros, entre eles 217463, 218169, 218373, 219491, 220233,
  220619, 220667, 220735

Total identificado: ~26 registros nos lotes P1 de 1 a 7.

DECISÃO: não reprocessar os lotes. São ~26 de 16.580 (0,16%), e somados a P7 (~1.500
registros) dariam +1,7% — não muda nenhuma conclusão do relatório. Estão identificados
por id e podem ser corrigidos à mão na auditoria, que custa quase nada. Reprocessar 8
lotes custaria 8 execuções de subagente para mexer numa casa decimal.

## Segunda lacuna de taxonomia: valores do item/nota
Padrão recorrente sem subgrupo em P1: item da nota com valor 0,00 recusado
(227437, 227495, 227897, 229005) e divergência valor x quantidade em NFS-e (228491).
Candidato a subgrupo "valores do item/nota inconsistentes" num bump de taxonomia,
junto com o cluster de datas.

## Medição da fronteira P1->P7 (em vez de estimativa)
Contados os registros em "Outro" cujo texto tem sinal de devolução/garantia/remessa
E de CFOP/CST, lote a lote:
  P1_1 0 | P1_2 3 | P1_3 3 | P1_4 0 | P1_5 2 | P1_6 2 | P1_7 15 | P1_8 0
  total: 25 candidatos
Os lotes 8, 10 e 11, já com o briefing corrigido, atravessaram 26 para P7 corretamente.
Os 61 "Outro" do P1_4 não têm nenhum candidato — são conversas sem dado diagnóstico,
como o subagente relatou.
Confirma a decisão de não reprocessar: 25 registros, 0,15% do total.

## CORREÇÃO da medição anterior
A primeira medição olhou só os registros em "Outro" — e um subagente apontou o buraco:
um caso de devolução pode ter ido para o subgrupo de CFOP/CST de P1, não para "Outro".
Medido de novo, agora nos dois lugares, nos lotes 1-7 (briefing antigo):
  60 em 'CFOP/CST incompatíveis...' (P1) + 45 em "Outro", com sinal de devolução
  atravessaram para P7: ZERO
Nos lotes 8-11, já corrigidos: 4, 11, 10 e 12 atravessaram.

Mas "sinal de devolução" é proxy fraco: a palavra pode aparecer de passagem. O P1_11,
já corrigido, tem 26 em P1-CFOP com o sinal E 12 atravessados — ou seja, o subagente
julgou que em 26 casos o documento não era devolução. Então o número de registros
realmente mal classificados nos lotes 1-7 está entre ~30 e ~65, por extrapolação da
taxa de atravessamento dos lotes corrigidos (~9/lote), não por contagem direta.

Efeito estimado: P7 subestimada em 2 a 4%. Não reordena frentes.

DECISÃO REVISTA: seguir sem reprocessar agora, e decidir na auditoria, quando o tamanho
real de P7 estiver na mesa. Se a auditoria mostrar P7 materialmente subestimada,
reprocessar os 7 lotes custa 7 execuções. Reprocessar agora seria decidir no escuro.

## LACUNA PRINCIPAL DA TAXONOMIA: a virada regulatória de janeiro
Três subagentes de P8, independentes (lotes 1, 2 e 3), relataram a MESMA coisa sem
combinar: a migração das prefeituras para o Portal/Emissor Nacional de NFS-e e a
Reforma Tributária (IBS/CBS/NBS) são o padrão dominante e não têm subgrupo próprio.
Caem em "Configuração fiscal inicial só sai com o suporte fazendo (virada de sistema)",
que descreve implantação INDIVIDUAL de cliente. Volume: 72, 79 e 122 registros nos três
lotes — metade da frente.

Risco de leitura: o relatório vai mostrar o maior subgrupo de P8 como problema de
onboarding, quando é evento regulatório de massa. Conclusão errada para quem decide.

Candidato a subgrupo: "Migração para o emissor/Portal Nacional de NFS-e".

## Segunda lacuna convergente: fila/SLA puro
~20 registros por lote de P8 são só espera, sem assunto ("3 dias esperando", "1 hora no
telefone e caiu", "vão esperar eu cancelar o contrato?"). Vão para "sem visibilidade do
status" ou "Outro", mas a causa é capacidade de atendimento, não autonomia do cliente.

## Outras lacunas relatadas em P8
- Correção mensal do arquivo SINTEGRA feita à mão pelo suporte (~9/lote)
- NBS item a item sem poder salvar no cadastro (fronteira ambígua entre 2 subgrupos)
- Dependência de integradora/prefeitura sem previsão
- Atrito de AnyDesk/RustDesk: custo de atendimento alto e invisível na taxonomia
- Subgrupo "Certificados, tokens e credenciais" quase vazio por sobreposição, não por
  falta de demanda

## SEGUNDA DISTORÇÃO: quedas de plataforma viram "falta de visibilidade"
P8_6: ~85-90 registros (35% do lote, ids 214295-215007) são uma queda generalizada
("sistema fora do ar", "orçamento não carrega", "previsão de retorno?"). Couberam em
"Cliente sem visibilidade do status do chamado e da origem da falha" só pela ponta da
descrição que fala em "não sabem se o erro é do Ultracar ou da SEFAZ". Inflou esse
subgrupo para 116 de 250 e mistura duas dores: "status do meu chamado" e "o sistema
caiu agora e ninguém me avisa".

Somando com as conversas: lote conversa_38 (68 registros), conversa_62 (166) e este
(~85-90). Três episódios distintos, 300+ atendimentos.

## Leitura que está se formando para o relatório
Dois eventos de 2026 — a virada regulatória de janeiro e as quedas de plataforma —
respondem por uma fatia grande do volume e estão diluídos dentro de frentes que
descrevem fricção estrutural recorrente. Reportados como fricção, levam a decisão
errada (investir em autonomia de implantação, em visibilidade de chamado). Reportados
como evento, mostram o que de fato aconteceu no ano.
Isolar os dois e reportá-los à parte é provavelmente a decisão mais importante do
relatório V2.

## TERCEIRA LACUNA CONVERGENTE: a taxonomia só olha a SAÍDA
Cinco lotes de P8 (1, 4, 5, 7, 8) relataram a mesma ausência: não existe subgrupo para
documento de ENTRADA. Os 9 subgrupos de P8 falam de emissão, configuração ou relatório.
Ficam sem casa: frete em NF separada e rateio nas peças, nota de entrada de serviço que
duplica no financeiro, CFOP de entrada para comodato, crédito de entrada, manifestação
do destinatário, CT-e de frete, XML do fornecedor, dar entrada em NFS-e recebida.
É o maior motivo de "Outro" em vários lotes.

## Achado operacional: pico do último dia do mês
P8_8: ~17 registros de instabilidade de SEFAZ/prefeitura concentrados no último dia do
mês. Não é lacuna de taxonomia, é padrão de carga — vale para o relatório.

## Outras ausências recorrentes (pedido de recurso, não erro)
- espelho / pré-visualização da nota antes de transmitir (5 lotes relataram)
- emissão em lote / faturar vários orçamentos juntos
- duplicar/clonar nota

## CORREÇÃO: a migração TEM subgrupo — só não em P8
O subagente de P6_1 mostrou que P6 já tem "Migração para Emissor Nacional / Reforma
Tributária", e 92 dos 250 do lote caíram lá corretamente.

Então o defeito não é lacuna de taxonomia, é FRONTEIRA FALTANDO entre P8 e P6: o
prompt de P8 não nomeia o subgrupo de P6, então registro de migração que chega por P8
fica preso em "Configuração fiscal inicial (virada de sistema)".

Conserto certo: acrescentar cláusula FRONTEIRA no prompt de P8 apontando para o
subgrupo de P6, e mover os registros já classificados. O absorver já sabe mover frente
quando recebe subgrupo de outra — é o mesmo mecanismo da fronteira P1->P7.

Contagem de migração por lote de P8 (varia MUITO, é evento datado, não fricção difusa):
  P8_3 ~122 | P8_4 ~90 | P8_5 ~60 | P8_11 6 | P8_9 4 | P8_10 0
A medição definitiva sai cruzando subgrupo x mês na base depois de absorver — não
estimar a partir dos lotes.

## Distinguir as duas instabilidades
P6_1: os 56 de "instabilidade" são webservice MUNICIPAL (São Paulo, Guarulhos, BH 503,
GINFES, SIL20, GISS, CONAM), não queda da plataforma Ultracar. O subagente procurou e
achou só 1 menção isolada. Não confundir com os episódios de queda da Ultracar vistos
em P8_6, P8_10 e nas conversas.

## São TRÊS instabilidades distintas, não uma
A taxonomia só tem subgrupo para uma delas.
1. Webservice MUNICIPAL fora do ar — tem subgrupo em P6, funciona bem.
2. Plataforma ULTRACAR fora do ar — sem subgrupo. Aparece em P8 (lotes 6 e 10, centenas
   de registros), em P6 (4 em P6_4, 2 em P6_3) e nas conversas (lotes 38 e 62).
3. Emissor/SEFIN NACIONAL fora do ar — sem subgrupo. ~20 registros só no P6_9
   ("Connect timed out ... sefin.nfse.gov.br", "503 The service is unavailable").
   Caem em "webservice da prefeitura" por falta de opção, o que é factualmente errado:
   não é a prefeitura, é o portal federal.

## Subgrupo sem lastro: "Certificado: atualização quebrou a emissão"
Ficou com ZERO em P6_1, P6_3, P6_4 e P6_9. Os candidatos foram diagnosticados no
próprio atendimento como indisponibilidade da prefeitura. Candidato a remoção no
próximo bump, ou a descrição está errada.

## ACHADO DE PRODUTO (não de taxonomia): certificado em dois lugares
P6_5: certificado digital é 29% do lote (72 de 250), espalhado em 4 subgrupos. O
subagente foi além da classificação e identificou a causa raiz comum da maioria dos
casos "não configurado": o certificado é cadastrado em Configurações > Fiscal mas
precisa ser TAMBÉM selecionado em Cadastro > Empresa > Nota Fiscal. Dois lugares.
A mensagem do sistema ainda é ambígua ("seu certificado venceu OU está desconfigurado"),
o que impede o cliente de distinguir vencimento de configuração incompleta.

Isso é acionável direto: um campo, uma mensagem de erro. Vale destaque no plano de ação,
não só como linha do relatório.

## Caso Contagem-MG
~22 chamados num lote só, todos "já normalizou?" / "tem previsão?". Município com
emissão paralisada por mais de um mês. É acompanhamento de status, não fricção técnica.
Mesmo padrão em Fortaleza-CE, Alegrete-RS, Barueri-SP.

## ACHADO ACIONÁVEL: municípios nunca homologados
P6_7: ~50 dos 84 que caíram em "Mudança de layout / re-homologação" não são mudança de
layout — são municípios que NUNCA foram homologados. O cliente emite só pelo portal da
prefeitura e o suporte pede PDF+XML para parametrizar a base, caso a caso.
Cidades nomeadas: Natal-RN, Contagem-MG, Fortaleza-CE, Vinhedo-SP, Petrolina-PE,
Itaquaquecetuba-SP, Jacarezinho-PR, Pinhais-PR, Ituverava-SP, Maringá-PR, Cuiabá-MT,
Três Pontas-MG, Vitória da Conquista-BA, Canaã dos Carajás-PA, Indaial-SC, Olinda-PE.

Vira backlog de homologação com nome e sobrenome, não "melhorar cobertura municipal".

## Incidente "País deve ser informado"
~10 chamados simultâneos em várias cidades (chamados 101275/101283/101289). Campo novo
exigido pelas prefeituras de uma vez. Incidente datado, hoje diluído em "mudança de
layout".

## O cluster de datas aparece em DUAS frentes
"Rejeição: Data de Saída menor que a Data de Emissão" foi relatado em P1 (lotes 1 e 2,
~80 registros) e agora em P7_1 (4 atendimentos dominados + ~8 como erro secundário).
Não tem subgrupo em nenhuma das duas.

Detalhe acionável: o suporte tem workaround conhecido (apagar a data de entrada; pôr
data/hora de emissão = agora + 2 min) que o cliente não conhece. É candidato a item de
base de conhecimento, não só a subgrupo de taxonomia.

## Rejeição 938 em nota de garantia
P7_1: 5+ registros quase idênticos (290843, 290929, 291053, 291239, 291307). Em 291307
a correção real foi o flag "Consumidor final = sim" — ou seja, não é falta de orientação
fiscal, é configuração da nota. Bloco homogêneo, candidato a subgrupo.
