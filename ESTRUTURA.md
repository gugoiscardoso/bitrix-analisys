# Estrutura de pastas

Organizada por **quem escreve e quem pode apagar**. Essa é a regra que mantém a saída limpa.

| Pasta | Quem escreve | Pode apagar? | Conteúdo |
|---|---|---|---|
| `data/raw/` | coletor C# | **Sim** — é cache | Exports brutos do Bitrix (chamados em JSON, conversas em XLSX). Regeneráveis a qualquer momento rodando o coletor. |
| `data/store/` | pipeline | **Não** — fonte da verdade | Base histórica, cache de classificação, taxonomia. É o que garante que o relatório seja reproduzível e que a IA não reclassifique o que já foi classificado. |
| `report/` | skill `/build-report` | Sim — é gerado | **Saída oficial da skill.** Sempre sobrescrito. Nada além disso entra aqui. |
| `docs/` | humano | Não | Artefatos curados: plano de ação revisado, relatórios de análise, navegador HTML. A skill **nunca** escreve aqui. |
| `pipeline/` | dev | Não | Scripts Python que transformam `data/` em `report/`. |
| `Ultracar-Support-Bitrix-Analisys/` | dev | Não | Coletor C# que fala com a API do Bitrix. |
| `local/` | você | Sim | Espaço pessoal, fora do git. Análises e arquivos de trabalho que não interessam ao time. |

## Saída da skill

Exatamente dois arquivos por execução, com o período no nome:

```
report/relatorio_executivo_<de>_<ate>.xlsx    frentes, subgrupos e métricas (sem plano de ação)
report/base_unificada_<de>_<ate>.xlsx         chamados e conversas classificados, linha a linha
```

## Regra de leitura do período

**Janela pura.** Tudo que o relatório mostra — contagens, médias, última incidência, cores de recência — considera apenas registros dentro de `--de`/`--ate`. A régua de recência é relativa ao `--ate`, não à data de execução.

Consequência intencional: rodar o relatório de junho hoje ou daqui a seis meses dá o mesmo resultado. Para perguntar "isso ainda está vivo?", rode com `--ate` = hoje (o padrão).

## Os três arquivos canônicos de `data/store/`

Gerados por `pipeline/consolidar_store.py`, que reconstrói tudo a partir de `data/raw/`.

**`taxonomia.json`** — 13 frentes, 23 temas e 69 subgrupos, congelados e versionados. O prompt do classificador é *gerado* deste arquivo, então é idêntico em toda execução e a IA nunca inventa categoria: o que não encaixa vai para "Outro". Alterar exige bump de versão.

**`classificacao.json`** — o cache que garante consistência. Uma entrada por chamado/conversa com tema, subgrupo, frente, origem (`llm`, `chat`, `manual`) e o hash do texto classificado. Na execução, quem já está aqui é **reusado sem chamar IA**; só o que é novo entra na fila de classificação. Entradas com origem `manual` são imunes a reprocessamento.

**`base_historica.jsonl`** — um registro por linha (15.935 hoje: 2.653 chamados e 13.282 conversas), com os campos usados nas métricas: datas de abertura, início de desenvolvimento, alteração e fechamento; status, canal, cliente, CNPJ, duração, mensagens e o texto.

`data/store/_legado/` guarda os 38 arquivos da análise exploratória que deram origem a esses três. Servem só de rastreabilidade e podem ser apagados quando a consolidação estiver comprovada em uso.

## O que ainda falta para a skill funcionar

- `pipeline/` tem caminhos absolutos apontando para o scratchpad da sessão em que os scripts foram escritos. Só `consolidar_store.py` já usa caminho relativo à raiz; os demais precisam do mesmo tratamento.
- O coletor C# aceita `--mode` e `--from`; faltam `--to` e busca incremental por `>=CHANGED_DATE`, que traz de uma vez os chamados novos e os que mudaram de status.
- Falta o classificador incremental: ler o cache, separar o que é novo, classificar só isso e gravar de volta.
- `output/problemas_2026-08-05.xlsx` ficou onde estava por não ter sido gerado pelo pipeline.
