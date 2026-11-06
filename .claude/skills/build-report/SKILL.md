---
name: build-report
description: Gera o relatório de suporte da Ultracar para um período — V2 e V3 num arquivo só, fiscal e não-fiscal, chamados e conversas de chat e WhatsApp. Coleta o que falta no Bitrix, lê e classifica só os registros novos, e produz o relatório em report/. O formato oficial é o de gerar_relatorio_completo.py; o relatório fiscal e o da V3 seguem existindo como saídas próprias. Use quando o usuário pedir para gerar ou atualizar o relatório de suporte, fiscal ou da V3, ou invocar /build-report.
---

# build-report

Gera o relatório de fricção fiscal para uma janela de datas.

**Argumentos:** `--de <yyyy-MM-dd>` (obrigatório) e `--ate <yyyy-MM-dd>` (padrão: hoje).
Aceite também linguagem natural do usuário ("junho", "últimos 3 meses") e converta.

**Saída:** exatamente dois arquivos em `report/`, com o período no nome.
Nunca escreva em `docs/` — lá ficam os artefatos curados por humano.

## Princípio que não pode ser violado

O relatório precisa ser **reproduzível**: rodar o mesmo período duas vezes deve dar o mesmo
resultado. A única fonte de variação é a IA, e ela é contida por três mecanismos já implementados
— cache de classificação, taxonomia congelada e prompt gerado. **Nunca reclassifique um registro
que já está no cache** e **nunca invente subgrupo fora da taxonomia**. Se algo não encaixa,
o rótulo correto é "Outro / não se encaixa".

## Passos

### 1. Coletar o que falta

Leia `data/store/coleta.json` para saber a data da última coleta bem-sucedida.

- **Primeira execução, ou janela anterior à já coletada:** colete o período inteiro.
  ```
  dotnet run --project Ultracar-Support-Bitrix-Analisys -- --mode all --from <de> --to <ate>
  ```
- **Já existe coleta anterior:** colete só o delta, o que traz os chamados novos e os que
  mudaram de status desde então.
  ```
  dotnet run --project Ultracar-Support-Bitrix-Analisys -- --mode tasks --changed-since <data-da-ultima-coleta>
  dotnet run --project Ultracar-Support-Bitrix-Analisys -- --mode conversations --from <ultima-coleta menos 3 dias> --to <ate>
  ```
  A sobreposição de 3 dias nas conversas cobre sessões que continuaram depois do corte anterior.

Se a coleta falhar por rede, tente de novo uma vez — já aconteceu de cair no meio da enumeração.

### 2. Atualizar a base histórica

```
python pipeline/consolidar_store.py
```
Mescla todos os exports de `data/raw/` por id e reconstrói `base_historica.jsonl`.
O cache de classificação é **preservado**, nunca reconstruído.

### 3. Classificar apenas o que é novo — **DUAS ETAPAS**

A classificação tem duas rodadas: primeiro o **assunto** (tema, entre ~22 opções), depois o
**subgrupo** dentro da frente já decidida. Medido em 07/08/2026 contra gabarito cego: duas
decisões fáceis acertam 89,5% onde uma escolha única entre 69 acertava 66,7%. Custa ~1,7x
mais tokens porque o texto é lido nas duas etapas — a troca foi aceita de propósito.

**Não pare depois da primeira rodada.** Se parar, todo registro fica sem subgrupo e o
relatório sai com as frentes certas e nenhuma subdivisão acionável.

```
python pipeline/classificar.py preparar --de <de> --ate <ate>
```

Se disser "Nada a classificar", **pule direto para o passo 4** — o relatório sai inteiro do cache.

Se houver pendências, o comando escreve em `data/store/_fila/`. **O ciclo abaixo se repete
até `absorver` imprimir "Classificação completa nas duas etapas".**

1. Veja quais lotes existem em `data/store/_fila/`. Cada `lote_*.json` tem um
   `prompt_*.md` correspondente, pelo mesmo sufixo:
   - etapa 1: `lote_tema_<tipo>_<n>.json` → `prompt_tema_<tipo>.md`
   - etapa 2: `lote_sub_<frente>_<n>.json` → `prompt_sub_<frente>.md`
