# -*- coding: utf-8 -*-
"""
Consolida os 45 arquivos herdados da análise exploratória em TRÊS arquivos canônicos
dentro de data/store/. É o passo que torna o relatório reproduzível.

    taxonomia.json        frentes, temas e subgrupos — congelados e versionados
    classificacao.json    id -> {tema, subgrupo, fonte, hash, em} — o cache que evita reclassificar
    base_historica.jsonl  um registro por chamado/conversa, com os campos usados nas métricas

Roda de qualquer lugar: todos os caminhos são relativos à raiz do repositório.
Reconstrói tudo a partir de data/raw/ + os arquivos de classificação legados.
"""
from __future__ import annotations
import collections
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
RAW = RAIZ / "data" / "raw"
STORE = RAIZ / "data" / "store"
VERSAO_TAXONOMIA = "2026-08-07"

sys.stdout.reconfigure(encoding="utf-8")


def ler_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def arquivos(padrao: str) -> list[Path]:
    """Todos os exports que casam, em ordem cronológica pelo nome.
    A coleta é incremental: cada execução gera um arquivo novo com o delta,
    então o store precisa MESCLAR todos — o mais recente vence por id."""
    achados = sorted(RAW.glob(padrao))
    if not achados:
        raise FileNotFoundError(f"nenhum arquivo casa com {padrao} em {RAW}")
    return achados


def hash_classificado(titulo: str, texto: str) -> str:
    """Hash do texto EXATAMENTE como classificar.py o monta e o envia à IA.

    Tem que ser bit a bit o mesmo cálculo de `preparar`, senão o registro é visto
    como "texto mudou" e reclassificado a cada execução, para sempre. Já aconteceu
    duas vezes por esta função existir em duplicata com regras diferentes: aqui se
    hasheava o texto cru e completo, lá o normalizado e truncado em 1200.
    """
    return hash_texto(((titulo or "") + " " + (texto or "")).strip()[:1200])


def hash_texto(t: str) -> str:
    norm = re.sub(r"\s+", " ", (t or "")).strip().lower()
    return hashlib.sha1(norm.encode("utf-8")).hexdigest()[:12]


# ─────────────────────────── taxonomia ───────────────────────────

FRENTES = {
    "P1": "Pré-validação da nota antes da transmissão",
    "P2": "Job de reconciliação com SEFAZ e prefeituras",
    "P3": "Pacote de conformidade tributária (IBS/CBS)",
    "P4": "Robustez de PDF/DANFE e impressão",
    "P5": "Triagem com evidência obrigatória",
    "P6": "Homologação municipal + certificado digital",
    "P7": "Fluxo guiado de devolução, garantia e remessa",
    "P8": "Autonomia do cliente (self-service)",
    # P10–P13 saíram de dentro de P9 na revisão de 07/08/2026. P9 não era uma frente:
    # eram 7 temas sem relação entre si somados num balde, e a soma (1.189) competia por
    # posição de roadmap com frentes reais. Como a soma cresce quanto mais heterogêneo o
    # balde, ele subia no ranking por ser bagunçado, não por ser importante.
    "P10": "Cadastro fiscal mestre (NCM, CFOP, CST, código de serviço, regime)",
    "P11": "Ciclo de cancelamento de nota",
    "P12": "Entrada: XML de compra e manifestação do destinatário",
    "P13": "Integração ERP × nota (financeiro, estoque, OS)",
    "P9": "Complementares (relatórios, e-mail, API interna)",
}

TEMA_PARA_FRENTE = {
    "Rejeição/erro de validação (schema XML, E0xxx, tags, campos, IE)": "P1",
    "Status dessincronizado sistema x prefeitura/SEFAZ": "P2",
    "Nota travada em processamento/transmissão sem retorno": "P2",
    "Numeração/duplicidade (pulos, RPS, DPS, inutilização)": "P2",
    "Cálculo/exibição de impostos errada (PIS/COFINS/ICMS/ISS/IBS/CBS/retenções)": "P3",
    "PDF/DANFE/impressão (não gera, dados fora do lugar)": "P4",
    "Sem causa identificável na descrição": "P5",
    "Particularidade municipal de NFS-e (layout, homologação, instabilidade da prefeitura)": "P6",
    "Certificado digital (cadastro, vencimento, atualização)": "P6",
    "Nota de devolução/garantia/remessa/complemento": "P7",
    "Dúvida de uso / orientação (how-to fiscal)": "P8",
    "Configuração assistida pelo suporte": "P8",
    "Acompanhamento de chamado já aberto": "P8",
    "Instabilidade geral / lentidão do sistema": "P8",
    "Cadastro/config fiscal (NCM, CFOP, CST, cód. serviço, SPED, regime)": "P10",
    "Cancelamento/exclusão de nota": "P11",
    "XML de compra / importação / manifestação do destinatário": "P12",
    "Integração financeiro/estoque/OS com a nota": "P13",
    # cauda: volume baixo demais para frente própria, segue em P9
    "Relatórios fiscais divergentes": "P9",
    "Envio de nota por e-mail falha": "P9",
    "NFS-e interna / API interna": "P9",
    "Conversa vazia / sem conteúdo útil": None,
    "Não fiscal (falso positivo)": None,
}

