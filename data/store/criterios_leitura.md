# Critérios de leitura — o que a taxonomia não resolve sozinha

Este arquivo é injetado em TODO prompt gerado por `pipeline/ler_pendentes.py`. Ele
existe porque as listas de tema e de módulo não bastam: em 69 lotes de leitura em
30/10/2026, cada leitor esbarrou nos mesmos casos de fronteira e resolveu cada um à
sua maneira até a regra ser escrita.

Cada regra abaixo nasceu de um caso real que um leitor relatou como dúvida. Não são
preferências — são decisões tomadas uma vez para que a série não varie por leitor.

**Quem editar este arquivo muda a classificação dos relatórios seguintes.** Mudança
aqui não reclassifica o que já foi lido: o passado fica com o critério da época.

---

## Regra zero

Classifique pelo que o **cliente** queria, não pelo que o atendente fez. O atendimento
pode ter terminado em outro assunto; o registro é do pedido.

## Quando NÃO há assunto

- O tema de conversa sem assunto identificável vale só quando realmente não há
  assunto: saudação, vazio, ruído de fila, "ok", agradecimento.
- Conversa abandonada **com pedido concreto declarado** é classificada pelo pedido.
- Quando o assunto só existe num anexo que você não vê ("está dando esse erro" +
  print), use sem assunto identificável. **Nunca escolha o tema mais frequente do
  corpus para preencher a lacuna** — isso infla o balde dominante com registros que
  ninguém leu. Um lote fez isso com 5 registros antes de a regra existir.
- Se o cliente só cumprimenta mas o **atendente** responde com o aviso de um incidente
  ou com um workaround, há assunto: classifique pelo incidente.

## "Sistema fora do ar" — a regra que mais custou

Vale **só quando o sistema INTEIRO está inacessível ou lento**: login falhando para
todos, comunicado de indisponibilidade.

Falha de UMA tela, função ou integração, com o cliente acessando o sistema
normalmente, é **erro de função no módulo correspondente** — mesmo que atinja dezenas
de clientes ao mesmo tempo, e mesmo que o atendente chame de "instabilidade".

Se o atendente responde que o sistema está normal e aponta conexão ou navegador do
cliente, não é fora do ar: é rotina, módulo Acesso e login.

> Por que isso importa: dois lotes marcaram 217 registros do incidente de cadastro de
> veículo de setembro como "fora do ar". Os clientes acessavam o sistema; só aquela
> tela falhava. Sem a regra, "fora do ar" viraria um tema grande do ano por causa de
> um bug de uma função. Os dois lotes foram descartados e relidos.

## Cobrança de prazo

Use o tema de cobrança **só quando o CLIENTE cita um chamado já aberto**. Se o número
vem do atendente e o cliente só diz "alguma novidade", é conversa sem assunto. Se ele
cobra a correção de um problema sem chamado, classifique pelo problema.

## Casos sem tema próprio na lista

A taxonomia tem lacunas conhecidas. Até que ganhem rótulo, use estas saídas:

- **Falha de login** sem relação com mensalidade → tema de rotina, módulo Acesso e login.
- **Código de liberação ou REF do Ultracar Express** → tema de acesso/plano/contrato,
  módulo Acesso e login.
- **Dúvida operacional de Financeiro** (plano de contas, estorno, baixa, parcelamento,
  PIX) → tema financeiro. A lista de rotina cobre OS, orçamento, estoque e cadastro de
  usuário, não Financeiro.
