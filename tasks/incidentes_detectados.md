# Surtos detectados durante a leitura de 30/10/2026

Registrados conforme os lotes reportam. Não são medição sistemática — são o que
apareceu à vista de quem leu. Vale uma varredura própria depois, por data e tema.

## Indisponibilidade (tema "Sistema inteiro fora do ar")
- lote A_019: 89 registros num lote só — o maior surto visto até agora
- lote A_023: faixa 220437–220549
- lote A_025: 222931, 222933, 222937, 222971
- lote A_027: 225197, 225213, 225235, 225297 (mesma manhã, sem confirmação do atendente)

## Defeito específico em massa — mais interessante que a indisponibilidade
Três regressões distintas na MESMA manhã, faixa 225851–226177 (lote A_028). Isso tem
cara de release ruim, e nenhum relatório atual mostra esse padrão:

1. **Erro "endereço principal" no cadastro de cliente** (~30 clientes):
   225851, 225855, 225883, 225887, 225891, 225903–225941, 225963–225969, 226005,
   226011, 226055, 226063, 226093, 226107, 226117, 226133, 226151
2. **Comissão que não salva** (chamados 100423 / 100427, ~14 clientes):
   225463, 225879, 225919, 225945, 225957, 225981, 225985, 225991, 226061, 226123,
   226139, 226175, 226283, 226335
3. **"Impossibilidade de envio / parcela já alterada o status" na baixa do financeiro**
   (chamado 100429, ~12 clientes):
   225861, 225947, 225979, 225997, 226009, 226083, 226085, 226087, 226113, 226177,
   226193, 226215

## Por que isso importa
O relatório conta fricção por categoria e por módulo, e nessas tabelas um surto de 30
clientes no mesmo defeito vira 30 linhas espalhadas em "erro de função / Cadastros".
Some com o ruído de fundo. Um eixo de "incidente" — agrupar por defeito e por dia —
mostraria o que a categoria esconde. Fica como proposta, não foi pedido.

## Mais defeitos em massa (lote A_029)
4. **Anexo de documentos no financeiro fica "rodando" e falha** (chamado 100135),
   faixa 226459–227157: 226459, 226529, 226627, 226969, 227003, 227025, 227157
5. **Etiquetas de peça no orçamento** — mesmo pedido de melhoria vindo do treinamento:
   226545, 226747, 226989

Neste lote a indisponibilidade NÃO se concentrou (226413, 226539, 227231, 227369
dispersos, e em 226869 / 227069 o atendente afirmou que o sistema estava normal).
Reforça a leitura: o que se repete nesta base não é queda, é defeito pontual atingindo
muitos clientes ao mesmo tempo.

## Defeitos em massa com chamado próprio (lote A_030)
6. **Integração Porto Seguro não retorna apólices/segurados**, quebra a abertura de
   orçamento (chamado 100681). Faixa 227841–228289, concentrado em 228159–228289:
   227841, 227983, 228029, 228043, 228061, 228159, 228161, 228167, 228171, 228173,
   228253, 228261, 228263, 228289. O cliente ACESSA o sistema normalmente — por isso
   entra como erro de função em Orçamentos & Serviços, não como queda.
7. **Replicar OS / orçamento** (chamado 100639): 227569, 227589, 228013, 228027,
   228193, 228381
8. **Gestão de Pátio não abre** (chamado 100729): 228289, 228331

Indisponibilidade real no lote, só dois casos — e um deles é um padrão, não um evento:
227713 relata que **o sistema cai todo sábado depois do meio-dia**. Vale conferir
contra a distribuição por dia da semana; se procede, é achado de infraestrutura que
nenhuma categoria do relatório mostraria.

## Lote A_036 — o mais sério até agora
9. **Emissão de boleto falha com erro de parse** (`Unexpected character encountered
   while parsing value: <`), chamado **101275**, tratado pelo suporte como "erro geral,
   prioridade máxima". Bancos Itaú e Inter. O atendente confirma ao cliente que
   TODOS os boletos seguintes falhariam enquanto durasse. 18 registros na faixa
   233999–234335: 233999, 234015, 234029, 234037, 234055, 234071, 234119, 234133,
   234139, 234155, 234171, 234177, 234201, 234221, 234233, 234237, 234243, 234335.
   Correlatos sem o número: 234005, 233789, 234087 ("não posso ficar sem faturar").

   Este é o único da lista que bloqueia FATURAMENTO do cliente. Os outros atrapalham
   a operação; este impede de receber.

10. **Placas de carreta/reboque sem dados na base** (ATD-25010/25012/25013):
    233235, 233379, 233485, 233675, 233679, 233797, 233799, 233877
11. **Impressão de etiqueta nunca sai conforme a folha** — chamado antigo fechado sem
    resolver, reaberto como 101281 e 101299: 233281, 234017, 234025, 234179

## Lote A_033 — defeitos operacionais
12. **OS não fecha: peça anexada e em estoque, sistema insiste em "aguardando entrega
    de peças"** — defeito dominante do lote, com DOIS chamados abertos para a mesma
    coisa (100951 e 100743): 230553, 230789, 230979, 231211, 231255, 231499
13. **Contas a pagar em "previsões" retorna "servidor não disponível"** (chamado
    101079, cliente diz "desde sexta-feira"): 230853, 231579
14. **Integração de placa/DETRAN não traz dados** — contorno do suporte é cadastro
    manual: 230557, 230879, 231209, 231347
15. **Emissão travada por "SEM GTIN" no código de barras do item**: 230601, 231065
16. **Todo cliente particular sai vinculado à empresa "ITRI RODOFERROVIA"** — em um
    caso o atendente negou ser erro, no outro abriu chamado: 232489, 232891