2. Para cada lote, lance um subagente:

   > Siga exatamente as instruções de `data/store/_fila/<prompt correspondente>.md`,
   > processando `data/store/_fila/<lote>.json`. Use somente os nomes exatos da lista.
   > Todos os ids do lote devem aparecer na saída — confira a contagem antes de gravar.
   > Leia o lote uma única vez e escreva a saída uma única vez. JSON em UTF-8 sem BOM.

3. Quando todos terminarem:
   ```
   python pipeline/classificar.py absorver
   ```
   Ele diz em qual etapa está. Se anunciar "ETAPA 2 de 2", **volte ao passo 1** — os lotes
   da segunda rodada já estão na fila.

Lance no máximo 6 subagentes em paralelo. Se houver mais lotes, faça em ondas — disparar muitos
de uma vez já estourou o limite de cota antes e derrubou 12 de 16 lotes.

A absorção grava lote a lote, então uma queda no meio não perde o que já entrou. Se algum lote
falhar, relance só ele e rode `absorver` de novo. O estado da rodada fica em `_fila/etapa.json`.

Registros de frente de tema único (P9–P13) e os casos especiais (`Não fiscal`,
`Conversa vazia`) **pulam a etapa 2** automaticamente — ali o subgrupo é o próprio tema.

### 3b. Retomar numa sessão nova

Uma janela grande não cabe numa sessão só. O que é durável e o que não é:

| | Onde | Sobrevive à sessão? |
|---|---|---|
| Rótulos já absorvidos | `data/store/classificacao.json` | Sim — está no git |
| Lotes e respostas em voo | `data/store/_fila/` | Só no disco local, e está no `.gitignore` |

**A ordem na retomada importa.** Comece sempre por:

```
python pipeline/classificar.py status --de <de> --ate <ate>
```

Depois, **se houver `resp_lote_*.json` em `_fila/`, rode `absorver` antes de qualquer
coisa.** `preparar` apaga a fila inteira, respostas incluídas. Desde 23/10/2026 ele se
recusa a rodar nesse estado e manda absorver primeiro; `--forcar` existe para o caso de a
fila ser lixo de uma execução abandonada, e aí o descarte é escolha explícita.

**Absorva só com todos os lotes da etapa respondidos.** `absorver` limpa os `lote_*.json`
sem olhar se cada um tinha resposta, e avança de etapa. Lote sem resposta não perde o
registro — ele volta como pendência no próximo `preparar` —, mas custa um ciclo inteiro a
mais. Se faltar lote, relance só ele antes de absorver.

Nada disso exige recoletar: a coleta já está em `data/raw/`, e `consolidar_store.py`
reconstrói a base a partir dela quantas vezes for preciso.

### 4. Gerar a saída

```
python pipeline/gerar_relatorio.py --de <de> --ate <ate>
```

**Escopo total (opcional).** Se o usuário pedir "todos os chamados", "não só o fiscal" ou
quiser dimensionar o suporte inteiro:

```
python pipeline/gerar_relatorio.py --de <de> --ate <ate> --escopo tudo
```

Acrescenta um terceiro arquivo, `base_completa_<de>_<ate>.xlsx`, com TODOS os registros da
janela — fiscais ou não, classificados ou não. As colunas `Frente`/`Tema`/`Subgrupo` ficam
vazias no que não é fiscal; as de volume, tempo e status valem para todos, porque vêm da
base histórica e não do classificador. A coluna `Categoria` traz a tag que o Bitrix já
grava no título do chamado (`[Melhoria]`, `[Orçamento]`, `[Erro]`...), que cobre 99% dos
chamados não-fiscais — agrupamento pronto, sem gastar um token.

Os dois arquivos oficiais **não mudam**: o executivo continua fiscal, porque a estrutura
dele é frente/subgrupo e quase metade da base sem frente viraria um balde maior que
qualquer frente real.

**Executivo do não-fiscal (opcional).** Existe agora um espelho, sobre as taxonomias
não-fiscais próprias:

```
python pipeline/gerar_executivo_naofiscal.py --de <de> --ate <ate>
```

