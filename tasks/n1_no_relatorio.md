# Conversas do robô N1 no relatório — medição e recomendação

Data da análise: 06/11/2026. Fontes: planilha `Ultracar - Conversation Report - PROD`
(id `1azoMwmwVCVVJOtxyzUMNQZhCvEzERmFluxdUbIcmA1w`, aba Conversas), lida com a conta de
serviço `ultracar-report-chat-ai@ultracar-492817` já usada por
`pipeline/publicar_relatorio.py`; `data/store/base_historica.jsonl`; e o código de
`ultracar-support-ai` para desambiguar duas colunas.

Credencial nova: **nenhuma**. A conta de serviço já é Editor da planilha do Cron.

## Volume e janela

| | |
|---|---|
| Conversas encerradas e exportadas | **2.627** |
| Janela | **27/08/2026 a 06/11/2026** (70 dias com registro) |
| Média por dia com registro | 37,5 |

Por mês: ago 149 (parcial, começa em 27) · set 887 · out 1.054 · nov 537 (até o dia 6).

A planilha tem 2.628 linhas preenchidas numa grade de 3.007 — é o universo completo
desde que o Cron entrou, não uma amostra. `ID Conversa` é único nas 2.627 linhas.

A aba `Clientes` tem 6.072 linhas de uma coluna só (`ID`); não serve de dimensão.

## O que já vem classificado — e por que isso muda o tamanho do trabalho

A planilha **não é texto cru**. O Cron já grava, por conversa, o resultado de uma
classificação feita pelo próprio N1:

| `Resultado` | n | % |
|---|---|---|
| Resolvido | 1.299 | 49,4% |
| Não resolvido — lacuna de conhecimento | 452 | 17,2% |
| Não resolvido — resposta inadequada | 174 | 6,6% |
| Abandonada | 153 | 5,8% |
| Encaminhado ao N2 | 135 | 5,1% |
| Ticket aberto | 117 | 4,5% |
| Parcialmente resolvido | 115 | 4,4% |
| Ticket consultado | 84 | 3,2% |
| Não resolvido — classificação incorreta | 71 | 2,7% |
| Apenas saudação | 15 | 0,6% |
| ⚠ Erro ao processar resumo | 12 | 0,5% |

Também vêm prontos: `Assunto` (2.072 valores distintos, texto livre), `Problema`,
`Resumo`, `Precisão` (1.734 em 100%), `Lacunas (base de conhecimento)`, `Foi útil?`
(966 Sim / 325 Não / 1.336 em branco), `Mensagens` (média 13,1), `Duração`,
`Transcrição`, `Matrix ID` e `User ID` (100% preenchidos), `Versão do ERP` (V2 531,
V3 630, 1.466 em branco — o robô atende as duas, e V3 só aparece de outubro em diante).

**Consequência para o esforço:** não é preciso classificar 2.627 conversas do zero. O
trabalho é **mapear `Assunto` livre para a nossa taxonomia** (como `modulo_por_rotulo.json`
já faz para os rótulos atuais) e reaproveitar `Resultado` como está. Isso é trabalho de
**horas**, não de dias. Classificar do zero, pela transcrição, seria dias — e jogaria
fora uma classificação que já existe.

## A armadilha das duas colunas

A coluna **I** tem cabeçalho `Ticket` na aba de prod, mas o código do N1 escreve ali
`escalatedToN2 ? "Encaminhado ao N2" : "N/A"` desde 13/10/2026
(`Infrastructure.ThirdParties/GoogleSheets/GoogleSheetsReportService.cs:184`). O
cabeçalho nunca foi atualizado. Então a coluna I guarda **duas coisas diferentes**:

| Período | Conteúdo da coluna I |
|---|---|
| 27/08 a 06/10/2026 | número do chamado aberto no Bitrix (`105881`..`106963`), ou `N/A` |
| de 07/10/2026 | flag de escalação (`Encaminhado ao N2` / `N/A`) |

Ler a coluna por nome de cabeçalho, sem o corte de data, é bug garantido. Quem ler
precisa tratar os dois significados.