## O incidente 101109, dimensionado
Os lotes A_034 e A_035 cobrem a mesma manhã. Juntos, o cadastro de veículo quebrado
aparece em mais de 200 conversas — faixas 231895–232251 e 232139–232473, com resíduo
no dia seguinte (232531 a 232967). Sintomas: "sem permissão para cadastrar veículo"
em todos os perfis, botão desabilitado com "cliente não informado", e placas já
cadastradas sumindo do vínculo. Workaround oficial: deslogar e logar — que vários
relatam não ter resolvido de imediato.

Impacto declarado pelos clientes: sem veículo não se abre OS nem orçamento.
232455 "estou com a oficina lotada, carros novos"; 232299 "continuamos sem conseguir
abrir Ordem de Serviço".

É o maior evento isolado do ano nesta base, e nenhum relatório atual o mostraria como
um evento — ele se dissolve em duzentas linhas de "erro de função / Cadastros".

## O caso do boleto, consolidado (lotes A_036 + A_037) — chamado 101275
51 registros ao longo de TRÊS DIAS, faixa 233999–235309. Erro
`Unexpected character encountered while parsing value: <`, variantes "O servidor não
está disponível" e `Name or service not known (plugboleto.com.br:443)`.

Causa informada pelo suporte: a integradora **plugboleto** pausou a integração; bancos
(Itaú, Inter) alteraram um campo de envio.

A previsão foi se empilhando: "sem previsão" → 17/04 → 20/04 → "5 a 6 dias úteis".
Em 234583 o cliente ameaça ação de danos morais e o gerente de suporte entra na
conversa.

Por que é o pior da lista: os outros defeitos atrapalham a operação da oficina; este
impede de RECEBER. E durou dias, não horas.

## Queda real de sistema (lote A_037) — a única inequívoca até agora
47 ids praticamente contíguos na faixa **234733–234901**, mesma tarde. Sintoma:
"Falha ao realizar o login / Não foi possível autenticar o usuário", sistema lento ou
não abrindo. O suporte respondeu com comunicado padrão de indisponibilidade
("instabilidade inesperada") e depois "já se normalizou". Nenhum chamado citado.

Aqui o tema "sistema fora do ar" está CERTO — diferente dos lotes A_034 e A_035, onde
o mesmo rótulo tinha sido aplicado a um defeito de uma única tela.

## Mais dois (lote A_037)
17. **Conciliação bancária não busca / arquivo não processa** — chamados 101251 e
    101367: 234395, 234547, 234685
18. **"Connection or outbound has closed"** — chamado 101363: 234991, 235001, 235273

## Boleto, terceira leva (lote A_038) — chamados 101483 e 101461
Mais 28 ids na faixa 235363–236367: 235363, 235431, 235447, 235471, 235509, 235567,
235587, 235613, 235651, 235653, 235657, 235835, 235847, 235905, 236021, 236025,
236027, 236041, 236065, 236085, 236119, 236163, 236171, 236205, 236227, 236303,
236319, 236367.

**Somando A_036 + A_037 + A_038: cerca de 79 conversas.** O boleto é, disparado, o
maior problema do período nesta base — não por pico num dia, mas por duração.

## Outros do lote A_038
19. **Chamado 101363 — erro geral que bloqueia alterações e cadastros.** O atendente
    diz que "está afetando diversos clientes" e trata como prioridade máxima: não
    cadastra usuário, não cadastra nota, não cria conta bancária. Chamados irmãos
    101375 e 101353. Ids 235321–235749: 235321, 235325, 235337, 235339, 235347,
    235405, 235693, 235749
20. **Chamado 101251 — boletos com valor zerado travando a conciliação** (previsão
    23/04): 235921, 236147, 236201, 236279, 236215
21. **Consulta de placa traz dados errados ou de outro veículo** — cor, ano,
    combustível e modelo errados na OS, inclusive após "atualizar dados"; placas
    cadastradas durante a falha seguem sem dados: 235351, 235481, 235839, 235951
22. **Entrada manual de peça/compra** — puxa 1 unidade quando a OS tem 2, não deixa
    editar quantidade, acusa "peça vinculada a outra compra": 236095, 236247, 236285

## Boleto, quarta leva (lote A_039) — e a duração real
Mais 18 ids: 236387, 236453, 236511, 236537, 236539, 236555, 236591, 236607, 236665,
236719, 236797, 236935, 236957, 237011, 237025, 237147, 237281, 237305.

O atendimento chama de "instabilidade na geração do PDF dos boletos" e "fila de
processamento de PDF alta". **Arrasta-se por cerca de DEZ DIAS**, com três chamados em
sequência: 101275 (aberto 13/04) → 101483 → 101539 (marcado exclusivo/prioridade),
mais um ticket junto à integradora.

**Total somando A_036 + A_037 + A_038 + A_039: cerca de 97 conversas.** É o maior
evento do período nesta base por qualquer medida — volume e duração.

## Mais defeitos repetidos (lote A_039)
23. **Conciliação bancária não busca o título / título zerado** (chamado 101251,
    liberado "a partir do dia 24"): 236711, 236827, 236869, 236891; desdobramento do
    lançamento 3156-2 em 236977 e 237115 (chamado 101521)
24. **Check-list Express não gera orçamento** ("vínculo com check-list já existente")
    — o próprio atendente reproduziu na base dele: 236861, 237323
25. **"Impossibilidade de envio" ao incluir cliente novo**: 237109, 237145
26. **Pós-atualização: erro ao gerar atividade e ao mudar etiqueta na OS**, resolvido
    deslogando: 237035, 237037, 237039
