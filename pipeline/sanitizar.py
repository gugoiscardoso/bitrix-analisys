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
_SENHA = re.compile(r"((?:senha|password|pwd|pass)\s*[:=]\s*)(\S{4,60})", re.IGNORECASE)

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
        if _NAO_E_SENHA.match(valor.strip(".,;:)")):
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