# nomes que mudaram ao longo da análise
NORM_TEMA = {
    "Certificado digital": "Certificado digital (cadastro, vencimento, atualização)",
    "Particularidade municipal de NFS-e (layout, homologação, prefeitura)":
        "Particularidade municipal de NFS-e (layout, homologação, instabilidade da prefeitura)",
}


def montar_taxonomia() -> dict:
    propostas = ler_json(STORE / "propostas.json")
    p7 = ler_json(STORE / "sub_p7.json")
    p8 = ler_json(STORE / "sub_p8.json")
    tag_de = {"prop1": "P1", "prop2": "P2", "prop3": "P3",
              "prop4": "P4", "prop5": "P5", "prop6": "P6"}

    subgrupos = []
    for pk, p in propostas.items():
        for sg in p["subgrupos"]:
            subgrupos.append({"frente": tag_de[pk], "nome": sg["nome"],
                              "descricao": sg.get("descricao", "")})
    for tag, j in (("P7", p7), ("P8", p8)):
        for sg in j["subgrupos"]:
            subgrupos.append({"frente": tag, "nome": sg["nome"],
                              "descricao": sg.get("descricao", "")})
    # P10–P13 (derivadas em 07/08/2026, depois da dissolução de P9). Arquivo único
    # porque nasceram juntas; o formato é {frente: {subgrupos: [...]}}.
    arq_p10 = STORE / "sub_p10_p13.json"
    if arq_p10.exists():
        for tag, j in ler_json(arq_p10).items():
            for sg in j["subgrupos"]:
                subgrupos.append({"frente": tag, "nome": sg["nome"],
                                  "descricao": sg.get("descricao", "")})
    # Frentes de tema único (P9 e as quatro que saíram dela): ainda não têm quebra
    # própria, então o subgrupo é o próprio tema. Derivado de quem NÃO recebeu subgrupo
    # acima, em vez de "== P9" fixo — senão a dissolução de P9 deixaria P10..P13 sem
    # nenhum subgrupo e o relatório passaria a agrupar tudo em "(sem subgrupo atribuído)".
    com_subgrupo = {s["frente"] for s in subgrupos}
    for tema, frente in TEMA_PARA_FRENTE.items():
        if frente and frente not in com_subgrupo:
            subgrupos.append({"frente": frente, "nome": tema,
                              "descricao": "Tema completo; esta frente ainda não tem "
                                           "quebra própria, então o subgrupo equivale ao tema."})

    # `tema` por subgrupo é derivado do cache por classificar.enriquecer_taxonomia().
    # Regenerar a taxonomia zerava esse campo nos 69 subgrupos, e tudo que depende dele
    # passava a ver None até alguém rodar o classificador. Carrega o valor anterior;
    # a derivação real continua sendo do classificador, que a recalcula e sobrescreve.
    anterior = {}
    p_tax = STORE / "taxonomia.json"
    if p_tax.exists():
        try:
            anterior = {s["nome"]: s.get("tema") for s in ler_json(p_tax)["subgrupos"]}
        except Exception:
            pass
    for sg in subgrupos:
        if anterior.get(sg["nome"]):
            sg["tema"] = anterior[sg["nome"]]

    return {
        "versao": VERSAO_TAXONOMIA,
        "observacao": ("Congelada. O classificador recebe exatamente estes nomes e nunca inventa "
                       "categoria: o que não encaixa vai para 'Outro'. Alterar exige bump de versão."),
        "frentes": [{"tag": t, "titulo": v} for t, v in FRENTES.items()],
        "temas": [{"nome": t, "frente": f} for t, f in TEMA_PARA_FRENTE.items()],
        "subgrupos": subgrupos,
    }


# ─────────────────────────── conversas ───────────────────────────

BOILER = re.compile(
    r"^(conversation #|conversa #|bem[- ]vindo|nosso hor|enquiry assigned|consulta atribu|dados recebidos|"
    r"\[b\]data received|data received|new (deal|contact) created|form completed|link do formul|"
    r"informa[cç][oõ]es de contato|contact information saved|deal attached|negócio anexado|order attached|"
    r"lead attached|diga-nos como|a ultracar agradece|conversa fechada|conversation closed|"
    r".*(aceitou a conversa|picked conversation|transfered|transferiu)|obrigad|pesquisa de satisfa|"
    r"basta enviar 1|\[user=|no momento,? nossa fila|percebemos o chat|the conversation is assigned|"
    r"qualquer d[uú]vida estamos|poxa! vi que n[aã]o tive)", re.IGNORECASE)

