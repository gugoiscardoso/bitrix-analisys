# -*- coding: utf-8 -*-
"""Confere que a skill e a tarefa agendada rodam o MESMO pipeline.

O prompt da tarefa agendada é auto-contido: ele não lê a skill. Isso é bom (a tarefa
roda sozinha, sem depender do repositório estar num estado específico) e é perigoso —
quem acrescenta um passo na skill e esquece a tarefa deixa o job rodando o pipeline
antigo, e ninguém percebe, porque ele entrega um arquivo que parece certo.

Aconteceu em 05/11 com o `atualizar_status.py`: o passo nasceu na skill e só não ficou
esquecido no job porque eu estava com os dois arquivos abertos.

Este script substitui o aviso por uma checagem. Rode-o depois de mexer no pipeline.

    python pipeline/conferir_pipeline.py        # sai 1 se divergirem
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SKILL = RAIZ / ".claude" / "skills" / "build-report" / "SKILL.md"
JOB = Path.home() / ".claude" / "scheduled-tasks" / "relatorio-suporte-diario" / "SKILL.md"

# O bloco da skill que vale é só o da ordem oficial: o resto do arquivo cita os
# geradores legados de propósito, e eles não devem entrar na comparação.
INICIO = "## A ordem"
FIM = "## Como classificar um lote"

COMANDO = re.compile(r"python pipeline/[a-z_]+\.py|Ultracar-Support-Bitrix-Analisys\.exe")

# Este script não é passo do pipeline: é a checagem. Citá-lo num dos dois arquivos
# apareceria como divergência — foi o primeiro falso positivo que ele deu de si mesmo.
IGNORAR = {"python pipeline/conferir_pipeline.py"}


def comandos(texto: str) -> set[str]:
    return set(COMANDO.findall(texto)) - IGNORAR


def main() -> int:
    problemas: list[str] = []

    if not SKILL.exists():
        print(f"ERRO: não achei a skill em {SKILL}")
        return 1
    if not JOB.exists():
        print(f"ERRO: não achei a tarefa agendada em {JOB}")
        print("  Se ela foi removida de propósito, apague este script também.")
        return 1

    sk = SKILL.read_text(encoding="utf-8")
    try:
        bloco = sk[sk.index(INICIO): sk.index(FIM, sk.index(INICIO))]
    except ValueError:
        print(f"ERRO: não achei a seção '{INICIO}' … '{FIM}' na skill.")
        print("  A skill foi reorganizada; ajuste INICIO/FIM aqui.")
        return 1

    na_skill = comandos(bloco)
    no_job = comandos(JOB.read_text(encoding="utf-8"))

    for falta, onde in ((na_skill - no_job, "está na skill e NÃO na tarefa agendada"),
                        (no_job - na_skill, "está na tarefa agendada e NÃO na skill")):
        for c in sorted(falta):
            problemas.append(f"{c} — {onde}")

    # Um comando citado que não existe em disco derruba o pipeline no meio.
    for c in sorted(na_skill | no_job):
        if c.startswith("python pipeline/") and not (RAIZ / c.split(" ", 1)[1]).exists():
            problemas.append(f"{c} — citado, mas o arquivo não existe")

    # A cópia versionada do prompt da tarefa tem de ser idêntica ao original. O
    # original mora fora do repositório e não tem backup; a cópia é o único rastro
    # se o perfil do usuário se perder, e cópia que envelhece em silêncio não é backup.
    copia = RAIZ / ".claude" / "scheduled-tasks" / "relatorio-suporte-diario.md"
    if not copia.exists():
        problemas.append(f"{copia.relative_to(RAIZ)} — a cópia versionada do prompt "
                         "da tarefa não existe")
    elif copia.read_bytes() != JOB.read_bytes():
        problemas.append(
            f"{copia.relative_to(RAIZ)} — divergiu do original em {JOB}. "
            "Copie o original por cima (o original manda).")

    print(f"ordem oficial da skill: {len(na_skill)} comandos")
    print(f"tarefa agendada:        {len(no_job)} comandos")
    if problemas:
        print("\nDIVERGÊNCIA:")
        for p in problemas:
            print(f"  - {p}")
        print("\nOs dois têm de rodar o mesmo pipeline. Corrija o que faltar.")
        return 1
    print("\nOK: os dois rodam o mesmo pipeline.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
