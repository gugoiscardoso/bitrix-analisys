# -*- coding: utf-8 -*-
"""Gera o artefato HTML do plano de propostas a partir de propostas.json."""
import json, sys, io, html
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
SCRATCH = r"C:\Users\Lucas\AppData\Local\Temp\claude\C--Dev-Qigger-Ultracar-bitrix-analisys\a9f3de17-99fb-4920-8408-48ea262b563e\scratchpad"

P = json.load(open(SCRATCH + r"\propostas.json", encoding="utf-8-sig"))
_p7 = json.load(open(SCRATCH + r"\sub_p7.json", encoding="utf-8-sig"))
_p8 = json.load(open(SCRATCH + r"\sub_p8.json", encoding="utf-8-sig"))
import sys as _sys
_sys.path.insert(0, SCRATCH)
from acoes import P9 as _P9

def _norm(subs, cham_por_nome=None):
    out = []
    for sg in subs:
        out.append({"nome": sg["nome"], "descricao": sg["descricao"],
                    "count": sg.get("count", 0), "n_conv": sg.get("n_exato") or sg.get("n_conv") or 0,
                    "abertos": sg.get("abertos", 0), "soma_dias": sg.get("soma_dias", 0),
                    "ultima": sg.get("ultima", "2026-08-05"),
                    "idade_dias": sg.get("idade_dias", 0), "heat": sg.get("heat", "recente")})
    return out

P["prop7"] = {"total": 24, "total_abertos": 2, "total_dias": 369,
              "chat_conv": 861, "chat_carga": 15.3, "iceberg": 35.9,
              "subgrupos": _norm(_p7["subgrupos"])}
P["prop8"] = {"total": 0, "total_abertos": 0, "total_dias": 0,
              "chat_conv": 994, "chat_carga": 15.4, "iceberg": None,
              "subgrupos": _norm(_p8["subgrupos"])}
P["prop9"] = {"total": 128, "total_abertos": 36, "total_dias": 0,
              "chat_conv": 1061, "chat_carga": None, "iceberg": 8.3,
              "subgrupos": [{"nome": n, "descricao": f"{cv} conversas no chat sobre o mesmo tema.",
                             "count": ch, "n_conv": cv, "abertos": ab, "soma_dias": 0,
                             "ultima": ult, "idade_dias": 0, "heat": heat}
                            for n, ch, ab, ult, heat, cv, _a in _P9]}

META = {
    "prop1": ("P1", "Pré-validação da nota antes da transmissão",
              "Validar a nota no sistema antes de enviar à SEFAZ/prefeitura, com mensagem clara de correção. Cada subgrupo é um validador implementável de forma independente."),
    "prop2": ("P2", "Job de reconciliação com SEFAZ e prefeituras",
              "Reconsultar protocolo/chave periodicamente e reconciliar o estado local. As 3 primeiras funções (70 chamados) usam a mesma mecânica e formam a fase 1."),
    "prop3": ("P3", "Pacote de conformidade tributária",
              "Corrigir cálculo e exibição de impostos. IBS/CBS é a frente que mais cresce — 6 dos 14 chamados abertos da proposta."),
    "prop4": ("P4", "Robustez de PDF/DANFE e impressão",
              "Garantir que o documento gerado sai, sai rápido e é fiel ao XML autorizado. Confiabilidade + fidelidade somam 55% da proposta."),
    "prop5": ("P5", "Triagem com evidência obrigatória",
              "90% dos chamados sem causa vêm do canal Matrix. Três mecanismos: captura obrigatória de erro+nota; bifurcação dúvida×erro; campos estruturados para alterações."),
    "prop6": ("P6", "Homologação municipal + certificado digital",
              "Monitoramento contínuo de prefeituras e gestão self-service de certificado. A onda do Emissor Nacional atinge dezenas de municípios; Contagem-MG e Limeira-SP em 01/09/2026 e São Paulo em setembro."),
    "prop7": ("P7", "Fluxo guiado de devolução, garantia e remessa",
              "Nasceu da análise do chat: 861 conversas contra 24 chamados (iceberg 35,9×). Não é bug, é fluxo — o sistema não reaproveita os tributos do XML da compra."),
    "prop8": ("P8", "Autonomia do cliente (self-service)",
              "Invisível nos chamados: 994 conversas sem equivalente em ticket. 26% delas mencionam AnyDesk — o operador entra na máquina para ajustar um parâmetro."),
    "prop9": ("P9", "Frentes complementares",
              "Temas fora das seis propostas originais. Cadastro/config fiscal sozinho soma 390 ocorrências, mais que a P4 inteira."),
}

