# Prompt — consultar a planilha de paridade V2/V3 (chamados 107675 e 107719)

> Copie daqui para baixo e cole na conversa que gerou a planilha de paridade.

---

Preciso consultar a planilha de paridade V2/V3 que você gerou. Tenho dois chamados de cliente em aberto e quero saber **se essas duas diferenças já estão mapeadas na planilha** — não quero que você reanalise o código agora, quero uma busca na planilha e a resposta de achou / não achou.

Para cada um dos dois itens, me responda:

- **ACHEI** → identificação da linha (número, ID ou chave que a planilha usa), o texto da linha como está escrito lá, em que módulo/aba ela foi classificada, e qual veredito/status a planilha registrou para ela.
- **NÃO ACHEI, MAS O ESCOPO FOI COBERTO** → a área foi varrida e esta diferença não apareceu. Nesse caso me diga o que a planilha tem de mais próximo e por que não bateu.
- **NÃO ACHEI E O ESCOPO NÃO FOI COBERTO** → essa tela/rotina ficou fora da varredura. Diga explicitamente que é lacuna de cobertura, não ausência de divergência.

Essa distinção é o que mais me interessa: se a planilha não pegou, quero saber se é porque a diferença não existe ou porque ninguém olhou ali.

---

## Item 1 — Campo "Área" obrigatório barrando o agrupamento de serviços na OS

Chamado 107675 (cliente EXCELENTE SERVICOS AUTOMOTIVOS, ID 9896). A V3 bloqueia com esta mensagem:

```
Não foi possível agrupar os serviços. Os seguintes serviços estão sem área definida:
'BUCHAS E PRESILHAS', 'Pintar: CAPÔ', 'Pintar: PORTA DIANT ESQ', 'Rem./Inst: BANCO
DIANT ESQ', 'Rem./Inst: CAPÔ', 'Rem./Inst: FAROL ESQUERDO', 'Reparar: PORTA DIANT ESQ',
'TROCAR LATERAL TRAS ESQ', 'Troca/Rem./Inst: MOLDURA ESQ DO PARACHOQUE DIANT' [...]
```

São 26 serviços de lataria/pintura, numa OS com orçamento já autorizado. O analista de suporte registrou "não consegui localizar área" — ou seja, não achou na V3 onde informar esse dado.

Hipótese a conferir contra a planilha: na V2 o agrupamento de serviços não exigia área (ou a área vinha preenchida automaticamente, possivelmente por vir de orçamento importado — a nomenclatura "Pintar:", "Rem./Inst:", "Troca/Rem./Inst:" sugere importação, não digitação manual), e a V3 passou a exigir.

**Termos para buscar na planilha:** `área`, `sem área definida`, `agrupar serviços`, `agrupamento`, `obrigatoriedade`, `campo obrigatório`, e o cruzamento de `serviço` com `OS` / `ordem de serviço`.

**Cruzamento adicional que eu quero:** existe um chamado nosso já **fechado**, o 107487, que pedia "remover obrigatoriedade do campo 'Área' na inclusão de **peças digitadas** na Ordem de Serviço", com o cliente dizendo que na V2 o processo rodava sem informar área. Esse caso — área obrigatória em **peça digitada** — está na planilha? Se estiver e o caso de **serviço/agrupamento** não estiver, me diga se a planilha tratou isso como uma validação só ou como duas, porque na prática pode ser o mesmo ponto de código aparecendo em duas telas.

---

## Item 2 — Informações complementares do veículo não exibidas na OS

Chamado 107719 (cliente SR MOTORS SERVIÇOS AUTOMOTIVOS, ID 9173, contato Levi). Relato: *"Informações complementares dos veículos não são mostradas na o.s como na versão anterior e o cliente precisa dessas informações."*

O chamado veio sem OS de exemplo e sem vídeo — só dois prints. Então o relato é genérico: um bloco de dados do veículo que a V2 mostrava na tela da OS e a V3 não mostra.

**Termos para buscar na planilha:** `informações complementares`, `informações adicionais`, `dados do veículo`, `cadastro de veículo`, e os campos que normalmente compõem esse bloco — `chassi`, `motor`, `câmbio`, `combustível`, `cor`, `km`, `placa`, `renavam`, `observações`, `acessórios`, `campos personalizados`.

**O que preciso distinguir na resposta:**

1. A planilha registra campos do veículo que **existem na V2 e não existem na V3**?
2. Ou campos que **existem nas duas, mas não são exibidos na tela da OS da V3** (ficaram só no cadastro do veículo, ou foram para outra aba/modal)?
3. E a **impressão/PDF da OS** — a planilha cobriu o que sai impresso, ou só o que aparece em tela? Porque se a V2 imprimia esses dados e a V3 não imprime, é divergência mesmo que a tela mostre.

Se a planilha não separa "existe no modelo de dados" de "aparece na tela da OS", me diga isso — muda o que eu respondo pro cliente.

**Contexto que pode ajudar a localizar:** esse mesmo cliente (SR Motors, ID 9173, contato Levi) já abriu três chamados de paridade que foram **fechados** em 02/10/2026, todos no padrão "a versão anterior tinha":

| Chamado | Diferença relatada |
|---|---|
| 106903 | OS > Financeiro: tipo de documento não é aplicado a todas as parcelas; na V2 o campo ficava na área superior da tela, junto à forma de pagamento |
| 106905 | OS > Financeiro: campo "número de autorização" não existe na V3; na V2 existe e é usado na conciliação de cartão |
| 106909 | Financeiro: total das parcelas selecionadas não é exibido antes da liquidação múltipla; na V2 o total atualiza conforme seleciona |

Esses três estão na planilha? Se estiverem, me passe as linhas — serve de calibragem: se a planilha pegou esses três e **não** pegou o das informações do veículo, é sinal de que a varredura da tela de OS cobriu o bloco financeiro e deixou de fora os blocos de cadastro/veículo.

---

## Fechamento da resposta

Depois dos dois itens, duas perguntas curtas sobre a planilha em si:

1. **Qual o escopo real dela?** Que módulos e telas foram varridos, e quais ficaram de fora. Quero saber o tamanho do "não sei" antes de usar a planilha como referência de paridade.
2. **Como ela foi montada?** Comparação de código, de banco, de tela, de documentação? Isso define se a ausência de uma linha é evidência de que a diferença não existe, ou só de que o método usado não enxergaria aquele tipo de diferença.

Se para qualquer um dos dois itens a resposta for "não está na planilha e deveria estar", diga isso direto — é exatamente o que preciso saber.