27. **Entrada de nota / baixa de peça não aparece na movimentação da OS** (chamado
    101525): 236741, 236749

## Lacuna de taxonomia confirmada por vários lotes
Não existe tema para "não sabe executar a rotina no FINANCEIRO" — o tema de rotina
cobre OS, orçamento, estoque e cadastro de usuário. Os leitores vinham jogando dúvida
operacional de financeiro (plano de contas, estorno, baixa em dinheiro, parcelamento,
PIX) no tema de "não acha o lançamento ou o valor não bate". É consistente entre
lotes, mas infla esse tema com how-to. Candidato a tema novo na próxima versão da
taxonomia.

## Surto de NFS-e (lote A_041) — 40 conversas num dia
Emissão de nota de serviço retorna "Não foi possível finalizar a requisição" ou a nota
fica presa em "Em processamento" por 20+ minutos. Em 239225 a nota é autorizada no
site da prefeitura e continua "em processamento" no Ultracar; uma filial do mesmo
grupo emitia normalmente.

Atendimento: sem previsão, "prioridade máxima", workaround = emitir pelo portal da
prefeitura. Normalização anunciada em etapas (14:00 → 14:30 → 15:00 → liberado 16:00
com lentidão residual). **Nenhum chamado citado** — um evento desse tamanho sem
número de chamado é, por si, um achado de processo.

Faixa 238771–239819, 40 ids: 238771, 238825, 238855, 238871, 238889, 238917, 238959,
238965, 239035, 239037, 239095, 239113, 239127, 239135, 239151, 239155, 239193,
239225, 239235, 239249, 239289, 239297, 239307, 239315, 239317, 239323, 239371,
239407, 239443, 239477, 239481, 239503, 239547, 239569, 239577, 239589, 239607,
239743, 239801, 239819.

## Achado de processo: chamados duplicados para o mesmo defeito
O defeito "não consegue excluir agendamento" (fica em "removendo" infinito) recebeu
DOIS números diferentes do suporte, para CNPJs distintos: **101721** em 238981 e
239079, e **101583** em 239769. O 101583 também já designava outra coisa (entrega de
insumo em lote).

Ou seja: o mesmo bug vira dois chamados, e um número de chamado cobre dois bugs. Isso
corrompe qualquer contagem por chamado — inclusive a que alguém faria para priorizar
desenvolvimento.

## Mais dois (lote A_041)
28. **Entrega de insumo em lote falha** (chamado 101583, aberto 27/04, sem prazo) —
    só vai 1 ou 2 insumos por vez: 238831, 238859, 239751
29. **Relatório de movimentação diária não filtra por dia** (chamado 101561, aberto há
    uma semana) — trava o fechamento e as planilhas dos mecânicos: 239027, 239763

## Defeitos de outubro (lote A_042) — os mais recentes da série
30. **Cadastro de veículo salva mas não traz marca, modelo, ano, cor e combustível
    da placa.** Arrasta-se "desde sexta" / "desde o dia 9" em pelo menos três oficinas.
    Chamados 107443, 107121, 107151 (um resolvido cadastrando a cor como "FANTASIA"),
    mais ATD-33267 na integradora: 293093, 293113, 293173, 293393, 293443, 293465,
    293505, 293537; pedidos de cadastro manual no mesmo poço: 240133, 292963, 293437,
    293571
31. **Importação de orçamentos do Cilia/Soma falha após a atualização do Cilia** —
    "Erro interno do servidor", "falha ao consultar o estoque", token/endpoint da
    versão nova. Chamado 107283: 293165, 293231, 293241, 293247, 293299, 293317,
    293521, 293719
32. **Curva ABC não lista por produtos, só por clientes** — mesmo cliente reabrindo
    três vezes sem solução: 293385, 293479, 293583
33. **Boleto Sicredi travado por falta de acesso ao portal do desenvolvedor**:
    293087, 293181, 293399, 293533, 293703
34. **Número lógico / Pix na TEF Elgin pendente há meses**: 292871, 293047, 293631,
    293633, 293687

## Segundo surto de NFS-e (lote A_040, tarde de 24/04)
Não emite, não transmite, não gera PDF; status preso em "PROCESSANDO". Em 238337 o
cliente relata alterações de nota que não foram salvas, com prejuízo. O atendente usa
o script de comunicado e promete normalização "por volta das 17/17:45".
**Outra vez sem número de chamado.** Ids: 238337, 238581, 238595, 238599, 238621,
238625, 238643, 238715, 238719, 238733, 238747, mais os genéricos 238525, 238579,
238605 e, mais cedo, 237929 e 237981.

São agora DOIS surtos fiscais grandes (lotes A_040 e A_041), nenhum dos dois com
chamado. Se a gestão quiser contar incidentes fiscais por chamado, vai contar zero.

## Mais do lote A_040
35. **Relatórios de movimentação e de orçamento fechado não abrem** — dois chamados
    paralelos para o que parece o mesmo defeito: 101561 (237423, 237837, 238033) e
    101477 (237829, 238071), mais 238049 sem chamado
36. **Entrega de material: só um item por entrega, peças com estoque não aparecem**
    (chamado 101583): 237447, 237519, 237555, 238229, 238685
37. **Gestão de Pátio não carrega** com o resto do sistema normal (chamado 11273):
    237355, 237775 — este último em três máquinas, inclusive modo anônimo, o que
    derruba a explicação de "memória do Chrome" dada pelo atendente
38. **Integradora de placas devolve dados de outro veículo**: 238259, 238363 (mesma
    Hilux), 238163, 238451 (Creta boliviano sem placa padrão)