TOTAL_FISCAL = 522
covered = sum(P[k]["total"] for k in P)

def ice_txt(sg):
    c, v = sg["count"], (sg.get("n_conv") or 0)
    return f" · iceberg {v/c:.0f}×" if c and v and v/c >= 3 else ""

def br_date(iso):
    y, m, d = iso.split("-")
    return f"{d}/{m}"

def sec(key):
    p = P[key]
    tag, title, blurb = META[key]
    def carga(x): return x["count"] + (x.get("n_conv") or 0)
    subs = sorted(p["subgrupos"], key=lambda x: -carga(x))
    mx = max(carga(sg) for sg in subs) or 1
    tot_carga = sum(carga(sg) for sg in subs) or 1
    rows = []
    for sg in subs:
        w = round(carga(sg) / mx * 100)
        ab = (f'<span class="ab">{sg["abertos"]} em aberto</span>' if sg["abertos"] else "")
        heat = sg["heat"]
        last = (f'<span class="last {heat}" title="Última incidência há {sg["idade_dias"]} dias">'
                f'última {br_date(sg["ultima"])}</span>')
        rows.append(f"""
      <div class="row" title="{html.escape(sg["descricao"])}">
        <div class="rowhead">
          <span class="rname">{html.escape(sg["nome"])}</span>
          <span class="rnums">{last} <b>{carga(sg)}</b> · {carga(sg)/tot_carga*100:.0f}% {ab}</span>
        </div>
        <div class="track"><i style="width:{w}%"></i></div>
        <p class="rsplit">{sg["count"]} chamado{"s" if sg["count"]!=1 else ""} · {sg.get("n_conv") or 0} conversa{"s" if (sg.get("n_conv") or 0)!=1 else ""}{ice_txt(sg)}</p>
        <p class="rdesc">{html.escape(sg["descricao"])}</p>
      </div>""")
    pct = p["total"] / TOTAL_FISCAL * 100
    chat = ""
    if p.get("chat_conv"):
        chat = f'<span class="badge chat"><b>{p["chat_conv"]:,}</b> conversas no chat</span>'.replace(",", ".")
        if p.get("chat_carga"):
            chat += f'<span class="badge chat"><b>{p["chat_carga"]}%</b> da carga do balcão</span>'
        if p.get("iceberg"):
            chat += f'<span class="badge chat"><b>{p["iceberg"]}×</b> iceberg</span>'
    return f"""
  <section id="{key}">
    <div class="sechead">
      <span class="ptag">{tag}</span>
      <div>
        <h2>{html.escape(title)}</h2>
        <p class="blurb">{html.escape(blurb)}</p>
      </div>
    </div>
    <div class="badges">
      {f'<span class="badge"><b>{p["total"]}</b> chamados</span>' if p["total"] else ""}
      {"" if p["total"] == 0 else f'<span class="badge"><b>{pct:.0f}%</b> dos fiscais</span>'}
      {"" if not p["total_abertos"] else f'<span class="badge amber"><b>{p["total_abertos"]}</b> em aberto</span>'}
      {"" if not p["total_dias"] else f'<span class="badge"><b>{p["total_dias"]:,}</b> dias de tratativa</span>'}
      {chat}
    </div>
    <div class="rows">{''.join(rows)}
    </div>
  </section>"""

sections = "".join(sec(k) for k in ["prop1", "prop2", "prop3", "prop4", "prop5", "prop6", "prop9", "prop7", "prop8"])
nav = "".join(f'<a href="#{k}">{META[k][0]} · {html.escape(META[k][1].split(" ")[0])}…</a>' for k in META)
nav = "".join(f'<a href="#{k}">{META[k][0]}<span> {html.escape(META[k][1])}</span></a>' for k in META) + '<a href="#rebal">↺<span> Rebalanceamento</span></a>'