Duas abas — chamado e conversa —, porque as duas taxonomias foram derivadas separadas e
não têm um nome de tema em comum; somá-las numa linha só daria total sem referente.
**Repasse ao usuário que essas taxonomias nunca passaram por auditoria cega**: o passo 4b
mede só a fiscal. Serve para dimensionar, não para fechar roadmap sem auditar antes.

**Não classifique o não-fiscal sem taxonomia própria.** A taxonomia atual é toda fiscal;
rodar o classificador sobre esses registros mandaria todos para `Não fiscal (falso
positivo)` ou `Outro`, ao custo de ~2M tokens. Isso exige derivar temas novos primeiro —
é projeto, não flag.

### 4b. Auditar a amostra — **não pule**

```
python pipeline/auditar.py preparar --de <de> --ate <ate> --n 50
```

Sorteia 50 registros já classificados, estratificados por frente, e escreve lotes **cegos**
(sem o rótulo atual) em `data/store/_auditoria/` para dois avaliadores independentes.
Lance um subagente por lote:

> Siga `data/store/_auditoria/prompt_<tipo>.md` para classificar
> `data/store/_auditoria/lote_<av>_<tipo>.json`. Use só os nomes exatos da lista, todo id
> deve aparecer, e grave `resp_lote_<av>_<tipo>.json` no mesmo diretório.

São no máximo 4 lotes — custo desprezível perto da classificação. Depois:

```
python pipeline/auditar.py medir --de <de> --ate <ate>
```

Reporte os três números ao usuário: **erro por consenso**, **ambiguidade** e **kappa**.
Eles significam coisas diferentes e não devem ser somados:

- **erro** — os dois avaliadores concordam entre si e contra o rótulo. É erro de execução.
- **ambiguidade** — os dois discordam *entre si*. Aí a fronteira da taxonomia é que está
  mal definida; reclassificar não resolve, só um bump de taxonomia resolve.
- **kappa** — concordância entre avaliadores descontado o acaso.

Se o comando imprimir `ATENÇÃO`, **repasse o aviso ao usuário junto com o relatório**.
Erro acima de 30% ou kappa abaixo de 0,75 significa que aquela janela não sustenta decisão
de roadmap sem revisão. Não omita isso para o relatório parecer mais sólido do que é.

### 5. Reportar ao usuário

Diga, de forma direta:
- o período e quantos registros fiscais ele tem (chamados e conversas)
- quantos vieram do cache e quantos foram classificados agora
- **a deriva** (`python pipeline/classificar.py status --de <de> --ate <ate>`) e, se passar de
  10%, avise explicitamente que a taxonomia precisa de subgrupos novos — foi assim que
  descobrimos IPI, pendência no portal e devolução com IBS/CBS
- os três números da auditoria do passo 4b, e o `ATENÇÃO` se houver

**O caminho dos arquivos, em absoluto e em bloco de código copiável.** O gerador já
imprime assim; repasse igual, não encurte para caminho relativo. Quem lê o relatório
nem sempre está no diretório do projeto.

```
C:\Dev\Qigger\Ultracar\bitrix-analisys\report\relatorio_executivo_<de>_<ate>.xlsx
```

Entregue os dois arquivos com **SendUserFile** — é o que faz o usuário conseguir abrir
com um clique, sem procurar pasta.

Ofereça abrir no Excel, mas **não abra por conta própria**:

```
python pipeline/gerar_relatorio.py --de <de> --ate <ate> --abrir
```

O motivo de não ser automático está nos Cuidados: arquivo aberto no Excel bloqueia a
gravação da execução seguinte. Abrir sempre garante o erro na próxima vez.

### 6. Relatório da V3 — pipeline paralelo

A V3 tem máquina própria e **não** passa pelos passos 3 e 4 acima. O relatório fiscal
exclui `versao == "V3"` de propósito.

```bash
python pipeline/classificar_v3.py status            # o que falta rotular
python pipeline/classificar_v3.py preparar          # esqueleto em _fila/
python pipeline/classificar_v3.py absorver <arq>    # {"chamados": {id: [frente, modulo]}}
python pipeline/classificar_v3.py derivar           # regrava evidencia/n da taxonomia
python pipeline/gerar_relatorio_v3.py --de 2026-09-01 --ate 2026-10-23
```

