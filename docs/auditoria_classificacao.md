# Auditoria da classificação — fricção fiscal Ultracar

> **Este é o diagnóstico, não o estado atual.** Os números abaixo mediram a base como ela
> estava em 07/08/2026 de manhã. As correções que eles motivaram foram aplicadas no mesmo
> dia (fases 9.x em [`planejamento_build_report.md`](planejamento_build_report.md)), e uma
> nova auditoria de amostra sobre a base corrigida mede **13,6% de erro** (0,0% em chamado,
> 17,4% em conversa; n=59, kappa 0,872) — contra os ~24% relatados aqui.
>
> O que **não** mudou: o topo do ranking continua sendo empate estatístico. A leitura por
> bloco de frentes segue valendo; a leitura por posição exata, não.

Período auditado: 01/05/2026 a 05/08/2026.
Executada em 07/08/2026 sobre `data/store/classificacao.json` (522 chamados, 6.376 conversas).
Artefatos reprodutíveis em `pipeline/_auditoria/` (semente `20260807`).

## Veredito

**A classificação de chamados se sustenta. A de conversas não.** E o filtro que
define o que entra na análise perde ~1 em cada 7 conversas fiscais.

A priorização **muda**: P1 deixa de ser a frente nº 1.

---

## 1. Desenho

Amostra aleatória estratificada por frente, rótulo removido do lote (cego).
**Dois avaliadores independentes** sobre a amostra inteira, em contextos separados,
com os lotes embaralhados por sementes diferentes para que nenhum par de itens caísse
junto para os dois.

A leitura de cada camada usa três números:

| Métrica | O que significa |
|---|---|
| erro por consenso (A==B≠armazenado) | os dois avaliadores concordam entre si **e** contra o rótulo → erro provável do dado |
| ambiguidade (A≠B) | os avaliadores discordam **entre si** → a fronteira é mal definida; culpa da taxonomia, não de quem executou |
| kappa de Cohen | concordância entre avaliadores descontado o acaso |

Dois vieses do próprio desenho foram detectados e corrigidos antes de medir:

- **Chamados com `fonte: chat`** (causa recuperada da conversa cruzada) foram excluídos.
  Os avaliadores não veem o chat; contá-los mediria a cegueira do auditor. Na amostra,
  **6 de 6 apareciam como "erro"** — os 17 do universo são informação real, não ruído.
- **`Sem causa identificável na descrição`** foi removido do prompt de conversa. Esse tema
  aparece **0 vezes** nas 6.376 conversas, ou seja, nunca foi oferecido ao classificador
  original. Oferecê-lo inflava o erro da camada B de 21,9% para 23,9% — diferença de prompt
  disfarçada de erro de dado. A camada B foi refeita do zero.

---

## 2. Taxa de erro por camada

| Camada | n | Universo | Erro (consenso) | IC95 | Ambiguidade | Kappa |
|---|---:|---:|---:|---|---:|---:|
| A — tema de chamado | 144 | 522 | **10,4%** | ±4,3pp | 7,6% | 0,917 |
| B — tema de conversa | 201 | 6.376 | **21,9%** | ±5,6pp | 9,0% | 0,903 |
| C — subgrupo de conversa *(condicional)* | 150 | 4.535 | **13,3%** | ±5,4pp | 9,3% | 0,903 |

A camada C mede acurácia **condicional**: dado que a frente está certa, o subgrupo está
certo? Foi feita com lotes por frente e só os ~8 subgrupos daquela frente, replicando as
condições em que o rótulo foi produzido. Dar as 69 opções mediria uma tarefa mais difícil
que a original.

**O erro composto do subgrupo de conversa** é o que vai para o relatório:

```
P(frente certa) × P(subgrupo certo | frente certa)
     0,781      ×          0,867          = 0,677
```

→ **~32% dos subgrupos de conversa estão errados.** Cerca de 1 em 3.

### O que isso responde das suas preocupações

| Sua preocupação | Veredito |
|---|---|
| 1. LLM dos 522 chamados nunca auditada | **Refutada como problema grave.** 10,4% de erro, kappa 0,92. A concordância de 72% com a regex não provava nada, mas o resultado é bom por outro caminho: a 2ª rodada de fato consertou a regex. |
| 2. 6.376 conversas por tema nunca auditadas | **Confirmada e séria.** 21,9%, o dobro dos chamados. |
| 3. 4.914 subgrupos nunca auditados | **Confirmada.** 13,3% condicional, ~32% composto. |
| 4. Inconsistência entre lotes | **Refutada como causa principal.** Kappa 0,90–0,92 em todas as camadas: dois avaliadores independentes concordam muito. Se os critérios de desempate variassem de forma relevante, a ambiguidade seria alta — ela é 7–9%. O problema é execução, não desempate. **Exceção estrutural em §4.** |
| 5. Falsos negativos do filtro nunca medidos | **Confirmada, e é o maior achado.** Ver §3. |
| 6. Truncamento | **Refutada.** O digest não tem 400–700 chars: mediana 554, p95 1.201, e só **3 de 6.376** encostam no teto de 2.200. O caractere não corta. Ver a correção abaixo sobre a mensagem. |

