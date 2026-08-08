#!/usr/bin/env python
"""Gera os prompts dos avaliadores da auditoria.

Tres prompts, cada um com o minimo necessario:
  tema_chamado / tema_conversa  -> so os 23 temas (sem as 69 descricoes de subgrupo)
  subgrupo                      -> o prompt de producao integral (montar_prompt)
  fiscal                        -> julgamento binario para as camadas D1/D2

Regra replicada da producao: P8 nao existe para chamado; 'Conversa vazia' e
'Nao fiscal' so existem para conversa. Sem isso a auditoria mediria uma
diferenca de prompt, nao um erro de classificacao.
"""
import json, sys, io, collections
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "pipeline"))
OUT = Path(__file__).resolve().parent / "prompts"
OUT.mkdir(exist_ok=True)

tax = json.loads((RAIZ / "data" / "store" / "taxonomia.json").read_text(encoding="utf-8"))
titulos = {f["tag"]: f["titulo"] for f in tax["frentes"]}
VAZIA = "Conversa vazia / sem conteúdo útil"
FALSO = "Não fiscal (falso positivo)"

SAIDA = """
## Saída
Responda APENAS com um bloco JSON, um objeto mapeando id -> rótulo escolhido:
```json
{"101793": "<nome exato>", "101797": "<nome exato>"}
```
Use a string EXATA da lista. Todo id do lote deve aparecer. Nada além do JSON.

## Eficiência
Leia o lote UMA vez e escreva a saída UMA vez. Não releia o arquivo nem imprima o conteúdo.
"""


def prompt_tema(tipo: str) -> str:
    rotulo = "chamado de suporte" if tipo == "chamado" else "conversa de chat"
    campo = "título e descrição" if tipo == "chamado" else "transcrição"
    por_frente = collections.defaultdict(list)
    for t in tax["temas"]:
        por_frente[t["frente"]].append(t["nome"])
    L = [f"# Classificação fiscal por TEMA — {rotulo}s (Ultracar)", "",
         f"Cada item tem `id` e `texto` ({campo}). Atribua a CADA item EXATAMENTE UM tema",
         "da lista abaixo, usando a string EXATA. Não invente categorias.", ""]
    for tag in sorted(k for k in por_frente if k):
        if tipo == "chamado" and tag == "P8":
            continue          # P8 so existe no chat
        if tipo == "conversa" and tag == "P5":
            continue          # 'Sem causa identificavel' nunca foi oferecido a conversa:
                              # 0 de 6.376 usam. Oferecer aqui mediria diferenca de prompt.
        L.append(f"## {tag} — {titulos.get(tag, '')}")
        L += [f'- "{n}"' for n in por_frente[tag]]
        L.append("")
    # Espelha exatamente o que o prompt de PRODUÇÃO oferece. 'Não fiscal' passou a valer
    # para chamado quando o filtro deixou de ser circular (9.1); auditar sem essa opção
    # mediria diferença de prompt, não erro — foi assim que a camada B saiu viciada.
    L += ["## Casos especiais", ""]
    if tipo == "conversa":
        L += [f'- "{VAZIA}" — sem assunto identificável: só saudação, chat abandonado,',
              "  atendimento resolvido sem descrever o problema."]
    L += [f'- "{FALSO}" — o assunto real não é fiscal (financeiro puro, estoque, acesso);',
          "  o termo fiscal apareceu de passagem.", ""]
    L += ["## Regras",
          "- Classifique pela CAUSA CENTRAL, não por palavras soltas.",
          "- Se o item toca dois temas, escolha o que dominou o atendimento.",
          "- Julgue só pelo texto. Não presuma o que não está escrito.",
          SAIDA]
    return "\n".join(L)


def prompt_fiscal() -> str:
    return """# Triagem: o item é FISCAL? (Ultracar, ERP automotivo)

Cada item tem `id` e `texto`. Decida se o assunto CENTRAL do atendimento é fiscal.

**É fiscal** — nota fiscal (NF-e/NFC-e/NFS-e/MDF-e/CT-e) em qualquer etapa: emissão,
rejeição, cancelamento, devolução, transmissão, status na SEFAZ/prefeitura; DANFE/PDF
da nota; impostos e tributação (ICMS/ISS/PIS/COFINS/IBS/CBS, alíquota, retenção);
cadastro fiscal (NCM, CFOP, CST, código de serviço, regime, SPED, SINTEGRA);
certificado digital; XML de compra, importação e manifestação do destinatário;
numeração/inutilização de RPS/DPS; homologação municipal.

**NÃO é fiscal** — financeiro puro (boleto, contas a pagar/receber, conciliação
bancária), estoque e compras sem nota, ordem de serviço, orçamento, cadastro de
cliente/peça, acesso e senha, agendamento. O termo fiscal aparecer de passagem
não torna o item fiscal: o que vale é o assunto central.

Na dúvida real entre os dois, responda "duvidoso".

## Saída
APENAS um bloco JSON, id -> "fiscal" | "nao_fiscal" | "duvidoso":
```json
{"102557": "fiscal", "101859": "nao_fiscal"}
```
Todo id do lote deve aparecer. Nada além do JSON.

## Eficiência
Leia o lote UMA vez e escreva a saída UMA vez. Não releia o arquivo.
"""


from classificar import montar_prompt
(OUT / "tema_chamado.md").write_text(prompt_tema("chamado"), encoding="utf-8")
(OUT / "tema_conversa.md").write_text(prompt_tema("conversa"), encoding="utf-8")
(OUT / "fiscal.md").write_text(prompt_fiscal(), encoding="utf-8")
(OUT / "subgrupo_conversa.md").write_text(
    montar_prompt(tax, "conversa").replace(
        "Cada item tem `id` e `t` (transcrição)",
        "Cada item tem `id` e `texto` (transcrição)") + "\n" + SAIDA, encoding="utf-8")

for p in sorted(OUT.glob("*.md")):
    n = len(p.read_text(encoding="utf-8"))
    print(f"{p.name:24} {n:6} chars ~= {n/3.5:6.0f} tokens")
