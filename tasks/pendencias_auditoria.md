# Pendências para a auditoria (etapa 4b do SKILL.md)

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

## ACHADO ACIONÁVEL 2: emissão duplicada de fato (duas notas autorizadas)
Dois lotes de P2, independentes, acharam o mesmo padrão sem subgrupo:
- P2_1 (6 registros): 99195, 106825, 101775, 276621, 276683, 285051
- P2_5 (4 registros): 283387 (duas NFS-e idênticas da mesma OS, ambas AUTORIZADAS),
  240095, 239059, 283773

Não é a duplicidade que a taxonomia cobre. O subgrupo D é REJEIÇÃO por contador
dessincronizado — o portal recusa. Aqui as duas notas passam: o sistema gera duas (ou
seis) notas válidas do mesmo orçamento/OS, em geral depois de lentidão ou duplo clique,
e o cliente fica com o custo de cancelar.

É defeito de produto com consequência financeira para o cliente, não fricção de
preenchimento. Candidato a subgrupo próprio e a item do plano de ação, junto com o do
certificado.

Espelho invertido também sem subgrupo: nota consta autorizada no sistema e não existe
no portal (99291, 276633, e 100619 no mesmo fenômeno).

## A taxonomia de P2 só olha UMA direção da divergência
Três lotes de P2 relataram o mesmo: os subgrupos descrevem sempre "o fisco tem, o
sistema não". A direção inversa não tem casa:
- nota AUTORIZADA no sistema que não existe no portal/SEFAZ: 99291, 276633, 100619,
  226647, 280979, 232303
- CANCELADA no sistema, continua ativa na Receita: 224819
- manifestação do destinatário feita na SEFAZ não reflete no sistema: 229779

A consequência fiscal é diferente e pior: o cliente paga imposto de nota que o fisco não
tem, e a contabilidade não fecha. Merece subgrupo próprio, não encaixe por aproximação.

## Ambiguidade A x D em P2, documentada
O erro "Já existe uma NFSe com os parâmetros informados" aparece ~20 vezes por lote e o
atendimento quase sempre termina sem confirmar se a nota foi autorizada no portal.
Critério adotado: só vai para A com confirmação explícita; sem confirmação, D.
Se a auditoria preferir o critério oposto, ~15-20 registros por lote migram de D para A.

## ACHADO GERAL: o mecanismo de FRONTEIRA está ligado em 2 frentes de 13
Os prompts de P2, P6 e P8 não têm nenhuma cláusula FRONTEIRA — confirmado por grep pelos
próprios subagentes. Só P1 e P7 se conhecem mutuamente. E as três frentes sem cláusula
mostraram registros que deveriam atravessar:

- P8 -> P6: migração para o Portal Nacional presa em "configuração fiscal inicial"
- P2 -> frente de validação tributária: ~10 por lote abrem como "nota presa em
  processando" e terminam em PIS/COFINS, CFOP interestadual, NBS/IBS-CBS, alíquota de
  ISS, regime tributário, endereço do cliente (209745, 212179, 213049, 211903, 208547,
  222149, 221833, 222065, 221047, 213935)
- P6: sem cláusula, mas o subagente de P6_9 apontou instabilidade do SEFIN Nacional
  caindo em "webservice da prefeitura"

O mecanismo funciona (62 travessias corretas de P1 para P7 nesta rodada). O que falta é
fiação: cada frente precisa declarar as fronteiras que tem com as outras. Isso é mais
barato e mais preciso que criar subgrupos novos, porque reaproveita subgrupo existente.

## Mais um candidato a subgrupo em P2
Rejeição de SÉRIE do RPS (E97/E093, "alterar série E para 1", troca de série): ~6
registros (208075, 208245, 208689, 216991, 220929, 217635). Não é duplicidade nem
contador: é formato de série exigido pelo padrão nacional.

## Série de RPS: confirmado por 2 lotes, é o maior buraco de P2
P2_2 mandou 22 registros para "Outro" e praticamente todos são o mesmo tema. Somado ao
P2_3 (6) e ao P2_5 (série numérica obrigatória após troca de certificado, 3), são ~31
registros identificados.

Erros: E97 "série não permitida para o tipo", Error1310 "série não autorizada para este
prestador", E093 "série inválida", série "U" inválida, campo de série ausente do
cadastro, série migrada para 900, "Campo NumRps não foi informado", GOV56 "número de
correlação não autorizado" (faixa esgotada).

Não é duplicidade: o número não colide com nada. É série/faixa que a prefeitura ou o
cadastro não tem. O job de reconciliação do subgrupo D não resolve nenhum deles.
Concentração em Joinville/SC e forte correlação com a virada da reforma.

