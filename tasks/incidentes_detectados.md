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

## RETRATADO — "a fila de atendimento travou" não aconteceu

**Esta seção afirmava, em duas versões, que o atendimento havia desabado em 04 e 05/11.
Está errada, e a causa é um defeito de medição nosso, não da operação.**

O que eu publiquei, e o que a API diz quando perguntada direto:

| dia | publicado (via transcrições) | real (API) |
|---|---|---|
| 03/11 | 99% | 99% |
| 04/11 | 84% | **100%** (460 de 460) |
| 05/11 | 37% | **97%** (462 de 476) |

Não houve queda. O suporte atendeu praticamente tudo nos dois dias.

### A causa: o mapa de autores não é atualizado quando a conversa cresce

`enriquecer_autores.py` buscava só as sessões **ausentes** de `remetentes.json`:

```python
faltam = [s for s in todas if s not in feito]
```

Sessão já mapeada nunca era rebuscada. Como a coleta diária roda de manhã e pega o dia
corrente, uma conversa iniciada às 9h era mapeada com as 1 ou 2 mensagens que tinha
naquele instante — e as 48 seguintes ficavam **sem autor para sempre**. Na transcrição
elas viram `(sistema)`, e qualquer contagem de atendimento feita sobre elas subconta.

Exemplo medido: sessão 297419 tem **1** mensagem no mapa, rotulada "Cliente". A API tem
**50**, das quais **18 do João Brum**.

Isso explica o gradiente que eu li como queda: 03/11 bateu porque aquelas sessões já
estavam fechadas quando foram mapeadas; 04/11 errou 12 pontos; 05/11, o dia da coleta,
errou 43. **Quanto mais recente o dia, maior a subcontagem** — e eu li essa curva como
uma operação piorando.

### O que sobrevive disto

- O número de **hoje, ao vivo** (`fila_agora.py`): ele lê a API direto, não passa pela
  base, e não tem esse defeito. Quando ele diz "106 esperando", são 106.
- O aviso automático de fila cheia **existe** e aparece em milhares de conversas. O que
  não se pode concluir dele, via transcrição, é quantas foram atendidas depois.
- A observação de que "autor se perde depois da transferência" (seção seguinte) era o
  sintoma visível deste mesmo defeito. A causa não é a transferência: é o mapa velho.

### A lição, que já custou duas correções

Eu corrigi este número uma vez, em 05/11, e a correção também estava errada — porque
troquei a contagem mas não questionei a **fonte**. As duas versões liam transcrições.
Perguntar à API foi o que resolveu, e só fiz isso quando precisei do dado ao vivo para
outra coisa.

**Série que depende de um derivado precisa ser conferida contra a origem ao menos uma
vez.** Ver `tasks/lessons.md`.

## Autor da mensagem se perde depois da transferência

Encontrado ao conferir o número acima. Numa conversa transferida, as mensagens seguintes
aparecem como `(sistema)` em vez de `Atendente (Nome)` ou `Cliente`, embora sejam diálogo
humano óbvio — em 297869, "vc prefere dar continuidade pelo chat ou pelo zap?" está
marcado como sistema.

**1.197 conversas** têm três ou mais linhas `(sistema)` depois de um `picked
conversation`. É a coluna Conversa do relatório mostrando "(sistema)" onde deveria dizer
quem falou. Não afeta classificação (o texto está lá), afeta quem lê a transcrição.

## Os defeitos de massa dos três lotes de fechamento

### Leiaute da Sefin Nacional — 11 clientes, e agora com causa nomeada
297869, 297919, 297977, 298225, 298315, 298391, 298413, 298611, 298651, 298785, 298891.

A subassinatura que importa: `cvc-pattern-valid: Value '1401' is not facet-valid with
respect to pattern '[0-9]{3}' for type 'TCCodTribMun'`. **O sistema envia o código de
serviço municipal no formato antigo (1401, 1406, `14.01.01.000`, `1.2001.31.10`) num
campo que o leiaute nacional exige com três dígitos.** Em 298371 o cliente diz que a
ficha cadastral do município **só fornece "1401"** — então o dado que o schema recusa é o
que a prefeitura dá. A conversão é do lado da Ultracar. É o defeito mais acionável do
dia, e nenhum dos 11 tem chamado aberto.

Segunda subassinatura, `cvc-complex-type.2.4.a` (elemento fora de ordem no XML): 297919,
298785, 298891. Em 297919 o erro **voltou** depois de o suporte ter corrigido no dia
anterior — não foi corrigido na origem.

