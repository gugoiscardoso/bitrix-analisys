#!/usr/bin/env python
"""Aplica a reclassificação de tema e prepara a etapa 2 só para quem mudou.

Regra central: tema igual ao que já estava -> não mexe em nada, o subgrupo continua
válido. Tema diferente -> grava tema+frente novos, limpa o subgrupo (que era da frente
antiga e não vale mais) e enfileira para a etapa 2.

Assim a etapa 2 custa proporcional ao que mudou, não ao universo. Roda com
--dry-run primeiro para ver o impacto antes de gravar.
"""
import argparse, collections, json, shutil, sys, io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AUD = Path(__file__).resolve().parent
RAIZ = AUD.parents[1]
STORE = RAIZ / "data" / "store"
DEST = AUD / "reclass"
sys.path.insert(0, str(RAIZ / "pipeline"))
from classificar import frentes_com_quebra, montar_prompt_subgrupo, hash_texto

ap = argparse.ArgumentParser()
ap.add_argument("--dry-run", action="store_true")
a = ap.parse_args()

tax = json.loads((STORE / "taxonomia.json").read_text(encoding="utf-8"))
TEMA_FRENTE = {t["nome"]: t["frente"] for t in tax["temas"]}
ESP = {"Outro / não se encaixa", "Conversa vazia / sem conteúdo útil",
       "Não fiscal (falso positivo)"}
COM_QUEBRA = set(frentes_com_quebra(tax))
cls = json.loads((STORE / "classificacao.json").read_text(encoding="utf-8"))

textos = {}
for lote in DEST.glob("R_*.json"):
    if lote.name.startswith("resp_"):
        continue
    tipo = "chamado" if "_chamado_" in lote.name else "conversa"
    for it in json.loads(lote.read_text(encoding="utf-8")):
        textos[(tipo, str(it["id"]))] = it["t"]

VALIDOS = set(TEMA_FRENTE) | ESP


def desmojibake(s: str) -> str:
    """Conserta UTF-8 relido como Latin-1 ('validaÃ§Ã£o' -> 'validação').

    Um subagente gravou a resposta com a codificação errada e 217 rótulos
    semanticamente CERTOS seriam descartados como inválidos, deixando esses
    registros com o tema antigo sem ninguém notar. Reparar é melhor que perder:
    a alternativa era reclassificar de novo, pagando IA por um erro de encoding.
    """
    if s in VALIDOS:
        return s
    try:
        cand = s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s
    return cand if cand in VALIDOS else s


respostas = sorted(DEST.glob("resp_R_*.json"))
print(f"respostas encontradas: {len(respostas)}")
novo = {}
invalidos, reparados = [], 0
for p in respostas:
    tipo = "chamado" if "_chamado_" in p.name else "conversa"
    for rid, nome in json.loads(p.read_text(encoding="utf-8")).items():
        rid = str(rid)
        limpo = desmojibake(nome)
        if limpo != nome:
            reparados += 1
        if limpo in VALIDOS:
            novo[(tipo, rid)] = limpo
        else:
            invalidos.append(limpo)
if reparados:
    print(f"  {reparados} rótulos reparados de mojibake (encoding, não classificação)")

mudou, igual, fluxo = [], 0, collections.Counter()
for (tipo, rid), tema_novo in novo.items():
    chave = "chamados" if tipo == "chamado" else "conversas"
    d = cls[chave].get(rid)
    if not d or d.get("fonte") == "manual":
        continue
    if d["tema"] == tema_novo:
        igual += 1
        continue
    mudou.append((chave, tipo, rid, tema_novo))
    fluxo[(d["tema"][:30], tema_novo[:30])] += 1

n = len(novo)
print(f"julgados: {n}  | invalidos ignorados: {len(invalidos)}")
print(f"  tema mantido : {igual} ({igual/max(1,n)*100:.1f}%)")
print(f"  tema MUDOU   : {len(mudou)} ({len(mudou)/max(1,n)*100:.1f}%)")

atual = collections.Counter()
depois = collections.Counter()
for chave in ("chamados", "conversas"):
    for d in cls[chave].values():
        atual[d.get("frente")] += 1
for chave, tipo, rid, tema in mudou:
    depois[cls[chave][rid].get("frente")] -= 1
    depois[None if tema in ESP else TEMA_FRENTE.get(tema)] += 1
print("\n  impacto por frente (saldo):")
for f, v in sorted(depois.items(), key=lambda x: -abs(x[1]))[:8]:
    if v:
        print(f"    {str(f):6} {v:+5}   ({atual[f]} -> {atual[f]+v})")
print("\n  maiores fluxos:")
for (de, para), q in fluxo.most_common(6):
    print(f"    {q:4}x  {de} -> {para}")

if a.dry_run:
    print("\n(dry-run: nada gravado)")
    raise SystemExit(0)

shutil.copy(STORE / "classificacao.json", STORE / "classificacao.json.pre_reclass")
pend = collections.defaultdict(list)
for chave, tipo, rid, tema in mudou:
    d = cls[chave][rid]
    frente = None if tema in ESP else TEMA_FRENTE.get(tema)
    d["tema"], d["frente"] = tema, frente
    d["hash"] = hash_texto(textos.get((tipo, rid), ""))
    d["fonte"] = "llm"
    if frente in COM_QUEBRA:
        d["subgrupo"] = ""
        pend[frente].append({"id": rid, "tipo": tipo, "t": textos.get((tipo, rid), "")})
    else:
        d["subgrupo"] = tema if frente else ""
(STORE / "classificacao.json").write_text(
    json.dumps(cls, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"\ngravado. backup em classificacao.json.pre_reclass")

FILA = STORE / "_fila"
FILA.mkdir(exist_ok=True)
for f in FILA.glob("*"):
    f.unlink()
lotes = 0
for frente, itens in sorted(pend.items()):
    (FILA / f"prompt_sub_{frente}.md").write_text(
        montar_prompt_subgrupo(tax, frente), encoding="utf-8")
    for i in range(0, len(itens), 250):
        lotes += 1
        (FILA / f"lote_sub_{frente}_{i//250+1}.json").write_text(
            json.dumps(itens[i:i + 250], ensure_ascii=False, indent=1), encoding="utf-8")
(FILA / "etapa.json").write_text(json.dumps({"etapa": 2}), encoding="utf-8")
print(f"ETAPA 2: {sum(len(v) for v in pend.values())} registros em {lotes} lote(s), "
      f"{len(pend)} frente(s)")
