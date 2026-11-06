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

## Um nulo numa planilha troca o tipo da coluna e quebra a comparação

Em 04/11/2026 a recoleta fez 164 das 180 conversas da V3 perderem a marcação. Causa:
o export daquele dia tinha **4 nulos** na coluna `LineId`, o pandas leu a coluna
inteira como float, e `str(17.0)` virou `"17.0"` — que não bate com `"17"`, a linha
da V3. A regra passou a classificar como V2 toda conversa que entrou pela linha da
V3. O relatório mostraria 18 conversas V3 em vez de 345.

É a **segunda vez** nesta base que um NaN do pandas muda o tipo de uma coluna e
corrompe uma decisão — a primeira foi `bool(nan) == True` marcando toda conversa
histórica como encerrada.

**Regra:** todo campo que vem de planilha e vira chave de comparação passa por uma
função de normalização própria, com teste. Nunca `str(valor)` direto.

**Como foi pego, e por que quase não foi:** o gerador acusou 99,7% em vez de 100%, e
161 registros sem classificação. Dava para ignorar — 0,3% parece arredondamento. Foi
ao perseguir *quais* 161 que a marcação quebrada apareceu. **Diferença pequena que
não deveria existir merece a pergunta "quais?", não um arredondamento.**

## Editar o store à mão pula o validador que você mesmo escreveu

No mesmo dia, realinhei 6 registros editando `leitura_completa.json` direto e gravei
um rótulo truncado — "Particularidade municipal de NFS-e" sem o resto do nome — que
não existe na taxonomia. O `absorver` teria recusado na hora; eu passei por fora dele.

**Regra:** depois de qualquer edição direta no store, rodar uma validação de todos os
rótulos contra as taxonomias. Foi o que achou o erro, e leva segundos.

## `write_text` do Python reescreve o arquivo inteiro no Windows

Editei cinco trechos de `criterios_leitura.md` com um script Python e o `git diff`
acusou **377 linhas mudadas**. Nenhuma edição minha; o `pathlib.write_text` usa a
tradução de newline padrão da plataforma e converteu as 219 linhas de LF para CRLF.

O risco não é cosmético: um diff de 377 linhas esconde as 5 que importam, e ninguém
revisa o que não consegue ler. Um critério errado passaria batido.

**Regra:** para editar arquivo de texto do repositório em script, usar
`write_bytes`, ou `open(..., newline="\n")`. E conferir o `--stat` depois: se o número
de linhas mudadas não parecer com o tamanho da edição, o problema é o arquivo, não a
edição.

## Medi "zero atendimentos em 1.069 conversas" e o zero era meu regex

Fui medir quantas conversas receberam o aviso de fila e depois foram atendidas. Deu
**0 de 1.069**. Publiquei? Não — porque zero absoluto numa operação com oito atendentes
é mais provável ser bug do que achado.

Era o rótulo: a transcrição escreve `Atendente (João Pedro)`, e meu regex pedia
`(Cliente|Atendente|\(sistema\)):` com dois-pontos logo depois. Nenhuma linha de
atendente casava. Com o rótulo certo, a resposta real apareceu — e era uma queda de 97%
para 17%, que é um achado de verdade, não um absurdo.

**Regra:** resultado extremo (0%, 100%, "nenhum", "todos") é hipótese de bug até ser
reproduzido por outro caminho. Antes de escrever o número, listar os valores que o campo
realmente tem — `collections.Counter` nos rótulos custa uma linha e teria mostrado
`Atendente (Nome)` de imediato.

**E o corolário, que foi o que salvou:** a linha de base é o melhor detector de bug de
medição que existe. Cinco meses entre 94% e 99% com a MESMA medição provaram que a
medição funciona e que a queda de novembro é real. Medição sem série histórica ao lado
não dá para distinguir de defeito de código.

## Portão de verificação que não tem com o que comparar nunca dispara

A tarefa agendada tinha duas travas que eu escrevi com confiança: "o total de registros
tem de ter crescido" e "as conversas da V3 só crescem; se despencaram, pare". Nenhuma das
duas podia funcionar — `base_historica.jsonl` está no .gitignore e a sessão das 9h nasce
sem memória, então não existia o número de ontem para comparar.

Pior que inúteis: **elas davam sensação de cobertura.** Uma delas é a trava do bug do
`str(17.0)`, que apagou a marcação V3 de 164 conversas e passou por um relatório inteiro.
Eu tinha escrito a trava e achado o assunto resolvido.

**Regra:** toda verificação que compara com "antes" precisa que alguém grave o "antes".
Ao escrever uma trava, pergunte de onde vem cada lado da comparação; se um dos lados não
existe em disco, a trava é decorativa.

**E prove que ela dispara.** Injetei uma linha de base falsa com 900 conversas V3 e
confirmei que o script acusa a queda e sai com 1. Trava não testada é trava não escrita —
vale para o `conferir_pipeline.py` também, que no primeiro teste deu falso positivo de si
mesmo.

## Instrução que manda "em caso de divergência, o outro arquivo manda"

O prompt da tarefa agendada dizia: leia a skill do projeto, e ela manda em caso de
divergência. Parecia prudente — uma fonte única de verdade. Era o contrário: a skill tem
660 linhas e metade descreve um pipeline aposentado, então a instrução mandava a execução
cega para a parte errada do arquivo, onde o comando é outro gerador.

**Regra:** prompt de execução autônoma é auto-contido ou não é. "O outro arquivo manda"
transfere a decisão para um texto que ninguém releu com essa execução em mente. Se dois
arquivos têm de concordar, o que garante isso é uma checagem que falha, não uma frase de
precedência.

## Três correções no mesmo número, e as duas primeiras erraram por não olhar a fonte

Em dois dias eu publiquei três versões da taxa de atendimento depois do aviso de fila:
37%, depois 84/37%, e por fim "não houve queda". As duas primeiras liam
`transcricoes.json`. A terceira perguntou à API.

Só que a terceira também está incompleta, e o motivo é o mesmo em outra camada:
`imopenlines.session.history.get` **pagina em 50 mensagens** e devolve `hasNextPage`.
Nem o `enriquecer_autores.py` nem o meu leitor ao vivo pediam a página seguinte. Numa
conversa de 50+ mensagens, o atendente costuma falar depois do começo — então as duas
leituras perdem exatamente as conversas longas, que são as mais atendidas.

O que isto ensina, e é o custo de três idas:

1. **Corrigir a conta sem questionar a fonte repete o erro.** Na segunda versão eu
   troquei o regex e me dei por satisfeito; a fonte era a mesma e seguia errada.
2. **Campo de paginação não é detalhe de implementação.** `hasNextPage`, `next`,
   `nextId` são a diferença entre "não achei" e "não procurei". Ao usar um endpoint novo,
   ler a lista de campos da resposta inteira **antes** de contar qualquer coisa — foi lá
   que estavam `message` (não `messages`), `tasks` dentro de `result`, e `hasNextPage`.
3. **Número que cai sempre merece mais desconfiança que número que sobe.** As três
   versões erraram para baixo, porque toda falha de leitura perde dado em vez de
   inventar. "Caiu" é o sintoma padrão de leitura incompleta.
4. **Enquanto não há resposta confiável, marque o artefato.** Pus o aviso na planilha
   antes de qualquer pessoa agir em cima da contagem por pessoa. Número errado sem aviso
   num painel que a gestão lê vale menos que número nenhum.
