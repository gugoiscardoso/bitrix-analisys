# -*- coding: utf-8 -*-
"""Planos de ação por subgrupo. Chave = (proposta_key, índice do subgrupo em propostas.json)."""

ACOES = {
 # ---------------- P1 Pré-validação ----------------
 ("prop1", "Regime/alíquota de ISSQN inválidos"): [
   "Derivar regEspTrib automaticamente do regime da empresa: forçar 0 quando CRT = Simples Nacional, bloqueando valor divergente no cadastro.",
   "Validar a alíquota de ISSQN contra a faixa do município (2–5%) na tela da nota, antes de habilitar o botão Transmitir.",
   "Corrigir em massa o regEspTrib das empresas do Simples já cadastradas (script de saneamento) — hoje o suporte ajusta uma a uma por AnyDesk.",
   "Traduzir E0175/E0178/E228/1454 para mensagem em português com o campo exato e o valor esperado.",
 ],
 ("prop1", "Códigos fiscais do item/serviço"): [
   "Bloquear o cadastro de item sem NCM válido e validar o NCM contra a tabela oficial atualizada (com carga automática periódica).",
   "Tornar o GTIN opcional de forma explícita ('SEM GTIN') em vez de deixar o campo quebrar o schema.",
   "Validar cTribMun/codigoServicoNacional contra a lista administrada pelo município do prestador na montagem da nota.",
   "Exigir UF de consumo quando o CFOP for de combustíveis (5656/5665 e correlatos), com aviso na tela.",
 ],
 ("prop1", "Cadastro do destinatário/tomador"): [
   "Validar o cadastro do cliente na gravação, não só na emissão: CEP com 8 dígitos, endereço completo, CNPJ/CPF obrigatório, razão social truncada em 60 caracteres.",
   "Tornar IE e indIEDest campos dependentes: ao marcar isento, preencher indIEDest automaticamente e travar a combinação inválida.",
   "Rodar consulta de CNPJ/IE na Receita/SEFAZ no momento do cadastro e preencher os campos validados.",
   "Marcar visualmente na lista de clientes quais cadastros estão incompletos para emissão.",
 ],
 ("prop1", "Série/numeração de RPS e habilitação"): [
   "Assistente de configuração fiscal por empresa que valida série, numeração inicial, credenciamento e token antes de liberar a primeira emissão.",
   "Bloquear série não numérica para NFS-e Nacional e impedir série de NFS-e em nota de peças já no cadastro.",
   "Verificar credenciamento do emissor junto à SEFAZ/prefeitura e sinalizar 'não habilitado' antes do usuário tentar emitir.",
   "Alertar quando a data de emissão estiver fora do prazo aceito pela prefeitura.",
 ],
 ("prop1", "Falha de schema XML na geração"): [
   "Sanear automaticamente o texto livre (informações complementares/xInfComp): remover caracteres de controle, normalizar acentuação e colapsar espaços duplos antes de montar o XML.",
   "Validar o XML gerado contra o XSD localmente antes de transmitir e apontar a tag ofensora ao usuário.",
   "Corrigir a ordem/condicionalidade das tags geradas (IBSCBS, indDest, Signature) no montador.",
   "Registrar o XML rejeitado junto à nota para o suporte não precisar pedir por AnyDesk.",
 ],
 ("prop1", "CFOP/CST incompatíveis"): [
   "Sugerir CFOP automaticamente a partir do tipo de operação, UF de origem/destino e finalidade (devolução, remessa, venda).",
   "Impedir CST quando o emissor é Simples Nacional (exigir CSOSN) e vice-versa, validando contra o CRT.",
   "Exigir o grupo de ICMS-ST retido em notas de devolução que referenciam nota com ST.",
   "Validar exclusividade mútua dos campos de PIS antes do envio.",
 ],
 ("prop1", "Consistência de pagamento/fatura"): [
   "Validar na tela que a soma das formas de pagamento é igual ao total da nota, exigindo valorTroco quando exceder.",
   "Tornar o grupo Fatura obrigatório quando a condição de pagamento for a prazo.",
   "Exigir indicativo de intermediador quando a venda for marcada como não presencial/marketplace.",
   "Completar dados do transportador (CPF/CNPJ) no cadastro, com validação de formato.",
 ],
 ("prop1", "Outros/heterogêneos"): [
   "Reclassificar estes casos após a implantação da P5 (evidência obrigatória) — hoje não há informação suficiente para uma regra de validação.",
   "Instrumentar a tela de emissão para registrar automaticamente o retorno bruto da SEFAZ/prefeitura em cada tentativa.",
 ],

 # ---------------- P2 Reconciliação ----------------
 ("prop2", "Nota autorizada no portal continua"): [
   "Job periódico que varre notas em 'digitação'/'processando' com DPS/RPS/chave conhecidos, consulta o provedor e atualiza para autorizada automaticamente. NOTA: o censo mostrou que esta função é a MENOS demandada da frente (22 conversas, iceberg 1x) — já quase sempre vira chamado. Implementar depois das duas primeiras.",
   "Reconciliação sob demanda: botão 'Consultar situação na prefeitura' na tela da nota, para o cliente resolver sem abrir chamado.",
   "Vincular a nota autorizada encontrada no portal ao registro existente em vez de criar duplicata.",
   "Registrar log de reconciliação (o que mudou, quando, com base em qual protocolo) para auditoria fiscal.",
 ],
 ("prop2", "Nota presa em processando"): [
   "FASE 1 — PRIORIDADE 1 da frente (207 conversas): detectar notas paradas além de um SLA (ex.: 15 min) e re-consultar o protocolo automaticamente.",
   "Reenviar a transmissão quando não houve envio efetivo (sem PlugID/IntegrationID) e devolver a nota para 'digitação' com erro claro quando o reenvio falhar.",
   "Tratar 'Connection reset' e timeouts com retry exponencial em vez de deixar a nota em limbo.",
   "Mostrar ao usuário o estado real ('aguardando retorno da prefeitura há X min') em vez de um spinner infinito.",
 ],
 ("prop2", "Nota cancelada na prefeitura permanece"): [
   "Job consulta notas autorizadas/'em cancelamento' contra o portal e propaga o cancelamento quando confirmado. Volume moderado no chat (32 conversas) — agrupar com a função de refletir autorização, que usa a mesma mecânica.",
   "Propagar o evento de cancelamento para financeiro e relatórios, não só para o status da nota.",
   "Corrigir a função 'sincronizar com prefeitura' que hoje roda sem alterar o status.",
 ],
 ("prop2", "Duplicidade de DPS/RPS/chave"): [
   "FASE 1 — PRIORIDADE 2 da frente (184 conversas, iceberg 13x): antes de emitir, consultar o último número efetivamente autorizado na SEFAZ/prefeitura e realinhar o contador automaticamente.",
   "Tratar E0014/E2404 com auto-recuperação: incrementar e reenviar, em vez de exigir intervenção do suporte.",
   "Impedir RPS zerado ou reinício de série sem validação, especialmente após migração para a API interna.",
   "Alertar na migração de sistema/série que a numeração precisa ser conferida com a contabilidade.",
 ],
 ("prop2", "Lacunas na sequência de numeração"): [
   "Auditoria automática da sequência por empresa/série, com relatório de lacunas.",
   "Para cada lacuna, verificar na SEFAZ se o número foi emitido; se não, oferecer inutilização em um clique (NF-e).",
   "Para NFS-e (sem inutilização), orientar o realinhamento e registrar a justificativa.",
 ],
 ("prop2", "Nota emitida na SEFAZ não aparece"): [
   "Job compara a base local com as notas existentes na SEFAZ/portal por CNPJ e período, e reimporta as ausentes pela chave de acesso.",
   "Impedir que tentativa de cancelamento apague o registro local antes da confirmação do portal.",
   "Exibir as notas reimportadas em fiscal e relatórios com marcação de origem.",
 ],
 ("prop2", "Outros/heterogêneos"): [
   "Encaminhar para o diagnóstico automático do job: ao detectar nota inconsistente, classificar o sintoma e sugerir a função de reconciliação aplicável.",
 ],

 # ---------------- P3 Impostos ----------------
 ("prop3", "IBS/CBS"): [
   "Revisar o motor de base de cálculo do IBS/CBS: dedução de ISS e tratamento de retenções de PIS/COFINS conforme a norma vigente.",
   "Corrigir a leitura da alíquota municipal cadastrada (erro 'ibscbs.municipio.aliquota - Preenchimento obrigatório').",
   "Implementar CST 515 e cClassTrib com valor padrão correto por regime — para Simples Nacional, não destacar quando não é devido.",
   "Criar suíte de testes fiscais com casos por regime/UF/município, executada a cada release, dado o ritmo de mudança da reforma.",
   "Publicar comunicado e checklist de adequação para os clientes antes de cada virada de obrigatoriedade.",
 ],
 ("prop3", "PIS/COFINS"): [
   "Corrigir a montagem do tpRetPisCofins (valor inválido no schema) e cobrir com teste automatizado.",
   "Garantir que as alíquotas cadastradas sejam aplicadas nos CSTs 04/07/08/99, hoje resultando em campo vazio.",
   "Revisar arredondamento do total de COFINS (diferença de centavos na soma).",
   "Exibir PIS/COFINS retidos no PDF da NFS-e.",
   "Eliminar o paliativo 'preencher 0 nos dois campos' que o suporte ensina hoje — o sistema deve assumir zero quando não aplicável.",
 ],
 ("prop3", "Valor líquido / base de cálculo divergente"): [
   "Auditar o cálculo do valor líquido da NFS-e contra a base e as retenções (origem da rejeição E1289 do ADN).",
   "Corrigir o destaque indevido de 'Valor aproximado total de tributos' no PDF.",
   "Validar base × alíquota antes de transmitir, evitando a rejeição do ADN.",
 ],
 ("prop3", "ISS/ISSQN"): [
   "Corrigir a gravação da flag de retenção de ISS na emissão (hoje não persiste).",
   "Destacar a alíquota de ISS configurada quando o tomador está fora do município do prestador.",
   "Revisar os valores de ISSQN na impressão da nota de serviço.",
 ],
 ("prop3", "ICMS"): [
   "Corrigir o cálculo de diferimento (percentual não aplicado) e o bloqueio de conversão com CST 51 + cBenef.",
   "Garantir destaque do ICMS na nota gerada quando devido.",
   "Permitir configurar alíquota de ICMS em notas de devolução.",
 ],
 ("prop3", "Cálculo de tributos em Compras"): [
   "Corrigir a exceção de sessão ('failed to lazily initialize... Purchase.purchaseItems') no módulo de compras — é bug técnico, correção pontual.",
   "Adicionar teste de regressão no fluxo 'calcular tributos' da compra com ST preenchida.",
 ],
 ("prop3", "Outros/heterogêneos"): [
   "Corrigir a gravação retroativa da data de emissão da NFS-e, que impede o cancelamento dentro do prazo legal.",
 ],

 # ---------------- P4 PDF/DANFE ----------------
 ("prop4", "PDF não gera / não baixa"): [
   "Implementar retry com timeout e fallback na integração de geração de PDF (TecnoSpeed/PlugNotas).",
   "Gerar o PDF de forma assíncrona com notificação, em vez de travar a tela em 'gerando'.",
   "Permitir regerar o PDF a partir do XML autorizado quando a chamada ao provedor falhar.",
   "Dar mensagem clara de falha com ação ('tentar novamente' / 'baixar XML') em vez de erro genérico.",
 ],
 ("prop4", "Valores e campos fiscais incorretos ou ausentes no PDF"): [
   "Renderizar o PDF sempre a partir do XML/JSON autorizado, nunca de dados recalculados na hora da impressão (causa raiz da divergência).",
   "Adicionar teste comparando campos-chave do PDF com o XML autorizado (total, líquido, alíquotas, destinatário, chave).",
   "Corrigir casas decimais, chave de acesso/código de autenticidade ausentes e desconto incondicionado não impresso.",
 ],
 ("prop4", "Dados adicionais / informações complementares no lugar errado"): [
   "Mapear informações complementares para o campo próprio do layout, não para a discriminação do serviço.",
   "Remover truncamento do texto livre no template.",
   "Validar o mapeamento em cada layout municipal suportado.",
 ],
 ("prop4", "Layout de impressão não atende"): [
   "Backlog de customização: logo na nota, layout com menos grades, impressão 58mm, DANFE de NF de compra a partir do XML.",
   "Avaliar um editor de template simples para reduzir a fila de pedidos pontuais.",
 ],
 ("prop4", "Campos operacionais da OS ausentes"): [
   "Propagar de forma confiável quilometragem, sinistro e data/assinatura da OS para o template da nota.",
   "Tornar esses campos configuráveis por empresa (quem usa, imprime).",
 ],
 ("prop4", "Layout / paginação quebrada"): [
   "Criar testes de regressão visual do template de impressão no pipeline.",
   "Corrigir a quebra de página indevida que joga conteúdo para a segunda folha.",
 ],

 # ---------------- P5 Triagem ----------------
 ("prop5", "Matrix — 'erro/dificuldade ao emitir' sem nenhuma evidência"): [
   "Tornar obrigatório no fluxo Matrix, para queixas de falha: número/URL da nota + print ou texto do erro. Sem isso, o bot não fecha a abertura.",
   "Capturar automaticamente o último erro de transmissão daquele CNPJ e anexar ao chamado, sem depender do cliente.",
   "Detectar duplicatas na abertura (mesmo CNPJ + mesmo tema em 24h) e vincular ao chamado existente — há ao menos 4 pares duplicados no período.",
 ],
 ("prop5", "Matrix — pedido de assistência/how-to"): [
   "Bifurcar na abertura: 'é um erro' vs 'é uma dúvida de uso'. Dúvida vai para artigo/atendimento guiado, não para a fila de desenvolvimento.",
   "Oferecer artigos do help center no próprio bot antes de abrir chamado (liga com a P8).",
 ],
 ("prop5", "Analista — formulário fiscal com campos de evidência em branco"): [
   "Validar preenchimento obrigatório no template [Fiscal]/[Cadastro]: número da nota, situação e evidência. Template sem validação não resolve.",
   "Incluir taxa de preenchimento de evidência como indicador de qualidade do atendimento.",
 ],
 ("prop5", "Matrix — mensagem de erro genérica"): [
   "Quando o erro citado for genérico ('erro 500', 'não foi possível finalizar'), exigir automaticamente número da nota e horário para permitir busca no log.",
   "Correlacionar o horário informado com os logs do servidor na própria abertura do chamado.",
 ],
 ("prop5", "Matrix — solicitação de alteração/ajuste em nota sem especificar"): [
   "Formulário estruturado para pedidos de alteração: nota + campo + valor atual + valor desejado, como campos separados e obrigatórios.",
 ],

 # ---------------- P6 Municipal + Certificado ----------------
 ("prop6", "Instabilidade / webservice da prefeitura fora do ar"): [
   "Monitoramento ativo dos webservices municipais com página de status pública para os clientes.",
   "Aviso proativo na tela de emissão quando o município do cliente estiver indisponível ('prefeitura X fora do ar, tente mais tarde') — evita o chamado.",
   "Fila de reenvio automático quando o serviço voltar, sem o cliente precisar refazer a nota.",
 ],
 ("prop6", "Mudança de layout / re-homologação municipal"): [
   "Processo formal de acompanhamento de mudanças municipais junto ao provedor, com calendário de re-homologação.",
   "Comunicar clientes do município afetado antes da quebra, não depois.",
   "Municípios com histórico recente: Ribeirão Preto-SP, Senador Canedo-GO, Catanduva-SP, Serrinha-BA, Presidente Prudente-SP.",
 ],
 ("prop6", "Certificado: cliente não conclui a instalação"): [
   "Fluxo self-service de certificado com validação imediata do arquivo e da senha, e feedback claro de sucesso.",
   "Assistente passo a passo com verificação final ('certificado válido até dd/mm, empresa X') — hoje 7 clientes pediram que o suporte fizesse por eles.",
   "Artigo no help center com vídeo curto, oferecido pelo bot quando o tema for certificado.",
 ],
 ("prop6", "Certificado: falha no cadastro/upload"): [
   "Corrigir o upload do .pfx (falha ao salvar/definir) e mostrar erro específico (senha incorreta, formato inválido, certificado expirado).",
   "Eliminar o estado inconsistente de certificado cadastrado que continua exibido como 'não configurado'.",
 ],
 ("prop6", "Certificado: vencido / renovação não reconhecida"): [
   "Invalidar o cache do certificado antigo ao cadastrar o novo (causa raiz do 'vencido mesmo após renovar').",
   "Alerta proativo de vencimento em 30/15/7 dias, no sistema e por e-mail.",
 ],
 ("prop6", "Migração para Emissor Nacional"): [
   "PRAZO: Limeira-SP obrigatório em 01/09/2026 — planejar a adequação com data.",
   "Mapear todos os municípios da base com data de migração anunciada e criar um roadmap por município.",
   "Rio Grande-RS: webservice interrompido e cidade ainda não migrada — definir contorno.",
 ],
 ("prop6", "Certificado: atualização quebrou a emissão"): [
   "Revalidar automaticamente a configuração fiscal após troca de certificado, apontando o que ficou inconsistente.",
   "Observação: sem incidência desde 01/06 — confirmar com o time se já foi corrigido antes de investir.",
 ],
 ("prop6", "Campo/regra municipal específica não suportada"): [
   "Rio Verde-GO: suportar código de cancelamento (hoje só justificativa).",
   "São Sebastião-SP: tornar 'código de contribuinte' configurável no cadastro da empresa, evitando digitação repetida.",
 ],
}

