---
name: fila-atendimento-horaria
description: A cada 20 minutos, das 8h às 18h todos os dias, atualiza a planilha de acompanhamento da fila de atendimento. A série mantém uma linha por hora, reescrita ao longo da hora.
---

Atualize a planilha de acompanhamento da fila de atendimento. São dois scripts e cerca
de **2 minutos** no total.

Diretório de trabalho: `C:\Dev\Qigger\Ultracar\bitrix-analisys`. Rode tudo de lá.

**Este prompt é auto-contido e manda.** Não leia a skill do projeto para decidir o que
rodar: ela descreve o relatório diário, que é outra coisa. Se quiser entender por que um
número é como é, leia depois de publicar.

**Não commite nada.** Esta tarefa não altera o repositório — ela só lê a API e escreve na
planilha. Se o `git status` acusar mudança, alguma coisa saiu do lugar: relate e não
commite.

---

## 1. Montar

```
python pipeline/montar_planilha.py --saida %TEMP%\fila_horaria.json
```

Monta as **seis** abas, todas da API: Agora, Atendimentos por pessoa, Chamados por
pessoa, Comparativo, Backlog de chamados e a linha de Fila por hora.

O Comparativo mostra os dez dias de calendário antes de hoje. Dia fechado sai de um
cache local (`data/store/atendimento_por_dia.json`, fora do git); o que faltar é lido da
API na hora, a cerca de 1 minuto por dia. Por isso **a primeira execução do dia leva um
minuto a mais** — ela lê o dia anterior —, e uma execução depois de dias parado leva
vários. Não é travamento; deixe terminar.

**Confira na saída:** as seis abas montadas e a linha `esperando N · em andamento N ·
chamados abertos N`. Se o script falhar, **pare e relate — não publique nada**.

## 2. Publicar

```
python -X utf8 pipeline/publicar_fila.py --entrada %TEMP%\fila_horaria.json
```

O script escreve direto na API do Google com a conta de serviço, a mesma do relatório
completo. Ele faz sozinho tudo o que antes era manual: envia as sete abas num envio só
(tudo ou nada), decide se a linha de `Fila por hora` é sobrescrita ou nova, repete em
erro 429/500/503, reaplica a formatação de cabeçalho e TOTAL, e lê de volta para
conferir o carimbo e a fila nas duas abas.

**Não use o conector do Google Sheets para escrever nesta planilha**, nem como plano B.
Em 13/11/2026 o conector ficou duas horas devolvendo 500 e deixou a planilha pela
metade; foi por isso que a publicação virou script. Escrita manual pelo conector também
passa por cima da regra da linha da hora, e linha de hora anterior sobrescrita não se
recupera.

**Sucesso é a linha `publicado e conferido: carimbo …`.** Qualquer outra coisa é falha:

- `CONFERÊNCIA FALHOU` — relate os números que o script mostrou.
- Erro HTTP depois das repetições — relate o código. Não tente de novo por outro
  caminho; a próxima execução, em 20 minutos, tenta sozinha.
- `A conta de serviço não tem acesso` — alguém tirou o compartilhamento; relate.

## 3. Relatar

Uma ou duas linhas, em português: quantos clientes na fila sem ninguém, quantas em
andamento, quantas pessoas atendendo, e a mais antiga esperando. Os números estão no
JSON (`abas.Agora` e `abas["Por pessoa"]`).

**Se a fila sem ninguém passar de 40, ou a mais antiga passar de 4 horas, destaque.**
Fora disso, não precisa alarmar: a fila oscila ao longo do dia, e é para isso que existe
a aba por hora.

Se a publicação falhou, diga isso na primeira linha, antes dos números.

---

## O que estes números são, para não os reinterpretar

- **CLIENTES NA FILA SEM NINGUÉM** — sessão aberta em que ninguém do suporte falou
  ainda. É cliente olhando a tela agora, e é o número que a gestão olha primeiro.
- **Em andamento** — sessão aberta, mas alguém já respondeu. Boa parte é sessão que
  ninguém encerrou, não cliente esperando. Não some os dois num total de "fila".
- **Atendendo / Concluiu**, por pessoa — conversa aberta em que a pessoa falou, e
  conversa encerrada em que ela falou. Transferência para quem nunca falou não conta
  para essa pessoa.
- **O backlog de chamados é outro relógio**: mais de mil abertos, mediana de meses. Não
  é fila de atendimento e não muda de uma hora para outra.

## Armadilha que custou quatro correções publicadas

`imopenlines.session.history.get` devolve **50 mensagens** e avisa com `hasNextPage`; a
página seguinte vem com `LAST_ID`. O `pipeline/historico.py` já pagina, e todos os
leitores passam por ele. **Se for mexer em alguma contagem, não chame o endpoint direto.**
Sem paginar, o atendente que falou no começo da conversa some, conversa longa aparece
como não atendida, e a fila incha — chegou a mostrar 106 esperando onde eram 24.