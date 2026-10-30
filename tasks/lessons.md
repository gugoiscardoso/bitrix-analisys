# Lições

Regras escritas depois de errar. Revisar no início de sessão.

---

## Pare de refinar quando a conclusão já está tomada

**07/08/2026 — correção do usuário:** *"to na dúvida se vc tá no caminho certo ou se está
viajando ou em overengineering."*

Ele estava certo. A auditoria pedida e os dois bugs que travavam o pipeline estavam
prontos de manhã. Depois disso vieram dissolução de P9, fronteira de CFOP, divisão de P7,
subgrupos de P10–P13, classificador de duas etapas e reclassificação de 6.898 registros —
tudo medido e defensável, e tudo com retorno decrescente. O efeito na conclusão que ia
para o chefe (*"P1 inflada, P6 subdimensionada, o topo é empate"*) foi quase nulo.

**Regra:** quando a pergunta original estiver respondida, dizer isso em voz alta e
perguntar se vale continuar — em vez de emendar a próxima melhoria porque ela é medível.
"Consigo medir que melhora" não é o mesmo que "muda a decisão".

## Data é fato verificável — cheque o relógio, não o contexto

**31/08/2026 — correção do usuário:** *"eu tinha pedido até o dia 31. hoje é dia 31, acho
que vc tava com uma data desatualizada."*

Meu contexto trazia `currentDate: 2026-08-08` e eu tratei como verdade. Pior: **construí
um argumento técnico em cima da premissa errada** — expliquei que a janela até 31/08
mediria recência contra data futura, mostrei uma tabela de 22 subgrupos mudando de "Ativa"
para "Atenção", e recomendei a janela de 08/08. O raciocínio estava certo e a conclusão
invertida, porque a premissa estava errada.

O efeito prático: o usuário ficou 23 dias com o relatório errado e com 24 dias de dados
não coletados, achando que estava em dia.

**Regra:** antes de qualquer decisão que dependa de hoje — janela de relatório, "está
desatualizado?", "isso é futuro?" — rode `date`. Custa um comando. Contexto de sessão
envelhece; relógio de máquina, não.

**Regra mais geral:** quando eu montar um argumento sofisticado a partir de um único dado
que não verifiquei, a sofisticação não valida o dado. Ela só torna o erro mais
convincente.

## Volume pequeno muda como classificar, não se classifica

**23/10/2026 — correção do usuário:** *"ainda assim queremos classificar os chamados da V3.
Pq 69 pra uma pessoa analisar já é muito."*

Propus, para os registros da V3, "listar e agrupar à mão" em vez de rodar o classificador,
porque eram poucos. Ele leu como "o entregável vem cru" — e a leitura estava certa, porque
foi isso que eu escrevi. O que eu queria dizer era que a *taxonomia* sairia da leitura em
vez de vir da fiscal, e que não precisaria da fila de lotes. Duas coisas diferentes
embrulhadas numa frase só.

Pior: "poucos registros" é a minha régua, não a dele. 54 linhas é pouco para quem vai
processá-las com script e é muito para quem vai abrir a planilha e tentar enxergar padrão.
O número que importa é o do leitor.

**Regra:** o entregável chega sempre classificado e agrupado. O volume decide de onde vem a
taxonomia e por qual máquina ela roda — nunca se existe rótulo. E ao propor "mais simples",
dizer o que *sai*, não só o que entra.

## Número que mudou de regra tem de ser recontado

**23/10/2026, na mesma conversa:** disse "~44 conversas V3" por três mensagens seguidas.
Esse número era 20 da linha 17 + 24 com vínculo de chat — mas eu já tinha decidido, com
argumento e tudo, **descartar** o vínculo de chat por reetiquetar conversa antiga. Pela regra
que eu mesmo fechei são 20 + 9 transferidas = **29**. Carreguei o número velho para dentro do
plano e do arquivo de entregáveis.

É o mesmo defeito do "número derivado, nunca cravado à mão", numa variante mais traiçoeira:
o número não estava cravado no código, estava cravado **na minha própria mensagem anterior**.

**Regra:** quando a regra de contagem muda, recontar na hora e corrigir onde o número velho
já foi escrito. Repetir um número de uma mensagem anterior é cravá-lo à mão.

## Auditar classificador: replicar o prompt que gerou o rótulo

Errei duas vezes na mesma sessão.

1. Ofereci aos avaliadores um tema (`Sem causa identificável`) que o classificador
   original nunca teve. Inflou o erro de 21,9% para 23,9% — diferença de prompt disfarçada
   de erro de dado. Camada B teve de ser refeita.
2. Chamei de "experimento natural" uma comparação em que mudei prompt **e** população ao
   mesmo tempo. Não isolava nada.

**Regra:** antes de auditar, verificar empiricamente o que o classificador original podia
responder (ex.: um tema com 0 ocorrências em 6.376 provavelmente não estava no prompt). E
em teste pareado, mudar **uma** variável — mesma população, mesmo gabarito.

## Nunca rodar teste destrutivo contra diretório de trabalho vivo

Rodei `teste_duas_etapas.py` com 14 lotes de produção em andamento. O `finally` limpava
`data/store/_fila/` sem olhar e apagou os lotes no meio do voo, junto com cinco lotes de
trabalho concluído.