# Filtro fiscal. A auditoria de 07/08/2026 mediu 15,3% de falso negativo em conversa
# (~1.059 de 6.906 descartadas). Os termos abaixo de "--- ampliação" fecham 87% desse
# buraco com 1,6% de falso positivo, e são ADITIVOS: o padrão original está inteiro
# acima, então nenhum registro já classificado pode deixar de ser fiscal.
FISCAL_RE = re.compile(
    r"nota fiscal|notas fiscais|\bnf-?e\b|\bnfc-?e\b|\bnfs-?e?\b|\bnfse\b|\bnfce\b|\bnfe\b|sefaz|"
    r"\bfiscal\b|fiscais|imposto|tribut|\bicms\b|\bcfop\b|\bncm\b|\bcst\b|csosn|\bpis\b|cofins|"
    r"\bdanfe\b|\biss\b|issqn|\bmdf-?e\b|\bct-?e\b|certificado digital|carta de corre|inutiliza|"
    r"conting[eê]ncia|simples nacional|regime tribut|emitir nota|emiss[aã]o de nota|cancelar nota|"
    r"rejei[cç]|denegad|al[ií]quota|aliquota|\bdps\b|\brps\b|prefeitura|emissor nacional|"
    r"\bxml\b|manifesta[cç]|emitir uma nota|nota de (pe[cç]a|servi[cç]o|devolu[cç])|"
    # --- ampliação (auditoria 07/08/2026) ---
    r"\bnf\b|\bnfs\b|\bnfd\b|"                    # a forma abreviada que o chat usa
    r"certificado|"                               # sem exigir a palavra "digital"
    r"sintegra|\bsped\b|"                         # obrigação acessória
    r"(?:emit|transmit|cancel|inutiliz|denegad|rejeit|manifest)\w*"
    r"(?:\W+\w+){0,3}\W+(?:nota|notas|cupom)|"    # verbo conjugado + objeto
    r"(?:nota|notas)(?:\W+\w+){0,3}\W+"
    r"(?:emitid|transmitid|cancelad|rejeitad|denegad|autorizad|inutilizad)\w*|"
    r"nota de (?:garantia|retorno|remessa|complement|entrada|sa[ií]da|"
    r"m[aã]o de obra|conserto|transfer[eê]ncia)|"
    r"\bcc-?e\b|chave de acesso|substitui[cç][aã]o trib", re.IGNORECASE)


def limpar(t) -> str:
    t = re.sub(r"\[/?[A-Za-z][^\]]*\]", "", str(t or "")).strip()
    return re.sub(r"\\n", " ", t)


def montar_digests(msgs: pd.DataFrame) -> dict[int, str]:
    """Mesma lógica do conv_pipeline original — o digest precisa ser idêntico
    para que os hashes do cache continuem batendo."""
    out = {}
    for sid, g in msgs.groupby("SessionId"):
        linhas = []
        for t in g.sort_values("Timestamp")["TextContent"]:
            t = limpar(t)
            if not t or t.lower() == "nan" or BOILER.match(t):
                continue
            linhas.append(t[:200])
            if len(linhas) >= 25:
                break
        out[int(sid)] = "\n".join(linhas)[:2200]
    return out


LIMITE_TRANSCRICAO = 3000

# Ruído de plataforma na transcrição. É DIFERENTE do BOILER usado no digest: aquele
# serve ao classificador e corta coisas como "obrigad", que numa leitura humana é fala
# legítima do cliente. Aqui só sai o que nenhuma pessoa escreveu. Medido em 6.000
# conversas — as linhas abaixo aparecem de 1.200 a 8.300 vezes cada.
# As transferências de fila FICAM: mostram o caminho do atendimento, e é delas que sai
# o sinal de entrada na V3.
RUIDO_TRANSCRICAO = re.compile(
    r"^(?:-{2,}|Suporte Ultracar|Data received:|New deal created|Novo neg[oó]cio criado"
    r"|Deal attached to conversation|Contact information saved"
    r"|Conversation #\d+ started|Conversation closed\.?|Conversa fechada\.?"
    r"|Enquiry assigned to all agents|Consulta atribu[ií]da a todos os agentes"
    r"|Diga-nos como nos sa[ií]mos|Basta enviar 1"
    r"|Bem-?vindo ao Canal de Suporte|Pedimos desculpas pelo transtorno"
    r"|A Ultracar agradece o seu contato|Nos ajude a melhorar o nosso atendimento"
    r"|Lembre-se: constru[ií]mos a melhoria"
    r"|Devido a alta demanda gerada pela Reforma"
    r"|Com as mudan[cç]as da Reforma Tribut[aá]ria"
    r"|No momento,? estamos com uma fila|Aproveite nosso PROGRAMA DE INDICA"
    r"|Acesse o formul[aá]rio e aproveite|Percebemos o chat sem resposta)", re.I)