São dezenas de registros, então cabe num subagente só — sem lotes, sem as duas etapas.
A taxonomia é `taxonomia_v3.json`, frentes R1..R6; `derivar` existe porque o arquivo
manda `evidencia` e `n` serem derivados do cache e isso não acontece sozinho. Rode-o
sempre depois de `absorver`.

**Janela com hora.** `--de 2026-10-29T08:00 --ate agora` para retrato intradiário. Isso
é pedido recorrente ("como está hoje desde as 8h"). Duas coisas só aparecem aí:

- **Fuso.** Conversa está gravada em UTC na base, chamado em hora de Brasília — três
  horas de diferença. `momento_br()` normaliza. Nunca compare `criado_em` cru entre os
  dois tipos, e nunca filtre por hora usando o campo `data`.
- **Conversa aberta.** `encerrada is False` é o sinal, vindo do `COMPLETED` da activity.
  Não use `fechado_em`: ele é o timestamp da última mensagem e nunca vem vazio. Em
  janela curta a maioria das conversas está aberta, com duração e assunto parciais — o
  Resumo e a coluna "Em andamento" avisam, e isso tem de continuar aparecendo.

**Ponto cego do WhatsApp.** A regra marca conversa como V3 pela linha de entrada (17) ou
pela transferência explícita para a fila da V3. O WhatsApp entra todo pela linha 7, então
zap de oficina recém-migrada só conta se o atendente transferiu. Medido em 29/10/2026, dia
da onda de 200 oficinas: a regra deu 1 conversa V3 no WhatsApp e a leitura das conversas
marcadas V2 achou outras 14 (11 pelo texto, 3 por citarem chamado V3). Ou seja, em dia de
rollout a regra pode errar por ordem de grandeza **no canal onde o cliente mais fala**.

Isso vive em `data/store/v3_por_conteudo.json` e sai numa aba própria, **fora de todos os
números**. Em janela de rollout, varra as conversas V2 da janela antes de entregar; não
mexa na regra de `consolidar_store.py` sem decisão do usuário, porque ela define a série
histórica inteira.

## Cuidados

**Taxonomia.** Se o usuário pedir subgrupo novo, edite `data/store/taxonomia.json` e **suba a
versão**. Não adicione categoria durante uma execução: isso quebraria a comparabilidade com
relatórios anteriores.

**Curadoria humana.** Entradas com `"fonte": "manual"` no cache são intocáveis. O comando
`absorver` já as ignora; não contorne isso.

**Excel aberto.** Se a escrita falhar com "Permission denied", o arquivo está aberto no Excel.
Peça para fechar em vez de gravar com outro nome.

**Plano de ação.** Não faz parte deste relatório. Vive em `docs/` como artefato curado, e a
skill não o toca.

## Custo

Cada execução classifica só o que é novo — cerca de 170 chamados e 2.000 conversas fiscais por
mês, algo em torno de 850 mil tokens numa execução mensal. Se o usuário estiver perto do limite
de cota, avise antes de disparar os subagentes e ofereça reduzir a janela.

### 7. Varredura do ponto cego — `varrer_ponto_cego.py`

A seção 6 explica por que ele existe. A mecânica:

```bash
python pipeline/varrer_ponto_cego.py preparar --de 2026-10-29T08:00 --ate 2026-10-29T18:00
# julgue data/store/_fila/ponto_cego_candidatos.md
python pipeline/varrer_ponto_cego.py absorver <vereditos.json> --de ... --ate ...
```

`preparar` divide as conversas V2 da janela em três: **candidatos** (têm sinal de versão
no texto ou citam chamado marcado V3) vão para leitura; **vazias** (WhatsApp sem conteúdo
útil depois de descontar mensagem de sistema) entram direto como não confirmada; o
**resto** fica fora.

O filtro foi calibrado contra as 16 conversas provadas de 29/10 e pega 16/16 lendo 22% das
conversas. Um regex mais estreito — "nova versão|v3|sistema novo|sistema3" — pegava 5 de
12: **o cliente quase nunca diz "V3"**, diz "atualizou", "está diferente", "antes dava e
agora não". A precisão é ~62%: "diferente" e "atualizado" aparecem em mensagem de erro,
certificado digital e Reforma Tributária. Largo de propósito — falso positivo custa
leitura, falso negativo custa a verdade.