**Regra:** teste que mexe em área compartilhada guarda e devolve o que encontrou, ou se
recusa a rodar. E não rodar teste enquanto há trabalho em voo sobre os mesmos arquivos.

## "Está pronto?" se responde verificando, não afirmando

Perguntado se estava tudo certo, fui checar e achei três coisas: mensagem de validação
com número cravado à mão que envelheceu, 8,5 MB de lixo entrando no commit, e um
diretório de trabalho fora do `.gitignore`. A correção de uma delas quebrou o script por
falta de `import` — peguei porque rodei.

**Regra:** confirmação de prontidão exige executar. Rodar o pipeline inteiro em sequência
custa segundos.

## Marcar script de uso único como perigoso

Sete scripts desta sessão mutaram `data/store/` e já foram executados. Ficaram numa pasta
parecendo scripts normais. `dividir_p7.py` rodado de novo procuraria um subgrupo que ele
próprio eliminou.

**Regra:** migração executada leva aviso explícito no LEIA-ME da pasta, separada do que é
reutilizável.

## Número derivado, nunca cravado à mão

`consolidar_store` imprimia `(esperado 152: P7 e P9)` e `gerar_relatorio` tinha a ordem
das frentes numa lista fixa — que descartava silenciosamente qualquer frente nova (1.107
registros sumiram assim). Os dois envelheceram no primeiro bump de taxonomia.

**Regra:** contagem e enumeração saem da taxonomia em tempo de execução. Se precisar de
lista curada, ela recebe no fim o que não estiver nela — nunca descarta.

## Campo que nunca vem vazio não está medindo o que você acha

Precisava marcar "conversa ainda em andamento" e usei `fechado_em`: parecia óbvio, o nome
diz. Escrevi a coluna, escrevi o aviso no Resumo, escrevi a frase explicando ao usuário
por que o número ia aparecer alto. Só então medi: 53 conversas V3 do dia, **zero** em
andamento. O coletor preenche `EndedAt` com o timestamp da última mensagem, com o
`END_TIME` da activity só como reserva — e toda sessão tem mensagem, então o campo nunca
vem vazio. A coluna ia responder "não" para sempre, no relatório inteiro, sem errar
visivelmente nada. O sinal verdadeiro era outro campo que o coletor nem buscava.

**Regra:** antes de usar um campo como sinal de ausência, olhe o código que o preenche.
E rode a contagem dos dois lados: um sinal binário que dá 100%/0% numa amostra onde você
esperava mistura é defeito do sinal, não descoberta sobre o mundo.

## Fuso se prova por registro, não se assume por sistema

A base guarda conversa em UTC e chamado em hora de Brasília — três horas de diferença,
dentro do mesmo arquivo, sem nada no código avisando. Em janela de meses ninguém vê. O
pedido era "hoje a partir das 8h", e o filtro ingênuo teria pegado conversa desde as 5h da
manhã e chamado desde as 8h: duas janelas diferentes somadas no mesmo número.

Suspeitei pelo histograma de criação (chamado pica 08h-18h, conversa 11h-21h), mas
histograma é indício. A prova foi pedir a mesma sessão à API e comparar: export
`10:16:46`, API `13:16:47+03:00`.

**Regra:** janela com hora exige confirmar o fuso de **cada fonte** contra a origem, um
registro concreto de cada lado. E o Bitrix não é coerente consigo mesmo: `crm.activity`
devolve `+03:00`, `tasks.task` devolve `-03:00`.

## Coluna nova em fonte mesclada: o NaN antigo mente

Acrescentei `SessionClosed` ao coletor e li com `bool(r.get("SessionClosed"))`. O
consolidador concatena dez exports: a coluna passa a existir para todos, com `NaN` nas
43 mil linhas antigas — e `bool(nan)` é `True`. Toda conversa histórica seria marcada como
encerrada, calado.

**Regra:** ao ler coluna que só existe nos arquivos novos, teste o valor (`pd.isna`), não
a existência da coluna. E distinga os três estados: sim, não, e não sei.

## Paralelismo de subagentes tem teto, e o teto é da sessão

Em 30/10/2026, classificando 69 lotes de 250 registros, subi de 6 para 9 subagentes
simultâneos achando que o custo de orquestração era o único limite. Seis lotes
morreram juntos com `rate_limit` HTTP 429 — "session limit". Não foi custo, foi
concorrência: o teto é da sessão inteira, somando todos os agentes, e estoura de uma
vez em todos em vez de enfileirar.

O prejuízo foi pequeno só por sorte de projeto: os seis falharam ANTES de gravar, e
`ler_pendentes.py` recalcula o que falta a partir do que está gravado, não de uma
lista fixa. Se o pipeline tivesse estado em memória, teria perdido tudo.

**Regra:** 4 a 6 subagentes simultâneos em trabalho longo. Antes de subir, pergunte o
que se perde se todos morrerem ao mesmo tempo — e se a resposta não for "nada",
não suba.

**Regra que valeu mais que a anterior:** trabalho longo grava no caminho e recalcula o
que falta pelo estado em disco. Tanto a leitura quanto `enriquecer_autores.py` foram
escritos assim, e foi isso que transformou uma queda de seis agentes em um reinício de
dois minutos.