def montar_transcricoes(msgs: pd.DataFrame,
                        remetentes: dict | None = None) -> dict[int, str]:
    """Conversa legível: uma mensagem por linha, com hora.

    Vai num ARQUIVO À PARTE, nunca no campo `texto`. O `texto` é o digest que alimenta
    `hash_texto`, e mudar um caractere dele marcaria os 35 mil registros já
    classificados como pendentes de releitura.

    O autor NÃO entra. O exportador grava AuthorType=System em 100% das 296 mil
    mensagens de todos os exports, porque lê `author_id`/`AUTHOR_ID`/`id_user` e o
    campo que a API devolve chama-se `senderid`. Enquanto isso não for corrigido e as
    conversas recoletadas, rotular autor seria inventar.
    """
    out = {}
    # O export grava a mensagem em UTC, como todo campo de conversa nesta base. Sem o
    # deslocamento a transcrição mostraria 20:57 para uma conversa das 17:57, três
    # horas fora das demais colunas do relatório.
    quando = pd.to_datetime(msgs["Timestamp"], errors="coerce") - pd.Timedelta(hours=3)
    msgs = msgs.assign(_br=quando)
    remetentes = remetentes or {}
    for sid, g in msgs.groupby("SessionId"):
        papeis = remetentes.get(str(int(sid)), {})
        linhas, tam, cortou = [], 0, False
        for _, m in g.sort_values("_br").iterrows():
            t = limpar(m["TextContent"])
            if not t or t.lower() == "nan" or RUIDO_TRANSCRICAO.match(t):
                continue
            hora = "" if pd.isna(m["_br"]) else m["_br"].strftime("%H:%M")
            # Sem mapa de remetentes a linha sai sem rótulo, em vez de sair com um
            # rótulo inventado. Quem não está no mapa é a plataforma falando.
            quem = papeis.get(str(m["MessageId"]), "" if not papeis else "(sistema)")
            cabeca = f"[{hora}] " if hora else ""
            linha = f"{cabeca}{quem}: {t}" if quem else f"{cabeca}{t}"
            if tam + len(linha) > LIMITE_TRANSCRICAO:
                cortou = True
                break
            linhas.append(linha)
            tam += len(linha) + 1
        if cortou:
            linhas.append("[...] restante da conversa não cabe nesta célula")
        out[int(sid)] = "\n".join(linhas)
    return out


# ─────────────────────────── versão do sistema (V2 / V3) ───────────────────────────
#
# Levantado em 23/10/2026 contra a API. Chamado e conversa têm marcas diferentes:
#
#   chamado  — tag `novaversao` (só o endpoint legado task.item.getdata devolve TAGS),
#              as três colunas de rollout criadas em set/out, o prefixo de título e a
#              URL do sistema3. A coluna 3357 "Nova Versão" NÃO entra: existe desde
#              fevereiro e guarda melhoria de V2 destinada à próxima release.
#   conversa — a linha do canal aberto. 17 é "Atendimento V3 Ultracar", o /online/suportev3.
#
# `V3-backlog` é o chamado que só tem a tag: melhoria pedida por cliente de V2 que será
# entregue na nova versão. Conta como V2 nos números, mas mantém marca própria.

TAG_V3 = "novaversao"
STAGES_ROLLOUT_V3 = {"3441", "3443", "3483"}
TITULO_V3_RE = re.compile(r"\[\s*nova\s+vers[ãa]o[^\]]*\]|\bv3\b|\[\s*v\s*\.?\s*3\s*\]", re.I)
URL_V3_RE = re.compile(r"sistema3\.ultracar", re.I)

LINHA_V3 = "17"
NOME_LINHA_V3 = "atendimento v3 ultracar"
# O Bitrix escreve o redirecionamento no idioma do operador, daí as duas formas.
REDIRECT_RE = re.compile(r'(?:para a fila|to queue)\s*"([^"]{3,80})"', re.I)


def versao_chamado(titulo: str, desc: str, tags, stage) -> str:
    explicito = (str(stage) in STAGES_ROLLOUT_V3
                 or bool(TITULO_V3_RE.search(titulo))
                 or bool(URL_V3_RE.search(desc)))
    if explicito:
        return "V3"
    tem_tag = any(str(t).strip().lstrip("#").lower() == TAG_V3 for t in (tags or []))
    return "V3-backlog" if tem_tag else "V2"


def linha_de(valor) -> str:
    """Id da linha de atendimento como string canônica: 17, nunca "17.0".

    Um único nulo na coluna LineId faz o pandas ler a coluna INTEIRA como float, e aí
    `str(17.0)` vira "17.0" — que não bate com LINHA_V3 e derruba a marcação V3 de
    todas as conversas que entraram pela linha 17. Medido em 04/11/2026: o export
    daquele dia tinha 4 nulos, e 164 das 180 conversas da V3 perderam a marca de uma
    vez. A regra achava que era V2.

    Segunda vez que um NaN do pandas muda o tipo de uma coluna e corrompe uma decisão
    nesta base — ver `encerrada_de`. Qualquer campo vindo de planilha que vire chave
    de comparação precisa ser normalizado assim.
    """
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return ""
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))
    s = str(valor).strip()
    return str(int(float(s))) if re.fullmatch(r"\d+\.0+", s) else s


