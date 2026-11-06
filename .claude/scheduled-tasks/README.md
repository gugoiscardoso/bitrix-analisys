# Cópia do prompt da tarefa agendada

`relatorio-suporte-diario.md` é uma **cópia versionada** do prompt que roda todo dia às
9h. O original — o que o agendador lê de verdade — fica fora do repositório, em:

```
C:\Users\Lucas\.claude\scheduled-tasks\relatorio-suporte-diario\SKILL.md
```

Isto existe porque aquele arquivo não é versionado nem tem backup. Ele carrega as travas
de verificação, os critérios de entrega e as armadilhas da base; perder o perfil do
usuário perderia a automação inteira, sem rastro.

**O original manda.** Esta cópia é backup e serve para revisar a mudança num diff.

Depois de editar o original, atualize a cópia e confira:

```bash
cp "$USERPROFILE/.claude/scheduled-tasks/relatorio-suporte-diario/SKILL.md" \
   .claude/scheduled-tasks/relatorio-suporte-diario.md
python pipeline/conferir_pipeline.py
```

O `conferir_pipeline.py` compara os dois byte a byte e acusa se divergirem — era deriva
silenciosa, agora é erro.
