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
  erro em compra ou estorno, tema de saldo de estoque que diverge.

## Migração da NFS-e para o Portal Nacional (a partir de 01/11/2026)

Resolução CGSN 189/2026 e 191, obrigatória para optantes do Simples Nacional. A partir
de novembro esse evento domina o grupo fiscal — foi 80% de um lote de 250. Sem regra,
cada leitor o distribui de um jeito e o bloco inteiro muda de lugar entre execuções.

O corte, por ordem de precedência:

0. **Bloqueio de ambiente** — `EM110`, `EM111`, `A31`, `P3084`, `P3090`, ou a frase
   *"não é permitido emitir NFSe através deste serviço na data de competência"* →
   **Particularidade municipal de NFS-e**, mesmo tendo código. Esses códigos não são
   falha de schema: são o município dizendo que aquele ambiente saiu do ar porque
   migrou. Tratá-los como rejeição mistura o evento regulatório com erro de leiaute.
   *(Medido em 04/11: sem esta exceção, 15 registros com a mesma assinatura ficaram
   divididos em quatro temas diferentes.)*
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

## Dois pedidos no mesmo registro

A regra zero resolve "cliente contra atendente", não "dois pedidos do mesmo cliente".
Quando o registro tem dois assuntos distintos, classifique pelo que **ocupa mais do
texto**. Se empatarem, pelo primeiro declarado.

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