def versao_conversa(linha, redirecionamentos) -> str:
    """A linha de entrada decide, salvo redirecionamento — e aí vale o último.

    Existe um terceiro sinal, `entity_data_1[7]`, que é a linha a que o CHAT do cliente
    está vinculado hoje. Fica de fora de propósito: ele reetiqueta sessão antiga quando
    o cliente migra, e isso quebraria a série temporal.
    """
    if redirecionamentos:
        return "V3" if redirecionamentos[-1].strip().lower() == NOME_LINHA_V3 else "V2"
    return "V3" if linha_de(linha) == LINHA_V3 else "V2"


def montar_redirecionamentos(msgs: pd.DataFrame) -> dict[int, list[str]]:
    """Fila de destino de cada redirecionamento, em ordem, por sessão.

    Lê as mensagens cruas, não o digest: o digest corta boilerplate e para em 25 linhas,
    e a mensagem de sistema do redirecionamento cai justamente nesses dois filtros.
    """
    out: dict[int, list[str]] = {}
    texto = msgs["TextContent"].astype(str)
    candidatas = msgs[texto.str.contains("para a fila|to queue", case=False, na=False)]
    for sid, g in candidatas.groupby("SessionId"):
        destinos = []
        for t in g.sort_values("Timestamp")["TextContent"]:
            m = REDIRECT_RE.search(limpar(t))
            if m:
                destinos.append(m.group(1))
        if destinos:
            out[int(sid)] = destinos
    return out


# ─────────────────────────── base + cache ───────────────────────────

CNPJ_RE = re.compile(r"\b(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})\b")
STATUS = {"1": "nova", "2": "pendente", "3": "em andamento",
          "4": "aguard. controle", "5": "concluída", "6": "adiada", "7": "recusada"}


def extrair_cnpj(titulo: str) -> str:
    m = CNPJ_RE.search(titulo.replace(" ", ""))
    if m:
        return m.group(1)
    m = re.search(r"\[filial:\s*(\d{14})\]", titulo, re.IGNORECASE)
    return m.group(1) if m else ""


MATRIZ_RE = re.compile(r"\[\s*matrix\s*:\s*(\d{1,12})\s*\]", re.IGNORECASE)


def extrair_matriz(titulo: str) -> str:
    """Id da matriz — a CONTA da oficina no ERP, não um canal nem um bot.

    `tb_company.matrix_id -> tb_matrix.id`: uma matriz tem N filiais, cada filial com
    CNPJ próprio. Guardar isto permite contar oficinas distintas; por CNPJ, uma rede de
    cinco lojas vira cinco clientes.

    Quem escrevia esse prefixo era o robô de IA do suporte N1, que montava o título
    como "[Matrix: {MatrixId}] [Filial: {cnpj}] - {assunto}".
    """
    m = MATRIZ_RE.search(titulo or "")
    return m.group(1) if m else ""


def limpar_nome(bruto: str) -> str:
    """Tira o rabo que o título costuma deixar colado no nome.

    Medido nos próprios dados: o mesmo CNPJ aparece como "AUTO BRILHO LTDA." e como
    "AUTO BRILHO LTDA.   ID: 3729". Sem isto, as duas grafias contam como clientes
    diferentes e o mapa de CNPJ fica com lixo competindo com o nome bom.
    """
    c = re.sub(r"\s*[-–|]?\s*ID\s*:?\s*\d+\s*$", "", (bruto or "").strip(), flags=re.I)
    return re.sub(r"\s{2,}", " ", c).strip(" -–:|")


def extrair_cliente(titulo: str) -> str:
    """Nome do cliente a partir do título do chamado.

    Duas convenções convivem. O analista escreve "Cliente: RAZÃO SOCIAL"; os chamados
    abertos pelo Matrix escrevem "[Filial: X]", e X ora é razão social, ora é CNPJ.
    Procurar só por "Cliente" deixava 693 dos 845 vazios — o nome estava no título o
    tempo todo, sob outro rótulo.
    """
    m = re.search(r"cliente\s*:?\s*(.+?)(?:\s*[-–]\s*(?:id|cnpj)|\s*cnpj|$)", titulo, re.IGNORECASE)
    if m:
        c = limpar_nome(m.group(1))
        if 2 < len(c) < 90 and not CNPJ_RE.match(c):
            return c
    # Filial vem entre colchetes e fecha no ']', então o recorte é exato.
    m = re.search(r"\[\s*filial\s*:\s*([^\]]{2,90})\]", titulo, re.IGNORECASE)
    if m:
        c = limpar_nome(m.group(1))
        # CNPJ puro não é nome: deixa vazio para o campo cnpj carregá-lo, em vez de
        # fingir que a coluna Cliente foi preenchida.
        if c and not CNPJ_RE.match(c) and not re.fullmatch(r"[\d./-]{11,20}", c):
            return c
    return ""