### Bloco IBS/CBS da Reforma — 6 clientes
"Encontrado o campo 'IBSCBS'. Campo(s) 'COFINSST, ICMSUFDest' é obrigatório": 298163,
298241, 298673; mesma família 298039 (E001), 298903, 298745, 298741 (destaque indevido
para Simples). Em 298745 o suporte já havia ajustado dias antes e o erro voltou.

### "IM do prestador" — 5 clientes, e o workaround é manual
298359, 298499 (E0120), 298805 (E0120), 298101, 298153. A mensagem se contradiz entre
clientes ("não deve ser informado" vs "deve ser informada"), e a solução repetida é
**remover a Inscrição Municipal do cadastro da empresa** — manual, cliente por cliente.

### "Falha na validação do JSON de NFe" — compra governamental
298143, 298259, 298717, 298819. O detalhe em 298259 e 298717 é
`documento[0].compraGovernamental.percentual`; em 297913, `gCompraGov` exigindo
`dhCont`/`NFref`. Mesma classe do defeito do boleto: parser de JSON recebendo outra
coisa.

### Bloqueio de ambiente — um código diferente por cliente
EM110 (298315), 1647 (298337), 2005-O (298345), E232 (298157), E999 Resolução CGSN
191/2026 (298807), E0014 (298799). Confirma o que o critério já avisava: a lista cresce, e
cada cliente vê um código distinto para o mesmo bloqueio. Em 298315 as duas assinaturas
aparecem juntas (EM110 + `cvc-pattern-valid`), e a precedência da regra 0 decidiu.

### Agrupamento de serviços sem área — 2 clientes
"Não foi possível agrupar os serviços. Os seguintes serviços estão sem área definida":
297485 e 298743. Em 297485 a cliente insiste que os itens **têm** área. Pequeno, mas é
bug de produto, não de cadastro nem da prefeitura.

### Nota presa bloqueando a própria migração — 3 clientes
"Em processamento na prefeitura e a chave de acesso ainda não foi atribuída": 107835 (3
dias), 298465, e 297931 (4 notas paradas do mês anterior, impedindo ativar o Portal
Nacional).

## Execução diária de 06/11 (lotes A_001, B_001 e C_001)

187 registros novos (114 conversas não-fiscais, 4 chamados, 69 fiscais). Nenhum defeito
novo de massa; o que aparece é continuação dos de 05/11.

### "Falha na validação do JSON de NFe" — 4 clientes, agora com IBS/CBS
298267, 298417, 299025, 299065, todos em NF-e de peças. Em 299065 o detalhe é
`ibscbs.classificacao: Preenchimento obrigatório` — o mesmo parser de JSON das entradas
de compra governamental, agora pedindo o bloco da Reforma. Nenhum dos 4 cita chamado.

### Leiaute da Sefin Nacional e E0014 seguem
`cvc-pattern-valid: Value '1401'`: 298371 (de novo), 298391, 298413. `E0014`: 298799,
298989. A migração da NFS-e para o Portal Nacional domina o lote fiscal.

### Placa que não digita nem puxa o veículo na OS — 2 clientes
298381 e 299039. Pequeno, mas mesma assinatura em clientes diferentes.