`preparar` **reconfere o recall a cada execução**: toda conversa já gravada como
`confirmada` tem de continuar sendo pega pelo filtro, senão ele aborta. Sem isso, afrouxar
o regex degradaria a varredura em silêncio e o sintoma seria um número baixo que ninguém
questiona.

`absorver` só acrescenta — nunca sobrescreve curadoria anterior — e recusa arquivo com
candidato sem veredito, id que não é candidato da janela, ou veredito fora de
V3/V2/indefinido.

### 8. Relatório único V2 + V3 — `gerar_relatorio_completo.py`

```
python pipeline/gerar_relatorio_completo.py --de 2026-01-01 --ate 2026-10-30
python pipeline/gerar_relatorio_completo.py --de ... --ate ... --amostra 1500
```

Pedido da gestão em 29/10: um arquivo só, com chamados, chat e WhatsApp, V2 e V3,
com coluna que diferencia a versão, e percentual de fiscal **e** dos demais assuntos.

O que torna este gerador diferente dos outros é uma restrição da base: existem
**quatro vocabulários** de classificação e eles não se cruzam — fiscal V2 (P1–P13,
três níveis), não-fiscal de chamado (11 temas planos), não-fiscal de conversa (12
temas, lista diferente da de chamado) e V3 (R1–R6 + módulo). Uma tabela única
exigiria inventar um mapeamento entre categorias derivadas separadamente. Por isso o
Resumo é em camadas:

1. **Versão** — V2 / V3-backlog / V3
2. **Natureza** dentro da versão — Fiscal / Não-fiscal
3. **Categoria** — um bloco por vocabulário, percentual só dentro do bloco

As camadas 1 e 2 saem de campos do coletor, então **já são finais mesmo com a leitura
incompleta**; só a 3 depende de classificação. É o que permite validar formato e
ordem de grandeza antes de pagar a leitura. A aba **Cobertura** diz quanto de cada
bloco foi lido — sem ela, percentual sobre 42% do bloco parece tão firme quanto sobre
100%.

`--amostra N` limita as abas de detalhe a N linhas espalhadas pelo período (não as N
mais recentes, que esconderiam a variação ao longo do ano) e acrescenta `_PREVIA` ao
nome do arquivo. Serve para validar formato sem gerar dezenas de MB.

Cuidados que já custaram correção:

- **Rótulo de serviço da V3** tem código igual ao nome; concatenar os dois dá
  "Sem conteúdo útil — Sem conteúdo útil".
- **"Teste interno" sai do denominador**, não só das linhas. Deixá-lo no denominador
  faz o bloco relatar "99,2% lido" quando está 100% — e sugere trabalho que não existe.
- **Fiscal sem frente não é "sem categoria"**: tem tema, e o tema informa. São 3.9 mil
  registros, a maior fatia sendo conversa vazia e 1.4 mil marcados pelo classificador
  como falso positivo do campo fiscal. Num balde anônimo isso sumiria.
- **Natureza "Fiscal" e frente R6 não batem de propósito** — uma é regra do coletor
  sobre o registro, a outra é leitura do conteúdo. A Legenda avisa.

#### Eixo módulo — o que torna V2 e V3 comparáveis

