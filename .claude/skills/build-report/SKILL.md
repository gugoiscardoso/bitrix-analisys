---
name: build-report
description: Gera o relatório de fricção fiscal do suporte Ultracar para um período. Coleta o que falta no Bitrix, classifica apenas os registros novos e produz o relatório executivo e a base unificada em report/. Use quando o usuário pedir para gerar/atualizar o relatório fiscal, ou invocar /build-report.
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

### 4. Gerar a saída

```
python pipeline/gerar_relatorio.py --de <de> --ate <ate>
```

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