> **Correção ao item 6 (07/08/2026, mesma sessão).** Este relatório afirmou que "59,8%
> das conversas fiscais têm mais de 25 mensagens" e tratou isso como exposição relevante
> ao corte do digest. **O número está errado.** Ele veio do campo `mensagens` do Bitrix,
> que conta todas as mensagens — saudação, transferência, boilerplate. O corte de 25 do
> digest se aplica às linhas **depois** do filtro de boilerplate. Reconstruindo a
> transcrição dos 201 registros da camada B a partir do XLSX bruto (reprodução conferida:
> bate 201/201 com a base), apenas **22,4%** excedem 25 linhas reais, e remover o corte
> por completo aumenta o conteúdo em só **1,2x** (mediana 518 → 551 chars). A exposição
> real ao truncamento é pequena.
| 7. Taxonomia de P7/P8 vinda de amostra | **Parcialmente confirmada, por motivo diferente.** O erro de subgrupo em P7 é 16,0% e em P8 15,6% — acima da média, mas não catastrófico. O problema real de P7 é estrutural (§4). |

---

## 3. Falsos negativos do filtro fiscal — o maior achado

### 3.1 O filtro de chamados é circular

`consolidar_store.py:261`:

```python
fiscal = tid in tema_chamado      # tema_chamado vem de class_final_v2.json
```

O regex de ~40 palavras-chave é aplicado **só a conversas** (`:301`). Para chamado,
"é fiscal" significa "já está no arquivo de classificação legado". A validação registrada
como *"filtro fiscal refeito do zero, bate exatamente com as 6.376 conversas"* é verdadeira
e cobre conversas; para os 522 chamados ela é **verdadeira por construção**.

### 3.2 Bug latente de produção

`classificar.py:158` só enfileira `if r["fiscal"]`. Como nenhum chamado novo está no arquivo
legado, **nenhum chamado novo jamais será classificado**. O teste de idempotência celebrado
na Fase 2 ("6.895 reusados, 0 a classificar") é exatamente o que esse bug produz — ele não
distingue "nada novo" de "incapaz de ver o novo". Toda execução futura da skill herda isso.

### 3.3 Quanto o filtro perde

| | n | Fiscal de fato (consenso) | Kappa |
|---|---:|---:|---:|
| Chamados descartados, **batem** no regex | 60 | **38,3%** [27–51] | 0,887 |
| Chamados descartados, **não batem** | 90 | **0,0%** [0–4] | 0,851 |
| Conversas descartadas | 150 | **15,3%** [10–22] | 0,955 |

**Chamados:** reponderado (76 batem + 642 não batem) → **~29 chamados fiscais perdidos**.
Os 522 deveriam ser ~551 (**+6%**). O regex em si é bom: fora do que ele pega, o falso
negativo é **zero**. O problema é que ele nunca foi aplicado a chamados.

**Conversas:** **~1.059 conversas fiscais perdidas** [721–1.516]. As 6.376 deveriam ser
~7.435 (**+17%**). Em relação à população fiscal verdadeira, o filtro perde **~14%**.

> **Limitação honesta:** os avaliadores de D1/D2 julgaram só "é fiscal ou não", sem atribuir
> frente. **Não sei onde essas 1.059 conversas cairiam.** Se estiverem concentradas numa
> frente, o ranking da §5 muda mais ainda. Isso não está incluído nos números da §5.

---

## 4. Pares confundidos e um defeito estrutural da taxonomia

### O erro não é aleatório — é direcional

Fluxo líquido por tema (consenso dos dois avaliadores):

| Camada | Tema | Saiu | Entrou | Líquido | Base |
|---|---|---:|---:|---:|---:|
| A | Rejeição/erro de validação | 8 | 0 | **−8** | 23 (−35%) |
| B | Rejeição/erro de validação | 14 | 1 | **−13** | 44 (−30%) |
| B | Particularidade municipal de NFS-e | 1 | 6 | +5 | 12 |
| B | Nota travada em processamento | 2 | 6 | +4 | 6 |
| B | Certificado digital | 0 | 3 | +3 | 8 |
| B | Instabilidade geral / lentidão | 5 | 1 | −4 | 8 |

**`Rejeição/erro de validação` é um atrator.** Em ambas as fontes ele perde ~1/3 do próprio
volume e quase não recebe nada. É o tema âncora de P1 — a frente nº 1. O erro do classificador
inflou sistematicamente exatamente a prioridade nº 1.