**A virada está no dado, não na documentação.** O código do N1 diz que o cabeçalho mudou
em 13/10, mas o flag aparece a partir de **06/10** — e 06/10 é o dia em que as duas formas
convivem (1 número, 16 flags, 18 `N/A`). Por isso o corte usado é 07/10, o primeiro dia
inteiro de flag. Isso importa: `N/A` antes da virada significa "não abriu chamado", não
"não escalou". Tratar os `N/A` de setembro como "não escalou" inventaria denominador e
puxaria a taxa para baixo — foi assim que a primeira medição saiu 47,5% em outubro em vez
de 54,9%.

## Taxa de escalação — dá, e sem join

Há **duas** medidas, e elas são diferentes de propósito:

| Medida | Origem | Significado |
|---|---|---|
| **Escalou ao N2** | coluna I, flag `escalatedToN2` | fato do código, vem do chamador, independe do resumo do LLM |
| **Handoff direto** | `Resultado = "Encaminhado ao N2"` | spec 023.01/D4: o agente **não tentou** responder |

Medido só onde o flag existe (07/10 em diante), que é o denominador honesto:

| Mês | Conversas | Escalou | % | Handoff direto | % |
|---|---|---|---|---|---|
| out/2026 (de 07) | 883 | 485 | 54,9% | 88 | 10,0% |
| nov/2026 | 537 | 314 | 58,5% | 45 | 8,4% |
| **07/10–06/11** | **1.420** | **799** | **56,3%** | **133** | **9,4%** |

Nenhuma das duas existe antes de 07/10/2026 — o flag não era gravado. Então a série de
escalação começa em outubro, não em agosto, e começa no dia 7.

Nuance a não perder: das 799 escaladas, 216 têm `Resultado = Resolvido` e 289 têm
`Lacuna de conhecimento`. Escalar e resolver não são excludentes na fonte — o robô pode
responder e ainda assim a conversa seguir para o N2.

**O que NÃO dá:** seguir o mesmo cliente para dentro do atendimento humano. O N1 tem
`Matrix ID` e `User ID` nas 2.627 linhas; as 45.731 conversas humanas de
`base_historica.jsonl` têm `matriz` e `cnpj` **vazios em 100%** dos casos — só um
`cliente` de texto livre, muitas vezes só o primeiro nome ("Daniel", "Amanda Rocha").
`remetentes.json` mapeia mensagem → "Cliente"/"Atendente (nome)", sem id do cliente.
Join por matriz + janela de 4h: **0 de 135**. A taxa de escalação é medível; o par
"conversa do robô ↔ conversa humana que a recebeu" não é, sem mudar o export do Bitrix.

## Contagem dobrada antes de 30/09 — risco pequeno e exatamente delimitado

A premissa se confirma, e o recorte é limpo:

- A planilha cita **117 números de chamado**, todos distintos, todos com
  `Resultado = "Ticket aberto"` (relação 1:1).
- **117 de 117 existem** em `base_historica.jsonl`, e **todos os 117 estão no canal
  `Robô N1 (IA)`**. Zero fora do canal, zero ausentes.
- Por período: **109 até 30/09** e 8 depois (ids `106849`..`106963`, até 06/10) — a
  cauda da integração, coerente com os 9 chamados de outubro que o canal tem na base.

O canal `Robô N1 (IA)` tem 696 chamados na base (16/04 a 06/10/2026), dos quais 129 caem
na janela da planilha. Desses 129, 117 são citados e **12 não** — conversas que o Cron
não exportou (provavelmente não encerradas na virada). Os outros 567 são anteriores a
27/08, quando o Cron ainda não existia: a planilha não os cobre.

**Portanto:** se as duas fontes forem somadas, a deduplicação é exata e barata — casar
o número da coluna I com `id` do chamado. Não precisa de heurística.

## Recomendação

### 1. Ao lado, em eixo próprio. Não somado.

Três razões, agora com número:

- **Semântica.** Conversa do N1 é fricção que **não** chegou ao suporte humano. Somar
  mistura "o cliente travou" com "o cliente travou e ocupou um atendente".
- **Denominador.** Na janela 27/08–06/11 a base tem 12.078 registros humanos (11.328
  conversas + 750 chamados). Somar 2.627 move o denominador **+21,8%** e reescreve todo
  percentual da série já publicada — sem que nada tenha mudado no mundo real.
- **Janela.** O N1 começa em 27/08/2026; a base vai a 07/02/2024. Uma série somada teria
  um degrau artificial em agosto que é só o início do export.

