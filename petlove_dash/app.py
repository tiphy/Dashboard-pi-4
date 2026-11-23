"""
Painel Petlove (admin)  —  rode com:  streamlit run app.py   (ou duplo clique em iniciar.bat)

COMO ALIMENTAR COM SEUS DADOS (JSON)
------------------------------------
Opção 1: salve o JSON do seu projeto em  ./dados/dados.json  e recarregue a página.
Opção 2: envie o(s) arquivo(s) .json em "Dados e filtros" na barra lateral.

Formato do dados.json (um objeto com listas):
    {
      "eventos":      [{"data": "2026-11-01T10:00:00", "usuario_id": 1, "evento": "login", "produto_id": null}],
      "pedidos":      [{"pedido_id": 9001, "data_pedido": "...", "usuario_id": 1, "status": "Entregue", "subtotal": 10,
                        "frete": 0, "total": 10, "previsao_entrega": "...", "data_entrega": "...", "assinatura": false}],
      "itens_pedido": [{"pedido_id": 9001, "produto_id": 1, "qtd": 2, "preco_unit": 12.99}],
      "produtos":     [{"produto_id": 1, "nome": "...", "categoria": "Cães", "preco": 12.99, "avaliacao": 4.9}],
      "usuarios":     [{"usuario_id": 1, "nome": "Sarah Santos", "pet": "Buddy", "data_cadastro": "..."}],   (opcional)
      "estoque":      [{"produto_id": 1, "quantidade": 5, "minimo": 20}]                                      (opcional)
    }
Se os nomes dos campos do SEU json forem diferentes, preencha MAPEAMENTO na seção CONFIGURAÇÃO.
Também funciona: um arquivo por tabela (dados/pedidos.json...), itens aninhados em cada pedido
(campo "itens": [...]) e CSV como alternativa.
"""
import html
import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# =============================================================================
# CONFIGURACAO  
# =============================================================================
PASTA_DADOS = Path(__file__).parent / "dados"
ARQUIVO_JSON_UNICO = PASTA_DADOS / "dados.json"

# Identidade visual 
COR = "#FF7A6B"           
COR_CLARA = "#FFE9E4"
COR_ESCURA = "#2B2321"
COR_MUTED = "#8A7F7A"
COR_TEXTO_GRAFICO = "#2B2321"   
COR_MARCA = "#2B2321"         
COR_BORDA = "#F1E9E2"
COR_FUNDO = "#FFFDF8"
COR_OK = "#2E9E5B"
COR_OK_FUNDO = "#E8F5EC"

USUARIO_NOME = "Guilherme Silva"
USUARIO_CARGO = "Gerente de Operações"
PREFIXO_PEDIDO = "PET-"           
CRITICO_FRACAO = 0.3             

# Etapas do funil de compra
FUNIL = [
    ("ver_home", "Home"),
    ("ver_produto", "Detalhe do produto"),
    ("add_carrinho", "Carrinho"),
    ("iniciar_checkout", "Checkout"),
    ("pedido_confirmado", "Pedido confirmado"),
]
STATUS_CANCELADO = "Cancelado"
STATUS_ENTREGUE = "Entregue"
STATUS_ANDAMENTO = "Em andamento"

# Icone e cor de cada categoria 
CATEGORIAS = {
    "Cães": ("🐶", "#FFE3E0"),
    "Gatos": ("🐱", "#E0EEFF"),
    "Aves": ("🐦", "#FFF4D6"),
    "Peixes": ("🐟", "#E3F6EA"),
    "Acessórios": ("🎒", "#EBE5FF"),
}

# Metas padrao 
META_RECEITA = 50_000.0
META_CONVERSAO = 3.0    
META_NO_PRAZO = 95.0      

# Traduz os nomes de campo do SEU json para os que o dashboard espera.
# Formato:  "tabela": {"campo_no_seu_json": "campo_esperado"}
# Campos aninhados são "achatados" com "_" (ex.: {"cliente": {"id": 1}} vira "cliente_id").
MAPEAMENTO = {
    "eventos": {},        # ex.: {"timestamp": "data", "user": "usuario_id", "type": "evento"}
    "pedidos": {},        # ex.: {"id": "pedido_id", "createdAt": "data_pedido", "valor": "total"}
    "itens_pedido": {},   # ex.: {"orderId": "pedido_id", "productId": "produto_id", "quantity": "qtd"}
    "produtos": {},       # ex.: {"id": "produto_id", "title": "nome", "category": "categoria"}
    "usuarios": {},       # ex.: {"id": "usuario_id", "name": "nome", "petName": "pet"}
    "estoque": {},        # ex.: {"productId": "produto_id", "stock": "quantidade", "minStock": "minimo"}
}
# Mapeamento de VALORES (ex.: seu status "delivered" -> "Entregue"), por coluna.
MAPEAMENTO_VALORES = {
    "pedidos": {"status": {}},     # ex.: {"delivered": "Entregue", "canceled": "Cancelado", "shipping": "Em andamento"}
    "eventos": {"evento": {}},     # ex.: {"purchase": "pedido_confirmado", "add_to_cart": "add_carrinho"}
}

# Colunas por tabela. "tabela_opcional": o dashboard funciona sem ela (some só o que depende dela).
SCHEMA = {
    "eventos": {
        "obrigatorias": ["data", "usuario_id", "evento"],
        "opcionais": ["produto_id"],
        "datas": ["data"],
    },
    "pedidos": {
        "obrigatorias": ["pedido_id", "data_pedido", "usuario_id", "status", "total"],
        "opcionais": ["subtotal", "frete", "previsao_entrega", "data_entrega", "assinatura"],
        "datas": ["data_pedido", "previsao_entrega", "data_entrega"],
    },
    "itens_pedido": {
        "obrigatorias": ["pedido_id", "produto_id", "qtd", "preco_unit"],
        "opcionais": [],
        "datas": [],
    },
    "produtos": {
        "obrigatorias": ["produto_id", "nome", "categoria"],
        "opcionais": ["preco", "avaliacao"],
        "datas": [],
    },
    "usuarios": {
        "obrigatorias": ["usuario_id"],
        "opcionais": ["nome", "pet", "data_cadastro"],
        "datas": ["data_cadastro"],
        "tabela_opcional": True,
    },
    "estoque": {
        "obrigatorias": ["produto_id", "quantidade"],
        "opcionais": ["minimo"],
        "datas": [],
        "tabela_opcional": True,
    },
}

