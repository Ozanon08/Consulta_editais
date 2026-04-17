import os
import sqlite3
import hashlib
from datetime import datetime
from io import BytesIO

import pandas as pd
import streamlit as st

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(
    page_title="Portal de Consulta de Editais - FGV PMO",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_PATH = "editais.db"


# =========================================================
# ESTILO
# =========================================================

def aplicar_estilo_dark():
    st.markdown("""
    <style>

    .stApp {
        background: linear-gradient(180deg, #0b1120 0%, #0f172a 100%);
        color: #e2e8f0;
    }

    .block-container {
        color: #e2e8f0;
        padding-top: 1.2rem;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0b1220 0%, #163a63 100%);
        border-right: 1px solid rgba(255,255,255,0.08);
    }

    section[data-testid="stSidebar"] * {
        color: #ffffff !important;
    }

    .main-header {
        background: linear-gradient(135deg, #163a63 0%, #1f4e79 55%, #2563eb 100%);
        padding: 26px 28px;
        border-radius: 18px;
        color: white !important;
        margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.22);
        min-height: 125px;
    }

    .header-title {
        font-size: 2rem;
        font-weight: 800;
        color: white !important;
        margin-bottom: 6px;
        line-height: 1.1;
    }

    .header-subtitle {
        font-size: 0.98rem;
        color: rgba(255,255,255,0.92) !important;
        margin-bottom: 12px;
    }

    .header-profile {
        display: inline-block;
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.18);
        padding: 8px 12px;
        border-radius: 999px;
        font-size: 0.92rem;
        color: white !important;
    }

    .theme-switch-card {
        background: #111827;
        border: 1px solid #334155;
        border-radius: 18px;
        padding: 16px 14px;
        min-height: 125px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.18);
    }
    /* ===================== */
    /* LOGO */
    /* ===================== */
    .logo-card {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 125px;
    }

    .logo-img {
        max-width: 140px;
        object-fit: contain;
    }
    .theme-switch-label {
        color: #cbd5e1 !important;
        font-size: 0.9rem;
        font-weight: 700;
        margin-bottom: 10px;
        text-align: center;
    }

    .section-card {
        background: #111827;
        color: #e5e7eb;
        padding: 20px;
        border-radius: 16px;
        border: 1px solid #334155;
        margin-bottom: 15px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.14);
    }

    .metric-card {
        background: #111827;
        color: #e5e7eb;
        padding: 18px;
        border-radius: 16px;
        border: 1px solid #334155;
        box-shadow: 0 4px 14px rgba(0,0,0,0.14);
    }

    .metric-title {
        color: #94a3b8;
        font-size: 0.9rem;
        font-weight: 600;
    }

    .metric-value {
        color: #93c5fd;
        font-weight: 800;
        font-size: 1.8rem;
    }

    .metric-sub {
        color: #94a3b8;
    }

    input, textarea {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border: 1px solid #475569 !important;
        border-radius: 10px !important;
    }

    div[data-baseweb="select"] {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border-radius: 10px !important;
    }

    label {
        color: #e2e8f0 !important;
    }

    .stButton > button,
    .stDownloadButton > button {
        background: linear-gradient(135deg, #1f4e79, #2563eb);
        color: white;
        border-radius: 10px;
        border: none;
        font-weight: 700;
        box-shadow: 0 4px 12px rgba(37,99,235,0.25);
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #2563eb, #1f4e79);
        color: white;
    }

    .dataframe {
        color: #e2e8f0 !important;
    }

    .dataframe th {
        background-color: #1e293b !important;
        color: #93c5fd !important;
    }

    div[data-testid="stForm"] {
        background: #111827;
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 18px;
    }

    .login-card {
        background: #111827;
        color: #e2e8f0;
        border: 1px solid #334155;
        border-radius: 18px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.18);
    }

    .login-title {
        color: #93c5fd !important;
    }

    .login-subtitle,
    .small-muted {
        color: #cbd5e1 !important;
    }

    </style>
    """, unsafe_allow_html=True)
    
def aplicar_estilo_light():
    st.markdown("""
    <style>

    /* ===================== */
    /* BASE GERAL */
    /* ===================== */
    .stApp {
        background: linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
        color: #000000 !important;
    }

    .block-container {
        color: #000000 !important;
        padding-top: 1.2rem;
    }

    html, body, p, label, h1, h2, h3, h4, h5, h6, span {
        color: #000000 !important;
    }

    /* ===================== */
    /* SIDEBAR */
    /* ===================== */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #163a63 0%, #1f4e79 100%);
        border-right: 1px solid rgba(255,255,255,0.08);
    }

    section[data-testid="stSidebar"] * {
        color: #ffffff !important;
    }

    /* ===================== */
    /* HEADER */
    /* ===================== */
    .main-header {
        background: linear-gradient(135deg, #163a63 0%, #1f4e79 55%, #3b82c4 100%);
        padding: 26px 28px;
        border-radius: 18px;
        color: white !important;
        margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(31,78,121,0.18);
        min-height: 125px;
    }

    .header-title {
        font-size: 2rem;
        font-weight: 800;
        color: white !important;
        margin-bottom: 6px;
        line-height: 1.1;
    }

    .header-subtitle {
        font-size: 0.98rem;
        color: rgba(255,255,255,0.94) !important;
        margin-bottom: 12px;
    }

    .header-profile {
        display: inline-block;
        background: rgba(255,255,255,0.14);
        border: 1px solid rgba(255,255,255,0.20);
        padding: 8px 12px;
        border-radius: 999px;
        font-size: 0.92rem;
        color: white !important;
    }

    .theme-switch-card {
        background: #ffffff;
        border: 1px solid #dbe4f0;
        border-radius: 18px;
        padding: 16px 14px;
        min-height: 125px;
        box-shadow: 0 10px 30px rgba(31,78,121,0.10);
    }

    .theme-switch-label {
        color: #1f4e79 !important;
        font-size: 0.9rem;
        font-weight: 700;
        margin-bottom: 10px;
        text-align: center;
    }

    /* ===================== */
    /* CARDS */
    /* ===================== */
    .section-card {
        background: #ffffff;
        color: #000000 !important;
        padding: 20px;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        margin-bottom: 15px;
        box-shadow: 0 4px 14px rgba(15,23,42,0.05);
    }

    .metric-card {
        background: #ffffff;
        color: #000000 !important;
        padding: 18px;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 14px rgba(15,23,42,0.05);
    }

    .metric-title {
        color: #334155 !important;
        font-size: 0.9rem;
        font-weight: 600;
    }

    .metric-value {
        color: #1f4e79 !important;
        font-weight: 800;
        font-size: 1.8rem;
    }

    .metric-sub {
        color: #475569 !important;
    }
    /* ===================== */
    /* LOGO */
    /* ===================== */
    .logo-card {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 125px;
    }

    .logo-img {
        max-width: 140px;
        object-fit: contain;
    }

    /* ===================== */
    /* INPUTS TEXTO / NUMBER / TEXTAREA */
    /* ===================== */
    .stTextInput input,
    .stNumberInput input,
    .stTextArea textarea,
    input[type="text"],
    input[type="number"],
    textarea {
        background: #dff2ff !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        border: 1px solid #7dcfff !important;
        border-radius: 10px !important;
    }

    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder {
        color: #475569 !important;
        opacity: 1 !important;
    }

    /* ===================== */
    /* SELECTBOX FECHADO */
    /* ===================== */
    .stSelectbox > div > div,
    .stMultiSelect > div > div,
    div[data-baseweb="select"] > div {
        background: #dff2ff !important;
        border: 1px solid #7dcfff !important;
        border-radius: 10px !important;
        color: #000000 !important;
    }

    div[data-baseweb="select"] * {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }

    div[data-baseweb="select"] svg {
        fill: #1f4e79 !important;
    }

    /* ===================== */
    /* DROPDOWN ABERTO - BASEWEB */
    /* ===================== */
    div[data-baseweb="popover"] {
        background-color: transparent !important;
    }

    div[data-baseweb="menu"] {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 12px !important;
        padding: 4px !important;
        box-shadow: 0 10px 30px rgba(15,23,42,0.10) !important;
    }

    div[data-baseweb="menu"] * {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }

    div[data-baseweb="menu"] [role="option"] {
        background-color: #ffffff !important;
        color: #000000 !important;
        border-radius: 8px !important;
    }

    div[data-baseweb="menu"] [role="option"]:hover {
        background-color: #e0f2fe !important;
        color: #000000 !important;
    }

    div[data-baseweb="menu"] [aria-selected="true"] {
        background-color: #bae6fd !important;
        color: #000000 !important;
    }

    /* fallback extra */
    ul[role="listbox"] {
        background: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
    }

    ul[role="listbox"] li {
        background: #ffffff !important;
        color: #000000 !important;
    }

    ul[role="listbox"] li:hover {
        background: #e0f2fe !important;
        color: #000000 !important;
    }

    ul[role="listbox"] li[aria-selected="true"] {
        background: #bae6fd !important;
        color: #000000 !important;
    }

    /* ===================== */
    /* NUMBER INPUT BOTÕES */
    /* ===================== */
    .stNumberInput button {
        background: #dff2ff !important;
        color: #000000 !important;
        border: 1px solid #7dcfff !important;
    }

    /* ===================== */
    /* FOCO */
    /* ===================== */
    .stTextInput input:focus,
    .stNumberInput input:focus,
    .stTextArea textarea:focus,
    div[data-baseweb="select"] > div:focus-within {
        border: 1px solid #38bdf8 !important;
        box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.20) !important;
    }

    label {
        color: #000000 !important;
    }

    /* ===================== */
    /* BOTÕES */
    /* ===================== */
    .stButton > button,
    .stDownloadButton > button {
        background: linear-gradient(135deg, #1f4e79, #3b82c4);
        color: white !important;
        border-radius: 10px;
        border: none;
        font-weight: 700;
        box-shadow: 0 4px 12px rgba(31,78,121,0.20);
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #163a63, #1f4e79);
        color: white !important;
    }

    /* ===================== */
    /* TABELA */
    /* ===================== */
    .stDataFrame,
    div[data-testid="stDataFrame"] {
        background: #ffffff !important;
        border-radius: 12px !important;
    }

    div[data-testid="stDataFrame"] * {
        color: #000000 !important;
    }

    div[data-testid="stDataFrame"] [role="grid"] {
        background: #ffffff !important;
        color: #000000 !important;
    }

    div[data-testid="stDataFrame"] [role="row"] {
        background: #ffffff !important;
    }

    div[data-testid="stDataFrame"] [role="columnheader"] {
        background: #dbeafe !important;
        color: #1e3a8a !important;
        font-weight: 700 !important;
    }

    div[data-testid="stDataFrame"] [role="gridcell"] {
        background: #ffffff !important;
        color: #000000 !important;
    }

    .dataframe {
        background: #ffffff !important;
        color: #000000 !important;
    }

    .dataframe td {
        background: #ffffff !important;
        color: #000000 !important;
    }

    .dataframe th {
        background: #dbeafe !important;
        color: #1e3a8a !important;
    }

    /* ===================== */
    /* FORM */
    /* ===================== */
    div[data-testid="stForm"] {
        background: #ffffff;
        color: #000000 !important;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 18px;
    }

    /* ===================== */
    /* LOGIN */
    /* ===================== */
    .login-card {
        background: #ffffff;
        color: #000000 !important;
        border: 1px solid #e2e8f0;
        border-radius: 18px;
        box-shadow: 0 10px 30px rgba(15,23,42,0.08);
        padding: 28px;
    }

    .login-title {
        color: #1f4e79 !important;
        font-size: 1.8rem;
        font-weight: 700;
    }

    .login-subtitle,
    .small-muted {
        color: #000000 !important;
    }

    </style>
    """, unsafe_allow_html=True)
    
def aplicar_estilo(modo="light"):
    if modo == "dark":
        aplicar_estilo_dark()
    else:
        aplicar_estilo_light()


# =========================================================
# BANCO / UTIL
# =========================================================
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        senha_hash TEXT NOT NULL,
        perfil TEXT NOT NULL,
        ativo INTEGER NOT NULL DEFAULT 1,
        criado_em TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS solicitacoes_tema (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tema_solicitado TEXT NOT NULL,
        descricao TEXT,
        solicitante TEXT NOT NULL,
        perfil_solicitante TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'PENDENTE',
        data_solicitacao TEXT NOT NULL
    )
    """)

    cur.execute("""
    SELECT COUNT(*) FROM usuarios WHERE username = 'ADMIN'
    """)
    exists = cur.fetchone()[0]

    if exists == 0:
        cur.execute("""
        INSERT INTO usuarios (username, senha_hash, perfil, ativo, criado_em)
        VALUES (?, ?, ?, ?, ?)
        """, (
            "ADMIN",
            hash_senha("ADMIN123"),
            "ADMIN",
            1,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

    conn.commit()
    conn.close()


def carregar_view():
    conn = get_conn()
    try:
        df = pd.read_sql_query("SELECT * FROM vw_consulta_editais", conn)
    except Exception:
        df = pd.DataFrame()
    finally:
        conn.close()
    return df


def autenticar(username: str, senha: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    SELECT username, perfil, ativo
    FROM usuarios
    WHERE UPPER(username) = UPPER(?) AND senha_hash = ?
    """, (username, hash_senha(senha)))
    row = cur.fetchone()
    conn.close()

    if row and row[2] == 1:
        return {"username": row[0], "perfil": row[1]}
    return None


