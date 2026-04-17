import os
import sqlite3
import hashlib
import smtplib
import base64
from datetime import datetime
from io import BytesIO
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
SMTP_SERVER = os.getenv("SMTP_SERVER", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USER)
LOGO_PATH = os.path.join("assets", "fgv pmo logo.png")


# =========================================================
# ESTILO
# =========================================================
def aplicar_estilo_dark():
    st.markdown("""
    <style>

    /* ===================== */
    /* BASE */
    /* ===================== */
    .stApp {
        background: linear-gradient(180deg, #0b1120 0%, #0f172a 100%) !important;
        color: #e2e8f0 !important;
    }

    .block-container {
        color: #e2e8f0 !important;
        padding-top: 0rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        padding-bottom: 1rem !important;
        max-width: 100% !important;
    }

    .header-inner {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 24px;
        width: 100%;
    }

    .header-text-block {
        flex: 1;
        min-width: 0;
    }

    .header-logo-block {
        flex-shrink: 0;
        display: flex;
        align-items: center;
        justify-content: flex-end;
    }

    .header-logo-full {
        height: 70px;
        max-width: 260px;
        object-fit: contain;
        display: block;
        opacity: 0.95;
        pointer-events: none;
    }

    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 0rem !important;
    }

    section.main > div {
        padding-top: 0rem !important;
    }

    div[data-testid="stVerticalBlock"] > div:first-child {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }

    /* ===================== */
    /* SIDEBAR */
    /* ===================== */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0b1220 0%, #163a63 100%) !important;
        border-right: 1px solid rgba(255,255,255,0.08) !important;
    }

    section[data-testid="stSidebar"] * {
        color: #ffffff !important;
    }

    section[data-testid="stSidebar"] .block-container {
        padding-top: 0rem !important;
        padding-left: 0.85rem !important;
        padding-right: 0.85rem !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:first-child {
        margin-top: -14px !important;
        padding-top: 0 !important;
    }

    .theme-toggle-mini {
        margin: -6px 4px 2px 4px !important;
        padding-top: 0 !important;
    }

    .sidebar-logo-wrap {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        padding: 2px 0 10px 0 !important;
    }

    .sidebar-logo-img {
        width: 230px !important;
        max-width: 100% !important;
        object-fit: contain !important;
        filter: none !important;
        opacity: 1 !important;
    }

    /* ===================== */
    /* HEADER */
    /* ===================== */
    .header-full-width {
        background: linear-gradient(90deg, #163a63 0%, #1f4e79 55%, #2563eb 100%);
        padding: 26px 28px 22px 32px;
        color: white !important;
        min-height: 132px;
        width: 100%;
        margin: 0 !important;
        border-radius: 0 !important;
        box-shadow: none !important;
        overflow: hidden !important;
    }

    .header-title {
        font-size: 2rem !important;
        font-weight: 800 !important;
        color: white !important;
        margin-bottom: 8px !important;
        line-height: 1.15 !important;
    }

    .header-subtitle {
        font-size: 1rem !important;
        color: rgba(255,255,255,0.92) !important;
        margin-bottom: 14px !important;
    }

    .header-profile {
        display: inline-block !important;
        background: rgba(255,255,255,0.12) !important;
        border: 1px solid rgba(255,255,255,0.18) !important;
        padding: 8px 12px !important;
        border-radius: 999px !important;
        font-size: 0.92rem !important;
        color: white !important;
    }

    /* ===================== */
    /* CARDS */
    /* ===================== */
    .section-card {
        background: #111827 !important;
        color: #e5e7eb !important;
        padding: 20px !important;
        border-radius: 16px !important;
        border: 1px solid #334155 !important;
        margin: 0 16px 15px 16px !important;
        box-shadow: 0 4px 14px rgba(0,0,0,0.14) !important;
    }

    .metric-card {
        background: #111827 !important;
        color: #e5e7eb !important;
        padding: 18px !important;
        border-radius: 16px !important;
        border: 1px solid #334155 !important;
        box-shadow: 0 4px 14px rgba(0,0,0,0.14) !important;
    }

    .metric-title {
        color: #94a3b8 !important;
        font-size: 0.9rem !important;
        font-weight: 600 !important;
    }

    .metric-value {
        color: #93c5fd !important;
        font-weight: 800 !important;
        font-size: 1.8rem !important;
    }

    .metric-sub {
        color: #94a3b8 !important;
    }

    /* ===================== */
    /* INPUTS */
    /* ===================== */
    .stTextInput input,
    .stNumberInput input,
    .stTextArea textarea,
    input[type="text"],
    input[type="number"],
    textarea {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        -webkit-text-fill-color: #f8fafc !important;
        border: 1px solid #475569 !important;
        border-radius: 10px !important;
    }

    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder {
        color: #cbd5e1 !important;
        opacity: 1 !important;
    }

    .stSelectbox > div > div,
    .stMultiSelect > div > div,
    div[data-baseweb="select"] > div {
        background: #1e293b !important;
        border: 1px solid #475569 !important;
        border-radius: 10px !important;
        color: #f8fafc !important;
    }

    div[data-baseweb="select"] * {
        color: #f8fafc !important;
        -webkit-text-fill-color: #f8fafc !important;
    }

    div[data-baseweb="select"] svg {
        fill: #93c5fd !important;
    }

    div[data-baseweb="menu"] {
        background-color: #111827 !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
    }

    div[data-baseweb="menu"] * {
        color: #f8fafc !important;
        -webkit-text-fill-color: #f8fafc !important;
    }

    .stNumberInput button {
        background: #1e293b !important;
        color: #f8fafc !important;
        border: 1px solid #475569 !important;
    }

    label {
        color: #e2e8f0 !important;
    }

    /* ===================== */
    /* BOTÕES GERAIS */
    /* ===================== */
    .stButton > button,
    .stDownloadButton > button,
    .stFormSubmitButton > button {
        background: linear-gradient(135deg, #1f4e79, #2563eb) !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 12px rgba(37,99,235,0.25) !important;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover,
    .stFormSubmitButton > button:hover {
        background: linear-gradient(135deg, #2563eb, #1f4e79) !important;
        color: #ffffff !important;
    }

    .stButton > button:disabled,
    .stDownloadButton > button:disabled,
    .stFormSubmitButton > button:disabled {
        background: #334155 !important;
        color: #cbd5e1 !important;
        opacity: 1 !important;
        border: 1px solid #475569 !important;
        box-shadow: none !important;
    }

    section[data-testid="stSidebar"] .stButton > button {
        height: 24px !important;
        min-height: 24px !important;
        padding: 0 !important;
        font-size: 12px !important;
        border-radius: 6px !important;
        box-shadow: none !important;
        background: #2563eb !important;
        color: white !important;
        border: none !important;
        font-weight: 600 !important;
    }

    section[data-testid="stSidebar"] .stButton > button:hover {
        background: #1d4ed8 !important;
        color: white !important;
    }

    /* ===================== */
    /* TABELA DARK ZEBRADA */
    /* ===================== */
    div[data-testid="stDataFrame"] {
        background: #0f172a !important;
        border-radius: 12px !important;
        border: 1px solid #334155 !important;
    }

    div[data-testid="stDataFrame"] div[role="grid"] {
        background: #0f172a !important;
    }

    div[data-testid="stDataFrame"] div[role="row"] {
        background: #0f172a !important;
    }

    div[data-testid="stDataFrame"] div[role="row"]:nth-child(even) {
        background: #111827 !important;
    }

    div[data-testid="stDataFrame"] div[role="gridcell"] {
        color: #e2e8f0 !important;
        border-bottom: 1px solid #334155 !important;
    }

    div[data-testid="stDataFrame"] div[role="row"]:hover {
        background: #1e293b !important;
    }

    div[data-testid="stDataFrame"] div[role="columnheader"] {
        background: #1e293b !important;
        color: #93c5fd !important;
        font-weight: 600 !important;
        border-bottom: 1px solid #475569 !important;
    }

    /* ===================== */
    /* LOGIN */
    /* ===================== */
    .login-card {
        background: #111827 !important;
        color: #e2e8f0 !important;
        border: 1px solid #334155 !important;
        border-radius: 18px !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.18) !important;
        padding: 10px !important;
    }

    .login-title {
        color: #93c5fd !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
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

    .stApp {
        background: linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%) !important;
        color: #000000 !important;
    }

    .header-inner {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 24px;
        width: 100%;
    }

    .header-text-block {
        flex: 1;
        min-width: 0;
    }

    .header-logo-block {
        flex-shrink: 0;
        display: flex;
        align-items: center;
        justify-content: flex-end;
    }

    .header-logo-full {
        height: 70px;
        max-width: 260px;
        object-fit: contain;
        display: block;
        opacity: 0.95;
        pointer-events: none;
    }

    .block-container {
        color: #000000 !important;
        padding-top: 0rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        padding-bottom: 1rem !important;
        max-width: 100% !important;
    }

    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 0rem !important;
    }

    section.main > div {
        padding-top: 0rem !important;
    }

    div[data-testid="stVerticalBlock"] > div:first-child {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }

    /* SIDEBAR */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #163a63 0%, #1f4e79 100%) !important;
        border-right: 1px solid rgba(255,255,255,0.08) !important;
    }

    section[data-testid="stSidebar"] * {
        color: #ffffff !important;
    }

    section[data-testid="stSidebar"] .block-container {
        padding-top: 0rem !important;
        padding-left: 0.85rem !important;
        padding-right: 0.85rem !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:first-child {
        margin-top: -14px !important;
        padding-top: 0 !important;
    }

    .theme-toggle-mini {
        margin: -6px 4px 2px 4px !important;
        padding-top: 0 !important;
    }

    section[data-testid="stSidebar"] .stButton > button {
        height: 24px !important;
        min-height: 24px !important;
        padding: 0 !important;
        font-size: 12px !important;
        border-radius: 6px !important;
        box-shadow: none !important;
        background: #2563eb !important;
        color: white !important;
        -webkit-text-fill-color: white !important;
        border: none !important;
        font-weight: 600 !important;
    }

    section[data-testid="stSidebar"] .stButton > button:hover {
        background: #1d4ed8 !important;
        color: white !important;
    }

    .sidebar-logo-wrap {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 2px 0 10px 0;
    }

    .sidebar-logo-img {
        width: 230px;
        max-width: 100%;
        object-fit: contain;
        filter: brightness(1.35) contrast(1.2);
        opacity: 1;
    }

    /* HEADER */
    .header-full-width {
        background: linear-gradient(90deg, #163a63 0%, #1f4e79 55%, #2563eb 100%) !important;
        padding: 26px 28px 22px 32px !important;
        color: white !important;
        min-height: 132px !important;
        width: 100% !important;
        margin: 0 !important;
        border-radius: 0 !important;
        box-shadow: none !important;
        overflow: hidden !important;
    }

    .header-title {
        font-size: 2rem !important;
        font-weight: 800 !important;
        color: white !important;
        margin-bottom: 8px !important;
        line-height: 1.15 !important;
    }

    .header-subtitle {
        font-size: 1rem !important;
        color: rgba(255,255,255,0.94) !important;
        margin-bottom: 14px !important;
    }

    .header-profile {
        display: inline-block !important;
        background: rgba(255,255,255,0.14) !important;
        border: 1px solid rgba(255,255,255,0.20) !important;
        padding: 8px 12px !important;
        border-radius: 999px !important;
        font-size: 0.92rem !important;
        color: white !important;
    }

    .section-card {
        background: #ffffff !important;
        color: #000000 !important;
        padding: 20px !important;
        border-radius: 16px !important;
        border: 1px solid #e2e8f0 !important;
        margin: 0 16px 15px 16px !important;
        box-shadow: 0 4px 14px rgba(15,23,42,0.05) !important;
    }

    .metric-card {
        background: #ffffff !important;
        color: #000000 !important;
        padding: 18px !important;
        border-radius: 16px !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: 0 4px 14px rgba(15,23,42,0.05) !important;
    }

    .metric-title {
        color: #334155 !important;
        font-size: 0.9rem !important;
        font-weight: 600 !important;
    }

    .metric-value {
        color: #1f4e79 !important;
        font-weight: 800 !important;
        font-size: 1.8rem !important;
    }

    .metric-sub {
        color: #475569 !important;
    }

    /* INPUTS */
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

    div[data-baseweb="menu"] {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 12px !important;
    }

    div[data-baseweb="menu"] * {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }

    .stNumberInput button {
        background: #dff2ff !important;
        color: #000000 !important;
        border: 1px solid #7dcfff !important;
    }

    label {
        color: #000000 !important;
    }

    /* BOTÕES LIGHT */
    .stButton > button,
    .stDownloadButton > button,
    .stFormSubmitButton > button {
        background: linear-gradient(135deg, #1f4e79, #3b82c4) !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 12px rgba(31,78,121,0.20) !important;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover,
    .stFormSubmitButton > button:hover {
        background: linear-gradient(135deg, #163a63, #1f4e79) !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }

    .stButton > button:disabled,
    .stDownloadButton > button:disabled,
    .stFormSubmitButton > button:disabled {
        background: #dbe4f0 !important;
        color: #64748b !important;
        -webkit-text-fill-color: #64748b !important;
        border: 1px solid #cbd5e1 !important;
        box-shadow: none !important;
        opacity: 1 !important;
    }

    /* mantém só os botões da sidebar pequenos */
    section[data-testid="stSidebar"] .stButton > button {
        height: 24px !important;
        min-height: 24px !important;
        padding: 0 !important;
        font-size: 12px !important;
        border-radius: 6px !important;
        box-shadow: none !important;
        background: #2563eb !important;
        color: white !important;
        -webkit-text-fill-color: white !important;
        border: none !important;
        font-weight: 600 !important;
    }

    section[data-testid="stSidebar"] .stButton > button:hover {
        background: #1d4ed8 !important;
        color: white !important;
    }

    /* TABELA LIGHT ZEBRADA */
    div[data-testid="stDataFrame"] {
        background: #ffffff !important;
        border: 1px solid #dbe4f0 !important;
        border-radius: 12px !important;
    }

    div[data-testid="stDataFrame"] div[role="grid"] {
        background: #ffffff !important;
    }

    div[data-testid="stDataFrame"] div[role="row"] {
        background: #ffffff !important;
    }

    div[data-testid="stDataFrame"] div[role="row"]:nth-child(even) {
        background: #f8fafc !important;
    }

    div[data-testid="stDataFrame"] div[role="gridcell"] {
        color: #0f172a !important;
        border-bottom: 1px solid #e2e8f0 !important;
    }

    div[data-testid="stDataFrame"] div[role="row"]:hover {
        background: #eaf2ff !important;
    }

    div[data-testid="stDataFrame"] div[role="columnheader"] {
        background: #e8f1ff !important;
        color: #1e3a8a !important;
        font-weight: 600 !important;
        border-bottom: 1px solid #cbd5e1 !important;
    }

    /* LOGIN */
    .login-card {
        background: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 18px !important;
        box-shadow: 0 10px 30px rgba(15,23,42,0.08) !important;
        padding: 10px !important;
    }

    .login-title {
        color: #1f4e79 !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }

    .login-subtitle,
    .small-muted,
    .login-footer {
        color: #000000 !important;
    }

    .login-card .stTextInput input {
        background: #eef6ff !important;
        color: #0f172a !important;
        border: 1px solid #93c5fd !important;
        border-radius: 10px !important;
    }

    .login-card .stTextInput input::placeholder {
        color: #64748b !important;
    }

    .login-card .stForm {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

    .login-card button[kind="primary"],
    .login-card .stFormSubmitButton button {
        background: linear-gradient(135deg, #1f4e79, #2563eb) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        height: 42px !important;
    }

    .login-card button[kind="primary"]:hover,
    .login-card .stFormSubmitButton button:hover {
        background: linear-gradient(135deg, #163a63, #1d4ed8) !important;
        color: white !important;
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

    garantir_coluna_se_nao_existir(cur, "usuarios", "email", "TEXT")
    garantir_coluna_se_nao_existir(cur, "usuarios", "atualizado_em", "TEXT")

    cur.execute("SELECT COUNT(*) FROM usuarios WHERE username = 'ADMIN'")
    exists = cur.fetchone()[0]

    if exists == 0:
        cur.execute("""
        INSERT INTO usuarios (username, email, senha_hash, perfil, ativo, criado_em, atualizado_em)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            "ADMIN",
            "",
            hash_senha("ADMIN123"),
            "ADMIN",
            1,
            agora_str(),
            agora_str()
        ))

    conn.commit()
    conn.close()


