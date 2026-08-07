# -*- coding: utf-8 -*-
"""Tempo tech por subgrupo = changedDate - dateStart, sobre chamados CONCLUIDOS."""
import json, collections, statistics
from datetime import datetime
def L(f): return json.load(open(f, encoding='utf-8-sig'))

EXPORT = r"C:\Dev\Qigger\Ultracar\bitrix-analisys\output\bitrix_export_139_20260804_200226.json"
tk = {t['task']['id']: t['task'] for t in json.load(open(EXPORT, encoding='utf-8'))['tasks']}

def tech(tid):
    t = tk.get(tid) or {}
    if str(t.get('status')) != '5':          # so concluidos
        return None
    a, b = t.get('dateStart'), t.get('changedDate')
    if not a or not b:
        return None
    try:
        d = (datetime.fromisoformat(b) - datetime.fromisoformat(a)).days
    except ValueError:
        return None
    return d if d >= 0 else None

P = L('propostas.json')
v2 = L('class_final_v2.json')['final']
NORM = {"Certificado digital": "Certificado digital (cadastro, vencimento, atualização)",
        "Particularidade municipal de NFS-e (layout, homologação, prefeitura)":
            "Particularidade municipal de NFS-e (layout, homologação, instabilidade da prefeitura)"}
por_tema = collections.defaultdict(list)
for tid, c in v2.items():
    por_tema[NORM.get(c, c)].append(tid)

TAG = {'prop1': 'P1', 'prop2': 'P2', 'prop3': 'P3', 'prop4': 'P4', 'prop5': 'P5', 'prop6': 'P6'}
out = {}
for pk, p in P.items():
    for sg in p['subgrupos']:
        ds = [d for i in sg.get('ids', []) if (d := tech(i)) is not None]
        out[f'{TAG[pk]}||{sg["nome"]}'] = ds
from acoes import P9
for nome, ch, ab, ult, heat, cv, acts in P9:
    out[f'P9||{nome}'] = [d for i in por_tema.get(nome, []) if (d := tech(i)) is not None]

json.dump(out, open('tempo_tech.json', 'w', encoding='utf-8'), indent=1)

TOT = L('tempo_medio.json')
print(f"{'subgrupo':52s} {'total':>16} {'tech':>16} {'fila':>6}")
for k in sorted(out, key=lambda x: -(statistics.mean(out[x]) if out[x] else 0)):
    t, h = TOT.get(k, []), out[k]
    st = f'{statistics.mean(t):.0f} d ({len(t)})' if t else '—'
    sh = f'{statistics.mean(h):.0f} d ({len(h)})' if h else '—'
    fila = f'{statistics.mean(t)-statistics.mean(h):.0f} d' if t and h else '—'
    print(f'{k[:50]:52s} {st:>16} {sh:>16} {fila:>6}')
tot_t = [x for v in TOT.values() for x in v]
tot_h = [x for v in out.values() for x in v]
print(f"\nGERAL: total média {statistics.mean(tot_t):.1f} d ({len(tot_t)} chamados) | "
      f"tech média {statistics.mean(tot_h):.1f} d ({len(tot_h)} chamados)")
