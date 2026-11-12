---
name: fila-atendimento-horaria
description: A cada 10 minutos, das 8h às 18h todos os dias, atualiza a planilha de acompanhamento da fila de atendimento. A série mantém uma linha por hora, reescrita ao longo da hora.
---

Atualize a planilha de acompanhamento da fila de atendimento. O script leva cerca de
**1 minuto**; a execução inteira, uns 3.

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

Nenhuma aba lê a base do relatório diário. A base guarda no máximo 50 mensagens por
conversa, então toda contagem de atendimento feita sobre ela subconta conversa longa —
que é justamente a mais atendida. O Comparativo usa um cache por dia
(`data/store/atendimento_por_dia.json`): dia fechado é lido uma vez e guardado, e só
hoje é relido, senão a passada levaria dez minutos em vez de um.

**Confira na saída:** as seis abas montadas e a linha `esperando N · em andamento N ·
chamados abertos N`. Se o script falhar, **pare e relate — não publique nada**. Planilha
pela metade é pior que planilha velha: quem olha não sabe que está pela metade.

## 2. Publicar no Google Sheets

Planilha: **`1OMeE3bxuEhL3vInphdLKdOKEpDsCrQnROdJJmt4w2U8`** (Atendimentos - Bitrix).
Confira o id caractere a caractere antes de escrever; um id trocado escreve na planilha
de outra pessoa, e isso já quase aconteceu.

O JSON tem `abas` (nome → linhas) e `linha_hora`. Use o conector do Google Sheets:

| Aba | Como escrever | Intervalo |
|---|---|---|
| `Agora` | `update_values`, sobrescreve | `Agora!A1:B<n>` |
| `Por pessoa` | `update_values`, sobrescreve | `Por pessoa!A1:E<n>` |
| `Chamados por pessoa` | `update_values`, sobrescreve | `Chamados por pessoa!A1:F<n>` |
| `Comparativo` | `update_values`, sobrescreve | `Comparativo!A1:L<n>` |
| `Backlog de chamados` | `update_values`, sobrescreve | `Backlog de chamados!A1:B<n>` |
| `Legenda` | `update_values`, sobrescreve | `Legenda!A1:C<n>` |
| `Fila por hora` | **uma linha por hora**, ver abaixo | `Fila por hora` |

**A aba `Fila por hora` tem UMA linha por hora, atualizada ao longo dela.** A tarefa roda
de 10 em 10 minutos, então na maior parte das vezes a linha da hora vigente já existe e
deve ser **sobrescrita**, não duplicada:

1. Leia a última linha preenchida da aba (`Fila por hora!A:B` basta).
2. Compare a **"Hora medida"** dela com a `hora_medida` que o script gerou. A janela é a
   identidade da linha — é ela que diz o que a linha contém, não o horário em que a
   execução rodou.
3. **Mesma janela:** `update_values` naquela linha, por exemplo `Fila por hora!A58:L58`.
4. **Janela diferente, ou aba só com cabeçalho:** `append_values` numa linha nova.

Comparar a janela, e não a hora do `Momento`, evita um erro silencioso na virada: uma
linha gerada às 09:19 que mediu `08:00-09:00` tem Momento na hora 09 mas pertence à
janela das 08h — sobrescrevê-la apagaria uma hora inteira do histórico.

As colunas "Entraram na hora" e "Fechadas na hora" medem **a hora corrente até agora** —
às 08:50 a janela é 08:00–08:50, e a coluna "Hora medida" declara isso. Por isso a linha
da hora em curso cresce ao longo dela, e a última escrita da hora é a que fica.

**Nunca sobrescreva uma linha de hora anterior.** O histórico do dia é a única coisa que
essa aba tem de útil, e ele não se recupera.

Duas armadilhas de escrita, as duas já custaram uma republicação:

- **O intervalo tem de ter exatamente o número de linhas que você manda.** Mandar 47
  linhas para `A1:E46` é erro, não corte.
- **Linha curta não apaga as colunas da direita.** O script já devolve toda linha com a
  largura da aba; mande as linhas como vieram, sem encurtar.

## 3. Manter a formatação no lugar

O `values.update` **não apaga formatação** — então, enquanto o número de linhas não
mudar, a planilha continua bonita sozinha e este passo é rápido.

O que muda é o **número de pessoas**: entra ou sai gente, a linha de TOTAL anda, e aí o
cinza do total fica numa linha de pessoa e a última pessoa fica sem cinza. Por isso o
JSON traz `formato`, com a linha de cabeçalho e a de TOTAL de cada aba, já contadas.

Para cada aba em `formato`, se a linha de TOTAL **mudou** em relação à execução
anterior (compare lendo a planilha), aplique com `update_spreadsheet`:

- **linha de cabeçalho** (a que começa com "Pessoa"): negrito, texto branco, fundo
  `{"red":0.12,"green":0.22,"blue":0.39}`, centralizado.
- **linha de TOTAL**: negrito, fundo `{"red":0.93,"green":0.93,"blue":0.93}`.
- as linhas entre as duas: fundo branco, sem negrito.

Se a linha de TOTAL for a mesma da execução anterior, **não mexa na formatação** — é
trabalho à toa e cada escrita é uma chance de estragar o que está bom.

## 4. Conferir

Leia de volta `Agora!A1:B6` e `Por pessoa!A1:B8` e confira:

- **O carimbo de "Última execução" é o mesmo nas duas** e é o de agora. Carimbos
  diferentes significam que uma aba não foi escrita.
- **"CLIENTES NA FILA SEM NINGUÉM" é o mesmo número nas duas.** Ele vem de uma fonte só;
  se divergir, alguma aba ficou da execução anterior.

## 5. Relatar

Uma ou duas linhas, em português: quantos clientes na fila sem ninguém, quantas em
andamento, quantas pessoas atendendo, e a mais antiga esperando.

**Se a fila sem ninguém passar de 40, ou a mais antiga passar de 4 horas, destaque.**
Fora disso, não precisa alarmar: a fila oscila ao longo do dia, e é para isso que existe
a aba por hora.

---

## O que estes números são, para não os reinterpretar

- **CLIENTES NA FILA SEM NINGUÉM** — sessão aberta em que ninguém do suporte falou
  ainda. É cliente olhando a tela agora, e é o número que a gestão olha primeiro.
- **Em andamento** — sessão aberta, mas alguém já respondeu. Boa parte é sessão que
  ninguém encerrou, não cliente esperando. Não some os dois num total de "fila".
- **Atendendo / Concluiu**, por pessoa — conversa aberta em que a pessoa falou, e
  conversa encerrada em que ela falou. Transferência para quem nunca falou não conta
  para essa pessoa.
- **O backlog de chamados é outro relógio**: 1.160 abertos, mediana de 98 dias. Não é
  fila de atendimento e não muda de uma hora para outra.

## Armadilha que custou quatro correções publicadas

`imopenlines.session.history.get` devolve **50 mensagens** e avisa com `hasNextPage`; a
página seguinte vem com `LAST_ID`. O `pipeline/historico.py` já pagina, e todos os
leitores passam por ele. **Se for mexer em alguma contagem, não chame o endpoint direto.**
Sem paginar, o atendente que falou no começo da conversa some, conversa longa aparece
como não atendida, e a fila incha — chegou a mostrar 106 esperando onde eram 24.