---
name: relatorio-suporte-diario
description: Toda manhã às 9h, atualiza o relatório completo do suporte Ultracar até hoje e gera o atendimento por pessoa do dia anterior, entregando os dois arquivos.
---

Atualize o relatório do suporte Ultracar e entregue **dois** arquivos ao usuário: o
relatório do período e o atendimento por pessoa do dia anterior.

Diretório de trabalho: `C:\Dev\Qigger\Ultracar\bitrix-analisys`. Rode tudo de lá.

**Este prompt é auto-contido e manda. Não leia a skill do projeto para decidir o que
rodar.** Ela tem 660 linhas, metade descreve um pipeline aposentado, e seguir aquela
metade faz você rodar o gerador errado (`gerar_relatorio.py` em vez de
`gerar_relatorio_completo.py`) e tratar como obrigatório um passo de auditoria que este
pipeline não tem. Se quiser entender *por que* um passo existe, a skill é boa leitura —
depois de entregar. Quem garante que os dois não divirjam é
`python pipeline/conferir_pipeline.py`, não a sua leitura.

**Se algum passo sair com erro, pare e relate.** Não improvise caminho alternativo e não
gere relatório com dado pela metade. **E desconfie de passo que termina sem erro mas
avisa** — há dois scripts que seguem adiante depois de falhar, e as conferências abaixo
existem para pegar exatamente isso.

---

## 1. Descobrir a janela e coletar

`data/store/coleta.json` tem **dois** campos `to`, um em `chamados` e um em `conversas`.
Use o **menor** dos dois: se um modo falhou na execução passada, eles divergem, e o menor
é o único que não deixa buraco. O `to` é **exclusivo** — o dia que ele nomeia ficou de
fora.

Colete do dia anterior a esse `to` até amanhã, para não deixar borda:

```
./Ultracar-Support-Bitrix-Analisys/bin/Debug/net10.0/Ultracar-Support-Bitrix-Analisys.exe --mode all --from <menor to, menos 1 dia> --to <amanhã>
```

Demora alguns minutos; rode em background e espere. Recoletar dia já coletado é seguro —
o consolidador deduplica por id e o hash do texto é estável, então classificação já feita
não se perde.

**Confira na saída:** as duas linhas finais dizendo quantos chamados e quantas conversas
foram exportados, e que `coleta.json` foi atualizado.

## 2. Autores das mensagens

```
python pipeline/enriquecer_autores.py
```

Incremental: busca só as sessões novas. Minutos no dia a dia; se `remetentes.json` tiver
sido perdido, ~55 min, e parece travado sem estar.

**Confira na saída, e isto não é opcional:** ela **não** pode conter
`falhou em definitivo` nem `aviso: não li`. Esse script, depois de três tentativas num
lote, imprime o aviso, **devolve vazio e sai com código 0** — ou seja, a regra "pare se
der erro" nunca dispara, porque não há erro.

Se aparecer, rode de novo (é incremental, retoma de onde parou) e só siga quando sair
limpo. Consequência de ignorar: as sessões do lote caído ficam sem autor, a transcrição
sai sem rótulo, e o arquivo de atendimento **subconta quem atendeu** — o erro exato que
já fez publicar 17% quando era 37%. O dia seguinte se autocorrige; o arquivo de hoje não.

## 3. Status atual dos chamados abertos

```
python pipeline/atualizar_status.py
```

Segundos. Pergunta ao Bitrix o status de cada chamado que ainda não fechou e grava
`data/store/status_chamados.json`, que o passo 4 aplica como override.

**Por que não dá para pular:** o merge do consolidador dá a cada chamado o status do dia
em que ele foi coletado por último, e a janela de coleta é de dois dias. Sem este passo,
chamado que fechou depois da última coleta aparece como aberto na planilha para sempre.
Medido em 05/11/2026: 84 dos 1.051 chamados que a base dizia abertos já estavam fechados.
É a única coluna do relatório que descreve o presente.

**Confira na saída:** a contagem de override(s) e quantos fecharam. Se der erro de rede,
o script não grava nada e sai com código 1 — rode de novo, não siga adiante.

## 4. Consolidar

```
python pipeline/consolidar_store.py
```