page = f"""<title>Fricção Fiscal — Plano de Propostas · Ultracar</title>
<style>
:root {{
  --bg:#F4F6F8; --panel:#FFFFFF; --ink:#1C2733; --ink2:#5C6C7C; --ink3:#8695A5;
  --line:#DFE6EC; --track:#E7EDF2; --accent:#175E8F; --accent2:#3D83B8; --accent-soft:#E3EDF5; --accent-ink:#12496E;
  --amber:#A15E14; --amber-bg:#F7ECDD;
  --hot:#A8261D; --hot-bg:#F8E4E1; --mid:#A15E14; --mid-bg:#F7ECDD; --old:#7D6A0B; --old-bg:#F3ECCB;
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --bg:#101720; --panel:#18222D; --ink:#E3EAF1; --ink2:#93A4B5; --ink3:#6D7E8F;
    --line:#273545; --track:#22303E; --accent:#5EA3D8; --accent2:#3D83B8; --accent-soft:#1D3348; --accent-ink:#9CC8EA;
    --amber:#DDA05B; --amber-bg:#31261731;
    --hot:#EE8A80; --hot-bg:#3A1E1B; --mid:#DDA05B; --mid-bg:#312617; --old:#CFC06A; --old-bg:#2D2913;
  }}
}}
:root[data-theme="dark"] {{
  --bg:#101720; --panel:#18222D; --ink:#E3EAF1; --ink2:#93A4B5; --ink3:#6D7E8F;
  --line:#273545; --track:#22303E; --accent:#5EA3D8; --accent2:#3D83B8; --accent-soft:#1D3348; --accent-ink:#9CC8EA;
  --amber:#DDA05B; --amber-bg:#31261731;
  --hot:#EE8A80; --hot-bg:#3A1E1B; --mid:#DDA05B; --mid-bg:#312617; --old:#CFC06A; --old-bg:#2D2913;
}}
:root[data-theme="light"] {{
  --bg:#F4F6F8; --panel:#FFFFFF; --ink:#1C2733; --ink2:#5C6C7C; --ink3:#8695A5;
  --line:#DFE6EC; --track:#E7EDF2; --accent:#175E8F; --accent2:#3D83B8; --accent-soft:#E3EDF5; --accent-ink:#12496E;
  --amber:#A15E14; --amber-bg:#F7ECDD;
  --hot:#A8261D; --hot-bg:#F8E4E1; --mid:#A15E14; --mid-bg:#F7ECDD; --old:#7D6A0B; --old-bg:#F3ECCB;
}}
* {{ box-sizing:border-box; margin:0; }}
body {{
  background:var(--bg); color:var(--ink);
  font:15px/1.55 -apple-system, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
  padding:0 20px 72px;
}}
main {{ max-width:880px; margin:0 auto; }}
.eyebrow {{ font-size:11.5px; font-weight:600; letter-spacing:.14em; text-transform:uppercase; color:var(--accent); }}
header {{ padding:44px 0 8px; }}
h1 {{ font-size:31px; line-height:1.15; font-weight:650; letter-spacing:-.015em; text-wrap:balance; margin:8px 0 10px; }}
.lede {{ color:var(--ink2); max-width:62ch; }}
.stats {{ display:flex; flex-wrap:wrap; gap:10px; margin:24px 0 6px; }}
.stat {{
  background:var(--panel); border:1px solid var(--line); border-radius:10px;
  padding:12px 18px; min-width:130px;
}}
.stat b {{ display:block; font-size:23px; font-weight:650; font-variant-numeric:tabular-nums; letter-spacing:-.01em; }}
.stat span {{ font-size:12px; color:var(--ink2); }}
nav {{ display:flex; flex-wrap:wrap; gap:8px; margin:22px 0 8px; position:sticky; top:0; padding:10px 0; background:var(--bg); z-index:5; }}
nav a {{
  font-size:12.5px; font-weight:600; color:var(--accent); text-decoration:none;
  border:1px solid var(--line); background:var(--panel); border-radius:999px; padding:5px 12px;
  white-space:nowrap; max-width:210px; overflow:hidden; text-overflow:ellipsis;
}}
nav a span {{ font-weight:500; color:var(--ink2); }}
nav a:hover {{ border-color:var(--accent); }}
section {{
  background:var(--panel); border:1px solid var(--line); border-radius:14px;
  padding:26px 28px 20px; margin:18px 0; scroll-margin-top:64px;
}}
.sechead {{ display:flex; gap:14px; align-items:flex-start; }}
.ptag {{
  flex-shrink:0; font-size:13px; font-weight:700; color:var(--accent);
  border:1.5px solid var(--accent); border-radius:8px; padding:3px 9px; margin-top:2px;
  font-variant-numeric:tabular-nums;
}}
h2 {{ font-size:19px; font-weight:650; letter-spacing:-.01em; text-wrap:balance; }}
.blurb {{ color:var(--ink2); font-size:13.5px; margin-top:4px; max-width:68ch; }}
.badges {{ display:flex; flex-wrap:wrap; gap:8px; margin:16px 0 4px; }}
.badge {{
  font-size:12.5px; color:var(--ink2); background:var(--bg); border:1px solid var(--line);
  border-radius:999px; padding:4px 12px; font-variant-numeric:tabular-nums;
}}
.badge b {{ color:var(--ink); font-weight:650; }}
.badge.amber {{ background:var(--amber-bg); border-color:transparent; color:var(--amber); }}
.badge.amber b {{ color:var(--amber); }}
.badge.chat {{ background:var(--accent-soft); border-color:transparent; color:var(--accent-ink); }}
.badge.chat b {{ color:var(--accent-ink); }}
table.rebal {{ width:100%; border-collapse:collapse; margin-top:14px; font-size:13px; }}
table.rebal th {{ text-align:left; font-size:11px; text-transform:uppercase; letter-spacing:.06em;
  color:var(--ink3); font-weight:650; padding:0 10px 7px 0; border-bottom:1px solid var(--line); }}
table.rebal td {{ padding:9px 10px 9px 0; border-bottom:1px solid var(--line); vertical-align:top;
  font-variant-numeric:tabular-nums; }}
table.rebal td.n {{ text-align:right; white-space:nowrap; }}
.verd {{ font-size:11.5px; font-weight:650; border-radius:999px; padding:2px 9px; white-space:nowrap; }}
.verd.up {{ color:var(--hot); background:var(--hot-bg); }}
.verd.down {{ color:var(--ink2); background:var(--track); }}
.verd.new {{ color:var(--accent-ink); background:var(--accent-soft); }}
.verd.keep {{ color:var(--old); background:var(--old-bg); }}
.tblwrap {{ overflow-x:auto; }}
.rows {{ margin-top:14px; }}
.row {{ padding:11px 0 9px; border-top:1px solid var(--line); }}
.rowhead {{ display:flex; justify-content:space-between; gap:16px; align-items:baseline; }}
.rname {{ font-size:13.5px; font-weight:600; }}
.rnums {{ font-size:12.5px; color:var(--ink2); white-space:nowrap; font-variant-numeric:tabular-nums; }}
.rnums b {{ color:var(--ink); font-size:14px; font-weight:650; }}
.ab {{ color:var(--amber); font-weight:600; margin-left:6px; }}
.last {{ font-size:11.5px; font-weight:650; border-radius:999px; padding:2px 9px; margin-right:8px; white-space:nowrap; }}
.last.recente {{ color:var(--hot); background:var(--hot-bg); }}
.last.medio {{ color:var(--mid); background:var(--mid-bg); }}
.last.antigo {{ color:var(--old); background:var(--old-bg); }}
.legend {{ display:flex; flex-wrap:wrap; gap:8px 14px; align-items:center; margin:14px 0 0; font-size:12px; color:var(--ink2); }}
.legend .last {{ margin-right:0; }}
.track {{ height:10px; border-radius:5px; background:var(--track); margin:7px 0 6px; overflow:hidden; }}
.track i {{ display:block; height:100%; background:linear-gradient(90deg, var(--accent), var(--accent2)); border-radius:5px 4px 4px 5px; min-width:14px; }}
.rdesc {{ font-size:12.5px; color:var(--ink3); max-width:76ch; }}
.rsplit {{ font-size:11.5px; color:var(--ink2); font-variant-numeric:tabular-nums; margin:2px 0 4px; }}
footer {{ color:var(--ink3); font-size:12.5px; margin-top:28px; max-width:76ch; }}
footer a {{ color:var(--accent); }}
@media (max-width:640px) {{ .sechead {{ flex-direction:column; gap:8px; }} h1 {{ font-size:25px; }} nav a span {{ display:none; }} }}
@media (prefers-reduced-motion: no-preference) {{
  section {{ animation:rise .35s ease both; }}
  @keyframes rise {{ from {{ opacity:0; transform:translateY(6px); }} to {{ opacity:1; transform:none; }} }}
}}
</style>
<main>
<header>
  <div class="eyebrow">Ultracar · Suporte Fiscal · mai–ago 2026</div>
  <h1>Plano de ataque à fricção fiscal</h1>
  <p class="lede">Seis propostas derivadas de 522 chamados fiscais classificados um a um, quebradas em subvariações
  com incidência, recência e a carga real medida nos dois canais: 522 chamados e 4.914 conversas de chat, todas classificadas por subgrupo uma a uma.</p>
  <div class="stats">
    <div class="stat"><b>522</b><span>chamados fiscais (43% do suporte)</span></div>
    <div class="stat"><b>{covered}</b><span>cobertos pelas 6 propostas ({covered/TOTAL_FISCAL*100:.0f}%)</span></div>
    <div class="stat"><b>~170</b><span>novos por mês, estável</span></div>
    <div class="stat"><b>13 d</b><span>mediana de resolução</span></div>
    <div class="stat"><b>11,4×</b><span>conversas por chamado (iceberg)</span></div>
  </div>
  <div class="legend">
    <span>Barra e número = carga total do subgrupo (chamados + conversas). Última incidência (ref. 04/08/2026):</span>
    <span class="last recente">últimos 30 dias — dor ativa</span>
    <span class="last medio">30–60 dias — atenção</span>
    <span class="last antigo">+60 dias — possivelmente já corrigido</span>
  </div>
</header>
<nav>{nav}</nav>
{sections}
<section id="rebal">
  <div class="sechead">
    <span class="ptag">↺</span>
    <div>
      <h2>Rebalanceamento após a análise do balcão</h2>
      <p class="blurb">As 5.975 conversas fiscais do chat (11,4&times; o volume de chamados) mostram que a priorização
      feita só com tickets enxergava menos de 10% da demanda. Duas propostas mudam de posição e duas novas aparecem.</p>
    </div>
  </div>
  <div class="tblwrap">
  <table class="rebal">
    <thead><tr><th>Proposta</th><th class="n">Chamados</th><th class="n">Conversas</th><th class="n">Carga do chat</th><th>Veredito</th></tr></thead>
    <tbody>
      <tr><td>P1 Pr&eacute;-valida&ccedil;&atilde;o</td><td class="n">80</td><td class="n">1.409</td><td class="n">21,7%</td><td><span class="verd keep">confirmada n&ordm; 1</span></td></tr>
      <tr><td><b>P7 Devolu&ccedil;&atilde;o guiada</b> <span style="color:var(--ink3)">(nova)</span></td><td class="n">24</td><td class="n">861</td><td class="n">15,3%</td><td><span class="verd new">criar &mdash; iceberg 35,9&times;</span></td></tr>
      <tr><td><b>P8 Autonomia / self-service</b> <span style="color:var(--ink3)">(nova)</span></td><td class="n">&mdash;</td><td class="n">994</td><td class="n">15,4%</td><td><span class="verd new">criar &mdash; invis&iacute;vel nos tickets</span></td></tr>
      <tr><td>P6 Municipal + certificado</td><td class="n">40</td><td class="n">642</td><td class="n">10,6%</td><td><span class="verd up">subir &mdash; 2,6&times; maior</span></td></tr>
      <tr><td>P2 Reconcilia&ccedil;&atilde;o</td><td class="n">109</td><td class="n">499</td><td class="n">9,0%</td><td><span class="verd keep">manter &mdash; tamanho j&aacute; fiel</span></td></tr>
      <tr><td>P3 Impostos</td><td class="n">38</td><td class="n">377</td><td class="n">7,2%</td><td><span class="verd keep">manter &mdash; cresce c/ IBS-CBS</span></td></tr>
      <tr><td>P5 Triagem</td><td class="n">61</td><td class="n">&mdash;</td><td class="n">&mdash;</td><td><span class="verd keep">manter &mdash; processo</span></td></tr>
      <tr><td>P4 PDF/DANFE</td><td class="n">42</td><td class="n">132</td><td class="n">2,0%</td><td><span class="verd down">rebaixar &mdash; iceberg 3,1&times;</span></td></tr>
    </tbody>
  </table>
  </div>
  <p class="rdesc" style="margin-top:14px">Iceberg = conversas por chamado do mesmo tema. Alto significa que a dor &eacute;
  absorvida no balc&atilde;o e quase nunca vira ticket; baixo significa que o ticket j&aacute; media bem a dor.
  Detalhamento em <em>analise_balcao_conversas_2026-08-05.md</em>.</p>
</section>

<footer>
  Metodologia: classificação por leitura completa dos 522 chamados (validada por amostragem), causas dos genéricos
  recuperadas do chat de Open Lines quando disponível, subgrupos derivados chamado a chamado. Detalhes e trilha de
  auditoria em <em>analise_chamados_fiscais_2026-08-04.md</em> e <em>chamados_fiscais_2026-08-04.xlsx</em>.
  "Dias de tratativa" = soma de (fechamento − abertura) dos chamados concluídos do subgrupo.
</footer>
</main>
"""

out = SCRATCH + r"\proposta_friccao_fiscal.html"
with open(out, "w", encoding="utf-8") as f:
    f.write(page)
print(f"salvo {out} ({len(page)//1024} KB)")