# temas fora das 6 propostas originais -> P9
P9 = [
  ("Cadastro/config fiscal (NCM, CFOP, CST, cód. serviço, SPED, regime)", 40, 14, "2026-08-05", "recente", 350, [
    "Sugestão automática de CFOP por operação/UF e tabela NCM atualizada de fábrica (com carga periódica).",
    "Assistente de configuração fiscal inicial por empresa, cobrindo NFS-e, regime e códigos de serviço.",
    "Corrigir o cadastro do contador no SPED (bloqueio relatado).",
    "Atenção: com o chat, este tema soma 390 ocorrências — maior que P4. Avaliar promover a proposta própria.",
  ]),
  ("Integração financeiro/estoque/OS com a nota", 26, 9, "2026-08-04", "recente", 159, [
    "Corrigir o vínculo nota × OS/orçamento (permitir revincular sem refazer a nota).",
    "Garantir retorno de item ao estoque no cancelamento da nota.",
    "Revisar geração de crédito e forma de pagamento na NF a partir do financeiro.",
    "Corrigir OS só de peças gerando NFS de franquia.",
  ]),
  ("Cancelamento/exclusão de nota", 19, 2, "2026-08-04", "recente", 287, [
    "Tornar o cancelamento self-service dentro do prazo legal, com mensagem clara quando fora do prazo.",
    "Corrigir 'impossibilidade de envio' ao excluir nota em digitação.",
    "Explicar na tela a diferença entre excluir (digitação) e cancelar (autorizada) — fonte recorrente de dúvida no chat (287 conversas).",
  ]),
  ("Relatórios fiscais divergentes", 12, 3, "2026-08-01", "recente", 33, [
    "Auditar os relatórios fiscais contra a base de notas (fiscal × real, somatórios, filtro por CST).",
    "Corrigir o filtro de CST que retorna vazio mesmo havendo notas.",
    "Definir uma fonte única de verdade para faturamento fiscal.",
  ]),
  ("XML de compra / importação / manifestação do destinatário", 12, 3, "2026-08-04", "recente", 214, [
    "Estabilizar a importação de XML de compra (houve desativação pelo desenvolvimento no período).",
    "Corrigir o módulo 'Notas a Manifestar' que altera o valor total no lançamento financeiro.",
    "Automatizar a busca de notas emitidas contra o CNPJ do cliente (manifestação do destinatário).",
    "Atenção: 214 conversas no chat — dor maior do que os 12 chamados sugerem.",
  ]),
  ("Envio de nota por e-mail falha", 11, 4, "2026-07-27", "recente", 15, [
    "Monitorar entregabilidade (bounce, spam) e exibir o status do envio na nota.",
    "Permitir reenvio manual e edição do destinatário pelo próprio cliente.",
  ]),
  ("NFS-e interna / API interna", 8, 1, "2026-07-24", "recente", 3, [
    "Cobrir a API interna com os mesmos testes e validações do fluxo padrão (erros de DPS e schema aparecem só nela).",
  ]),
]
