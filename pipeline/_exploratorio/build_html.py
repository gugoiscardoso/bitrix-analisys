# -*- coding: utf-8 -*-
"""Gera HTML self-contained para consulta dos chamados com agrupamento e detalhe."""
import json, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

SCRATCH = r"C:\Users\Lucas\AppData\Local\Temp\claude\C--Dev-Qigger-Ultracar-bitrix-analisys\a9f3de17-99fb-4920-8408-48ea262b563e\scratchpad"
EXPORT = r"C:\Dev\Qigger\Ultracar\bitrix-analisys\output\bitrix_export_139_20260804_200226.json"
OUT = r"C:\Dev\Qigger\Ultracar\bitrix-analisys\output\chamados_fiscais_2026-08-04.html"

NORMALIZE = {
    "Certificado digital": "Certificado digital (cadastro, vencimento, atualização)",
    "Particularidade municipal de NFS-e (layout, homologação, prefeitura)":
        "Particularidade municipal de NFS-e (layout, homologação, instabilidade da prefeitura)",
}
STATUS = {"1": "nova", "2": "pendente", "3": "em andamento", "4": "aguard. controle",
          "5": "concluída", "6": "adiada", "7": "recusada"}
CNPJ_RE = re.compile(r"\b(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})\b")

with open(EXPORT, encoding="utf-8") as f:
    export = json.load(f)
with open(SCRATCH + r"\fiscal_final.json", encoding="utf-8") as f:
    groups = json.load(f)
with open(SCRATCH + r"\class_final_v2.json", encoding="utf-8") as f:
    v2 = json.load(f)
final = v2["final"]
fonte = v2["fonte"]
with open(SCRATCH + r"\sub_conv_final.json", encoding="utf-8-sig") as f:
    _sc = json.load(f)
sub_by_sid = {}
for _fr in _sc.values():
    for _k, _v in _fr.items():
        sub_by_sid[int(_k)] = ("" if _v.startswith("Outro") else _v)
with open(SCRATCH + r"\propostas.json", encoding="utf-8-sig") as f:
    _P = json.load(f)
sub_by_tid = {}
for _pp in _P.values():
    for _sg in _pp["subgrupos"]:
        for _i in _sg.get("ids", []):
            sub_by_tid[_i] = _sg["nome"]
PROP = {
 "Rejeição/erro de validação (schema XML, E0xxx, tags, campos, IE)": "P1 Pré-validação",
 "Status dessincronizado sistema x prefeitura/SEFAZ": "P2 Reconciliação",
 "Nota travada em processamento/transmissão sem retorno": "P2 Reconciliação",
 "Numeração/duplicidade (pulos, RPS, DPS, inutilização)": "P2 Reconciliação",
 "Cálculo/exibição de impostos errada (PIS/COFINS/ICMS/ISS/IBS/CBS/retenções)": "P3 Impostos",
 "PDF/DANFE/impressão (não gera, dados fora do lugar)": "P4 PDF/DANFE",
 "Sem causa identificável na descrição": "P5 Triagem",
 "Particularidade municipal de NFS-e (layout, homologação, instabilidade da prefeitura)": "P6 Municipal+Certificado",
 "Certificado digital (cadastro, vencimento, atualização)": "P6 Municipal+Certificado",
 "Nota de devolução/garantia/remessa/complemento": "P7 Devolução guiada",
 "Dúvida de uso / orientação (how-to fiscal)": "P8 Autonomia",
 "Configuração assistida pelo suporte": "P8 Autonomia",
 "Acompanhamento de chamado já aberto": "P8 Autonomia",
 "Instabilidade geral / lentidão do sistema": "P8 Autonomia",
 "Cadastro/config fiscal (NCM, CFOP, CST, cód. serviço, SPED, regime)": "P9 Frentes complementares",
 "Integração financeiro/estoque/OS com a nota": "P9 Frentes complementares",
 "Cancelamento/exclusão de nota": "P9 Frentes complementares",
 "Relatórios fiscais divergentes": "P9 Frentes complementares",
 "XML de compra / importação / manifestação do destinatário": "P9 Frentes complementares",
 "Envio de nota por e-mail falha": "P9 Frentes complementares",
 "NFS-e interna / API interna": "P9 Frentes complementares",
}
with open(SCRATCH + r"\refined.json", encoding="utf-8") as f:
    initial = json.load(f)["final"]

