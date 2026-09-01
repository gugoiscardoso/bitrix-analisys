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