Formato sugerido: aba própria (`Robô N1`) com a mesma taxonomia de assunto/módulo das
demais, mais as colunas que só o N1 tem (resultado, escalação, precisão, lacuna). O
total humano segue intocado; a comparação fica possível porque o eixo de assunto é o
mesmo.

### 2. Período anterior a 30/09: manter como está, e marcar.

Os 109 chamados anteriores a 30/09 já estão na base com canal `Robô N1 (IA)` e já
contam como chamado — foi trabalho que **chegou** ao humano, então o lugar deles é onde
estão. O que fazer:

- **Não** somar essas 117 conversas ao eixo do N1 como se fossem só conversa; elas têm
  as duas pontas.
- Na aba do N1, marcar a conversa com o id do chamado que ela gerou (a coluna I já dá
  isso de graça), para que "conversa do N1 que virou chamado" seja filtrável.
- Deixar explícito no relatório que **a comparabilidade quebra em 30/09**: antes dessa
  data o robô abria chamado e o volume do canal `Robô N1 (IA)` é consequência disso;
  depois, ele encaminha ao N2 e esse volume vira escalação, que vive em outra coluna.
  O mesmo cliente com o mesmo problema aparece em lugares diferentes antes e depois.

Dedup, se um dia alguém somar: casar coluna I numérica com `id` — 117 casos, exato.

### 3. Escalação: publicar as duas medidas, a partir de outubro.

56,3% escalaram e 9,4% foram handoff direto, no período em que o flag existe. As duas
juntas contam a história: mais da metade das conversas termina no N2, mas só uma em dez é
o robô desistindo antes de tentar. Publicar só uma das duas distorce em qualquer direção.

Não prometer o par conversa↔conversa humana. Se isso virar requisito, o caminho é o
export do Bitrix passar a trazer um id de cliente nas conversas de canal aberto — hoje
não traz.

## O que a comparação mostrou, agora que o eixo é o mesmo

Com os 2.615 módulos lidos, dá para colocar os dois eixos lado a lado. Fora os baldes de
"sem assunto" dos dois lados (o humano tem 17,2% de conversa vazia; o N1 não produz esse
rótulo), na janela 27/08–06/11:

| Módulo | Suporte humano | Robô N1 |
|---|---|---|
| **Fiscal** | **62,7%** | **34,8%** |
| Transversal | 6,5% | **16,6%** |
| Financeiro | 7,8% | 10,6% |
| Peças & Estoque | 3,7% | 8,1% |
| Relatórios | 4,0% | 7,6% |
| Cadastros | 5,2% | 7,1% |
| Ordem de Serviço | 2,7% | 5,2% |
| Orçamentos & Serviços | 2,3% | 3,6% |
| Acesso e login | 3,4% | 3,6% |
| Checklist & Diagnóstico | 0,5% | 1,2% |
| Gestão de Pátio | 0,5% | 0,8% |
| Auto-guias | 0,1% | 0,5% |
| Visão Geral | 0,3% | 0,3% |

Base: 9.998 registros humanos e 2.615 conversas do N1.

**A leitura:** o suporte humano é esmagadoramente fiscal (62,7%), enquanto o robô pega
uma fricção muito mais espalhada. O contraste mais forte é `Transversal`, 2,5× maior no
N1 (16,6% contra 6,5%) — é onde moram consulta de chamado, pedido de atendente, boleto da
mensalidade, treinamento e conversa sem pedido concreto. Ou seja: **o robô absorve uma
classe de fricção que quase não aparece na fila humana**, e é exatamente por isso que
somar os dois eixos apagaria a informação em vez de criá-la.

Isto é a primeira coisa que o relatório passa a responder e antes não respondia: não
"quantas conversas o robô atendeu", mas *em que o robô é acionado que o humano não é*.

## Publicado, e dois bugs que a publicação revelou

Publicado em 06/11/2026 na planilha de sempre: aba "Robô N1" com 2.627 linhas, 17
colunas, congelamento e filtro. As abas humanas seguem intactas (3.229 chamados, 45.782
conversas).

Dois defeitos apareceram no caminho, **nenhum deles causado pelo N1** — a aba nova só os
expôs:

1. **O publicador escolhia o arquivo por ordem alfabética**, não por data
   (`sorted(glob(...))[-1]`). Como `"_"` vem depois de `"."`, o `..._PREVIA.xlsx` SEMPRE
   vencia o arquivo real da mesma janela. Qualquer prévia da janela corrente deixava a
   próxima publicação — inclusive **o job das 9h, que roda sem argumento** — subindo
   25 linhas de amostra sobre a planilha que a gestão lê. Agora é data de modificação, e
   prévia não é candidata. `formatar_planilha.py` tinha a mesma linha e aponta para a
   mesma função.
2. **`Precisão` era publicada como `0,8`** em vez de `80%`. O `number_format` do openpyxl
   não atravessa para o Google: aba grande recebe regra, não formatação fiel. Resolvido
   com uma regra de formato por nome de coluna, no mesmo padrão que o `CLIP` da coluna
   `Conversa` já usava.

## O que foi implementado (06/11/2026)

- [x] **`pipeline/coletar_n1.py`** — lê a planilha com a conta de serviço existente,
      resolve as duas semânticas da coluna I e grava `data/store/n1_conversas.jsonl` +
      `n1_transcricoes.json`. Incremental: compara registro a registro, porque o N1
      reconcilia linhas já escritas.
- [x] **`pipeline/classificar_n1.py`** — `preparar`/`absorver`/`status`, no mesmo contrato
      arquivo-para-subagente do resto do projeto. Importa o prompt do grupo D, a lista
      `modulos_validos` e o `hash_texto` de `ler_pendentes.py` em vez de copiar.
      Grava `data/store/classificacao_n1.json` (versionado: é julgamento de leitura).
- [x] **Aba "Robô N1"** em `gerar_relatorio_completo.py` — `carregar_n1()` e
      `aba_robo_n1()`, fora de `regs`. Conferido: os 12.078 registros humanos da janela
      continuam idênticos, nenhum denominador se moveu.
- [x] Skill, tarefa agendada e a cópia versionada em sincronia
      (`conferir_pipeline.py` passa). O passo do N1 é o único com licença para falhar sem
      parar o job.
- [x] Espelho da planilha no `.gitignore` (4 MB cada, refeito em segundos);
      `classificacao_n1.json` fica versionado.

## Pendências que isto abre

- [ ] **Dois casos de fronteira sem regra escrita**, apontados na classificação:
      `6a959e8c2f4c66f5179a7480` ("lançar um novo MCM" — sigla não resolvida) e
      `6a90d533ff104f63a73386ae` ("OTEF e SPED", dois assuntos empatados). Resolvidos por
      regra de empate, não por critério. Se virarem padrão, entram em
      `criterios_leitura.md`.
- [ ] **Pedido de treinamento não tem critério, e os lotes divergiram.** Um lote mandou
      para `Transversal` ("vale o que o cliente pediu, não o formato da resposta"), outro
      para `Auto-guias` ("pedido de vídeo/treinamento gravado"). Medido nas 1.615
      primeiras classificadas: **15 conversas** falam de treinamento/vídeo, **7 em
      Transversal e 6 em Auto-guias** — e os dois conjuntos são indistinguíveis
      ("Treinamento sobre orçamento no novo sistema" caiu em Auto-guias; "Treinamentos
      sobre módulo financeiro", em Transversal).

      É deriva real, do tipo que `criterios_leitura.md` existe para evitar, mas são 13
      registros em 1.615 (0,8%) num módulo que fica perto de zero de qualquer forma. Não
      vale refazer lotes; vale uma linha no `criterios_leitura.md` antes da próxima
      corrida. A escolha é de quem conhece o negócio: "pedido de treinamento é
      Transversal porque o cliente pediu ajuda, não usou um recurso" **ou** "é Auto-guias
      porque é a demanda que aquele módulo atende".
- [ ] Não editar `criterios_leitura.md` no meio de uma corrida de lotes: os primeiros
      lotes ficariam com critério diferente dos últimos, que é exatamente a deriva que o
      arquivo existe para evitar. Mudança de critério vale para a próxima corrida inteira.
- [ ] Decidir se os 12 chamados do canal N1 na janela sem conversa exportada merecem
      investigação ou nota de rodapé
- [ ] Pedir ao N1 (ou ao export do Bitrix) um id de cliente nas conversas humanas, se o
      par ponta-a-ponta virar requisito
- [ ] Avaliar se o volume do N1 merece um campo em `serie_diaria.py` — hoje a série não
      vigia essa fonte, então uma queda de volume do Cron passaria em silêncio