id2problem = {i["id"]: i["problem"] for g in groups.values() for i in g}

def strip_bb(s):
    return re.sub(r"\[/?[A-Za-z][^\]]*\]", "", s or "")

def extract_client(title):
    m = re.search(r"cliente\s*:?\s*(.+?)(?:\s*[-–]\s*(?:id|cnpj)|\s*cnpj|$)", title, re.IGNORECASE)
    if m:
        c = m.group(1).strip(" -–:|")
        if 2 < len(c) < 90 and not CNPJ_RE.match(c):
            return c
    return ""

def extract_cnpj(title):
    m = CNPJ_RE.search(title.replace(" ", ""))
    if m:
        return m.group(1)
    m = re.search(r"\[filial:\s*(\d{14})\]", title, re.IGNORECASE)
    return m.group(1) if m else ""

NAO_FISCAL = "Não fiscal (fora do escopo da análise)"
records = []
for t in export["tasks"]:
    task = t["task"]
    tid = task["id"]
    title = task.get("title") or ""
    fiscal = tid in final
    grp = NORMALIZE.get(final[tid], final[tid]) if fiscal else NAO_FISCAL
    resumo = re.sub(r"\s+", " ", id2problem.get(tid, "")) if fiscal else ""
    NORM_INI = NORMALIZE
    ini = NORM_INI.get(initial.get(tid, ""), initial.get(tid, "")) if fiscal else ""
    records.append({
        "tp": "Chamado",
        "sg": sub_by_tid.get(tid, ""),
        "pr": PROP.get(grp, "") if fiscal else "",
        "id": int(tid),
        "g": grp,
        "fx": fonte.get(tid, "") if fiscal else "",
        "g0": ini,
        "f": 1 if fiscal else 0,
        "st": STATUS.get(str(task.get("status")), str(task.get("status"))),
        "cr": (task.get("createdDate") or "")[:10],
        "cl": (task.get("closedDate") or "")[:10],
        "px": (re.match(r"\s*\[([^\]]+)\]", title).group(1).strip()
               if re.match(r"\s*\[([^\]]+)\]", title) else ""),
        "cli": extract_client(title),
        "cnpj": extract_cnpj(title),
        "rs": resumo[:400],
        "ti": re.sub(r"\s+", " ", title),
        "ds": strip_bb(task.get("description") or "").strip(),
    })

# ---- conversas ----
import pandas as _pd
_conv = _pd.DataFrame(json.load(open(SCRATCH + r"\conv_fiscais.json", encoding="utf-8")))
_cls = {}
for _i in range(1, 17):
    for _k, _v in json.load(open(SCRATCH + rf"\class_conv_{_i}.json", encoding="utf-8-sig")).items():
        _cls[int(_k)] = _v
for _, _r in _conv.iterrows():
    _sid = int(_r["SessionId"])
    _tema = _cls.get(_sid)
    if _tema is None:
        continue
    _d = re.sub(r"\s+", " ", str(_r["digest"] or ""))
    records.append({
        "tp": "Conversa", "sg": sub_by_sid.get(_sid, ""), "pr": PROP.get(_tema, ""),
        "id": _sid, "g": _tema, "fx": "chat (LLM)", "g0": "",
        "f": 1, "st": "—", "cr": str(_r["StartedAt"])[:10], "cl": "",
        "px": _r.get("Channel") or "", "cli": "", "cnpj": "",
        "rs": _d[:300], "ti": "", "ds": _d[:2500],
        "dur": int(_r.get("DurationMinutes") or 0), "msg": int(_r.get("TotalMessages") or 0),
        "tk": "Sim" if _r.get("tem_chamado") else "Não",
    })

records.sort(key=lambda r: r["cr"], reverse=True)
data_json = json.dumps(records, ensure_ascii=False).replace("<", "\\u003c")

fiscal_total = sum(1 for r in records if r["f"])
open_total = sum(1 for r in records if r["f"] and r["st"] != "concluída")

html = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Chamados Fiscais — Ultracar/Portocar</title>
<style>
:root{
  --bg:#f4f6f9; --panel:#ffffff; --border:#e2e8f0; --text:#1a2332; --muted:#64748b;
  --accent:#1f4e79; --accent-soft:#e8f0f8; --hover:#f1f5f9;
  --green:#0d7a4f; --green-bg:#e3f5ec; --blue:#1d5fbf; --blue-bg:#e5effc;
  --orange:#b45309; --orange-bg:#fdf0e0; --gray:#5b6472; --gray-bg:#eceff3;
  --shadow:0 1px 3px rgba(15,23,42,.08),0 4px 16px rgba(15,23,42,.06);
}
@media (prefers-color-scheme: dark){
  :root{
    --bg:#0f1520; --panel:#1a2332; --border:#2c3a52; --text:#e6ebf2; --muted:#8fa0b8;
    --accent:#6ea8dc; --accent-soft:#1e3350; --hover:#22304a;
    --green:#4ade9d; --green-bg:#12362a; --blue:#7ab3f5; --blue-bg:#182f4e;
    --orange:#f0b060; --orange-bg:#3a2a12; --gray:#a5b0c0; --gray-bg:#28324454;
    --shadow:0 1px 3px rgba(0,0,0,.4);
  }
}
*{box-sizing:border-box;margin:0}
body{font:14px/1.5 -apple-system,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--text)}
header{background:var(--accent);color:#fff;padding:14px 22px;display:flex;flex-wrap:wrap;align-items:baseline;gap:8px 18px}
header h1{font-size:17px;font-weight:600}
header .sub{font-size:12.5px;opacity:.85}
.layout{display:flex;gap:16px;padding:16px 22px;max-width:1500px;margin:0 auto;align-items:flex-start}
/* sidebar */
.side{width:330px;flex-shrink:0;background:var(--panel);border:1px solid var(--border);border-radius:10px;box-shadow:var(--shadow);overflow:hidden;position:sticky;top:16px;max-height:calc(100vh - 32px);display:flex;flex-direction:column}
.side h2{font-size:11.5px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);padding:12px 14px 6px}
.glist{overflow-y:auto}
.gitem{display:flex;align-items:center;gap:8px;width:100%;text-align:left;border:0;background:none;color:var(--text);padding:8px 14px;cursor:pointer;font:inherit;font-size:13px;border-left:3px solid transparent}
.gitem:hover{background:var(--hover)}
.gitem.active{background:var(--accent-soft);border-left-color:var(--accent);font-weight:600}
.gitem .n{margin-left:auto;flex-shrink:0;background:var(--gray-bg);color:var(--gray);border-radius:99px;padding:1px 9px;font-size:11.5px;font-weight:600}
.gitem.active .n{background:var(--accent);color:#fff}
.gitem .bar{position:relative;flex-shrink:0;width:34px;height:5px;border-radius:3px;background:var(--gray-bg);overflow:hidden}
.gitem .bar i{position:absolute;inset:0;right:auto;background:var(--accent);border-radius:3px}
.gsep{border-top:1px solid var(--border);margin:6px 0}
/* main */
.main{flex:1;min-width:0}
.toolbar{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:12px}
.toolbar input[type=search]{flex:1;min-width:220px;padding:9px 13px;border:1px solid var(--border);border-radius:8px;background:var(--panel);color:var(--text);font:inherit}
.toolbar select{padding:9px 11px;border:1px solid var(--border);border-radius:8px;background:var(--panel);color:var(--text);font:inherit}
.count{font-size:12.5px;color:var(--muted);margin:2px 2px 10px}
.card{background:var(--panel);border:1px solid var(--border);border-radius:10px;box-shadow:var(--shadow);padding:12px 16px;margin-bottom:9px;cursor:pointer;transition:border-color .12s}
.card:hover{border-color:var(--accent)}
.card .top{display:flex;flex-wrap:wrap;align-items:center;gap:7px;margin-bottom:5px}
.card .id{font-weight:700;color:var(--accent);font-size:13px}
.card .cli{font-weight:600;font-size:13.5px}
.card .res{color:var(--text);font-size:13.5px}
.card .meta{margin-top:5px;font-size:12px;color:var(--muted)}
.chip{font-size:11px;font-weight:600;border-radius:99px;padding:2px 9px;white-space:nowrap}
.chip.concluida{background:var(--green-bg);color:var(--green)}
.chip.andamento{background:var(--blue-bg);color:var(--blue)}
.chip.pendente{background:var(--orange-bg);color:var(--orange)}
.chip.outro{background:var(--gray-bg);color:var(--gray)}
.chip.px{background:var(--accent-soft);color:var(--accent)}
.chip.tpt{background:var(--green-bg);color:var(--green)}
.chip.tpc{background:#efe7f7;color:#6b4e8f}
@media (prefers-color-scheme:dark){.chip.tpc{background:#2c2340;color:#c3a8e8}}
.gitem.sub{padding-left:26px;font-size:12.5px;color:var(--muted)}
.gitem.sub .n{font-size:11px}
.ghdr{font-size:10.5px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);padding:8px 14px 4px;font-weight:700}
.empty{color:var(--muted);text-align:center;padding:50px 0}
.more{display:block;margin:14px auto;padding:9px 22px;border:1px solid var(--border);background:var(--panel);color:var(--accent);border-radius:8px;font:inherit;font-weight:600;cursor:pointer}
.more:hover{background:var(--hover)}
/* modal */
.overlay{position:fixed;inset:0;background:rgba(10,16,28,.55);display:none;align-items:flex-start;justify-content:center;padding:4vh 16px;z-index:50}
.overlay.open{display:flex}
.modal{background:var(--panel);border-radius:12px;box-shadow:0 20px 60px rgba(0,0,0,.35);width:min(880px,100%);max-height:92vh;display:flex;flex-direction:column;overflow:hidden}
.mhead{padding:16px 22px 12px;border-bottom:1px solid var(--border);display:flex;gap:12px;align-items:flex-start}
.mhead h3{font-size:15px;line-height:1.4;flex:1}
.mhead .x{border:0;background:var(--gray-bg);color:var(--text);width:30px;height:30px;border-radius:8px;font-size:15px;cursor:pointer;flex-shrink:0}
.mbody{padding:16px 22px;overflow-y:auto}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px 18px;margin-bottom:16px}
.grid .f label{display:block;font-size:10.5px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin-bottom:2px}
.grid .f div{font-size:13px;font-weight:500;word-break:break-word}
.mbody h4{font-size:11.5px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);margin:14px 0 6px}
.desc{background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:13px 15px;white-space:pre-wrap;word-break:break-word;font-size:13px;max-height:45vh;overflow-y:auto}
.btn{display:inline-block;background:var(--accent);color:#fff;border-radius:8px;padding:8px 16px;text-decoration:none;font-weight:600;font-size:13px}
.btn:hover{opacity:.9}
@media (max-width:900px){.layout{flex-direction:column}.side{width:100%;position:static;max-height:300px}}
</style>
</head>
<body>
<header>
  <h1>Chamados Fiscais — Ultracar/Portocar</h1>
  <span class="sub">Bitrix24 grupo 139 + Open Lines · 2026-05-01 a 2026-08-05 · __TOTAL__ registros (__FISCAL__ fiscais, classificados por frente e subgrupo)</span>
</header>
<div class="layout">
  <aside class="side">
    <h2>Grupos de dor</h2>
    <div class="glist" id="glist"></div>
  </aside>
  <section class="main">
    <div class="toolbar">
      <input type="search" id="q" placeholder="Buscar por id, cliente, CNPJ, texto...">
      <select id="tpf">
        <option value="">Chamados e conversas</option>
        <option value="Chamado">So chamados</option>
        <option value="Conversa">So conversas</option>
      </select>
      <select id="stf">
        <option value="">Todos os status</option>
        <option value="concluída">Concluída</option>
        <option value="em andamento">Em andamento</option>
        <option value="pendente">Pendente</option>
      </select>
    </div>
    <div class="count" id="count"></div>
    <div id="list"></div>
  </section>
</div>
<div class="overlay" id="ov">
  <div class="modal">
    <div class="mhead"><h3 id="mt"></h3><button class="x" id="mx" title="Fechar">✕</button></div>
    <div class="mbody" id="mb"></div>
  </div>
</div>
<script>
const DATA = __DATA__;
const NAO_FISCAL = __NAO_FISCAL__;
const PAGE = 60;
let curGroup = null, shown = PAGE;

const groups = {};
DATA.forEach(r => { (groups[r.g] = groups[r.g] || []).push(r); });
const fiscalGroups = Object.keys(groups).filter(g => g !== NAO_FISCAL)
  .sort((a,b) => groups[b].length - groups[a].length);
const maxN = Math.max(...fiscalGroups.map(g => groups[g].length));

function chipClass(st){
  if (st === 'concluída') return 'concluida';
  if (st === 'em andamento') return 'andamento';
  if (st === 'pendente') return 'pendente';
  return 'outro';
}
function esc(s){ const d = document.createElement('div'); d.textContent = s || ''; return d.innerHTML; }

function renderSidebar(){
  const el = document.getElementById('glist');
  el.innerHTML = '';
  const mk = (label, key, n, withBar) => {
    const b = document.createElement('button');
    b.className = 'gitem' + (curGroup === key ? ' active' : '');
    b.innerHTML = (withBar ? `<span class="bar"><i style="width:${Math.round(n/maxN*100)}%"></i></span>` : '') +
      `<span>${esc(label)}</span><span class="n">${n}</span>`;
    b.onclick = () => { curGroup = key; shown = PAGE; renderSidebar(); renderList(); window.scrollTo(0,0); };
    el.appendChild(b);
  };
  mk('Todos os fiscais', '__fiscal__', DATA.filter(r => r.f).length, false);
  el.insertAdjacentHTML('beforeend', '<div class="gsep"></div><div class="ghdr">Por frente e subgrupo</div>');
  const props = {};
  DATA.filter(r => r.f && r.pr).forEach(r => {
    props[r.pr] = props[r.pr] || {n:0, subs:{}};
    props[r.pr].n++;
    const sg = r.sg || '(sem subgrupo)';
    props[r.pr].subs[sg] = (props[r.pr].subs[sg]||0)+1;
  });
  Object.keys(props).sort().forEach(pr => {
    mk(pr, 'P::'+pr, props[pr].n, false);
    Object.entries(props[pr].subs).sort((a,b)=>b[1]-a[1]).forEach(function(e) {
      const b = document.createElement('button');
      b.className = 'gitem sub' + (curGroup === 'S::'+e[0] ? ' active' : '');
      b.innerHTML = '<span>' + esc(e[0]) + '</span><span class="n">' + e[1] + '</span>';
      b.onclick = () => { curGroup = 'S::'+e[0]; shown = PAGE; renderSidebar(); renderList(); window.scrollTo(0,0); };
      el.appendChild(b);
    });
  });
  el.insertAdjacentHTML('beforeend', '<div class="gsep"></div><div class="ghdr">Por tema</div>');
  fiscalGroups.forEach(g => mk(g, g, groups[g].length, true));
  el.insertAdjacentHTML('beforeend', '<div class="gsep"></div>');
  if (groups[NAO_FISCAL]) mk(NAO_FISCAL, NAO_FISCAL, groups[NAO_FISCAL].length, false);
  mk('Todos os chamados', '__all__', DATA.length, false);
}

function filtered(){
  const q = document.getElementById('q').value.trim().toLowerCase();
  const st = document.getElementById('stf').value;
  const tp = document.getElementById('tpf').value;
  return DATA.filter(r => {
    if (curGroup === '__fiscal__') { if (!r.f) return false; }
    else if (curGroup === '__all__' || curGroup === null) { /* todos */ }
    else if (curGroup.startsWith('P::')) { if (r.pr !== curGroup.slice(3)) return false; }
    else if (curGroup.startsWith('S::')) { if ((r.sg || '(sem subgrupo)') !== curGroup.slice(3)) return false; }
    else if (r.g !== curGroup) return false;
    if (tp && r.tp !== tp) return false;
    if (st && r.st !== st) return false;
    if (q){
      const hay = (r.id + ' ' + r.cli + ' ' + r.cnpj + ' ' + r.ti + ' ' + r.rs + ' ' + r.ds + ' ' + r.px + ' ' + (r.sg||'')).toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });
}

function renderList(){
  const rows = filtered();
  const el = document.getElementById('list');
  const label = curGroup === null || curGroup === '__all__' ? 'todos os registros'
    : curGroup === '__fiscal__' ? 'todos os fiscais'
    : (curGroup.startsWith('P::') || curGroup.startsWith('S::')) ? curGroup.slice(3) : curGroup;
  document.getElementById('count').textContent = rows.length + ' registro(s) — ' + label;
  el.innerHTML = '';
  if (!rows.length){ el.innerHTML = '<div class="empty">Nenhum chamado encontrado.</div>'; return; }
  rows.slice(0, shown).forEach(r => {
    const c = document.createElement('div');
    c.className = 'card';
    const main = r.rs || r.ti;
    c.innerHTML =
      `<div class="top"><span class="chip ${r.tp==='Conversa'?'tpc':'tpt'}">${r.tp}</span><span class="id">#${r.id}</span>` +
      (r.px ? `<span class="chip px">${esc(r.px)}</span>` : '') +
      `<span class="chip ${chipClass(r.st)}">${esc(r.st)}</span>` +
      (r.cli ? `<span class="cli">${esc(r.cli)}</span>` : '') + `</div>` +
      `<div class="res">${esc(main.length > 220 ? main.slice(0,220) + '…' : main)}</div>` +
      `<div class="meta">${r.tp==='Conversa'?'em':'criado'} ${r.cr}${r.cl ? ' · fechado ' + r.cl : ''}${r.cnpj ? ' · CNPJ ' + esc(r.cnpj) : ''}${r.sg ? ' · ' + esc(r.sg) : (r.f ? ' · ' + esc(r.g) : '')}</div>`;
    c.onclick = () => openModal(r);
    el.appendChild(c);
  });
  if (rows.length > shown){
    const b = document.createElement('button');
    b.className = 'more';
    b.textContent = 'Mostrar mais (' + (rows.length - shown) + ' restantes)';
    b.onclick = () => { shown += PAGE; renderList(); };
    el.appendChild(b);
  }
}

function openModal(r){
  document.getElementById('mt').textContent = '#' + r.id + ' — ' + (r.ti || r.sg || r.g);
  const f = (l, v) => v ? `<div class="f"><label>${l}</label><div>${esc(v)}</div></div>` : '';
  document.getElementById('mb').innerHTML =
    `<div class="grid">` +
    `<div class="f"><label>Status</label><div><span class="chip ${chipClass(r.st)}">${esc(r.st)}</span></div></div>` +
    f('Criado em', r.cr) + f('Fechado em', r.cl) +
    f('Cliente', r.cli) + f('CNPJ', r.cnpj) + f('Prefixo original', r.px) +
    f('Tipo de registro', r.tp) +
    (r.f ? f('Classificação final', r.g) : f('Tema', 'Não fiscal')) +
    (r.sg ? f('Subgrupo', r.sg) : '') + (r.pr ? f('Frente', r.pr) : '') +
    (r.tp === 'Conversa' ? f('Canal', r.px) + f('Duração (min)', String(r.dur)) +
       f('Mensagens', String(r.msg)) + f('Tem chamado vinculado', r.tk) : '') +
    (r.f ? f('Fonte da classificação', r.tp === 'Conversa' ? 'Leitura da transcrição do chat (LLM)' : (r.fx === 'chat Open Lines' ? 'Causa recuperada do chat de Open Lines' : 'Leitura da descrição (LLM)')) : '') +
    (r.f && r.g0 && r.g0 !== r.g ? f('Classificação inicial (regex, auditoria)', r.g0) : '') +
    `</div>` +
    (r.rs ? `<h4>Resumo do problema</h4><div class="desc" style="max-height:none;white-space:normal">${esc(r.rs)}</div>` : '') +
    `<h4>${r.tp === 'Conversa' ? 'Transcrição do chat' : 'Descrição completa'}</h4><div class="desc">${esc(r.ds) || '<i>sem descrição</i>'}</div>` +
    (r.tp === 'Chamado' ? `<p style="margin-top:16px"><a class="btn" href="https://ultracar.bitrix24.com/workgroups/group/139/tasks/task/view/${r.id}/" target="_blank" rel="noopener">Abrir no Bitrix24 ↗</a></p>` : '');
  document.getElementById('ov').classList.add('open');
  document.body.style.overflow = 'hidden';
}
function closeModal(){
  document.getElementById('ov').classList.remove('open');
  document.body.style.overflow = '';
}
document.getElementById('mx').onclick = closeModal;
document.getElementById('ov').onclick = e => { if (e.target === document.getElementById('ov')) closeModal(); };
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });
document.getElementById('q').oninput = () => { shown = PAGE; renderList(); };
document.getElementById('stf').onchange = () => { shown = PAGE; renderList(); };
document.getElementById('tpf').onchange = () => { shown = PAGE; renderList(); };

curGroup = '__fiscal__';
renderSidebar();
renderList();
</script>
</body>
</html>
"""

html = (html
        .replace("__TOTAL__", str(len(records)))
        .replace("__FISCAL__", str(fiscal_total))
        .replace("__OPEN__", str(open_total))
        .replace("__NAO_FISCAL__", json.dumps(NAO_FISCAL, ensure_ascii=False))
        .replace("__DATA__", data_json))

with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
import os
print(f"HTML salvo: {OUT} ({os.path.getsize(OUT)//1024} KB, {len(records)} chamados)")