MESES = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto",
         "Setembro", "Outubro", "Novembro", "Dezembro"]

NAV = ["🏠  Dashboard", "🛍️  Produtos", "📦  Pedidos", "📋  Estoque"]
PAGINAS = {
    NAV[0]: ("Painel de Controle", "Visão operacional de vendas, faturamento e estoque."),
    NAV[1]: ("Produtos", "Desempenho de vendas, desejo e conversão por produto."),
    NAV[2]: ("Pedidos", "Acompanhe status, entregas e atendimento dos pedidos."),
    NAV[3]: ("Estoque", "Níveis de estoque e cobertura de cada produto."),
}

st.set_page_config(page_title="Petlove • Painel Admin", page_icon="🐾", layout="wide")

# =============================================================================
# ESTILO (CSS)  —  visual do painel admin Petlove
# =============================================================================
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@600;700;800&family=DM+Sans:wght@400;500;600;700&display=swap');
.stApp { background: __FUNDO__; font-family: 'DM Sans', sans-serif; color: __ESCURA__; }
button, input, textarea, select { font-family: 'DM Sans', sans-serif !important; }
header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1480px; }

/* ---- barra lateral ---- */
section[data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid __BORDA__; }
section[data-testid="stSidebar"] > div { padding-top: 1.2rem; }
.brand { display:flex; align-items:center; gap:12px; margin: 0 4px 22px 4px; }
.brand-logo { width:40px; height:40px; border-radius:12px; background:__COR__; color:#fff; display:flex;
  align-items:center; justify-content:center; font-family:'Bricolage Grotesque',sans-serif; font-weight:800; font-size:16px; }