### Os pares que você suspeitava

| Par suspeito | Veredito |
|---|---|
| devolução × rejeição de validação | **Real, mas menor.** 1x em A, 1x em B na direção rejeição→devolução. |
| nota presa × status dessincronizado | **Não é o par.** O par real é **instabilidade geral × nota travada** (4x em B, +2x ambíguo). |
| how-to × configuração assistida | **Real.** `Configuração assistida` tem saldo −2 e é o 2º maior emissor em B; 3x vai para certificado digital, 3x para particularidade municipal. |
| tema × "Outro" | **Não confirmado como erro.** O que aparece é o inverso: subgrupo vazio em P1 (15,5%) e P7 (10,8%) — omissão, não escolha errada. |

### Defeito estrutural: P1 e P7 têm o mesmo subgrupo

| Frente | Subgrupo | Volume |
|---|---|---:|
| P1 | `CFOP/CST incompatíveis com a operação ou regime (devolução, idDest...)` | 411 (29,2% de P1) |
| P7 | `CFOP, CST/CSOSN e regime tributário incompatíveis` | 120 (13,9% de P7) |

O mesmo problema de fundo tem dois destinos legítimos. E o subgrupo nº 1 de P7 —
`Destaque manual de impostos para bater com o espelho do fornecedor` (23,7%) — é um
problema de **cálculo de imposto**, que é a definição de P3.

Isso não é erro de execução: **a taxonomia permite duas respostas certas.** Nenhum ajuste
de prompt conserta; exige bump de versão fundindo ou disjuntando esses subgrupos.

### P9 não é uma frente

P9 é a 2ª maior (1.189) e tem **0% de subgrupos** — 100% dos registros sem subgrupo, nos
dois lados. É um balde residual competindo por posição de roadmap com frentes acionáveis.

---

## 5. Impacto na priorização — o que muda

Reordenação aplicando os saldos medidos por consenso (chamados + conversas):

| # atual | Frente | n atual | | # novo | Frente | n estimado | var |
|---:|---|---:|---|---:|---|---:|---:|
| 1 | P1 | 1.489 | → | 1 | **P9** | 1.228 | +3,3% |
| 2 | P9 | 1.189 | → | 2 | **P1** | 1.048 | **−29,6%** |
| 3 | P8 | 994 | → | 3 | **P6** | 943 | **+38,3%** |
| 4 | P7 | 885 | → | 4 | P7 | 885 | 0,0% |
| 5 | P6 | 682 | → | 5 | **P8** | 867 | −12,8% |
| 6 | P2 | 608 | → | 6 | P2 | 770 | +26,7% |

**Quatro frentes trocam de posição:**

- **P1 cai de 1º para 2º** e perde ~30% do volume. A frente nº 1 do roadmap era inflada.
- **P6 sobe de 5º para 3º** (+38%). Homologação municipal + certificado digital estava
  subdimensionada — é o principal destino do que saiu de P1.
- **P2 cresce 27%** sem mudar de posição.
- **P9 vira nº 1** — mas isso é artefato de balde residual, não descoberta. Não trate como
  prioridade: trate como sinal de que 1.228 registros estão sem diagnóstico acionável.

**Conclusão de decisão:** a ordem P1 > P9 > P8 > P7 > P6 **não se sustenta**. A leitura
defensável dos dados atuais é que **P6 e P2 estão subdimensionadas e P1 superdimensionada**,
e que P9 precisa ser quebrada em subgrupos antes de entrar em qualquer comparação.

---

## 6. O que fazer, em ordem

1. **Corrigir o bug do filtro de chamados** (`consolidar_store.py:261`). Aplicar `FISCAL_RE`
   a título+descrição como já se faz com conversas. Sem isso a skill nunca classifica chamado
   novo. É correção de código, não de dado.
2. **Ampliar o filtro de conversas.** Ele perde ~14% da população fiscal. Medir onde as 1.059
   caem antes de refazer a priorização — é a maior incerteza restante.
3. **Reclassificar as conversas.** 21,9% de erro de tema é alto demais para sustentar
   roadmap. Os chamados (10,4%) podem ficar.
4. **Bump de taxonomia** resolvendo P1×P7 (CFOP/CST duplicado), P7×P3 (destaque de impostos)
   e quebrando P9 em subgrupos.
5. **Não congelar roadmap** em cima da ordem atual das frentes.

## 7. O que esta auditoria não cobre

- Onde caem as 1.059 conversas fiscais perdidas (§3.3).
- Subgrupos de **chamado** — 100% de P9 e P7 em chamado estão sem subgrupo, então não havia
  o que auditar nessas frentes.
- Efeito do corte de 25 mensagens sobre a causa raiz (§2, item 6): medido como exposição
  (59,8%), não como erro.
- Os 401 falsos positivos já marcados pela IA não foram reavaliados.
