#!/usr/bin/env python
"""Teste de integração do classificador de duas etapas, sem chamar IA.

Tira alguns registros do cache, roda preparar -> absorver -> absorver simulando as
respostas do classificador, e confere que tema, frente e subgrupo voltam corretos.
Restaura o cache no fim, sempre — inclusive se falhar no meio.
"""
import json, sys, io, shutil, subprocess, collections
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[2]
STORE = RAIZ / "data" / "store"
FILA = STORE / "_fila"
CLS = STORE / "classificacao.json"
BAK = STORE / "classificacao.json.teste_bak"
sys.path.insert(0, str(RAIZ / "pipeline"))
from classificar import frentes_com_quebra

DE, ATE = "2026-05-01", "2026-08-05"
tax = json.loads((STORE / "taxonomia.json").read_text(encoding="utf-8"))
COM_QUEBRA = frentes_com_quebra(tax)
TEMA_FRENTE = {t["nome"]: t["frente"] for t in tax["temas"]}


def rodar(*args):
    r = subprocess.run([sys.executable, str(RAIZ / "pipeline" / "classificar.py"), *args],
                       capture_output=True, text=True, encoding="utf-8", cwd=RAIZ)
    print("   " + (r.stdout or "").strip().replace("\n", "\n   "))
    if r.returncode:
        print("   STDERR:", (r.stderr or "")[:400])
    return r.returncode


# A fila é área de trabalho compartilhada com a produção, e este teste a limpa no
# fim. Rodar com uma fila viva destrói lotes em andamento — aconteceu em 07/08/2026:
# apagou 14 lotes da etapa 2 no meio do voo e as respostas já gravadas. Agora a fila
# é guardada inteira antes e devolvida depois.
FILA_BAK = FILA.parent / "_fila_teste_bak"
if FILA_BAK.exists():
    shutil.rmtree(FILA_BAK)
if FILA.exists() and any(FILA.iterdir()):
    shutil.copytree(FILA, FILA_BAK)
    print(f"fila de produção com {len(list(FILA.iterdir()))} arquivo(s) — guardada\n")