### Perguntas sobre a migração V2→V3 sem rótulo próprio
298405, 298721, 298951, 298997, 299055 ("quando vou migrar", "é obrigatório?", "não
enviaram o acesso"). Caem em acesso/plano/contrato por falta de tema; se crescer, é
candidato a rótulo na próxima revisão da taxonomia. Campos da V2 que sumiram na V3:
298263, 298347, 298495, 298703, 298939; e o chamado 107843 (campo prisma exige placa na V3).

## Execução diária de 07/11 (lotes A_001, B_001 e C_001)

472 registros novos (235 conversas não-fiscais, 29 chamados, 208 fiscais). Um defeito
novo de massa, e a placa de 06/11 explodiu.

### Integração de placas não puxa o veículo — 12 clientes
A placa não traz marca, modelo e chassi, e a opção "Atualizar dados do veículo" sumiu:
299087, 299177, 299363, 299365, 299415, 299427, 299431, 299483, 299515, 299643, mais
299039 e 299581 (cadastro automático do carro ao abrir OS). Em 06/11 eram 2. Nenhum
chamado 107xxx; há chamados abertos na integradora, ATD-33837 (299363) e ATD-33872
(299515). Classificado como erro de função, módulo Cadastros.

### Rejeição "codigoIndOp preenchido exige bloco IBS/CBS completo" — 4 clientes
299155, 299233, 299237, 299595, sem chamado. Mesma família do JSON de NF-e pedindo o
bloco da Reforma em 06/11.

### Dado do cadastro do cliente que não sai no orçamento/impressão — 3 clientes
Endereço cortado no relatório administrativo (107867), endereço que não aparece no
orçamento (107911), km que não aparece no orçamento (107923).

### Menores
- Boleto do Banco do Brasil falhando — 3 clientes: 299337, 299467, 299627.
- Chave da NF de compra não traz o fornecedor: chamado 107855 (citado em 299797), mesma
  queixa em 299495.
- A migração da NFS-e para o Portal Nacional segue dominando o lote fiscal (298923 a
  299817).

## Execução diária de 10/11 (lotes A_001, B_001 e C_001)

387 registros novos (175 conversas não-fiscais, 14 chamados, 198 fiscais), quase todos de
09/11. Nenhum defeito inédito de grande porte; o que há é a continuação da placa e do
Portal Nacional, agora com chamado aberto para os dois.

### `tpOper` / indicador de operação na NFS-e Nacional — chamado 107967, 7 registros
A nota é recusada com "Código do tipo de Operação (tpOper) não pode ser informado quando
não se tratar de compra governamental"; ao tirar o código, outro erro aparece. Com esse
texto: 107967, 299929 (cita o chamado), 300137, 300547. Variantes do mesmo campo
("preencheu tpOper/codigoIndOp, então exige o bloco IBS/CBS"): 300007, 300419, 300647.
É a rejeição `codigoIndOp` de 07/11, que agora tem chamado.

### Integração de placas segue — 8 registros, chamado 107921
A placa não puxa o veículo, ou veículo já cadastrado volta como "não cadastrado": 299881,
300015, 300061, 300275, 300373, 300497, 300557, 300609. Chamados 107921 (299881, 300373)
e 107973 (300015); ATD-33915 na integradora (300061). Em 07/11 eram 12 sem chamado 107xxx.

### `cvc-pattern-valid` no código de tributação municipal — 5 registros, sem chamado
`1401`/`14.01` recusado pelo leiaute da Sefin Nacional: 299921, 299949, 300259, 300333,
300347. O 300283 é parecido, com `07455`. Mesma assinatura de 06/11.

### Outros do Portal Nacional (lote C_001)
- E0175, regime especial de tributação do ISSQN para Simples Nacional — 4: 300137,
  300389, 300561, 300283.
- Numeração da NFS-e reiniciou em 1 depois da migração — 4: 299955, 300135, 300399,
  299989 (este com E0014).
- "Não é permitido informar alíquota" de ISS (opSimpNac = 3) — 2: 300285, 300383.
- NFS-e que não emite depois da ida para o portal, sem código legível — 299983, 300175,
  300179.

### Bloco IBS/CBS na NF-e/NFC-e
- Rejeição 225/215 de schema por causa do campo `IBSCBS` / `cMunFGIBS` — 3: 300157,
  300351, 300563.
- "Falha na validação do JSON de NFe", `fundoCombatePobreza.baseCalculo` obrigatório —
  2: 300437, 300451.

### Menores
- Quantidade e valor dos produtos zerados ao inserir itens no orçamento/OS, e kits que
  não entram — 300217, 300257, 300635, sem chamado. Pode ser o mesmo cliente em mais de
  um registro; o 300635 diz que voltou no dia seguinte ao atendimento.
- Importação do Cilia não traz veículo nem itens — chamado 107885: 299931, 299999.
- V3 exige placa na OS — 299861 (chamado 107843, motor avulso) e 300519 (chamado 108017,
  trailer novo sem placa).
- Layout do orçamento impresso mudou na V3: o "Resumo Geral" desceu e empurra a
  assinatura para outra folha — 300167, 300271, 300477, sem chamado.

### V3: pedidos de volta e perguntas sobre a migração
Seis chamados pedem algo que a V2 tinha e a V3 não tem: 107987, 108003, 108005, 108015,
108023, 108025. Perguntas sobre a migração seguem sem rótulo próprio e caem em
acesso/plano/contrato: 300111, 300149, 300203, 300255, 300359, 300381, 300605, 300685.

### Robô N1 (116 conversas novas)
Saldo financeiro que muda ou desajusta sozinho — 3 conversas, e o robô mandou todas ao
N2: `6af1e06dbb4d393cda354700`, `6af2171bbb4d393cda354801`, `6af2f1e95c0caf89646f98ac`
(vizinha: `6af2138ebb4d393cda3547e3`, saldo do Movimento de Caixa divergente). Não
apareceu no suporte humano neste lote.

## Execução diária de 11/11 (lotes A_001, B_001 e C_001)

383 registros lidos (159 conversas não-fiscais, 15 chamados, 209 fiscais), quase todos de
10/11. Dois defeitos fiscais multi-cliente que ainda não estavam nesta lista (PIS/COFINS
na NF-e de peças e o agrupamento de compras), mais a continuação do Portal Nacional, da
placa e do boleto.

### NF-e de peças recusada por PIS/COFINS — 7 clientes, sem chamado
`vPIS`, `pPIS`, `pCOFINS` obrigatórios; "PISOutr não está completo". Ids 300727, 300965,
301145, 301173, 301217, 301255, e 301099 (em nota de devolução). O atendente corrige o
preenchimento caso a caso; ninguém abriu chamado. O robô N1 viu a mesma família no mesmo
dia (ver abaixo).

### Agrupamento de compras passou a exigir CST/CSOSN de ICMS no item — 3 registros
301245, 301253, 301261, ao menos 2 clientes; um diz "em todos os agrupamentos, antes não
dava". Sem chamado. Tem cara de regressão recente.

### Nota de devolução de compra não gera — chamados 108045 e 108047
"Não foi possível finalizar a requisição" ou sem retorno: os dois chamados, mais 300909
(mesmo cliente do 108047), 300813 e 300869 (resolvidas no atendimento). 3 a 4 clientes.
Devolução/garantia/remessa foi o maior tema fiscal do lote (44 de 209).

### Portal Nacional segue — ~45 registros, chamado 108061
Entre 300649 e 301283: 29 em particularidade municipal, 9 em configuração assistida, o
resto em rejeição (`cvc-pattern-valid` '1401', `codigoIndOp`/IBSCBS, E0177, E0625, E0621,
E0904) ou numeração (E0014, numeração reiniciada). Chamado 108061 (trava de série/DPS),
com a conversa 300889 do mesmo cliente.

### Integração de placas segue — 6 registros
300721 (nenhum veículo novo aparece "desde quinta-feira passada", 7 placas, ATD-33967),
301011, 300717 (ATD-33962), 301039, 301073, 301201. Chamados do dia sobre placa: 108031
(dentro do orçamento) e 108041 (leitura por foto no Ultravision).

### Boleto não gera ou demora — 3 clientes, sem chamado
300665 (PDF não baixa), 300823 ("mais de uma hora por boleto, há 3 semanas"), 301257 e
301317 (mesma cliente, dois dias seguidos). Chamados de boleto do dia, cada um com defeito
próprio: 108059 (duplicidade na conciliação por OFX reimportado), 108065 (erro ao salvar
configuração), 108095 (não gera PDF).

### V3: busca de peça não considera o campo Observação — chamado 108035
300773, 300939 e 301153 (mesmo cliente, o último cobrando o chamado) e 300693 (outro
cliente; busca por descrição/aplicação não lista as opções, atendente confirma erro em
tratamento). Regressão V2→V3.

### Menores
- E-mail de NFS-e/NF que não sai: chamado 108101 com 301277 (há 2 meses), e 300687,
  301171, 301309 de um único cliente depois da ida para o Portal Nacional; 301005 e 301105
  de outro cliente, "desde a mudança de versão".
- EXCEPTION ao emitir NF-e — chamado 108091, com 300825 e 300991 (mesmo cliente).
- Pedidos de migração para a V3 seguem sem rótulo próprio: 300849, 300961, 301143,
  301157, 301107.

### Robô N1 (129 conversas novas, 63 fiscais)
- E0904 (`tpOper` fora de compra governamental) — 3: `6af32100907efe90201f22f0`,
  `6af3270c907efe90201f2326`, `6af3765139152e693cc442d0`. É o chamado 107967 de 10/11.
- Schema de NF-e com campo obrigatório ausente (PISOutr/COFINSOutr, IBSCBS) e "Falha na
  validação do JSON de NFe" — 8 ao todo: `6af3104c0b3dd72d0c4902b2`,
  `6af342bdc457fbc4b3872292`, `6af37ac1c457fbc4b387246e`, `6af3815ec457fbc4b3872481`,
  `6af3295cc457fbc4b387224c`, `6af364c4907efe90201f24d1`, `6af368bfc457fbc4b387237d`,
  `6af37231907efe90201f2538`.
- Não emite depois de trocar o certificado digital (o novo não fica selecionado) — 2:
  `6af2fd210b3dd72d0c4901e0`, `6af3661e907efe90201f24d2`.
- Cerca de 17 conversas sobre nota de devolução (como emitir, erro, onde encontrar) —
  mesmo tema que liderou o lote fiscal humano.

## Execução diária de 12/11 (lotes A_001, B_001 e C_001)

414 registros lidos (208 conversas não-fiscais, 16 chamados, 190 fiscais) e 175 conversas
do robô N1.

### Instabilidade da API operacional na tarde de 11/11 — ~36 conversas humanas, sem chamado
Erros `Error invoke operational API(PartRestService), status response: unknown`,
`400 BAD_REQUEST` e `500 INTERNAL_SERVER_ERROR`, entre os ids 301819 e 301995. Os
fabricantes sumiram (não dava para cadastrar peça nem inserir peça digitada) e falharam
importação de compra, montagem de orçamento e emissão de nota. O suporte respondeu com o
comunicado "breve momento de instabilidade, já retornou ao normal". Nenhum número de
chamado aparece. Aparentemente um cliente por conversa.
- Não-fiscal, função com erro (9): 301829, 301843, 301853, 301895, 301859, 301883, 301941,
  301995, 301869.
- Não-fiscal, fora do ar (13): 301821, 301839, 301863, 301873, 301897, 301901, 301905,
  301909, 301915, 301923, 301931, 301969, 301981.
- Fiscal, como "NFS-e interna / API interna" (13): 301819, 301831, 301845, 301847, 301857,
  301861, 301889, 301891 (erro literal); 301867, 301881, 301913, 301943 (confirmado pelo
  atendente); 301837 (INTERNAL_SERVER_ERROR).
- Prováveis, erro só em anexo, ficaram como "Sem causa identificável": 301825, 301835,
  301871, 301875, 301919.
- Sequela num cliente: 301827 e 302035 — depois do incidente parou de conseguir arrastar
  XML para a importação de compra; o atendente abriu chamado, número não aparece.
- O mesmo incidente bateu no robô N1: `6af4c3e3907efe90201f2a3a`,
  `6af4c413907efe90201f2a3b`, `6af4c445c457fbc4b38728f9`, `6af4c498c457fbc4b3872900`,
  `6af4c611907efe90201f2a91`, e prováveis `6af4c4dec457fbc4b3872908` e
  `6af4c61e907efe90201f2a92`.

Critério de corte usado (dúvida dos dois lotes): quem nomeou a função que falhou foi para
função com erro no módulo dela; quem disse "sem sistema" ou só recebeu o comunicado foi
para fora do ar / Transversal; no fiscal, como o cliente acessava o sistema e só a nota
falhava, ficou em API interna e não em instabilidade geral.

### Itens de combustível/óleo exigindo preenchimento novo — 4 clientes, sem chamado
Rejeição 660 / aba Combustível: 301687, 301801, 302045, 302101. Dois dizem que "nunca
pediu isso".

### `codigoIndOp` exige bloco IBS/CBS completo (NFS-e) — 3 clientes, sem chamado
301505, 301713, 301799; o suporte ajusta a configuração caso a caso. No robô N1 o mesmo
erro aparece como E1235: `6af4adc6c457fbc4b387284f`, `6af4bc6dc457fbc4b38728d0`.
Correlato: NFS-e saindo com IBS/CBS para optante do Simples mesmo com alíquota zerada —
301391 e 301421 (no segundo o atendente diz que só foi corrigido na versão nova).

### V3: peças do estoque "não aparecem" no orçamento — 6 clientes, não é defeito
302033, 302107, 302123, 302129, e de passagem 302079 e 302147. O cliente recém-migrado
entra em Orçamentos (função nova) em vez de Ordem de Serviço. É fricção de migração, não
bug; classificado como rotina / Orçamentos & Serviços.

### Veículo cadastrado no cliente não aparece na OS — chamados 108127 e 108165
Dois clientes. No 108127 (V3), ao tentar recadastrar, a placa volta como "já cadastrada".

### Menores
- Erro de servidor ao abrir qualquer cadastro de peça no PortoCar — chamado 108135,
  interno; o texto diz que acontece "com qualquer base porto".
- NF-e de peças não transmite (`PlugNotasUnprocessableEntity`) — chamado 108073, com
  301389 e 301817 ("há 4 dias sem emitir NF"); podem ser o mesmo cliente.
- NF não é enviada por e-mail — chamado 108101 segue: 301309 e 301617.
- Preço de custo e margem de peças mudaram sozinhos na passagem V2→V3 — chamado 108107
  (custo de 832,00 para 1081,60; margem de 30% para 60%). Um cliente; vale vigiar.
- NFC-e 4729 e 4742 não aparecem no sistema nem no XML — um cliente só: chamado 108139,
  301363, 301803.
- Pedidos de voltar à versão antiga ou agendar a migração seguem sem rótulo próprio:
  301419, 301423, 301601, 302023, 302025, 302029, 302071, 302079, 302131, 302135, 302147.
- Ruído de teste na base: 301745, 301795, 301887, 302005 ("teste do spike") e 302013 a
  302019 (resumo automático, empresa "Automatico") — foram para "Conversa vazia".

### Robô N1 (175 conversas novas, 52 fiscais)
- NFS-e rejeitada, "XML não está de acordo com o leiaute da Sefin Nacional" — 3:
  `6af4571f907efe90201f26e0`, `6af4646b907efe90201f2759`, `6af4827b39152e693cc4455e`.
- Venda direta/avulsa não tem módulo na tabela de fronteiras; as três do dia foram para
  Orçamentos & Serviços (`6af4c61e907efe90201f2a92`, `6af4cb1139152e693cc44806`,
  `6af4cc7839152e693cc4482c`). Vale uma regra.
- Nota de devolução de compra segue sendo um grupo grande, com erros distintos entre si.

## Execução diária de 13/11 (lotes A_001, A_002, B_001 e C_001)

530 registros lidos (252 conversas não-fiscais, 39 chamados, 239 fiscais) e 338 conversas
do robô N1 (343 novas na planilha, quase o dobro da véspera). A V3 ganhou 172 conversas
num dia só (799 → 971): é dia de virada em massa, e quase todo incidente abaixo é da V3.

### V3: estoque não reflete na OS depois de compra ou correção — ~25 registros, chamado 108227
O item segue "sem estoque", em vermelho, e trava o fechamento da OS, mesmo depois de a
compra ser autorizada ou o estoque corrigido. É o maior incidente do dia e atravessa os
quatro lotes.
- Conversas não-fiscais, função com erro / Ordem de Serviço (11): 302259, 302431, 302589,
  302711, 302753, 302759, 302841, 302887, 302935, 303079, 303083.
- Mesma assinatura sem citar a OS, Peças & Estoque (3): 302311, 302575, 302707.
- Resolvidos com o botão "Atualizar itens", ficaram como rotina (2): 302417, 302475.
- Chamados (3 clientes): 108227, 108237 (status da peça não vai para "em produção"),
  108241 (quantidade do item não atualiza).
- Fiscal, como "Integração financeiro/estoque/OS com a nota" (6): 108243, 302735 (mesmo
  cliente do 108243), 302739 (cita o 108227), 302705 (cita o 108241), 302847 (cita o
  108253), 302423.
- Robô N1 (7): `6af5c0615909eea9e7e8aa37`, `6af5cef86131adb3941d5d2b`,
  `6af5cefc2a4d5b1adb9586ef`, `6af5ef712a4d5b1adb958841`, `6af5ff8e2a4d5b1adb9589c3`,
  `6af611742a4d5b1adb958b47`, `6af61e8a5909eea9e7e8b147`. O robô manda usar "Atualizar
  itens".
Correlato, saldo negativo de estoque: chamados 108251 (V2) e 108253 (V3) — versões
diferentes, pode não ser a mesma causa.

### V3: orçamento não encontra peças e serviços do cadastro próprio — 15 conversas humanas e 13 do N1
Só aparecem as sugestões da IA. Em 12/11 isto foi registrado como "não é defeito" (o
cliente entra em Orçamentos em vez de OS); hoje o suporte ora trata como uso errado, ora
abre chamado ("vou abrir chamado referente à busca de peças", 302107; "time já está
verificando"). Sem número de chamado no texto. Dois resumos do N1 atribuem a causa ao
filtro de compatibilidade com o veículo.
- Função com erro / Orçamentos & Serviços (10): 302089, 302107, 302129, 302187, 302225,
  302235, 302585, 302635, 302717, 302923 (este por inferência).
- Rotina / Orçamentos & Serviços (5): 302123, 302165, 302171, 302511, 302765. Também
  302131, que ficou em "voltar versão".
- Robô N1 (13): `6af5a8065909eea9e7e8a710`, `6af5b3f06131adb3941d598b`,
  `6af5b7236131adb3941d5a27`, `6af5b7326131adb3941d5a28`, `6af5b92c5909eea9e7e8a959`,
  `6af5ba1e6131adb3941d5ace`, `6af5baaa6131adb3941d5ada`, `6af5bec22a4d5b1adb958535`,
  `6af5e10d5909eea9e7e8acbd`, `6af5f5f42a4d5b1adb9588b9`, `6af5ff165909eea9e7e8aeef`,
  `6af610cf5909eea9e7e8b080`, `6af6f5362a4d5b1adb958d94`.
O mesmo fenômeno ficou partido em dois temas pelo enquadramento do cliente ("não puxa" =
erro; "como faço?" = rotina). Vale uma regra.

### Login com "senha inválida" sem troca de senha, manhã de 13/11 — 10 conversas e 1 chamado
302991, 302995, 302999, 303005, 303013, 303023, 303041, 303043, 303059, 303093. Vários
clientes dizem que ninguém trocou a senha; em 303043 o atendente responde "estamos
verificando essa situação" e aplica paliativo; em 303023, 303041 e 303059 o e-mail de
recuperação não chega. O chamado 108277 relata 5 casos de CNPJs diferentes. Classificado
como rotina / Acesso e login pela regra escrita (o sistema estava no ar e o reset
resolvia), mas tem cara de incidente — a conferir amanhã se continua.

### V3: tipo de documento vazio na importação de XML de compra — 9 conversas e 6 do N1, sem chamado
O combo não lista nada (nem "Vale") e a importação não conclui: 302429, 302455, 302469,
302721, 302823, 302889. A mesma causa impede a devolução de achar a compra: 302427,
302551, 302633. Paliativo do suporte: marcar "É um documento fiscal" em Financeiro >
Contas > Tipos de documento. N1: `6af5c9332a4d5b1adb958671`, `6af5cbfb5909eea9e7e8ab3d`,
`6af5d9932a4d5b1adb95877d`, `6af5ec465909eea9e7e8ad42`, `6af5fbcc5909eea9e7e8ae91`,
`6af5fc695909eea9e7e8aeac`.

### V3: grupo Fatura/parcelas derruba a NF-e — 8 registros, sem chamado
Rejeição 905 "Campos do grupo Fatura não informados" ou "Falha na validação do JSON …
cobranca.parcelas": 302249, 302473, 302525, 302605, 302745, 302803, 302819, 302213. O
suporte resolve apagando a fatura; 302605 e 302819 reclamam que o cliente final fica sem
parcelas e vencimentos. No N1, "Falha na validação do JSON de NFe" / Schema XML aparece
em 10: `6af5b4bc5909eea9e7e8a8a3`, `6af5da185909eea9e7e8ac54`, `6af5dfd12a4d5b1adb9587d6`,
`6af5f0435909eea9e7e8ad72`, `6af5fa805909eea9e7e8ae61`, `6af5fc595909eea9e7e8aea5`,
`6af601e66131adb3941d6139`, `6af604366131adb3941d615a`, e prováveis
`6af6e8085909eea9e7e8b211` e `6af61baf6131adb3941d6367`.

### Consulta de placa ou chassi não retorna o veículo — 7 conversas e 6 do N1
Atendimentos na integradora ATD-34124 (302763) e ATD-34139 (302843). 302211, 302279,
302535, 302749, 302763, 302843, 303091 (este traz dado errado: diesel em vez de flex).
N1: `6af5a6782a4d5b1adb958186`, `6af5b3626131adb3941d596a`, `6af5b3892a4d5b1adb958351`,
`6af5ba112a4d5b1adb9584c4`, `6af5e7f72a4d5b1adb958813`, `6af5fbdf5909eea9e7e8ae92`.
É a "integração de placas" de 10 e 11/11, que segue.

### V3: venda direta não autoriza nem aceita vendedor, empresa e quantidade — 7 conversas, chamados 108233, 108217 e 108197
302103, 302393, 302523, 302599 (108233, filtro por código), 302801 (cita o 108217),
302867, 303033. O chamado 108197 é "Erro de API para autorizar venda direta". N1:
`6af59ec75909eea9e7e8a5ed`, `6af5a7235909eea9e7e8a706`, `6af5cbba5909eea9e7e8ab36`.
Venda direta segue sem módulo na tabela de fronteiras; foi tudo para Orçamentos &
Serviços (no B_001, o 108197 foi para Ordem de Serviço por falta de balde).

### Rejeição 963, PIX estático recusado pela SEFAZ — 4 registros
302215, 302241, 302925, 302119 (sem o código, mesma solução: trocar para PIX dinâmico);
302121 é provável quinto.

### Portal Nacional da NFS-e segue — ~30 registros
Particularidade municipal (10): 302201, 302219, 302331, 302385, 302437, 302567, 302609,
302655, 302669, 303037. Configuração assistida (9): 302145, 302159, 302389, 302531,
302557, 302773, 302793, 303027, 303053. Rejeições de leiaute:
- regime especial / alíquota (E0175, E0625): 302555, 302645, 302787, 302885;
- código de tributação municipal de 3 dígitos (E0314): 302443, 302555, 302653;
- IM do prestador (E0120): 302833, 302981, e chamado 107917 no 302277;
- tpOper / `codigoIndOp` exigindo bloco IBS/CBS: 302565, 302683, 302871.

### Menores
- GTIN / cEAN inválido ("SEM GTIN" digitado errado): 302507, 302637, 302859, 302939,
  303061; em 302637 e 303061 a correção não salva no cadastro. N1:
  `6af610952a4d5b1adb958b20`, `6af623462a4d5b1adb958c84`.
- Nota presa em "processando": 302335, 302757, 302893, e 302487 (chamado 107895).
- NFS-e não envia por e-mail (NF-e e NFC-e enviam): 302323, 302339, 302783. N1:
  `6af5bf0f2a4d5b1adb958536`, `6af5c0d75909eea9e7e8aa1b`.
- Sintegra incorreto: 302291 (chamado 107493), 302975, 303009.
- Nota de devolução com ICMS-ST / CFOP 5202 no N1: `6af5caf42a4d5b1adb95868e`,
  `6af5f91a2a4d5b1adb958915`, `6af5fa082a4d5b1adb95892f`, `6af5fa766131adb3941d6029`.
- Estoque não salva alteração ou zera após a entrada, N1 (5): `6af5b4d52a4d5b1adb9583a2`,
  `6af5b8745909eea9e7e8a93b`, `6af5b8ff6131adb3941d5a8a`, `6af5cd2e5909eea9e7e8ab6a`,
  `6af5ffd46131adb3941d6106`.
- Agrupamento de notas/compras não mostra mais a soma — chamado 108181; 302193 e 302329.
- Manifesto do destinatário, rejeição 656 "Consumo indevido": 302813 e 302985,
  aparentemente o mesmo cliente, "há meses".
- Lentidão ou queda geral em 12/11: 302173, 302369, 302827, 302831.
- Regressão V2→V3 pedida de volta: assinatura do cliente no checklist (chamados 108207 e
  108215); consultar chassi pela placa sem cadastrar o veículo (302167, 302275, 303045).
- Checklist/Diagnóstico: "Relato do Cliente" rejeita texto longo e observações não salvam
  — chamados 108261 e 108271.
- Chamados cobrados mais de uma vez: 108073 e 107885 (302245, 302659, 303025); 108203,
  Rio Truck, retenção de PIS/COFINS fora do PDF da NFS-e (302229, 302541).

### V3: pedidos de volta à versão antiga — 11 conversas humanas e 11 do N1
302131, 302135, 302151, 302183, 302195, 302299, 302399, 302449, 302457, 302751, 302863.
N1: `6af59aef6131adb3941d5704`, `6af5acc85909eea9e7e8a78c`, `6af5ad245909eea9e7e8a796`,
`6af5b2522a4d5b1adb958317`, `6af5b4f55909eea9e7e8a8b4`, `6af5bb605909eea9e7e8a9d6`,
`6af5bdda2a4d5b1adb95852a`, `6af5c1ec2a4d5b1adb95859e`, `6af5cc632a4d5b1adb9586c3`,
`6af5ea382a4d5b1adb95881d`, `6af617e72a4d5b1adb958bae`. Segue sem rótulo próprio: no
humano foi para "função que o sistema não tem" / Transversal; no N1, Transversal.
Regressões atribuídas à migração no N1: dados da oficina somem do PDF do orçamento
(`6af606166131adb3941d61a8`), boletos não vieram em Contas a Pagar
(`6af618675909eea9e7e8b0e6`), previsão do mês sumiu da Visão Geral
(`6af6187f5909eea9e7e8b0e7`), status e etiquetas das OS migrados errado
(`6af620f86131adb3941d63c3`).

### Ruído e higiene
- 10 conversas são testes e2e do "Chat do ERP Ultracar DEV" (usuários de teste,
  `e2e-…@example.test`): 302607, 302639, 302647, 302917, 302921, 302927, 302933, 302945,
  302947, 302951. Foram para "Conversa vazia" / Transversal; não são clientes e talvez
  devam ser filtradas na coleta.
- 302337, 302531 e 302609 têm senha digitada pelo cliente em texto claro no chat
  (sistema, certificado, prefeitura) — e essas conversas vão para a planilha publicada.

### Dúvidas de critério do dia
- Nota de devolução com código de rejeição citado: ficou em "Nota de devolução…" (o
  pedido do cliente é emitir a devolução). Se a regra for "código citado vence", 8 a 10
  dos 34 migram para Rejeição. O prompt não diz qual prevalece.
- "Peças cadastradas sumiram" depois da migração, no N1, fica entre Cadastros e Peças &
  Estoque; foi para Cadastros.