Alguns minutos, **saída bufferizada — não tente acompanhar, espere terminar.** Só depois
que terminar há o que conferir.

**Confira na saída, três coisas:**

1. A linha `status_chamados.json N override(s) de status`. Se ela disser que o arquivo
   NÃO existe, o passo 3 não rodou — volte e rode.
2. `transcricoes.json` e `remetentes.json` têm de ser **iguais entre si**. A diferença
   deles para o número de conversas mescladas é de poucas unidades e é esperada: o
   consolidador conta "conversas legíveis", que é outro denominador (em 05/11: 45.660
   conversas, 45.656 em cada um dos dois). Se a diferença passar de ~0,1%, o passo 2
   ficou pela metade — volte ao passo 2.
3. `subgrupos fora da taxonomia: 0`. Qualquer número aqui significa rótulo inválido na
   base; pare e relate.

## 5. Conferir que nada regrediu (não grava nada)

```
python pipeline/serie_diaria.py
```

**Sem `--registrar` aqui.** Este passo só confere; quem grava é o passo 10, depois da
leitura. Rodar com `--registrar` agora gravaria o número de leituras de *antes* de ler,
e o campo ficaria sempre uma execução atrasado — foi o que aconteceu em 06/11, quando a
série dizia 18.716 e o arquivo tinha 18.791.

Compara os números de hoje com os da última execução e **sai com código 1 se algum
regrediu**. Registros, conversas da V3 e leituras só crescem; queda significa que algo
quebrou a montagem da base.

Isto existe porque as duas conferências que havia aqui antes eram inexecutáveis: pediam
"o total tem de ter crescido" e "a V3 não pode ter despencado" sem que nada guardasse o
número de ontem. `base_historica.jsonl` está no .gitignore, e numa sessão nova você não
tem com o que comparar. **Portão que nunca dispara é pior que portão nenhum**, porque dá
sensação de cobertura — e este é justamente o portão do bug que apagou a marcação V3 de
164 conversas.

Se sair 1, **pare e relate**, dizendo qual número caiu e quanto.

## 6. Ler o que entrou

```
python pipeline/ler_pendentes.py status
python pipeline/ler_pendentes.py preparar --de 2026-01-01 --ate <hoje>
```

Um dia costuma render algumas centenas de registros. Os grupos (A conversa não-fiscal,
B chamado não-fiscal, C fiscal, D só módulo) são loteados **separadamente**, em lotes de
até 250 cada, então o número de lotes depende da mistura do dia — não presuma.
Os arquivos saem em `data/store/_fila/leitura/`.

**Delegue cada lote a um subagente**, com este contrato:

- lê `prompt_X.md` e `lote_X_NNN.json` **de `data/store/_fila/leitura/`**, do mesmo grupo,
  e grava `resp_X_NNN.json` no mesmo diretório, em UTF-8 **sem BOM**;
- a resposta tem exatamente os ids do lote, nem um a mais nem a menos;
- `tema` e `modulo` são cópia exata dos rótulos — mande o agente montar o JSON por um
  script que LÊ os rótulos do próprio prompt, em vez de digitar strings acentuadas;
- grave uma vez só e releia do disco com um segundo script para conferir;
- peça também: até 3 dúvidas reais e, se vários clientes tiveram o mesmo defeito, o
  defeito, o número do chamado e a faixa de ids.

**Os critérios de classificação já vêm embutidos no `prompt_X.md`** — não repita regra no
briefing, só mande seguir o bloco CRITÉRIOS à risca.

**No máximo 4 a 6 subagentes simultâneos.** Acima disso o limite de sessão derruba todos
de uma vez.

Depois:

```
python pipeline/ler_pendentes.py absorver
```

`absorver` recusa o arquivo inteiro se um id faltar ou um rótulo estiver fora da lista. Se
recusar, corrija a resposta do lote e absorva de novo — **nunca edite `data/store/` à mão
para contornar**, porque isso pula a validação.

Repita preparar/absorver até `status` dizer **FALTA LER: 0**.

**Se um lote não fechar em 3 rodadas, desista dele em vez de girar até a sessão acabar:**

```
python pipeline/ler_pendentes.py absorver --parcial
```

