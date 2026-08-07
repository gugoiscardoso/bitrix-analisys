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

### 3. Classificar apenas o que é novo

```
python pipeline/classificar.py preparar --de <de> --ate <ate>
```

Se disser "Nada a classificar", **pule direto para o passo 4** — o relatório sai inteiro do cache.

Se houver pendências, o comando escreve em `data/store/_fila/`:
- `prompt_chamado.md` e/ou `prompt_conversa.md` — as instruções, geradas da taxonomia
- `lote_<tipo>_<n>.json` — os lotes de até 250 itens

Para cada lote, lance um subagente com esta instrução, substituindo os nomes:

> Siga exatamente as instruções de `data/store/_fila/prompt_<tipo>.md`, processando o arquivo
> `data/store/_fila/lote_<tipo>_<n>.json`. Máxima economia de tokens: leia o lote uma única vez
> e escreva a saída uma única vez. Grave o JSON em UTF-8 sem BOM.

Lance no máximo 6 subagentes em paralelo. Se houver mais lotes, faça em ondas — disparar muitos
de uma vez já estourou o limite de cota antes e derrubou 12 de 16 lotes.

Quando todos terminarem:
```
python pipeline/classificar.py absorver
```
A absorção grava lote a lote, então uma queda no meio não perde o que já entrou. Se algum lote
falhar, relance só ele e rode `absorver` de novo.

### 4. Gerar a saída

```
python pipeline/gerar_relatorio.py --de <de> --ate <ate>
```

### 5. Reportar ao usuário

Diga, de forma direta:
- o período e quantos registros fiscais ele tem (chamados e conversas)
- quantos vieram do cache e quantos foram classificados agora
- **a deriva** (`python pipeline/classificar.py status --de <de> --ate <ate>`) e, se passar de
  10%, avise explicitamente que a taxonomia precisa de subgrupos novos — foi assim que
  descobrimos IPI, pendência no portal e devolução com IBS/CBS
- onde ficaram os dois arquivos

Entregue os arquivos com SendUserFile.

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
