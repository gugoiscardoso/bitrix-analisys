# Scripts da análise exploratória

Estes são os scripts que produziram a análise original de fricção fiscal (mai–ago/2026)
e os artefatos curados em `docs/`: o plano de ação, o navegador HTML, o artefato de
propostas e os dois relatórios em markdown.

**Não fazem parte do pipeline automatizado.** A saída oficial da skill `/build-report`
é gerada por `pipeline/gerar_relatorio.py`, que lê o store canônico.

## Limitações conhecidas

- Têm caminhos absolutos apontando para o scratchpad da sessão em que foram escritos.
  Não rodam de outra máquina sem ajuste.
- Dependem da ordem em que foram executados na sessão original.
- `acoes.py` guarda o texto das ações da fase exploratória; a versão revisada e válida
  está em `docs/acoes_user.json`.

## Quando usar

Só para regenerar os artefatos curados de `docs/`, e nesse caso vale corrigir os caminhos
antes. Para o relatório periódico, use o pipeline novo.