def garantir_coluna_se_nao_existir(cur, tabela: str, coluna: str, definicao_sql: str):
    cur.execute(f"PRAGMA table_info({tabela})")
    colunas = [row[1] for row in cur.fetchall()]
    if coluna not in colunas:
        cur.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {definicao_sql}")


def agora_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


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
    SELECT username, perfil, ativo, email
    FROM usuarios
    WHERE UPPER(username) = UPPER(?) AND senha_hash = ?
    """, (username, hash_senha(senha)))
    row = cur.fetchone()
    conn.close()

    if row and row[2] == 1:
        return {"username": row[0], "perfil": row[1], "email": row[3] if len(row) > 3 else ""}
    return None


def listar_usuarios():
    conn = get_conn()
    df = pd.read_sql_query("""
        SELECT id, username, COALESCE(email, '') AS email, perfil, ativo, criado_em
        FROM usuarios
        ORDER BY username
    """, conn)
    conn.close()
    return df


def criar_usuario(username: str, email: str, senha: str, perfil: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO usuarios (username, email, senha_hash, perfil, ativo, criado_em, atualizado_em)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        username.strip(),
        email.strip(),
        hash_senha(senha),
        perfil,
        1,
        agora_str(),
        agora_str()
    ))
    conn.commit()
    conn.close()


def alterar_status_usuario(user_id: int, ativo: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE usuarios SET ativo = ?, atualizado_em = ? WHERE id = ?", (ativo, agora_str(), user_id))
    conn.commit()
    conn.close()


def excluir_usuario(user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM usuarios WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


def alterar_senha_usuario(username: str, senha_atual: str, nova_senha: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT senha_hash FROM usuarios WHERE UPPER(username) = UPPER(?)", (username,))
    row = cur.fetchone()

    if not row:
        conn.close()
        return False, "Usuário não encontrado."

    if row[0] != hash_senha(senha_atual):
        conn.close()
        return False, "Senha atual incorreta."

    cur.execute(
        "UPDATE usuarios SET senha_hash = ?, atualizado_em = ? WHERE UPPER(username) = UPPER(?)",
        (hash_senha(nova_senha), agora_str(), username)
    )
    conn.commit()
    conn.close()
    return True, "Senha alterada com sucesso."


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
        agora_str()
    ))
    solicitacao_id = cur.lastrowid
    conn.commit()
    conn.close()
    return solicitacao_id


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
    cur.execute("UPDATE solicitacoes_tema SET status = ? WHERE id = ?", (novo_status, solicitacao_id))
    conn.commit()
    conn.close()


def obter_solicitacao_por_id(solicitacao_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, tema_solicitado, descricao, solicitante, perfil_solicitante, status, data_solicitacao
        FROM solicitacoes_tema
        WHERE id = ?
    """, (solicitacao_id,))
    row = cur.fetchone()
    conn.close()
    return row