.brand-nome { color:__MARCA__; font-family:'Bricolage Grotesque',sans-serif; font-weight:800; font-size:19px; line-height:1.1; }
.brand-sub { font-size:10px; letter-spacing:.08em; color:__MUTED__; font-weight:600; }
.st-key-nav [role="radiogroup"] { gap: 4px; }
.st-key-nav label { width:100%; padding:10px 14px; border-radius:12px; cursor:pointer; margin:0; }
.st-key-nav label > div:first-child { display:none; }
.st-key-nav label p { font-weight:500; font-size:15px; color:__ESCURA__; }
.st-key-nav label:hover { background:#FFF4F1; }
.st-key-nav label:has(input:checked) { background:__CLARA__; }
.st-key-nav label:has(input:checked) p { color:__COR__; font-weight:700; }
.usercard { display:flex; align-items:center; gap:12px; padding-top:16px; border-top:1px solid __BORDA__; margin-top:8px; }
.avatar { width:38px; height:38px; border-radius:50%; background:__CLARA__; color:__COR__; font-weight:700;
  display:flex; align-items:center; justify-content:center; font-size:14px; }
.user-nome { color:__ESCURA__; font-weight:700; font-size:13px; }
.user-cargo { font-size:11px; color:__MUTED__; }

/* ---- topo ---- */
.topbar { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:22px;
  padding-bottom:16px; border-bottom:1px solid __BORDA__; }
.topbar h1 { color:__ESCURA__; font-family:'Bricolage Grotesque',sans-serif; font-weight:800; font-size:28px; margin:0; padding:0; line-height:1.2; }
.topbar p { color:__MUTED__; font-size:14px; margin:4px 0 0 0; }
.topbar-right { color:__ESCURA__; display:flex; align-items:center; gap:10px; font-weight:700; font-size:14px; }
.pill-hoje { background:__CLARA__; color:__COR__; font-size:11px; font-weight:700; padding:4px 10px; border-radius:8px; }
.pill-periodo { color:__MUTED__; font-weight:500; font-size:13px; }

/* ---- cards ---- */
.kpi { background:#fff; border:1px solid __BORDA__; border-radius:18px; padding:18px 20px; height:100%; }
.kpi-top { display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; }
.kpi-label { font-size:12px; font-weight:600; color:__MUTED__; letter-spacing:.02em; text-transform:uppercase; }
.kpi-value { color:__ESCURA__; font-family:'Bricolage Grotesque',sans-serif; font-weight:800; font-size:27px; line-height:1.15; }
.kpi-sub { font-size:12px; color:__MUTED__; margin-top:6px; }
.badge { font-size:11px; font-weight:700; padding:3px 9px; border-radius:8px; white-space:nowrap; }
.badge.up { background:__OKBG__; color:__OK__; }
.badge.down, .badge.alert { background:__CLARA__; color:__COR__; }
.badge.neutro { background:#F3EEEA; color:__MUTED__; }
div[data-testid="stVerticalBlockBorderWrapper"] { background:#fff; border-radius:18px; border:1px solid __BORDA__ !important; }
.card-title { color:__ESCURA__; font-family:'Bricolage Grotesque',sans-serif; font-weight:700; font-size:18px; }
.card-sub { font-size:12px; color:__MUTED__; margin-bottom:10px; }

/* ---- listas ---- */
.row { display:flex; justify-content:space-between; align-items:center; padding:12px 16px; border:1px solid __BORDA__;
  border-radius:12px; margin-bottom:10px; background:#fff; gap:12px; }
.row-id { color:__ESCURA__; font-weight:700; font-size:14px; }
.row-sub { font-size:12px; color:__MUTED__; margin-top:2px; }
.row-right { display:flex; align-items:center; gap:14px; }
.row-meta { text-align:right; }
.row-valor { color:__ESCURA__; font-weight:700; font-size:14px; }
.cat-tag { font-size:10px; font-weight:700; color:__COR__; text-transform:uppercase; letter-spacing:.03em; }
.chip { font-size:11px; font-weight:700; padding:4px 12px; border-radius:999px; white-space:nowrap; }
.chip.ok { background:__OKBG__; color:__OK__; }
.chip.warn { background:__CLARA__; color:__COR__; }
.chip.muted { background:#EEE9E5; color:__MUTED__; }
.est { margin-bottom:16px; }
.est-top { color:__ESCURA__; display:flex; justify-content:space-between; font-size:13px; margin-bottom:6px; }
.est-qtd { color:__COR__; font-weight:700; }
.est-qtd.ok { color:__OK__; }
.track { background:#F3EEEA; height:6px; border-radius:6px; overflow:hidden; }
.fill { background:__COR__; height:100%; border-radius:6px; }
.fill.ok { background:__OK__; }
.cats { display:flex; gap:22px; flex-wrap:wrap; padding:6px 0 2px 0; }
.cat { text-align:center; min-width:84px; }
.cat-circulo { width:60px; height:60px; border-radius:50%; display:flex; align-items:center; justify-content:center;
  font-size:26px; margin:0 auto 8px auto; }
.cat-nome { color:__ESCURA__; font-size:13px; font-weight:600; }
.cat-valor { font-size:12px; color:__MUTED__; }
.vazio { color:__MUTED__; font-size:14px; padding:18px 4px; }

/* ---- botões e filtros ---- */
.stButton > button { width:100%; border-radius:12px; border:1px solid __BORDA__; background:#fff; color:__ESCURA__;
  font-weight:600; padding:.55rem 1rem; }
.stButton > button:hover { border-color:__COR__; color:__COR__; background:#fff; }
.st-key-ver_hist button { border:none; background:transparent; color:__COR__; font-weight:700; font-size:13px; width:auto; float:right; }
.st-key-ver_hist button:hover { background:transparent; text-decoration:underline; }
.st-key-pedidos_filtro [role="radiogroup"] { flex-direction:row; gap:8px; flex-wrap:wrap; }
.st-key-pedidos_filtro label { padding:6px 18px; border-radius:999px; border:1px solid __BORDA__; background:#fff; margin:0; cursor:pointer; }
.st-key-pedidos_filtro label > div:first-child { display:none; }
.st-key-pedidos_filtro label p { font-size:13px; font-weight:600; }
.st-key-pedidos_filtro label:has(input:checked) { background:__COR__; border-color:__COR__; }
.st-key-pedidos_filtro label:has(input:checked) p { color:#fff; }
</style>
"""
for k_, v_ in {"__FUNDO__": COR_FUNDO, "__ESCURA__": COR_ESCURA, "__BORDA__": COR_BORDA, "__COR__": COR,
               "__MUTED__": COR_MUTED, "__MARCA__": COR_MARCA, "__CLARA__": COR_CLARA, "__OK__": COR_OK, "__OKBG__": COR_OK_FUNDO}.items():
    CSS = CSS.replace(k_, v_)
st.markdown(CSS, unsafe_allow_html=True)


# =============================================================================
# FORMATAÇÃO E COMPONENTES HTML
# =============================================================================
def _stretch(fn, *a, **kw):
    """Funciona em versões novas (width='stretch') e antigas (use_container_width) do Streamlit."""
    try:
        return fn(*a, width="stretch", **kw)
    except Exception:
        return fn(*a, use_container_width=True, **kw)


def plot(dg, fig):
    return _stretch(dg.plotly_chart, fig, theme=None)


def tbl(dg, df, **kw):
    return _stretch(dg.dataframe, df, **kw)


def esc(x):
    return html.escape(str(x))


def brl(v):
    if v is None or pd.isna(v):
        return "—"
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(v):
    if v is None or pd.isna(v):
        return "—"
    return f"{v:.1f}%".replace(".", ",")


def num(v):
    return f"{int(v):,}".replace(",", ".")


def delta_badge(atual, anterior, inverso=False):
    """Variação % vs. período anterior -> (texto, tom). None se não houver base de comparação."""
    if anterior is None or pd.isna(anterior) or pd.isna(atual) or anterior == 0:
        return None, None
    v = (atual - anterior) / abs(anterior) * 100
    bom = (v <= 0) if inverso else (v >= 0)
    return f"{v:+.1f}%".replace(".", ","), ("up" if bom else "down")


def kpi(label, valor, sub="", badge=None, tom="up"):
    b = f'<span class="badge {tom}">{esc(badge)}</span>' if badge else ""
    return (f'<div class="kpi"><div class="kpi-top"><span class="kpi-label">{esc(label)}</span>{b}</div>'
            f'<div class="kpi-value">{esc(valor)}</div><div class="kpi-sub">{esc(sub)}</div></div>')


def titulo(texto, sub=""):
    s = f'<div class="card-sub">{esc(sub)}</div>' if sub else ""
    return f'<div class="card-title">{esc(texto)}</div>{s}'


def vazio(msg):
    return f'<div class="vazio">{esc(msg)}</div>'


def estilo(fig, h=340, legenda=False):
    fig.update_layout(
        height=h, margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, sans-serif", color=COR_ESCURA, size=13), showlegend=legenda,
        legend=dict(orientation="h", y=1.12, x=0), colorway=[COR, COR_ESCURA, "#F5B041", COR_OK, "#8E7CC3"],
    )
    eixo = dict(tickfont=dict(color=COR_TEXTO_GRAFICO), title_font=dict(color=COR_TEXTO_GRAFICO))
    fig.update_xaxes(showgrid=False, linecolor=COR_BORDA, **eixo)
    fig.update_yaxes(gridcolor="#F4EDE7", zeroline=False, **eixo)
    fig.update_layout(legend_font_color=COR_TEXTO_GRAFICO)
    return fig


def chip_status(status):
    cls = {STATUS_ENTREGUE: "ok", STATUS_ANDAMENTO: "warn", STATUS_CANCELADO: "muted"}.get(status, "muted")
    return f'<span class="chip {cls}">{esc(status)}</span>'


def rotulo_data(d, ref):
    if pd.isna(d):
        return "—"
    dia, r = d.normalize(), ref.normalize()
    if dia == r:
        return f"Hoje, {d:%H:%M}"
    if dia == r - pd.Timedelta(days=1):
        return f"Ontem, {d:%H:%M}"
    return f"{d:%d/%m}, {d:%H:%M}"


# =============================================================================
# CARGA DE DADOS (JSON)
# =============================================================================
def aplicar_mapa(nome, df):
    df = df.rename(columns=MAPEAMENTO.get(nome, {}))
    for col, mapa in MAPEAMENTO_VALORES.get(nome, {}).items():
        if mapa and col in df.columns:
            df[col] = df[col].replace(mapa)
    return df


def padronizar(nome, df):
    """Valida campos, cria opcionais ausentes e converte datas."""
    cfg = SCHEMA[nome]
    df = aplicar_mapa(nome, df.copy())
    df.columns = [str(c).strip().lower() for c in df.columns]
    faltando = [c for c in cfg["obrigatorias"] if c not in df.columns]
    if faltando:
        st.error(
            f"Tabela **{nome}**: faltam os campos {faltando}. Campos encontrados: {list(df.columns)}. "
            f"Ajuste o JSON ou o dicionário MAPEAMENTO no app.py."
        )
        st.stop()
    for c in cfg["opcionais"]:
        if c not in df.columns:
            df[c] = pd.NA
    for c in cfg["datas"]:
        df[c] = pd.to_datetime(df[c], errors="coerce", utc=True).dt.tz_localize(None)
    return df


def json_para_df(obj):
    """Lista de registros (ou {"qualquer_chave": [...]}) -> DataFrame, achatando campos aninhados."""
    if isinstance(obj, dict):
        listas = [v for v in obj.values() if isinstance(v, list)]
        obj = listas[0] if len(listas) == 1 else [obj]
    return pd.json_normalize(obj, sep="_")


def ler_json(fonte):
    if hasattr(fonte, "read"):
        return json.load(fonte)
    return json.loads(Path(fonte).read_text(encoding="utf-8"))


def carregar(uploads):
    """Prioridade: enviados na barra lateral > dados/dados.json > dados/<tabela>.json > dados/<tabela>.csv."""
    brutos = {}

    def registrar(obj, stem):
        if isinstance(obj, dict) and any(str(k).lower() in SCHEMA for k in obj):
            for k, v in obj.items():
                if str(k).lower() in SCHEMA and str(k).lower() not in brutos:
                    brutos[str(k).lower()] = json_para_df(v)
        elif stem in SCHEMA and stem not in brutos:
            brutos[stem] = json_para_df(obj)

    for up in uploads or []:
        stem = Path(up.name).stem.lower()
        if up.name.lower().endswith(".json"):
            try:
                registrar(ler_json(up), stem)
            except ValueError as e:
                st.error(f"JSON inválido em **{up.name}**: {e}")
                st.stop()
        elif up.name.lower().endswith(".csv") and stem in SCHEMA:
            brutos[stem] = pd.read_csv(up)

    if ARQUIVO_JSON_UNICO.exists():
        try:
            registrar(ler_json(ARQUIVO_JSON_UNICO), None)
        except ValueError as e:
            st.error(f"JSON inválido em **{ARQUIVO_JSON_UNICO.name}**: {e}")
            st.stop()
    for nome in SCHEMA:
        if nome not in brutos:
            arq_j, arq_c = PASTA_DADOS / f"{nome}.json", PASTA_DADOS / f"{nome}.csv"
            if arq_j.exists():
                registrar(ler_json(arq_j), nome)
            elif arq_c.exists():
                brutos[nome] = pd.read_csv(arq_c)

    # itens aninhados em pedidos ("itens": [...]) -> tabela itens_pedido
    if "itens_pedido" not in brutos and "pedidos" in brutos:
        ped = aplicar_mapa("pedidos", brutos["pedidos"])
        ped.columns = [str(c).strip().lower() for c in ped.columns]
        if "itens" in ped.columns and "pedido_id" in ped.columns:
            ex = ped[["pedido_id", "itens"]].explode("itens").dropna(subset=["itens"])
            if len(ex):
                brutos["itens_pedido"] = pd.concat(
                    [ex[["pedido_id"]].reset_index(drop=True), pd.json_normalize(ex["itens"].tolist(), sep="_")], axis=1)
            brutos["pedidos"] = ped.drop(columns="itens")

    faltam = [n for n, c in SCHEMA.items() if n not in brutos and not c.get("tabela_opcional")]
    if faltam:
        st.error(
            f"Não encontrei os dados de: **{faltam}**. Coloque o JSON em `{ARQUIVO_JSON_UNICO}` "
            "(objeto com essas chaves) ou envie em 'Dados e filtros'. Para gerar um exemplo: `python gerar_dados_exemplo.py`."
        )
        st.stop()
    out = {}
    for n, cfg in SCHEMA.items():
        if n in brutos:
            out[n] = padronizar(n, brutos[n])
        else:  # tabela opcional ausente -> vazia
            out[n] = pd.DataFrame(columns=cfg["obrigatorias"] + cfg["opcionais"])
    return out


# =============================================================================
# INDICADORES
# =============================================================================
def usuarios_unicos(ev, nome_evento):
    return ev.loc[ev["evento"] == nome_evento, "usuario_id"].nunique()

def calcular_kpis(ev, ped):
    validos = ped[ped["status"] != STATUS_CANCELADO]
    receita = validos["total"].sum()
    n_ped = len(validos)
    home = usuarios_unicos(ev, "ver_home")
    compradores = validos["usuario_id"].nunique()
    carrinho = usuarios_unicos(ev, "add_carrinho")
    compra_ev = usuarios_unicos(ev, "pedido_confirmado")
    logins = (ev["evento"] == "login").sum()
    entregues = ped[(ped["status"] == STATUS_ENTREGUE) & ped["data_entrega"].notna() & ped["previsao_entrega"].notna()]
    no_prazo = (entregues["data_entrega"] <= entregues["previsao_entrega"]).mean() * 100 if len(entregues) else float("nan")
    por_cliente = validos.groupby("usuario_id").size()
    return {
        "receita": receita,
        "pedidos": n_ped,
        "ticket": receita / n_ped if n_ped else 0,
        "conversao": compradores / home * 100 if home else 0,
        "abandono": (1 - compra_ev / carrinho) * 100 if carrinho else 0,
        "cadastros": int((ev["evento"] == "cadastro").sum()),
        "logins": int(logins),
        "esqueci_senha": (ev["evento"] == "esqueci_senha").sum() / logins * 100 if logins else 0,
        "cancelamento": (ped["status"] == STATUS_CANCELADO).mean() * 100 if len(ped) else 0,
        "no_prazo": no_prazo,
        "frete_gratis": (ped["frete"] == 0).mean() * 100 if len(ped) else 0,
        "ajuda": (ev["evento"] == "abrir_ajuda").sum() / n_ped * 100 if n_ped else 0,
        "assinantes": (validos["assinatura"].astype("string").str.lower().isin(["true", "1", "sim"])).mean() * 100 if n_ped else 0,
        "compradores": compradores,
        "recompra": (por_cliente > 1).mean() * 100 if len(por_cliente) else 0,
    }


# =============================================================================
# BARRA LATERAL: marca, navegacao, dados e filtros
# =============================================================================
st.sidebar.markdown(
    '<div class="brand"><div class="brand-logo">PL</div><div><div class="brand-nome">Petlove</div>'
    '<div class="brand-sub">PAINEL ADMIN</div></div></div>', unsafe_allow_html=True)
st.session_state.setdefault("nav", NAV[0])
pagina = st.sidebar.radio("Navegação", NAV, key="nav", label_visibility="collapsed")

with st.sidebar.expander("⚙️  Dados e filtros"):
    uploads = st.file_uploader(
        "Enviar dados (JSON)", type=["json", "csv"], accept_multiple_files=True,
        help="Um JSON com as chaves eventos, pedidos, itens_pedido, produtos (e opcionalmente usuarios, estoque) — ou um arquivo por tabela.",
    )
    dados = carregar(uploads)

    ev_all, ped_all = dados["eventos"], dados["pedidos"]
    itens_all, prod = dados["itens_pedido"], dados["produtos"]
    usuarios, estoque = dados["usuarios"], dados["estoque"]
    for df_, cols_ in ((ev_all, ["produto_id"]), (itens_all, ["produto_id", "qtd", "preco_unit"]), (prod, ["produto_id", "preco", "avaliacao"]),
                       (ped_all, ["total", "subtotal", "frete"]), (estoque, ["produto_id", "quantidade", "minimo"]),
                       (usuarios, ["usuario_id"])):
        for c_ in cols_:
            df_[c_] = pd.to_numeric(df_[c_], errors="coerce")

    dmin = min(ev_all["data"].min(), ped_all["data_pedido"].min()).normalize()
    dmax = max(ev_all["data"].max(), ped_all["data_pedido"].max()).normalize()
    periodo = st.selectbox("Período", ["Últimos 7 dias", "Últimos 30 dias", "Últimos 90 dias", "Mês atual",
                                       "Todo o período", "Personalizado"], index=1)
    ini = {"Últimos 7 dias": dmax - pd.Timedelta(days=6), "Últimos 30 dias": dmax - pd.Timedelta(days=29),
           "Últimos 90 dias": dmax - pd.Timedelta(days=89), "Mês atual": dmax.replace(day=1),
           "Todo o período": dmin}.get(periodo, dmin)
    fim = dmax
    if periodo == "Personalizado":
        faixa = st.date_input("Datas", value=(max(dmin, dmax - pd.Timedelta(days=29)).date(), dmax.date()),
                              min_value=dmin.date(), max_value=dmax.date())
        if isinstance(faixa, (list, tuple)) and len(faixa) == 2:
            ini, fim = pd.Timestamp(faixa[0]), pd.Timestamp(faixa[1])
    ini = max(ini, dmin)
    st.markdown("**Metas**")
    meta_receita = st.number_input("Faturamento no período (R$)", value=META_RECEITA, step=1000.0)
    meta_conv = st.number_input("Conversão (%)", value=META_CONVERSAO, step=0.5)
    meta_prazo = st.number_input("Entregas no prazo (%)", value=META_NO_PRAZO, step=1.0)

st.sidebar.markdown(
    f'<div style="height:30vh"></div><div class="usercard"><div class="avatar">{esc("".join(p[0] for p in USUARIO_NOME.split()[:2]))}</div>'
    f'<div><div class="user-nome">{esc(USUARIO_NOME)}</div><div class="user-cargo">{esc(USUARIO_CARGO)}</div></div></div>',
    unsafe_allow_html=True)

# ---- recortes do período atual e do anterior (mesmo tamanho)
dias = (fim - ini).days + 1
ini_ant, fim_ant = ini - pd.Timedelta(days=dias), ini - pd.Timedelta(days=1)


def recorte(df, col, a, b):
    d = df[col].dt.normalize()
    return df[(d >= a) & (d <= b)]


ev, ped = recorte(ev_all, "data", ini, fim), recorte(ped_all, "data_pedido", ini, fim)
if periodo == "Todo o período" or ini_ant < dmin:
    ev_a, ped_a = ev_all.iloc[0:0], ped_all.iloc[0:0]
else:
    ev_a, ped_a = recorte(ev_all, "data", ini_ant, fim_ant), recorte(ped_all, "data_pedido", ini_ant, fim_ant)
ped_validos = ped[ped["status"] != STATUS_CANCELADO]
itens = itens_all[itens_all["pedido_id"].isin(ped_validos["pedido_id"])]
k, ka = calcular_kpis(ev, ped), calcular_kpis(ev_a, ped_a)
REF = dmax  # "hoje" = último dia com dados

# ---- clientes e produtos (consulta rápida)
CLIENTES = {}
for r_ in usuarios.itertuples():
    if pd.isna(r_.usuario_id):
        continue
    nome_ = r_.nome if pd.notna(r_.nome) else f"Cliente #{int(r_.usuario_id)}"
    CLIENTES[int(r_.usuario_id)] = f"{nome_} ({r_.pet})" if pd.notna(r_.pet) else str(nome_)


def rotulo_cliente(uid):
    try:
        return CLIENTES.get(int(uid)) or f"Cliente #{int(uid)}"
    except (TypeError, ValueError):
        return str(uid)


NOME_PRODUTO = dict(zip(prod["produto_id"], prod["nome"]))
_it = itens_all.assign(nome=itens_all["produto_id"].map(NOME_PRODUTO).fillna("Produto"), _pid=itens_all["pedido_id"].astype(str))
RESUMO_ITENS = _it.groupby("_pid")["nome"].agg(
    lambda s: s.iloc[0] + (f" + {len(s) - 1} item" + ("s" if len(s) > 2 else "") if len(s) > 1 else "")).to_dict()


def ir_para(destino):
    st.session_state["nav"] = destino


def linhas_pedidos(df, rico=False):
    if not len(df):
        return vazio("Nenhum pedido encontrado.")
    out = []
    for r in df.itertuples():
        sub = esc(rotulo_cliente(r.usuario_id))
        if rico:
            sub += f" · {esc(RESUMO_ITENS.get(str(r.pedido_id), ''))}"
        out.append(
            f'<div class="row"><div><div class="row-id">#{esc(PREFIXO_PEDIDO)}{esc(r.pedido_id)}</div><div class="row-sub">{sub}</div></div>'
            f'<div class="row-right"><div class="row-meta"><div class="row-sub">{esc(rotulo_data(r.data_pedido, REF))}</div>'
            f'<div class="row-valor">{brl(r.total)}</div></div>{chip_status(r.status)}</div></div>')
    return "".join(out)


# ---- estoque
def montar_estoque():
    if not len(estoque):
        return pd.DataFrame()
    e = estoque.copy()
    e["minimo"] = e["minimo"].fillna(10)
    e["nome"] = e["produto_id"].map(NOME_PRODUTO).fillna("Produto " + e["produto_id"].astype(str))
    e["baixo"] = e["quantidade"] <= e["minimo"]
    e["critico"] = e["quantidade"] <= np.maximum(2, e["minimo"] * CRITICO_FRACAO)
    e["pct"] = (e["quantidade"] / (e["minimo"] * 3) * 100).clip(lower=4, upper=100)
    vend = itens.groupby("produto_id")["qtd"].sum() / max(dias, 1)
    e["vendas_dia"] = e["produto_id"].map(vend).fillna(0)
    e["cobertura_dias"] = np.where(e["vendas_dia"] > 0, e["quantidade"] / e["vendas_dia"].replace(0, np.nan), np.nan)
    return e.sort_values(["baixo", "pct"], ascending=[False, True])


EST = montar_estoque()


def linhas_estoque(df):
    if not len(df):
        return vazio("Sem itens para mostrar.")
    out = []
    for r in df.itertuples():
        q = int(r.quantidade)
        txt = f"{q} un restante" if r.baixo else f"{q} un em estoque"
        cls = "" if r.baixo else " ok"
        out.append(
            f'<div class="est"><div class="est-top"><span>{esc(r.nome)}</span><span class="est-qtd{cls}">{txt}</span></div>'
            f'<div class="track"><div class="fill{cls}" style="width:{r.pct:.0f}%"></div></div></div>')
    return "".join(out)


def tabela_produtos():
    vend = itens.assign(receita=itens["qtd"] * itens["preco_unit"]).groupby("produto_id").agg(
        unidades=("qtd", "sum"), receita=("receita", "sum"))
    vistas = ev[ev["evento"] == "ver_produto"].groupby("produto_id").size().rename("visualizacoes")
    favs = ev[ev["evento"] == "favoritar"].groupby("produto_id").size().rename("favoritos")
    t = prod.merge(vend, left_on="produto_id", right_index=True, how="left") \
            .merge(vistas, left_on="produto_id", right_index=True, how="left") \
            .merge(favs, left_on="produto_id", right_index=True, how="left")
    for c in ["unidades", "receita", "visualizacoes", "favoritos"]:
        t[c] = t[c].fillna(0)
    t["conv_pct"] = (t["unidades"] / t["visualizacoes"].replace(0, np.nan) * 100).round(1)
    return t


# =============================================================================
# TOPO
# =============================================================================
tit, subt = PAGINAS[pagina]
e_hoje = fim.normalize() == pd.Timestamp.today().normalize()
st.markdown(
    f'<div class="topbar"><div><h1>{esc(tit)}</h1><p>{esc(subt)}</p></div><div class="topbar-right">'
    f'<span class="pill-periodo">{ini:%d/%m/%Y} – {fim:%d/%m/%Y}</span>'
    f'<span>{MESES[fim.month]}, {fim.year}</span><span class="pill-hoje">{"HOJE" if e_hoje else f"até {fim:%d/%m}"}</span></div></div>',
    unsafe_allow_html=True)


# =============================================================================
# PÁGINAS
# =============================================================================
def kpis_principais():
    b1 = delta_badge(k["receita"], ka["receita"])
    b2 = delta_badge(k["pedidos"], ka["pedidos"])
    b3 = delta_badge(k["cadastros"], ka["cadastros"])
    novos = set(ev.loc[ev["evento"] == "cadastro", "usuario_id"])
    pets = [str(p) for p in usuarios[usuarios["usuario_id"].isin(novos)]["pet"].dropna().unique()[:2]]
    sub_cli = (", ".join(pets) + " & mais pets") if pets else "Cadastros no período"
    c = st.columns(4)
    c[0].markdown(kpi("Faturamento", brl(k["receita"]), f"Meta do período: {brl(meta_receita)}", b1[0], b1[1] or "up"), unsafe_allow_html=True)
    c[1].markdown(kpi("Pedidos processados", f"{num(k['pedidos'])} pedidos", f"Ticket médio: {brl(k['ticket'])}", b2[0], b2[1] or "up"), unsafe_allow_html=True)
    c[2].markdown(kpi("Novos clientes", f"{num(k['cadastros'])} tutores", sub_cli, b3[0], b3[1] or "up"), unsafe_allow_html=True)
    if len(EST):
        baixos, crit = int(EST["baixo"].sum()), int(EST["critico"].sum())
        c[3].markdown(kpi("Alertas de estoque", f"{baixos} itens baixos", "Requer reposição imediata" if baixos else "Estoque saudável",
                          f"{crit} críticos" if crit else None, "alert"), unsafe_allow_html=True)
    else:
        c[3].markdown(kpi("Alertas de estoque", "—", "Sem tabela de estoque no JSON"), unsafe_allow_html=True)


def kpis_secundarios():
    b = {n: delta_badge(k[n], ka[n], inverso=inv) for n, inv in
         [("conversao", False), ("abandono", True), ("no_prazo", False), ("cancelamento", True)]}
    c = st.columns(4)
    c[0].markdown(kpi("Conversão home → compra", pct(k["conversao"]), f"Meta: {pct(meta_conv)}", b["conversao"][0], b["conversao"][1] or "up"), unsafe_allow_html=True)
    c[1].markdown(kpi("Abandono de carrinho", pct(k["abandono"]), "Carrinho sem pedido confirmado", b["abandono"][0], b["abandono"][1] or "up"), unsafe_allow_html=True)
    c[2].markdown(kpi("Entregas no prazo", pct(k["no_prazo"]), f"Meta: {pct(meta_prazo)}", b["no_prazo"][0], b["no_prazo"][1] or "up"), unsafe_allow_html=True)
    c[3].markdown(kpi("Cancelamentos", pct(k["cancelamento"]), "% dos pedidos do período", b["cancelamento"][0], b["cancelamento"][1] or "up"), unsafe_allow_html=True)


def grafico_receita(dg):
    val = ped_validos.assign(dia=ped_validos["data_pedido"].dt.normalize())
    diario = val.groupby("dia").agg(receita=("total", "sum")).reset_index()
    if not len(diario):
        dg.markdown(vazio("Sem pedidos no período."), unsafe_allow_html=True)
        return
    diario["media_7d"] = diario["receita"].rolling(7, min_periods=1).mean()
    fig = go.Figure()
    fig.add_bar(x=diario["dia"], y=diario["receita"], name="Receita diária", marker_color=COR)
    fig.add_scatter(x=diario["dia"], y=diario["media_7d"], name="Média 7 dias", line=dict(color=COR_ESCURA, width=3))
    plot(dg, estilo(fig, 340, legenda=True))


def grafico_funil(dg):
    etapas = [(rot, usuarios_unicos(ev, nome)) for nome, rot in FUNIL]
    fun = go.Figure(go.Funnel(y=[e[0] for e in etapas], x=[e[1] for e in etapas], textinfo="value+percent previous",
                              marker=dict(color=[COR, "#FF8F82", "#FFA498", "#FFB9AF", "#FFCDC6"][:len(etapas)])))
    plot(dg, estilo(fun, 340))


def pagina_dashboard():
    kpis_principais()
    st.write("")
    kpis_secundarios()
    st.write("")
    esq, dir_ = st.columns([2, 1], gap="large")
    with esq:
        with st.container(border=True):
            h1, h2 = st.columns([3, 2])
            h1.markdown(titulo("Últimos Pedidos"), unsafe_allow_html=True)
            h2.button("Ver histórico completo", key="ver_hist", on_click=ir_para, args=(NAV[2],))
            st.markdown(linhas_pedidos(ped.sort_values("data_pedido", ascending=False).head(6)), unsafe_allow_html=True)
    with dir_:
        with st.container(border=True):
            st.markdown(titulo("Atenção ao Estoque"), unsafe_allow_html=True)
            if len(EST):
                st.markdown(linhas_estoque(EST[EST["baixo"]].head(5)) if EST["baixo"].any() else vazio("Nenhum item abaixo do mínimo."),
                            unsafe_allow_html=True)
            else:
                st.markdown(vazio("Envie a tabela `estoque` no JSON para acompanhar aqui."), unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(titulo("Atalhos Rápidos"), unsafe_allow_html=True)
            a, b = st.columns(2)
            a.button("Ver produtos", key="at_prod", on_click=ir_para, args=(NAV[1],))
            b.button("Ver estoque", key="at_est", on_click=ir_para, args=(NAV[3],))
    st.write("")
    g1, g2 = st.columns([3, 2], gap="large")
    with g1:
        with st.container(border=True):
            st.markdown(titulo("Faturamento por dia", "Barras: diário · linha: média móvel de 7 dias"), unsafe_allow_html=True)
            grafico_receita(st)
    with g2:
        with st.container(border=True):
            st.markdown(titulo("Funil de compra", "Usuários únicos por etapa"), unsafe_allow_html=True)
            grafico_funil(st)


def pagina_produtos():
    t = tabela_produtos()
    cats = t.groupby("categoria", as_index=False).agg(receita=("receita", "sum"), unidades=("unidades", "sum"))
    blocos = []
    for r in cats.sort_values("receita", ascending=False).itertuples():
        emoji, cor = CATEGORIAS.get(r.categoria, ("🐾", "#F3EEEA"))
        blocos.append(f'<div class="cat"><div class="cat-circulo" style="background:{cor}">{emoji}</div>'
                      f'<div class="cat-nome">{esc(r.categoria)}</div><div class="cat-valor">{brl(r.receita)}</div></div>')
    with st.container(border=True):
        st.markdown(titulo("Vendas por pet", "Faturamento por categoria no período") + f'<div class="cats">{"".join(blocos)}</div>',
                    unsafe_allow_html=True)
    st.write("")
    esq = st.container()
    with esq:
        with st.container(border=True):
            st.markdown(titulo("Petiscos e brinquedos populares", "Top 8 por faturamento"), unsafe_allow_html=True)
            top = t.sort_values("receita", ascending=False).head(8)
            linhas = []
            for r in top.itertuples():
                rating = f" · ★ {r.avaliacao:.1f}" if pd.notna(r.avaliacao) else ""
                conv = f'<span class="chip warn">{r.conv_pct:.1f}% conv.</span>' if pd.notna(r.conv_pct) else ""
                linhas.append(
                    f'<div class="row"><div><div class="cat-tag">{esc(r.categoria)}</div><div class="row-id">{esc(r.nome)}</div>'
                    f'<div class="row-sub">{num(r.visualizacoes)} visualizações · {num(r.favoritos)} favoritos{rating}</div></div>'
                    f'<div class="row-right">{conv}<div class="row-meta"><div class="row-sub">{num(r.unidades)} un</div>'
                    f'<div class="row-valor">{brl(r.receita)}</div></div></div></div>')
            st.markdown("".join(linhas) or vazio("Sem vendas no período."), unsafe_allow_html=True)
    with st.expander("Tabela completa de produtos"):
        tbl(st, t[["nome", "categoria", "preco", "avaliacao", "visualizacoes", "favoritos", "unidades", "receita", "conv_pct"]]
            .sort_values("receita", ascending=False), hide_index=True)


def pagina_pedidos():
    c = st.columns(4)
    c[0].markdown(kpi("Pedidos no período", num(len(ped)), f"{num(int((ped['status'] == STATUS_ANDAMENTO).sum()))} em andamento"), unsafe_allow_html=True)
    c[1].markdown(kpi("Frete grátis", pct(k["frete_gratis"]), "% de pedidos com frete zero"), unsafe_allow_html=True)
    c[2].markdown(kpi("Pedidos que pediram ajuda", pct(k["ajuda"]), "Atendimento via “Precisa de ajuda?”"), unsafe_allow_html=True)
    c[3].markdown(kpi("Pedidos por assinatura", pct(k["assinantes"]), "Benefício Petlove"), unsafe_allow_html=True)
    st.write("")
    a, b = st.columns(2, gap="large")
    with a:
        with st.container(border=True):
            st.markdown(titulo("Pedidos por status"), unsafe_allow_html=True)
            cnt = ped.groupby("status").size().reset_index(name="pedidos")
            plot(st, estilo(px.bar(cnt, x="status", y="pedidos", color_discrete_sequence=[COR]), 300))
    with b:
        with st.container(border=True):
            st.markdown(titulo("Atraso na entrega", "Dias além da previsão (pedidos entregues)"), unsafe_allow_html=True)
            ent = ped[(ped["status"] == STATUS_ENTREGUE) & ped["data_entrega"].notna() & ped["previsao_entrega"].notna()].copy()
            if len(ent):
                ent["atraso"] = (ent["data_entrega"] - ent["previsao_entrega"]).dt.days.clip(lower=0).astype(str) + " dia(s)"
                d = ent.groupby("atraso").size().reset_index(name="pedidos")
                plot(st, estilo(px.bar(d, x="atraso", y="pedidos", color_discrete_sequence=[COR_OK]), 300))
            else:
                st.markdown(vazio("Sem entregas concluídas no período."), unsafe_allow_html=True)
    st.write("")
    with st.container(border=True):
        st.markdown(titulo("Meus pedidos", "Filtre por status ou busque por nº do pedido / cliente"), unsafe_allow_html=True)
        filtro = st.radio("Status", ["Todos", "Em andamento", "Entregues", "Cancelados"], horizontal=True,
                          key="pedidos_filtro", label_visibility="collapsed")
        busca = st.text_input("Buscar", placeholder="Buscar por nº do pedido ou cliente…", label_visibility="collapsed")
        lista = ped.sort_values("data_pedido", ascending=False)
        alvo = {"Em andamento": STATUS_ANDAMENTO, "Entregues": STATUS_ENTREGUE, "Cancelados": STATUS_CANCELADO}.get(filtro)
        if alvo:
            lista = lista[lista["status"] == alvo]
        if busca.strip():
            q = busca.strip().lower().lstrip("#")
            alvo_txt = lista["pedido_id"].astype(str).str.lower() + " " + lista["usuario_id"].map(rotulo_cliente).str.lower()
            lista = lista[alvo_txt.str.contains(q.replace(PREFIXO_PEDIDO.lower(), ""), regex=False)]
        st.caption(f"{num(len(lista))} pedido(s) — mostrando os 30 mais recentes")
        st.markdown(linhas_pedidos(lista.head(30), rico=True), unsafe_allow_html=True)


def pagina_estoque():
    if not len(EST):
        with st.container(border=True):
            st.markdown(titulo("Estoque não informado", "Adicione a chave `estoque` ao seu JSON"), unsafe_allow_html=True)
            st.code('"estoque": [{"produto_id": 1, "quantidade": 5, "minimo": 20}]', language="json")
        return
    cob = EST["cobertura_dias"].median()
    c = st.columns(4)
    c[0].markdown(kpi("Itens baixos", num(EST["baixo"].sum()), "Quantidade ≤ mínimo", None), unsafe_allow_html=True)
    c[1].markdown(kpi("Críticos", num(EST["critico"].sum()), "Reposição imediata", None), unsafe_allow_html=True)
    c[2].markdown(kpi("Produtos no estoque", num(len(EST)), f"{num(EST['quantidade'].sum())} unidades no total"), unsafe_allow_html=True)
    c[3].markdown(kpi("Cobertura mediana", f"{cob:.0f} dias" if pd.notna(cob) else "—", "Estoque ÷ vendas médias por dia"), unsafe_allow_html=True)
    st.write("")
    with st.container(border=True):
        st.markdown(titulo("Níveis de estoque", "Do mais urgente ao mais confortável"), unsafe_allow_html=True)
        st.markdown(linhas_estoque(EST), unsafe_allow_html=True)
    with st.expander("Tabela de estoque"):
        tbl(st, EST[["nome", "quantidade", "minimo", "vendas_dia", "cobertura_dias"]].round(1), hide_index=True)


{NAV[0]: pagina_dashboard, NAV[1]: pagina_produtos, NAV[2]: pagina_pedidos,
 NAV[3]: pagina_estoque}[pagina]()