Pedido em 30/10: dar categoria de negócio ao não-fiscal ("clientes, orçamentação,
ordem de serviço"). Isso abriu o que eu tinha dado como impossível. Os quatro
vocabulários discordam sobre **que tipo** de fricção é; todos concordam sobre **onde**
ela acontece. Logo o eixo módulo atravessa V2 e V3 e cabe numa tabela só — é a
camada 3 do Resumo.

A lista de módulos é a **mesma** do eixo módulo de `taxonomia_v3.json`, de propósito:
uma segunda lista tornaria os dois incomparáveis justamente no eixo que os une.
"Clientes" entra em Cadastros, que cobre cliente, veículo, peça e serviço.

`data/store/modulo_por_rotulo.json` mapeia rótulo → módulo. Nada ali é heurística
sobre o registro — é propriedade do rótulo, então todo registro com aquele rótulo
recebe o mesmo módulo, e o resultado é auditável. Precedência:

1. tema de conversa vazia → `(sem assunto)`, nunca Transversal
2. fiscal confirmado → `Fiscal`
3. chamado: colchete do título (`[Orçamento]`, `[Financeiro]`...)
4. tema, quando o tema só existe dentro de um módulo
5. nada resolve → `(a determinar na leitura)`

Medido em 30/10: **66,9% dos 46.981 registros ganham módulo sem custo nenhum**.

Três armadilhas que o mapa resolve e que voltam se alguém simplificar:

- **Campo fiscal ligado não basta.** 1.436 registros têm o campo ligado e foram lidos
  como falso positivo. Dar-lhes módulo Fiscal infla o maior bloco do relatório com o
  que o próprio classificador desmentiu. Só conta fiscal confirmado.
- **Conversa vazia não é Transversal.** São ~4.8 mil no período. Jogá-las no balde
  transversal esconderia que 10% do volume é só "bom dia" e chat abandonado.
- **Colchete vence tema** quando discordam (122 casos): o colchete *nomeia* o módulo,
  o tema só o revela de passagem.

Custo: o que ainda não foi lido recebe módulo junto com a leitura, sem passo extra.
O custo **novo** é só releitura de registro já classificado cujo tema abrange vários
módulos por definição — 4.566 registros em 30/10. A aba Cobertura separa os dois.

#### O que o chamado identifica, e quem o abriu

**Matriz x filial.** No ERP, `tb_company.matrix_id -> tb_matrix.id`: a MATRIZ é a conta
da oficina, a FILIAL é a unidade, com CNPJ único. Para contar oficinas distintas use a
matriz — por CNPJ, uma rede de cinco lojas vira cinco clientes.

**O canal "Robô N1 (IA)"** (antes rotulado "Matrix (bot)", errado) são os chamados
abertos pelo robô de atendimento do site, que montava o título como
`[Matrix: {MatrixId}] [Filial: {cnpj}] - {assunto}`. "Matrix" ali é o id da conta do
cliente, não o nome de uma ferramenta. A integração do robô com o Bitrix caiu em
30/09/2026 — o volume vai de 92 chamados em setembro para 9 em outubro, o que confirma
a data sem depender de documentação.

**Cliente vazio.** Era 845 de 3.078. O robô identifica o cliente só por CNPJ, então a
coluna ficava vazia embora a empresa estivesse identificada. `completar_cliente_por_cnpj`
herda o nome que o mesmo CNPJ tem em outro chamado, pela grafia MAIS FREQUENTE — 249 dos
1.002 CNPJs têm mais de uma grafia, quase sempre variação de sufixo ou sobra de parser
("ID: 9663" sozinho), e a frequência faz o nome bom ganhar do lixo. Caiu para 488, que
são os chamados sem CNPJ nenhum. `cliente_fonte` diz se veio do título ou do CNPJ.

#### Transcrição legível — `transcricoes.json`

Uma mensagem por linha, com hora, para a aba Conversas. Três coisas que não são óbvias:

- **Não vai no campo `texto`.** Aquele é o digest que alimenta `hash_texto`; mudar um
  caractere marcaria os 35 mil registros já classificados como pendentes. Por isso é
  arquivo separado, que só `gerar_relatorio_completo.py` lê — `base_historica.jsonl` é
  percorrida linha a linha por seis scripts e não deve engordar 50 MB.
- **A hora é deslocada em -3h.** O export grava a mensagem em UTC. Sem isso a
  transcrição mostra 20:57 para uma conversa das 17:57. A conferência é o histograma:
  com o ajuste o pico fica em 08h–18h, que é o horário de atendimento.
- **`RUIDO_TRANSCRICAO` é diferente do `BOILER`.** O BOILER serve ao classificador e
  corta "obrigad", que numa leitura humana é fala legítima do cliente. O filtro da
  transcrição só tira o que nenhuma pessoa escreveu. As transferências de fila FICAM.

**O autor da mensagem não existe nos dados.** O exportador grava `AuthorType=System` em
100% das 296 mil mensagens de todos os exports, porque lê `author_id`/`AUTHOR_ID`/
`id_user` e o campo que `imopenlines.session.history.get` devolve chama-se **`senderid`**
(`ConversationMessages.cs:40`). A correção é de uma linha, mas exige recoletar as
conversas para o dado entrar nos exports.

---

# O FORMATO OFICIAL — use este

A partir de 30/10/2026 o relatório entregue à gestão é o de
`gerar_relatorio_completo.py`: um arquivo só, V2 e V3 juntos, janela de um ano.
Os geradores anteriores (`gerar_relatorio.py`, `gerar_conversas.py`,
`gerar_chamados.py`, `gerar_executivo_naofiscal.py`, `gerar_relatorio_v3.py`)
continuam funcionando e **não** devem ser apagados — o `gerar_relatorio_v3.py` ainda
atende o pedido diário da V3, e os outros sustentam séries publicadas. Mas o relatório
geral é este.

## A ordem

```
# 1. coletar o que falta (minutos)
./Ultracar-Support-Bitrix-Analisys/bin/Debug/net10.0/Ultracar-Support-Bitrix-Analisys.exe \
    --mode all --from <AAAA-MM-DD> --to <AAAA-MM-DD>

# 2. quem falou cada mensagem (incremental; ~55 min do zero, minutos no dia a dia)
#    Lê os ids dos exports CRUS, então roda logo após a coleta — não precisa esperar
#    a consolidação. Era o contrário até 04/11 e por isso não achava nada.
python pipeline/enriquecer_autores.py

# 3. status atual dos chamados abertos (~20 chamadas de API, segundos)
#    O merge dá o status do DIA DA COLETA, e a janela diária pega dois dias: sem este
#    passo, chamado que fechou depois da última coleta fica aberto na planilha para
#    sempre. Medido em 05/11: 84 dos 1.051 chamados abertos já estavam fechados.
#    Grava `data/store/status_chamados.json`, que o passo 4 aplica como override.
python pipeline/atualizar_status.py

# 4. consolidar (minutos) — usa o passo 2 para montar as transcrições com autor
python pipeline/consolidar_store.py

# 5. ler o que falta
python pipeline/ler_pendentes.py status
python pipeline/ler_pendentes.py preparar --de <de> --ate <ate>
#    ... classificar cada lote_X_NNN.json com o prompt_X.md do mesmo grupo ...
python pipeline/ler_pendentes.py absorver

# 6. gerar
python pipeline/gerar_relatorio_completo.py --de <de> --ate <ate>
```

**O passo 3 não é opcional, e é o único do pipeline que descreve o presente.** Todas
as outras colunas do relatório contam o que aconteceu num dia e não mudam mais; `Status`
conta onde o chamado está *agora*. Se ele não rodar, a planilha mostra chamado fechado
como aberto, sem avisar — e um relatório que erra o que está aberto erra justamente a
pergunta que a chefia faz primeiro. Ele pula quem já está em status final, então o custo
não cresce com a série.

O passo 5 se repete até `status` dizer `FALTA LER: 0`. O gerador **não** se recusa a
rodar com leitura incompleta de propósito: ele mostra a cobertura no Resumo e cria a
aba Cobertura. Isso é o que permite entregar uma prévia antes de pagar a leitura.

## Como classificar um lote

Entregue a um subagente por lote, com este contrato:

- lê `prompt_X.md` e `lote_X_NNN.json`, grava `resp_X_NNN.json` em UTF-8 **sem BOM**;
- a resposta tem exatamente os ids do lote, nem um a mais nem a menos;
- `tema` e `modulo` são cópia **exata** dos rótulos — o jeito que funcionou em 69 de
  69 lotes foi o agente montar o JSON por um script que LÊ os rótulos do próprio
  prompt, em vez de digitar strings acentuadas;
- peça também: as dúvidas reais (no máximo 3) e, se vários clientes tiveram o mesmo
  defeito, o defeito, o número do chamado e a faixa de ids. **Foi daí que saiu o
  catálogo de incidentes** — o maior valor do último relatório não estava no escopo.

**Quatro a seis subagentes simultâneos, não mais.** Em 30/10 subi para nove e o limite
de sessão derrubou seis de uma vez. Custou dois minutos só porque a fila se retoma do
disco — ver `tasks/lessons.md`.

## Onde moram as decisões

| Arquivo | O que guarda |
|---|---|
| `data/store/criterios_leitura.md` | **os critérios de fronteira**, injetados em todo prompt |
| `data/store/modulo_por_rotulo.json` | mapa determinístico rótulo → módulo |
| `data/store/leitura_completa.json` | o resultado da leitura; **não se regenera** |
| `data/store/taxonomia*.json` | as quatro listas de tema |

`criterios_leitura.md` é o arquivo que faz a série não variar por leitor. Ele nasceu
porque em 30/10 cada lote esbarrou nos mesmos casos de fronteira e resolveu do seu
jeito até a regra ser escrita — os primeiros lotes ficaram mais frouxos que os
últimos, e isso é uma limitação real daquele relatório. Editar esse arquivo muda os
relatórios seguintes e **não** reclassifica o passado.

## O que NÃO está versionado, e por quê

`remetentes.json` (19 MB) e `transcricoes.json` (50 MB) ficam fora por tamanho, e só
porque se refazem com os passos 2 e 3. Tudo o mais que envolve julgamento está no
repositório.

## Atendimento por pessoa — `gerar_atendimento.py`

```bash
python pipeline/gerar_atendimento.py --dia 2026-11-05 --compara 10
```

Pergunta diferente da do relatório principal, e por isso arquivo separado: o relatório
conta **fricção do cliente**, este conta **trabalho da equipe**. Misturar os dois numa
planilha convida a ler um pelo outro.

**Quem atendeu** sai de três fontes na transcrição: a fala (`Atendente (Nome)`), o pick
(`Nome picked conversation`) e a transferência. As duas primeiras contam; a terceira
**não** — conversa roteada para quem nunca a pegou não é atendimento dela. Em 05/11, 105
das 218 conversas atendidas só tinham o nome no pick, porque o autor das mensagens se
perde depois de uma transferência; exigir a fala descartaria metade do atendimento real.

**O campo `operador` da base não serve para isto.** Ele é quem está atribuído, não quem
atendeu: em 05/11 aponta duas pessoas em 478 das 484 conversas, e em 371 delas ninguém
falou.

**O arquivo abre com quem estava fora da fila**, calculado (quem atendeu 15+ em dois dos
dias anteriores e ≤2 no dia). Isso não é enfeite: uma coluna de volume por pessoa, lida
sozinha, faz parecer que quem ficou produziu pouco, quando o que explica o dia é quem não
estava. Em 05/11 foram quatro pessoas com pico de 39 a 74 conversas/dia.

Não mede tempo de atendimento, dificuldade nem qualidade — está escrito na aba Legenda,
onde quem recebe o arquivo vai ler.

### A aba de chamados, e a coluna que não existe

`Chamados por pessoa` conta o trabalho feito NO chamado: concluiu, moveu no fluxo, mexeu
no status, abriu, tocou. Tudo vem do `history` do export, que veio preenchido nos 3.782
chamados — o bloco `comments` veio em 440, todos de 2025.

**Não há coluna de "respondeu", e isso é achado, não limitação do script.** Comentário em
chamado acabou em **27/11/2025**, confirmado de duas formas independentes: no `history`,
os eventos `COMMENT` param nessa data enquanto todos os outros campos seguem até hoje; e
por amostragem na API (`task.commentitem.getlist`), todo chamado sorteado de out/nov 2025
tem comentário e nenhum de dez/2025 em diante tem. A resposta ao cliente migrou para o
chat. Uma coluna zerada diria "ninguém respondeu", que é falso — por isso ela sai do
arquivo com a explicação no lugar dela.

O caminho `COMMENT` segue no código para que uma janela de 2025 ainda saia certa.

**Fusos:** o `history` chega em `+03:00` (servidor do Bitrix) e o chamado em `-03:00`.
São seis horas, que jogam o fim da tarde para o dia seguinte. Provado pelo histograma:
cru, os eventos picam às 14h–22h; convertidos, às 8h–17h com a queda do almoço. Terceira
vez que fuso quase corrompe uma série aqui.

**Invariantes para conferir:** nenhuma coluna pode ser maior que `Chamados que tocou`, e
nome com espaço duplo criaria duas linhas para a mesma pessoa (o Bitrix devolve "Alice
Ribeiro" com dois espaços em alguns registros).