Subgrupo sugerido: "Série/faixa de RPS não autorizada ou não cadastrada
(E97/E093/1310/NumRps/GOV56)".

## LIMITE DE COLETA, não de taxonomia: o atendimento opaco
Relatado por praticamente todos os lotes de P7 e por vários de P1 e P8. Padrão:
cliente diz "deu esse erro", manda print que NÃO é transcrito, passa AnyDesk/RustDesk,
o atendente resolve na sessão remota e escreve só "autorizada". A causa fiscal existe,
mas vive na imagem e na tela remota — nunca no texto.

Volume: ~25 por lote em P7, ~22-30 em alguns lotes de P1. É o maior componente de
"Outro" em toda a etapa 2.

Duas leituras, as duas úteis para o relatório:
1. Para o relatório: é o teto de precisão da análise. Não dá para classificar o que não
   foi escrito, e inflar subgrupo por adivinhação seria pior.
2. Para a operação: é um processo que não registra a causa do que resolve. Cada um
   desses atendimentos é conhecimento que se perde — o mesmo erro volta e ninguém
   consegue contar quantas vezes.

Medição possível depois de absorver: contar "Outro" por frente e por tipo. Isso dá o
tamanho do ponto cego com número, não com impressão.

Sugestão operacional (vai no plano de ação, não na taxonomia): campo obrigatório de
"mensagem de erro" no fechamento do atendimento, ou OCR dos anexos no pipeline.

## PRECISÃO sobre o achado da FRONTEIRA
Eu escrevi "o mecanismo está ligado em 2 frentes de 13". Impreciso. O subagente de P13
mostrou que P13 tem OITO cláusulas FRONTEIRA — mas todas nomeiam subgrupos da própria
P13, para desambiguar internamente.

A afirmação correta: a FRONTEIRA é usada bastante DENTRO das frentes, e só entre P1 e P7
ENTRE frentes. O buraco é a fiação cruzada, não o mecanismo nem o hábito de usá-lo.

Isso melhora o prognóstico: quem escreveu a taxonomia já domina a ferramenta. Faltou
aplicá-la nas travessias entre frentes, que são menos óbvias de enxergar de dentro de
uma frente só.

## P10: um subgrupo fazendo o trabalho de dois
Dois lotes de P10, independentes, pediram a mesma quebra. "Correção fiscal em massa:
planilhas de NCM e arquivos SPED/Sintegra" tem 102 de 250 num lote e 51 de 178 no outro,
e mistura duas causas sem relação:
 (a) correção em massa de cadastro de ITENS (planilha de NCM, troca de CFOP no estoque)
 (b) OBRIGAÇÃO ACESSÓRIA fora do sistema (Sintegra, SPED, inventário), com arquivo
     mandado por e-mail para um analista nominal, SLA de dias e o cliente recobrando
     porque o prazo da contabilidade é dia 15
São ~30 de 51 num lote e 16 de 102 no outro. Causas, donos e correções diferentes.

Dentro de (b) há um caso que não é nem fiscal: clientes esperando **liberação comercial
do módulo SPED** por semanas. É contrato, não produto.