def completar_cliente_por_cnpj(registros: list[dict]) -> int:
    """Chamado sem nome de cliente herda o nome que o mesmo CNPJ tem em outro chamado.

    Os chamados abertos pelo Matrix identificam o cliente só pelo CNPJ — a coluna
    Cliente ficava vazia em 845 dos 3.078 da janela, embora a empresa esteja
    identificada. O nome existe: o mesmo CNPJ aparece nomeado em chamados abertos por
    analista.

    Vence a grafia MAIS FREQUENTE, não a primeira. 249 dos 1.002 CNPJs têm mais de uma
    grafia, quase sempre variação de sufixo ou sobra de parser ("ID: 9663" sozinho);
    pela frequência o nome bom ganha do lixo, que aparece uma vez só.

    Marca `cliente_fonte` para a planilha poder distinguir o que veio do próprio
    título do que foi herdado.
    """
    so_digitos = lambda s: re.sub(r"\D", "", s or "")  # noqa: E731
    grafias: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for r in registros:
        if r["tipo"] != "chamado":
            continue
        cnpj, nome = so_digitos(r.get("cnpj")), (r.get("cliente") or "").strip()
        if len(cnpj) == 14 and nome:
            grafias[cnpj][nome] += 1

    n = 0
    for r in registros:
        if r["tipo"] != "chamado":
            continue
        if (r.get("cliente") or "").strip():
            r["cliente_fonte"] = "título"
            continue
        cnpj = so_digitos(r.get("cnpj"))
        if len(cnpj) == 14 and grafias.get(cnpj):
            r["cliente"] = grafias[cnpj].most_common(1)[0][0]
            r["cliente_fonte"] = "CNPJ"
            n += 1
        else:
            r["cliente_fonte"] = ""
    return n


def encerrada_de(r) -> bool | None:
    """A sessão foi encerrada? None quando o export não sabe dizer.

    SessionClosed vem do COMPLETED da activity e só existe em export a partir de
    29/10/2026. Concatenar exports antigos e novos deixa a coluna presente com NaN nas
    linhas antigas, e `bool(nan)` é True — era assim que toda conversa histórica ia ser
    marcada como encerrada. Então o teste é do valor, não da existência da coluna, e
    ausência vira None: "não sei" não é "não fechou".
    """
    v = r.get("SessionClosed")
    if v is None or pd.isna(v):
        return None
    if isinstance(v, str):
        return v.strip().lower() in ("true", "1", "sim", "y", "yes")
    return bool(v)


