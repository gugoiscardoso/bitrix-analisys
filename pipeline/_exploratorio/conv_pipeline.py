# -*- coding: utf-8 -*-
"""Fase 1: digests das conversas, filtro fiscal, vínculo com chamados, duração."""
import json, re, sys, io
import pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

SCRATCH = r"C:\Users\Lucas\AppData\Local\Temp\claude\C--Dev-Qigger-Ultracar-bitrix-analisys\a9f3de17-99fb-4920-8408-48ea262b563e\scratchpad"
XLSX = r"C:\Dev\Qigger\Ultracar\bitrix-analisys\output\conversations_export_20260805_134927.xlsx"
EXPORT = r"C:\Dev\Qigger\Ultracar\bitrix-analisys\output\bitrix_export_139_20260804_200226.json"

print("Carregando planilhas...")
conv = pd.read_excel(XLSX, sheet_name="Conversations")
msgs = pd.read_excel(XLSX, sheet_name="Messages", usecols=["SessionId", "Timestamp", "TextContent"])
print(f"{len(conv)} conversas, {len(msgs)} mensagens")

BOILER = re.compile(
    r"^(conversation #|conversa #|bem[- ]vindo|nosso hor|enquiry assigned|consulta atribu|dados recebidos|"
    r"\[b\]data received|data received|new (deal|contact) created|form completed|link do formul|"
    r"informa[cç][oõ]es de contato|contact information saved|deal attached|negócio anexado|order attached|"
    r"lead attached|diga-nos como|a ultracar agradece|conversa fechada|conversation closed|"
    r".*(aceitou a conversa|picked conversation|transfered|transferiu)|obrigad|pesquisa de satisfa|"
    r"basta enviar 1|\[user=|no momento,? nossa fila|percebemos o chat|the conversation is assigned|"
    r"qualquer d[uú]vida estamos|poxa! vi que n[aã]o tive)", re.IGNORECASE)

def clean(t):
    t = re.sub(r"\[/?[A-Za-z][^\]]*\]", "", str(t or "")).strip()
    t = re.sub(r"\\n", " ", t)
    return t

print("Montando digests...")
digests = {}
for sid, g in msgs.groupby("SessionId"):
    g = g.sort_values("Timestamp")
    lines = []
    for t in g["TextContent"]:
        t = clean(t)
        if not t or t.lower() == "nan" or BOILER.match(t):
            continue
        lines.append(t[:200])
        if len(lines) >= 25:
            break
    digests[int(sid)] = "\n".join(lines)[:2200]

FISCAL_RE = re.compile(
    r"nota fiscal|notas fiscais|\bnf-?e\b|\bnfc-?e\b|\bnfs-?e?\b|\bnfse\b|\bnfce\b|\bnfe\b|sefaz|"
    r"\bfiscal\b|fiscais|imposto|tribut|\bicms\b|\bcfop\b|\bncm\b|\bcst\b|csosn|\bpis\b|cofins|"
    r"\bdanfe\b|\biss\b|issqn|\bmdf-?e\b|\bct-?e\b|certificado digital|carta de corre|inutiliza|"
    r"conting[eê]ncia|simples nacional|regime tribut|emitir nota|emiss[aã]o de nota|cancelar nota|"
    r"rejei[cç]|denegad|al[ií]quota|aliquota|\bdps\b|\brps\b|prefeitura|emissor nacional|"
    r"\bxml\b|manifesta[cç]|emitir uma nota|nota de (pe[cç]a|servi[cç]o|devolu[cç])", re.IGNORECASE)

conv["digest"] = conv["SessionId"].map(digests).fillna("")
conv["fiscal"] = conv["digest"].str.contains(FISCAL_RE)
n_f = int(conv["fiscal"].sum())
print(f"Conversas fiscais (keyword): {n_f} de {len(conv)} ({n_f/len(conv)*100:.0f}%)")

# ---- vínculo com chamados ----
print("Extraindo contatos dos 1227 chamados...")
export = json.load(open(EXPORT, encoding="utf-8"))
PHONE_RE = re.compile(r"(?:telefone|tel|fone|whats(?:app)?)\s*:?\s*([\d\s().+\-/]{8,25})", re.IGNORECASE)
ANYPHONE_RE = re.compile(r"\b(\d{2}\s?9?\d{4}[-\s]?\d{4})\b")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")

def norm_phone(p):
    d = re.sub(r"\D", "", p)
    if len(d) >= 10 and d.startswith("55"):
        d = d[2:]
    return d[-8:] if len(d) >= 8 else ""

ticket_phones, ticket_emails = set(), set()
for t in export["tasks"]:
    txt = (t["task"].get("title") or "") + "\n" + (t["task"].get("description") or "")
    for m in PHONE_RE.finditer(txt):
        p = norm_phone(m.group(1))
        if p: ticket_phones.add(p)
    for m in ANYPHONE_RE.finditer(txt):
        p = norm_phone(m.group(1))
        if p: ticket_phones.add(p)
    for e in EMAIL_RE.findall(txt):
        if not e.lower().endswith("ultracar.com.br"):
            ticket_emails.add(e.lower())
print(f"{len(ticket_phones)} telefones e {len(ticket_emails)} e-mails de chamados")

CHAMADO_RE = re.compile(r"chamado[:\s#]*(\d{5,6})", re.IGNORECASE)

def conv_phones(cell):
    out = set()
    for part in re.split(r"[;,/]", str(cell or "")):
        p = norm_phone(part)
        if p: out.add(p)
    return out

def linked(row):
    if CHAMADO_RE.search(row["digest"]):
        return True
    if conv_phones(row["CustomerPhone"]) & ticket_phones:
        return True
    for e in re.split(r"[;,]", str(row["CustomerEmail"] or "").lower()):
        if e.strip() in ticket_emails:
            return True
    return False

conv["tem_chamado"] = conv.apply(linked, axis=1)
fis = conv[conv["fiscal"]]
print(f"Fiscais com vínculo a chamado: {int(fis['tem_chamado'].sum())} | balcão puro: {int((~fis['tem_chamado']).sum())}")

# duração
dur = pd.to_numeric(fis["DurationMinutes"], errors="coerce").fillna(0)
print(f"Duração fiscais: soma {dur.sum()/60:.0f} h | mediana {dur.median():.0f} min | p90 {dur.quantile(0.9):.0f} min | max {dur.max():.0f} min")
om = pd.to_numeric(fis["OperatorMessages"], errors="coerce").fillna(0)
print(f"Mensagens de operador (fiscais): soma {om.sum():.0f} | mediana {om.median():.0f}")

# salva base para classificação
cols = ["SessionId", "Channel", "StartedAt", "DurationMinutes", "TotalMessages",
        "CustomerMessages", "OperatorMessages", "OperatorName", "tem_chamado", "digest"]
base = fis[cols].copy()
base["StartedAt"] = base["StartedAt"].astype(str)
base.to_json(SCRATCH + r"\conv_fiscais.json", orient="records", force_ascii=False)
print(f"Salvo conv_fiscais.json com {len(base)} conversas")