def listar_usuarios():
    conn = get_conn()
    df = pd.read_sql_query("""
        SELECT id, username, perfil, ativo, criado_em
        FROM usuarios
        ORDER BY username
    """, conn)
    conn.close()
    return df


def criar_usuario(username: str, senha: str, perfil: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO usuarios (username, senha_hash, perfil, ativo, criado_em)
    VALUES (?, ?, ?, ?, ?)
    """, (
        username.strip(),
        hash_senha(senha),
        perfil,
        1,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()


def alterar_status_usuario(user_id: int, ativo: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE usuarios SET ativo = ? WHERE id = ?", (ativo, user_id))
    conn.commit()
    conn.close()


def inserir_solicitacao(tema: str, descricao: str, solicitante: str, perfil: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO solicitacoes_tema (
        tema_solicitado, descricao, solicitante, perfil_solicitante, status, data_solicitacao
    )
    VALUES (?, ?, ?, ?, 'PENDENTE', ?)
    """, (
        tema.strip(),
        descricao.strip(),
        solicitante,
        perfil,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()


def listar_solicitacoes():
    conn = get_conn()
    df = pd.read_sql_query("""
        SELECT id, tema_solicitado, descricao, solicitante, perfil_solicitante, status, data_solicitacao
        FROM solicitacoes_tema
        ORDER BY id DESC
    """, conn)
    conn.close()
    return df


def atualizar_status_solicitacao(solicitacao_id: int, novo_status: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    UPDATE solicitacoes_tema
    SET status = ?
    WHERE id = ?
    """, (novo_status, solicitacao_id))
    conn.commit()
    conn.close()


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Consulta")
    return output.getvalue()


def formatar_numero(valor):
    try:
        return f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(valor)


def pode_solicitar(perfil):
    return perfil in ["ADMIN", "PMO", "COORDENADOR"]


def pode_ver_solicitacoes(perfil):
    return perfil in ["ADMIN", "PMO"]


def pode_gerenciar_usuarios(perfil):
    return perfil == "ADMIN"


def pode_substituir_base(perfil):
    return perfil in ["ADMIN", "PMO"]

def pode_baixar_arquivos(perfil):
    return perfil in ["ADMIN", "PMO"]


# =========================================================
# SESSION
# =========================================================
def init_session():
    if "logado" not in st.session_state:
        st.session_state.logado = False
    if "usuario" not in st.session_state:
        st.session_state.usuario = None
    if "perfil" not in st.session_state:
        st.session_state.perfil = None
    if "menu" not in st.session_state:
        st.session_state.menu = "Consulta"
    if "tema_visual" not in st.session_state:
        st.session_state.tema_visual = "Dark"


def logout():
    st.session_state.logado = False
    st.session_state.usuario = None
    st.session_state.perfil = None
    st.session_state.menu = "Consulta"
    st.rerun()


# =========================================================
# UI AUX
# =========================================================

import base64

def get_base64_logo():
    with open("assets/fgv pmo logo.png", "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()
    
    
def header_principal():
    tema_atual = st.session_state.get("tema_visual", "Light")

    col1, col2 = st.columns([6, 1.4])

    with col1:
        st.markdown(f"""
        <div class="main-header">
            <div class="header-title">Portal de Consulta de Editais - FGV PMO</div>
            <div class="header-subtitle">
                Consulta e busca de novos editais
            </div>
            <div class="header-profile">
                <b>Perfil ativo:</b> {st.session_state.perfil}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="logo-card">
            <img src="data:image/png;base64,{}" class="logo-img"/>
        </div>
        """.format(get_base64_logo()), unsafe_allow_html=True)

        novo_tema = st.segmented_control(
            label="Tema visual",
            options=["Light", "Dark"],
            default=tema_atual,
            label_visibility="collapsed",
            key="theme_selector_header"
        )

        st.markdown('</div>', unsafe_allow_html=True)

    if novo_tema and novo_tema != tema_atual:
        st.session_state.tema_visual = novo_tema
        st.rerun()


def metric_card(titulo, valor, subtitulo=""):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">{titulo}</div>
        <div class="metric-value">{valor}</div>
        <div class="metric-sub">{subtitulo}</div>
    </div>
    """, unsafe_allow_html=True)


# =========================================================
# LOGIN
# =========================================================
def tela_login():

    # CSS corrigido (remove espaço extra do Streamlit)
    st.markdown("""
    <style>

    /* REMOVE espaçamento padrão do topo */
    .block-container {
        padding-top: 0rem !important;
    }

    /* Container central */
    .login-container {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100vh;
        margin-top: -600px; /* ajuste fino */
    }

    .login-box {
        width: 420px;
    }

    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<div class="login-box">', unsafe_allow_html=True)

    st.markdown("""
    <div class="login-card">
        <div class="login-title" style="text-align:center;">FGV PMO</div>
        <div class="login-subtitle" style="text-align:center; margin-bottom:20px;">
            Portal de Consulta de Editais
        </div>
    """, unsafe_allow_html=True)

    with st.form("form_login", clear_on_submit=False):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")

        entrar = st.form_submit_button(
            "Entrar",
            use_container_width=True
        )


    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Login
    if entrar:
        user = autenticar(usuario, senha)
        if user:
            st.session_state.logado = True
            st.session_state.usuario = user["username"]
            st.session_state.perfil = user["perfil"]
            st.success("Login realizado com sucesso.")
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")


# =========================================================
# SIDEBAR
# =========================================================
def menu_sidebar():
    with st.sidebar:
        st.markdown("## Portal de Editais")
        st.markdown(f"**Usuário:** {st.session_state.usuario}")
        st.markdown("---")

        opcoes = ["Consulta"]

        if pode_solicitar(st.session_state.perfil):
            opcoes.append("Solicitações")

        opcoes.append("Base de dados")

        if pode_gerenciar_usuarios(st.session_state.perfil):
            opcoes.append("Usuários")

        escolha = st.radio("Menu", opcoes, index=opcoes.index(st.session_state.menu) if st.session_state.menu in opcoes else 0)
        st.session_state.menu = escolha

        st.markdown("---")
        if st.button("Sair", use_container_width=True):
            logout()


# =========================================================
# CONSULTA
# =========================================================
def pagina_consulta():
    header_principal()

    df = carregar_view()

    if df.empty:
        st.warning("A view 'vw_consulta_editais' não foi encontrada ou não possui dados.")
        return

    # Padronização defensiva
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].fillna("").astype(str)

    colunas_esperadas = {
        "tema": "Tema",
        "subtema": "Subtema",
        "estado": "Estado",
        "municipio": "Municipio",
        "tipo_edital": "Tipo edital",
        "fonte": "Fonte",
        "servicos": "Servicos",
        "nome": "Nome",
        "descricao": "Descricao",
        "codigo": "Codigo",
        "observacao": "Observacao",
        "custo": "Custo",
        "prazo_meses": "Prazo_meses",
        "data_edital": "Data_edital"
    }

    df.columns = [c.strip() for c in df.columns]

    def achar_coluna(preferidas):
        for p in preferidas:
            for c in df.columns:
                if c.lower() == p.lower():
                    return c
        return None

    col_tema = achar_coluna(["tema"])
    col_subtema = achar_coluna(["subtema"])
    col_estado = achar_coluna(["estado"])
    col_municipio = achar_coluna(["municipio", "município"])
    col_tipo = achar_coluna(["tipo_edital", "tipo edital"])
    col_fonte = achar_coluna(["fonte", "fonte_dado"])
    col_servicos = achar_coluna(["servicos", "serviços", "servico", "serviço"])
    col_nome = achar_coluna(["nome", "denominacao", "denominação"])
    col_desc = achar_coluna(["descricao", "descrição"])
    col_codigo = achar_coluna(["codigo", "código", "codigo_planilha"])
    col_obs = achar_coluna(["observacao", "observação", "obs"])
    col_custo = achar_coluna(["custo", "valor"])
    col_prazo = achar_coluna(["prazo_meses", "prazo", "prazo_meses"])
    col_data = achar_coluna(["data_edital", "data edital", "data"])

    if col_custo:
        df[col_custo] = pd.to_numeric(df[col_custo], errors="coerce")
    if col_prazo:
        df[col_prazo] = pd.to_numeric(df[col_prazo], errors="coerce")
    if col_data:
        df[col_data] = pd.to_datetime(df[col_data], errors="coerce")

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Filtros de consulta")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        tema = st.selectbox("Tema", ["Todos"] + sorted(df[col_tema].dropna().replace("", pd.NA).dropna().unique().tolist()) if col_tema else ["Todos"])
    with c2:
        subtema = st.selectbox("Subtema", ["Todos"] + sorted(df[col_subtema].dropna().replace("", pd.NA).dropna().unique().tolist()) if col_subtema else ["Todos"])
    with c3:
        estado = st.selectbox("Estado", ["Todos"] + sorted(df[col_estado].dropna().replace("", pd.NA).dropna().unique().tolist()) if col_estado else ["Todos"])
    with c4:
        municipio = st.selectbox("Município", ["Todos"] + sorted(df[col_municipio].dropna().replace("", pd.NA).dropna().unique().tolist()) if col_municipio else ["Todos"])

    c5 = st.columns(1)[0]

    with c5:
        busca = st.text_input("Busca textual", placeholder="Nome, descrição, código...")

    c9, c10, c11, c12 = st.columns(4)

    custo_min = c9.number_input("Custo mínimo", min_value=0.0, value=0.0, step=1000.0, format="%.2f")
    custo_max = c10.number_input("Custo máximo", min_value=0.0, value=0.0, step=1000.0, format="%.2f")
    prazo_min = c11.number_input("Prazo mínimo (meses)", min_value=0.0, value=0.0, step=1.0, format="%.2f")
    prazo_max = c12.number_input("Prazo máximo (meses)", min_value=0.0, value=0.0, step=1.0, format="%.2f")

    st.markdown('</div>', unsafe_allow_html=True)

    filtrado = df.copy()

    if col_tema and tema != "Todos":
        filtrado = filtrado[filtrado[col_tema] == tema]
    if col_subtema and subtema != "Todos":
        filtrado = filtrado[filtrado[col_subtema] == subtema]
    if col_estado and estado != "Todos":
        filtrado = filtrado[filtrado[col_estado] == estado]
    if col_municipio and municipio != "Todos":
        filtrado = filtrado[filtrado[col_municipio] == municipio]


    if busca:
        texto_cols = [c for c in [col_nome, col_desc, col_codigo, col_obs] if c]
        if texto_cols:
            mask = False
            for c in texto_cols:
                mask = mask | filtrado[c].astype(str).str.contains(busca, case=False, na=False)
            filtrado = filtrado[mask]

    if col_custo:
        if custo_min > 0:
            filtrado = filtrado[filtrado[col_custo] >= custo_min]
        if custo_max > 0:
            filtrado = filtrado[filtrado[col_custo] <= custo_max]

    if col_prazo:
        if prazo_min > 0:
            filtrado = filtrado[filtrado[col_prazo] >= prazo_min]
        if prazo_max > 0:
            filtrado = filtrado[filtrado[col_prazo] <= prazo_max]

    total_registros = len(filtrado)
    total_temas = filtrado[col_tema].nunique() if col_tema else 0
    total_estados = filtrado[col_estado].nunique() if col_estado else 0
    custo_medio = filtrado[col_custo].mean() if col_custo and not filtrado.empty else 0

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        metric_card("Registros filtrados", total_registros, )
    with m2:
        metric_card("Temas", total_temas, )
    with m3:
        metric_card("Estados", total_estados, )
    with m4:
        metric_card("Custo médio", formatar_numero(custo_medio if pd.notna(custo_medio) else 0), )

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Resultados")

    # Colunas que NÃO queremos mostrar
    colunas_remover = [
        "tipo_edital",
        "codigo_planilha",
        "fonte_dado",
        "metodo_calculo",
        "valor_min",
        "valor_max",
        "observacao"
    ]

    colunas_remover_existentes = [c for c in colunas_remover if c in filtrado.columns]

    df_exibicao = filtrado.drop(columns=colunas_remover_existentes)

    # =========================
    # RENOMEAR COLUNAS
    # =========================
    mapa_colunas = {
        "codigo": "Código",
        "nome": "Nome",
       "descricao": "Descrição",
        "tema": "Tema",
        "subtema": "Subtema",
        "pais": "País",
        "estado": "Estado",
        "municipio": "Município",
        "nome_edital": "Edital",
        "esforco" : "Esforço",
        "unidade" :"Unidade",
        "servicos": "Serviços",
        "custo_execucao": "Custo (R$)",
        "prazo_meses": "Prazo (meses)",
        "data_edital": "Data do edital"
    }

    # Aplica apenas se a coluna existir
    df_exibicao = df_exibicao.rename(columns={
        k: v for k, v in mapa_colunas.items() if k in df_exibicao.columns
})
    
# =========================
# FORMATAÇÕES (AQUI 👇)
# =========================

    # Data
    if "Data do edital" in df_exibicao.columns:
        df_exibicao["Data do edital"] = pd.to_datetime(
            df_exibicao["Data do edital"], errors="coerce"
        ).dt.strftime("%d/%m/%Y")

    # Custo
    if "Custo (R$)" in df_exibicao.columns:
        df_exibicao["Custo (R$)"] = df_exibicao["Custo (R$)"].apply(
            lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            if pd.notnull(x) else ""
        )

# =========================
# EXIBIÇÃO FINAL
# =========================
    st.dataframe(df_exibicao, use_container_width=True, hide_index=True)

    if pode_baixar_arquivos(st.session_state.perfil):
        col_dl1, col_dl2 = st.columns([1, 5])

        with col_dl1:
            st.download_button(
                "Baixar CSV",
                data=filtrado.to_csv(index=False).encode("utf-8-sig"),
                file_name="consulta_editais.csv",
                mime="text/csv",
                use_container_width=True
            )

        with col_dl2:
            st.download_button(
                "Baixar Excel",
                data=to_excel_bytes(filtrado),
                file_name="consulta_editais.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=False
            )
#    else:
#        st.info("Seu perfil possui acesso apenas à visualização. O download de arquivos está disponível somente para ADMIN e PMO.")
#        st.markdown('</div>', unsafe_allow_html=True)

    if not filtrado.empty:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Detalhe do registro")

        indice = st.selectbox("Selecione um registro para detalhar", filtrado.index.tolist(), format_func=lambda x: f"Registro {x}")
        linha = filtrado.loc[indice]

        detalhes = pd.DataFrame({
            "Campo": linha.index,
            "Valor": linha.values
        })
        st.dataframe(detalhes, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# SOLICITAÇÕES
# =========================================================
def pagina_solicitacoes():
    header_principal()

    if pode_solicitar(st.session_state.perfil):
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Solicitar busca de novos editais")

        with st.form("form_solicitacao_tema", clear_on_submit=True):
            tema = st.text_input("Tema da pesquisa")
            descricao = st.text_area("Descrição complementar", placeholder="Explique melhor o tema, palavras-chave, região, tipo de edital, observações...")
            enviar = st.form_submit_button("Enviar solicitação")

        if enviar:
            if not tema.strip():
                st.warning("Informe o tema da pesquisa.")
            else:
                inserir_solicitacao(
                    tema=tema,
                    descricao=descricao,
                    solicitante=st.session_state.usuario,
                    perfil=st.session_state.perfil
                )
                st.success("Solicitação registrada com sucesso.")
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    if pode_ver_solicitacoes(st.session_state.perfil):
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Solicitações recebidas")

        df_sol = listar_solicitacoes()
        if df_sol.empty:
            st.info("Nenhuma solicitação cadastrada.")
        else:
            st.dataframe(df_sol, use_container_width=True, hide_index=True)

            st.markdown("### Atualizar status")
            c1, c2 = st.columns(2)
            with c1:
                ids = df_sol["id"].tolist()
                solicitacao_id = st.selectbox("ID da solicitação", ids)
            with c2:
                novo_status = st.selectbox("Novo status", ["PENDENTE", "EM ANÁLISE", "CONCLUÍDA", "RECUSADA"])

            if st.button("Salvar status"):
                atualizar_status_solicitacao(solicitacao_id, novo_status)
                st.success("Status atualizado.")
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Minhas solicitações")
        df_sol = listar_solicitacoes()
        df_sol = df_sol[df_sol["solicitante"].str.upper() == st.session_state.usuario.upper()]
        if df_sol.empty:
            st.info("Você ainda não possui solicitações.")
        else:
            st.dataframe(df_sol, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# BASE DE DADOS
# =========================================================
def pagina_base():
    header_principal()

    df = carregar_view()

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Visualização da base")

    if df.empty:
        st.warning("A view 'vw_consulta_editais' não foi encontrada ou não possui dados.")
    else:
        st.dataframe(df.head(500), use_container_width=True, hide_index=True)
        st.caption("Exibindo até 500 linhas para visualização.")

    st.markdown('</div>', unsafe_allow_html=True)
    

    if pode_substituir_base(st.session_state.perfil):
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Substituir base de dados")

        st.info("Área reservada para ADMIN e PMO. Aqui você pode implementar a carga de uma nova planilha para atualizar a base.")

        arquivo = st.file_uploader("Selecione uma planilha", type=["xlsx", "xls", "csv"])

        if arquivo is not None:
            st.success(f"Arquivo carregado: {arquivo.name}")
            st.caption("Neste ponto você pode conectar a rotina que lê a planilha e atualiza o banco.")

        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
#        st.subheader("Permissão")
#        st.warning("Seu perfil não possui permissão para substituir a base.")
        st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# USUÁRIOS
# =========================================================
def pagina_usuarios():
    header_principal()

    if not pode_gerenciar_usuarios(st.session_state.perfil):
        st.error("Acesso restrito ao perfil ADMIN.")
        return

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Criar novo usuário")

    with st.form("form_novo_usuario", clear_on_submit=True):
        novo_user = st.text_input("Usuário")
        nova_senha = st.text_input("Senha", type="password")
        perfil = st.selectbox("Perfil", ["ADMIN", "PMO", "COORDENADOR", "GERAL"])
        criar = st.form_submit_button("Criar usuário")

    if criar:
        if not novo_user.strip() or not nova_senha.strip():
            st.warning("Preencha usuário e senha.")
        else:
            try:
                criar_usuario(novo_user, nova_senha, perfil)
                st.success("Usuário criado com sucesso.")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("Já existe um usuário com esse nome.")
            except Exception as e:
                st.error(f"Erro ao criar usuário: {e}")

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Usuários cadastrados")

    df_users = listar_usuarios()
    if df_users.empty:
        st.info("Nenhum usuário cadastrado.")
    else:
        df_exib = df_users.copy()
        df_exib["ativo"] = df_exib["ativo"].map({1: "Sim", 0: "Não"})
        st.dataframe(df_exib, use_container_width=True, hide_index=True)

        st.markdown("### Ativar / desativar usuário")
        c1, c2 = st.columns(2)
        with c1:
            user_id = st.selectbox("Usuário", df_users["id"].tolist(), format_func=lambda x: f"{x} - {df_users.loc[df_users['id']==x, 'username'].values[0]}")
        with c2:
            status = st.selectbox("Novo status", ["Ativo", "Inativo"])

        if st.button("Salvar alteração"):
            alterar_status_usuario(user_id, 1 if status == "Ativo" else 0)
            st.success("Status atualizado com sucesso.")
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# MAIN
# =========================================================
def main():
    init_db()
    init_session()

    tema_visual = st.session_state.get("tema_visual", "Dark")
    aplicar_estilo("dark" if tema_visual == "Dark" else "light")

    if not st.session_state.logado:
        tela_login()
        return

    menu_sidebar()

    if st.session_state.menu == "Consulta":
        pagina_consulta()
    elif st.session_state.menu == "Solicitações":
        pagina_solicitacoes()
    elif st.session_state.menu == "Base de dados":
        pagina_base()
    elif st.session_state.menu == "Usuários":
        pagina_usuarios()


if __name__ == "__main__":
    main()