def main() -> int:
    STORE.mkdir(parents=True, exist_ok=True)

    # ---------- taxonomia ----------
    tax = montar_taxonomia()
    (STORE / "taxonomia.json").write_text(
        json.dumps(tax, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"taxonomia.json      {len(tax['frentes'])} frentes, "
          f"{len(tax['temas'])} temas, {len(tax['subgrupos'])} subgrupos")

    # ---------- cache de classificação ----------
    # O cache é a fonte da verdade e NUNCA é reconstruído por cima: só é semeado
    # a partir do legado na primeira vez. Reexecutar este script não pode perder
    # classificação (foi assim que o cache de conversas foi zerado uma vez).
    cache_existente = {}
    caminho_cache = STORE / "classificacao.json"
    if caminho_cache.exists():
        cache_existente = ler_json(caminho_cache)
        n_ch = len(cache_existente.get("chamados", {}))
        n_cv = len(cache_existente.get("conversas", {}))
        if n_ch or n_cv:
            print(f"cache existente     {n_ch} chamados, {n_cv} conversas — PRESERVADO")

    LEGADO = STORE / "_legado"
    def legado(nome: str) -> Path:
        return LEGADO / nome if (LEGADO / nome).exists() else STORE / nome

    tema_chamado = {k: NORM_TEMA.get(v, v)
                    for k, v in ler_json(STORE / "class_final_v2.json")["final"].items()}
    fonte_chamado = ler_json(STORE / "class_final_v2.json")["fonte"]
    sub_chamado = {}
    for p in ler_json(STORE / "propostas.json").values():
        for sg in p["subgrupos"]:
            for i in sg.get("ids", []):
                sub_chamado[i] = sg["nome"]

    tema_conversa = {}
    for i in range(1, 17):
        f = legado(f"class_conv_{i}.json")
        if f.exists():
            for k, v in ler_json(f).items():
                tema_conversa[int(k)] = NORM_TEMA.get(v, v)
    sub_conversa = {}
    for frente in ler_json(STORE / "sub_conv_final.json").values():
        for k, v in frente.items():
            if not v.startswith("Outro"):
                sub_conversa[int(k)] = v

    # ---------- chamados ----------
    por_id = {}
    fontes = arquivos("bitrix_export_*.json")
    for arq in fontes:                       # ordem cronológica: o mais novo sobrescreve
        for td in ler_json(arq)["tasks"]:
            # guarda o envelope inteiro, não só td["task"]: as tags vêm ao lado dele
            por_id[td["task"]["id"]] = td
    tarefas = list(por_id.values())
    print(f"chamados            {len(tarefas)} mesclados de {len(fontes)} export(s): "
          + ", ".join(a.name.replace('bitrix_export_139_', '') for a in fontes))

    # Status atual, de `atualizar_status.py`. O merge acima dá o status do dia em que
    # o chamado foi coletado por último, e a janela diária só pega dois dias: sem este
    # override, chamado que fechou depois da coleta fica aberto na planilha para sempre.
    p_status = STORE / "status_chamados.json"
    status_atual = (json.loads(p_status.read_text(encoding="utf-8")).get("status", {})
                    if p_status.exists() else {})
    print(f"status_chamados.json {len(status_atual)} override(s) de status"
          if status_atual else
          "status_chamados.json NÃO existe — a coluna Status fica a do dia da coleta."
          "\n  Rode `python pipeline/atualizar_status.py` antes deste script.")

    registros = []
    cache = {"chamados": dict(cache_existente.get("chamados", {})),
             "conversas": dict(cache_existente.get("conversas", {}))}
    for td in tarefas:
        t = td["task"]
        tid = t["id"]
        # Export anterior a 23/10/2026 não tem tags — e não precisa: todo chamado
        # anterior a setembro é V2 de qualquer jeito.
        tags_t = td.get("tags") or []
        titulo = t.get("title") or ""
        desc = re.sub(r"\[/?[A-Za-z][^\]]*\]", "", t.get("description") or "").strip()
        # O filtro de chamado era CIRCULAR: `tid in tema_chamado` significa apenas
        # "já está no arquivo de classificação legado". Consequência: nenhum chamado
        # novo era marcado fiscal, e como classificar.py só enfileira o que é fiscal,
        # nenhum chamado novo jamais seria classificado. Agora vale o mesmo regex das
        # conversas; o `or` preserva o que já está classificado caso o regex mude.
        fiscal = bool(FISCAL_RE.search(titulo + " " + desc)) or tid in tema_chamado
        registros.append({
            "tipo": "chamado", "id": tid,
            "data": (t.get("createdDate") or "")[:10],
            "criado_em": t.get("createdDate"), "fechado_em": t.get("closedDate"),
            "inicio_dev": t.get("dateStart"), "alterado_em": t.get("changedDate"),
            "status": status_atual.get(
                str(tid), STATUS.get(str(t.get("status")), str(t.get("status")))),
            # Quem abria estes chamados era o robô de IA do suporte N1, não um canal
            # chamado "Matrix": esse prefixo é o id da CONTA do cliente, que o robô
            # punha no título. A integração dele com o Bitrix caiu em 30/09/2026 —
            # daí o volume despencar de 92 em setembro para 9 em outubro.
            "canal": "Robô N1 (IA)" if re.search(r"\[matrix", titulo, re.I) else "Analista",
            "cliente": extrair_cliente(titulo), "cnpj": extrair_cnpj(titulo),
            "matriz": extrair_matriz(titulo),
            "fiscal": fiscal,
            "versao": versao_chamado(titulo, desc, tags_t, t.get("stageId")),
            "tags": tags_t,
            "stage": t.get("stageId"),
            "titulo": re.sub(r"\s+", " ", titulo)[:500],
            "texto": desc[:4000],
        })
        # Só semeia do legado quem ESTÁ no legado. Antes bastava `fiscal`, porque
        # fiscal era definido como "está no legado" — as duas condições eram a mesma.
        # Agora que o regex decide, um chamado fiscal pode não ter classificação
        # nenhuma: ele fica de fora do cache e é isso que faz classificar.py pegá-lo.
        if fiscal and tid in tema_chamado and tid not in cache["chamados"]:
            cache["chamados"][tid] = {
                "tema": tema_chamado[tid],
                "subgrupo": sub_chamado.get(tid, ""),
                "frente": TEMA_PARA_FRENTE.get(tema_chamado[tid]),
                "fonte": "chat" if fonte_chamado.get(tid) == "chat Open Lines" else "llm",
                # dos valores COMO FICAM em base_historica.jsonl, que é o que
                # classificar.py lê — não do texto cru desta função
                "hash": hash_classificado(re.sub(r"\s+", " ", titulo)[:500], desc[:4000]),
                "em": "2026-08-05",
            }

    # ---------- conversas ----------
    fontes_conv = arquivos("conversations_export_*.xlsx")
    partes_conv, partes_msg = [], []
    for arq in fontes_conv:
        partes_conv.append(pd.read_excel(arq, sheet_name="Conversations"))
        # MessageId entra por causa da transcrição: é a chave que liga a mensagem ao
        # papel do remetente em remetentes.json. AuthorName/AuthorType não servem —
        # o exportador grava "System" em todas.
        partes_msg.append(pd.read_excel(
            arq, sheet_name="Messages",
            usecols=["SessionId", "MessageId", "Timestamp", "TextContent"]))
    conv = (pd.concat(partes_conv, ignore_index=True)
              .drop_duplicates(subset="SessionId", keep="last"))
    msgs = pd.concat(partes_msg, ignore_index=True).drop_duplicates()
    print(f"conversas           {len(conv)} mescladas de {len(fontes_conv)} export(s)")
    digests = montar_digests(msgs)
    arq_rem = STORE / "remetentes.json"
    remetentes = json.loads(arq_rem.read_text(encoding="utf-8")) if arq_rem.exists() else {}
    if remetentes:
        print(f"remetentes.json     {len(remetentes)} sessões com autor identificado")
    else:
        print("remetentes.json     ausente — transcrição sairá sem autor "
              "(rode pipeline/enriquecer_autores.py)")
    transcricoes = montar_transcricoes(msgs, remetentes)
    redirects = montar_redirecionamentos(msgs)
    (STORE / "transcricoes.json").write_text(
        json.dumps({str(k): v for k, v in transcricoes.items()}, ensure_ascii=False),
        encoding="utf-8")
    print(f"transcricoes.json   {len(transcricoes)} conversas legíveis")

    n_fiscal = 0
    for _, r in conv.iterrows():
        sid = int(r["SessionId"])
        dig = digests.get(sid, "")
        fiscal = bool(FISCAL_RE.search(dig))
        n_fiscal += fiscal
        registros.append({
            "tipo": "conversa", "id": sid,
            "data": str(r["StartedAt"])[:10],
            "criado_em": str(r["StartedAt"]), "fechado_em": str(r.get("EndedAt") or "")[:19] or None,
            "inicio_dev": None, "alterado_em": None,
            "encerrada": encerrada_de(r),
            "status": "", "canal": r.get("Channel") or "",
            "cliente": r.get("CustomerName") or "", "cnpj": "",
            "fiscal": fiscal,
            "versao": versao_conversa(r.get("LineId"), redirects.get(sid)),
            "linha": linha_de(r.get("LineId")),
            "duracao_min": int(r.get("DurationMinutes") or 0),
            "mensagens": int(r.get("TotalMessages") or 0),
            "operador": r.get("OperatorName") or "",
            "titulo": "", "texto": re.sub(r"\s+", " ", dig)[:4000],
        })
        if sid in tema_conversa and str(sid) not in cache["conversas"]:
            tema = tema_conversa[sid]
            cache["conversas"][str(sid)] = {
                "tema": tema,
                "subgrupo": sub_conversa.get(sid, ""),
                "frente": TEMA_PARA_FRENTE.get(tema),
                "fonte": "llm",
                # conversa não tem título; o texto é o digest normalizado
                "hash": hash_classificado("", re.sub(r"\s+", " ", dig)[:4000]),
                "em": "2026-08-05",
            }

    n_herdado = completar_cliente_por_cnpj(registros)
    print(f"\nCliente preenchido pelo CNPJ de outro chamado: {n_herdado}")

    # ---------- grava ----------
    with (STORE / "base_historica.jsonl").open("w", encoding="utf-8") as fh:
        for r in registros:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    cache["taxonomia_versao"] = VERSAO_TAXONOMIA
    cache["consolidado_em"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    (STORE / "classificacao.json").write_text(
        json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\nbase_historica.jsonl {len(registros)} registros "
          f"({sum(1 for r in registros if r['tipo']=='chamado')} chamados, "
          f"{sum(1 for r in registros if r['tipo']=='conversa')} conversas; "
          f"{sum(1 for r in registros if r['fiscal'])} fiscais)")
    print(f"classificacao.json   {len(cache['chamados'])} chamados, "
          f"{len(cache['conversas'])} conversas em cache")

    # ---------- validação ----------
    print("\nVALIDAÇÃO")
    sem_sub_ch = sum(1 for v in cache["chamados"].values() if not v["subgrupo"])
    sem_sub_cv = sum(1 for v in cache["conversas"].values() if not v["subgrupo"])
    # Antes esta linha dizia "(esperado 152: P7 e P9)" — número e frentes cravados à
    # mão, que envelheceram assim que P9 foi dissolvida e P7 ganhou subgrupos. Passou a
    # mostrar de onde vem, em vez de comparar com uma expectativa fóssil.
    por_fr = collections.Counter(
        cache["chamados"][r]["frente"] for r in cache["chamados"]
        if not cache["chamados"][r].get("subgrupo"))
    detalhe = ", ".join(f"{f}:{n}" for f, n in por_fr.most_common(4)) or "nenhuma"
    print(f"  chamados fiscais sem subgrupo: {sem_sub_ch} ({detalhe})")
    print(f"  conversas com tema mas sem subgrupo: {sem_sub_cv}")
    nomes_validos = {s["nome"] for s in tax["subgrupos"]}
    orfaos = {v["subgrupo"] for v in list(cache["chamados"].values()) + list(cache["conversas"].values())
              if v["subgrupo"] and v["subgrupo"] not in nomes_validos}
    print(f"  subgrupos fora da taxonomia: {len(orfaos)}"
          + (f" -> {sorted(orfaos)[:3]}" if orfaos else ""))
    fiscais_base = {r["id"] for r in registros if r["tipo"] == "conversa" and r["fiscal"]}
    print(f"  conversas fiscais recalculadas: {n_fiscal} "
          f"(cache tem {len(cache['conversas'])}; diferença = "
          f"{len(fiscais_base - {int(k) for k in cache['conversas']})} sem classificação)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