## Boleto Sicoob (lote A_044, fim de outubro) — sem chamado
Cinco conversas seguidas da mesma tarde: boleto não gera, e um cliente relata que os
já gerados sumiram da tela. O atendente pergunta o banco, ouve "Sicoob" e confirma
que parecia geral com esse banco, com outros clientes no mesmo problema — e mesmo
assim **nenhum chamado foi aberto**. Ids 295163, 295183, 295189, 295201, 295225.

## Padrão que atravessa todos os surtos
Dos eventos grandes catalogados aqui, os que têm chamado são os de defeito em tela
(cadastro de veículo, comissão, entrega de material). Os que NÃO têm chamado são
justamente os de integração externa: os dois surtos de NFS-e e o boleto Sicoob.

Se alguém dimensionar incidentes contando chamados, vai concluir que o fiscal e o
bancário são estáveis — quando são as duas maiores paradas do período.

## Outubro (lote A_043) — o boleto volta, e o dia do rollout
39. **Erro `IncludeBoletoAsync` na inclusão/emissão de boleto**, atingindo Sicoob,
    Itaú, Sicredi E Inter ao mesmo tempo; também "listagem de boletos vazia".
    Chamados 107519 e 107583. 26 ids na faixa 294359–295025: 294359, 294425, 294441,
    294509, 294525, 294533, 294539, 294565, 294571, 294577, 294605, 294683, 294691,
    294753, 294775, 294785, 294823, 294827, 294853, 294855, 294877, 294897, 294913,
    294947, 295021, 295025; mais 294261, com clientes finais sem conseguir pagar
    boletos vencidos.
    É o quinto episódio de boleto do período. O problema não foi resolvido em abril —
    voltou em outubro, em quatro bancos de uma vez.
40. **Integração de placas não retorna dados** — marca é obrigatória e bloqueia a
    entrada do carro. ATD-33308 e ATD-33358 na integradora: 293871, 294163, 294307,
    294549, 294555, 294583, 294587, 295111
41. **Travamento da V3 em 29/10 — chamado 107503.** 294373, 294385, 294393, 294399,
    294429, 294431, 294443, 294445, 294451, 294485, 294499, 294501. Workaround:
    deslogar/logar, CTRL+F5 ou guia anônima.
    **Vários desses ids são os mesmos que a varredura do ponto cego confirmou como
    conversas da V3 em 29/10.** Ou seja: parte do que o relatório da V3 contou como
    "fricção de rollout" é, na verdade, este incidente.
42. **PDF da nota de serviço sai como "cancelada" embora autorizada no nacional** —
    assumido pela coordenação de desenvolvimento: 294309, 294355, 295045
43. **Lançamento de múltiplas notas de compra falhando** (107505/107507): 294419, 294981

## Chamados duplicados — o padrão se confirma (lote B_002)
Além do caso já registrado (mesmo bug com dois números), o B_002 achou duplicatas
puras: **106203 / 106207 / 106213** são três chamados para o mesmo estorno de produto,
mesma filial; **106827 / 106829** são idênticos.

E defeitos com vários chamados ao longo do tempo:
- OS barrada por "existe compra pendente" com estoque cheio: 100537, 106371, 106521,
  106631, 106675, 106967 — seis chamados, o mais volumoso do lote
- Inventário preso em "Finalizando inventário": 100653, 106227, 106585 — somados aos
  13 do lote B_001, são **16 chamados para o mesmo defeito**
- Boleto `includeBoletoASync`: 106089, 106311 (reaberto), 106787, 106569, 106579
- Transferir itens de OS deixa a entrega indisponível: 100443, 100843, 100889, que
  apontam o chamado anterior 91915 — o defeito atravessa numeração antiga

## Sinal que olha para frente (lote C_003, fim de outubro)
Sete dos 59 registros do último lote fiscal são sobre a virada de **01/11/2026 para o
Portal Nacional / grupo IBS-CBS**: 294871, 294911, 294957, 294961, 294975, 295019,
295229. É o assunto dominante do lote.