def buscar_emails_admins():
    conn = get_conn()
    df = pd.read_sql_query("""
        SELECT email
        FROM usuarios
        WHERE perfil = 'ADMIN'
          AND ativo = 1
          AND email IS NOT NULL
          AND TRIM(email) <> ''
    """, conn)
    conn.close()
    return df["email"].tolist()


def buscar_email_usuario(username: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT email FROM usuarios WHERE UPPER(username) = UPPER(?)", (username,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row and row[0] else ""


def enviar_email(destinatarios, assunto: str, corpo_html: str):
    if not destinatarios:
        return False, "Nenhum destinatário informado."

    if not all([SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, EMAIL_FROM]):
        return False, "SMTP não configurado. Defina SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD e EMAIL_FROM."

    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_FROM
        msg["To"] = ", ".join(destinatarios)
        msg["Subject"] = assunto
        msg.attach(MIMEText(corpo_html, "html", "utf-8"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(EMAIL_FROM, destinatarios, msg.as_string())

        return True, None
    except Exception as e:
        return False, str(e)


def enviar_email_nova_solicitacao_para_admins(tema: str, descricao: str, solicitante: str, perfil: str, solicitacao_id: int):
    emails_admin = buscar_emails_admins()
    if not emails_admin:
        return False, "Nenhum ADMIN com e-mail cadastrado."

    assunto = f"Nova solicitação de edital - ID {solicitacao_id}"
    corpo = f"""
    <h3>Nova solicitação cadastrada</h3>
    <p><b>ID:</b> {solicitacao_id}</p>
    <p><b>Solicitante:</b> {solicitante}</p>
    <p><b>Perfil:</b> {perfil}</p>
    <p><b>Tema:</b> {tema}</p>
    <p><b>Descrição:</b> {descricao if descricao else '-'}</p>
    <p><b>Data:</b> {agora_str()}</p>
    """
    return enviar_email(emails_admin, assunto, corpo)


def enviar_email_atualizacao_status_para_solicitante(solicitacao_id: int, tema: str, solicitante: str, novo_status: str):
    email_solicitante = buscar_email_usuario(solicitante)
    if not email_solicitante:
        return False, "Solicitante sem e-mail cadastrado."

    assunto = f"Atualização da solicitação de edital - ID {solicitacao_id}"
    corpo = f"""
    <h3>Status da solicitação atualizado</h3>
    <p><b>ID:</b> {solicitacao_id}</p>
    <p><b>Tema:</b> {tema}</p>
    <p><b>Solicitante:</b> {solicitante}</p>
    <p><b>Novo status:</b> {novo_status}</p>
    <p><b>Data da atualização:</b> {agora_str()}</p>
    """
    return enviar_email([email_solicitante], assunto, corpo)


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
    return perfil in ["ADMIN", "PMO", "COORDENADOR"]


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
    if "email" not in st.session_state:
        st.session_state.email = None
    if "menu" not in st.session_state:
        st.session_state.menu = "Consulta"
    if "tema_visual" not in st.session_state:
        st.session_state.tema_visual = "Light"


def logout():
    st.session_state.logado = False
    st.session_state.usuario = None
    st.session_state.perfil = None
    st.session_state.email = None
    st.session_state.menu = "Consulta"
    st.rerun()


# =========================================================
# UI AUX
# =========================================================
def get_base64_logo():
    if not os.path.exists(LOGO_PATH):
        return ""
    with open(LOGO_PATH, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()
    
def get_base64_logo_completo():
    with open("assets/FGV_PMO_LOGO_COMPLETO.png", "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

def header_principal():
    logo_b64 = get_base64_logo_completo()

    st.markdown(
        f"""
        <div class="header-full-width">
            <div class="header-inner">
                <div class="header-text-block">
                    <div class="header-title">Portal de Consulta de Editais - FGV PMO</div>
                    <div class="header-subtitle">Consulta e busca de novos editais</div>
                    <div class="header-profile"><b>Perfil ativo:</b> {st.session_state.perfil}</div>
                </div>
                <div class="header-logo-block">
                    <img src="data:image/png;base64,{logo_b64}" class="header-logo-full"/>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


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
    st.markdown("""
    <style>
    .login-page-wrap {
        min-height: 0vh;
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 0px;
    }

    .login-panel {
        width: 100%;
        max-width: 420px;
    }

    .login-brand {
        text-align: center;
        margin-bottom: 18px;
    }

    .login-brand img {
        width: 220px;
        max-width: 100%;
        object-fit: contain;
        margin-bottom: 10px;
    }

    .login-card {
        padding: 5px;
    }

    .login-title {
        text-align: center;
        font-size: 1.9rem;
        font-weight: 800;
        margin-bottom: 8px;
    }

    .login-subtitle {
        text-align: center;
        font-size: 0.98rem;
        margin-bottom: 22px;
        opacity: 0.9;
    }

    .login-footer {
        margin-top: 16px;
        text-align: center;
        font-size: 0.88rem;
        opacity: 0.85;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-page-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="login-panel">', unsafe_allow_html=True)

    st.markdown("""
    <div class="login-brand">
        <img src="data:image/png;base64,{}" />
    </div>
    """.format(get_base64_logo()), unsafe_allow_html=True)

    st.markdown("""
    <div class="login-card">
        <div class="login-title">Portal de Consulta de Editais</div>
        <div class="login-subtitle">FGV PMO</div>
    """, unsafe_allow_html=True)

    with st.form("form_login", clear_on_submit=False):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar", use_container_width=True)

    st.markdown("""
        <div class="login-footer">
            Acesso restrito a usuários autorizados
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if entrar:
        user = autenticar(usuario, senha)
        if user:
            st.session_state.logado = True
            st.session_state.usuario = user["username"]
            st.session_state.perfil = user["perfil"]
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")


# =========================================================
# SIDEBAR
# =========================================================
def menu_sidebar():
    with st.sidebar:
        tema_atual = st.session_state.get("tema_visual", "Light")

        st.markdown('<div class="theme-toggle-mini">', unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            if st.button("☀", key="btn_light", use_container_width=True):
                if tema_atual != "Light":
                    st.session_state.tema_visual = "Light"
                    st.rerun()

        with col2:
            if st.button("☾", key="btn_dark", use_container_width=True):
                if tema_atual != "Dark":
                    st.session_state.tema_visual = "Dark"
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("""
        <div class="sidebar-logo-wrap">
            <img src="data:image/png;base64,{}" class="sidebar-logo-img"/>
        </div>
        """.format(get_base64_logo()), unsafe_allow_html=True)

        st.markdown("## Portal de Editais")
        st.markdown(f"**Usuário:** {st.session_state.usuario}")

        opcoes = ["Consulta"]

        if pode_solicitar(st.session_state.perfil):
            opcoes.append("Solicitações")

        opcoes.append("Base de dados")
        opcoes.append("Minha conta")

        if pode_gerenciar_usuarios(st.session_state.perfil):
            opcoes.append("Usuários")

        escolha = st.radio(
            "Menu",
            opcoes,
            index=opcoes.index(st.session_state.menu) if st.session_state.menu in opcoes else 0
        )
        st.session_state.menu = escolha

        st.markdown("---")
        if st.button("Sair", use_container_width=True, key="btn_sair_sidebar"):
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

    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].fillna("").astype(str)

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
    col_nome = achar_coluna(["nome", "denominacao", "denominação"])
    col_desc = achar_coluna(["descricao", "descrição"])
    col_codigo = achar_coluna(["codigo", "código", "codigo_planilha"])
    col_obs = achar_coluna(["observacao", "observação", "obs"])
    col_custo = achar_coluna(["custo", "valor", "custo_execucao"])
    col_prazo = achar_coluna(["prazo_meses", "prazo"])
    col_data = achar_coluna(["data_edital", "data edital", "data"])

    if col_custo:
        df[col_custo] = pd.to_numeric(df[col_custo], errors="coerce")
    if col_prazo:
        df[col_prazo] = pd.to_numeric(df[col_prazo], errors="coerce")
    if col_data:
        df[col_data] = pd.to_datetime(df[col_data], errors="coerce")


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
        metric_card("Registros filtrados", total_registros)
    with m2:
        metric_card("Temas", total_temas)
    with m3:
        metric_card("Estados", total_estados)
    with m4:
        metric_card("Custo médio", formatar_numero(custo_medio if pd.notna(custo_medio) else 0))


    st.subheader("Resultados")

    colunas_remover = [
        "tipo_edital", "codigo_planilha", "fonte_dado", "metodo_calculo", "valor_min", "valor_max", "observacao"
    ]
    colunas_remover_existentes = [c for c in colunas_remover if c in filtrado.columns]
    df_exibicao = filtrado.drop(columns=colunas_remover_existentes)

    mapa_colunas = {
        "codigo": "Código",
        "nome": "Nome",
        "descricao": "Objetivo do Projeto",
        "tema": "Tema",
        "subtema": "Subtema",
        "pais": "País",
        "estado": "Estado",
        "municipio": "Município",
        "nome_edital": "Edital",
        "esforco": "Parâmetro utilizado para verificação do prazo",
        "unidade": "Unidade de Medida do Parâmetro ",
        "servicos": "Serviços",
        "custo_execucao": "Custo (R$)",
        "custo": "Custo (R$)",
        "prazo_meses": "Prazo (meses)",
        "data_edital": "Data do edital"
    }
    df_exibicao = df_exibicao.rename(columns={k: v for k, v in mapa_colunas.items() if k in df_exibicao.columns})

    if "Data do edital" in df_exibicao.columns:
        df_exibicao["Data do edital"] = pd.to_datetime(df_exibicao["Data do edital"], errors="coerce").dt.strftime("%d/%m/%Y")
    if "Custo (R$)" in df_exibicao.columns:
        df_exibicao["Custo (R$)"] = df_exibicao["Custo (R$)"].apply(
            lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if pd.notnull(x) else ""
        )

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
            descricao = st.text_area("Descrição complementar", placeholder="Explique melhor o tema, palavras-chave, região, observações...")
            enviar = st.form_submit_button("Enviar solicitação")

        if enviar:
            if not tema.strip():
                st.warning("Informe o tema da pesquisa.")
            else:
                solicitacao_id = inserir_solicitacao(
                    tema=tema,
                    descricao=descricao,
                    solicitante=st.session_state.usuario,
                    perfil=st.session_state.perfil
                )
                ok_email, msg_email = enviar_email_nova_solicitacao_para_admins(
                    tema=tema,
                    descricao=descricao,
                    solicitante=st.session_state.usuario,
                    perfil=st.session_state.perfil,
                    solicitacao_id=solicitacao_id
                )
                if ok_email:
                    st.success("Solicitação registrada com sucesso e notificação enviada aos administradores.")
                else:
                    st.success("Solicitação registrada com sucesso.")
                    st.info(f"Aviso sobre e-mail: {msg_email}")
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
                dados_sol = obter_solicitacao_por_id(solicitacao_id)
                if not dados_sol:
                    st.error("Solicitação não encontrada.")
                else:
                    _, tema_solicitado, _, solicitante, _, _, _ = dados_sol
                    atualizar_status_solicitacao(solicitacao_id, novo_status)
                    ok_email, msg_email = enviar_email_atualizacao_status_para_solicitante(
                        solicitacao_id=solicitacao_id,
                        tema=tema_solicitado,
                        solicitante=solicitante,
                        novo_status=novo_status
                    )
                    if ok_email:
                        st.success("Status atualizado e e-mail enviado ao solicitante.")
                    else:
                        st.success("Status atualizado.")
                        st.info(f"Aviso sobre e-mail: {msg_email}")
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


# =========================================================
# MINHA CONTA
# =========================================================
def pagina_minha_conta():
    header_principal()

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Minha conta")
    st.write(f"**Usuário:** {st.session_state.usuario}")
    st.write(f"**Perfil:** {st.session_state.perfil}")
    st.write(f"**E-mail:** {st.session_state.email or '-'}")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Alterar senha")
    with st.form("form_alterar_senha", clear_on_submit=True):
        senha_atual = st.text_input("Senha atual", type="password")
        nova_senha = st.text_input("Nova senha", type="password")
        confirmar_senha = st.text_input("Confirmar nova senha", type="password")
        salvar = st.form_submit_button("Salvar nova senha")

    if salvar:
        if not senha_atual or not nova_senha or not confirmar_senha:
            st.warning("Preencha todos os campos.")
        elif nova_senha != confirmar_senha:
            st.error("A confirmação da nova senha não confere.")
        elif len(nova_senha) < 6:
            st.error("A nova senha deve ter pelo menos 6 caracteres.")
        else:
            ok, msg = alterar_senha_usuario(st.session_state.usuario, senha_atual, nova_senha)
            if ok:
                st.success(msg)
            else:
                st.error(msg)

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
        novo_email = st.text_input("E-mail")
        nova_senha = st.text_input("Senha", type="password")
        perfil = st.selectbox("Perfil", ["ADMIN", "PMO", "COORDENADOR", "GERAL"])
        criar = st.form_submit_button("Criar usuário")

    if criar:
        if not novo_user.strip() or not nova_senha.strip():
            st.warning("Preencha usuário e senha.")
        elif not novo_email.strip():
            st.warning("Preencha o e-mail do usuário.")
        else:
            try:
                criar_usuario(novo_user, novo_email, nova_senha, perfil)
                st.success("Usuário criado com sucesso.")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("Já existe um usuário com esse nome ou e-mail.")
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

        st.markdown("### Gerenciar usuário")
        c1, c2 = st.columns(2)
        with c1:
            user_id = st.selectbox(
                "Usuário",
                df_users["id"].tolist(),
                format_func=lambda x: f"{x} - {df_users.loc[df_users['id'] == x, 'username'].values[0]}"
            )
        with c2:
            status = st.selectbox("Novo status", ["Ativo", "Inativo"])

        c3, c4 = st.columns(2)
        with c3:
            if st.button("Salvar alteração de status", use_container_width=True):
                alterar_status_usuario(user_id, 1 if status == "Ativo" else 0)
                st.success("Status atualizado com sucesso.")
                st.rerun()

        with c4:
            if st.button("Excluir usuário", use_container_width=True):
                username_selecionado = df_users.loc[df_users["id"] == user_id, "username"].values[0]
                if username_selecionado.upper() == st.session_state.usuario.upper():
                    st.error("Você não pode excluir o próprio usuário logado.")
                elif username_selecionado.upper() == "ADMIN":
                    st.error("Não é permitido excluir o usuário ADMIN padrão.")
                else:
                    excluir_usuario(user_id)
                    st.success("Usuário excluído com sucesso.")
                    st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Configuração de e-mail")
    if all([SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, EMAIL_FROM]):
        st.success("SMTP configurado. Os e-mails automáticos estão habilitados.")
    else:
        st.warning("SMTP não configurado. Defina SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD e EMAIL_FROM como variáveis de ambiente.")
    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# MAIN
# =========================================================
def main():
    init_db()
    init_session()

    tema_visual = st.session_state.get("tema_visual", "Light")
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
    elif st.session_state.menu == "Minha conta":
        pagina_minha_conta()
    elif st.session_state.menu == "Usuários":
        pagina_usuarios()


if __name__ == "__main__":
    main()
