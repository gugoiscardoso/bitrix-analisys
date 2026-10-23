# -*- coding: utf-8 -*-
"""
Classificador da V3 — mesmo contrato do fiscal, máquina menor.

O fiscal quebra em lotes de 250 porque lida com milhares. A V3 tem dezenas, então
cabe numa leitura só. O que NÃO muda é a regra de reprodutibilidade: quem já está em
data/store/classificacao_v3.json com o mesmo texto não é reclassificado.

    python pipeline/classificar_v3.py preparar
        Lista o que ainda falta rotular e escreve o esqueleto em data/store/_fila/.

    python pipeline/classificar_v3.py absorver <arquivo de rótulos>
        Lê {"chamados": {id: [frente, modulo]}, "conversas": {...}} e grava no cache.
        Valida contra taxonomia_v3.json: frente ou módulo fora da lista é recusado.

    python pipeline/classificar_v3.py status
        Cobertura do cache sobre os registros versao=V3 da base.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
STORE = RAIZ / "data" / "store"
CACHE = STORE / "classificacao_v3.json"
TAXONOMIA = STORE / "taxonomia_v3.json"

sys.stdout.reconfigure(encoding="utf-8")


def ler(p: Path, padrao=None):
    if not p.exists():
        return padrao
    return json.loads(p.read_text(encoding="utf-8-sig"))


def hash_texto(titulo: str, texto: str) -> str:
    base = re.sub(r"\s+", " ", f"{titulo} {texto}").strip().lower()
    return hashlib.sha1(base.encode()).hexdigest()[:12]


def registros_v3():
    """Os registros marcados V3 pela regra de consolidar_store, em ordem de data."""
    out = []
    with (STORE / "base_historica.jsonl").open(encoding="utf-8") as fh:
        for linha in fh:
            r = json.loads(linha)
            if r.get("versao") == "V3":
                out.append(r)
    return sorted(out, key=lambda r: (r["data"], str(r["id"])))


def vocabulario():
    tax = ler(TAXONOMIA)
    eixos = {e["nome"]: e for e in tax["eixos"]}
    frentes = {v["codigo"]: v["nome"] for v in eixos["frente"]["valores"]}
    servico = {r["nome"] for r in tax["rotulos_de_servico"]}
    return frentes, set(eixos["modulo"]["valores"]), servico, tax["versao"]


def carregar_cache():
    return ler(CACHE, {"chamados": {}, "conversas": {}})


def chave(r):
    return ("chamados" if r["tipo"] == "chamado" else "conversas"), str(r["id"])


def pendentes(cache):
    """Registro novo, ou cujo texto mudou desde a última classificação."""
    falta = []
    for r in registros_v3():
        grupo, rid = chave(r)
        atual = cache[grupo].get(rid)
        h = hash_texto(r.get("titulo", ""), r.get("texto", ""))
        if atual is None or atual.get("hash") != h:
            falta.append(r)
    return falta


def cmd_preparar(_):
    cache = carregar_cache()
    falta = pendentes(cache)
    total = len(registros_v3())
    print(f"registros V3 na base: {total}")
    print(f"já no cache:          {total - len(falta)}")
    print(f"a classificar:        {len(falta)}")
    if not falta:
        print("\nNada a classificar.")
        return 0
    esqueleto = {"chamados": {}, "conversas": {}}
    for r in falta:
        grupo, rid = chave(r)
        esqueleto[grupo][rid] = ["", ""]
    fila = STORE / "_fila"
    fila.mkdir(exist_ok=True)
    saida = fila / "v3_a_classificar.json"
    saida.write_text(json.dumps(esqueleto, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nesqueleto em {saida}")
    print("preencher cada id com [frente, modulo] e rodar: absorver <arquivo>")
    return 0


def cmd_absorver(args):
    frentes, modulos, servico, versao_tax = vocabulario()
    validos_frente = set(frentes) | servico
    rotulos = ler(Path(args.arquivo))
    if rotulos is None:
        print(f"arquivo não encontrado: {args.arquivo}")
        return 1

    porreg = {chave(r): r for r in registros_v3()}
    cache = carregar_cache()
    erros, gravados = [], 0

    for grupo in ("chamados", "conversas"):
        for rid, par in (rotulos.get(grupo) or {}).items():
            r = porreg.get((grupo, str(rid)))
            if r is None:
                erros.append(f"{grupo}/{rid}: não é um registro V3 da base")
                continue
            if not isinstance(par, list) or len(par) != 2:
                erros.append(f"{grupo}/{rid}: esperado [frente, modulo]")
                continue
            frente, modulo = par
            if frente not in validos_frente:
                erros.append(f"{grupo}/{rid}: frente '{frente}' fora da taxonomia")
                continue
            if modulo not in modulos:
                erros.append(f"{grupo}/{rid}: módulo '{modulo}' fora da taxonomia")
                continue
            cache[grupo][str(rid)] = {
                "frente": frente,
                "frente_nome": frentes.get(frente, frente),
                "modulo": modulo,
                "fonte": "leitura",
                "hash": hash_texto(r.get("titulo", ""), r.get("texto", "")),
                "em": date.today().isoformat(),
            }
            gravados += 1

    if erros:
        print(f"RECUSADO — {len(erros)} problema(s), nada foi gravado:")
        for e in erros[:20]:
            print("  ", e)
        return 1

    cache["taxonomia_versao"] = versao_tax
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"gravados {gravados} rótulos em {CACHE}")
    return cmd_status(args)


def cmd_status(_):
    cache = carregar_cache()
    regs = registros_v3()
    falta = pendentes(cache)
    print(f"\nregistros V3: {len(regs)} "
          f"({sum(1 for r in regs if r['tipo'] == 'chamado')} chamados, "
          f"{sum(1 for r in regs if r['tipo'] == 'conversa')} conversas)")
    print(f"classificados: {len(regs) - len(falta)} | pendentes: {len(falta)}")
    for r in falta[:15]:
        print(f"   falta {r['tipo']} {r['id']} ({r['data']})")
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("preparar")
    pa = sub.add_parser("absorver")
    pa.add_argument("arquivo")
    sub.add_parser("status")
    a = ap.parse_args()
    return {"preparar": cmd_preparar, "absorver": cmd_absorver, "status": cmd_status}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