Não é incidente — é antecipação. A mudança acontece no dia seguinte ao fim da janela
do relatório, e os clientes já estão perguntando. Se a Ultracar não tiver material e
resposta pronta, a primeira semana de novembro repete, com volume maior, o que a
Reforma Tributária de agosto já produziu (a mensagem automática de "demanda acima do
normal" no chat é de lá).

Vale a gestão ver isso ANTES de 01/11, não no relatório do mês que vem.

## A causa raiz do boleto, enfim nomeada (lote B_003)
O erro `Unexpected character encountered while parsing value: <` é o parser JSON
recebendo HTML. Ou seja: o serviço de boleto devolve uma página de erro onde deveria
vir JSON, e o sistema estoura no parse em vez de tratar.

Isso une o que parecia ser vários defeitos:
- `Unexpected character...` — chamados 101483, 101539
- `IncludeBoletoAsync` — chamados 101623, 107519
- PDF não sai mesmo com boleto emitido e liquidado — 107157, 107397, 101275
- listagem de boletos vazia / "servidor indisponível" — 101277, 107559, 107519

São **nove chamados distintos** para o que o próprio padrão de erro sugere ser um
problema só, atravessando abril e outubro. Nenhum deles aponta para outro.

## Outros defeitos com vários chamados (lote B_003)
- **"No matching color for description" na consulta de placa** — a cor do veículo não
  existe no de-para e o cadastro inteiro falha: 107151 (FANTASIA), 101599 (GRENA).
  Relacionados: 107425, 107443, 107455
- **Placa retorna o veículo ERRADO** — 101181 (vem Hilux, é Corolla) e 101351 (mesmo
  par invertido); 101579 é a variante sem retorno
- **Importação Cilia quebrada** — 107225, 107283, 101231, 107467, com 107457 como
  causa raiz: o Cilia mudou de versão e o endpoint da Ultracar não acompanhou
- **Entrega de material com estoque disponível** — 101201, 101385, 101715, 101153,
  107181, 101549, 101583, 107149 (estoque mostra 4,00 e a entrega oferece 1,00)
- **OS não fecha por compra pendente inexistente** — 107165, 107199, 101567, 101651,
  107263, 101339
- **Agendamento não pode ser excluído** — 101585, 101717, 101721

## Dois fechamentos (lote C_002)
44. **PDF da nota sai marcado "cancelada" com a nota autorizada** — chamado 107497,
    **14 registros**: 294251, 294281, 294283, 294289, 294295, 294337, 294343, 294345,
    294347, 294349, 294361, 294563, 294595, mais 294557 (variante: cancelada na
    Ultracar, aprovada na prefeitura). Some aos 3 já vistos no lote A_043 (294309,
    294355, 295045) — é um surto de 17, não os 3 que eu tinha registrado.
    Grave porque o PDF é o que o cliente da oficina recebe: a nota vale, mas o
    documento que chega ao consumidor diz que foi cancelada.

45. **Migração para o Emissor / Portal Nacional de 01/11** — 14 registros no C_002
    (293869, 293897, 293923, 293979, 293989, 294043, 294143, 294189, 294325, 294329,
    294389, 294591, 294625, 294645), mais 7 no C_003. **Mais de vinte conversas** nos
    últimos dias da janela sobre uma mudança que entra em vigor em 01/11.

    Em quatro casos (294093, 294111, 294327, 294789) o suporte teve de configurar na
    sessão, com XML e PDF na mão. Isso não escala: se vinte clientes perguntaram antes
    da virada, a semana seguinte traz centenas.

## Taxa de falso positivo fiscal, medida nos três lotes
C_001: 10/250 (4,0%) · C_002: 11/250 (4,4%) · C_003: 4/59 (6,8%). Média ~4,4%,
consistente com os 5,5% que eu tinha medido por outro caminho (os registros que o
classificador fiscal já havia marcado como "Não fiscal (falso positivo)").

Duas medições independentes convergindo dão confiança no número: **o campo fiscal da
base erra para mais em cerca de 5% dos casos.**

## Queda de sistema em 04/11 (lote A_003) — confirmada, sem chamado
Nove clientes distintos na mesma tarde, faixa 297527–297569: 297527, 297529, 297531,
297543, 297549, 297553, 297555, 297557, 297569.

O atendente confirma em 297527: "O sistema passou por uma instabilidade, já voltou."
Em 297557 o cliente cola a mensagem da tela: *"Um problema inesperado aconteceu!
Houve um problema na consulta de funcionalidades, contate o suporte para mais
informações."*

É queda de verdade — login e carregamento do sistema todo, não uma tela. **Nenhum
chamado citado**, mantendo o padrão: os eventos de infraestrutura e de integração
externa não geram número, só os defeitos de tela geram.

## Novembro — o que mudou depois do rollout

### Demanda espontânea pela V3 (lote A_002)
Vinte registros num único dia são clientes PEDINDO a migração: "quero migrar para a
nova versão", "habilita nosso acesso ao novo sistema", "não aparece o botão de
solicitar". Ids com pedido de liberação: 296261, 296357, 296363, 296369, 296371,
296467, 296631, 296701, 297055, 297221, 297231.

Isso inverte o sinal de 29/10. Lá a V3 aparecia como fricção de quem foi migrado;
aqui aparece como fila de quem quer entrar. Não existe tema para isso na taxonomia —
foi classificado como acesso/plano/contrato por analogia. **Candidato forte a tema
próprio**, porque é demanda comercial, não problema.

### Placa não encontrada na integradora (lote A_002) — ATD-33620
Oito clientes diferentes no mesmo dia, placas distintas, todos com "veículo não
encontrado": 296377, 296571, 296585, 296713, 296735, 296913, 296945, 297063. O
chamado ATD-33620 foi aberto para a Fraga verificar junto ao Senatran/Denatran.
É a terceira vez que a integradora de placas aparece nesta lista (ver itens 21, 30,
40) — o mesmo fornecedor falhando em abril, outubro e novembro.

### Importação Soma/Cilia ainda travada (lote A_002) — chamados 107577 e 107549
296869, 296889, 297319. Prazo informado ao cliente: dia 12. O Cilia já aparecia
quebrado no relatório de outubro (item 31), com causa raiz identificada no chamado
107457: o Cilia mudou de versão e o endpoint da Ultracar não acompanhou. Segue aberto.

### O boleto quebrou de novo em 3 e 4/11 (lote A_001) — chamados 107509 e 107559
~28 registros, faixa 294859–296117: 294859, 295009, 295025, 295087, 295099, 295163,
295183, 295189, 295201, 295257, 295277, 295291, 295293, 295303, 295319, 295345,
295389, 295391, 295453, 295469, 295501, 295597, 295665, 295715, 295745, 296001,
296039, 296117 (mais 295279, que entrou como cobrança de prazo do mesmo chamado).

Erros citados: `IncludeBoletoAsync`, "Nosso Número já incluído anteriormente para
este convênio", "object reference not set to an instance of an object" ao pedir o PDF.
O atendimento confirma **"erro geral nas bases"** e aponta a API dos bancos —
**Sicredi, Sicoob, Itaú e Santander ao mesmo tempo**.

**Este é o SEXTO episódio do boleto no período coberto** (abril, duas vezes em
outubro, Sicoob no fim de outubro, 29/10 e agora 3–4/11). Quatro bancos falhando
juntos não é falha de banco: é o lado da Ultracar, como o erro de parse já sugeria em
abril. O problema nunca foi resolvido — foi contornado seis vezes.

Se há uma coisa nesta lista para a gestão ler primeiro, é esta.

### Placa sem marca/modelo, de novo (lote A_001) — ATD-33513 e ATD-33584
295111, 295285, 295539, 295627, 295709, 296129, 296145. Campo marca obrigatório vem
vazio e sem opção, travando a entrada do carro na OS. **Quarta aparição da
integradora de placas na lista.**

### Regressões da virada de versão (lote A_001)
- **Duplicar peça não vincula mais a substituta** — regressão confirmada pelo suporte:
  294859, 295519
- **Etiqueta "Cliente final" some da OS após a atualização**, só volta criando outra
  etiqueta e deslogando — chamado 107697: 295269, 296135

---

# NOVEMBRO — a migração da NFS-e é o evento do período

## Portal Nacional, 01/11/2026 — chamado nenhum, ~200 conversas num lote só
Resolução CGSN 189/2026 e 191, obrigatória para optantes do Simples Nacional. Num
lote de 250 conversas de 03–04/11, **cerca de 200 são esse evento**. Faixa
296025–296915.

### O que os clientes recebem na tela
- **Bloqueio de ambiente**: `EM110`, `EM111`, `A31`, `P3084`, `P3090`, `L9999`, `1651`
  — *"não é permitido emitir NFSe através deste serviço na data de competência
  informada"*.
- **Rejeição de leiaute** quando o cliente tenta reconfigurar sozinho: o código de
  serviço passou a exigir **6 dígitos** (140101, não 1401) e o de tributação municipal
  **3 dígitos**. Mensagens: `cvc-pattern-valid`, `E202` (código de tributação não
  informado), `E160` (desacordo com o XML Schema), `E0178` (não informar alíquota com
  regime especial — tem de ir 0), *"IM do prestador não deve ser informado"* (precisa
  apagar a inscrição municipal do cadastro), `cIndOp` esperado (050101 para oficina).
- **A numeração reiniciou em 1** para quem migrou: 296113, 296323, 296359, 296651,
  296717, 296753, 296803, 296807. Vira dúvida recorrente "está certo sair como 1?".
  E `E0014` por pulo de DPS em 296767.
- **O próprio Portal Nacional instável**: `Status 503 The service is unavailable`
  (296115, 296133, 296733) e "a prefeitura está temporariamente indisponível" (296525).

### O gargalo real, e é de processo, não de software
**O suporte não consegue configurar sem o XML ou o PDF de uma nota já emitida no
Portal Nacional — e o cliente não tem acesso ao portal.** Depende da contabilidade.
Isso trava dezenas de atendimentos: 296093, 296235, 296535, 296647, 296661, 296663,
296677, 296737, 296791.

Em 296737 o cliente diz explicitamente que está no ping-pong: *a contabilidade diz
que é com vocês, vocês dizem que é com eles.*

Esse é o item desta lista com conserto mais barato: não é código, é conseguir o XML de
referência por um caminho que não dependa do cliente intermediar a contabilidade.

## Defeito secundário multi-cliente (lote C_002) — chamado 107691
**NF-e de devolução rejeitada por falta de documento fiscal referenciado.** A chave
tem de ir **no item**, não no cabeçalho. Ids 296027, 296107, 296119, 296127, 296159,
296179, 296299, 296617, 296649, 296761.

Atenção: a orientação divergiu entre atendentes — um tratou como instabilidade da
SEFAZ, outro abriu chamado de desenvolvimento. Dez clientes receberam explicações
diferentes para o mesmo erro.

## Paridade V2 → V3 nos chamados de novembro (lote B_001)
Dos 36 chamados do período, **22 são "pedido de campo, filtro ou regra que o sistema
não oferece"** — e o grosso é paridade: coisa que existia na V2 e não existe na V3.

Exemplo com dois clientes distintos e mesmo defeito: **relatório de Comissão por
Funcionário na V3 vem em branco**, e por movimentação nem gera. Chamados **107625**
(MAXIMA 100 AUTO PECAS) e **107707** (CARFLEX). O 107707 acrescenta que o filtro por
status da OS — Aberta, Fechada, Cancelada — existia na V2 e sumiu na V3.

Isso casa com a frente R3 da taxonomia da V3 ("lacuna de paridade com a V2"), que no
relatório de 29/10 tinha só 9% do peso. Com o rollout avançando, é a frente a vigiar.

## Qualidade do dado no Bitrix (lote B_001)
O campo "O que precisa ser Ajustado" do chamado **107623** está com o texto do
**107621** colado dentro — mesmo contato, chamados consecutivos. Quem abriu copiou e
não trocou. Não dá para saber quantos outros têm isso; apareceu porque o leitor
estranhou a descrição não bater com o título.

## Dois achados concretos e baratos de consertar (lote C_001)

### "sem gtin" em caixa baixa faz a SEFAZ rejeitar — 8 clientes
A peça importada pelo XML do fornecedor entra com código de barras inválido ou com
`sem gtin` em minúsculo. A SEFAZ rejeita (611 / cEAN inválido). A nota só passa depois
de o cliente **editar item por item no estoque** para `SEM GTIN` em maiúsculo.

Ids 295471, 295481, 295533, 295605, 295623, 295657, 295775, 295889.

É diferença de caixa alta numa string. Normalizar na importação resolve oito
atendimentos repetidos — e provavelmente muitos mais fora deste lote.

### Reforma Tributária: grupo IBS/CBS malformado — ~13 registros, chamado 107613
"Falha na validação do JSON de NFe" (NFE3:5) e "Falha no Schema XML — encontrado
`vIBSMun`/`vIBSUF`/`vPIS`, campo `pIBSMun`/`pIBSUF`/`pPIS` é esperado". O sistema
manda **valor** onde o schema espera **percentual**.

Workaround que o suporte repete: apagar tudo de IBS/CBS em todos os itens, ou clicar
em calcular tributos antes de transmitir. Ids 295143, 295177, 295247, 295263, 295385,
295407, 295481, 295583, 295607, 295757, 295893, 295991, 295997.

### Outros multi-cliente do mesmo lote
- **Devolução rejeitada por documento referenciado + ICMS-ST obrigatório** — chamados
  107689 e 107691: 295231, 295351, 295505, 295551, 295607, 295997
- **NF gerada pela OS não traz os serviços** ("não foi possível agrupar serviços") —
  chamados 107609, 107633, 107651, 107675; conversas 295101, 295445, 295503, 295603,
  295801 (a Viecar aparece três vezes)
- **Importação de compra sem "tipo de documento"**, sem o qual não há devolução nem
  XML depois — chamado 107627: 295339, 295473, 295809, 295897
- **Limite de 3 caracteres em série e código de tributação da NFS-e** — 107703,
  295683, 295835, 295837
- **PDF "CANCELADO" com nota autorizada** segue vivo (chamado 107497): 295287,
  295383, 295881, mais a dessincronia em 107705, 107737, 107749

### Lacuna de taxonomia que a V3 vai repetir
Campo da nota que a V3 não deixa mais editar — 107729 (NFC-e não permite remover o
destinatário, a V2 permitia) e 295621. Não é rejeição, não é dúvida, não é
configuração. Precisa de saída decidida antes que vire volume.

## Execução diária de 04/11, fim de tarde (lotes A_001 e C_001)

### E0014 — DPS repetida na NFS-e nacional, 4 clientes, chamado 107223
*"Conjunto de série, número, município e CNPJ já existe numa DPS anterior"*: o sistema
reenvia um número de DPS que o Portal Nacional já recebeu. Ids 297341, 297361, 297629,
297757. O 296767 do lote anterior era o mesmo erro.

O chamado 107223 foi aberto em **13/10**, antes da migração de 01/11. Em 297629 o cliente
diz que espera desde então. Ou seja, o defeito já existia, e a migração multiplicou quem
esbarra nele. Não é dúvida de numeração do tipo "está certo sair como 1?": é envio repetido.

### O Portal Nacional segue gerando volume (continuação de 01/11)
- **Bloqueio de ambiente** `A31` / `EM110` (CGSN 189/2026): 297259, 297343, 297477
- **Leiaute da Sefin Nacional** `cvc-pattern-valid` / `cvc-complex-type`: 296973,
  297287, 297453, 297669. Nenhum chamado citado.

### Releitura apagou a marcação da queda de 04/11
297543, 297553, 297555 e 297557 tinham entrado como "Sistema inteiro fora do ar" (ver
"Queda de sistema em 04/11"). As conversas continuaram, o hash mudou e elas voltaram para
a leitura **sem** a 297527, onde o atendente confirma a instabilidade. Lidas isoladas,
viraram "não sabe executar a rotina" (3) e "função dá erro" (1), no módulo Acesso e login.

Pelo critério, isso está certo: sem confirmação no próprio texto, não se marca queda. Mas
é um limite do método: **a releitura de uma conversa perde o contexto que só existia no
lote**. A queda de 04/11 conta hoje 5 conversas em vez de 9.

## Execução diária de 05/11 (lotes A_001, B_001 e C_001)

Parte dos ids abaixo já tinha sido lida em 04/11 e voltou porque a conversa cresceu
(297287, 297341, 297343, 297361, 297477, 297669). O que é novo é a segunda ocorrência
dos mesmos erros em clientes que ainda não tinham aparecido.

### Leiaute da Sefin Nacional: duas assinaturas distintas, nenhum chamado
- **`cvc-pattern-valid: Value '1401'`**, provavelmente um código de 4 dígitos onde o
  padrão aceita 3: 297287, 297407, 297977. Em 297407 o cliente já desistiu e emite
  direto no site da prefeitura.
- **`cvc-complex-type.2.4.a`**, elemento fora de ordem no XML: 297669, 297919, 297961.
  Em 297919 o erro voltou depois de ter sido corrigido com o suporte no dia anterior.

Somadas às de 04/11 (296973, 297453), são ao menos 8 conversas de erro de leiaute do
Portal Nacional **sem nenhum chamado aberto**. É defeito do XML que a Ultracar monta,
não do cliente.

### Outros multi-cliente do Portal Nacional (lote C_001)
- **E160, arquivo em desacordo com o XML Schema**: 297801, 298113
- **Erro 07455 na NFS-e**: 297603, 297833
- **Alíquota informada sem retenção de ISS para ME/EPP** (tpRetISSQN/opSimpNac):
  297409, 297431; parecido, com E0635 (convênio municipal), 297733
- **"A IM do prestador deve ser informada"**: 297391, 297743 — este cobra o chamado
  **107581**, o único citado
- **PlugNotas pede série e numeração inicial de RPS**: 297401, 297491
- **Bloqueio de ambiente** `A31` / `EM110` / `GOV130`: 297161, 297343, 297477
- **E0014** segue: 297341, 297361 (cliente com R$ 22.327,01 em notas paradas)

### Placa não encontrada, quinta aparição da integradora (lote A_001)
297791 (RTZ5I23) e 297843 (EEG4B63), placas válidas, sem veículo correspondente; o
atendente acionou a integradora nos dois. 298053 perdeu os dados do motor e a opção de
atualizar, provavelmente a mesma integração. Nenhum chamado citado. Ver ATD-33620.

### Pós-atualização no Financeiro (lote A_001)
Plano de contas: em 297899 o do fornecedor não vem mais automático no contas a pagar;
em 298051 sumiu a conta "telefonia". Parecido, não idêntico. Sem chamado.

### Demanda de migração para a V3, de novo sem tema (lote A_001)
297723 pede para adiar a migração, 297729 pergunta a previsão, 297777 pediu o acesso
sem querer, 297851 quer saber do novo layout. Foram para acesso/plano/contrato por
analogia, como em 29/10. Reforça o pedido de tema próprio.

## Segunda execução de 05/11, à tarde (janela até ~14:30)

Os nomes de lote repetem os da manhã — a fila sempre começa em `_001` — mas são 451
registros novos, coletados depois do job das 09h. Dois temas da manhã voltaram com
clientes diferentes, e isso é o sinal: não é a mesma conversa relida, é o defeito
reaparecendo.

### Consulta de placa: de três clientes pela manhã para oito à tarde
Sexta aparição da integradora, e a maior até aqui. A placa não puxa marca e modelo, não
é aceita no campo, ou uma placa válida volta como "já cadastrada":
**297791, 298197, 298215, 298299, 298343, 298369, 298381, 298581**.

Em 298581 o atendente abriu chamado com a integradora **sem número**, e o cliente diz
que outro já tinha sido aberto no dia anterior. Oito clientes, nenhum chamado
rastreável. É o candidato mais forte a incidente aberto do dia.

### A migração para a V3 está perdendo cadastro de serviço
Sete clientes, assinaturas próximas mas não idênticas: mão de obra zerada, serviço
cadastrado que não aparece no orçamento, tempo que não puxa, nomenclatura de peça
alterada sozinha, campo de código mestre e de observação da peça que desapareceram:
**298121, 298177, 298223, 298263, 298297, 298389, 298393**, mais **298481** no mesmo
padrão de campo que sumiu. Chamado para o TI em 298177, também sem número.

Isto não é dúvida de uso: é dado que existia na V2 e não chegou na V3.

### Seis clientes pedindo a versão anterior de volta
**297777, 298117, 298141, 298145, 298347, 298495** — migração sem treinamento, vários na
véspera de feriado. Classificados como acesso/plano/contrato por analogia, porque **não
existe tema para pedido de migração nem para rejeição da V3**. Terceiro dia seguido que
esta lacuna aparece; é a que mais distorce o relatório, porque esconde rejeição da V3
dentro de um balde de contrato.

### Aba "Combustível" travando nota de item que não é combustível
Rejeições "Obrigatório o preenchimento de Grupo de Tributação do ICMS monofásica sobre
combustíveis" e "CFOP de Combustivel e nao informado grupo de combustivel":
**297913, 298239, 298553, 298569**. Em dois casos o suporte resolveu **apagando todos os
campos da aba Combustível do item** — workaround, não correção. Em 298239 faltava a UF
nessa aba e a nota só mostrava "Buscando a orientação desta recusa". Nenhum chamado.

### "Falha na validação do JSON de NFe"
**298143, 298251, 298267, 298505**, na transmissão de nota de peças e de devolução.
Mesma classe de falha do boleto: um parser de JSON recebendo outra coisa. Vale conferir
se é a mesma causa — o boleto já quebrou seis vezes por isso.

### Cupom fiscal parado e orçamento zerado juntos
**298317** e **298323** com texto quase igual em clientes diferentes, e **298239** com os
dois sintomas. Cupom parado em "processando" também em 298083 e 298147 (neste o atendente
apontou SEFAZ-MG fora do ar, então pode não ser o mesmo).

### Código municipal no formato antigo, agora com cinco clientes
`cvc-pattern-valid: Value '1401' is not facet-valid`: **297977, 298225, 298371, 298391**,
variante '1200131' em **297699**. Em 298371 o cliente diz que **a ficha cadastral do
município só traz "1401"** — ou seja, o dado que o schema recusa é o que a prefeitura
fornece. Isso aponta para conversão no lado da Ultracar, não para erro de cadastro.

### "IM do prestador": a mensagem se contradiz entre clientes
Uns recebem "não deve ser informado, pois não existem informações complementares no CNC",
outros "deve ser informada": **297745, 298153, 298359, 298485**. Em 297745 resolveu-se
**removendo** a Inscrição Municipal do cadastro da empresa.

### NFC-e "fica só processando"
**298213, 298233** com assinatura idêntica; perto, **298219** (não fatura), **298285**
(erro ao imprimir depois de transmitir), **297639** e **297787** (não emite após
configurar). Nenhum código de rejeição citado em nenhum.

### Endereço do cliente, dois defeitos que se tocam (lote B_001)
- Endereço cadastrado **não sai na impressão** do relatório da V3: chamados **107803**
  (relatório administrativo) e **107787** (relatório da OS).
- **Não há campo de endereço** ao cadastrar o cliente durante a abertura da OS; ele só
  aparece depois de a OS existir: chamados **107805** e **107787**.

O 107787 é a interseção dos dois. São dois chamados cada, pouco para surto, mas o par
descreve o mesmo cadastro incompleto visto de duas telas.

### Chamados citados nesta rodada
**107581** (fiscal, prazo 11/11) cobrado em 297755, 297925 e 298485 — três clientes
cobrando o mesmo chamado. Também **107785**, **107789**, **107793**, **107795**,
**107797**, **107801**, **107809**, **106677**, **ATD-33584**.