- **Rotina fiscal** ("como faço para...") → tema de rotina, módulo Fiscal.
- **Dúvida comercial sobre parceiro ou integração de terceiro** ("vocês têm parceria
  com o app X?") → tema de função que o sistema não tem, módulo Transversal.

### Só para CHAMADOS — os rótulos abaixo não existem nas outras listas

Se o seu prompt não tem esses rótulos, esta subseção não é para o seu grupo; ignore-a.

- **"Função quebra" genérico** → se o defeito é numa OS, tema de OS que não fecha; se
  é dado salvo que não aparece, tema de cadastro que não é encontrado nem grava; se é
  erro em compra ou estorno, tema de saldo de estoque que diverge; se é uma função do
  **Financeiro** que falha (agrupar contas, conciliar, gerar remessa), tema de boleto e
  lançamento financeiro, módulo Financeiro — é o único balde financeiro que a lista tem.

## Migração da NFS-e para o Portal Nacional (a partir de 01/11/2026)

Resolução CGSN 189/2026 e 191, obrigatória para optantes do Simples Nacional. A partir
de novembro esse evento domina o grupo fiscal — foi 80% de um lote de 250. Sem regra,
cada leitor o distribui de um jeito e o bloco inteiro muda de lugar entre execuções.

O corte, por ordem de precedência:

0. **Bloqueio de ambiente** → **Particularidade municipal de NFS-e**, mesmo tendo
   código. O teste não é o código, é o que a mensagem diz: se ela fala do **ambiente,
   do município ou da data** — este serviço saiu do ar, emita no ambiente nacional,
   este leiaute foi encerrado, procure a Prefeitura — é bloqueio de ambiente. Se ela
   nomeia um **campo ou valor** da nota, é rejeição (regra 1).

   Vistos até agora: `EM110`, `EM111`, `A31`, `P3084`, `P3090`, `2005-O` ("o leiaute 1
   do lote de RPS foi encerrado"), `1647` ("emitir no ambiente nacional a partir de
   01/11/2026"), `E232` ("procure a Prefeitura"), e a frase *"não é permitido emitir
   NFSe através deste serviço na data de competência"*. **A lista é exemplo, não
   fronteira** — ela cresceu três vezes em dois dias, e quem a tratar como fechada vai
   mandar para rejeição o próximo código que signifique a mesma coisa.

   Esses códigos não são falha de schema: são o município dizendo que aquele ambiente
   saiu do ar porque migrou. Tratá-los como rejeição mistura o evento regulatório com
   erro de leiaute. *(Medido em 04/11: sem esta exceção, 15 registros com a mesma
   assinatura ficaram divididos em quatro temas diferentes.)*
1. O texto cita **código de erro ou campo rejeitado de LEIAUTE** (`E202`, `E160`,
   `cvc-pattern-valid`, `cIndOp`, `IM do prestador`…) → **Rejeição/erro de validação**.
2. O cliente **não consegue emitir** por causa da migração, ou o atendente identifica a
   migração como a causa, sem código citado → **Particularidade municipal de NFS-e**.
3. O cliente pede "configurem para mim" e não há erro citado → **Configuração
   assistida pelo suporte**.
4. O cliente só **pergunta** sobre a mudança, sem relatar falha → **Dúvida de uso**.

Dois efeitos colaterais que têm tema próprio e não devem virar "particularidade":
- **A numeração reiniciou em 1** para quem migrou, e vira dúvida recorrente
  ("está certo a nota sair como 1?") → **Numeração/duplicidade**.
- **`E0014`** (série + número + município + CNPJ já existe), por pulo de DPS →
  também **Numeração/duplicidade**.

## Os dois temas de relatório financeiro (grupo de CONVERSAS)

A lista de conversas tem dois rótulos que se sobrepõem:
*"não acha o lançamento ou o relatório financeiro que precisa, ou o valor apresentado
não bate"* e *"não acha o relatório certo ou os números do relatório não batem"*.

O corte usado na série:

- O cliente procura ou questiona um **relatório** → tema de **relatório**. Vale também
  para relatórios financeiros: DRE, balancete, contas a receber, conciliação, vendas
  por tipo de documento.
- O problema é um **lançamento ou saldo na tela** do financeiro → tema **financeiro**.
- **Dúvida operacional do financeiro** (plano de contas, estorno, baixa, parcelamento,
  PIX) também vai no tema financeiro, porque a lista não tem tema de rotina para esse
  módulo.

O módulo segue a tabela de fronteiras — relatório que falha ao emitir é Relatórios,
inclusive o financeiro.

## Dois pedidos no mesmo registro

A regra zero resolve "cliente contra atendente", não "dois pedidos do mesmo cliente".
Quando o registro tem dois assuntos distintos, classifique pelo que **ocupa mais do
texto**. Se empatarem, pelo primeiro declarado.

Mede-se **só o corpo escrito pelo cliente**. O cabeçalho do chamado — o rótulo entre
colchetes e o título do formulário — é a leitura do analista, não o pedido, e a regra
zero já diz que o registro é do cliente. O cabeçalho vale como desempate quando o corpo
empata, nunca como voto. *(Levantado em 05/11 no chamado 107787, cujo título diz
"[Relatório]" e cujo corpo é, em dois terços, um pedido de campo no cadastro.)*

## Consulta de placa que não retorna o veículo

O tema *"Veículo, marca ou modelo não existe na base **e o cliente pede o cadastro**"*
é **pedido de cadastro de um dado que falta** — a segunda metade do rótulo é a que
decide. Não use para falha de consulta.

Quando a placa não puxa marca e modelo, não é aceita, ou volta como "já cadastrada", é
a integração de placas falhando: **tema de função que dá erro**, módulo **Cadastros** —
é na tela de cadastro de veículo que o usuário trava, e a tabela de módulo pergunta onde
dói, não de quem é a API. *(8 registros com essa assinatura em 05/11.)*

## Layout de relatório que mudou da V2 para a V3

Nenhum tema de relatório cobre **layout** — o único fala de filtro, vazio e valor que
não bate. Quando o cliente diz que o relatório agora sai em mais páginas, desalinhado ou
diferente do que era, e pede a versão antiga, use **tema de pedido de campo, filtro ou
regra configurável**, módulo **Relatórios**.

É o balde de "o sistema não tem o que o cliente quer", e é onde isso cai com menos
distorção: o relatório existe e roda, só não sai como antes. Fica registrado como lacuna
da taxonomia — não há rótulo para regressão de layout, e enquanto não houver, esses
casos engordam um balde de pedido em vez de aparecerem como defeito da migração.

## Fronteiras de módulo

| Situação | Módulo |
|---|---|
| Dado cadastral de peça, serviço, cliente, veículo, empresa, funcionário | Cadastros |
| Saldo, movimentação, transferência, compra, cotação, inventário, precificação, etiqueta | Peças & Estoque |
| Funcionário que não aparece como orçamentista ou consultor | Cadastros (a correção é no cadastro dele) |
| CRM interno · termos personalizados · template de WhatsApp · logo na OS | Cadastros |
| CRM externo, API, Cilia, Power BI, apólice Porto/Azul, sistema legado Express | Transversal |
| Importação de orçamento do Cilia | Orçamentos & Serviços |
| Permissão, grupo, usuário, senha, bloqueio | Acesso e login, **mesmo quando o recurso bloqueado é de outro módulo** |
| "Liberar acesso" com pendência financeira explícita | Transversal |
| "Liberar acesso" sem menção de pagamento | Acesso e login |
| Rejeição por GTIN ou IE **na emissão da nota** | Fiscal |
| A mesma exigência **na tela de cadastro** | Cadastros |
| Erro em lançamento, mesmo na tela do DRE | Financeiro |
| Relatório que não abre, não filtra ou falha ao emitir — **inclusive financeiros** (DRE, fluxo de caixa) | Relatórios |
| Layout da folha impressa | Relatórios |
| Logo, CNPJ ou termo que **não se consegue configurar** | Cadastros |
| Logo, CNPJ ou termo configurado que **não sai na impressão** | Relatórios |
| TEF, Stone, Pix | Financeiro |
| Agendamento e atividades do pátio | Gestão de Pátio |
| Vídeo, manual ou material gravado | Auto-guias |
| Call ou treinamento ao vivo | Transversal |
| Tela de consulta ou busca de peça (filtro, aplicação, catálogo) | Peças & Estoque |
| Texto curto ou vazio demais para decidir | Transversal |

Quando o texto cita mais de um módulo, escolha aquele em que o problema **acontece**,
não os citados de passagem.

## "Não fecha a OS porque há compra pendente ou falta item no estoque"

**Módulo: Ordem de Serviço.** Decidido em 04/11/2026. Vale para qualquer grupo; o tema
citado abaixo é o da lista de CHAMADOS, mas a regra de módulo vale sempre que o caso
aparecer.

O eixo é "onde a fricção acontece", e esse caso tem a causa num lugar (a compra, o
estoque) e o travamento em outro (a tela da OS). Vale onde o usuário trava: é o que
responde "onde dói", que é a pergunta da tabela de módulo.

Histórico, porque muda número: a série de janeiro a outubro saiu com os dois
critérios — 63 registros em Ordem de Serviço e 40 espalhados entre Peças & Estoque,
Orçamentos & Serviços e Checklist. Os 40 foram realinhados em 04/11 para Ordem de
Serviço, de forma determinística: todo registro cujo tema é exatamente *"OS não fecha
ou não aceita item por vínculo pendente de compra, entrega ou estoque"* recebe esse
módulo. Quem comparar o relatório entregue em 30/10 com uma regeração posterior vai
ver Ordem de Serviço 40 registros maior, e é só isto.