Isso grava o que está válido em vez de recusar o arquivo inteiro. Siga para o passo 7, e
então **entregue como prévia**: diga no começo da mensagem que é prévia, qual o
percentual de classificados e quantos registros ficaram de fora. O gerador aceita leitura
incompleta de propósito — ele mostra a cobertura e cria a aba Cobertura. Entregar prévia
avisada às 9h é melhor que não entregar nada.

## 7. Gerar

**São dois arquivos, e os dois vão para o usuário.**

```
python pipeline/gerar_relatorio_completo.py --de 2026-01-01 --ate <hoje>
python pipeline/gerar_atendimento.py --dia <ontem> --compara 10
```

A janela do relatório é **o ano corrente inteiro**, sempre `--de 2026-01-01`. Não é o
período que alguém mencionou: a gestão espera a série do ano.

O segundo é atendimento por pessoa. Repare no `--dia <ontem>`, **não** hoje: o job roda
às 09h e o dia de hoje ainda não aconteceu, então pedir hoje devolve uma planilha quase
vazia que parece dizer que ninguém atendeu. O dia fechado mais recente é o de ontem. (Em
fim de semana e feriado o dia anterior tem volume quase zero — isso é normal, não é
falha; a aba Comparativo mostra os dias anteriores e deixa claro.)

Quando alguém que costuma atender ficou fora da fila, o arquivo abre com uma linha
calculada dizendo quem. Não remova nem reescreva essa linha: uma coluna de volume por
pessoa, lida sozinha, faz parecer que quem ficou produziu pouco, quando o que explica o
dia é quem não estava. **Num dia em que ninguém faltou a linha não existe** — e isso não
é problema.

**Se o Excel estiver aberto no arquivo que você vai gravar**, o `wb.save()` falha com
"Permission denied" — e ele é o último ato, depois de toda a leitura paga. Peça para
fechar a planilha e rode o gerador de novo; **não** grave com outro nome.

## 8. Conferir antes de entregar

- **A linha "classificados" tem de dizer 100,0%.** Se disser 99,x%, **não aceite como
  arredondamento** — descubra QUAIS registros ficaram de fora e por quê. Foi assim que se
  achou um bug que apagava a marcação V3 de 164 conversas. (Se você veio pela saída de
  prévia do passo 6, aqui o esperado é menos de 100% — diga o percentual na entrega.)
- Abra o arquivo com openpyxl e confira: as abas Resumo, Chamados, Conversas e Legenda
  existem; o número de linhas das abas de detalhe bate com o total do Resumo.
- **Aba Cobertura:** ela aparece quando há registro sem tema **ou sem módulo**. Com
  100,0% de classificados ela normalmente não existe. Se os dois sinais discordarem —
  100,0% e aba Cobertura presente —, há registro com tema e sem módulo: investigue qual
  antes de entregar, não escolha um dos dois sinais.
- **Os dois arquivos existem** em `report/`: `relatorio_completo_2026-01-01_<hoje>.xlsx` e
  `atendimento_por_pessoa_<ontem>.xlsx`. Se o segundo não saiu, não entregue só o primeiro
  em silêncio — diga que faltou.
- **No arquivo de atendimento**, a linha `TOTAL atendidas` da aba Comparativo não pode ser
  maior que `Conversas abertas no dia`.
- **Na aba `Chamados por pessoa`**, nenhuma coluna pode ser maior que `Chamados que
  tocou` — é o superconjunto. E não espere uma coluna de "respondeu": comentário em
  chamado acabou em 27/11/2025 e o script põe a explicação no lugar dela.

A sanidade da V3 e o crescimento da base **já foram conferidos no passo 5**, contra a
série — não tente reconferir de cabeça.

## 9. Publicar na planilha do Google

```
python pipeline/publicar_relatorio.py
```

Sobe o .xlsx recém-gerado para a planilha **Relatório Completo de Atendimento**, as
quatro abas. Leva pouco mais de um minuto para as 49 mil linhas.

Ele fala direto com a API do Google usando a conta de serviço do `appsettings.json` —
não é o conector do Sheets, e por isso o volume não passa pela sessão. **Não tente
publicar pelo conector**: a aba Conversas tem 35 MB de texto e não cabe numa mensagem.