## Campanha de outubro: saída da ST de autopeças
Portaria SRE 34/2026. Dezenas de atendimentos com o mesmo texto ("trocar CFOP 5405->5102
e CSOSN 500->102 em todo o estoque"), sempre terminando em "não existe self-service,
mande planilha ou altere item a item". Hoje se parte entre três subgrupos conforme a
forma da pergunta. É a segunda campanha regulatória datada do ano, junto com a de
janeiro — mesmo padrão, mesma ausência de ferramenta de alteração em lote.

## "Código de tributação municipal deve ter 3 dígitos"
Muito recorrente em P10_4 (280961, 282081, 282129, 282469, 282931, 283251, 283343,
283807, 283941...). Evento de virada de padrão, não erro de cadastro individual, e o
atendimento quase sempre devolve a pergunta para a contabilidade sem resolver.

## ACHADO ACIONÁVEL 3: bug na geração do Sintegra (chamado 99959/100381)
P10_3: ~22 registros num lote só, erro IDÊNTICO:
  "Impossibilidade de envio [400] /operational/v1/ncm/batch/?ids=... BAD_REQUEST
   Could not locate appropriate constructor"
Cliente travado por semanas, com prazo de imposto em 15 e 20, e o suporte só repassa o
número do chamado. Ids: 221413, 221419, 221495, 221511, 221577, 221797, 221893, 222023,
222025, 222071, 222125, 222135, 222343, 222361, 224823, 224871, 225497.

Hoje isso cai em "Correção fiscal em massa", que descreve tratamento manual fora do
sistema. NÃO é isso: é bug de produto com chamado aberto. Um defeito único, nomeável,
com 22 clientes atrás dele e prazo legal correndo.

## SPED Fiscal: não é fricção, é produto que não existe (+ conflito comercial)
P10_3 (~14 registros) e P10_1/P10_4 (bloco de "liberação comercial"). O roteiro:
"o sistema gera SPED?" -> "ainda não" / "previsão primeiro semestre de 2026" /
"R$ 399,90 à parte, fale com o comercial". Inclui Bloco H e inventário em TXT exigidos
pela contabilidade.
Ids: 215355, 215487, 220687, 222141, 222233, 222341, 222953, 223225, 224073, 226027,
227937, 227999, 229209, 229463, 280239.

Lacuna de funcionalidade somada a conflito comercial, contada hoje como fricção fiscal.
O cliente está com obrigação legal e recebe cotação. Isso precisa sair da frente fiscal
e virar linha própria no relatório — é decisão de produto e de contrato, não de suporte.

## P13 é a frente com a taxonomia mais defasada — e por motivo DIFERENTE
P13_1 teve 77 "Outro" em 250 (31%), a maior taxa da etapa 2 inteira. Mas o subagente foi
explícito: "quase todos clusters nítidos, não ruído".

Isso distingue P13 de P1/P7/P8, onde "Outro" é atendimento opaco (print não transcrito,
sessão remota). Em P13 o problema está BEM DESCRITO no texto e a taxonomia é que não
tem onde pôr. Diagnóstico diferente, conserto diferente.

Os sete clusters, com volume:
 ~13  custo/preço de custo da peça não vem da entrada da NF (o subgrupo de estoque é
      explicitamente sobre SALDO, não custo) — já visto também no P13_2
  ~8  rastreabilidade peça <-> NF ("em qual nota esse item entrou/saiu")
  ~8  fiscal x financeiro sem vínculo (nota emitida não gera contas a receber)
  ~8  erro técnico genérico ao gerar NFS-e/NF-e a partir da OS (Error invoke
      operational API, erro 500, notas que "sumiram")
  ~6  nota avulsa/manual de saída não movimenta estoque (o saldo deveria DESCER; o
      subgrupo existente trata de cancelamento/devolução, onde o saldo VOLTA)
  ~5  conversão de unidade na entrada (caixa -> unidade/litro)
  ~4  "data de autorização" travando o fechamento da OS já com NF emitida
  ~6  agrupar várias OS numa nota única (hoje forçado num subgrupo de nota cancelada)

Conclusão para a auditoria: P13 precisa de bump de taxonomia, não de reclassificação.
É a frente onde o relatório hoje mais esconde problema real dentro de "Outro".

## LINHA DO TEMPO DOS EVENTOS DE 2026 (a seção que o relatório não tem)
Juntando o que apareceu em frentes diferentes, 2026 teve pelo menos seis eventos
datados que hoje estão diluídos como fricção recorrente:

 jan  Virada regulatória: prefeituras migram para o Portal/Emissor Nacional de NFS-e
      + campos novos da Reforma (IBS/CBS/NBS/IBPT). Domina P6 e P8 nos lotes de janeiro.
 abr  Chamado 101363 — Manifestação do Destinatário fora do ar ("Connection or outbound
      has closed"). ~30 registros num lote só de P12. Correlatos: 100285, 100773, 106463.
  ?   Chamado 99959/100381 — bug na geração do Sintegra. ~22 registros em P10_3,
      clientes travados por semanas com prazo em 15 e 20.
  ?   Quedas da plataforma Ultracar: 3 episódios distintos (conversa_38 ~68,
      conversa_62 ~166, P8_6 ~85, P8_10 quase o lote inteiro).
  ?   Instabilidade do SEFIN/Emissor Nacional (~20 em P6_9, mais blocos em P6_8).
 out  Saída da ST de autopeças (Portaria SRE 34/2026): troca em lote de CFOP 5405->5102
      e CSOSN 500->102 em todo o estoque, sem ferramenta no sistema.

As datas com "?" saem cruzando os ids com a coluna de data depois de absorver — não
chutar. Com as datas na mão, isso vira uma linha do tempo com volume por evento, que
é provavelmente a página mais útil do relatório para quem decide.

## ACHADO ACIONÁVEL 4: o botão "Calcular Tributos" apaga o que o usuário digitou
Relatado em DUAS frentes independentes:
- P7_3: "transmita SEM clicar em calcular tributos quando tem ICMS ST" — o próprio
  suporte ensina a contornar o botão (213943, 216415, 211347)
- P3_2: o botão recalcula por cima dos valores de ICMS digitados à mão
  (225773, 225835, 227113, 235475, 281721, 281737)

Também aparece em P7_1/P7_4 como discriminador do subgrupo "Espelho do fornecedor":
"calcular tributos sobrescrevendo valores".

É um defeito de produto com workaround ORAL, passado de atendente para cliente. Não
está em nenhuma base de conhecimento e não aparece como frente no relatório: está
diluído em ICMS, em espelho do fornecedor e em devolução. Mesmo perfil do achado do
certificado — causa única, sintomas espalhados por vários subgrupos.

## Possível duplicata de origem em P3_2
5+ registros do mesmo cliente/caso (diferimento de ICMS com CSOSN, valor 52,26 em vez
de 36,89): 279867, 225603, 225835, 226003, 230861, 231431. Pode ser o mesmo atendimento
reaberto várias vezes ou duplicata na coleta. Conferir na deduplicação antes de contar
como seis incidências.

## SÍNTESE: incidente não é subgrupo, é marcação transversal
Sete frentes pediram, cada uma por conta própria, um subgrupo de incidente:
  P4  "pode valer uma marcação de incidente/instabilidade transversal"
  P6  instabilidade do SEFIN Nacional sem casa
  P7  bloco de indisponibilidade poluindo o "Outro" de devolução
  P8  queda da plataforma virando "falta de visibilidade"
  P10 bug do Sintegra virando "correção fiscal em massa"
  P11 cancelamento que falha por indisponibilidade
  P12 chamado 101363 (manifestação fora do ar) inflando o subgrupo de manifestação

Criar subgrupo de incidente em cada frente seria errado: multiplicaria sete vezes o
mesmo conceito e ainda deixaria o evento fatiado entre frentes, impossível de somar.

O que o dado pede é outra coisa: uma MARCAÇÃO TRANSVERSAL de incidente, ortogonal à
frente. O registro continua em P8 ou P12 pela natureza do assunto, e ganha um campo
dizendo "isto é o incidente X, de tal data". Aí o relatório consegue as duas leituras
sem recontar nada: por frente (o que costuma doer) e por incidente (o que aconteceu).

Isso é mudança de ESTRUTURA da taxonomia, não de conteúdo. Vale levar junto com o bump,
porque é a diferença entre um relatório que mede fricção e um que também consegue
explicar o ano.

## P12 prova que a marcação de incidente funciona
P12 é a ÚNICA frente que já tem subgrupo de incidente ("Rotina de importação de XML fora
do ar"). Resultado: 48 de 250 caíram ali, limpos, com os chamados 98239, 99157/99159 e
99163 nomeados pelos próprios atendentes em ~20 conversas. O resto da frente ficou
legível.

Onde o subgrupo não existe (P6, P7, P8, P10, P11), o evento vaza para subgrupos
estruturais e contamina a leitura. Não é hipótese: é o mesmo dado, com e sem a caixa.

## Defeito pequeno e concreto: o bot Matrix reabre chamado
P5_1: 106045 e 106047 são o MESMO chamado ("acesso negado", Matrix 8027, filial
40492470000134) aberto duas vezes. Indício de que o bot abre chamado novo em vez de
anexar ao existente. Se for sistemático, infla a contagem de chamados do relatório.
Vale medir: procurar pares de chamados [Matrix] com mesma filial e mesmo título em
janela curta.

## P5 só tem subgrupo para o canal Matrix
Os subgrupos de P5 são todos rotulados "Matrix — ...", mas o mesmo fenômeno (erro
genérico sem nota identificada, how-to sem falha) chega pelo canal do analista:
98305, 98999, 107335, 100543, 106969. ~4-5 num lote de 52. Falta o espelho desses
subgrupos para o canal humano.

=========================================================================
# MEDIÇÕES DEPOIS DE ABSORVER — e uma correção da minha narrativa
=========================================================================

Estado final: 26.224 registros fiscais classificados, 0 sem classificação,
deriva de 5,4% (limite de revisão é 10%). A taxonomia NÃO quebrou.

## CORREÇÃO: eu estava exagerando a fatia da migração
Durante a etapa 2 eu disse coisas como "metade da frente P8 é a virada de janeiro",
apoiado em subagentes que reportavam "90 de 98 neste lote". Eles estavam certos sobre
os lotes deles — mas os lotes seguem a ordem dos registros, que é quase cronológica.
Um lote de janeiro é quase todo janeiro.

Medido sobre a frente inteira e o ano inteiro, a concentração em janeiro é de 23% a 30%
nos subgrupos ligados à migração, não 90%. Continua sendo 2,5x a 3x a linha de base —
spike real — mas não é "o subgrupo é o evento".

Lição: relato de lote é amostra enviesada pelo recorte temporal do lote. Só vale como
pista; o número sai do cruzamento na base inteira.

## O QUE A MEDIÇÃO MOSTROU DE VERDADE (e é mais forte)
Volume fiscal por mês: jan 4.575 contra média de 2.622. Janeiro é 1,7x.
Excesso de janeiro sobre a mediana dos outros meses: ~1.950 registros.

Decomposto, o excesso NÃO é majoritariamente migração sendo atendida:

  tema                                  jan    mediana   excesso
  Conversa vazia / sem conteúdo útil   1.322      105     1.217
  Não fiscal (falso positivo)            549       94       455
  Configuração fiscal inicial            320       87       233
  Mudança de layout / re-homologação     135       32       103
  Migração para Emissor Nacional         116       20        96

**1.217 do excesso são conversas abandonadas** — 12,6x a taxa normal. Cliente abriu o
chat, esperou e saiu sem que o problema fosse sequer registrado.

A leitura correta: a virada regulatória gerou a demanda; a fila não absorveu; o rastro
mensurável são 1.217 clientes que desistiram. Isso é maior, mais específico e mais
acionável do que "a migração inflou a frente X".

## Ponto cego por frente (sem subgrupo)
  P9  27,2% (265 reg) | P13 19,5% (534) | P1 9,9% (5.128) | P7 8,3% (2.815)
  P11 7,7% | P8 3,7% | P12 2,9% | P2 2,7% | P5 2,2% | P3 1,8% | P10 1,4%
  P6  0,7% | P4 0,6%
Confirma o diagnóstico por leitura: P13 e P9 são defasagem de taxonomia; P1 e P7 são
atendimento opaco; P4, P6 e P10 têm taxonomia que serve.

=========================================================================
# RESULTADO DA AUDITORIA — 24/10/2026
=========================================================================

  chamado   n=13  erro  7,7% [1-33]  ambiguidade  0,0%  kappa 1,000
  conversa  n=48  erro 12,5% [6-25]  ambiguidade 10,4%  kappa 0,882
  TOTAL     n=61  erro 11,5% [6-22]  ambiguidade  8,2%  kappa 0,909

Dentro dos limites do SKILL (erro < 30%, kappa > 0,75). O relatório sustenta leitura
por bloco de frentes.

## Método, declarado
Os dois avaliadores receberam o MESMO prompt do classificador original (conferido: 18
rótulos para chamado, 22 para conversa, nenhum fora da taxonomia) MAIS os quatro
critérios de desempate que eu fui acrescentando durante a etapa 1. Isso torna o teste
pareado: mede execução, não aderência à taxonomia pura.

Ressalva que não consigo eliminar: os critérios entraram ao longo da etapa 1, então os
lotes iniciais não tiveram todos os quatro. A amostra é aleatória na janela inteira e
mistura registros classificados com e sem eles. O efeito tende a INFLAR o erro medido,
não a escondê-lo.

## Os 5 pares trocados, e o que eles confirmam
  Cancelamento/exclusão          -> Rejeição/erro de validação
  Particularidade municipal      -> Acompanhamento de chamado já aberto
  Configuração assistida         -> Cadastro/config fiscal
  Cadastro/config fiscal         -> Rejeição/erro de validação
  Nota travada em processamento  -> Instabilidade geral / lentidão do sistema

Duas observações:
1. Duas das cinco trocas terminam em "Rejeição/erro de validação" — o balde genérico
   atraindo casos que tinham categoria específica. Mesmo padrão que os subagentes
   relataram ao pedir o critério 1.
2. A troca "Nota travada -> Instabilidade geral" é a terceira evidência independente
   do mesmo buraco: não há onde pôr indisponibilidade, e ela se disfarça de problema
   estrutural. Agora confirmada por avaliador cego, não só por quem classificou.

## Ambiguidade 0% em chamado, 10,4% em conversa
Faz sentido e vale para o relatório: chamado tem template, campos e título estruturado;
conversa é texto livre com transferência de fila no meio. A fronteira da taxonomia é
mais difícil de aplicar onde o registro é mais pobre. É a mesma causa do "atendimento
opaco" — o limite não é a taxonomia, é o que o canal registra.