shutil.copy(CLS, BAK)
try:
    cache = json.loads(CLS.read_text(encoding="utf-8"))
    # só registros DENTRO da janela: preparar filtra por data, então pegar de fora
    # faria o teste acusar "sumiu do cache" para algo que nunca deveria ser enfileirado.
    na_janela = set()
    with (STORE / "base_historica.jsonl").open(encoding="utf-8") as fh:
        for linha in fh:
            r = json.loads(linha)
            if DE <= r["data"] <= ATE:
                na_janela.add((r["tipo"], str(r["id"])))
    # OS DOIS TIPOS, obrigatoriamente. A primeira versão deste teste só pegava conversa
    # e por isso não viu o bug em que a etapa 2 mandava todo chamado para o cache errado
    # (o lote da etapa 2 é nomeado pela frente, não pelo tipo). 27 de 27 chamados foram
    # descartados em produção antes de alguém notar.
    alvos = []
    for chave, tipo in (("conversas", "conversa"), ("chamados", "chamado")):
        vistos = collections.Counter()
        n0 = len(alvos)
        for rid, d in cache[chave].items():
            if (tipo, rid) not in na_janela:
                continue
            f = d.get("frente")
            if vistos[f] < 2 and f in (*COM_QUEBRA, "P10", "P11", None):
                alvos.append((chave, rid, dict(d)))
                vistos[f] += 1
            if len(alvos) - n0 >= 8:
                break
    for chave, rid, _ in alvos:
        del cache[chave][rid]
    CLS.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"removidos {len(alvos)} registros do cache "
          f"(frentes: {sorted({str(d['frente']) for _, _, d in alvos})}, "
          f"tipos: {dict(collections.Counter(c for c, _, _ in alvos))})\n")

    print("1) preparar")
    rodar("preparar", "--de", DE, "--ate", ATE)
    etapa = json.loads((FILA / "etapa.json").read_text(encoding="utf-8"))["etapa"]
    assert etapa == 1, f"esperava etapa 1, veio {etapa}"

    print("\n2) simular resposta da etapa 1 (devolve o tema original)")
    esperado = {rid: d for _, rid, d in alvos}
    chave_de = {rid: c for c, rid, _ in alvos}
    for lote in FILA.glob("lote_tema_*.json"):
        resp = {str(it["id"]): esperado[str(it["id"])]["tema"] for it in json.loads(
            lote.read_text(encoding="utf-8")) if str(it["id"]) in esperado}
        (FILA / f"resp_{lote.stem}.json").write_text(
            json.dumps(resp, ensure_ascii=False), encoding="utf-8")
        print(f"   {lote.name}: {len(resp)} respostas simuladas")

    print("\n3) absorver etapa 1")
    rodar("absorver")

    print("\n4) simular resposta da etapa 2 (devolve o subgrupo original)")
    n2 = 0
    for lote in FILA.glob("lote_sub_*.json"):
        itens = json.loads(lote.read_text(encoding="utf-8"))
        resp = {}
        for it in itens:
            rid = str(it["id"])
            sub = esperado[rid].get("subgrupo") or "Outro / não se encaixa"
            resp[rid] = sub
        (FILA / f"resp_{lote.stem}.json").write_text(
            json.dumps(resp, ensure_ascii=False), encoding="utf-8")
        n2 += len(resp)
        print(f"   {lote.name}: {len(resp)} respostas simuladas")
    print(f"   total na etapa 2: {n2}")

    print("\n5) absorver etapa 2")
    rodar("absorver")

    print("\n6) conferência")
    final = json.loads(CLS.read_text(encoding="utf-8"))
    ok, erros = 0, []
    for chave, rid, d in alvos:
        novo = final[chave].get(rid)
        if not novo:
            erros.append(f"{rid}: sumiu do cache")
            continue
        # Frente de tema único agora recebe subgrupo = tema automaticamente. Registros
        # antigos dessas frentes estão com subgrupo vazio (herança da dissolução de P9),
        # então o esperado ali é o tema, não o vazio que está no cache.
        esperado_sub = d.get("subgrupo") or ""
        if not esperado_sub and d.get("frente") and d["frente"] not in COM_QUEBRA:
            esperado_sub = d["tema"]
        # Os catch-all por frente ('Outros/heterogêneos' em P1/P2/P3, 'Outro / não
        # classificado' em P7/P8) são a mesma coisa que a saída genérica 'Outro': o
        # absorver normaliza os cinco para vazio, que é o que alimenta a métrica de
        # deriva. Unificar é o comportamento desejado, não defeito.
        if esperado_sub.startswith("Outro"):
            esperado_sub = ""
        if novo["tema"] != d["tema"]:
            erros.append(f"{rid}: tema {novo['tema']!r} != {d['tema']!r}")
        elif novo["frente"] != d["frente"]:
            erros.append(f"{rid}: frente {novo['frente']} != {d['frente']}")
        elif (novo.get("subgrupo") or "") != esperado_sub:
            erros.append(f"{rid}: subgrupo {novo.get('subgrupo')!r} != {esperado_sub!r}")
        else:
            ok += 1
    print(f"   {ok}/{len(alvos)} registros voltaram idênticos")
    for e in erros:
        print(f"   FALHA {e}")
    print(f"\n   etapa.json removido no fim: {not (FILA/'etapa.json').exists()}")
    print(f"   fila limpa: {not list(FILA.glob('lote_*.json'))}")
    print("\nRESULTADO:", "PASSOU" if not erros else "FALHOU")
finally:
    shutil.move(str(BAK), str(CLS))
    for f in FILA.glob("*"):
        f.unlink()
    if FILA_BAK.exists():
        for f in FILA_BAK.iterdir():
            shutil.copy(f, FILA / f.name)
        shutil.rmtree(FILA_BAK)
        print("cache restaurado, fila de produção DEVOLVIDA")
    else:
        print("cache restaurado, fila limpa")
