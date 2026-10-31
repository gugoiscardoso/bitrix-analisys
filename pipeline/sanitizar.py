# -*- coding: utf-8 -*-
"""Higieniza o texto que vai para os arquivos de report/.

Chamado e conversa de suporte carregam credencial de cliente em texto claro: o
analista pede o acesso para entrar no sistema e aquilo fica gravado no Bitrix. Medido
em 23/10/2026 sobre 46.347 registros: 138 com senha aparentemente em claro, 129 em
conversa e 9 em chamado.

A base histórica guarda o texto como veio — ela é local, está no .gitignore e o
classificador precisa do texto íntegro. Quem é compartilhado é report/, e é ali que a
máscara entra. Por isso esta função é aplicada na hora de escrever a planilha, não na
hora de consolidar.
"""
from __future__ import annotations
import re

# "senha: x", "Senha = x", "pwd: x". O valor vai até o fim da palavra.
#
# Três furos medidos em 30/10/2026 sobre 47.589 registros — 49 dos 196 com padrão de
# senha escapavam, entre eles senha de certificado digital e senhas de app do Gmail:
#
#   1. Qualificador entre a palavra e os dois-pontos. "Senha de APP: ..." e "Senha do
#      certificado: ..." não casavam porque o `:` não vinha colado. A lista de
#      qualificadores abaixo saiu da própria base, não da imaginação: medindo os 196
#      casos, só "de app" e "do certificado" aparecem de verdade. Mantê-la curta é o
#      que impede o padrão de engolir frases como "a senha não funciona: vou ver".
#   2. Valor de 3 caracteres. O mínimo era 4 e deixava passar 31 registros com
#      "Senha: 123".
#   3. Espaço NÃO-QUEBRÁVEL dentro do valor. Senha de app do Gmail vem como quatro
#      grupos separados por \xa0, que `\S` trata como espaço — a captura parava no
#      primeiro grupo e mascarava um quarto da senha. Daí o `_NAO_ESPACO` abaixo
#      listar os brancos de verdade em vez de usar `\S`.
_NAO_ESPACO = r"[^ \t\n\r\f\v]"
# Allowlist de qualificador não funcionou: medindo os casos que escapavam, o conector
# entre "senha" e o valor é prosa livre — "padrão para", "era esse", "do login",
# "criada", "é", "de instalação", "anydesk". Então o qualificador é largo e quem
# segura o falso positivo é a trava do VALOR, em `troca`. Pontuação de frase corta o
# qualificador, o que já descarta a maior parte da prosa.
_QUALIFICADOR = r"[^\n:=,.;!?]{0,40}"
_SENHA = re.compile(
    r"((?:senha|password|pwd|pass)" + _QUALIFICADOR + r"[:=]\s*)"
    r"(" + _NAO_ESPACO + r"{3,80})",
    re.IGNORECASE)

# O valor não é senha quando é outra coisa identificável. Sem estas travas, o
# qualificador largo mascara URL, CNPJ e telefone que aparecem perto da palavra senha.
_VALOR_NAO_E_SENHA = re.compile(
    # `//...` porque o `:` que o padrão casa costuma ser o do próprio "https:", e aí
    # o valor começa nas barras em vez do esquema.
    r"^(?://|https?://|www\.)"                   # link
    r"|^\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}$"    # CNPJ
    r"|^\d{3}\.?\d{3}\.?\d{3}-?\d{2}$"           # CPF
    r"|^\(?\d{2}\)?9?\d{4}-?\d{4}$",             # telefone
    re.IGNORECASE)

# Valores que não são senha: o texto segue falando sobre a senha, não a informa.
_NAO_E_SENHA = re.compile(
    r"^(?:do|da|de|e|ou|no|na|nova|antiga|nao|n[aã]o|correta|errada|incorreta|certa|"
    r"aqui|qual|essa|esta|esse|para|pra|com|sem|que|the|is)$",
    re.IGNORECASE)


def mascarar_credenciais(texto: str) -> str:
    """Troca o valor de senha por [SENHA REMOVIDA], preservando o resto do texto.

    O rótulo fica visível de propósito: quem lê o relatório precisa saber que ali havia
    uma credencial — é isso que torna o problema visível para quem pode corrigi-lo na
    origem.
    """
    if not texto:
        return texto

    def troca(m: re.Match) -> str:
        valor = m.group(2)
        limpo = valor.strip(".,;:)")
        if _NAO_E_SENHA.match(limpo) or _VALOR_NAO_E_SENHA.match(limpo):
            return m.group(0)
        return m.group(1) + "[SENHA REMOVIDA]"

    return _SENHA.sub(troca, texto)


def contar_credenciais(textos) -> int:
    """Quantos textos da sequência tinham credencial. Para log, não para decisão."""
    n = 0
    for t in textos:
        if t and mascarar_credenciais(t) != t:
            n += 1
    return n
