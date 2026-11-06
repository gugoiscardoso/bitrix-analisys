# Análise do suporte Ultracar

Lê os chamados e as conversas do Bitrix24 e produz um relatório de onde o suporte
dói: um arquivo Excel com V2 e V3 juntos, fiscal e não-fiscal, chamados e conversas
de chat e WhatsApp, classificados por assunto e por módulo do produto.

O relatório oficial sai de `pipeline/gerar_relatorio_completo.py`. A receita completa,
com os critérios de classificação e os cuidados, está em
[`.claude/skills/build-report/SKILL.md`](.claude/skills/build-report/SKILL.md) — leia
esse arquivo antes de rodar qualquer coisa.

Há um segundo produto, que responde outra pergunta: `pipeline/gerar_atendimento.py` dá
**quantas conversas e chamados cada pessoa atendeu** num dia, com comparativo dos dias
anteriores. O relatório conta fricção do cliente; este conta trabalho da equipe. São
arquivos separados de propósito — juntos, convidam a ler um pelo outro.

Os dois saem sozinhos todo dia às 9h, pela tarefa agendada `relatorio-suporte-diario`.

---

## O que está no git e o que não está

Esta é a decisão de projeto que mais importa entender:

**Está versionado todo o julgamento.** São **70.733 classificações** acumuladas —
cada registro lido e rotulado por assunto e por módulo, mais as taxonomias e os
critérios de fronteira. É o que custou caro e o que não se regenera:

| Arquivo | Conteúdo |
|---|---|
| `data/store/leitura_completa.json` | 18.716 leituras (assunto + módulo) |
| `data/store/classificacao.json` | 26.224 classificações fiscais |
| `data/store/classificacao_nao_fiscal*.json` | 25.539 não-fiscais |
| `data/store/classificacao_v3.json` | 254 da V3 |
| `data/store/criterios_leitura.md` | as regras de fronteira, injetadas em todo prompt |
| `data/store/taxonomia*.json` | as quatro listas de assunto |
| `data/store/modulo_por_rotulo.json` | mapa determinístico rótulo → módulo |

**Não está versionado nada que se refaz com um comando**, por tamanho:
`data/raw/` (os exports do Bitrix), `data/store/base_historica.jsonl` (47 MB),
`remetentes.json` (19 MB) e `transcricoes.json` (50 MB).

A consequência prática: **um clone limpo recupera o julgamento de graça e só precisa
refazer a parte mecânica.** Nenhuma releitura, nenhum custo de LLM.

---

## Começando do zero, num clone limpo

Precisa de **.NET 10 SDK** (o coletor) e **Python 3.12+**.

```bash
pip install -r requirements.txt
dotnet build Ultracar-Support-Bitrix-Analisys
```

Depois, o caminho completo. Os tempos são medidos, não estimados:

```bash
# 1. coletar o período inteiro        ~5 h para 10 meses (medido: 10 min / 7 dias)
./Ultracar-Support-Bitrix-Analisys/bin/Debug/net10.0/Ultracar-Support-Bitrix-Analisys.exe \
    --mode all --from 2026-01-01 --to 2026-11-05

# 2. quem falou cada mensagem         ~55 min do zero, incremental depois
python pipeline/enriquecer_autores.py

# 3. status atual dos chamados abertos  segundos (~20 chamadas de API)
#    Sem este passo a coluna Status fica a do dia da coleta, e chamado que fechou
#    depois aparece como aberto. Medido em 05/11: 84 de 1.051 já estavam fechados.
python pipeline/atualizar_status.py

# 4. consolidar                       ~5 min
python pipeline/consolidar_store.py

# 5. conferir que nada ficou por ler  deve dizer FALTA LER: 0
python pipeline/ler_pendentes.py status

# 6. gerar o relatório do período
python pipeline/gerar_relatorio_completo.py --de 2026-01-01 --ate 2026-11-05

# 7. e, se quiserem o atendimento por pessoa, UM dia fechado
python pipeline/gerar_atendimento.py --dia 2026-11-05 --compara 10
```

O passo 5 **tem de dar zero**. Se der mais que zero, são registros novos, e aí o
pipeline de leitura entra — está descrito no skill. Classificação já feita volta pelo
cache: o hash é do texto, e recoletar o mesmo período não invalida nada (verificado em
04/11, recoletando por cima de um dia já lido).

Cerca de **6 horas de máquina**, sem ninguém olhando.

## No dia a dia

Mesma sequência, só mudando a janela do passo 1 para o que falta desde a última
coleta — veja `data/store/coleta.json`. Leva minutos em vez de horas.

---

## Antes de clonar isto para outro lugar

**`Ultracar-Support-Bitrix-Analisys/appsettings.json` está no repositório com o token
do webhook do Bitrix dentro.** Quem tiver o clone tem acesso de **leitura** ao Bitrix da
Ultracar.

A outra credencial do projeto, a da conta de serviço do Google, **não está versionada**:
ela vive em `local/sheets.env`, que está no `.gitignore`. A diferença entre as duas não é
capricho — o token do Bitrix só lê; a chave do Google **escreve** em toda planilha
compartilhada com a conta `ultracar-report-chat-ai@…`, inclusive a do relatório do N1,
que não é deste projeto.

**Num clone novo, o `publicar_relatorio.py` não roda até alguém repor a chave.** Ele diz
isso com todas as letras quando falta, e o valor está em
`ultracar-support-ai/Infrastructure.EndInactiveConversations.Job/Properties/launchSettings.json`,
na variável `GOOGLE_SHEETS_CREDENTIALS_JSON`. O id da planilha, que não é segredo, segue
no appsettings.



Isso é conveniente — a coleta funciona sem configurar nada — e é um segredo versionado.

**Decidido em 04/11/2026: fica como está**, porque o repositório é privado e restrito
ao time. A conveniência de clonar e rodar vale mais que o risco nesse perímetro.

A decisão depende do perímetro, não do arquivo. **Se o repositório for para outra
pessoa, outra organização ou um host público, o token tem de ser revogado no Bitrix** —
tirá-lo do arquivo não basta, porque ele continua em todo o histórico de commits
anteriores. Revogar é a única saída, e é mais barato decidir isso antes de o repo
circular do que depois.

---

## Avisos que vêm da experiência

O `tasks/lessons.md` guarda os erros que já custaram caro aqui. Três que atingem quem
for mexer no pipeline:

- **Campo de planilha que vira chave de comparação nunca passa por `str()` direto.**
  Um único nulo faz o pandas trocar o tipo da coluna inteira. Já aconteceu duas vezes:
  `bool(nan)` marcando toda conversa como encerrada, e `str(17.0)` apagando a marcação
  V3 de 164 conversas.
- **Não edite os arquivos de `data/store/` à mão.** O `absorver` valida cada rótulo
  contra as taxonomias; editar direto pula essa checagem e grava rótulo inválido.
- **Quatro a seis subagentes simultâneos na leitura, não mais.** Acima disso o limite
  de sessão derruba todos de uma vez.