**Confira na saída:** as quatro abas listadas com a contagem de linhas, e a linha
`pronto em N min`. Se der `HttpError 403`, a planilha deixou de estar compartilhada com
`ultracar-report-chat-ai@ultracar-492817.iam.gserviceaccount.com` — relate, não tente
contornar.

Se este passo falhar, **o relatório já foi gerado e entregue**: diga que a planilha não
foi atualizada e siga para o commit. Não repita o pipeline inteiro por causa dele.

## 10. Entregar e commitar

Entregue **os dois arquivos** com `SendUserFile`, `status: "proactive"` (o usuário não
está esperando na frente da tela). **Escreva também os dois caminhos absolutos** em bloco
de código na mensagem: se o `SendUserFile` falhar, o usuário fica sem arquivo e sem saber
onde ele está, e `report/` está no .gitignore.

Na mensagem final, em português, diga: o total de registros e a quebra
chamados/conversas, quantos entraram desde a última execução (o passo 5 imprime o delta),
a divisão por módulo (os 5 maiores), e **se algum lote reportou um mesmo defeito
atingindo vários clientes, destaque isso** — é o que tem mais valor para a gestão e não
aparece em nenhuma tabela.

Do arquivo de atendimento, diga: quantas conversas o dia teve, quantas foram atendidas,
quantas ficaram abertas sem ninguém atender, e, **se houver**, quem estava fora da fila
(a linha que o script calcula). Esse último é o que explica um dia ruim; sem ele o número
de atendimentos por pessoa é lido como desempenho.

**A taxa de atendimento depois do aviso de fila cheia** sai da última linha do
`gerar_atendimento.py`: `aviso de fila: N conversas, M atendidas`. Divida M por N. Ficou
entre 97% e 100% de junho a outubro, caiu para 84% em 04/11 e 37% em 05/11. **Abaixo de
90%, destaque na mensagem.**

Se houver defeito em massa novo, acrescente ao fim de `tasks/incidentes_detectados.md`,
no mesmo estilo das entradas que já estão lá.

## 11. Registrar a série

```
python pipeline/serie_diaria.py --registrar
```

Agora sim com `--registrar`, e só aqui: a leitura já aconteceu, então o número gravado é
o estado final do dia e serve de linha de base honesta para amanhã.

## 12. Commitar

Por fim, commit direto na master (projeto simples, sem fluxo de branches). Entram as
mudanças em `data/store/` que forem rastreadas e qualquer coisa em `tasks/`. O diretório
`report/` está no .gitignore. Termine a mensagem de commit com:

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>

---

## Armadilhas desta base, para não redescobrir

- **Campo de planilha que vira chave de comparação nunca passa por `str()` direto.** Um
  único nulo faz o pandas ler a coluna inteira como float, e `str(17.0)` vira "17.0". Já
  quebrou duas coisas aqui.
- **Console é cp1252**: imprimir texto com acento estoura com UnicodeEncodeError. Escreva
  em arquivo com `encoding="utf-8"` e leia o arquivo.
- **Heredoc do bash come barra invertida**: escrevendo Python por heredoc, `\b` num regex
  vira caractere de controle. Use a ferramenta Write para criar scripts.
- **`write_text` do Python converte LF para CRLF no Windows** e reescreve o arquivo
  inteiro no git. Para editar arquivo de texto do repositório, use `write_bytes`.
- **`preparar` apaga a fila.** Não rode com resposta não absorvida em
  `data/store/_fila/leitura/`.
- **Fuso, três variantes no mesmo projeto:** conversa é gravada em UTC, chamado em
  horário de Brasília, e o `history` do chamado em `+03:00`. Os scripts normalizam; o
  perigo é escrever um filtro próprio.
- **Não crie categoria nem subgrupo durante a execução.** A taxonomia é congelada; se
  algo não encaixa, o rótulo é o de "não se encaixa". Registro com `"fonte": "manual"` é
  curadoria humana e não se toca.
- **Em janela de rollout da V3**, a regra de marcação erra por ordem de grandeza: o
  WhatsApp entra todo pela linha 7 (V2), então conversa da V3 por WhatsApp só é contada
  se um atendente transferiu. Em 29/10 a regra deu 1 e a leitura achou 25. Se o dia tiver
  migração em massa, diga na entrega que o número da V3 é piso.
