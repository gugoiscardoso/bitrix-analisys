#!/usr/bin/env python
"""9.3.2 — aplica o consenso dos dois avaliadores à fronteira P1 × P7.

Só move quem os DOIS avaliadores colocaram do mesmo lado. Onde discordam, ou onde
algum respondeu '?', o rótulo atual fica e o caso é sinalizado: a lição da auditoria
é que discordância entre leitores independentes indica fronteira mal definida, e
trocar rótulo com um voto só é ruído com cara de correção.

Mover de frente muda TRÊS campos — frente, subgrupo e tema. O tema sai da taxonomia
enriquecida, não de constante escrita à mão.
"""
import json, sys, io, glob, collections, shutil
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AUD = Path(__file__).resolve().parent
STORE = AUD.parents[1] / "data" / "store"

SUB = {"P1": "CFOP/CST incompatíveis com a operação ou regime (devolução, idDest, grupos de imposto)",
       "P7": "CFOP, CST/CSOSN e regime tributário incompatíveis"}

tax = json.loads((STORE / "taxonomia.json").read_text(encoding="utf-8"))
TEMA = {}
for s in tax["subgrupos"]:
    if s["nome"] in SUB.values():
        TEMA[s["nome"]] = s.get("tema")
faltando = [n for n in SUB.values() if not TEMA.get(n)]
if faltando:
    print(f"ERRO: tema não derivável para {faltando}. Rode consolidar_store.py e "
          f"classificar.py status para enriquecer a taxonomia.")
    raise SystemExit(1)


def carregar(av):
    o = {}
    for p in glob.glob(str(AUD / "respostas" / f"{av}_CFOP_*.json")):
        for k, v in json.loads(Path(p).read_text(encoding="utf-8")).items():
            o[str(k)] = v
    return o


a, b = carregar("av1"), carregar("av2")
gab = json.loads((AUD / "cfop_gabarito.json").read_text(encoding="utf-8"))
cache = json.loads((STORE / "classificacao.json").read_text(encoding="utf-8"))

mov, mantidos, disc, interr, faltou = collections.Counter(), 0, [], [], 0
for k, m in gab.items():
    tipo, rid = k.split("|")
    chave = "chamados" if tipo == "chamado" else "conversas"
    va, vb = a.get(rid), b.get(rid)
    if va is None or vb is None:
        faltou += 1
        continue
    if "?" in (va, vb):
        interr.append((rid, va, vb))
        continue
    if va != vb:
        disc.append((rid, m["frente_atual"], va, vb))
        continue
    d = cache[chave].get(rid)
    if not d:
        continue
    if d.get("fonte") == "manual":       # curadoria humana é intocável
        mantidos += 1
        continue
    if va == d["frente"]:
        mantidos += 1
        continue
    mov[(d["frente"], va)] += 1
    d["frente"] = va
    d["subgrupo"] = SUB[va]
    d["tema"] = TEMA[SUB[va]]
    d["fonte"] = "llm"

total = sum(mov.values())
print(f"julgados: {len(gab)}  | sem resposta: {faltou}")
print(f"  consenso e já correto : {mantidos}")
print(f"  consenso e MOVIDO     : {total}")
for (de, para), n in mov.most_common():
    print(f"      {de} -> {para}: {n}")
print(f"  avaliadores discordam : {len(disc)}  (mantido o atual — fronteira ambígua)")
print(f"  marcado '?'           : {len(interr)} (mantido o atual)")
conc = (mantidos + total) / max(1, len(gab) - faltou)
print(f"\nconcordância entre avaliadores: {conc*100:.1f}%")

if total:
    shutil.copy(STORE / "classificacao.json", STORE / "classificacao.json.pre_cfop")
    (STORE / "classificacao.json").write_text(
        json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"gravado. backup em classificacao.json.pre_cfop")

(AUD / "cfop_sinalizados.json").write_text(json.dumps(
    {"discordancia": [{"id": r, "atual": f, "av1": x, "av2": y} for r, f, x, y in disc],
     "interrogacao": [{"id": r, "av1": x, "av2": y} for r, x, y in interr]},
    ensure_ascii=False, indent=1), encoding="utf-8")
print(f"sinalizados em cfop_sinalizados.json ({len(disc)} discordâncias, {len(interr)} '?')")
