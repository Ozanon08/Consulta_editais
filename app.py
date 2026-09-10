import os
import hashlib
import hmac
import logging
import threading
import bcrypt
import smtplib
import base64
from datetime import datetime, timezone
from io import BytesIO

logger = logging.getLogger(__name__)
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import pandas as pd
import psycopg2
import streamlit as st

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(
    page_title="FGV PMO - Portal de Consulta de Editais",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATABASE_URL = os.environ.get("DATABASE_URL", "")
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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /*  TOKENS  */
    :root {
        --fgv-navy:      #0b1f3a;
        --fgv-blue:      #1a3f6f;
        --fgv-mid:       #1e5799;
        --fgv-accent:    #2979d4;
        --fgv-bright:    #4d9fff;
        --ink-primary:   #e8edf4;
        --ink-secondary: #94a8c2;
        --ink-muted:     #5a7296;
        --surface-0:     #071628;
        --surface-1:     #0d1e33;
        --surface-2:     #122440;
        --surface-3:     #1a2f52;
        --border:        rgba(41, 121, 212, 0.18);
        --border-strong: rgba(41, 121, 212, 0.35);
        --radius-sm: 6px;
        --radius-md: 10px;
        --radius-lg: 16px;
        --shadow-sm: 0 1px 4px rgba(0,0,0,.3);
        --shadow-md: 0 4px 16px rgba(0,0,0,.4);
        --shadow-lg: 0 8px 32px rgba(0,0,0,.5);
        --font: 'Inter', system-ui, sans-serif;
    }

    /*  BASE  */
    .stApp { background: var(--surface-0) !important; color: var(--ink-primary) !important; font-family: var(--font) !important; }
    .block-container { padding: 0 !important; max-width: 100% !important; color: var(--ink-primary) !important; }
    header[data-testid="stHeader"] { background: transparent !important; height: 0 !important; }
    section.main > div { padding-top: 0 !important; }
    div[data-testid="stVerticalBlock"] > div:first-child { margin-top: 0 !important; padding-top: 0 !important; }
    * { font-family: var(--font) !important; }
    p, li { color: var(--ink-primary) !important; }

    /* Esconde apenas o texto "keyboard_double_arrow" dentro do botão de colapso */
    [class*="keyboard_double_arrow"] { display: none !important; }

    /*  SIDEBAR  */
    section[data-testid="stSidebar"] {
        background: linear-gradient(170deg, var(--fgv-navy) 0%, var(--fgv-blue) 100%) !important;
        border-right: 1px solid var(--border-strong) !important;
    }
    section[data-testid="stSidebar"] * { color: #fff !important; }
    section[data-testid="stSidebar"] .block-container { padding: 0 0.75rem !important; }
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:first-child { margin-top: -14px !important; }
    .theme-toggle-mini { margin: -6px 4px 2px !important; }

    /* Theme toggle buttons */
    .theme-toggle-mini .stButton > button {
        font-size: 0.7rem !important;
        padding: 2px 6px !important;
        height: 26px !important;
        letter-spacing: 0.08em !important;
        font-weight: 600 !important;
        color: rgba(255,255,255,0.7) !important;
        -webkit-text-fill-color: rgba(255,255,255,0.7) !important;
        background: transparent !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        border-radius: 4px !important;
        box-shadow: none !important;
        transform: none !important;
        min-height: 26px !important;
    }
    .theme-toggle-mini .stButton > button:hover {
        background: rgba(255,255,255,0.12) !important;
        color: #fff !important;
        -webkit-text-fill-color: #fff !important;
        transform: none !important;
    }
    .sidebar-logo-wrap { display: flex; justify-content: center; padding: 2px 0 10px; }
    .sidebar-logo-wrap img,
    .sidebar-logo-wrap .sidebar-logo-img {
        display: block !important;
        visibility: visible !important;
        opacity: 0.92 !important;
        max-height: none !important;
        max-width: 100% !important;
    }
    .sidebar-logo-img {
        width: 220px; max-width: 100%; object-fit: contain;
        filter: brightness(0) invert(1) !important;
        opacity: 0.92 !important;
        display: block !important;
        visibility: visible !important;
    }
    section[data-testid="stSidebar"] .stButton > button {
        background: rgba(255,255,255,0.06) !important;
        color: rgba(255,255,255,0.85) !important;
        -webkit-text-fill-color: rgba(255,255,255,0.85) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: var(--radius-md) !important;
        text-align: center !important;
        justify-content: center !important;
        padding: 9px 14px !important;
        font-size: 0.88rem !important;
        font-weight: 400 !important;
        box-shadow: none !important;
        transform: none !important;
        transition: background .12s, color .12s, border-color .12s !important;
        letter-spacing: 0.01em !important;
        width: 100% !important;
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255,255,255,0.14) !important;
        color: #fff !important;
        -webkit-text-fill-color: #fff !important;
        border-color: rgba(255,255,255,0.2) !important;
        transform: none !important;
    }


    /* ── SIDEBAR NAV MODERNO ── */
    .sb-divider {
        height: 1px; background: rgba(255,255,255,.1);
        margin: 4px 0 10px;
    }
    .sb-group-label {
        font-size: 0.58rem; font-weight: 700; letter-spacing: 0.1em;
        text-transform: uppercase; color: rgba(255,255,255,.3);
        padding: 0 2px 4px; margin-top: 6px;
    }
    /* Caixa visual para containers de grupo na sidebar */
    section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(0,0,0,.18) !important;
        border: 1px solid rgba(255,255,255,.08) !important;
        border-radius: 10px !important;
        padding: 4px !important;
        margin-bottom: 4px !important;
    }
    section[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] > div {
        border-radius: 8px !important;
        overflow: hidden !important;
    }

    /* Botões de nav menores e alinhados à esquerda */
    section[data-testid="stSidebar"] .stButton > button {
        background: transparent !important;
        color: rgba(255,255,255,.65) !important;
        -webkit-text-fill-color: rgba(255,255,255,.65) !important;
        border: none !important;
        border-radius: 7px !important;
        font-size: 0.82rem !important;
        font-weight: 400 !important;
        padding: 7px 10px !important;
        height: auto !important;
        min-height: 0 !important;
        box-shadow: none !important;
        transform: none !important;
        text-align: left !important;
        justify-content: flex-start !important;
        margin: 1px 0 !important;
        display: flex !important;
        width: 100% !important;
        visibility: visible !important;
        opacity: 1 !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255,255,255,.08) !important;
        color: #fff !important;
        -webkit-text-fill-color: #fff !important;
        transform: none !important;
    }
    /* Botão ativo */
    .sb-btn-active .stButton > button {
        background: rgba(255,255,255,.12) !important;
        color: #fff !important;
        -webkit-text-fill-color: #fff !important;
        font-weight: 600 !important;
        border-left: 2px solid var(--fgv-bright) !important;
        border-radius: 0 7px 7px 0 !important;
        box-shadow: none !important;
        transform: none !important;
    }
    /* Tema e sair ficam menores */
    .sb-footer-sep {
        height: 1px; background: rgba(255,255,255,.08);
        margin: 10px 0 6px;
    }
    /* Remove espaços extras entre botões */
    section[data-testid="stSidebar"] .stButton {
        margin: 0 !important;
        padding: 0 !important;
    }
    /* Zero gap em todos os filhos da sidebar */
    section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 0 !important;
    }
    /* O div vazio do sb-btn-active não deve ocupar espaço */
    section[data-testid="stSidebar"] .sb-btn-active {
        display: contents !important;
    }
    /* Paragraphs vazios gerados pelo st.markdown não ocupam espaço */
    section[data-testid="stSidebar"] p:empty,
    section[data-testid="stSidebar"] div.stMarkdown:empty,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"]:has(div:empty) {
        display: none !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    /*  NAV ITEM ATIVO  */
    .nav-ativo {
        background: rgba(255,255,255,0.15) !important;
        border: none !important;
        border-radius: var(--radius-md) !important;
        color: #fff !important;
        font-size: 0.88rem !important;
        font-weight: 700 !important;
        padding: 9px 20px !important;
        margin: 1px 0 !important;
        letter-spacing: 0.01em !important;
        text-align: center !important;
        display: block !important;
        width: 100% !important;
        box-sizing: border-box !important;
        line-height: 1.5 !important;
    }


    /* ── SIDEBAR NAV MODERNO ── */
    .sb-divider {
        height: 1px; background: rgba(255,255,255,.1);
        margin: 4px 0 10px;
    }
    .sb-group-label {
        font-size: 0.58rem; font-weight: 700; letter-spacing: 0.1em;
        text-transform: uppercase; color: rgba(255,255,255,.3);
        padding: 0 2px 4px; margin-top: 6px;
    }
    /* Botões de nav menores e alinhados à esquerda */
    section[data-testid="stSidebar"] .stButton > button {
        background: transparent !important;
        color: rgba(255,255,255,.65) !important;
        -webkit-text-fill-color: rgba(255,255,255,.65) !important;
        border: none !important;
        border-radius: 7px !important;
        font-size: 0.82rem !important;
        font-weight: 400 !important;
        padding: 7px 10px !important;
        height: auto !important;
        min-height: 0 !important;
        box-shadow: none !important;
        transform: none !important;
        text-align: left !important;
        justify-content: flex-start !important;
        margin: 1px 0 !important;
        display: flex !important;
        width: 100% !important;
        visibility: visible !important;
        opacity: 1 !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255,255,255,.08) !important;
        color: #fff !important;
        -webkit-text-fill-color: #fff !important;
        transform: none !important;
    }
    /* Botão ativo */
    .sb-btn-active .stButton > button {
        background: rgba(255,255,255,.12) !important;
        color: #fff !important;
        -webkit-text-fill-color: #fff !important;
        font-weight: 600 !important;
        border-left: 2px solid var(--fgv-bright) !important;
        border-radius: 0 7px 7px 0 !important;
        box-shadow: none !important;
        transform: none !important;
    }
    /* Tema e sair ficam menores */
    .sb-footer-sep {
        height: 1px; background: rgba(255,255,255,.08);
        margin: 10px 0 6px;
    }
    /* Remove espaços extras entre botões */
    section[data-testid="stSidebar"] .stButton {
        margin: 0 !important;
        padding: 0 !important;
    }
    /* Zero gap em todos os filhos da sidebar */
    section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 0 !important;
    }
    /* O div vazio do sb-btn-active não deve ocupar espaço */
    section[data-testid="stSidebar"] .sb-btn-active {
        display: contents !important;
    }
    /* Paragraphs vazios gerados pelo st.markdown não ocupam espaço */
    section[data-testid="stSidebar"] p:empty,
    section[data-testid="stSidebar"] div.stMarkdown:empty,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"]:has(div:empty) {
        display: none !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    /*  SIDEBAR NAV RADIO  */
    section[data-testid="stSidebar"] div[role="radiogroup"] { gap: 2px !important; }
    section[data-testid="stSidebar"] label[data-testid="stWidgetLabel"] { display: none !important; }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] > div { gap: 2px !important; }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label {
        display: flex !important; align-items: center !important;
        padding: 8px 12px !important; border-radius: var(--radius-md) !important;
        cursor: pointer !important; transition: background .15s !important;
        font-size: 0.9rem !important; font-weight: 500 !important;
        color: rgba(255,255,255,0.82) !important;
        -webkit-text-fill-color: rgba(255,255,255,0.82) !important;
        margin: 0 !important; width: 100% !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label:hover {
        background: rgba(255,255,255,0.1) !important;
        color: #fff !important; -webkit-text-fill-color: #fff !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked) {
        background: rgba(41,121,212,0.35) !important;
        color: #fff !important; -webkit-text-fill-color: #fff !important;
        font-weight: 600 !important;
        border-left: 3px solid rgba(77,159,255,0.9) !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] input[type="radio"] {
        display: none !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[data-testid="stMarkdownContainer"] {
        display: none !important;
    }


    /*  NAV MENU (dark)  */
    section[data-testid="stSidebar"] .stButton > button {
        background: transparent !important;
        color: rgba(255,255,255,0.75) !important;
        -webkit-text-fill-color: rgba(255,255,255,0.75) !important;
        border: none !important;
        border-radius: var(--radius-md) !important;
        text-align: center !important;
        justify-content: center !important;
        padding: 9px 14px !important;
        font-size: 0.88rem !important;
        font-weight: 400 !important;
        box-shadow: none !important;
        transform: none !important;
        transition: background .12s, color .12s !important;
        letter-spacing: 0.01em !important;
        width: 100% !important;
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255,255,255,0.1) !important;
        color: #fff !important;
        -webkit-text-fill-color: #fff !important;
        transform: none !important;
    }

    /*  NAV ITEM ATIVO  */
    .nav-ativo {
        background: rgba(255,255,255,0.15) !important;
        border: none !important;
        border-radius: var(--radius-md) !important;
        color: #fff !important;
        font-size: 0.88rem !important;
        font-weight: 700 !important;
        padding: 9px 20px !important;
        margin: 1px 0 !important;
        letter-spacing: 0.01em !important;
        text-align: center !important;
        display: block !important;
        width: 100% !important;
        box-sizing: border-box !important;
        line-height: 1.5 !important;
    }

    /*  SIDEBAR NAV RADIO (dark)  */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] > div { gap: 2px !important; }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label {
        display: flex !important; align-items: center !important;
        padding: 8px 12px !important; border-radius: var(--radius-md) !important;
        cursor: pointer !important; transition: background .15s !important;
        font-size: 0.9rem !important; font-weight: 500 !important;
        color: rgba(255,255,255,0.78) !important;
        -webkit-text-fill-color: rgba(255,255,255,0.78) !important;
        margin: 0 !important; width: 100% !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label:hover {
        background: rgba(255,255,255,0.08) !important;
        color: #fff !important; -webkit-text-fill-color: #fff !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked) {
        background: rgba(41,121,212,0.28) !important;
        color: #fff !important; -webkit-text-fill-color: #fff !important;
        font-weight: 600 !important; border-left: 3px solid var(--fgv-bright) !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] input[type="radio"] { display: none !important; }

        /*  HEADER  */
    .header-full-width {
        background: linear-gradient(135deg, var(--fgv-navy) 0%, #112a50 60%, var(--fgv-blue) 100%);
        padding: 0 36px; color: #fff; height: 68px;
        border-bottom: 1px solid rgba(255,255,255,.07);
        box-shadow: 0 1px 0 rgba(41,121,212,.25), 0 4px 24px rgba(0,0,0,.2);
        position: relative; overflow: hidden;
    }
    .header-full-width::before {
        content: "";
        position: absolute; inset: 0;
        background: radial-gradient(ellipse at 72% 50%, rgba(41,121,212,.2) 0%, transparent 62%);
        pointer-events: none;
    }
    .header-inner {
        display: flex; align-items: center;
        justify-content: space-between; height: 100%;
        position: relative; z-index: 1;
    }
    .header-left { display: flex; align-items: center; gap: 20px; }
    .header-text-block { display: flex; flex-direction: column; gap: 1px; }
    .header-logo-block { display: flex; align-items: center; }
    .header-logo-full { height: 34px; width: auto; object-fit: contain; opacity: .9; display: block; }
    .header-divider { width: 1px; height: 26px; background: rgba(255,255,255,.18); flex-shrink: 0; }
    .header-title { font-size: 0.92rem; font-weight: 600; color: #fff; letter-spacing: -0.01em; line-height: 1.3; white-space: nowrap; }
    .header-subtitle { font-size: 0.68rem; color: rgba(255,255,255,.45); letter-spacing: 0.06em; text-transform: uppercase; font-weight: 500; }
    .header-right { display: flex; align-items: center; gap: 12px; }
    .header-profile {
        display: inline-flex; align-items: center; gap: 8px;
        background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.12);
        padding: 6px 14px 6px 8px; border-radius: 999px;
        font-size: 0.78rem; color: rgba(255,255,255,.85);
        transition: background 160ms ease, border-color 160ms ease;
        cursor: default;
    }
    .header-profile:hover { background: rgba(255,255,255,.14); border-color: rgba(255,255,255,.22); }
    .header-avatar {
        width: 22px; height: 22px; border-radius: 50%;
        background: linear-gradient(135deg, var(--fgv-accent), var(--fgv-bright));
        display: inline-flex; align-items: center; justify-content: center;
        font-size: 0.6rem; font-weight: 700; color: #fff; flex-shrink: 0; text-transform: uppercase;
    }
    .header-page-name {
        font-size: 0.68rem; font-weight: 600; color: rgba(255,255,255,.38);
        letter-spacing: 0.07em; text-transform: uppercase;
    }

    /*  SECTION CARDS  */
    .section-card {
        background: var(--surface-1); border: 1px solid var(--border);
        border-radius: var(--radius-lg); padding: 20px;
        margin: 0 16px 14px; box-shadow: var(--shadow-sm);
    }
    .metric-card {
        background: var(--surface-2); border: 1px solid var(--border);
        border-radius: var(--radius-md); padding: 16px; box-shadow: var(--shadow-sm);
    }
    .metric-title { color: var(--ink-secondary) !important; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: .04em; }
    .metric-value { color: var(--fgv-bright) !important; font-weight: 800; font-size: 1.7rem; line-height: 1.1; }
    .metric-sub { color: var(--ink-muted) !important; font-size: 0.8rem; margin-top: 2px; }

    /*  INPUTS  */
    .stTextInput input, .stNumberInput input, .stTextArea textarea,
    input[type="text"], input[type="number"], textarea {
        background: var(--surface-2) !important; color: var(--ink-primary) !important;
        -webkit-text-fill-color: var(--ink-primary) !important;
        border: 1px solid var(--border-strong) !important; border-radius: var(--radius-md) !important;
        font-family: var(--font) !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
        border-color: var(--fgv-accent) !important; box-shadow: 0 0 0 2px rgba(41,121,212,.2) !important;
    }
    .stTextInput input::placeholder, .stTextArea textarea::placeholder { color: var(--ink-muted) !important; opacity: 1 !important; }
    .stSelectbox > div > div, div[data-baseweb="select"] > div {
        background: var(--surface-2) !important; border: 1px solid var(--border-strong) !important;
        border-radius: var(--radius-md) !important;
    }
    div[data-baseweb="select"] * { color: var(--ink-primary) !important; -webkit-text-fill-color: var(--ink-primary) !important; }
    div[data-baseweb="select"] svg { fill: var(--fgv-bright) !important; }
    div[data-baseweb="menu"] {
        background: var(--surface-1) !important; border: 1px solid var(--border-strong) !important;
        border-radius: var(--radius-md) !important; box-shadow: var(--shadow-lg) !important;
    }
    div[data-baseweb="menu"] * { color: var(--ink-primary) !important; -webkit-text-fill-color: var(--ink-primary) !important; }
    div[data-baseweb="menu"] li:hover { background: var(--surface-3) !important; }
    label { color: var(--ink-secondary) !important; font-size: 0.85rem !important; font-weight: 500 !important; }
    .stNumberInput button { background: var(--surface-2) !important; color: var(--ink-primary) !important; border: 1px solid var(--border-strong) !important; }

    /*  BUTTONS  */
    .stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
        background: var(--fgv-accent) !important; color: #fff !important;
        -webkit-text-fill-color: #fff !important; border: none !important;
        border-radius: var(--radius-md) !important; font-weight: 600 !important;
        font-family: var(--font) !important; transition: background .15s, transform .1s !important;
        box-shadow: 0 2px 8px rgba(41,121,212,.3) !important;
    }
    .stButton > button:hover, .stDownloadButton > button:hover { background: var(--fgv-mid) !important; transform: translateY(-1px) !important; }
    .stButton > button:active { transform: translateY(0) !important; }
    .stButton > button:disabled { background: var(--surface-3) !important; color: var(--ink-muted) !important; -webkit-text-fill-color: var(--ink-muted) !important; box-shadow: none !important; transform: none !important; }


    /*  SELECTBOX MODERNO (dark)  */
    div[data-baseweb="select"] {
        border-radius: var(--radius-md) !important;
    }
    div[data-baseweb="select"] > div {
        background: var(--surface-2) !important;
        border: 1.5px solid var(--border-strong) !important;
        border-radius: var(--radius-md) !important;
        min-height: 42px !important;
        transition: border-color .15s, box-shadow .15s !important;
    }
    div[data-baseweb="select"] > div:hover {
        border-color: var(--fgv-accent) !important;
    }
    div[data-baseweb="select"] > div:focus-within {
        border-color: var(--fgv-accent) !important;
        box-shadow: 0 0 0 3px rgba(41,121,212,.2) !important;
    }
    div[data-baseweb="select"] [data-testid="stSelectboxVirtualDropdown"],
    div[data-baseweb="popover"] {
        background: var(--surface-1) !important;
        border: 1px solid var(--border-strong) !important;
        border-radius: var(--radius-md) !important;
        box-shadow: 0 8px 24px rgba(0,0,0,.5) !important;
        padding: 4px !important;
    }
    div[data-baseweb="option"] {
        border-radius: var(--radius-sm) !important;
        margin: 1px 4px !important;
        padding: 8px 12px !important;
        transition: background .1s !important;
    }
    div[data-baseweb="option"]:hover {
        background: var(--surface-3) !important;
    }
    div[data-baseweb="option"][aria-selected="true"] {
        background: rgba(41,121,212,.25) !important;
    }

    /* =========================================================
       MOTION SYSTEM - corporativo-premium, ease-out-quart
       Reduced-motion: crossfade simples, sem transform
    ========================================================= */
    @keyframes fgv-fade-up {
        from { opacity: 0; transform: translateY(14px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes fgv-fade-in {
        from { opacity: 0; }
        to   { opacity: 1; }
    }
    @keyframes fgv-slide-right {
        from { opacity: 0; transform: translateX(-10px); }
        to   { opacity: 1; transform: translateX(0); }
    }
    :root {
        --ease-out-quart: cubic-bezier(0.25, 1, 0.5, 1);
        --ease-out-expo:  cubic-bezier(0.16, 1, 0.3, 1);
        --dur-fast: 160ms;
        --dur-base: 260ms;
        --dur-slow: 400ms;
    }
    section.main .block-container > div {
        animation: fgv-fade-up var(--dur-slow) var(--ease-out-expo) both;
    }
    section.main .block-container > div:nth-child(1) { animation-delay: 0ms; }
    section.main .block-container > div:nth-child(2) { animation-delay: 40ms; }
    section.main .block-container > div:nth-child(3) { animation-delay: 80ms; }
    section.main .block-container > div:nth-child(4) { animation-delay: 120ms; }
    section.main .block-container > div:nth-child(5) { animation-delay: 160ms; }
    section.main .block-container > div:nth-child(6) { animation-delay: 200ms; }
    section.main .block-container > div:nth-child(7) { animation-delay: 240ms; }
    section.main .block-container > div:nth-child(8) { animation-delay: 280ms; }
    section[data-testid="stSidebar"] > div:first-child {
        animation: fgv-slide-right var(--dur-slow) var(--ease-out-expo) both;
    }
    .section-card {
        animation: fgv-fade-up var(--dur-base) var(--ease-out-quart) both;
        transition: box-shadow var(--dur-fast) var(--ease-out-quart), border-color var(--dur-fast) var(--ease-out-quart) !important;
    }
    .section-card:hover {
        box-shadow: 0 4px 20px rgba(11,31,58,.12) !important;
        border-color: var(--border-strong) !important;
    }
    div[data-testid="stMetric"] {
        animation: fgv-fade-up var(--dur-base) var(--ease-out-quart) both;
        transition: box-shadow var(--dur-fast) var(--ease-out-quart), transform var(--dur-fast) var(--ease-out-quart) !important;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(11,31,58,.1) !important;
    }
    .stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
        transition: background var(--dur-fast) var(--ease-out-quart), box-shadow var(--dur-fast) var(--ease-out-quart), transform var(--dur-fast) var(--ease-out-quart), border-color var(--dur-fast) var(--ease-out-quart) !important;
    }
    section[data-testid="stSidebar"] .stButton > button {
        transition: background var(--dur-fast) var(--ease-out-quart), color var(--dur-fast) var(--ease-out-quart) !important;
    }
    div[data-testid="stDataFrame"] {
        animation: fgv-fade-in var(--dur-base) var(--ease-out-quart) both;
    }
    div[data-testid="stExpander"] {
        transition: box-shadow var(--dur-fast) var(--ease-out-quart) !important;
    }
    div[data-testid="stExpander"]:hover {
        box-shadow: 0 2px 12px rgba(11,31,58,.08) !important;
    }
    div[data-baseweb="select"] > div {
        transition: border-color var(--dur-fast) var(--ease-out-quart), box-shadow var(--dur-fast) var(--ease-out-quart) !important;
    }
    .header-full-width {
        animation: fgv-fade-in var(--dur-slow) var(--ease-out-expo) both;
    }
    div[data-testid="stAlert"] {
        animation: fgv-fade-up var(--dur-base) var(--ease-out-quart) both;
    }
    @media (prefers-reduced-motion: reduce) {
        @keyframes fgv-fade-up    { from { opacity: 0; } to { opacity: 1; } }
        @keyframes fgv-fade-in    { from { opacity: 0; } to { opacity: 1; } }
        @keyframes fgv-slide-right { from { opacity: 0; } to { opacity: 1; } }
        :root { --dur-fast: 80ms; --dur-base: 120ms; --dur-slow: 160ms; }
        div[data-testid="stMetric"]:hover { transform: none !important; }
        .stButton > button:hover { transform: none !important; }
    }

    /*  TABLE  */
    div[data-testid="stDataFrame"] { background: var(--surface-1) !important; border: 1px solid var(--border) !important; border-radius: var(--radius-md) !important; }
    div[data-testid="stDataFrame"] div[role="grid"] { background: var(--surface-1) !important; }
    div[data-testid="stDataFrame"] div[role="row"] { background: var(--surface-1) !important; }
    div[data-testid="stDataFrame"] div[role="row"]:nth-child(even) { background: var(--surface-2) !important; }
    div[data-testid="stDataFrame"] div[role="row"]:hover { background: var(--surface-3) !important; }
    div[data-testid="stDataFrame"] div[role="gridcell"] { color: var(--ink-primary) !important; border-bottom: 1px solid var(--border) !important; }
    div[data-testid="stDataFrame"] div[role="columnheader"] { background: var(--surface-3) !important; color: var(--fgv-bright) !important; font-weight: 600 !important; font-size: 0.8rem !important; text-transform: uppercase !important; letter-spacing: .04em !important; border-bottom: 1px solid var(--border-strong) !important; }

    /*  LOGIN  */
    .login-card { background: var(--surface-1) !important; border: 1px solid var(--border-strong) !important; border-radius: var(--radius-lg) !important; box-shadow: var(--shadow-lg) !important; padding: 10px !important; }
    .login-title { color: var(--fgv-bright) !important; font-size: 1.6rem !important; font-weight: 700 !important; letter-spacing: -0.02em !important; }
    .login-subtitle, .small-muted { color: var(--ink-secondary) !important; }

    /*  ALERTS  */
    div[data-testid="stAlert"] { border-radius: var(--radius-md) !important; border-left-width: 3px !important; }

    /*  EXPANDER  */
    div[data-testid="stExpander"] { background: var(--surface-2) !important; border: 1px solid var(--border) !important; border-radius: var(--radius-md) !important; }

    /*  METRICS  */
    div[data-testid="stMetric"] { background: var(--surface-2) !important; border: 1px solid var(--border) !important; border-radius: var(--radius-md) !important; padding: 12px 16px !important; }
    div[data-testid="stMetric"] label { color: var(--ink-secondary) !important; }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: var(--fgv-bright) !important; }

    </style>
    """, unsafe_allow_html=True)


def aplicar_estilo_light():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /*  TOKENS  */
    :root {
        --fgv-navy:      #0b1f3a;
        --fgv-blue:      #1a3f6f;
        --fgv-mid:       #1e5799;
        --fgv-accent:    #1d6fc4;
        --fgv-bright:    #1a5fa8;
        --ink-primary:   #0d1b2e;
        --ink-secondary: #3d5575;
        --ink-muted:     #7a97b8;
        --surface-0:     #f0f4f9;
        --surface-1:     #ffffff;
        --surface-2:     #e8eef6;
        --surface-3:     #d8e5f2;
        --border:        rgba(26, 63, 111, 0.12);
        --border-strong: rgba(26, 63, 111, 0.22);
        --radius-sm: 6px;
        --radius-md: 10px;
        --radius-lg: 16px;
        --shadow-sm: 0 1px 4px rgba(11,31,58,.06);
        --shadow-md: 0 4px 16px rgba(11,31,58,.09);
        --shadow-lg: 0 8px 32px rgba(11,31,58,.12);
        --font: 'Inter', system-ui, sans-serif;
    }

    /*  BASE  */
    .stApp { background: var(--surface-0) !important; color: var(--ink-primary) !important; font-family: var(--font) !important; }
    .block-container { padding: 0 !important; max-width: 100% !important; color: var(--ink-primary) !important; }
    header[data-testid="stHeader"] { background: transparent !important; height: 0 !important; }
    section.main > div { padding-top: 0 !important; }
    div[data-testid="stVerticalBlock"] > div:first-child { margin-top: 0 !important; padding-top: 0 !important; }
    * { font-family: var(--font) !important; }
    p, li { color: var(--ink-primary) !important; }

    /* Esconde apenas o texto "keyboard_double_arrow" dentro do botão de colapso */
    [class*="keyboard_double_arrow"] { display: none !important; }

    /*  SIDEBAR  */
    section[data-testid="stSidebar"] {
        background: linear-gradient(170deg, var(--fgv-navy) 0%, var(--fgv-blue) 100%) !important;
        border-right: 1px solid var(--border-strong) !important;
    }
    section[data-testid="stSidebar"] * { color: #fff !important; }
    section[data-testid="stSidebar"] .block-container { padding: 0 0.75rem !important; }
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:first-child { margin-top: -14px !important; }
    .theme-toggle-mini { margin: -6px 4px 2px !important; }

    /* Theme toggle buttons */
    .theme-toggle-mini .stButton > button {
        font-size: 0.7rem !important;
        padding: 2px 6px !important;
        height: 26px !important;
        letter-spacing: 0.08em !important;
        font-weight: 600 !important;
        color: rgba(255,255,255,0.7) !important;
        -webkit-text-fill-color: rgba(255,255,255,0.7) !important;
        background: transparent !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        border-radius: 4px !important;
        box-shadow: none !important;
        transform: none !important;
        min-height: 26px !important;
    }
    .theme-toggle-mini .stButton > button:hover {
        background: rgba(255,255,255,0.12) !important;
        color: #fff !important;
        -webkit-text-fill-color: #fff !important;
        transform: none !important;
    }
    .sidebar-logo-wrap { display: flex; justify-content: center; padding: 2px 0 10px; }
    .sidebar-logo-img {
        width: 220px; max-width: 100%; object-fit: contain;
        filter: brightness(0) invert(1) !important;
        opacity: 0.92 !important;
        display: block !important;
        visibility: visible !important;
    }
        /*  HEADER  */
    .header-full-width {
        background: linear-gradient(135deg, var(--fgv-navy) 0%, #112a50 60%, var(--fgv-blue) 100%);
        padding: 0 36px; color: #fff; height: 68px;
        border-bottom: 1px solid rgba(255,255,255,.07);
        box-shadow: 0 1px 0 rgba(41,121,212,.25), 0 4px 24px rgba(0,0,0,.2);
        position: relative; overflow: hidden;
    }
    .header-full-width::before {
        content: "";
        position: absolute; inset: 0;
        background: radial-gradient(ellipse at 72% 50%, rgba(41,121,212,.2) 0%, transparent 62%);
        pointer-events: none;
    }
    .header-inner {
        display: flex; align-items: center;
        justify-content: space-between; height: 100%;
        position: relative; z-index: 1;
    }
    .header-left { display: flex; align-items: center; gap: 20px; }
    .header-text-block { display: flex; flex-direction: column; gap: 1px; }
    .header-logo-block { display: flex; align-items: center; }
    .header-logo-full { height: 34px; width: auto; object-fit: contain; opacity: .9; display: block; }
    .header-divider { width: 1px; height: 26px; background: rgba(255,255,255,.18); flex-shrink: 0; }
    .header-title { font-size: 0.92rem; font-weight: 600; color: #fff; letter-spacing: -0.01em; line-height: 1.3; white-space: nowrap; }
    .header-subtitle { font-size: 0.68rem; color: rgba(255,255,255,.45); letter-spacing: 0.06em; text-transform: uppercase; font-weight: 500; }
    .header-right { display: flex; align-items: center; gap: 12px; }
    .header-profile {
        display: inline-flex; align-items: center; gap: 8px;
        background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.12);
        padding: 6px 14px 6px 8px; border-radius: 999px;
        font-size: 0.78rem; color: rgba(255,255,255,.85);
        transition: background 160ms ease, border-color 160ms ease;
        cursor: default;
    }
    .header-profile:hover { background: rgba(255,255,255,.14); border-color: rgba(255,255,255,.22); }
    .header-avatar {
        width: 22px; height: 22px; border-radius: 50%;
        background: linear-gradient(135deg, var(--fgv-accent), var(--fgv-bright));
        display: inline-flex; align-items: center; justify-content: center;
        font-size: 0.6rem; font-weight: 700; color: #fff; flex-shrink: 0; text-transform: uppercase;
    }
    .header-page-name {
        font-size: 0.68rem; font-weight: 600; color: rgba(255,255,255,.38);
        letter-spacing: 0.07em; text-transform: uppercase;
    }

    /*  SECTION CARDS  */
    .section-card {
        background: var(--surface-1); border: 1px solid var(--border);
        border-radius: var(--radius-lg); padding: 20px;
        margin: 0 16px 14px; box-shadow: var(--shadow-sm);
    }
    .metric-card {
        background: var(--surface-1); border: 1px solid var(--border);
        border-radius: var(--radius-md); padding: 16px; box-shadow: var(--shadow-sm);
    }
    .metric-title { color: var(--ink-secondary) !important; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: .04em; }
    .metric-value { color: var(--fgv-blue) !important; font-weight: 800; font-size: 1.7rem; line-height: 1.1; }
    .metric-sub { color: var(--ink-muted) !important; font-size: 0.8rem; margin-top: 2px; }

    /*  INPUTS  */
    .stTextInput input, .stNumberInput input, .stTextArea textarea,
    input[type="text"], input[type="number"], textarea {
        background: #f5f8fd !important; color: var(--ink-primary) !important;
        -webkit-text-fill-color: var(--ink-primary) !important;
        border: 1px solid var(--border-strong) !important; border-radius: var(--radius-md) !important;
        font-family: var(--font) !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
        border-color: var(--fgv-accent) !important; box-shadow: 0 0 0 2px rgba(29,111,196,.15) !important;
    }
    .stTextInput input::placeholder, .stTextArea textarea::placeholder { color: var(--ink-muted) !important; opacity: 1 !important; }
    .stSelectbox > div > div, div[data-baseweb="select"] > div {
        background: #f5f8fd !important; border: 1px solid var(--border-strong) !important;
        border-radius: var(--radius-md) !important;
    }
    div[data-baseweb="select"] * { color: var(--ink-primary) !important; -webkit-text-fill-color: var(--ink-primary) !important; }
    div[data-baseweb="select"] svg { fill: var(--fgv-blue) !important; }
    div[data-baseweb="menu"],
    div[data-baseweb="popover"] div[data-baseweb="menu"],
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] > div,
    div[data-baseweb="popover"] > div > div,
    ul[data-baseweb="menu"] {
        background: #ffffff !important;
        background-color: #ffffff !important;
        border: 1px solid var(--border-strong) !important;
        border-radius: var(--radius-md) !important;
        box-shadow: 0 8px 24px rgba(11,31,58,.12) !important;
    }
    div[data-baseweb="menu"] *,
    div[data-baseweb="popover"] *,
    ul[data-baseweb="menu"] li {
        color: var(--ink-primary) !important;
        -webkit-text-fill-color: var(--ink-primary) !important;
        background-color: transparent !important;
    }
    div[data-baseweb="menu"] li:hover,
    div[data-baseweb="popover"] li:hover,
    div[data-baseweb="option"]:hover {
        background: var(--surface-2) !important;
        background-color: var(--surface-2) !important;
    }
    div[data-baseweb="option"][aria-selected="true"] {
        background: var(--surface-3) !important;
        background-color: var(--surface-3) !important;
    }
    label { color: var(--ink-secondary) !important; font-size: 0.85rem !important; font-weight: 500 !important; }
    .stMarkdown p, .stMarkdown li, .stMarkdown span { color: var(--ink-primary) !important; }
    .stNumberInput button { background: #f5f8fd !important; color: var(--ink-primary) !important; border: 1px solid var(--border-strong) !important; }

    /*  BUTTONS  */
    .stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
        background: var(--fgv-accent) !important; color: #fff !important;
        -webkit-text-fill-color: #fff !important; border: none !important;
        border-radius: var(--radius-md) !important; font-weight: 600 !important;
        font-family: var(--font) !important; transition: background .15s, transform .1s !important;
        box-shadow: 0 2px 8px rgba(29,111,196,.25) !important;
    }
    .stButton > button:hover, .stDownloadButton > button:hover { background: var(--fgv-blue) !important; transform: translateY(-1px) !important; }
    .stButton > button:active { transform: translateY(0) !important; }
    .stButton > button:disabled { background: var(--surface-2) !important; color: var(--ink-muted) !important; -webkit-text-fill-color: var(--ink-muted) !important; box-shadow: none !important; transform: none !important; }


    /*  SELECTBOX MODERNO (light)  */
    div[data-baseweb="select"] {
        border-radius: var(--radius-md) !important;
    }
    div[data-baseweb="select"] > div {
        background: #f5f8fd !important;
        border: 1.5px solid var(--border-strong) !important;
        border-radius: var(--radius-md) !important;
        min-height: 42px !important;
        transition: border-color .15s, box-shadow .15s !important;
    }
    div[data-baseweb="select"] > div:hover {
        border-color: var(--fgv-accent) !important;
    }
    div[data-baseweb="select"] > div:focus-within {
        border-color: var(--fgv-accent) !important;
        box-shadow: 0 0 0 3px rgba(29,111,196,.15) !important;
    }
    div[data-baseweb="popover"],
    div[data-baseweb="select"] [data-testid="stSelectboxVirtualDropdown"] {
        background: #fff !important;
        border: 1px solid var(--border-strong) !important;
        border-radius: var(--radius-md) !important;
        box-shadow: 0 8px 24px rgba(11,31,58,.12) !important;
        padding: 4px !important;
    }
    div[data-baseweb="option"] {
        border-radius: var(--radius-sm) !important;
        margin: 1px 4px !important;
        padding: 8px 12px !important;
        transition: background .1s !important;
        color: var(--ink-primary) !important;
    }
    div[data-baseweb="option"]:hover {
        background: var(--surface-2) !important;
    }
    div[data-baseweb="option"][aria-selected="true"] {
        background: var(--surface-3) !important;
        color: var(--fgv-blue) !important;
        font-weight: 600 !important;
    }

    /* =========================================================
       MOTION SYSTEM - corporativo-premium, ease-out-quart
       Reduced-motion: crossfade simples, sem transform
    ========================================================= */
    @keyframes fgv-fade-up {
        from { opacity: 0; transform: translateY(14px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes fgv-fade-in {
        from { opacity: 0; }
        to   { opacity: 1; }
    }
    @keyframes fgv-slide-right {
        from { opacity: 0; transform: translateX(-10px); }
        to   { opacity: 1; transform: translateX(0); }
    }
    :root {
        --ease-out-quart: cubic-bezier(0.25, 1, 0.5, 1);
        --ease-out-expo:  cubic-bezier(0.16, 1, 0.3, 1);
        --dur-fast: 160ms;
        --dur-base: 260ms;
        --dur-slow: 400ms;
    }
    section.main .block-container > div {
        animation: fgv-fade-up var(--dur-slow) var(--ease-out-expo) both;
    }
    section.main .block-container > div:nth-child(1) { animation-delay: 0ms; }
    section.main .block-container > div:nth-child(2) { animation-delay: 40ms; }
    section.main .block-container > div:nth-child(3) { animation-delay: 80ms; }
    section.main .block-container > div:nth-child(4) { animation-delay: 120ms; }
    section.main .block-container > div:nth-child(5) { animation-delay: 160ms; }
    section.main .block-container > div:nth-child(6) { animation-delay: 200ms; }
    section.main .block-container > div:nth-child(7) { animation-delay: 240ms; }
    section.main .block-container > div:nth-child(8) { animation-delay: 280ms; }
    section[data-testid="stSidebar"] > div:first-child {
        animation: fgv-slide-right var(--dur-slow) var(--ease-out-expo) both;
    }
    .section-card {
        animation: fgv-fade-up var(--dur-base) var(--ease-out-quart) both;
        transition: box-shadow var(--dur-fast) var(--ease-out-quart), border-color var(--dur-fast) var(--ease-out-quart) !important;
    }
    .section-card:hover {
        box-shadow: 0 4px 20px rgba(11,31,58,.12) !important;
        border-color: var(--border-strong) !important;
    }
    div[data-testid="stMetric"] {
        animation: fgv-fade-up var(--dur-base) var(--ease-out-quart) both;
        transition: box-shadow var(--dur-fast) var(--ease-out-quart), transform var(--dur-fast) var(--ease-out-quart) !important;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(11,31,58,.1) !important;
    }
    .stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
        transition: background var(--dur-fast) var(--ease-out-quart), box-shadow var(--dur-fast) var(--ease-out-quart), transform var(--dur-fast) var(--ease-out-quart), border-color var(--dur-fast) var(--ease-out-quart) !important;
    }
    section[data-testid="stSidebar"] .stButton > button {
        transition: background var(--dur-fast) var(--ease-out-quart), color var(--dur-fast) var(--ease-out-quart) !important;
    }
    div[data-testid="stDataFrame"] {
        animation: fgv-fade-in var(--dur-base) var(--ease-out-quart) both;
    }
    div[data-testid="stExpander"] {
        transition: box-shadow var(--dur-fast) var(--ease-out-quart) !important;
    }
    div[data-testid="stExpander"]:hover {
        box-shadow: 0 2px 12px rgba(11,31,58,.08) !important;
    }
    div[data-baseweb="select"] > div {
        transition: border-color var(--dur-fast) var(--ease-out-quart), box-shadow var(--dur-fast) var(--ease-out-quart) !important;
    }
    .header-full-width {
        animation: fgv-fade-in var(--dur-slow) var(--ease-out-expo) both;
    }
    div[data-testid="stAlert"] {
        animation: fgv-fade-up var(--dur-base) var(--ease-out-quart) both;
    }
    @media (prefers-reduced-motion: reduce) {
        @keyframes fgv-fade-up    { from { opacity: 0; } to { opacity: 1; } }
        @keyframes fgv-fade-in    { from { opacity: 0; } to { opacity: 1; } }
        @keyframes fgv-slide-right { from { opacity: 0; } to { opacity: 1; } }
        :root { --dur-fast: 80ms; --dur-base: 120ms; --dur-slow: 160ms; }
        div[data-testid="stMetric"]:hover { transform: none !important; }
        .stButton > button:hover { transform: none !important; }
    }

    /*  TABLE  */
    div[data-testid="stDataFrame"] { background: #fff !important; border: 1px solid var(--border) !important; border-radius: var(--radius-md) !important; }
    div[data-testid="stDataFrame"] div[role="grid"] { background: #fff !important; }
    div[data-testid="stDataFrame"] div[role="row"] { background: #fff !important; }
    div[data-testid="stDataFrame"] div[role="row"]:nth-child(even) { background: var(--surface-2) !important; }
    div[data-testid="stDataFrame"] div[role="row"]:hover { background: var(--surface-3) !important; }
    div[data-testid="stDataFrame"] div[role="gridcell"] { color: var(--ink-primary) !important; -webkit-text-fill-color: var(--ink-primary) !important; border-bottom: 1px solid var(--border) !important; background: transparent !important; }
    div[data-testid="stDataFrame"] div[role="gridcell"] * { color: var(--ink-primary) !important; -webkit-text-fill-color: var(--ink-primary) !important; }
    div[data-testid="stDataFrame"] div[role="columnheader"] { background: var(--surface-2) !important; color: var(--fgv-blue) !important; -webkit-text-fill-color: var(--fgv-blue) !important; font-weight: 700 !important; font-size: 0.8rem !important; text-transform: uppercase !important; letter-spacing: .04em !important; border-bottom: 2px solid var(--border-strong) !important; }
    div[data-testid="stDataFrame"] div[role="columnheader"] * { color: var(--fgv-blue) !important; -webkit-text-fill-color: var(--fgv-blue) !important; }

    /*  LOGIN  */
    .login-card { background: #fff !important; border: 1px solid var(--border) !important; border-radius: var(--radius-lg) !important; box-shadow: var(--shadow-lg) !important; padding: 10px !important; }
    .login-title { color: var(--fgv-blue) !important; font-size: 1.6rem !important; font-weight: 700 !important; letter-spacing: -0.02em !important; }
    .login-subtitle, .small-muted, .login-footer { color: var(--ink-secondary) !important; }
    .login-card .stTextInput input { background: #f5f8fd !important; border: 1px solid var(--border-strong) !important; }

    /*  ALERTS  */
    div[data-testid="stAlert"] { border-radius: var(--radius-md) !important; border-left-width: 3px !important; }

    /*  EXPANDER  */
    div[data-testid="stExpander"] { background: var(--surface-1) !important; border: 1px solid var(--border) !important; border-radius: var(--radius-md) !important; }

    /*  METRICS  */
    div[data-testid="stMetric"] { background: var(--surface-1) !important; border: 1px solid var(--border) !important; border-radius: var(--radius-md) !important; padding: 12px 16px !important; }
    div[data-testid="stMetric"] label { color: var(--ink-secondary) !important; }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: var(--fgv-blue) !important; }

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
    return psycopg2.connect(DATABASE_URL)


def hash_senha(senha: str) -> str:
    """Retorna o hash bcrypt da senha."""
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_senha(senha: str, hash_armazenado: str) -> bool:
    """Verifica senha contra hash bcrypt ou SHA-256 legado."""
    try:
        return bcrypt.checkpw(senha.encode("utf-8"), hash_armazenado.encode("utf-8"))
    except Exception:
        calculado = hashlib.sha256(senha.encode("utf-8")).hexdigest()
        return hmac.compare_digest(calculado, hash_armazenado or "")


#  Rate limiting em memória
_DUMMY_BCRYPT_HASH = "$2b$12$KIXdR5v2FJjBi3vkHxBnL.aBGz8zVkxRZl1GQoqsJZJw5c5gVkIUC"
_login_lock = threading.Lock()
_login_attempts: dict = {}
_MAX_TENTATIVAS = 5
_JANELA_SEGUNDOS = 300


def _checar_e_registrar_tentativa(username: str, sucesso: bool):
    import time
    agora = time.time()
    key = username.strip().upper()
    with _login_lock:
        tentativas = _login_attempts.get(key, [])
        tentativas = [t for t in tentativas if agora - t < _JANELA_SEGUNDOS]
        if sucesso:
            _login_attempts[key] = []
            return False, 0
        tentativas.append(agora)
        _login_attempts[key] = tentativas
        if len(tentativas) >= _MAX_TENTATIVAS:
            restante = int(_JANELA_SEGUNDOS - (agora - tentativas[0]))
            return True, max(0, restante)
        return False, 0


def _dummy_bcrypt(senha: str) -> None:
    try:
        bcrypt.checkpw(senha.encode("utf-8"), _DUMMY_BCRYPT_HASH.encode("utf-8"))
    except Exception:
        pass


def agora_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def init_db():
    """Garante que o usuário ADMIN existe. Tabelas já criadas via schema_supabase.sql."""
    if not DATABASE_URL:
        st.error("Variável DATABASE_URL não configurada. Defina-a nas configurações do Streamlit Cloud.")
        st.stop()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM usuarios WHERE username = 'ADMIN'")
    exists = cur.fetchone()[0]
    if exists == 0:
        senha_inicial = os.environ.get("ADMIN_INITIAL_PASSWORD", "")
        if not senha_inicial:
            conn.close()
            st.error("Defina ADMIN_INITIAL_PASSWORD nas variáveis de ambiente do Streamlit Cloud.")
            st.stop()
        cur.execute("""
            INSERT INTO usuarios (username, email, senha_hash, perfil, ativo, criado_em, atualizado_em)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, ("ADMIN", "", hash_senha(senha_inicial), "ADMIN", 1, agora_str(), agora_str()))
    conn.commit()
    conn.close()


@st.cache_data(ttl=300, show_spinner=False)
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
    # Rate limiting antes de qualquer consulta ao banco
    bloqueado, restante = _checar_e_registrar_tentativa(username, sucesso=False)
    if bloqueado:
        raise PermissionError(f"Muitas tentativas incorretas. Aguarde {restante} segundos.")

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT username, perfil, ativo, email, senha_hash
        FROM usuarios
        WHERE UPPER(username) = UPPER(%s)
    """, (username,))
    row = cur.fetchone()

    if not row:
        # Usuário não existe - dummy bcrypt para nivelar tempo (evita username enumeration)
        _dummy_bcrypt(senha)
        conn.close()
        return None

    if row[2] == 1 and verificar_senha(senha, row[4]):
        _checar_e_registrar_tentativa(username, sucesso=True)
        # Upgrade automático SHA-256 → bcrypt
        if not row[4].startswith("$2b$") and not row[4].startswith("$2a$"):
            novo_hash = hash_senha(senha)
            cur.execute("UPDATE usuarios SET senha_hash = %s WHERE UPPER(username) = UPPER(%s)",
                       (novo_hash, row[0]))
            conn.commit()
        conn.close()
        return {"username": row[0], "perfil": row[1], "email": row[3] if len(row) > 3 else ""}

    conn.close()
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


def validar_senha(senha: str) -> tuple[bool, str]:
    if len(senha) < 8:
        return False, "A senha deve ter pelo menos 8 caracteres."
    if not any(c.isupper() for c in senha):
        return False, "A senha deve conter pelo menos uma letra maiúscula."
    if not any(c.islower() for c in senha):
        return False, "A senha deve conter pelo menos uma letra minúscula."
    if not any(c.isdigit() for c in senha):
        return False, "A senha deve conter pelo menos um número."
    return True, ""


def criar_usuario(username: str, email: str, senha: str, perfil: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO usuarios (username, email, senha_hash, perfil, ativo, criado_em, atualizado_em)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (username.strip(), email.strip(), hash_senha(senha), perfil, 1, agora_str(), agora_str()))
    conn.commit()
    conn.close()


def alterar_status_usuario(user_id: int, ativo: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE usuarios SET ativo = %s, atualizado_em = %s WHERE id = %s", (ativo, agora_str(), user_id))
    conn.commit()
    conn.close()


def excluir_usuario(user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM usuarios WHERE id = %s", (user_id,))
    conn.commit()
    conn.close()


def alterar_senha_usuario(username: str, senha_atual: str, nova_senha: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT senha_hash FROM usuarios WHERE UPPER(username) = UPPER(%s)", (username,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False, "Usuário não encontrado."
    if row[0] != hash_senha(senha_atual):
        conn.close()
        return False, "Senha atual incorreta."
    cur.execute(
        "UPDATE usuarios SET senha_hash = %s, atualizado_em = %s WHERE UPPER(username) = UPPER(%s)",
        (hash_senha(nova_senha), agora_str(), username)
    )
    conn.commit()
    conn.close()
    return True, "Senha alterada com sucesso."


def inserir_solicitacao(tema: str, descricao: str, solicitante: str, perfil: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO solicitacoes_tema
            (tema_solicitado, descricao, solicitante, perfil_solicitante, status, data_solicitacao)
        VALUES (%s, %s, %s, %s, 'PENDENTE', %s)
        RETURNING id
    """, (tema.strip(), descricao.strip(), solicitante, perfil, agora_str()))
    solicitacao_id = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return solicitacao_id


@st.cache_data(ttl=60, show_spinner=False)
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
    cur.execute("UPDATE solicitacoes_tema SET status = %s WHERE id = %s", (novo_status, solicitacao_id))
    conn.commit()
    conn.close()


def obter_solicitacao_por_id(solicitacao_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, tema_solicitado, descricao, solicitante, perfil_solicitante, status, data_solicitacao
        FROM solicitacoes_tema
        WHERE id = %s
    """, (solicitacao_id,))
    row = cur.fetchone()
    conn.close()
    return row


def buscar_emails_admins():
    conn = get_conn()
    df = pd.read_sql_query("""
        SELECT email FROM usuarios
        WHERE perfil = 'ADMIN' AND ativo = 1
          AND email IS NOT NULL AND TRIM(email) <> ''
    """, conn)
    conn.close()
    return df["email"].tolist()


def buscar_email_usuario(username: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT email FROM usuarios WHERE UPPER(username) = UPPER(%s)", (username,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row and row[0] else ""


def normalizar_servicos(value) -> list:
    if not value or str(value).strip() in ("", "nan", "None", "-"):
        return []
    text = str(value).strip().rstrip(".")
    separators = [",", ";", "|", " / "]
    parts = [text]
    for sep in separators:
        new_parts = []
        for item in parts:
            new_parts.extend(item.split(sep))
        parts = new_parts
    parts = [p.strip(" .;") for p in parts if str(p).strip(" .;")]
    seen = set()
    result = []
    for part in parts:
        key = part.casefold()
        if key not in seen:
            seen.add(key)
            result.append(part)
    return result


def processar_upload_planilha(arquivo):
    import pandas as pd

    COLUMN_MAP = {
        # Colunas originais da base interna
        "Tema": "tema", "Subtema": "subtema", "Serviços": "servicos",
        "País": "pais", "Estado": "estado", "Município": "municipio",
        "Nome Edital": "nome_edital", "Descrição": "descricao", "Esforço": "esforco",
        "Unidade": "unidade", "Prazo (meses)": "prazo_meses",
        "Tipo de Edital": "tipo_edital", "Código Planilha": "codigo_planilha",
        "Fonte de Dados": "fonte_dado", "OBS": "observacao",
        "Custo de Execução": "custo_execucao", "Data edital (mês/ano)": "data_edital",
        "Min": "valor_min", "Máx": "valor_max",
        "Metodo de Calculo": "metodo_calculo",
        "Método de Cálculo": "metodo_calculo",
        # Colunas da Planilha Modelo das áreas
        "Objetivo do Projeto": "descricao",
        "Nome Edital/Projeto": "nome_edital",
        "1º Parâmetro para verificação do prazo": "esforco",
        "Unidade de medida do 1º Parâmetro ": "unidade",
        "Unidade de medida do 1º Parâmetro": "unidade",
        "2º Parâmetro para verificação do prazo": "esforco2",
        "Unidade de medida do 2º Parâmetro ": "unidade2",
        "Unidade de medida do 2º Parâmetro": "unidade2",
        "Prazo de execução\n(meses)": "prazo_meses",
        "Prazo de execução (meses)": "prazo_meses",
        "Data edital/projeto (mês/ano)": "data_edital",
        "Data de Início do Projeto (Caso concluído)": "data_inicio",
        "Data de Término do Projeto (Caso concluído)": "data_conclusao",
    }

    # Aceita aba "Base" ou usa a primeira aba disponível
    xl = pd.ExcelFile(arquivo)
    sheet = "Base" if "Base" in xl.sheet_names else xl.sheet_names[0]
    df = pd.read_excel(arquivo, sheet_name=sheet)
    df = df.rename(columns=COLUMN_MAP)
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.strip().replace({"nan": None, "None": None, "": None})
    for col in ["prazo_meses", "custo_execucao", "valor_min", "valor_max"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "data_edital" in df.columns:
        dt = pd.to_datetime(df["data_edital"], errors="coerce", dayfirst=True)
        mask = dt.notna()
        df.loc[mask, "data_edital"] = dt.loc[mask].dt.strftime("%Y-%m")

    conn = get_conn()
    conn.autocommit = False
    cur = conn.cursor()

    # Limpa apenas os editais (preserva usuários e solicitações)
    cur.execute("DELETE FROM edital_servico")
    cur.execute("DELETE FROM edital")
    cur.execute("DELETE FROM servico")
    cur.execute("DELETE FROM fonte_dado")
    cur.execute("DELETE FROM unidade")
    cur.execute("DELETE FROM tipo_edital")
    cur.execute("DELETE FROM municipio")
    cur.execute("DELETE FROM estado")
    cur.execute("DELETE FROM pais")
    cur.execute("DELETE FROM subtema")
    cur.execute("DELETE FROM tema")

    def limpar(val):
        """Converte qualquer valor para string limpa ou None."""
        if val is None:
            return None
        import math
        try:
            if isinstance(val, float) and math.isnan(val):
                return None
        except Exception:
            pass
        s = str(val).strip()
        return None if s in ("", "-", "nan", "None", "NaN", "<NA>") else s

    def upsert(table, nome):
        _TABELAS_PERMITIDAS = {
            "tema", "subtema", "pais", "estado", "municipio",
            "tipo_edital", "unidade", "fonte_dado", "servico"
        }
        if table not in _TABELAS_PERMITIDAS:
            raise ValueError(f"Tabela não permitida: {table}")
        nome = limpar(nome)
        if not nome:
            return None
        cur.execute(f"SELECT id FROM {table} WHERE nome = %s", (nome,))
        row = cur.fetchone()
        if row:
            return row[0]
        cur.execute(f"INSERT INTO {table} (nome) VALUES (%s) RETURNING id", (nome,))
        return cur.fetchone()[0]

    tema_map, subtema_map, pais_map, estado_map = {}, {}, {}, {}
    municipio_map, tipo_map, unidade_map, fonte_map, servico_map = {}, {}, {}, {}, {}

    for _, row in df.iterrows():
        tema_id = None
        v = limpar(row.get("tema"))
        if v:
            tema_id = tema_map.get(v) or upsert("tema", v)
            tema_map[v] = tema_id

        subtema_id = None
        v = limpar(row.get("subtema"))
        if v:
            key = (tema_id, v)
            if key not in subtema_map:
                cur.execute("SELECT id FROM subtema WHERE tema_id IS NOT DISTINCT FROM %s AND nome = %s", (tema_id, v))
                found = cur.fetchone()
                if found:
                    subtema_map[key] = found[0]
                else:
                    cur.execute("INSERT INTO subtema (tema_id, nome) VALUES (%s, %s) RETURNING id", (tema_id, v))
                    subtema_map[key] = cur.fetchone()[0]
            subtema_id = subtema_map[key]

        pais_id = None
        v = limpar(row.get("pais"))
        if v:
            pais_id = pais_map.get(v) or upsert("pais", v)
            pais_map[v] = pais_id

        estado_id = None
        v = limpar(row.get("estado"))
        if v:
            if v not in estado_map:
                cur.execute("SELECT id FROM estado WHERE nome = %s", (v,))
                found = cur.fetchone()
                if found:
                    estado_map[v] = found[0]
                else:
                    cur.execute("INSERT INTO estado (pais_id, nome) VALUES (%s, %s) RETURNING id", (pais_id, v))
                    estado_map[v] = cur.fetchone()[0]
            estado_id = estado_map[v]

        municipio_id = None
        v = limpar(row.get("municipio"))
        if v:
            key = (estado_id, v)
            if key not in municipio_map:
                cur.execute("SELECT id FROM municipio WHERE estado_id IS NOT DISTINCT FROM %s AND nome = %s", (estado_id, v))
                found = cur.fetchone()
                if found:
                    municipio_map[key] = found[0]
                else:
                    cur.execute("INSERT INTO municipio (estado_id, nome) VALUES (%s, %s) RETURNING id", (estado_id, v))
                    municipio_map[key] = cur.fetchone()[0]
            municipio_id = municipio_map[key]

        tipo_id = None
        v = limpar(row.get("tipo_edital"))
        if v:
            tipo_id = tipo_map.get(v) or upsert("tipo_edital", v)
            tipo_map[v] = tipo_id

        unidade_id = None
        v = limpar(row.get("unidade"))
        if v:
            unidade_id = unidade_map.get(v) or upsert("unidade", v)
            unidade_map[v] = unidade_id

        fonte_id = None
        v = limpar(row.get("fonte_dado"))
        if v:
            fonte_id = fonte_map.get(v) or upsert("fonte_dado", v)
            fonte_map[v] = fonte_id

        def safe_float(v):
            if v is None:
                return None
            try:
                if pd.isna(v):
                    return None
            except Exception:
                pass
            s = str(v).strip()
            if s in ("", "-", "nan", "None", "NaN"):
                return None
            # Trata formato brasileiro: 1.234.567,89 → 1234567.89
            if "," in s and "." in s:
                s = s.replace(".", "").replace(",", ".")
            elif "," in s:
                s = s.replace(",", ".")
            # Remove espaços internos (ex: "5 77.413,08")
            s = s.replace(" ", "")
            try:
                return float(s)
            except Exception:
                return None

        # 2º parâmetro
        unidade2_id = None
        v_u2 = limpar(row.get("unidade2"))
        if v_u2:
            unidade2_id = unidade_map.get(v_u2) or upsert("unidade", v_u2)
            unidade_map[v_u2] = unidade2_id

        cur.execute("""
            INSERT INTO edital (
                tema_id, subtema_id, pais_id, estado_id, municipio_id, nome_edital,
                descricao, esforco, unidade_id, esforco2, unidade2_id, prazo_meses,
                tipo_edital_id, codigo_planilha, fonte_dado_id, observacao,
                custo_execucao, data_edital, metodo_calculo, valor_min, valor_max
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
        """, (
            tema_id, subtema_id, pais_id, estado_id, municipio_id,
            limpar(row.get("nome_edital")), limpar(row.get("descricao")),
            limpar(row.get("esforco")), unidade_id,
            limpar(row.get("esforco2")), unidade2_id,
            safe_float(row.get("prazo_meses")), tipo_id,
            limpar(row.get("codigo_planilha")), fonte_id,
            limpar(row.get("observacao")), safe_float(row.get("custo_execucao")),
            limpar(row.get("data_edital")), limpar(row.get("metodo_calculo")),
            safe_float(row.get("valor_min")), safe_float(row.get("valor_max")),
        ))
        edital_id = cur.fetchone()[0]

        for serv in normalizar_servicos(row.get("servicos")):
            servico_id = servico_map.get(serv) or upsert("servico", serv)
            servico_map[serv] = servico_id
            cur.execute("INSERT INTO edital_servico (edital_id, servico_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (edital_id, servico_id))

    conn.commit()
    conn.close()



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


def _base_email(conteudo_interno: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head><meta charset="UTF-8"></head>
    <body style="margin:0;padding:0;background:#f4f6f9;font-family:Arial,sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f9;padding:32px 0;">
        <tr><td align="center">
          <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
            <!-- Cabeçalho -->
            <tr>
              <td style="background:#1e3a8a;padding:24px 32px;">
                <p style="margin:0;color:#ffffff;font-size:18px;font-weight:bold;">FGV PMO</p>
                <p style="margin:4px 0 0;color:#93c5fd;font-size:13px;">Portal de Consulta de Editais</p>
              </td>
            </tr>
            <!-- Conteúdo -->
            <tr>
              <td style="padding:32px;">
                {conteudo_interno}
              </td>
            </tr>
            <!-- Rodapé -->
            <tr>
              <td style="background:#f8fafc;padding:16px 32px;border-top:1px solid #e2e8f0;">
                <p style="margin:0;color:#94a3b8;font-size:12px;">
                  Este é um e-mail automático enviado pelo Portal de Editais FGV PMO. Por favor, não responda diretamente a esta mensagem.
                </p>
              </td>
            </tr>
          </table>
        </td></tr>
      </table>
    </body>
    </html>
    """


def _linha_info(label: str, valor: str) -> str:
    return f"""
    <tr>
      <td style="padding:8px 12px;font-size:13px;color:#64748b;font-weight:600;width:160px;vertical-align:top;">{label}</td>
      <td style="padding:8px 12px;font-size:13px;color:#0f172a;vertical-align:top;">{valor}</td>
    </tr>"""


def _badge_status(status: str) -> str:
    cores = {
        "PENDENTE":    ("#fef3c7", "#92400e"),
        "EM ANÁLISE":  ("#dbeafe", "#1e40af"),
        "CONCLUÍDA":   ("#dcfce7", "#166534"),
        "RECUSADA":    ("#fee2e2", "#991b1b"),
    }
    bg, fg = cores.get(status, ("#f1f5f9", "#475569"))
    return f'<span style="background:{bg};color:{fg};padding:4px 12px;border-radius:20px;font-size:12px;font-weight:600;">{status}</span>'


def enviar_email_nova_solicitacao_para_admins(tema: str, descricao: str, solicitante: str, perfil: str, solicitacao_id: int):
    import html as _html
    emails_admin = buscar_emails_admins()
    if not emails_admin:
        return False, "Nenhum ADMIN com e-mail cadastrado."

    assunto = f"[FGV PMO] Nova solicitação de busca de edital - #{solicitacao_id}"
    conteudo = f"""
        <h2 style="margin:0 0 8px;color:#1e3a8a;font-size:20px;">Nova solicitação recebida</h2>
        <p style="margin:0 0 24px;color:#64748b;font-size:14px;">
          Uma nova solicitação de busca de edital foi registrada no Portal e aguarda análise.
        </p>
        <table width="100%" cellpadding="0" cellspacing="0"
               style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;margin-bottom:24px;">
          {_linha_info("Nº da solicitação", f"#{solicitacao_id}")}
          {_linha_info("Data", agora_str())}
          {_linha_info("Solicitante", _html.escape(solicitante))}
          {_linha_info("Perfil", perfil)}
          {_linha_info("Tema solicitado", _html.escape(tema))}
          {_linha_info("Descrição", _html.escape(descricao) if descricao else "-")}
          {_linha_info("Status atual", _badge_status("PENDENTE"))}
        </table>
        <p style="margin:0;font-size:14px;color:#475569;">
          Acesse o Portal para analisar e atualizar o status desta solicitação.
        </p>
    """
    return enviar_email(emails_admin, assunto, _base_email(conteudo))


def enviar_email_atualizacao_status_para_admins(solicitacao_id: int, tema: str, solicitante: str, novo_status: str):
    import html as _html
    emails_admin = buscar_emails_admins()
    if not emails_admin:
        return False, "Nenhum ADMIN com e-mail cadastrado."

    assunto = f"[FGV PMO] Atualização de status - Solicitação #{solicitacao_id}"
    conteudo = f"""
        <h2 style="margin:0 0 8px;color:#1e3a8a;font-size:20px;">Status de solicitação atualizado</h2>
        <p style="margin:0 0 24px;color:#64748b;font-size:14px;">
          O status da solicitação abaixo foi atualizado no Portal.
        </p>
        <table width="100%" cellpadding="0" cellspacing="0"
               style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;margin-bottom:24px;">
          {_linha_info("Nº da solicitação", f"#{solicitacao_id}")}
          {_linha_info("Data da atualização", agora_str())}
          {_linha_info("Solicitante", _html.escape(solicitante))}
          {_linha_info("Tema solicitado", _html.escape(tema))}
          {_linha_info("Novo status", _badge_status(novo_status))}
        </table>
        <p style="margin:0;font-size:14px;color:#475569;">
          Acesse o Portal para gerenciar as solicitações.
        </p>
    """
    return enviar_email(emails_admin, assunto, _base_email(conteudo))


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
        st.session_state.menu = "Base de Prazos"
    if "tema_visual" not in st.session_state:
        st.session_state.tema_visual = "Light"


def logout():
    st.session_state.logado = False
    st.session_state.usuario = None
    st.session_state.perfil = None
    st.session_state.email = None
    st.session_state.menu = "Base de Prazos"
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

def esconder_elementos_streamlit():
    """Remove elementos indesejados do Streamlit via JS."""
    st.markdown("""
    <script>
    (function() {
        function removeUnwanted() {
            // Sem remoção de botões - botão de colapso da sidebar é mantido

            // Destaca botão ativo na sidebar
            function highlightNav() {
                var sidebar = document.querySelector('[data-testid="stSidebar"]');
                if (!sidebar) { setTimeout(highlightNav, 150); return; }
                var activeText = '';
                sidebar.querySelectorAll('button').forEach(function(btn) {
                    var txt = (btn.innerText || '').trim();
                    if (txt === activeText) {
                        btn.style.setProperty('background', 'rgba(255,255,255,0.12)', 'important');
                        btn.style.setProperty('color', '#fff', 'important');
                        btn.style.setProperty('-webkit-text-fill-color', '#fff', 'important');
                        btn.style.setProperty('font-weight', '600', 'important');
                        btn.style.setProperty('border-left', '2px solid var(--fgv-bright)', 'important');
                        btn.style.setProperty('border-radius', '0 7px 7px 0', 'important');
                    }
                });
            }
            setTimeout(highlightNav, 200);
            setTimeout(highlightNav, 600);

            // Agrupa botões de nav em caixas visuais
            function groupNavButtons() {
                var sidebar = document.querySelector('[data-testid="stSidebar"]');
                if (!sidebar) return;
                // Remove caixas anteriores para não duplicar
                sidebar.querySelectorAll('.sb-group-box-js').forEach(function(el) {
                    var parent = el.parentNode;
                    while (el.firstChild) parent.insertBefore(el.firstChild, el);
                    parent.removeChild(el);
                });
                // Encontra todos os rótulos de grupo
                var labels = sidebar.querySelectorAll('.sb-group-label');
                labels.forEach(function(label) {
                    var box = document.createElement('div');
                    box.className = 'sb-group-box-js';
                    box.style.cssText = 'background:rgba(0,0,0,.2);border:1px solid rgba(255,255,255,.08);border-radius:10px;padding:4px;margin-bottom:10px;';
                    label.parentNode.insertBefore(box, label.nextSibling);
                    // Move próximos irmãos (botões) para dentro da caixa até o próximo rótulo ou separador
                    var next = box.nextSibling;
                    while (next && !next.classList?.contains('sb-group-label') && !next.classList?.contains('sb-footer-sep')) {
                        var toMove = next;
                        next = next.nextSibling;
                        // Só move se contiver um botão
                        if (toMove.querySelector && toMove.querySelector('button')) {
                            box.appendChild(toMove);
                        }
                    }
                });
            }
            setTimeout(groupNavButtons, 300);
            setTimeout(groupNavButtons, 800);
            var navObserver = new MutationObserver(function() { groupNavButtons(); });
            setTimeout(function() {
                var sidebar = document.querySelector('[data-testid="stSidebar"]');
                if (sidebar) navObserver.observe(sidebar, { childList: true, subtree: false });
            }, 500);
        }
        removeUnwanted();
        setTimeout(removeUnwanted, 500);
        setTimeout(removeUnwanted, 1500);
        var observer = new MutationObserver(function() { removeUnwanted(); });
        observer.observe(document.body, { childList: true, subtree: true });

        // Highlight active nav button
        function highlightActiveNav() {
            var menuName = window._activeMenu || '';
            var sidebar = document.querySelector('[data-testid="stSidebar"]');
            if (!sidebar) return;
            sidebar.querySelectorAll('.nav-menu button, div.nav-menu ~ div button').forEach(function(btn) {
                var txt = btn.innerText || '';
                // Remove previous active style
                btn.style.removeProperty('background');
                btn.style.removeProperty('color');
                btn.style.removeProperty('-webkit-text-fill-color');
                btn.style.removeProperty('border-left');
                btn.style.removeProperty('font-weight');
            });
        }
        setTimeout(highlightActiveNav, 300);
    })();
    </script>
    """, unsafe_allow_html=True)


def header_principal():
    esconder_elementos_streamlit()
    logo_b64 = get_base64_logo_completo()

    import html as _html_esc
    usuario_safe = _html_esc.escape(str(st.session_state.get("usuario", "")))
    perfil_safe  = _html_esc.escape(str(st.session_state.get("perfil", "")))
    menu_safe    = _html_esc.escape(str(st.session_state.get("menu", "Portal")))
    inicial = usuario_safe[0].upper() if usuario_safe else "U"

    st.markdown(
        f"""
        <div class="header-full-width">
            <div class="header-inner">
                <div class="header-left">
                    <div class="header-logo-block">
                        <img src="data:image/png;base64,{logo_b64}" class="header-logo-full"/>
                    </div>
                    <div class="header-divider"></div>
                    <div class="header-text-block">
                        <div class="header-title">Portal de Editais/Projetos</div>
                        <div class="header-subtitle">FGV &middot; Project Management Office</div>
                    </div>
                </div>
                <div class="header-right">
                    <div class="header-page-name">{menu_safe}</div>
                    <div class="header-profile">
                        <div class="header-avatar">{inicial}</div>
                        {usuario_safe}
                    </div>
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
    logo_b64 = get_base64_logo()
    st.markdown(f"""
    <style>
    /* Login - fundo azul claro institucional */
    .stApp {{ background: #e8eef6 !important; }}
    section.main .block-container {{ padding: 0 !important; max-width: 100% !important; }}

    /* Área superior com gradiente navy */
    .lp-top {{
        background: linear-gradient(135deg, #0b1f3a 0%, #112a50 55%, #1a3f6f 100%);
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        padding: 40px 24px 40px;
    }}
    .lp-logo {{ text-align: center; margin-bottom: 0; }}
    .lp-logo img {{ height: 68px; width: auto; object-fit: contain; }}


    /* Wrapper que centraliza card+form como bloco único */
    .lp-card-wrap {{
        background: #e8eef6;
        display: flex; justify-content: center;
        padding: 0 24px 0;
        margin-top: -1px;
    }}
    /* Card do título - faz parte do mesmo bloco visual do form */
    .lp-card {{
        width: 100%; max-width: 400px;
        background: #ffffff;
        border-radius: 16px 16px 0 0;
        padding: 28px 28px 20px;
        margin-top: -24px;
        box-shadow: none;
        position: relative; z-index: 1;
        box-sizing: border-box;
    }}
    /* Form alinhado com o card */
    .stForm {{
        background: #ffffff !important;
        width: 100% !important;
        max-width: 400px !important;
        margin: -8px auto 0 !important;
        padding: 0 28px 24px !important;
        border: none !important;
        border-radius: 0 0 16px 16px !important;
        box-shadow: 0 8px 32px rgba(11,31,58,0.12) !important;
        box-sizing: border-box !important;
    }}
    .lp-title {{
        color: #0b1f3a; font-size: 1.25rem; font-weight: 700;
        letter-spacing: -0.02em; text-align: center;
        margin-bottom: 3px; font-family: 'Inter', sans-serif;
    }}
    .lp-sub {{
        color: #3d5575; font-size: 0.72rem; text-align: center;
        letter-spacing: 0.07em; text-transform: uppercase; font-weight: 500;
        margin-bottom: 20px; font-family: 'Inter', sans-serif;
    }}
    .lp-divider {{
        height: 1px; background: #e2e8f0; margin-bottom: 20px;
    }}

    /* Labels em azul claro */
    .lp-card label,
    .lp-card .stTextInput label,
    .lp-card [data-testid="stWidgetLabel"] p {{
        color: #4d9fff !important;
        -webkit-text-fill-color: #4d9fff !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
    }}
    .lp-card .stTextInput input {{
        background: #f5f8fd !important;
        border: 1.5px solid #d0dff0 !important;
        border-radius: 8px !important;
        color: #0d1b2e !important;
        -webkit-text-fill-color: #0d1b2e !important;
    }}
    .lp-card .stTextInput input:focus {{
        border-color: #2979d4 !important;
        box-shadow: 0 0 0 3px rgba(41,121,212,0.15) !important;
    }}
    .lp-card .stTextInput input::placeholder {{ color: #94a8c2 !important; }}
    .lp-card .stFormSubmitButton > button {{
        background: linear-gradient(135deg, #1d6fc4, #2979d4) !important;
        color: #fff !important; font-weight: 600 !important;
        border: none !important; border-radius: 8px !important;
        height: 44px !important; font-size: 0.9rem !important;
        box-shadow: 0 4px 16px rgba(41,121,212,0.3) !important;
        margin-top: 6px !important; transform: none !important;
    }}
    .lp-card .stFormSubmitButton > button:hover {{
        opacity: 0.9 !important; transform: none !important;
    }}

    /* Rodapé em azul escuro (fundo claro) */
    section.main .block-container > div > div > div {{
        background: transparent !important;
    }}
    .stForm > div {{ border: none !important; }}
    .lp-footer {{
        color: #1a3f6f;
        font-size: 0.75rem; text-align: center;
        padding: 16px 0 32px;
        background: #e8eef6;
        font-family: 'Inter', sans-serif;
        letter-spacing: 0.02em;
    }}
    </style>

    <div class="lp-top">
        <div class="lp-logo">
            <img src="data:image/png;base64,{logo_b64}" />
        </div>
    </div>
    <div class="lp-card-wrap">
        <div class="lp-card">
            <div class="lp-title">Portal de Editais/Projetos</div>
            <div class="lp-sub">FGV &middot; Project Management Office</div>
            <div class="lp-divider"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("form_login", clear_on_submit=False):
        usuario = st.text_input("Usuário", placeholder="seu.usuario")
        senha = st.text_input("Senha", type="password", placeholder="••••••••")
        entrar = st.form_submit_button("Entrar", use_container_width=True)

    st.markdown("""
    <div class="lp-footer">Acesso restrito a usuários autorizados</div>
    """, unsafe_allow_html=True)

    if entrar:
        try:
            user = autenticar(usuario, senha)
        except PermissionError as pe:
            st.error(str(pe))
            st.stop()
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
        perfil = st.session_state.perfil
        menu_atual = st.session_state.menu

        # Logo
        # Logo via st.image — funciona em todos os temas
        try:
            import base64 as _b64, os as _os
            _paths = ["assets/FGV_PMO_LOGO_COMPLETO.png", "assets/fgv pmo logo.png"]
            _img_path = next((p for p in _paths if _os.path.exists(p)), None)
            if _img_path:
                from PIL import Image as _PILImage
                import io as _io
                _img = _PILImage.open(_img_path).convert("RGBA")
                # Inverte para branco (fundo transparente preservado)
                _r, _g, _b, _a = _img.split()
                _white = _PILImage.new("RGBA", _img.size, (255,255,255,0))
                _white.paste(_PILImage.merge("RGBA", [
                    _PILImage.eval(_r, lambda x: 255),
                    _PILImage.eval(_g, lambda x: 255),
                    _PILImage.eval(_b, lambda x: 255),
                    _a
                ]), mask=_a)
                _buf = _io.BytesIO()
                _white.save(_buf, format="PNG")
                _buf.seek(0)
                st.image(_buf, width=180)
            else:
                st.markdown("**FGV PMO**")
        except Exception:
            # Fallback simples se PIL não disponível
            _logo_b64 = get_base64_logo_completo() or get_base64_logo()
            if _logo_b64:
                st.markdown(f'<div style="text-align:center;padding:8px 0;">' +
                            f'<img src="data:image/png;base64,{_logo_b64}" ' +
                            f'style="width:180px;filter:brightness(0) invert(1);"/></div>',
                            unsafe_allow_html=True)
        st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)

        # Monta grupos
        grupo_consulta = ["Base de Prazos"]
        if perfil in ("ADMIN", "PMO"):
            grupo_consulta += ["Análise de Prazos"]
        grupo_consulta.append("Projetos Concluídos")

        grupo_operacional = []
        if perfil in ("ADMIN", "PMO", "COORDENADOR"):
            if perfil in ("ADMIN", "PMO"):
                try:
                    df_pend = listar_solicitacoes()
                    n_pend = len(df_pend[df_pend["status"] == "PENDENTE"])
                    grupo_operacional.append(f"Solicitações ({n_pend})" if n_pend > 0 else "Solicitações")
                except Exception:
                    grupo_operacional.append("Solicitações")
            else:
                grupo_operacional.append("Solicitações")
        if perfil in ("ADMIN", "PMO"):
            grupo_operacional.append("Base de dados")

        grupo_conta = ["Minha conta"]
        if perfil == "ADMIN":
            grupo_conta.append("Usuários")

        grupos = [
            ("Consulta", grupo_consulta),
            ("Gestão", grupo_operacional),
            ("Configurações", grupo_conta),
        ]

        all_opcoes = []
        for _, grupo_itens in grupos:
            all_opcoes.extend(grupo_itens)

        for opcao in all_opcoes:
            if st.button(opcao, key=f"nav_{opcao}", use_container_width=True):
                if st.session_state.menu != opcao:
                    st.session_state.menu = opcao
                    st.rerun()

        # JS para destacar botão ativo (injeta menu_atual como valor real)
        import html as _h_sb
        menu_safe = _h_sb.escape(repr(menu_atual))
        st.markdown(f"""
        <script>
        (function(){{
            var active = {menu_safe};
            function hi(){{
                var sb = document.querySelector('[data-testid="stSidebar"]');
                if(!sb){{setTimeout(hi,150);return;}}
                sb.querySelectorAll('button').forEach(function(b){{
                    var t=(b.innerText||'').trim();
                    if(t===active){{
                        b.style.setProperty('background','rgba(255,255,255,0.12)','important');
                        b.style.setProperty('color','#fff','important');
                        b.style.setProperty('-webkit-text-fill-color','#fff','important');
                        b.style.setProperty('font-weight','600','important');
                        b.style.setProperty('border-left','2px solid #4d9fff','important');
                        b.style.setProperty('border-radius','0 7px 7px 0','important');
                    }} else {{
                        b.style.removeProperty('border-left');
                        b.style.removeProperty('border-radius');
                        b.style.removeProperty('font-weight');
                    }}
                }});
            }}
            hi();setTimeout(hi,400);
        }})();
        </script>
        """, unsafe_allow_html=True)

        # Rodapé
        st.markdown('<div class="sb-footer-sep"></div>', unsafe_allow_html=True)
        fc1, fc2, fc3 = st.columns([1, 1, 2])
        with fc1:
            if st.button("●" if tema_atual == "Light" else "○", key="btn_light", use_container_width=True):
                if tema_atual != "Light":
                    st.session_state.tema_visual = "Light"
                    st.rerun()
        with fc2:
            if st.button("●" if tema_atual == "Dark" else "○", key="btn_dark", use_container_width=True):
                if tema_atual != "Dark":
                    st.session_state.tema_visual = "Dark"
                    st.rerun()
        with fc3:
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

    col_tema     = achar_coluna(["tema"])
    col_subtema  = achar_coluna(["subtema"])
    col_estado   = achar_coluna(["estado"])
    col_municipio= achar_coluna(["municipio", "município"])
    col_nome     = achar_coluna(["nome", "denominacao", "denominação"])
    col_desc     = achar_coluna(["descricao", "descrição"])
    col_codigo   = achar_coluna(["codigo", "código", "codigo_planilha"])
    col_obs      = achar_coluna(["observacao", "observação", "obs"])
    col_custo    = achar_coluna(["custo", "valor", "custo_execucao"])
    col_prazo    = achar_coluna(["prazo_meses", "prazo"])
    col_data     = achar_coluna(["data_edital", "data edital", "data"])

    if col_custo: df[col_custo] = pd.to_numeric(df[col_custo], errors="coerce")
    if col_prazo: df[col_prazo] = pd.to_numeric(df[col_prazo], errors="coerce")
    if col_data:  df[col_data]  = pd.to_datetime(df[col_data], errors="coerce")

    def opcoes(df_base, col):
        if not col: return ["Todos"]
        return ["Todos"] + sorted(df_base[col].dropna().replace("", pd.NA).dropna().unique().tolist())

    # ── Filtros principais ──
    st.markdown('<div class="section-card">', unsafe_allow_html=True)

    filtrado = df.copy()
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        tema = st.selectbox("Tema", opcoes(filtrado, col_tema), label_visibility="visible")
    if col_tema and tema != "Todos":
        filtrado = filtrado[filtrado[col_tema] == tema]
    with f2:
        subtema = st.selectbox("Subtema", opcoes(filtrado, col_subtema))
    if col_subtema and subtema != "Todos":
        filtrado = filtrado[filtrado[col_subtema] == subtema]
    with f3:
        estado = st.selectbox("Estado", opcoes(filtrado, col_estado))
    if col_estado and estado != "Todos":
        filtrado = filtrado[filtrado[col_estado] == estado]
    with f4:
        municipio = st.selectbox("Município", opcoes(filtrado, col_municipio))
    if col_municipio and municipio != "Todos":
        filtrado = filtrado[filtrado[col_municipio] == municipio]

    busca = st.text_input("Busca textual", placeholder="Nome, descrição, código...",
                          label_visibility="collapsed")
    if busca:
        texto_cols = [c for c in [col_nome, col_desc, col_codigo, col_obs] if c]
        if texto_cols:
            mask = False
            for c in texto_cols:
                mask = mask | filtrado[c].astype(str).str.contains(busca, case=False, na=False)
            filtrado = filtrado[mask]

    # Filtros avançados colapsáveis
    with st.expander("Filtros avançados - custo e prazo"):
        c9, c10, c11, c12 = st.columns(4)
        custo_min = c9.number_input("Custo mínimo (R$)", min_value=0.0, value=0.0, step=1000.0, format="%.2f")
        custo_max = c10.number_input("Custo máximo (R$)", min_value=0.0, value=0.0, step=1000.0, format="%.2f")
        prazo_min = c11.number_input("Prazo mínimo (meses)", min_value=0.0, value=0.0, step=1.0, format="%.1f")
        prazo_max = c12.number_input("Prazo máximo (meses)", min_value=0.0, value=0.0, step=1.0, format="%.1f")

    if col_custo:
        if custo_min > 0: filtrado = filtrado[filtrado[col_custo] >= custo_min]
        if custo_max > 0: filtrado = filtrado[filtrado[col_custo] <= custo_max]
    if col_prazo:
        if prazo_min > 0: filtrado = filtrado[filtrado[col_prazo] >= prazo_min]
        if prazo_max > 0: filtrado = filtrado[filtrado[col_prazo] <= prazo_max]

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Métricas ──
    total_registros = len(filtrado)
    total_temas     = filtrado[col_tema].nunique()   if col_tema   else 0
    total_estados   = filtrado[col_estado].nunique() if col_estado else 0
    custo_medio     = filtrado[col_custo].mean()     if col_custo and not filtrado.empty else 0

    m1, m2, m3, m4 = st.columns(4)
    with m1: metric_card("Registros filtrados", total_registros)
    with m2: metric_card("Temas", total_temas)
    with m3: metric_card("Estados", total_estados)
    with m4: metric_card("Custo médio", formatar_numero(custo_medio if pd.notna(custo_medio) else 0))

    # ── Abas: Tabela | Evolução | Mapa ──
    tab_tabela, tab_evolucao, tab_mapa = st.tabs(["Tabela", "Evolução por tema", "Distribuição geográfica"])

    # ── TAB Tabela ──
    with tab_tabela:
        colunas_remover = ["id","tipo_edital","codigo_planilha","metodo_calculo","valor_min","valor_max","observacao"]
        colunas_remover_existentes = [c for c in colunas_remover if c in filtrado.columns]
        df_exibicao = filtrado.drop(columns=colunas_remover_existentes)

        mapa_colunas = {
            "codigo":"Código","nome":"Nome","descricao":"Objetivo do Projeto",
            "tema":"Tema","subtema":"Subtema","pais":"País","estado":"Estado",
            "municipio":"Município","nome_edital":"Edital",
            "esforco":"Parâmetro","unidade":"Unidade",
            "esforco2":"esforco2","unidade2":"unidade2",
            "servicos":"Serviços",
            "custo_execucao":"Custo da Execução (R$)","custo":"Custo da Execução (R$)",
            "prazo_meses":"Prazo (meses)","data_edital":"Data do edital",
            "fonte_dado":"URL"
        }
        df_exibicao = df_exibicao.rename(columns={k:v for k,v in mapa_colunas.items() if k in df_exibicao.columns})

        if "Data do edital" in df_exibicao.columns:
            df_exibicao["Data do edital"] = pd.to_datetime(df_exibicao["Data do edital"], errors="coerce").dt.strftime("%d/%m/%Y")

        def fmt_brl(x):
            if pd.isnull(x) or x == 0: return ""
            return f"R$ {x:,.2f}".replace(",","X").replace(".",",").replace("X",".")

        if "Custo da Execução (R$)" in df_exibicao.columns:
            df_exibicao["Custo da Execução (R$)"] = df_exibicao["Custo da Execução (R$)"].apply(fmt_brl)

        ipca_bd = carregar_ipca()
        from datetime import datetime as _dt_now
        data_ref_bd = f"{_dt_now.now().year}-{_dt_now.now().month:02d}"
        if ipca_bd and "custo_execucao" in filtrado.columns and "data_edital" in filtrado.columns:
            def _corrigir_linha(row):
                custo = row.get("custo_execucao")
                data_b = row.get("data_edital")
                if not custo or not data_b or pd.isnull(custo) or pd.isnull(data_b): return ""
                try:
                    v = corrigir_ipca(float(custo), str(data_b)[:7], data_ref_bd, ipca_bd)
                    return fmt_brl(v) if v else ""
                except Exception: return ""
            df_exibicao["Custo da Execução corrigido pelo IPCA (R$)"] = filtrado.apply(_corrigir_linha, axis=1)
        else:
            df_exibicao["Custo da Execução corrigido pelo IPCA (R$)"] = ""

        if "Custo da Execução (R$)" in df_exibicao.columns and "Custo da Execução corrigido pelo IPCA (R$)" in df_exibicao.columns:
            cols = list(df_exibicao.columns)
            idx_custo = cols.index("Custo da Execução (R$)")
            cols.remove("Custo da Execução corrigido pelo IPCA (R$)")
            cols.insert(idx_custo + 1, "Custo da Execução corrigido pelo IPCA (R$)")
            df_exibicao = df_exibicao[cols]

        # Paginação
        PAGE_SIZE = 50
        total = len(df_exibicao)
        n_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
        if "pagina_consulta" not in st.session_state:
            st.session_state["pagina_consulta"] = 1
        if st.session_state["pagina_consulta"] > n_pages:
            st.session_state["pagina_consulta"] = 1
        pg_atual = st.session_state["pagina_consulta"]
        inicio = (pg_atual - 1) * PAGE_SIZE
        fim = min(inicio + PAGE_SIZE, total)

        _col_cfg_consulta = {
            "Parâmetro": st.column_config.TextColumn(
                "1° Parâmetro",
                help="Parâmetro utilizado para calculo de execução do projeto."
            ),
            "Unidade": st.column_config.TextColumn(
                "Unidade",
                help="Unidade de medida referente ao parâmetro."
            ),
            "esforco2": st.column_config.TextColumn(
                "2° Parâmetro",
                help="Parâmetro utilizado para calculo de execução do projeto."
            ),
            "unidade2": st.column_config.TextColumn(
                "Unidade 2",
                help="Unidade de medida referente ao 2° parâmetro."
            ),
        }
        if "Custo da Execução corrigido pelo IPCA (R$)" in df_exibicao.columns:
            _col_cfg_consulta["Custo da Execução corrigido pelo IPCA (R$)"] = st.column_config.TextColumn(
                "Custo da Execução corrigido pelo IPCA (R$)",
                help="Corrige o custo inicial pelo IPCA acumulado desde a data do edital ate o mes atual. Formula: Valor x PI(1 + IPCA_mes/100) para cada mes entre a data base e hoje. Fonte: Banco Central do Brasil, serie SGS 433."
            )
        st.dataframe(df_exibicao.iloc[inicio:fim], use_container_width=True,
                     hide_index=True, column_config=_col_cfg_consulta)

        # Paginação
        pg1, pg2, pg3, pg4, pg5 = st.columns([1, 1, 3, 1, 1])
        with pg1:
            if st.button("Primeira", use_container_width=True, disabled=pg_atual==1):
                st.session_state["pagina_consulta"] = 1; st.rerun()
        with pg2:
            if st.button("Anterior", use_container_width=True, disabled=pg_atual==1):
                st.session_state["pagina_consulta"] -= 1; st.rerun()
        with pg3:
            st.markdown(
                f"<div style='text-align:center;padding:8px 0;font-size:13px;color:var(--ink-secondary);'>"
                f"Página <b>{pg_atual}</b> de <b>{n_pages}</b> &nbsp;·&nbsp; "
                f"<b>{inicio+1}</b>-<b>{fim}</b> de <b>{total}</b> registros</div>",
                unsafe_allow_html=True)
        with pg4:
            if st.button("Próxima", use_container_width=True, disabled=pg_atual==n_pages):
                st.session_state["pagina_consulta"] += 1; st.rerun()
        with pg5:
            if st.button("Última", use_container_width=True, disabled=pg_atual==n_pages):
                st.session_state["pagina_consulta"] = n_pages; st.rerun()

        # Exportação em linha separada
        if pode_baixar_arquivos(st.session_state.perfil):
            dl1, dl2, _ = st.columns([1, 1, 4])
            with dl1:
                st.download_button("Exportar CSV", data=filtrado.to_csv(index=False).encode("utf-8-sig"),
                                   file_name="consulta_editais.csv", mime="text/csv",
                                   use_container_width=True)
            with dl2:
                st.download_button("Exportar Excel", data=to_excel_bytes(filtrado),
                                   file_name="consulta_editais.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   use_container_width=True)

    # ── TAB Evolução ──
    with tab_evolucao:
        if not filtrado.empty and col_data and col_tema:
            try:
                import plotly.graph_objects as go
                df_graf = filtrado[[col_data, col_tema]].copy()
                df_graf[col_data] = pd.to_datetime(df_graf[col_data], errors="coerce")
                df_graf = df_graf.dropna(subset=[col_data])
                df_graf["ano"] = df_graf[col_data].dt.year.astype(int)
                df_graf = df_graf[df_graf["ano"] >= 2015]
                if not df_graf.empty:
                    pivot = df_graf.groupby(["ano", col_tema]).size().reset_index(name="n")
                    temas_graf = pivot.groupby(col_tema)["n"].sum().nlargest(8).index.tolist()
                    pivot = pivot[pivot[col_tema].isin(temas_graf)]
                    cores = ["#1d6fc4","#10b981","#f59e0b","#ef4444","#8b5cf6",
                             "#06b6d4","#ec4899","#84cc16"]
                    fig = go.Figure()
                    for i, tema_g in enumerate(temas_graf):
                        d = pivot[pivot[col_tema] == tema_g].sort_values("ano")
                        fig.add_trace(go.Scatter(
                            x=d["ano"].tolist(), y=d["n"].tolist(),
                            name=tema_g, mode="lines+markers",
                            line=dict(width=2, color=cores[i % len(cores)]),
                            marker=dict(size=6),
                        ))
                    fig.update_layout(
                        title="Evolução de editais/projetos por tema",
                        xaxis_title="Ano", yaxis_title="Nº de editais/projetos",
                        height=400, template="plotly_white",
                        legend=dict(orientation="h", yanchor="bottom", y=-0.4),
                        margin=dict(t=50, b=120, l=40, r=20),
                        xaxis=dict(tickmode="linear", dtick=1),
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Sem dados de evolução para o filtro selecionado.")
            except ImportError:
                st.info("Instale plotly para visualizar os gráficos.")
        else:
            st.info("Sem dados suficientes para o gráfico.")

    # ── TAB Mapa ──
    with tab_mapa:
        if not filtrado.empty:
            try:
                import plotly.express as px
                tem_estado = "estado" in filtrado.columns and filtrado["estado"].notna().any()
                tem_pais   = "pais"   in filtrado.columns and filtrado["pais"].notna().any()

                if tem_estado:
                    df_mapa = (filtrado.groupby(["pais","estado"], dropna=True)
                               .size().reset_index(name="qtd"))
                    df_mapa = df_mapa[df_mapa["qtd"] > 0]
                    uf_map = {
                        "Acre":"AC","Alagoas":"AL","Amapá":"AP","Amazonas":"AM",
                        "Bahia":"BA","Ceará":"CE","Distrito Federal":"DF",
                        "Espírito Santo":"ES","Goiás":"GO","Maranhão":"MA",
                        "Mato Grosso":"MT","Mato Grosso do Sul":"MS","Minas Gerais":"MG",
                        "Pará":"PA","Paraíba":"PB","Paraná":"PR","Pernambuco":"PE",
                        "Piauí":"PI","Rio de Janeiro":"RJ","Rio Grande do Norte":"RN",
                        "Rio Grande do Sul":"RS","Rondônia":"RO","Roraima":"RR",
                        "Santa Catarina":"SC","São Paulo":"SP","Sergipe":"SE","Tocantins":"TO",
                    }
                    df_br = df_mapa[df_mapa["pais"] == "Brasil"].copy()
                    df_br["uf"] = df_br["estado"].map(uf_map)
                    df_br = df_br.dropna(subset=["uf"])

                    if not df_br.empty:
                        sub_mapa, sub_tabela = st.tabs(["Mapa", "Tabela por estado"])
                        with sub_mapa:
                            fig_mapa = px.choropleth(
                                df_br,
                                geojson="https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson",
                                locations="uf", featureidkey="properties.sigla",
                                color="qtd", hover_name="estado",
                                hover_data={"qtd":True,"uf":False},
                                color_continuous_scale=[[0,"#dbeafe"],[0.3,"#93c5fd"],[0.6,"#3b82f6"],[1.0,"#1e3a8a"]],
                                labels={"qtd":"Editais/Projetos"},
                                title="Editais/Projetos por estado (Brasil)",
                            )
                            fig_mapa.update_geos(fitbounds="locations", visible=False)
                            fig_mapa.update_layout(height=500, margin=dict(l=0,r=0,t=40,b=0),
                                                   coloraxis_colorbar=dict(title="Qtd."))
                            st.plotly_chart(fig_mapa, use_container_width=True)
                        with sub_tabela:
                            st.dataframe(df_mapa.sort_values("qtd", ascending=False)
                                         .rename(columns={"pais":"País","estado":"Estado","qtd":"Editais/Projetos"}),
                                         use_container_width=True, hide_index=True)
                            df_top = df_br.sort_values("qtd", ascending=True).tail(20)
                            fig_bar = px.bar(df_top, x="qtd", y="estado", orientation="h",
                                             labels={"qtd":"Editais/Projetos","estado":"Estado"},
                                             color="qtd", color_continuous_scale=["#93c5fd","#1e3a8a"],
                                             title="Top 20 estados")
                            fig_bar.update_layout(height=420, template="plotly_white",
                                                  showlegend=False, coloraxis_showscale=False,
                                                  margin=dict(l=10,r=10,t=40,b=10))
                            st.plotly_chart(fig_bar, use_container_width=True)

                elif tem_pais:
                    df_pais = filtrado.groupby("pais", dropna=True).size().reset_index(name="qtd")
                    fig_pais = px.bar(df_pais.sort_values("qtd", ascending=False),
                                      x="pais", y="qtd",
                                      labels={"pais":"País","qtd":"Editais/Projetos"},
                                      title="Editais/Projetos por país",
                                      color="qtd", color_continuous_scale=["#93c5fd","#1e3a8a"])
                    fig_pais.update_layout(height=350, template="plotly_white",
                                           showlegend=False, coloraxis_showscale=False)
                    st.plotly_chart(fig_pais, use_container_width=True)
                else:
                    st.info("Sem dados geográficos para exibir.")
            except ImportError:
                st.info("Instale plotly para visualizar o mapa.")
        else:
            st.info("Sem dados para o mapa com o filtro selecionado.")



# =========================================================
# SOLICITAÇÕES
# =========================================================
def pagina_solicitacoes():
    import html as _html_sol
    header_principal()

    def badge_status(s):
        cores = {
            "PENDENTE":    ("#fef3c7","#92400e","#f59e0b"),
            "EM ANÁLISE":  ("#dbeafe","#1e40af","#3b82f6"),
            "CONCLUÍDA":   ("#dcfce7","#166534","#10b981"),
            "RECUSADA":    ("#fee2e2","#991b1b","#ef4444"),
        }
        s_safe = s if s in cores else "DESCONHECIDO"
        bg, fg, _ = cores.get(s_safe, ("#f1f5f9","#475569","#94a3b8"))
        return (f'<span style="background:{bg};color:{fg};padding:3px 12px;'
                f'border-radius:999px;font-size:11px;font-weight:700;'
                f'letter-spacing:0.04em;">{_html_sol.escape(s_safe)}</span>')

    def sol_card(row):
        import html as _h
        sid    = int(row["id"])
        tema_s = _h.escape(str(row.get("tema_solicitado", "")))
        desc_s = _h.escape(str(row.get("descricao", "") or ""))
        sol_s  = _h.escape(str(row.get("solicitante", "")))
        data_s = str(row.get("data_solicitacao", ""))[:10]
        status = str(row.get("status", ""))
        badge  = badge_status(status)
        cores_borda = {
            "PENDENTE": "#f59e0b", "EM ANÁLISE": "#3b82f6",
            "CONCLUÍDA": "#10b981", "RECUSADA": "#ef4444",
        }
        cor = cores_borda.get(status, "#94a3b8")
        desc_html = (f'<div style="color:#64748b;font-size:0.82rem;margin-bottom:4px;">{desc_s}</div>'
                     if desc_s else "")
        st.markdown(f"""
        <div style="border:1px solid #e2e8f0;border-left:4px solid {cor};
                    border-radius:10px;padding:14px 16px;background:#fff;margin-bottom:2px;">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;">
                <div style="flex:1;min-width:0;">
                    <div style="font-weight:700;color:#0f172a;font-size:0.92rem;margin-bottom:3px;">
                        #{sid} &nbsp;·&nbsp; {tema_s}
                    </div>
                    {desc_html}
                    <div style="color:#94a3b8;font-size:0.75rem;">{sol_s} &nbsp;·&nbsp; {data_s}</div>
                </div>
                <div style="flex-shrink:0;padding-top:2px;">{badge}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Nova solicitação ──
    if pode_solicitar(st.session_state.perfil):
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Nova solicitação")
        st.caption("Descreva o tema que deseja pesquisar. A equipe PMO será notificada.")
        with st.form("form_solicitacao_tema", clear_on_submit=True):
            tema = st.text_input("Tema da pesquisa",
                                 placeholder="Ex: Pavimentação urbana, Saneamento rural...")
            descricao = st.text_area("Descrição complementar (opcional)",
                                     placeholder="Palavras-chave, região de interesse, observações...",
                                     height=90)
            enviar = st.form_submit_button("Enviar solicitação", use_container_width=True)
        if enviar:
            if not tema.strip():
                st.warning("Informe o tema da pesquisa.")
            else:
                solicitacao_id = inserir_solicitacao(
                    tema=tema, descricao=descricao,
                    solicitante=st.session_state.usuario,
                    perfil=st.session_state.perfil,
                )
                ok_email, _ = enviar_email_nova_solicitacao_para_admins(
                    tema=tema, descricao=descricao,
                    solicitante=st.session_state.usuario,
                    perfil=st.session_state.perfil,
                    solicitacao_id=solicitacao_id,
                )
                st.success("Solicitação registrada e notificação enviada." if ok_email
                           else "Solicitação registrada.")
                st.cache_data.clear()
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Painel ADMIN/PMO: cards com controle inline ──
    if pode_ver_solicitacoes(st.session_state.perfil):
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        df_sol = listar_solicitacoes()

        ha, hb = st.columns([3, 1])
        with ha:
            st.subheader("Solicitações recebidas")
        with hb:
            filtro = st.selectbox("Filtrar", ["Todas","PENDENTE","EM ANÁLISE","CONCLUÍDA","RECUSADA"],
                                  key="sol_filtro", label_visibility="collapsed")

        df_view = df_sol if filtro == "Todas" else df_sol[df_sol["status"] == filtro]

        n_pend = len(df_sol[df_sol["status"] == "PENDENTE"])
        if n_pend:
            st.markdown(
                f'<div style="display:inline-flex;align-items:center;gap:6px;'
                f'background:#fef3c7;border:1px solid #fcd34d;border-radius:8px;'
                f'padding:6px 14px;font-size:0.82rem;color:#92400e;font-weight:600;'
                f'margin-bottom:12px;">{n_pend} pendente(s) aguardando análise</div>',
                unsafe_allow_html=True,
            )

        if df_view.empty:
            st.info("Nenhuma solicitação encontrada.")
        else:
            for _, row in df_view.iterrows():
                sol_card(row)
                sid = int(row["id"])
                _, cc2, cc3 = st.columns([3, 2, 1])
                with cc2:
                    novo_status = st.selectbox(
                        "Status", ["PENDENTE","EM ANÁLISE","CONCLUÍDA","RECUSADA"],
                        index=(["PENDENTE","EM ANÁLISE","CONCLUÍDA","RECUSADA"].index(row["status"])
                               if row["status"] in ["PENDENTE","EM ANÁLISE","CONCLUÍDA","RECUSADA"] else 0),
                        key=f"status_{sid}", label_visibility="collapsed",
                    )
                with cc3:
                    if st.button("Salvar", key=f"salvar_{sid}", use_container_width=True):
                        dados_sol = obter_solicitacao_por_id(sid)
                        if dados_sol:
                            _, tema_sol, _, sol_name, _, _, _ = dados_sol
                            atualizar_status_solicitacao(sid, novo_status)
                            enviar_email_atualizacao_status_para_admins(
                                solicitacao_id=sid, tema=tema_sol,
                                solicitante=sol_name, novo_status=novo_status,
                            )
                            st.cache_data.clear()
                            st.rerun()
                st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    # ── Minhas solicitações ──
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Minhas solicitações")
    df_todas = listar_solicitacoes()
    df_minhas = df_todas[
        df_todas["solicitante"].str.upper() == st.session_state.usuario.upper()
    ].copy()
    if df_minhas.empty:
        st.info("Você ainda não possui solicitações registradas.")
    else:
        st.caption(f"{len(df_minhas)} solicitação(ões) registrada(s)")
        for _, row in df_minhas.iterrows():
            sol_card(row)
    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# BASE DE DADOS
# =========================================================
def _inserir_edital_individual(tema, subtema, pais, estado, municipio,
                                nome_edital, descricao, servicos, esforco,
                                unidade, prazo_meses, custo_execucao,
                                valor_min, valor_max, data_edital,
                                codigo_planilha, observacao):
    """Insere um único edital na base mantendo a normalização."""
    conn = get_conn()
    cur = conn.cursor()

    def upsert(table, nome):
        _TABELAS_PERMITIDAS = {
            "tema", "subtema", "pais", "estado", "municipio",
            "tipo_edital", "unidade", "fonte_dado", "servico"
        }
        if table not in _TABELAS_PERMITIDAS:
            raise ValueError(f"Tabela não permitida: {table}")
        if not nome:
            return None
        cur.execute(f"SELECT id FROM {table} WHERE nome = %s", (nome,))
        row = cur.fetchone()
        if row:
            return row[0]
        cur.execute(f"INSERT INTO {table} (nome) VALUES (%s) RETURNING id", (nome,))
        return cur.fetchone()[0]

    # Dimensões
    tema_id = upsert("tema", tema)

    subtema_id = None
    if subtema:
        cur.execute("SELECT id FROM subtema WHERE tema_id = %s AND nome = %s", (tema_id, subtema))
        row = cur.fetchone()
        if row:
            subtema_id = row[0]
        else:
            cur.execute("INSERT INTO subtema (tema_id, nome) VALUES (%s, %s) RETURNING id", (tema_id, subtema))
            subtema_id = cur.fetchone()[0]

    pais_id = upsert("pais", pais)

    estado_id = None
    if estado:
        cur.execute("SELECT id FROM estado WHERE nome = %s", (estado,))
        row = cur.fetchone()
        if row:
            estado_id = row[0]
        else:
            cur.execute("INSERT INTO estado (pais_id, nome) VALUES (%s, %s) RETURNING id", (pais_id, estado))
            estado_id = cur.fetchone()[0]

    municipio_id = None
    if municipio:
        cur.execute("SELECT id FROM municipio WHERE estado_id IS NOT DISTINCT FROM %s AND nome = %s", (estado_id, municipio))
        row = cur.fetchone()
        if row:
            municipio_id = row[0]
        else:
            cur.execute("INSERT INTO municipio (estado_id, nome) VALUES (%s, %s) RETURNING id", (estado_id, municipio))
            municipio_id = cur.fetchone()[0]

    unidade_id = upsert("unidade", unidade)

    def safe_float(v):
        try:
            return float(v) if v else None
        except Exception:
            return None

    cur.execute("""
        INSERT INTO edital (
            tema_id, subtema_id, pais_id, estado_id, municipio_id,
            nome_edital, descricao, esforco, unidade_id, prazo_meses,
            codigo_planilha, observacao, custo_execucao,
            data_edital, valor_min, valor_max
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING id
    """, (
        tema_id, subtema_id, pais_id, estado_id, municipio_id,
        nome_edital, descricao, esforco, unidade_id,
        safe_float(prazo_meses), codigo_planilha, observacao,
        safe_float(custo_execucao), data_edital,
        safe_float(valor_min), safe_float(valor_max),
    ))
    edital_id = cur.fetchone()[0]

    # Serviços
    if servicos:
        for serv in normalizar_servicos(servicos):
            servico_id = None
            cur.execute("SELECT id FROM servico WHERE nome = %s", (serv,))
            row = cur.fetchone()
            if row:
                servico_id = row[0]
            else:
                cur.execute("INSERT INTO servico (nome) VALUES (%s) RETURNING id", (serv,))
                servico_id = cur.fetchone()[0]
            cur.execute("INSERT INTO edital_servico (edital_id, servico_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                       (edital_id, servico_id))

    conn.commit()
    conn.close()
    return edital_id


def pagina_base():
    header_principal()
    df = carregar_view()

    # ── Métricas de resumo ──
    st.markdown('<div class="section-card">', unsafe_allow_html=True)

    if not df.empty:
        m1, m2, m3, m4 = st.columns(4)
        total = len(df)
        n_temas = df["tema"].nunique() if "tema" in df.columns else 0
        n_estados = df["estado"].nunique() if "estado" in df.columns else 0
        anos = pd.to_datetime(df["data_edital"], errors="coerce").dt.year.dropna()
        periodo = f"{int(anos.min())}-{int(anos.max())}" if not anos.empty else "-"
        m1.metric("Total de registros", f"{total:,}".replace(",","."))
        m2.metric("Temas", n_temas)
        m3.metric("Estados cobertos", n_estados)
        m4.metric("Período", periodo)

    # ── Tabs ──
    if pode_substituir_base(st.session_state.perfil):
        tab_viz, tab_import, tab_ipca, tab_edital = st.tabs([
            "Visualizar base", "Importar planilha", "Atualizar IPCA", "Incluir edital"
        ])
    else:
        tab_viz, = st.tabs(["Visualizar base"])
        tab_import = tab_ipca = tab_edital = None

    # ── TAB: Visualizar ──
    with tab_viz:
        if df.empty:
            st.warning("A view 'vw_consulta_editais' não foi encontrada ou não possui dados.")
        else:
            col_busca, col_tema = st.columns([2, 1])
            with col_busca:
                busca = st.text_input("Buscar na base", placeholder="Nome, tema, município...",
                                      label_visibility="collapsed")
            with col_tema:
                temas_disp = ["Todos"] + sorted(df["tema"].dropna().unique().tolist()) \
                    if "tema" in df.columns else ["Todos"]
                tema_filtro = st.selectbox("Tema", temas_disp, label_visibility="collapsed")

            df_show = df.copy()
            if busca:
                mask = df_show.apply(lambda r: r.astype(str).str.contains(busca, case=False, na=False).any(), axis=1)
                df_show = df_show[mask]
            if tema_filtro != "Todos" and "tema" in df_show.columns:
                df_show = df_show[df_show["tema"] == tema_filtro]

            st.caption(f"Exibindo {min(500, len(df_show))} de {len(df_show)} registros")
            st.dataframe(df_show.head(500), use_container_width=True, hide_index=True)

    # ── TAB: Importar planilha ──
    if tab_import:
        with tab_import:
            st.markdown("""
            <div style="background:#f0f7ff;border:1px solid #bfdbfe;border-radius:10px;
                        padding:14px 16px;margin-bottom:16px;font-size:0.85rem;color:#1e40af;">
                <strong>Atenção:</strong> O upload <strong>substitui toda a base</strong> de editais/projetos 
                pelos dados da nova planilha. Usuários e solicitações não são afetados.
            </div>
            """, unsafe_allow_html=True)

            arquivo = st.file_uploader("Selecione a planilha (Excel ou CSV)",
                                       type=["xlsx", "xls", "csv"], key="base_upload")
            if arquivo is not None:
                # Preview antes de processar
                try:
                    import pandas as _pd_prev
                    xl = _pd_prev.ExcelFile(arquivo)
                    sheet = "Base" if "Base" in xl.sheet_names else xl.sheet_names[0]
                    df_prev = _pd_prev.read_excel(arquivo, sheet_name=sheet, nrows=5)
                    arquivo.seek(0)
                    n_cols = len(df_prev.columns)
                    st.markdown(f"""
                    <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;
                                padding:12px 16px;margin-bottom:12px;font-size:0.84rem;color:#166534;">
                        <strong>{arquivo.name}</strong> detectado - 
                        aba <em>{sheet}</em>, {n_cols} colunas identificadas.
                    </div>
                    """, unsafe_allow_html=True)
                    with st.expander("Ver primeiras linhas"):
                        st.dataframe(df_prev, use_container_width=True, hide_index=True)
                except Exception:
                    arquivo.seek(0)

                if st.button("Processar e atualizar base", type="primary", use_container_width=True):
                    with st.spinner("Processando planilha e atualizando o banco..."):
                        try:
                            processar_upload_planilha(arquivo)
                            st.success("Base atualizada com sucesso!")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            logger.error("Erro ao processar planilha: %s", e)
                            st.error("Erro ao processar a planilha. Verifique o formato e tente novamente.")

    # ── TAB: IPCA ──
    if tab_ipca:
        with tab_ipca:
            st.markdown("""
            <div style="background:#f0f7ff;border:1px solid #bfdbfe;border-radius:10px;
                        padding:14px 16px;margin-bottom:16px;font-size:0.85rem;color:#1e40af;">
                Faça upload do CSV do IPCA do Banco Central (série SGS 433) para atualizar os custos 
                corrigidos na Base de Prazos e em Projetos Concluídos.<br><br>
                <strong>Download:</strong> 
                <a href="https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?formato=csv" 
                   target="_blank" style="color:#1d4ed8;">
                   api.bcb.gov.br → série 433
                </a>
            </div>
            """, unsafe_allow_html=True)

            # Mostra último mês disponível no banco
            try:
                ipca_atual = carregar_ipca()
                if ipca_atual:
                    ultimo = max(ipca_atual.keys())
                    st.markdown(f"""
                    <div style="display:inline-flex;align-items:center;gap:6px;
                                background:#f0fdf4;border:1px solid #bbf7d0;
                                border-radius:8px;padding:6px 14px;
                                font-size:0.82rem;color:#166534;
                                font-weight:600;margin-bottom:12px;">
                        Última atualização no banco: {ultimo[1]:02d}/{ultimo[0]}
                    </div>
                    """, unsafe_allow_html=True)
            except Exception:
                pass

            arquivo_ipca = st.file_uploader("Selecione o arquivo CSV do IPCA",
                                             type=["csv"], key="ipca_upload")
            if arquivo_ipca is not None:
                if st.button("Importar IPCA", type="primary",
                             use_container_width=True, key="ipca_importar"):
                    with st.spinner("Importando série histórica do IPCA..."):
                        try:
                            import csv, io
                            conteudo = arquivo_ipca.read().decode("utf-8")
                            reader = csv.DictReader(io.StringIO(conteudo), delimiter=";")
                            conn_ipca = get_conn()
                            cur_ipca = conn_ipca.cursor()
                            inseridos = 0
                            for row in reader:
                                data = row.get("data", "").strip()
                                valor = row.get("valor", "").strip().replace(",", ".")
                                if not data or not valor:
                                    continue
                                partes = data.split("/")
                                if len(partes) < 3:
                                    continue
                                mes, ano = int(partes[1]), int(partes[2])
                                try:
                                    variacao = float(valor)
                                except ValueError:
                                    continue
                                cur_ipca.execute("""
                                    INSERT INTO ipca_mensal (ano, mes, variacao)
                                    VALUES (%s, %s, %s)
                                    ON CONFLICT (ano, mes) DO UPDATE SET variacao = EXCLUDED.variacao
                                """, (ano, mes, variacao))
                                inseridos += 1
                            conn_ipca.commit()
                            conn_ipca.close()
                            st.cache_data.clear()
                            st.success(f"IPCA atualizado! {inseridos} meses inseridos/atualizados.")
                        except Exception as e:
                            logger.error("Erro ao importar IPCA: %s", e)
                            st.error("Erro ao importar o IPCA. Verifique o formato do arquivo.")

    # ── TAB: Incluir edital ──
    if tab_edital:
        with tab_edital:
            conn_ref = get_conn()
            try:
                temas_ref   = pd.read_sql_query("SELECT DISTINCT nome FROM tema ORDER BY nome", conn_ref)["nome"].tolist()
                estados_ref = pd.read_sql_query("SELECT DISTINCT nome FROM estado ORDER BY nome", conn_ref)["nome"].tolist()
            except Exception:
                temas_ref, estados_ref = [], []
            finally:
                conn_ref.close()

            with st.form("form_novo_edital", clear_on_submit=True):
                # Identificação
                st.markdown("""
                <div style="font-size:0.72rem;font-weight:700;letter-spacing:0.08em;
                            text-transform:uppercase;color:#64748b;
                            border-bottom:1px solid #e2e8f0;padding-bottom:6px;
                            margin-bottom:12px;">Identificação</div>
                """, unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                with c1:
                    ne_tema = st.selectbox("Tema *", [""] + temas_ref)
                    ne_subtema = st.text_input("Subtema *")
                with c2:
                    ne_nome_edital = st.text_input("Nome do edital *")
                    ne_pais = st.text_input("País", value="Brasil")
                with c3:
                    ne_estado = st.selectbox("Estado", [""] + estados_ref)
                    ne_municipio = st.text_input("Município")

                # Descrição
                st.markdown("""
                <div style="font-size:0.72rem;font-weight:700;letter-spacing:0.08em;
                            text-transform:uppercase;color:#64748b;
                            border-bottom:1px solid #e2e8f0;padding-bottom:6px;
                            margin-bottom:12px;margin-top:8px;">Descrição</div>
                """, unsafe_allow_html=True)
                ne_descricao = st.text_area("Objetivo do edital", height=90)
                ne_servicos  = st.text_input("Serviços (separados por vírgula)")

                # Dados técnicos
                st.markdown("""
                <div style="font-size:0.72rem;font-weight:700;letter-spacing:0.08em;
                            text-transform:uppercase;color:#64748b;
                            border-bottom:1px solid #e2e8f0;padding-bottom:6px;
                            margin-bottom:12px;margin-top:8px;">Dados técnicos</div>
                """, unsafe_allow_html=True)
                d1, d2, d3, d4 = st.columns(4)
                with d1:
                    ne_esforco = st.number_input("Esforço", min_value=0.0, step=0.1, format="%.2f")
                    ne_unidade = st.text_input("Unidade", placeholder="km, m², unid...")
                with d2:
                    ne_prazo = st.number_input("Prazo (meses)", min_value=0.0, step=0.5, format="%.1f")
                    ne_custo = st.number_input("Custo de execução (R$)", min_value=0.0, step=1000.0, format="%.2f")
                with d3:
                    ne_valor_min = st.number_input("Valor mínimo (R$)", min_value=0.0, step=1000.0, format="%.2f")
                    ne_valor_max = st.number_input("Valor máximo (R$)", min_value=0.0, step=1000.0, format="%.2f")
                with d4:
                    ne_data   = st.text_input("Data do edital (AAAA-MM)", placeholder="2024-03")
                    ne_codigo = st.text_input("Código planilha")
                ne_obs = st.text_area("Observações", height=70)

                salvar_edital = st.form_submit_button("Salvar edital", type="primary",
                                                       use_container_width=True)

            if salvar_edital:
                if not ne_tema or not ne_subtema.strip() or not ne_nome_edital.strip():
                    st.warning("Preencha ao menos Tema, Subtema e Nome do edital.")
                else:
                    try:
                        _inserir_edital_individual(
                            tema=ne_tema, subtema=ne_subtema.strip(),
                            pais=ne_pais.strip() or "Brasil",
                            estado=ne_estado or None,
                            municipio=ne_municipio.strip() or None,
                            nome_edital=ne_nome_edital.strip(),
                            descricao=ne_descricao.strip() or None,
                            servicos=ne_servicos.strip() or None,
                            esforco=str(ne_esforco) if ne_esforco > 0 else None,
                            unidade=ne_unidade or None,
                            prazo_meses=ne_prazo if ne_prazo > 0 else None,
                            custo_execucao=ne_custo if ne_custo > 0 else None,
                            valor_min=ne_valor_min if ne_valor_min > 0 else None,
                            valor_max=ne_valor_max if ne_valor_max > 0 else None,
                            data_edital=ne_data.strip() or None,
                            codigo_planilha=ne_codigo.strip() or None,
                            observacao=ne_obs.strip() or None,
                        )
                        st.success(f"Edital '{ne_nome_edital}' incluído com sucesso!")
                        st.cache_data.clear()
                    except Exception as e:
                        logger.error("Erro ao incluir edital: %s", e)
                        st.error("Erro ao salvar o edital. Tente novamente.")

    st.markdown('</div>', unsafe_allow_html=True)



# =========================================================
# MINHA CONTA
# =========================================================
def pagina_minha_conta():
    import html as _html_conta
    header_principal()

    usuario  = st.session_state.usuario
    perfil   = st.session_state.perfil
    email    = st.session_state.email or "-"
    inicial  = usuario[0].upper() if usuario else "U"

    cores_perfil = {
        "ADMIN":       ("#fee2e2", "#991b1b", "#ef4444"),
        "PMO":         ("#dbeafe", "#1e40af", "#3b82f6"),
        "COORDENADOR": ("#fef3c7", "#92400e", "#f59e0b"),
        "GERAL":       ("#f0fdf4", "#166534", "#10b981"),
    }
    bg_p, fg_p, cor_av = cores_perfil.get(perfil, ("#f1f5f9","#475569","#94a3b8"))

    col_perfil, col_senha = st.columns([1, 1], gap="large")

    # ── Card de perfil ──
    with col_perfil:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="display:flex;flex-direction:column;align-items:center;
                    padding:24px 0 16px;text-align:center;">
            <div style="width:72px;height:72px;border-radius:50%;
                        background:linear-gradient(135deg,{cor_av},{cor_av}99);
                        display:flex;align-items:center;justify-content:center;
                        font-size:1.8rem;font-weight:700;color:#fff;
                        box-shadow:0 4px 16px {cor_av}40;margin-bottom:14px;">
                {_html_conta.escape(inicial)}
            </div>
            <div style="font-size:1.15rem;font-weight:700;color:var(--ink-primary);
                        margin-bottom:6px;">
                {_html_conta.escape(usuario)}
            </div>
            <div style="margin-bottom:10px;">
                <span style="background:{bg_p};color:{fg_p};padding:3px 14px;
                             border-radius:999px;font-size:0.75rem;font-weight:700;
                             letter-spacing:0.05em;">
                    {_html_conta.escape(perfil)}
                </span>
            </div>
            <div style="color:var(--ink-secondary);font-size:0.83rem;">
                {_html_conta.escape(email)}
            </div>
        </div>

        <div style="border-top:1px solid var(--border-subtle);padding-top:14px;margin-top:4px;">
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
                <div style="background:var(--surface-2);border-radius:8px;
                            padding:10px 14px;text-align:center;">
                    <div style="font-size:0.65rem;font-weight:600;letter-spacing:0.06em;
                                text-transform:uppercase;color:var(--ink-secondary);
                                margin-bottom:3px;">Acesso</div>
                    <div style="font-size:0.88rem;font-weight:600;color:var(--ink-primary);">
                        {_html_conta.escape(perfil)}
                    </div>
                </div>
                <div style="background:var(--surface-2);border-radius:8px;
                            padding:10px 14px;text-align:center;">
                    <div style="font-size:0.65rem;font-weight:600;letter-spacing:0.06em;
                                text-transform:uppercase;color:var(--ink-secondary);
                                margin-bottom:3px;">Usuário</div>
                    <div style="font-size:0.88rem;font-weight:600;color:var(--ink-primary);
                                word-break:break-all;">
                        {_html_conta.escape(usuario)}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Card de alterar senha ──
    with col_senha:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Alterar senha")
        st.caption("A nova senha deve ter ao menos 8 caracteres, uma maiúscula, uma minúscula e um número.")

        with st.form("form_alterar_senha", clear_on_submit=True):
            senha_atual     = st.text_input("Senha atual", type="password")
            nova_senha      = st.text_input("Nova senha", type="password")
            confirmar_senha = st.text_input("Confirmar nova senha", type="password")

            # Indicador de força visual
            if nova_senha:
                forca = 0
                checks = [
                    (len(nova_senha) >= 8,  "8+ caracteres"),
                    (any(c.isupper() for c in nova_senha), "Maiúscula"),
                    (any(c.islower() for c in nova_senha), "Minúscula"),
                    (any(c.isdigit() for c in nova_senha), "Número"),
                ]
                forca = sum(1 for ok, _ in checks if ok)
                cores_f = ["#ef4444","#f59e0b","#3b82f6","#10b981"]
                labels_f = ["Fraca","Razoável","Boa","Forte"]
                cor_f = cores_f[min(forca-1, 3)] if forca > 0 else "#e2e8f0"
                label_f = labels_f[min(forca-1, 3)] if forca > 0 else ""
                checks_html = "".join([
                    f'<span style="color:{"#10b981" if ok else "#cbd5e1"};'
                    f'font-size:0.75rem;margin-right:8px;">'
                    f'{"✓" if ok else "·"} {txt}</span>'
                    for ok, txt in checks
                ])
                st.markdown(f"""
                <div style="margin:6px 0 10px;">
                    <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
                        <div style="flex:1;height:4px;border-radius:2px;
                                    background:linear-gradient(to right,{cor_f} {forca*25}%,#e2e8f0 {forca*25}%);">
                        </div>
                        <span style="font-size:0.72rem;font-weight:600;color:{cor_f};">{label_f}</span>
                    </div>
                    <div>{checks_html}</div>
                </div>
                """, unsafe_allow_html=True)

            salvar = st.form_submit_button("Salvar nova senha", type="primary",
                                           use_container_width=True)

        if salvar:
            if not senha_atual or not nova_senha or not confirmar_senha:
                st.warning("Preencha todos os campos.")
            elif nova_senha != confirmar_senha:
                st.error("A confirmação da nova senha não confere.")
            else:
                ok_v, msg_v = validar_senha(nova_senha)
                if not ok_v:
                    st.error(msg_v)
                else:
                    ok, msg = alterar_senha_usuario(usuario, senha_atual, nova_senha)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

        st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# USUÁRIOS
# =========================================================
def pagina_usuarios():
    import html as _h_usr
    header_principal()

    if not pode_gerenciar_usuarios(st.session_state.perfil):
        st.error("Acesso restrito ao perfil ADMIN.")
        return

    cores_perfil = {
        "ADMIN":       ("#fee2e2","#991b1b","#ef4444"),
        "PMO":         ("#dbeafe","#1e40af","#3b82f6"),
        "COORDENADOR": ("#fef3c7","#92400e","#f59e0b"),
        "GERAL":       ("#f0fdf4","#166534","#10b981"),
    }

    df_users = listar_usuarios()

    # ── Métricas ──
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    if not df_users.empty:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total de usuários", len(df_users))
        m2.metric("Ativos", int(df_users["ativo"].sum()) if "ativo" in df_users.columns else "-")
        m3.metric("Inativos", int((df_users["ativo"] == 0).sum()) if "ativo" in df_users.columns else "-")
        perfis_unicos = df_users["perfil"].nunique() if "perfil" in df_users.columns else "-"
        m4.metric("Perfis distintos", perfis_unicos)

    # ── Abas ──
    tab_lista, tab_novo = st.tabs(["Usuários cadastrados", "Criar novo usuário"])

    # ── TAB: Lista de usuários como cards ──
    with tab_lista:
        if df_users.empty:
            st.info("Nenhum usuário cadastrado.")
        else:
            # Filtros
            fa, fb = st.columns([2, 1])
            with fa:
                busca_usr = st.text_input("Buscar usuário", placeholder="Nome ou e-mail...",
                                          label_visibility="collapsed")
            with fb:
                filtro_perfil = st.selectbox("Perfil", ["Todos","ADMIN","PMO","COORDENADOR","GERAL"],
                                             label_visibility="collapsed")

            df_view = df_users.copy()
            if busca_usr:
                mask = (df_view["username"].str.contains(busca_usr, case=False, na=False) |
                        df_view.get("email", pd.Series(dtype=str)).str.contains(busca_usr, case=False, na=False))
                df_view = df_view[mask]
            if filtro_perfil != "Todos" and "perfil" in df_view.columns:
                df_view = df_view[df_view["perfil"] == filtro_perfil]

            st.markdown(f'<div style="height:8px;"></div>', unsafe_allow_html=True)

            for _, row in df_view.iterrows():
                uid      = int(row["id"])
                uname    = str(row.get("username",""))
                uemail   = str(row.get("email","") or "-")
                uperfil  = str(row.get("perfil",""))
                uativo   = row.get("ativo", 1)
                inicial  = uname[0].upper() if uname else "U"
                bg_p, fg_p, cor_av = cores_perfil.get(uperfil, ("#f1f5f9","#475569","#94a3b8"))
                status_badge = (
                    '<span style="background:#dcfce7;color:#166534;padding:2px 10px;'
                    'border-radius:999px;font-size:11px;font-weight:600;">Ativo</span>'
                    if uativo else
                    '<span style="background:#f1f5f9;color:#64748b;padding:2px 10px;'
                    'border-radius:999px;font-size:11px;font-weight:600;">Inativo</span>'
                )
                perfil_badge = (
                    f'<span style="background:{bg_p};color:{fg_p};padding:2px 10px;'
                    f'border-radius:999px;font-size:11px;font-weight:600;">{_h_usr.escape(uperfil)}</span>'
                )
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:14px;
                            border:1px solid var(--border-subtle);border-radius:10px;
                            padding:12px 16px;background:var(--surface-1);margin-bottom:6px;">
                    <div style="width:40px;height:40px;border-radius:50%;flex-shrink:0;
                                background:linear-gradient(135deg,{cor_av},{cor_av}88);
                                display:flex;align-items:center;justify-content:center;
                                font-size:1rem;font-weight:700;color:#fff;">
                        {_h_usr.escape(inicial)}
                    </div>
                    <div style="flex:1;min-width:0;">
                        <div style="font-weight:600;font-size:0.9rem;color:var(--ink-primary);">
                            {_h_usr.escape(uname)}
                        </div>
                        <div style="font-size:0.78rem;color:var(--ink-secondary);">
                            {_h_usr.escape(uemail)}
                        </div>
                    </div>
                    <div style="display:flex;gap:6px;align-items:center;">
                        {perfil_badge} {status_badge}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Controles inline
                is_self  = uname.upper() == st.session_state.usuario.upper()
                is_admin = uname.upper() == "ADMIN"
                if not is_self and not is_admin:
                    cc1, cc2, cc3 = st.columns([3, 1, 1])
                    with cc2:
                        novo_status = 0 if uativo else 1
                        label_btn = "Desativar" if uativo else "Ativar"
                        if st.button(label_btn, key=f"ativ_{uid}", use_container_width=True):
                            alterar_status_usuario(uid, novo_status)
                            st.cache_data.clear()
                            st.rerun()
                    with cc3:
                        if st.button("Excluir", key=f"excl_{uid}", use_container_width=True):
                            excluir_usuario(uid)
                            st.cache_data.clear()
                            st.rerun()
                st.markdown('<div style="height:2px;"></div>', unsafe_allow_html=True)

    # ── TAB: Criar usuário ──
    with tab_novo:
        st.caption("Preencha os dados do novo usuário. A senha deve ter ao menos 8 caracteres, uma maiúscula, uma minúscula e um número.")
        with st.form("form_novo_usuario", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                novo_user  = st.text_input("Usuário *", placeholder="nome.sobrenome")
                novo_email = st.text_input("E-mail *", placeholder="email@dominio.com")
            with c2:
                nova_senha = st.text_input("Senha *", type="password")
                perfil_novo = st.selectbox("Perfil *", ["GERAL","COORDENADOR","PMO","ADMIN"])
            criar = st.form_submit_button("Criar usuário", type="primary",
                                          use_container_width=True)

        if criar:
            if not novo_user.strip() or not nova_senha.strip():
                st.warning("Preencha usuário e senha.")
            elif not novo_email.strip():
                st.warning("Preencha o e-mail do usuário.")
            else:
                ok_senha, msg_senha = validar_senha(nova_senha)
                if not ok_senha:
                    st.warning(msg_senha)
                else:
                    try:
                        criar_usuario(novo_user, novo_email, nova_senha, perfil_novo)
                        st.success(f"Usuário '{novo_user}' criado com sucesso.")
                        st.cache_data.clear()
                        st.rerun()
                    except psycopg2.errors.UniqueViolation:
                        st.error("Já existe um usuário com esse nome ou e-mail.")
                    except Exception as e:
                        logger.error("Erro ao criar usuario: %s", e)
                        st.error("Erro ao criar o usuário.")

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Status do e-mail ──
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    smtp_ok = all([SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, EMAIL_FROM])
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:12px;">
        <div style="width:10px;height:10px;border-radius:50%;flex-shrink:0;
                    background:{'#10b981' if smtp_ok else '#f59e0b'};
                    box-shadow:0 0 6px {'#10b981' if smtp_ok else '#f59e0b'}88;">
        </div>
        <div>
            <div style="font-weight:600;font-size:0.88rem;color:var(--ink-primary);">
                E-mail automático - {'Habilitado' if smtp_ok else 'Não configurado'}
            </div>
            <div style="font-size:0.78rem;color:var(--ink-secondary);">
                {'SMTP configurado. Notificações de solicitações estão ativas.' if smtp_ok
                 else 'Defina SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD e EMAIL_FROM nos Secrets.'}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# PROJETOS CONCLUÍDOS
# =========================================================
@st.cache_data(ttl=60, show_spinner=False)
def listar_projetos_concluidos():
    conn = get_conn()
    try:
        df = pd.read_sql_query("""
            SELECT id, nome_projeto, tema, subtema, pais, estado, municipio,
                   data_inicio, data_conclusao, prazo_real_meses,
                   esforco, unidade, esforco2, unidade2,
                   custo_contratado, custo_final, observacoes, criado_por, criado_em
            FROM projetos_concluidos
            ORDER BY data_conclusao DESC NULLS LAST, id DESC
        """, conn)
    except Exception:
        df = pd.DataFrame()
    finally:
        conn.close()
    return df


def processar_upload_projetos_concluidos(arquivo):
    """Lê planilha modelo e insere registros em projetos_concluidos."""
    COLUMN_MAP_PC = {
        "Tema": "tema", "Subtema": "subtema",
        "Objetivo do Projeto": "objetivo", "Descrição": "descricao",
        "País": "pais", "Estado": "estado", "Município": "municipio",
        "Nome Edital/Projeto": "nome_projeto",
        "1º Parâmetro para verificação do prazo": "esforco",
        "Unidade de medida do 1º Parâmetro ": "unidade",
        "Unidade de medida do 1º Parâmetro": "unidade",
        "2º Parâmetro para verificação do prazo": "esforco2",
        "Unidade de medida do 2º Parâmetro ": "unidade2",
        "Unidade de medida do 2º Parâmetro": "unidade2",
        "Prazo de execução\n(meses)": "prazo_meses",
        "Prazo de execução (meses)": "prazo_meses",
        "Custo de Execução": "custo_contratado",
        "Data edital/projeto (mês/ano)": "data_edital",
        "Data de Início do Projeto (Caso concluído)": "data_inicio",
        "Data de Término do Projeto (Caso concluído)": "data_conclusao",
        "Serviços": "servicos",
    }

    xl = pd.ExcelFile(arquivo)
    sheet = "Planilha Modelo" if "Planilha Modelo" in xl.sheet_names else (
            "Base" if "Base" in xl.sheet_names else xl.sheet_names[0])
    df = pd.read_excel(arquivo, sheet_name=sheet)
    df = df.rename(columns=COLUMN_MAP_PC)

    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.strip().replace({"nan": None, "None": None, "": None})

    def limpar_pc(val):
        if val is None:
            return None
        import math
        try:
            if isinstance(val, float) and math.isnan(val):
                return None
        except Exception:
            pass
        s = str(val).strip()
        return None if s in ("", "-", "nan", "None", "NaN", "<NA>") else s

    def safe_float_pc(v):
        if v is None:
            return None
        try:
            import math
            if isinstance(v, float) and math.isnan(v):
                return None
        except Exception:
            pass
        s = str(v).strip().replace(" ", "")
        if s in ("", "-", "nan", "None", "NaN"):
            return None
        if "," in s and "." in s:
            s = s.replace(".", "").replace(",", ".")
        elif "," in s:
            s = s.replace(",", ".")
        try:
            return float(s)
        except Exception:
            return None

    conn = get_conn()
    cur = conn.cursor()
    inseridos = 0

    for _, row in df.iterrows():
        nome = limpar_pc(row.get("nome_projeto"))
        if not nome:
            continue

        data_inicio = limpar_pc(row.get("data_inicio"))
        data_conclusao = limpar_pc(row.get("data_conclusao"))

        prazo_real = None
        if data_inicio and data_conclusao:
            try:
                di = pd.to_datetime(data_inicio, dayfirst=True)
                dc = pd.to_datetime(data_conclusao, dayfirst=True)
                prazo_real = round((dc - di).days / 30.44, 2)
            except Exception:
                prazo_real = safe_float_pc(row.get("prazo_meses"))

        cur.execute("""
            INSERT INTO projetos_concluidos (
                nome_projeto, tema, subtema, pais, estado, municipio,
                descricao, objetivo, servicos, esforco, unidade,
                esforco2, unidade2, data_inicio, data_conclusao,
                prazo_real_meses, custo_contratado, data_edital,
                criado_por, criado_em, atualizado_em
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            nome,
            limpar_pc(row.get("tema")), limpar_pc(row.get("subtema")),
            limpar_pc(row.get("pais")), limpar_pc(row.get("estado")),
            limpar_pc(row.get("municipio")),
            limpar_pc(row.get("descricao") or row.get("objetivo")),
            limpar_pc(row.get("objetivo")),
            limpar_pc(row.get("servicos")),
            limpar_pc(row.get("esforco")), limpar_pc(row.get("unidade")),
            limpar_pc(row.get("esforco2")), limpar_pc(row.get("unidade2")),
            data_inicio, data_conclusao, prazo_real,
            safe_float_pc(row.get("custo_contratado")),
            limpar_pc(row.get("data_edital")),
            "upload", agora_str(), agora_str()
        ))
        inseridos += 1

    conn.commit()
    conn.close()
    return inseridos


def inserir_projeto_concluido(nome, tema, subtema, pais=None, estado=None, municipio=None,
                               data_inicio=None, data_conclusao=None, custo_contratado=None,
                               custo_final=None, observacoes=None, criado_por=None,
                               esforco=None, unidade=None, esforco2=None, unidade2=None):
    from datetime import date
    prazo_real = None
    if data_inicio and data_conclusao:
        try:
            di = data_inicio if isinstance(data_inicio, date) else date.fromisoformat(str(data_inicio))
            dc = data_conclusao if isinstance(data_conclusao, date) else date.fromisoformat(str(data_conclusao))
            delta_dias = (dc - di).days
            prazo_real = round(delta_dias / 30.44, 2)
        except Exception:
            prazo_real = None

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO projetos_concluidos
            (nome_projeto, tema, subtema, pais, estado, municipio,
             data_inicio, data_conclusao, prazo_real_meses,
             custo_contratado, custo_final, observacoes, criado_por, criado_em, atualizado_em,
             esforco, unidade, esforco2, unidade2)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING id
    """, (nome, tema, subtema, pais, estado, municipio,
          str(data_inicio) if data_inicio else None,
          str(data_conclusao) if data_conclusao else None,
          prazo_real, custo_contratado, custo_final,
          observacoes, criado_por, agora_str(), agora_str(),
          esforco or None, unidade or None, esforco2 or None, unidade2 or None))
    proj_id = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return proj_id, prazo_real


def excluir_projeto_concluido(proj_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM projetos_concluidos WHERE id = %s", (proj_id,))
    conn.commit()
    conn.close()


def kerzner_total_para_projeto(subtema: str, esforco) -> dict | None:
    """
    Calcula o prazo TOTAL Kerzner (min e max) para um projeto,
    usando o esforço do projeto e a regressão do subtema (ou tema como fallback).
    Se não houver esforço ou correlação fraca, usa min/max histórico / 0.4.
    Retorna {"total_min": x, "total_max": y} ou None.
    """
    import math

    def _buscar_df(campo, valor):
        if campo not in ("subtema", "tema"):
            raise ValueError(f"Campo não permitido: {campo}")
        conn = get_conn()
        try:
            return pd.read_sql_query(f"""
                SELECT prazo_meses, esforco FROM vw_consulta_editais
                WHERE {campo} = %s
                  AND prazo_meses IS NOT NULL AND prazo_meses > 0
                  AND esforco IS NOT NULL
            """, conn, params=(valor,))
        except Exception:
            return pd.DataFrame()
        finally:
            conn.close()

    # Tenta primeiro como subtema, depois como tema
    df = _buscar_df("subtema", subtema)
    if len(df) < 3:
        df = _buscar_df("tema", subtema)
    if len(df) < 3:
        # Último fallback: busca sem filtro de esforço para ter ao menos o histórico
        conn = get_conn()
        try:
            df = pd.read_sql_query("""
                SELECT prazo_meses, esforco FROM vw_consulta_editais
                WHERE (subtema = %s OR tema = %s)
                  AND prazo_meses IS NOT NULL AND prazo_meses > 0
            """, conn, params=(subtema, subtema))
        except Exception:
            return None
        finally:
            conn.close()

    if len(df) < 3:
        return None

    xs = pd.to_numeric(df["esforco"], errors="coerce").dropna().tolist()
    ys_all = pd.to_numeric(df["prazo_meses"], errors="coerce").dropna().tolist()
    # Align xs and ys to only rows that have both
    df_valid = df.dropna(subset=["esforco"])
    df_valid = df_valid[pd.to_numeric(df_valid["esforco"], errors="coerce").notna()]
    xs = pd.to_numeric(df_valid["esforco"], errors="coerce").tolist()
    ys = pd.to_numeric(df_valid["prazo_meses"], errors="coerce").tolist()

    # Need at least prazos for hist_min/max even without esforco pairs
    if not ys_all:
        return None
    # If xs < 3, can't do regression - use full prazo history for hist bounds
    tem_regressao = len(xs) >= 3

    pearson = calcular_pearson(xs, ys) if tem_regressao else 0.0
    spearman = calcular_spearman(xs, ys) if tem_regressao else 0.0
    max_corr = max(abs(pearson), abs(spearman))
    corr_forte = max_corr >= 0.6 and tem_regressao

    # Tenta converter esforco do projeto
    esforco_val = None
    if esforco is not None:
        try:
            esforco_val = float(str(esforco).replace(",", ".").strip())
        except Exception:
            esforco_val = None

    # Estatísticas históricas de prazo de execução (usa todos os projetos do tema/subtema)
    s_prazos = sorted(ys_all)
    n = len(s_prazos)
    hist_min = s_prazos[0]
    hist_max = s_prazos[-1]
    mean_p = sum(s_prazos) / n
    std_p = math.sqrt(sum((v - mean_p) ** 2 for v in s_prazos) / max(n - 1, 1))

    if corr_forte and esforco_val and esforco_val > 0:
        # Usa regressão para estimar prazo de execução
        if abs(pearson) >= abs(spearman):
            reg = regressao_linear(xs, ys)
        else:
            reg = regressao_logaritmica(xs, ys)

        if reg:
            y_pred = reg["predict"](esforco_val)
            comp = max(0.1, 1 - reg["r2"])
            exec_min = max(0.5, y_pred * (1 - comp))
            exec_max = y_pred * (1 + comp)
        else:
            exec_min, exec_max = hist_min, hist_max
    else:
        exec_min, exec_max = hist_min, hist_max

    # Kerzner: execução = 40% do total
    total_min = round(exec_min / 0.4, 2)
    total_max = round(exec_max / 0.4, 2)
    return {"total_min": total_min, "total_max": total_max,
            "exec_min": exec_min, "exec_max": exec_max,
            "corr_forte": corr_forte, "max_corr": max_corr}


def calcular_estatisticas_subtema(subtema: str):
    """Recalcula min/max/media de prazo_meses da view para o subtema."""
    conn = get_conn()
    try:
        df = pd.read_sql_query("""
            SELECT prazo_meses FROM vw_consulta_editais
            WHERE subtema = %s AND prazo_meses IS NOT NULL AND prazo_meses > 0
        """, conn, params=(subtema,))
    except Exception:
        df = pd.DataFrame()
    finally:
        conn.close()

    if df.empty:
        return None
    vals = df["prazo_meses"].tolist()
    s = sorted(vals)
    n = len(s)
    import math
    mean = sum(s)/n
    q1 = s[max(0, n//4)]
    q3 = s[min(n-1, 3*n//4)]
    iqr = q3 - q1
    return {
        "min": s[0], "max": s[-1], "mean": mean,
        "q1": q1, "q3": q3, "iqr": iqr,
        "lower": q1 - 1.5*iqr, "upper": q3 + 1.5*iqr,
        "n": n
    }


# =========================================================
# IPCA - CORREÇÃO MONETÁRIA
# =========================================================
@st.cache_data(ttl=3600, show_spinner=False)
def carregar_ipca() -> dict:
    """Retorna dict {(ano, mes): variacao_pct} com toda a série histórica."""
    conn = get_conn()
    try:
        df = pd.read_sql_query("SELECT ano, mes, variacao FROM ipca_mensal ORDER BY ano, mes", conn)
    except Exception:
        return {}
    finally:
        conn.close()
    return {(int(r.ano), int(r.mes)): float(r.variacao) for _, r in df.iterrows()}


def corrigir_ipca(valor: float, data_base: str, data_ref: str, ipca: dict) -> float | None:
    """
    Corrige `valor` da data_base até data_ref pelo IPCA.
    data_base e data_ref no formato 'YYYY-MM' ou 'YYYY-MM-DD'.
    Retorna o valor corrigido ou None se não houver dados suficientes.
    """
    if not valor or not data_base or not data_ref or not ipca:
        return None
    try:
        def parse_ym(s):
            partes = str(s).strip().split("-")
            return int(partes[0]), int(partes[1])
        ano_b, mes_b = parse_ym(data_base)
        ano_r, mes_r = parse_ym(data_ref)
    except Exception:
        return None

    # Acumula índice do mês seguinte à data_base até data_ref inclusive
    fator = 1.0
    ano, mes = ano_b, mes_b
    while (ano, mes) <= (ano_r, mes_r):
        if (ano, mes) != (ano_b, mes_b):  # exclui o mês base, inclui o de referência
            v = ipca.get((ano, mes))
            if v is not None:
                fator *= (1 + v / 100)
        mes += 1
        if mes > 12:
            mes = 1
            ano += 1

    return round(valor * fator, 2)


def exportar_projetos_excel(df_tabela: "pd.DataFrame", df_comp: "pd.DataFrame",
                             figs: list, subtema_comp: str,
                             t_min: float, t_max: float, esforco_label: str) -> tuple:
    """Gera Excel com dados + ZIP contendo Excel e HTML com gráficos interativos."""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    from io import BytesIO
    import zipfile

    NAVY = "FF0B1F3A"; BLUE = "FF1A3F6F"; WHITE = "FFFFFFFF"
    LGRAY = "FFF0F4F9"; MGRAY = "FFE8EEF6"; DGRAY = "FF3D5575"

    def hdr(ws, row, col, text, bg=NAVY, fg=WHITE, bold=True, align="center"):
        c = ws.cell(row=row, column=col, value=text)
        c.font = Font(name="Arial", bold=bold, size=10, color=fg)
        c.fill = PatternFill("solid", fgColor=bg)
        c.alignment = Alignment(horizontal=align, vertical="center", wrap_text=True)
        return c

    def val(ws, row, col, value, bold=False, bg=None, align="left", color="FF0D1B2E"):
        c = ws.cell(row=row, column=col, value=value)
        c.font = Font(name="Arial", bold=bold, size=9, color=color)
        if bg: c.fill = PatternFill("solid", fgColor=bg)
        c.alignment = Alignment(horizontal=align, vertical="center", wrap_text=True)
        return c

    def borders(ws, r1, r2, c1, c2):
        s = Side(style="thin", color="FFD8E5F2")
        b = Border(left=s, right=s, top=s, bottom=s)
        for r in range(r1, r2+1):
            for c in range(c1, c2+1):
                ws.cell(r, c).border = b

    wb = openpyxl.Workbook()

    # ── ABA 1: Dados ──────────────────────────────────────
    ws1 = wb.active
    ws1.title = "Projetos Concluídos"
    ws1.sheet_view.showGridLines = False

    # Título
    ws1.merge_cells("A1:L1")
    c = ws1.cell(1, 1, "PROJETOS CONCLUÍDOS")
    c.font = Font(name="Arial", bold=True, size=13, color=WHITE)
    c.fill = PatternFill("solid", fgColor=NAVY)
    c.alignment = Alignment(horizontal="center", vertical="center")
    ws1.row_dimensions[1].height = 30

    from datetime import datetime as _dt
    ws1.merge_cells("A2:L2")
    c2 = ws1.cell(2, 1, f"Gerado em: {_dt.now().strftime('%d/%m/%Y %H:%M')}")
    c2.font = Font(name="Arial", size=9, color=DGRAY)
    c2.fill = PatternFill("solid", fgColor=MGRAY)
    c2.alignment = Alignment(horizontal="center", vertical="center")

    # Headers da tabela
    cols_map = [
        ("nome_projeto", "Projeto", 40),
        ("tema", "Tema", 20),
        ("subtema", "Subtema", 20),
        ("estado", "Estado", 12),
        ("municipio", "Município", 18),
        ("data_inicio", "Início", 12),
        ("data_conclusao", "Conclusão", 12),
        ("esforco", "Esforço", 10),
        ("unidade", "Unidade", 10),
        ("Prazo", "Prazo", 14),
        ("Estimativa Kerzner", "Estimativa Kerzner", 18),
        ("Custo da Execução (R$)", "Custo da Execução (R$)", 20),
        ("Custo final (R$)", "Custo final (R$)", 20),
    ]
    # Only include columns that exist in df_tabela
    cols_disp = [(src, lbl, w) for src, lbl, w in cols_map if src in df_tabela.columns]

    r = 4
    for i, (_, lbl, w) in enumerate(cols_disp, start=1):
        hdr(ws1, r, i, lbl, align="center")
        ws1.column_dimensions[get_column_letter(i)].width = w
    ws1.row_dimensions[r].height = 20
    r += 1

    for idx_row, (_, row) in enumerate(df_tabela.iterrows()):
        bg = LGRAY if idx_row % 2 == 0 else WHITE
        for i, (src, _, _) in enumerate(cols_disp, start=1):
            v = row.get(src, "")
            val(ws1, r, i, v if v is not None and str(v) != "nan" else "", bg=bg,
                align="left" if i == 1 else "center")
        ws1.row_dimensions[r].height = 18
        r += 1
    borders(ws1, 4, r-1, 1, len(cols_disp))

    # ── Gera HTML com gráficos interativos ───────────────
    from datetime import datetime as _dt_html
    titulos_fig = ["Prazo real por projeto", "Evolução do prazo ao longo do tempo", "Custo contratado vs. realizado"]
    html_parts = [f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Gráficos - {subtema_comp}</title>
<style>
  body {{ font-family: Arial, sans-serif; background: #f0f4f9; margin: 0; padding: 24px; }}
  h1 {{ color: #0b1f3a; font-size: 1.4rem; margin-bottom: 4px; }}
  .sub {{ color: #3d5575; font-size: 0.85rem; margin-bottom: 24px; }}
  .card {{ background: #fff; border-radius: 10px; padding: 20px; margin-bottom: 20px;
           box-shadow: 0 2px 8px rgba(11,31,58,.08); }}
  h2 {{ color: #1a3f6f; font-size: 1rem; margin: 0 0 12px; }}
</style>
</head>
<body>
<h1>Projetos Concluídos - {subtema_comp}</h1>
<div class="sub">Estimativa Kerzner: {t_min:.1f}-{t_max:.1f} meses &nbsp;|&nbsp; Esforço: {esforco_label} &nbsp;|&nbsp; Gerado em: {_dt_html.now().strftime('%d/%m/%Y %H:%M')}</div>
"""]
    figs_validos = [f for f in figs if f is not None]
    for i, fig in enumerate(figs_validos):
        try:
            titulo = titulos_fig[i] if i < len(titulos_fig) else f"Gráfico {i+1}"
            fig_html = fig.to_html(full_html=False, include_plotlyjs=(i == 0))
            html_parts.append(f'<div class="card"><h2>{titulo}</h2>{fig_html}</div>')
        except Exception:
            pass
    html_parts.append("</body></html>")
    html_bytes = "\n".join(html_parts).encode("utf-8")

    # ── ABA 3: Estimativa Kerzner ─────────────────────────
    ws3 = wb.create_sheet("Estimativa Kerzner")
    ws3.sheet_view.showGridLines = False
    ws3.column_dimensions["A"].width = 28
    ws3.column_dimensions["B"].width = 22

    ws3.merge_cells("A1:B1")
    c = ws3.cell(1, 1, "ESTIMATIVA KERZNER")
    c.font = Font(name="Arial", bold=True, size=12, color=WHITE)
    c.fill = PatternFill("solid", fgColor=NAVY)
    c.alignment = Alignment(horizontal="center", vertical="center")
    ws3.row_dimensions[1].height = 28

    r = 3
    dados_kz = [
        ("Subtema", subtema_comp),
        ("Esforço utilizado", esforco_label),
        ("Prazo total mínimo (Kerzner)", f"{t_min:.2f} meses"),
        ("Prazo total máximo (Kerzner)", f"{t_max:.2f} meses"),
        ("Planejamento mínimo (50%)", f"{t_min*0.5:.2f} meses"),
        ("Planejamento máximo (50%)", f"{t_max*0.5:.2f} meses"),
        ("Execução mínima (40%)", f"{t_min*0.4:.2f} meses"),
        ("Execução máxima (40%)", f"{t_max*0.4:.2f} meses"),
        ("Encerramento mínimo (10%)", f"{t_min*0.1:.2f} meses"),
        ("Encerramento máximo (10%)", f"{t_max*0.1:.2f} meses"),
    ]
    for i, (label, value) in enumerate(dados_kz):
        bg = LGRAY if i % 2 == 0 else WHITE
        val(ws3, r, 1, label, bold=True, bg=bg, color=DGRAY)
        val(ws3, r, 2, value, bg=bg, align="center")
        r += 1
    borders(ws3, 3, r-1, 1, 2)

    # ── Salva Excel ────────────────────────────────────────
    buf_xlsx = BytesIO()
    wb.save(buf_xlsx)
    buf_xlsx.seek(0)
    xlsx_bytes = buf_xlsx.read()

    # ── Empacota ZIP: Excel + HTML ──────────────────────────
    from datetime import datetime as _dt_zip
    buf_zip = BytesIO()
    with zipfile.ZipFile(buf_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        fname = f"projetos_concluidos_{_dt_zip.now().strftime('%Y-%m-%d')}"
        zf.writestr(f"{fname}.xlsx", xlsx_bytes)
        if html_bytes:
            zf.writestr(f"{fname}_graficos.html", html_bytes)
    buf_zip.seek(0)
    return buf_zip.read(), xlsx_bytes


def pagina_projetos_concluidos():
    try:
        import plotly.graph_objects as go
        import plotly.express as px
        HAS_PLOTLY = True
    except ImportError:
        HAS_PLOTLY = False

    header_principal()

    df_proj = listar_projetos_concluidos()
    is_admin = st.session_state.perfil in ("ADMIN", "PMO")

    # ── Abas principais ──
    if is_admin:
        tab_proj, tab_analise, tab_gerenciar = st.tabs([
            "Projetos", "Análise Kerzner", "Gerenciar"
        ])
    else:
        tab_proj, tab_analise = st.tabs(["Projetos", "Análise Kerzner"])
        tab_gerenciar = None

    # =========================================================
    # ABA: PROJETOS
    # =========================================================
    with tab_proj:
        if df_proj.empty:
            st.info("Nenhum projeto concluído registrado ainda.")
        else:
            # ── Filtros compactos ──
            f1, f2, f3, f4 = st.columns([2, 1, 1, 1])
            with f1:
                busca_proj = st.text_input("Buscar", placeholder="Nome do projeto...",
                                           label_visibility="collapsed")
            with f2:
                temas_f = ["Todos"] + sorted(df_proj["tema"].dropna().unique().tolist())
                tema_f = st.selectbox("Tema", temas_f, key="pc_tema_f",
                                      label_visibility="collapsed")
            with f3:
                df_pf = df_proj[df_proj["tema"] == tema_f] if tema_f != "Todos" else df_proj
                subtemas_f = ["Todos"] + sorted(df_pf["subtema"].dropna().unique().tolist())
                subtema_f = st.selectbox("Subtema", subtemas_f, key="pc_subtema_f",
                                         label_visibility="collapsed")
            with f4:
                estados_f = ["Todos"] + sorted(df_proj["estado"].dropna().unique().tolist())
                estado_f = st.selectbox("Estado", estados_f, key="pc_estado_f",
                                        label_visibility="collapsed")

            df_exib = df_proj.copy()
            if busca_proj.strip():
                df_exib = df_exib[df_exib["nome_projeto"].str.contains(
                    busca_proj.strip(), case=False, na=False)]
            if tema_f != "Todos":
                df_exib = df_exib[df_exib["tema"] == tema_f]
            if subtema_f != "Todos":
                df_exib = df_exib[df_exib["subtema"] == subtema_f]
            if estado_f != "Todos":
                df_exib = df_exib[df_exib["estado"] == estado_f]

            # ── Métricas ──
            prazo_vals = df_exib["prazo_real_meses"].dropna()
            custo_dif  = (df_exib["custo_final"] - df_exib["custo_contratado"]).dropna()
            var_pct    = (custo_dif / df_exib["custo_contratado"].replace(0, None)).dropna() * 100

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Projetos", len(df_exib))
            m2.metric("Prazo médio real",
                      f"{prazo_vals.mean():.1f} m" if not prazo_vals.empty else "-")
            m3.metric("Prazo mín. / máx.",
                      f"{prazo_vals.min():.1f} - {prazo_vals.max():.1f} m"
                      if not prazo_vals.empty else "-")
            if not var_pct.empty:
                mv = var_pct.mean()
                m4.metric("Variação de custo média", f"{mv:+.1f}%",
                          delta=f"{'acima' if mv > 0 else 'abaixo'} do contratado")
            else:
                m4.metric("Variação de custo média", "-")

            # ── IPCA ──
            ipca = carregar_ipca()
            from datetime import datetime as _dt
            data_ref_ipca = f"{_dt.now().year}-{_dt.now().month:02d}"
            tem_ipca = bool(ipca)

            # ── Tabela ──
            df_tabela = df_exib.copy()

            def badge_prazo(row):
                sub    = row.get("subtema")
                prazo  = row.get("prazo_real_meses")
                esforco= row.get("esforco")
                if not sub or pd.isna(prazo):
                    return "-"
                kz = kerzner_total_para_projeto(sub, esforco)
                if not kz:
                    return f"{prazo:.1f} m"
                t_min, t_max = kz["total_min"], kz["total_max"]
                if t_min <= prazo <= t_max:
                    return f"OK {prazo:.1f} m"
                elif prazo < t_min:
                    return f"< {prazo:.1f} m"
                else:
                    return f"> {prazo:.1f} m"

            df_tabela["Prazo"] = df_tabela.apply(badge_prazo, axis=1)
            df_tabela["Estimativa Kerzner"] = df_tabela.apply(
                lambda r: (lambda kz: f"{kz['total_min']:.1f}-{kz['total_max']:.1f} m"
                           if kz else "-")(kerzner_total_para_projeto(
                               r.get("subtema"), r.get("esforco"))), axis=1)

            def custo_corrigido(row):
                if not tem_ipca: return None
                custo  = row.get("custo_contratado")
                data_b = row.get("data_edital") or row.get("data_inicio")
                if pd.isna(custo) or not data_b: return None
                v = corrigir_ipca(float(custo), str(data_b)[:7], data_ref_ipca, ipca)
                return (f"R$ {v:,.2f}".replace(",","X").replace(".",",").replace("X",".")
                        if v else None)

            if tem_ipca:
                df_tabela["Custo da Execução corrigido pelo IPCA"] = df_tabela.apply(custo_corrigido, axis=1)

            def fmt_brl(x):
                if pd.isnull(x) or x == 0: return "-"
                return f"R$ {x:,.2f}".replace(",","X").replace(".",",").replace("X",".")

            for col_c, col_l in [("custo_contratado","Custo da Execução (R$)"),
                                   ("custo_final","Custo final (R$)")]:
                if col_c in df_tabela.columns:
                    df_tabela[col_l] = df_tabela[col_c].apply(fmt_brl)

            for col_dt in ["data_inicio","data_conclusao"]:
                if col_dt in df_tabela.columns:
                    df_tabela[col_dt] = pd.to_datetime(
                        df_tabela[col_dt], errors="coerce").dt.strftime("%d/%m/%Y").fillna("-")

            colunas_exib = ["nome_projeto","tema","subtema","estado","municipio",
                            "data_inicio","data_conclusao","esforco","unidade",
                            "Prazo","Estimativa Kerzner",
                            "Custo da Execução (R$)","Custo final (R$)"]
            if tem_ipca:
                colunas_exib.append("Custo da Execução corrigido pelo IPCA")
            colunas_exib += ["observacoes","criado_por"]

            rename_map = {
                "nome_projeto":"Projeto","tema":"Tema","subtema":"Subtema",
                "estado":"Estado","municipio":"Município",
                "data_inicio":"Início","data_conclusao":"Conclusão",
                "esforco":"Esforço","unidade":"Unidade",
                "observacoes":"Obs.","criado_por":"Registrado por",
            }
            df_show = df_tabela[
                [c for c in colunas_exib if c in df_tabela.columns]
            ].rename(columns=rename_map)
            _col_cfg_proj = {
                "Esforço": st.column_config.TextColumn(
                    "1° Parâmetro",
                    help="Parâmetro utilizado para calculo de execução do projeto."
                ),
                "Unidade": st.column_config.TextColumn(
                    "Unidade",
                    help="Unidade de medida referente ao parâmetro."
                ),
                "esforco2": st.column_config.TextColumn(
                    "2° Parâmetro",
                    help="Parâmetro utilizado para calculo de execução do projeto."
                ),
                "unidade2": st.column_config.TextColumn(
                    "Unidade 2",
                    help="Unidade de medida referente ao 2° parâmetro."
                ),
            }
            if "Custo da Execução corrigido pelo IPCA" in df_show.columns:
                _col_cfg_proj["Custo da Execução corrigido pelo IPCA"] = st.column_config.TextColumn(
                    "Custo da Execução corrigido pelo IPCA",
                    help="Corrige o custo inicial pelo IPCA acumulado desde a data do edital ate o mes atual. Formula: Valor x PI(1 + IPCA_mes/100) para cada mes entre a data base e hoje. Fonte: Banco Central do Brasil, serie SGS 433."
                )
            st.dataframe(df_show, use_container_width=True, hide_index=True,
                         column_config=_col_cfg_proj)

            # Legenda visual
            st.markdown("""
            <div style="display:flex;gap:12px;flex-wrap:wrap;margin:4px 0 8px;">
                <span style="font-size:0.76rem;color:var(--ink-secondary);">
                    <span style="background:#dcfce7;color:#166534;padding:1px 8px;
                                 border-radius:4px;font-weight:600;">OK</span>
                    Dentro do intervalo Kerzner
                </span>
                <span style="font-size:0.76rem;color:var(--ink-secondary);">
                    <span style="background:#dbeafe;color:#1e40af;padding:1px 8px;
                                 border-radius:4px;font-weight:600;">&lt;</span>
                    Abaixo do mínimo
                </span>
                <span style="font-size:0.76rem;color:var(--ink-secondary);">
                    <span style="background:#fee2e2;color:#991b1b;padding:1px 8px;
                                 border-radius:4px;font-weight:600;">&gt;</span>
                    Acima do máximo
                </span>
            </div>
            """, unsafe_allow_html=True)

            # Exportação
            dl1, dl2, _ = st.columns([1, 1, 3])
            with dl1:
                try:
                    buf = __import__("io").BytesIO()
                    df_show.to_excel(buf, index=False, engine="openpyxl")
                    buf.seek(0)
                    from datetime import datetime as _dt2
                    st.download_button("Exportar Excel", data=buf.read(),
                                       file_name=f"projetos_{_dt2.now().strftime('%Y-%m-%d')}.xlsx",
                                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                       use_container_width=True)
                except Exception:
                    pass
            with dl2:
                csv_bytes = df_exib.drop(columns=["id"], errors="ignore").to_csv(
                    index=False).encode("utf-8")
                from datetime import datetime as _dt3
                st.download_button("Exportar CSV", data=csv_bytes,
                                   file_name=f"projetos_{_dt3.now().strftime('%Y-%m-%d')}.csv",
                                   mime="text/csv", use_container_width=True)

    # =========================================================
    # ABA: ANÁLISE KERZNER
    # =========================================================
    with tab_analise:
        if df_proj.empty:
            st.info("Nenhum projeto registrado para análise.")
        else:
            subtemas_comp = sorted(df_proj["subtema"].dropna().unique().tolist())
            if not subtemas_comp:
                st.info("Nenhum projeto com subtema definido.")
            else:
                fa, fb = st.columns([1, 2])
                with fa:
                    subtema_comp = st.selectbox("Subtema", subtemas_comp,
                                                key="pc_subtema_comp")
                df_sub = df_proj[df_proj["subtema"] == subtema_comp].dropna(
                    subset=["prazo_real_meses"])
                with fb:
                    opcoes_proj = df_sub["nome_projeto"].tolist()
                    proj_sel = st.multiselect("Projetos para análise", opcoes_proj,
                                              default=opcoes_proj, key="pc_proj_sel")

                if not proj_sel:
                    st.info("Selecione ao menos um projeto.")
                else:
                    df_comp = df_sub[df_sub["nome_projeto"].isin(proj_sel)].copy()

                    esforcos_sel = pd.to_numeric(df_comp["esforco"], errors="coerce").dropna()
                    if not esforcos_sel.empty:
                        media_esforco = esforcos_sel.mean()
                        kz = kerzner_total_para_projeto(subtema_comp, media_esforco)
                        unid = (df_comp["unidade"].dropna().iloc[0]
                                if not df_comp["unidade"].dropna().empty else "")
                        esforco_label = f"média {media_esforco:.1f} {unid}".strip()
                    else:
                        kz = kerzner_total_para_projeto(subtema_comp, None)
                        esforco_label = "sem esforço - usando histórico"

                    if not kz:
                        st.info("Dados insuficientes para calcular Kerzner neste subtema.")
                    else:
                        t_min  = kz["total_min"]
                        t_max  = kz["total_max"]
                        t_medio= (t_min + t_max) / 2
                        prazo_real_medio = df_comp["prazo_real_meses"].mean()
                        dentro = df_comp[(df_comp["prazo_real_meses"] >= t_min) &
                                         (df_comp["prazo_real_meses"] <= t_max)]

                        # Métricas Kerzner
                        ce1, ce2, ce3, ce4 = st.columns(4)
                        ce1.metric("Kerzner mínimo", f"{t_min:.1f} m")
                        ce2.metric("Kerzner máximo", f"{t_max:.1f} m")
                        ce3.metric("Prazo real médio", f"{prazo_real_medio:.1f} m",
                                   delta=f"{prazo_real_medio - t_medio:+.1f} m vs. Kerzner")
                        ce4.metric("Dentro do intervalo", f"{len(dentro)}/{len(df_comp)}")

                        # Info card
                        metodo = "Regressão estatística" if kz.get("corr_forte") else "Mín/máx histórico"
                        st.markdown(f"""
                        <div style="background:var(--surface-2);border:1px solid var(--border-subtle);
                                    border-radius:10px;padding:12px 16px;font-size:0.82rem;
                                    color:var(--ink-secondary);margin-bottom:12px;">
                            <strong>Subtema:</strong> {subtema_comp} &nbsp;·&nbsp;
                            <strong>Esforço:</strong> {esforco_label} &nbsp;·&nbsp;
                            <strong>Método:</strong> {metodo}
                        </div>
                        """, unsafe_allow_html=True)

                        if HAS_PLOTLY:
                            projetos_nomes = df_comp["nome_projeto"].tolist()
                            prazos_reais   = df_comp["prazo_real_meses"].tolist()

                            # Gráfico 1: Barras
                            fig1 = go.Figure()
                            fig1.add_trace(go.Bar(
                                x=projetos_nomes, y=prazos_reais, name="Prazo real",
                                marker_color=["#10b981" if t_min<=p<=t_max else "#ef4444"
                                              for p in prazos_reais],
                                hovertemplate="<b>%{x}</b><br>Prazo real: %{y:.1f} m<extra></extra>"
                            ))
                            for y_val, dash, cor, label in [
                                (t_min,   "dash", "#3b82f6", f"Kerzner mín.: {t_min:.1f}m"),
                                (t_max,   "dash", "#f59e0b", f"Kerzner máx.: {t_max:.1f}m"),
                                (t_medio, "dot",  "#8b5cf6", f"Kerzner médio: {t_medio:.1f}m"),
                            ]:
                                fig1.add_hline(y=y_val, line_dash=dash, line_color=cor,
                                               annotation_text=label,
                                               annotation_position="top right")
                            fig1.update_layout(
                                title=f"Prazo real por projeto - {subtema_comp}",
                                xaxis_title="Projeto", yaxis_title="Meses",
                                height=380, template="plotly_white", showlegend=False)
                            st.plotly_chart(fig1, use_container_width=True)
                            _figs_export = [fig1]

                            # Gráfico 2: Temporal
                            df_comp_ord = df_comp.sort_values("data_conclusao")
                            if not df_comp_ord["data_conclusao"].isna().all():
                                fig2 = go.Figure()
                                fig2.add_trace(go.Scatter(
                                    x=df_comp_ord["data_conclusao"].astype(str).tolist(),
                                    y=df_comp_ord["prazo_real_meses"].tolist(),
                                    mode="markers+lines",
                                    marker=dict(size=10, color="#2563eb"),
                                    line=dict(color="#93c5fd", width=1, dash="dot"),
                                    text=df_comp_ord["nome_projeto"].tolist(),
                                    hovertemplate="<b>%{text}</b><br>Conclusão: %{x}<br>Prazo: %{y:.1f} m<extra></extra>",
                                    name="Prazo real"
                                ))
                                fig2.add_hrect(y0=t_min, y1=t_max, fillcolor="#3b82f6",
                                               opacity=0.08,
                                               annotation_text=f"Intervalo Kerzner ({t_min:.1f}-{t_max:.1f}m)",
                                               annotation_position="top right")
                                fig2.update_layout(
                                    title="Evolução do prazo ao longo do tempo",
                                    xaxis_title="Data de conclusão", yaxis_title="Meses",
                                    height=320, template="plotly_white")
                                st.plotly_chart(fig2, use_container_width=True)
                                _figs_export.append(fig2)
                            else:
                                _figs_export.append(None)

                            # Gráfico 3: Custo
                            df_custo = df_comp.dropna(subset=["custo_contratado","custo_final"])
                            if not df_custo.empty:
                                fig3 = go.Figure()
                                fig3.add_trace(go.Bar(name="Contratado",
                                    x=df_custo["nome_projeto"].tolist(),
                                    y=df_custo["custo_contratado"].tolist(),
                                    marker_color="#3b82f6"))
                                fig3.add_trace(go.Bar(name="Realizado",
                                    x=df_custo["nome_projeto"].tolist(),
                                    y=df_custo["custo_final"].tolist(),
                                    marker_color="#ef4444"))
                                fig3.update_layout(
                                    title="Custo contratado vs. realizado",
                                    xaxis_title="Projeto", yaxis_title="R$",
                                    barmode="group", height=340, template="plotly_white")
                                st.plotly_chart(fig3, use_container_width=True)
                                _figs_export.append(fig3)
                            else:
                                _figs_export.append(None)

                            # Exportação ZIP
                            st.markdown("---")
                            from datetime import datetime as _dt_exp
                            try:
                                zip_bytes, xlsx_only = exportar_projetos_excel(
                                    df_tabela=df_show if 'df_show' in dir() else df_comp,
                                    df_comp=df_comp, figs=_figs_export,
                                    subtema_comp=subtema_comp,
                                    t_min=t_min, t_max=t_max,
                                    esforco_label=esforco_label)
                                ex1, ex2 = st.columns(2)
                                with ex1:
                                    st.download_button(
                                        "Exportar Excel + Gráficos (ZIP)", data=zip_bytes,
                                        file_name=f"analise_kerzner_{_dt_exp.now().strftime('%Y-%m-%d')}.zip",
                                        mime="application/zip", use_container_width=True)
                                with ex2:
                                    st.download_button(
                                        "Exportar Excel (somente dados)", data=xlsx_only,
                                        file_name=f"analise_kerzner_{_dt_exp.now().strftime('%Y-%m-%d')}.xlsx",
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        use_container_width=True)
                            except Exception as _ex:
                                logger.error("Erro ao exportar: %s", _ex)

    # =========================================================
    # ABA: GERENCIAR (ADMIN / PMO)
    # =========================================================
    if tab_gerenciar:
        with tab_gerenciar:
            sub_import, sub_manual, sub_excluir = st.tabs([
                "Importar planilha", "Cadastrar manualmente", "Excluir projeto"
            ])

            # ── Sub-aba: Importar ──
            with sub_import:
                st.caption("Envie a Planilha Modelo preenchida pelas áreas para importar em lote.")
                arquivo_pc = st.file_uploader("Selecione a planilha",
                                              type=["xlsx","xls"], key="pc_upload")
                if arquivo_pc is not None:
                    st.success(f"Arquivo carregado: {arquivo_pc.name}")
                    if st.button("Importar projetos", type="primary",
                                 key="pc_importar", use_container_width=True):
                        with st.spinner("Importando projetos..."):
                            try:
                                n = processar_upload_projetos_concluidos(arquivo_pc)
                                st.success(f"{n} projeto(s) importado(s) com sucesso!")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                logger.error("Erro ao importar projetos: %s", e)
                                st.error("Erro ao importar. Verifique o formato e tente novamente.")

            # ── Sub-aba: Cadastrar manualmente ──
            with sub_manual:
                conn_view = get_conn()
                try:
                    df_temas = pd.read_sql_query(
                        "SELECT DISTINCT tema, subtema FROM vw_consulta_editais "
                        "WHERE tema IS NOT NULL ORDER BY tema, subtema", conn_view)
                except Exception:
                    df_temas = pd.DataFrame(columns=["tema","subtema"])
                finally:
                    conn_view.close()

                temas_disp = sorted(df_temas["tema"].dropna().unique().tolist())
                pc1, pc2 = st.columns(2)
                with pc1:
                    tema_proj = st.selectbox("Tema", [""]+temas_disp, key="pc_form_tema")
                with pc2:
                    subtemas_disp = (sorted(df_temas[df_temas["tema"]==tema_proj]
                                     ["subtema"].dropna().unique().tolist())
                                     if tema_proj else [])
                    subtema_proj = st.selectbox("Subtema", [""]+subtemas_disp,
                                                key="pc_form_subtema")

                with st.form("form_proj_concluido", clear_on_submit=True):
                    st.markdown("""
                    <div style="font-size:0.72rem;font-weight:700;letter-spacing:0.08em;
                                text-transform:uppercase;color:#64748b;
                                border-bottom:1px solid #e2e8f0;padding-bottom:6px;
                                margin-bottom:12px;">Identificação</div>
                    """, unsafe_allow_html=True)
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        nome_proj = st.text_input("Nome do projeto *")
                        pais_proj = st.text_input("País", value="Brasil")
                    with c2:
                        estado_proj    = st.text_input("Estado")
                        municipio_proj = st.text_input("Município")
                    with c3:
                        data_inicio_proj    = st.date_input("Data de início",
                                                             value=None, format="DD/MM/YYYY")
                        data_conclusao_proj = st.date_input("Data de conclusão",
                                                             value=None, format="DD/MM/YYYY")

                    st.markdown("""
                    <div style="font-size:0.72rem;font-weight:700;letter-spacing:0.08em;
                                text-transform:uppercase;color:#64748b;
                                border-bottom:1px solid #e2e8f0;padding-bottom:6px;
                                margin-bottom:12px;margin-top:8px;">Parâmetros</div>
                    """, unsafe_allow_html=True)
                    p1, p2, p3, p4 = st.columns(4)
                    with p1:
                        esforco_proj  = st.text_input("1º Parâmetro")
                    with p2:
                        unidade_proj  = st.text_input("Unidade", placeholder="km, m², unid...")
                    with p3:
                        esforco2_proj = st.text_input("2º Parâmetro")
                    with p4:
                        unidade2_proj = st.text_input("Unidade 2", placeholder="km, m², unid...")

                    st.markdown("""
                    <div style="font-size:0.72rem;font-weight:700;letter-spacing:0.08em;
                                text-transform:uppercase;color:#64748b;
                                border-bottom:1px solid #e2e8f0;padding-bottom:6px;
                                margin-bottom:12px;margin-top:8px;">Custos</div>
                    """, unsafe_allow_html=True)
                    cc1, cc2 = st.columns(2)
                    with cc1:
                        custo_contratado_proj = st.number_input(
                            "Custo da Execução (R$)", min_value=0.0, step=1000.0, format="%.2f")
                    with cc2:
                        custo_final_proj = st.number_input(
                            "Custo final realizado (R$)", min_value=0.0, step=1000.0, format="%.2f")
                    obs_proj = st.text_area("Observações", height=70)
                    salvar   = st.form_submit_button("Salvar projeto", type="primary",
                                                     use_container_width=True)

                if salvar:
                    if not nome_proj.strip():
                        st.warning("Informe o nome do projeto.")
                    else:
                        proj_id, prazo_real = inserir_projeto_concluido(
                            nome=nome_proj.strip(), tema=tema_proj or None,
                            subtema=subtema_proj or None,
                            pais=pais_proj.strip() or None,
                            estado=estado_proj or None,
                            municipio=municipio_proj or None,
                            data_inicio=data_inicio_proj,
                            data_conclusao=data_conclusao_proj,
                            custo_contratado=custo_contratado_proj or None,
                            custo_final=custo_final_proj or None,
                            observacoes=obs_proj or None,
                            criado_por=st.session_state.usuario,
                            esforco=esforco_proj.strip() or None,
                            unidade=unidade_proj.strip() or None,
                            esforco2=esforco2_proj.strip() or None,
                            unidade2=unidade2_proj.strip() or None,
                        )
                        prazo_msg = (f" Prazo real: **{prazo_real:.1f} meses**."
                                     if prazo_real else "")
                        st.success(f"Projeto registrado!{prazo_msg}")
                        st.cache_data.clear()
                        st.rerun()

            # ── Sub-aba: Excluir ──
            with sub_excluir:
                if df_proj.empty:
                    st.info("Nenhum projeto cadastrado.")
                else:
                    proj_id_del = st.selectbox(
                        "Selecione o projeto a excluir",
                        df_proj["id"].tolist(),
                        format_func=lambda x: (
                            f"{x} - "
                            f"{df_proj.loc[df_proj['id']==x,'nome_projeto'].values[0]}"
                        )
                    )
                    nome_del = df_proj.loc[
                        df_proj["id"]==proj_id_del, "nome_projeto"].values[0]
                    st.markdown(f"""
                    <div style="background:#fff5f5;border:1px solid #fecaca;
                                border-radius:10px;padding:14px 16px;margin:12px 0;">
                        <div style="font-weight:600;color:#991b1b;margin-bottom:4px;">
                            Atenção - ação irreversível
                        </div>
                        <div style="color:#7f1d1d;font-size:0.85rem;">
                            O projeto <strong>{nome_del}</strong> será excluído permanentemente.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    confirmar = st.checkbox("Confirmo que desejo excluir este projeto")
                    if st.button("Excluir projeto", type="primary",
                                 disabled=not confirmar, use_container_width=False):
                        excluir_projeto_concluido(proj_id_del)
                        st.cache_data.clear()
                        st.success("Projeto excluído.")
                        st.rerun()



# =========================================================
# ANÁLISE DE PRAZOS
# =========================================================
def exportar_analise_excel(data: dict) -> bytes:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    from io import BytesIO
    import math

    NAVY="FF0B1F3A"; BLUE="FF1A3F6F"; MID="FF1E5799"; ACCENT="FF1D6FC4"
    WHITE="FFFFFFFF"; LGRAY="FFF0F4F9"; MGRAY="FFE8EEF6"; DGRAY="FF3D5575"

    def hdr(ws,row,col,text,fg=WHITE,bg=NAVY,bold=True,size=10,merge_to=None,align="left"):
        c=ws.cell(row=row,column=col,value=text)
        c.font=Font(name="Arial",bold=bold,size=size,color=fg)
        c.fill=PatternFill("solid",fgColor=bg)
        c.alignment=Alignment(horizontal=align,vertical="center",wrap_text=True)
        if merge_to: ws.merge_cells(start_row=row,start_column=col,end_row=merge_to[0],end_column=merge_to[1])
        return c

    def val(ws,row,col,value,bold=False,size=10,color="FF0D1B2E",bg=None,align="left"):
        c=ws.cell(row=row,column=col,value=value)
        c.font=Font(name="Arial",bold=bold,size=size,color=color)
        if bg: c.fill=PatternFill("solid",fgColor=bg)
        c.alignment=Alignment(horizontal=align,vertical="center",wrap_text=True)
        return c

    def sec(ws,row,col,text,cols=2):
        ws.merge_cells(start_row=row,start_column=col,end_row=row,end_column=col+cols-1)
        c=ws.cell(row=row,column=col,value=text)
        c.font=Font(name="Arial",bold=True,size=10,color=WHITE)
        c.fill=PatternFill("solid",fgColor=BLUE)
        c.alignment=Alignment(horizontal="left",vertical="center")
        ws.row_dimensions[row].height=18
        return c

    def borders(ws,r1,r2,c1,c2):
        s=Side(style="thin",color="FFD8E5F2")
        b=Border(left=s,right=s,top=s,bottom=s)
        for r in range(r1,r2+1):
            for c in range(c1,c2+1):
                ws.cell(r,c).border=b

    def cols_w(ws,d):
        for c,w in d.items(): ws.column_dimensions[get_column_letter(c)].width=w

    wb=openpyxl.Workbook()

    #  ABA 1: Resumo
    ws1=wb.active; ws1.title="Resumo da Análise"
    ws1.sheet_view.showGridLines=False
    cols_w(ws1,{1:34,2:30})

    ws1.merge_cells("A1:B1")
    c=ws1.cell(1,1,"RELATÓRIO DE ANÁLISE DE PROJETOS")
    c.font=Font(name="Arial",bold=True,size=14,color=WHITE)
    c.fill=PatternFill("solid",fgColor=NAVY)
    c.alignment=Alignment(horizontal="center",vertical="center")
    ws1.row_dimensions[1].height=36

    from datetime import datetime
    ws1.merge_cells("A2:B2")
    c2=ws1.cell(2,1,f"Gerado em: {datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}")
    c2.font=Font(name="Arial",size=9,color=DGRAY)
    c2.fill=PatternFill("solid",fgColor=MGRAY)
    c2.alignment=Alignment(horizontal="center",vertical="center")

    r=4
    sec(ws1,r,1,"PARÂMETROS DA ANÁLISE",2); r+=1
    for label,value in [
        ("Tema",data.get("tema","")),("Subtema",data.get("subtema","")),
        ("País",data.get("pais_sel","Todos")),("Estado",data.get("estado_sel","Todos")),
        ("Tema SAN","Sim" if data.get("is_san") else "Não"),
    ]:
        val(ws1,r,1,label,bold=True,color=DGRAY,bg=LGRAY); val(ws1,r,2,value); r+=1
    borders(ws1,5,r-1,1,2)

    pearson=data.get("pearson",0); spearman=data.get("spearman",0)
    corr_forte=data.get("corr_forte",False); reg=data.get("reg"); reg_label=data.get("reg_label","")

    def forca(v):
        a=abs(v)
        if a>=0.7: return "Forte"
        if a>=0.6: return "Moderada"
        if a>=0.3: return "Fraca"
        return "Muito fraca"

    r+=1; sec(ws1,r,1,"CORRELAÇÃO",2); r+=1
    for label,value in [
        ("Pearson (Linear)",f"{pearson:.4f}"),("Spearman (Não-linear)",f"{spearman:.4f}"),
        ("Correlação Dominante","Logarítmica (Spearman)" if abs(spearman)>abs(pearson) else "Linear (Pearson)"),
        ("Status da Correlação",f"{'FORTE (≥ 0,6) - usando regressão' if corr_forte else 'FRACA (< 0,6) - usando histórico'}"),
        ("Tipo de Regressão Utilizado",data.get("reg_type_display","Automático")),
    ]:
        val(ws1,r,1,label,bold=True,color=DGRAY,bg=LGRAY); val(ws1,r,2,value); r+=1
    borders(ws1,r-5,r-1,1,2)

    if reg:
        r+=1; sec(ws1,r,1,"REGRESSÃO",2); r+=1
        for label,value in [
            ("Tipo",reg.get("type","").capitalize()),("Equação",reg.get("eq","")),
            ("R²",f"{reg.get('r2',0):.4f}"),("1 - R²",f"{1-reg.get('r2',0):.4f}"),
            ("Coeficiente a",f"{reg.get('a',0):.4f}"),("Coeficiente b",f"{reg.get('b',0):.4f}"),
        ]:
            val(ws1,r,1,label,bold=True,color=DGRAY,bg=LGRAY); val(ws1,r,2,value); r+=1
        borders(ws1,r-6,r-1,1,2)

    st_p=data.get("st_prazos",{})
    r+=1; sec(ws1,r,1,"INTERVALO HISTÓRICO OBSERVADO",2); r+=1
    val(ws1,r,1,"Prazo Mínimo Histórico (meses)",bold=True,color=DGRAY,bg=LGRAY)
    val(ws1,r,2,f"{st_p.get('min',0):.2f}"); r+=1
    val(ws1,r,1,"Prazo Máximo Histórico (meses)",bold=True,color=DGRAY,bg=LGRAY)
    val(ws1,r,2,f"{st_p.get('max',0):.2f}"); r+=1
    borders(ws1,r-2,r-1,1,2)

    alerts=data.get("alerts",[])
    if alerts:
        r+=1
        ws1.merge_cells(start_row=r,start_column=1,end_row=r,end_column=2)
        c=ws1.cell(r,1," ALERTA: ESTIMATIVA FORA DO INTERVALO HISTÓRICO")
        c.font=Font(name="Arial",bold=True,size=10,color=WHITE)
        c.fill=PatternFill("solid",fgColor="FFDC2626")
        c.alignment=Alignment(horizontal="left",vertical="center")
        ws1.row_dimensions[r].height=18; r+=1
        for a in alerts:
            ws1.merge_cells(start_row=r,start_column=1,end_row=r,end_column=2)
            c=ws1.cell(r,1,a)
            c.font=Font(name="Arial",size=9,color="FFDC2626")
            c.fill=PatternFill("solid",fgColor="FFFFF1F1")
            c.alignment=Alignment(wrap_text=True); r+=1

    #  ABA 2: Cronograma
    ws2=wb.create_sheet("Cronograma Kerzner")
    ws2.sheet_view.showGridLines=False
    cols_w(ws2,{1:30,2:22,3:22,4:22})
    ws2.merge_cells("A1:D1")
    c=ws2.cell(1,1,"CRONOGRAMA KERZNER (2009)")
    c.font=Font(name="Arial",bold=True,size=13,color=WHITE)
    c.fill=PatternFill("solid",fgColor=NAVY)
    c.alignment=Alignment(horizontal="center",vertical="center")
    ws2.row_dimensions[1].height=32

    r=3; kr=data.get("kerzner",{})
    enc_desc="10% da execução (SAN)" if data.get("is_san") else "10% do total (mín. 1 mês)"
    for label,value in [
        ("Metodologia","Kerzner (2009)"),("Encerramento",enc_desc),
        ("Método de Cálculo",f"Regressão ({reg_label})" if corr_forte else "Valores históricos"),
        ("Equação utilizada",reg.get("eq","-") if reg else "-"),
        ("R²",f"{reg.get('r2',0):.4f}" if reg else "-"),
    ]:
        val(ws2,r,1,label,bold=True,color=DGRAY,bg=LGRAY)
        ws2.merge_cells(start_row=r,start_column=2,end_row=r,end_column=4)
        val(ws2,r,2,value); r+=1
    borders(ws2,3,r-1,1,4)

    r+=1
    for i,h in enumerate(["FASE","PERCENTUAL","CENÁRIO MÍNIMO (meses)","CENÁRIO MÁXIMO (meses)"]):
        hdr(ws2,r,i+1,h,bg=NAVY,align="center")
    ws2.row_dimensions[r].height=20; r+=1

    total_min=kr.get("total_min",0); total_max=kr.get("total_max",0)
    for i,(fase,pct,vmin,vmax) in enumerate([
        ("Planejamento","50% do total",kr.get("plan_min",0),kr.get("plan_max",0)),
        ("Execução","40% do total",kr.get("exec_min",0),kr.get("exec_max",0)),
        ("Encerramento",enc_desc,kr.get("enc_min",0),kr.get("enc_max",0)),
        ("TOTAL DO PROJETO","100%",total_min,total_max),
    ]):
        bg=LGRAY if i%2==0 else WHITE
        bold=fase=="TOTAL DO PROJETO"
        if bold: bg=MGRAY
        val(ws2,r,1,fase,bold=bold,bg=bg)
        val(ws2,r,2,pct,align="center",bg=bg)
        val(ws2,r,3,f"{vmin:.4f}",align="center",bg=bg,bold=bold)
        val(ws2,r,4,f"{vmax:.4f}",align="center",bg=bg,bold=bold); r+=1
    borders(ws2,r-4,r-1,1,4)

    r+=1
    ws2.merge_cells(start_row=r,start_column=1,end_row=r,end_column=4)
    c=ws2.cell(r,1,"DETALHAMENTO DO PLANEJAMENTO (Kerzner)")
    c.font=Font(name="Arial",bold=True,size=10,color=WHITE)
    c.fill=PatternFill("solid",fgColor=MID)
    c.alignment=Alignment(horizontal="left",vertical="center")
    ws2.row_dimensions[r].height=18; r+=1
    for i,h in enumerate(["Sub-fase","Percentual do Total","Cenário Mínimo (meses)","Cenário Máximo (meses)"]):
        hdr(ws2,r,i+1,h,bg=MID,align="center")
    ws2.row_dimensions[r].height=18; r+=1
    for i,(nome,pct) in enumerate([("Conceitualização",0.05),("Estudo de Viabilidade",0.10),
                                    ("Planejamento Preliminar",0.15),("Planejamento Detalhado",0.20)]):
        bg=LGRAY if i%2==0 else WHITE
        val(ws2,r,1,nome,bg=bg)
        val(ws2,r,2,f"{int(pct*100)}%",align="center",bg=bg)
        val(ws2,r,3,f"{total_min*pct:.4f}",align="center",bg=bg)
        val(ws2,r,4,f"{total_max*pct:.4f}",align="center",bg=bg); r+=1
    borders(ws2,r-4,r-1,1,4)

    #  ABA 3: Estatísticas
    ws3=wb.create_sheet("Estatísticas")
    ws3.sheet_view.showGridLines=False
    cols_w(ws3,{1:28,2:18,3:18})
    ws3.merge_cells("A1:C1")
    c=ws3.cell(1,1,"ESTATÍSTICAS DA ANÁLISE")
    c.font=Font(name="Arial",bold=True,size=13,color=WHITE)
    c.fill=PatternFill("solid",fgColor=NAVY)
    c.alignment=Alignment(horizontal="center",vertical="center")
    ws3.row_dimensions[1].height=32

    r=3
    for i,h in enumerate(["INDICADOR","ESFORÇO","PRAZO (meses)"]):
        hdr(ws3,r,i+1,h,bg=NAVY,align="center")
    ws3.row_dimensions[r].height=20; r+=1

    st_e=data.get("st_esforcos",{})
    for i,(label,key) in enumerate([
        ("Média","mean"),("Mediana","median"),("Desvio Padrão","std"),
        ("1º Quartil (Q1)","q1"),("3º Quartil (Q3)","q3"),("IQR (Q3 - Q1)","iqr"),
        ("Limite Inferior","lower"),("Limite Superior","upper"),
    ]):
        bg=LGRAY if i%2==0 else WHITE
        val(ws3,r,1,label,bold=True,color=DGRAY,bg=bg)
        val(ws3,r,2,f"{st_e.get(key,0):.2f}",align="center",bg=bg)
        val(ws3,r,3,f"{st_p.get(key,0):.2f}",align="center",bg=bg); r+=1
    borders(ws3,4,r-1,1,3)

    r+=1
    for i,h in enumerate(["CORRELAÇÃO","VALOR","FORÇA"]):
        hdr(ws3,r,i+1,h,bg=NAVY,align="center")
    ws3.row_dimensions[r].height=20; r+=1
    val(ws3,r,1,"Pearson (Linear)",bold=True,color=DGRAY,bg=LGRAY)
    val(ws3,r,2,f"{pearson:.4f}",align="center",bg=LGRAY)
    val(ws3,r,3,forca(pearson),align="center",bg=LGRAY); r+=1
    val(ws3,r,1,"Spearman (Não-linear)",bold=True,color=DGRAY)
    val(ws3,r,2,f"{spearman:.4f}",align="center")
    val(ws3,r,3,forca(spearman),align="center"); r+=1
    borders(ws3,r-2,r-1,1,3)

    #  ABA 4: Projetos
    ws4=wb.create_sheet("Projetos")
    ws4.sheet_view.showGridLines=False
    cols_w(ws4,{1:55,2:10,3:16,4:12,5:12,6:14,7:14,8:16})
    ws4.merge_cells("A1:H1")
    c=ws4.cell(1,1,"DETALHAMENTO DOS PROJETOS")
    c.font=Font(name="Arial",bold=True,size=13,color=WHITE)
    c.fill=PatternFill("solid",fgColor=NAVY)
    c.alignment=Alignment(horizontal="center",vertical="center")
    ws4.row_dimensions[1].height=32

    r=3
    for i,h in enumerate(["Nome","País","Estado","Tipo","Esforço","Duração (meses)","Classificação","Status na Análise"]):
        hdr(ws4,r,i+1,h,bg=NAVY,align="center")
    ws4.row_dimensions[r].height=20; r+=1

    projetos=data.get("projetos",[])
    for i,p in enumerate(projetos):
        bg=LGRAY if i%2==0 else WHITE
        classif=p.get("Classificação","Normal")
        if classif=="Outlier Alto": bg="FFFFF1F1"
        elif classif=="Outlier Baixo": bg="FFF0F9FF"
        status="Excluído" if p.get("_excluido") else "Incluído"
        for j,v in enumerate([
            p.get("nome_edital",""),p.get("pais",""),p.get("estado",""),
            "Esforço",p.get("esforco",""),p.get("prazo_meses",""),classif,status
        ]):
            val(ws4,r,j+1,v,bg=bg,align="left" if j==0 else "center")
        ws4.row_dimensions[r].height=40; r+=1
    borders(ws4,4,r-1,1,8)

    r+=1
    total=len(projetos); analisados=len([p for p in projetos if not p.get("_excluido")])
    ws4.cell(r,4,f"Total: {total} projetos").font=Font(name="Arial",bold=True,size=9)
    ws4.cell(r,5,f"Analisados: {analisados}").font=Font(name="Arial",bold=True,size=9)
    ws4.cell(r,6,f"Excluídos: {total-analisados}").font=Font(name="Arial",bold=True,size=9)

    buf=BytesIO(); wb.save(buf); buf.seek(0)
    return buf.read()


def calcular_pearson(x, y):
    import math
    n = len(x)
    if n < 2:
        return 0
    mx, my = sum(x)/n, sum(y)/n
    num = sum((x[i]-mx)*(y[i]-my) for i in range(n))
    dx = math.sqrt(sum((v-mx)**2 for v in x))
    dy = math.sqrt(sum((v-my)**2 for v in y))
    if dx == 0 or dy == 0:
        return 0
    return num / (dx * dy)


def calcular_spearman(x, y):
    n = len(x)
    if n < 2:
        return 0

    def rank_com_empates(vals):
        # Atribui média dos ranks para valores empatados (tie-average)
        sorted_vals = sorted(enumerate(vals), key=lambda t: t[1])
        ranks = [0.0] * n
        i = 0
        while i < n:
            j = i
            # Encontra grupo de empate
            while j < n - 1 and sorted_vals[j][1] == sorted_vals[j+1][1]:
                j += 1
            # Rank médio para o grupo (1-indexed)
            rank_medio = (i + j) / 2 + 1
            for k in range(i, j + 1):
                ranks[sorted_vals[k][0]] = rank_medio
            i = j + 1
        return ranks

    rx = rank_com_empates(x)
    ry = rank_com_empates(y)
    return calcular_pearson(rx, ry)


def regressao_linear(x, y):
    import math
    n = len(x)
    sx, sy = sum(x), sum(y)
    sxy = sum(x[i]*y[i] for i in range(n))
    sx2 = sum(v**2 for v in x)
    denom = n*sx2 - sx**2
    if abs(denom) < 1e-10:
        return None
    a = (n*sxy - sx*sy) / denom
    b = (sy - a*sx) / n
    my = sy/n
    ss_tot = sum((v-my)**2 for v in y)
    ss_res = sum((y[i] - (a*x[i]+b))**2 for i in range(n))
    r2 = 1 - ss_res/ss_tot if ss_tot > 0 else 0
    return {"type": "linear", "a": a, "b": b, "r2": r2,
            "eq": f"y = {a:.4f} x + {b:.4f}",
            "predict": lambda xi, _a=a, _b=b: _a*xi + _b}


def regressao_logaritmica(x, y):
    import math
    lx = [math.log(max(v, 0.001)) for v in x]
    result = regressao_linear(lx, y)
    if result:
        a, b = result["a"], result["b"]
        result["eq"] = f"y = {a:.4f} * ln(x) + {b:.4f}"
        result["type"] = "logaritmica"
        result["predict"] = lambda xi, _a=a, _b=b: _a * __import__("math").log(max(xi, 0.001)) + _b
    return result




from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime
from io import BytesIO


#  Paleta de cores FGV
C_NAVY   = "0B1F3A"   # cabeçalhos principais
C_BLUE   = "1A3F6F"   # cabeçalhos de seção
C_MID    = "1E5799"   # cabeçalhos de tabela
C_LIGHT  = "D6E4F0"   # fundo de linhas de dados
C_WHITE  = "FFFFFF"
C_WARN   = "FFF3CD"   # fundo alerta
C_WARN_B = "FF8C00"   # borda alerta
C_NORM   = "D4EDDA"   # normal
C_LOW    = "CCE5FF"   # outlier baixo
C_HIGH   = "F8D7DA"   # outlier alto
C_EXCL   = "E2E3E5"   # excluído

def _ft(bold=False, color=C_WHITE, size=10, italic=False):
    return Font(name="Arial", bold=bold, color=color, size=size, italic=italic)

def _fill(hex_color):
    return PatternFill("solid", fgColor=hex_color)

def _border(style="thin"):
    s = Side(border_style=style, color="CBD5E1")
    return Border(left=s, right=s, top=s, bottom=s)

def _align(h="left", v="center", wrap=False):
    return Alignment(horizontal=h, vertical=v, wrap_text=wrap)


def _header_row(ws, row, text, span_end_col, bg=C_NAVY, fg=C_WHITE, size=12):
    cell = ws.cell(row=row, column=1, value=text)
    cell.font = _ft(bold=True, color=fg, size=size)
    cell.fill = _fill(bg)
    cell.alignment = _align("left")
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=span_end_col)


def _section(ws, row, text, span_end_col):
    _header_row(ws, row, text, span_end_col, bg=C_BLUE, size=10)


def _kv(ws, row, label, value, label_color="334155", value_color="0D1B2E"):
    lc = ws.cell(row=row, column=1, value=label)
    lc.font = _ft(bold=True, color=label_color, size=10)
    lc.alignment = _align()
    lc.fill = _fill("F8FAFC")
    vc = ws.cell(row=row, column=2, value=value)
    vc.font = _ft(color=value_color, size=10)
    vc.alignment = _align()


def gerar_relatorio_excel(
    subtema, tema, pais_sel, estado_sel,
    pearson, spearman, reg, reg_type_label,
    st_prazos, st_esforcos,
    exec_min, exec_max, plan_min, plan_max,
    enc_min, enc_max, total_min, total_max,
    metodo, is_san, hist_exec_min, hist_exec_max,
    df_class, excluir_ids,
) -> bytes:
    wb = Workbook()
    now_str = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
    max_corr = max(abs(pearson), abs(spearman))
    corr_forte = max_corr >= 0.6

    def corr_forca(v):
        a = abs(v)
        if a >= 0.7: return "Forte"
        if a >= 0.6: return "Moderada"
        if a >= 0.3: return "Fraca"
        return "Muito fraca"

    #  ABA 1: Resumo da Análise
    ws1 = wb.active
    ws1.title = "Resumo da Análise"
    ws1.column_dimensions["A"].width = 38
    ws1.column_dimensions["B"].width = 42

    _header_row(ws1, 1, "RELATÓRIO DE ANÁLISE DE PROJETOS", 2, size=13)
    ws1.cell(row=2, column=1, value=f"Gerado em: {now_str}").font = _ft(color="64748B", size=9, italic=True)
    ws1.merge_cells("A2:B2")

    ws1.row_dimensions[3].height = 6

    _section(ws1, 4, "PARÂMETROS DA ANÁLISE", 2)
    _kv(ws1, 5, "Tema", tema or "Todos")
    _kv(ws1, 6, "Subtema", subtema)
    _kv(ws1, 7, "País", pais_sel)
    _kv(ws1, 8, "Estado", estado_sel)
    _kv(ws1, 9, "Tema SAN", "Sim" if is_san else "Não")

    ws1.row_dimensions[10].height = 6
    _section(ws1, 11, "CORRELAÇÃO", 2)
    _kv(ws1, 12, "Pearson (Linear)", f"{pearson:.4f}  -  {corr_forca(pearson)}")
    _kv(ws1, 13, "Spearman (Não-linear)", f"{spearman:.4f}  -  {corr_forca(spearman)}")
    dom = "Linear (Pearson)" if abs(pearson) >= abs(spearman) else "Logarítmica (Spearman)"
    _kv(ws1, 14, "Correlação Dominante", dom)
    status_corr = f"FORTE (≥ 0,6) - usando regressão" if corr_forte else f"FRACA (< 0,6) - usando histórico"
    _kv(ws1, 15, "Status da Correlação", status_corr)
    _kv(ws1, 16, "Tipo de Regressão Utilizado", reg_type_label if reg else "-")

    row = 17
    if reg and corr_forte:
        ws1.row_dimensions[row].height = 6; row += 1
        _section(ws1, row, "REGRESSÃO", 2); row += 1
        tipo_r = "Linear" if reg.get("type") == "linear" else "Logarítmica"
        _kv(ws1, row, "Tipo", tipo_r); row += 1
        _kv(ws1, row, "Equação", reg["eq"]); row += 1
        _kv(ws1, row, "R²", f"{reg['r2']:.4f}"); row += 1
        _kv(ws1, row, "1 - R²", f"{1-reg['r2']:.4f}"); row += 1
        _kv(ws1, row, "Coeficiente a", f"{reg['a']:.4f}"); row += 1
        _kv(ws1, row, "Coeficiente b", f"{reg['b']:.4f}"); row += 1

    ws1.row_dimensions[row].height = 6; row += 1
    _section(ws1, row, "INTERVALO HISTÓRICO DE EXECUÇÃO OBSERVADO", 2); row += 1
    _kv(ws1, row, "Prazo Mínimo Histórico de Execução (meses)", f"{hist_exec_min:.2f}"); row += 1
    _kv(ws1, row, "Prazo Máximo Histórico de Execução (meses)", f"{hist_exec_max:.2f}"); row += 1

    # Alertas - só execução
    alerts = []
    if exec_min > hist_exec_max:
        alerts.append(f"Prazo mínimo de execução estimado ({exec_min:.2f} m) ACIMA do máximo histórico ({hist_exec_max:.2f} m)")
    if exec_max > hist_exec_max:
        alerts.append(f"Prazo máximo de execução estimado ({exec_max:.2f} m) ACIMA do máximo histórico ({hist_exec_max:.2f} m)")

    if alerts:
        ws1.row_dimensions[row].height = 6; row += 1
        c = ws1.cell(row=row, column=1, value=" ALERTA: ESTIMATIVA DE EXECUÇÃO FORA DO INTERVALO HISTÓRICO")
        c.font = _ft(bold=True, color="92400E", size=10)
        c.fill = _fill(C_WARN)
        c.alignment = _align()
        ws1.merge_cells(start_row=row, start_column=1, end_row=row, end_column=2)
        row += 1
        for a in alerts:
            ac = ws1.cell(row=row, column=2, value=a)
            ac.font = _ft(color="92400E", size=9)
            ac.fill = _fill(C_WARN)
            row += 1

    #  ABA 2: Cronograma Kerzner
    ws2 = wb.create_sheet("Cronograma Kerzner")
    for col, w in enumerate([28, 28, 22, 22], 1):
        ws2.column_dimensions[get_column_letter(col)].width = w

    _header_row(ws2, 1, "CRONOGRAMA KERZNER (2009)", 4, size=13)
    ws2.row_dimensions[2].height = 6

    enc_desc = "10% do tempo de execução (tema SAN)" if is_san else "10% do total (mín. 1 mês)"
    metas = [
        ("Metodologia", "Kerzner (2009)"),
        ("Encerramento", enc_desc),
        ("Método de Cálculo", metodo),
    ]
    if reg and corr_forte:
        metas += [("Equação utilizada", reg["eq"]), ("R²", f"{reg['r2']:.4f}")]

    for i, (k, v) in enumerate(metas, 3):
        _kv(ws2, i, k, v)

    r = 3 + len(metas) + 1
    ws2.row_dimensions[r].height = 6; r += 1

    # Header tabela fases
    for col, txt in enumerate(["FASE", "PERCENTUAL", "CENÁRIO MÍNIMO (meses)", "CENÁRIO MÁXIMO (meses)"], 1):
        c = ws2.cell(row=r, column=col, value=txt)
        c.font = _ft(bold=True, color=C_WHITE, size=10)
        c.fill = _fill(C_MID)
        c.alignment = _align("center")
    r += 1

    fases = [
        ("Planejamento", "50% do total", plan_min, plan_max),
        ("Execução",     "40% do total", exec_min, exec_max),
        ("Encerramento", "10% do total" if not is_san else "10% da execução", enc_min, enc_max),
        ("TOTAL DO PROJETO", "100%", total_min, total_max),
    ]
    for i, (nome, pct, vmin, vmax) in enumerate(fases):
        bg = C_LIGHT if i % 2 == 0 else C_WHITE
        bold = nome == "TOTAL DO PROJETO"
        for col, val in enumerate([nome, pct, round(vmin,4), round(vmax,4)], 1):
            c = ws2.cell(row=r, column=col, value=val)
            c.font = _ft(bold=bold, color="0D1B2E", size=10)
            c.fill = _fill(C_NAVY if bold else bg)
            if bold: c.font = _ft(bold=True, color=C_WHITE, size=10)
            c.alignment = _align("center" if col > 1 else "left")
        r += 1

    ws2.row_dimensions[r].height = 8; r += 1
    _section(ws2, r, "DETALHAMENTO DO PLANEJAMENTO (Kerzner)", 4); r += 1
    for col, txt in enumerate(["Sub-fase", "Percentual do Total", "Cenário Mínimo (meses)", "Cenário Máximo (meses)"], 1):
        c = ws2.cell(row=r, column=col, value=txt)
        c.font = _ft(bold=True, color=C_WHITE, size=9)
        c.fill = _fill(C_BLUE)
        c.alignment = _align("center")
    r += 1

    subfases = [
        ("Conceitualização",      0.05),
        ("Estudo de Viabilidade", 0.10),
        ("Planejamento Preliminar", 0.15),
        ("Planejamento Detalhado", 0.20),
    ]
    for i, (nome, pct) in enumerate(subfases):
        bg = C_LIGHT if i % 2 == 0 else C_WHITE
        for col, val in enumerate([nome, f"{int(pct*100)}%",
                                    round(total_min*pct, 4), round(total_max*pct, 4)], 1):
            c = ws2.cell(row=r, column=col, value=val)
            c.font = _ft(color="0D1B2E", size=10)
            c.fill = _fill(bg)
            c.alignment = _align("center" if col > 1 else "left")
        r += 1

    #  ABA 3: Estatísticas
    ws3 = wb.create_sheet("Estatísticas")
    for col, w in enumerate([30, 20, 20], 1):
        ws3.column_dimensions[get_column_letter(col)].width = w

    _header_row(ws3, 1, "ESTATÍSTICAS DA ANÁLISE", 3, size=13)
    ws3.row_dimensions[2].height = 6

    for col, txt in enumerate(["INDICADOR", "ESFORÇO", "PRAZO (meses)"], 1):
        c = ws3.cell(row=3, column=col, value=txt)
        c.font = _ft(bold=True, color=C_WHITE, size=10)
        c.fill = _fill(C_MID)
        c.alignment = _align("center")

    indicadores = [
        ("Média",           st_esforcos.get("mean",0),   st_prazos.get("mean",0)),
        ("Mediana",         st_esforcos.get("median",0), st_prazos.get("median",0)),
        ("Desvio Padrão",   st_esforcos.get("std",0),    st_prazos.get("std",0)),
        ("1º Quartil (Q1)", st_esforcos.get("q1",0),     st_prazos.get("q1",0)),
        ("3º Quartil (Q3)", st_esforcos.get("q3",0),     st_prazos.get("q3",0)),
        ("IQR (Q3 - Q1)",   st_esforcos.get("iqr",0),    st_prazos.get("iqr",0)),
        ("Limite Inferior", st_esforcos.get("lower",0),  st_prazos.get("lower",0)),
        ("Limite Superior", st_esforcos.get("upper",0),  st_prazos.get("upper",0)),
        ("Mínimo histórico",st_esforcos.get("min",0),    st_prazos.get("min",0)),
        ("Máximo histórico",st_esforcos.get("max",0),    st_prazos.get("max",0)),
    ]
    for i, (label, esf, prazo) in enumerate(indicadores, 4):
        bg = C_LIGHT if i % 2 == 0 else C_WHITE
        for col, val in enumerate([label, round(esf,4), round(prazo,4)], 1):
            c = ws3.cell(row=i, column=col, value=val)
            c.font = _ft(color="0D1B2E", size=10)
            c.fill = _fill(bg)
            c.alignment = _align("center" if col > 1 else "left")

    r3 = len(indicadores) + 5
    ws3.row_dimensions[r3].height = 8; r3 += 1
    _section(ws3, r3, "CORRELAÇÃO", 3); r3 += 1
    for col, txt in enumerate(["CORRELAÇÃO", "VALOR", "FORÇA"], 1):
        c = ws3.cell(row=r3, column=col, value=txt)
        c.font = _ft(bold=True, color=C_WHITE, size=10)
        c.fill = _fill(C_BLUE)
        c.alignment = _align("center")
    r3 += 1
    for i, (label, val) in enumerate([("Pearson (Linear)", pearson), ("Spearman (Não-linear)", spearman)]):
        bg = C_LIGHT if i % 2 == 0 else C_WHITE
        for col, v in enumerate([label, round(val, 4), corr_forca(val)], 1):
            c = ws3.cell(row=r3, column=col, value=v)
            c.font = _ft(color="0D1B2E", size=10)
            c.fill = _fill(bg)
            c.alignment = _align("center" if col > 1 else "left")
        r3 += 1

    #  ABA 4: Projetos
    ws4 = wb.create_sheet("Projetos")
    ws4.column_dimensions["A"].width = 55
    for col, w in enumerate([14, 18, 12, 12, 18, 18, 16], 2):
        ws4.column_dimensions[get_column_letter(col)].width = w

    _header_row(ws4, 1, "DETALHAMENTO DOS PROJETOS", 8, size=13)
    ws4.row_dimensions[2].height = 6

    headers = ["Nome", "País", "Estado", "Tipo", "Esforço", "Duração (meses)", "Classificação", "Status na Análise"]
    for col, txt in enumerate(headers, 1):
        c = ws4.cell(row=3, column=col, value=txt)
        c.font = _ft(bold=True, color=C_WHITE, size=10)
        c.fill = _fill(C_MID)
        c.alignment = _align("center")

    row4 = 4
    total = len(df_class)
    excluidos_count = len(excluir_ids)
    analisados = total - excluidos_count

    for _, proj in df_class.iterrows():
        excluido = proj["id"] in excluir_ids
        classif = proj.get("Classificação", "Normal")
        status = "Excluído" if excluido else "Incluído"

        if excluido:
            bg = C_EXCL
        elif classif == "Outlier Alto":
            bg = C_HIGH
        elif classif == "Outlier Baixo":
            bg = C_LOW
        else:
            bg = C_NORM if row4 % 2 == 0 else C_WHITE

        vals = [
            str(proj.get("nome_edital") or "-"),
            str(proj.get("pais") or "-"),
            str(proj.get("estado") or "-"),
            str(proj.get("tipo_edital") or "Esforço"),
            proj.get("esforco") or 0,
            abs(proj.get("prazo_meses") or 0),
            classif,
            status,
        ]
        for col, val in enumerate(vals, 1):
            c = ws4.cell(row=row4, column=col, value=val)
            c.font = _ft(color="0D1B2E", size=9)
            c.fill = _fill(bg)
            c.alignment = _align("left" if col == 1 else "center", wrap=col==1)
        row4 += 1

    # Rodapé totais
    ws4.row_dimensions[row4].height = 6; row4 += 1
    summary = f"Total: {total} projetos   |   Analisados: {analisados}   |   Excluídos: {excluidos_count}"
    c = ws4.cell(row=row4, column=1, value=summary)
    c.font = _ft(bold=True, color="1A3F6F", size=10)
    ws4.merge_cells(start_row=row4, start_column=1, end_row=row4, end_column=8)

    #  Salvar
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()


def pagina_analise_prazos():
    import math

    header_principal()

    df_edit = carregar_view()
    if df_edit.empty:
        st.warning("Nenhum dado disponível.")
        return

    for col in ["prazo_meses", "esforco"]:
        if col in df_edit.columns:
            df_edit[col] = pd.to_numeric(df_edit[col], errors="coerce")

    # Filtros
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    cf1, cf2, cf3, cf4 = st.columns(4)
    with cf1:
        temas = sorted(df_edit["tema"].dropna().unique().tolist())
        tema_sel = st.selectbox("Tema", ["Todos"] + temas, key="ap_tema")
    df_filt = df_edit if tema_sel == "Todos" else df_edit[df_edit["tema"] == tema_sel]
    with cf2:
        subtemas = sorted(df_filt["subtema"].dropna().unique().tolist())
        subtema_sel = st.selectbox("Subtema (opcional)",
                                   ["Todos"] + subtemas, key="ap_subtema")
    if tema_sel == "Todos" and subtema_sel == "Todos":
        st.info("Selecione ao menos um Tema ou Subtema para iniciar a análise.")
        st.markdown('</div>', unsafe_allow_html=True)
        return
    if subtema_sel != "Todos":
        df_tema = df_filt[df_filt["subtema"] == subtema_sel].copy()
    else:
        df_tema = df_filt.copy()
    with cf3:
        paises = sorted(df_tema["pais"].dropna().unique().tolist())
        pais_sel = st.selectbox("País", ["Todos"] + paises, key="ap_pais")
    if pais_sel != "Todos":
        df_tema = df_tema[df_tema["pais"] == pais_sel]
    with cf4:
        estados = sorted(df_tema["estado"].dropna().unique().tolist())
        estado_sel = st.selectbox("Estado", ["Todos"] + estados, key="ap_estado")
    if estado_sel != "Todos":
        df_tema = df_tema[df_tema["estado"] == estado_sel]
    st.markdown('</div>', unsafe_allow_html=True)

    #  Exclusões
    label_analise = subtema_sel if subtema_sel != "Todos" else tema_sel
    excluir_key = f"excluir_{label_analise}_{pais_sel}_{estado_sel}"
    if excluir_key not in st.session_state:
        st.session_state[excluir_key] = set()
    df_tema["_excluido"] = df_tema["id"].isin(st.session_state[excluir_key])
    df_analise = df_tema[~df_tema["_excluido"]].copy()

    if len(df_analise) < 3:
        st.warning(f"São necessários pelo menos 3 projetos. Encontrados: {len(df_analise)}")
        return

    df_valido = df_analise.dropna(subset=["prazo_meses", "esforco"])
    df_valido = df_valido[(df_valido["prazo_meses"] > 0) & (df_valido["esforco"] > 0)]
    is_san = "SAN-" in subtema_sel.upper() or (subtema_sel == "Todos" and "SAN-" in tema_sel.upper())

    #  Estatísticas
    def stats(vals):
        if not vals: return {}
        s = sorted(vals)
        n = len(s)
        mean = sum(s)/n
        median = s[n//2] if n%2 else (s[n//2-1]+s[n//2])/2
        variance = sum((v-mean)**2 for v in s)/(n-1) if n>1 else 0
        std = math.sqrt(variance)
        q1 = s[max(0, n//4)]
        q3 = s[min(n-1, 3*n//4)]
        iqr = q3-q1
        return {"mean":mean,"median":median,"std":std,"q1":q1,"q3":q3,"iqr":iqr,
                "lower":q1-1.5*iqr,"upper":q3+1.5*iqr,"min":s[0],"max":s[-1]}

    prazos = df_analise["prazo_meses"].dropna().tolist()
    esforcos = df_analise["esforco"].dropna().tolist()
    st_prazos = stats(prazos)
    st_esforcos = stats(esforcos)

    #  Correlações
    pearson, spearman = 0.0, 0.0
    reg_linear, reg_log = None, None

    if len(df_valido) >= 3:
        xs = df_valido["esforco"].tolist()
        ys = df_valido["prazo_meses"].tolist()
        pearson = calcular_pearson(xs, ys)
        spearman = calcular_spearman(xs, ys)
        if max(abs(pearson), abs(spearman)) >= 0.6:
            reg_linear = regressao_linear(xs, ys)
            reg_log = regressao_logaritmica(xs, ys)

    max_corr = max(abs(pearson), abs(spearman))
    corr_forte = max_corr >= 0.6

    #  Seletor de Tipo de Regressão
    reg_type_sel = "auto"
    if corr_forte and reg_linear and reg_log:
        st.markdown('<div style="font-size:0.72rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#64748b;margin-bottom:8px;">Tipo de Regressão</div>', unsafe_allow_html=True)
        auto_label = f"Automático ({'Linear' if abs(pearson) >= abs(spearman) else 'Logarítmica'})"
        opcoes_reg = {
            "auto": auto_label,
            "linear": f"Linear (Pearson: {pearson:.2f})",
            "logaritmica": f"Logarítmica (Spearman: {spearman:.2f})",
        }
        reg_cols = st.columns(3)
        for i, (key, label) in enumerate(opcoes_reg.items()):
            with reg_cols[i]:
                if st.button(label, key=f"reg_{key}", use_container_width=True,
                             type="primary" if st.session_state.get("reg_type_ap", "auto") == key else "secondary"):
                    st.session_state["reg_type_ap"] = key
                    st.rerun()
        reg_type_sel = st.session_state.get("reg_type_ap", "auto")

    #  Determina regressão ativa
    reg = None
    reg_type_label = ""
    if corr_forte and reg_linear and reg_log:
        if reg_type_sel == "auto":
            if abs(pearson) >= abs(spearman):
                reg = reg_linear; reg_type_label = "Linear (Pearson dominante)"
            else:
                reg = reg_log; reg_type_label = "Logarítmica (Spearman dominante)"
        elif reg_type_sel == "linear":
            reg = reg_linear; reg_type_label = "Linear"
        else:
            reg = reg_log; reg_type_label = "Logarítmica"

    # Status correlação
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    if corr_forte:
        st.success(f"Correlação forte detectada - máxima: {max_corr:.2f} (≥ 0,6). Regressão **{reg_type_label}** será usada.")
    else:
        st.warning(f"Correlação fraca ({max_corr:.2f} < 0,6). Serão usados os valores históricos mínimos e máximos.")

    # Gráfico dispersão
    if len(df_valido) >= 2:
        try:
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_valido["esforco"].tolist(), y=df_valido["prazo_meses"].tolist(),
                mode="markers",
                marker=dict(size=10, color="#2563eb", opacity=0.7, line=dict(color="#1d4ed8", width=1)),
                text=df_valido.get("nome_edital", df_valido.index).tolist(),
                hovertemplate="<b>%{text}</b><br>Esforço: %{x}<br>Prazo: %{y:.1f} meses<extra></extra>",
                name="Projetos"
            ))
            title = f"Esforço vs Duração - {subtema_sel}"
            if reg and corr_forte:
                xs_s = sorted(df_valido["esforco"].tolist())
                ys_r = [reg["predict"](x) for x in xs_s]
                fig.add_trace(go.Scatter(
                    x=xs_s, y=ys_r, mode="lines",
                    line=dict(color="#ef4444", width=2),
                    name=f"Regressão {reg_type_label}",
                ))
                title = f"Regressão {reg_type_label}: {reg['eq']}"
            fig.update_layout(
                title=dict(text=title, font=dict(color="#ef4444", size=13)),
                xaxis_title="Esforço", yaxis_title="Duração (meses)",
                height=420, template="plotly_white",
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                margin=dict(t=60, b=40, l=40, r=20)
            )
            st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            st.info("Instale plotly: pip install plotly")

    st.markdown('<div style="font-size:0.72rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#64748b;border-bottom:1px solid #e2e8f0;padding-bottom:6px;margin:16px 0 12px;">Correlação</div>', unsafe_allow_html=True)
    cc1, cc2 = st.columns(2)
    def corr_badge(val):
        a = abs(val)
        if a >= 0.7: return "Forte"
        if a >= 0.6: return "Moderada"
        if a >= 0.3: return "Fraca"
        return "Muito fraca"
    def corr_dir(val):
        return "positiva" if val > 0 else "negativa" if val < 0 else "neutra"

    with cc1:
        em_uso_p = reg and reg.get("type") == "linear"
        badge_uso = ' <span style="background:#2563eb;color:#fff;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:600;"> Em uso</span>' if em_uso_p else ''
        st.markdown(f"""
        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:16px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                <span style="color:#64748b;font-size:13px;">Pearson (Linear)</span>
                <span style="background:#e0f2fe;color:#0369a1;padding:2px 10px;border-radius:999px;font-size:11px;font-weight:600;">{corr_badge(pearson)}{badge_uso}</span>
            </div>
            <div style="font-size:28px;font-weight:800;color:#1e3a8a;">{pearson:.2f}</div>
            <div style="color:#94a3b8;font-size:12px;margin-top:4px;">Correlação {corr_dir(pearson)}</div>
        </div>
        """, unsafe_allow_html=True)

    with cc2:
        em_uso_s = reg and reg.get("type") == "logaritmica"
        badge_uso_s = ' <span style="background:#2563eb;color:#fff;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:600;"> Em uso</span>' if em_uso_s else ''
        st.markdown(f"""
        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:16px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                <span style="color:#64748b;font-size:13px;">Spearman (Não-linear)</span>
                <span style="background:#e0f2fe;color:#0369a1;padding:2px 10px;border-radius:999px;font-size:11px;font-weight:600;">{corr_badge(spearman)}{badge_uso_s}</span>
            </div>
            <div style="font-size:28px;font-weight:800;color:#1e3a8a;">{spearman:.2f}</div>
            <div style="color:#94a3b8;font-size:12px;margin-top:4px;">Correlação {corr_dir(spearman)}</div>
        </div>
        """, unsafe_allow_html=True)

    if reg and corr_forte:
        st.markdown(f"""
        <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:14px;margin-top:12px;">
            <div style="font-weight:700;color:#1e40af;margin-bottom:4px;">Equação da Regressão {reg_type_label}:</div>
            <div style="font-family:monospace;color:#1d4ed8;font-size:14px;">{reg['eq']}</div>
            <div style="font-weight:700;color:#1e40af;margin-top:8px;margin-bottom:4px;">Coeficiente de Determinação:</div>
            <div style="font-family:monospace;color:#1d4ed8;font-size:13px;">R² = {reg['r2']:.4f} &nbsp;&nbsp; 1 - R² = {1-reg['r2']:.4f}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.72rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#64748b;border-bottom:1px solid #e2e8f0;padding-bottom:6px;margin-bottom:12px;">Estatísticas</div>', unsafe_allow_html=True)
    sc1, sc2 = st.columns(2)
    def stat_table(data):
        return pd.DataFrame(list(data.items()), columns=["Métrica", "Valor"])
    with sc1:
        st.markdown("**Prazo (meses)**")
        if st_prazos:
            st.dataframe(stat_table({
                "Média": f"{st_prazos['mean']:.2f}", "Mediana": f"{st_prazos['median']:.2f}",
                "Desvio Padrão": f"{st_prazos['std']:.2f}", "Q1": f"{st_prazos['q1']:.2f}",
                "Q3": f"{st_prazos['q3']:.2f}", "IQR": f"{st_prazos['iqr']:.2f}",
                "Mínimo histórico": f"{st_prazos['min']:.2f}", "Máximo histórico": f"{st_prazos['max']:.2f}",
            }), hide_index=True, use_container_width=True)
    with sc2:
        st.markdown("**Esforço**")
        if st_esforcos:
            st.dataframe(stat_table({
                "Média": f"{st_esforcos['mean']:.2f}", "Mediana": f"{st_esforcos['median']:.2f}",
                "Desvio Padrão": f"{st_esforcos['std']:.2f}", "Q1": f"{st_esforcos['q1']:.2f}",
                "Q3": f"{st_esforcos['q3']:.2f}", "IQR": f"{st_esforcos['iqr']:.2f}",
                "Mínimo histórico": f"{st_esforcos['min']:.2f}", "Máximo histórico": f"{st_esforcos['max']:.2f}",
            }), hide_index=True, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Calculadora Kerzner
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.72rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#64748b;border-bottom:1px solid #e2e8f0;padding-bottom:6px;margin-bottom:12px;">Calculadora de Prazos - Metodologia Kerzner</div>', unsafe_allow_html=True)
    if is_san:
        st.info("Tema SAN - Encerramento = 10% da execução.")

    esforco_input = 0.0
    if corr_forte and reg:
        unidade = ""
        if "unidade" in df_analise.columns:
            vals = df_analise["unidade"].dropna()
            if not vals.empty: unidade = vals.iloc[0]
        esforco_input = st.number_input(f"Esforço ({unidade})", min_value=0.0, step=0.1, key="ap_esforco")

    if st.button("Calcular Prazos", type="primary", key="ap_calcular"):
        hist_min = st_prazos.get("min", 0)
        hist_max = st_prazos.get("max", 0)
        if corr_forte and reg and esforco_input > 0:
            y_pred = reg["predict"](max(0.001, esforco_input))
            comp = max(0.1, 1 - reg["r2"])
            exec_min = max(0.5, y_pred * (1 - comp))
            exec_max = y_pred * (1 + comp)
            metodo = f"Regressão {reg_type_label}"
        else:
            exec_min = hist_min
            exec_max = hist_max
            metodo = "Valores históricos (correlação fraca)"

        total_min = exec_min / 0.4
        total_max = exec_max / 0.4
        plan_min = total_min * 0.5
        plan_max = total_max * 0.5
        enc_min = exec_min * 0.1 if is_san else max(1, total_min * 0.1)
        enc_max = exec_max * 0.1 if is_san else max(1, total_max * 0.1)

        kerzner_alerts = []
        if exec_min > hist_max:
            kerzner_alerts.append(f"Prazo mínimo de execução estimado ({exec_min:.1f}m) acima do máximo histórico ({hist_max:.1f}m)")
        if exec_max > hist_max:
            kerzner_alerts.append(f"Prazo máximo de execução estimado ({exec_max:.1f}m) acima do máximo histórico ({hist_max:.1f}m)")
        st.session_state["kerzner_alerts"] = kerzner_alerts
        st.session_state["kerzner_result"] = {
            "exec": (exec_min, exec_max), "plan": (plan_min, plan_max),
            "enc": (enc_min, enc_max), "total": (total_min, total_max),
            "metodo": metodo, "hist_exec_min": hist_min, "hist_exec_max": hist_max,
            "is_san": is_san, "reg_label": reg_type_label,
            "reg_eq": reg["eq"] if reg else "", "r2": reg["r2"] if reg else 0,
        }

    if "kerzner_result" in st.session_state:
        r = st.session_state["kerzner_result"]
        exec_min, exec_max = r["exec"]
        plan_min, plan_max = r["plan"]
        enc_min, enc_max = r["enc"]
        total_min, total_max = r["total"]
        hist_exec_min, hist_exec_max = r["hist_exec_min"], r["hist_exec_max"]
        enc_desc = "10% da execução" if r["is_san"] else "10% do total (mín. 1 mês)"

        st.markdown("#### Cronograma Completo do Projeto")
        fases = [
            ("🟡 Planejamento", "50% do projeto total", plan_min, plan_max, "#f59e0b"),
            (" Execução", "40% do projeto total", exec_min, exec_max, "#3b82f6"),
            (f"🟢 Encerramento", enc_desc, enc_min, enc_max, "#10b981"),
            ("🟣 Total", "Projeto completo", total_min, total_max, "#8b5cf6"),
        ]
        k1, k2, k3, k4 = st.columns(4)
        for col, (titulo, desc, vmin, vmax, cor) in zip([k1,k2,k3,k4], fases):
            with col:
                st.markdown(f"""
                <div style="border:1px solid #e2e8f0;border-left:4px solid {cor};border-radius:10px;padding:14px;background:#fff;">
                    <div style="font-weight:700;color:#0f172a;font-size:13px;margin-bottom:4px;">{titulo}</div>
                    <div style="color:#94a3b8;font-size:11px;margin-bottom:10px;">{desc}</div>
                    <div style="color:#64748b;font-size:12px;">Mínimo:</div>
                    <div style="font-size:22px;font-weight:800;color:{cor};">{vmin:.2f} <span style="font-size:13px;font-weight:400;">meses</span></div>
                    <div style="color:#64748b;font-size:12px;margin-top:6px;">Máximo:</div>
                    <div style="font-size:22px;font-weight:800;color:{cor};">{vmax:.2f} <span style="font-size:13px;font-weight:400;">meses</span></div>
                </div>
                """, unsafe_allow_html=True)

        # Alerta - só quando execução estimada > máximo histórico de execução
        alerts = []
        if exec_min > hist_exec_max:
            alerts.append(f"Prazo mínimo de execução estimado ({exec_min:.1f} m) está **acima** do máximo histórico observado ({hist_exec_max:.1f} m)")
        if exec_max > hist_exec_max:
            alerts.append(f"Prazo máximo de execução estimado ({exec_max:.1f} m) está **acima** do máximo histórico observado ({hist_exec_max:.1f} m)")
        if alerts:
            st.warning(" **Atenção: estimativa de execução fora do intervalo histórico**\n\n" + "\n\n".join(alerts) +
                      f"\n\nIntervalo histórico de execução: **{hist_exec_min:.1f}** a **{hist_exec_max:.1f}** meses. Use os valores com cautela.")

        # Cronograma visual
        st.markdown("#### Cronograma Visual (Metodologia Kerzner)")
        st.markdown("""
        <div style="display:flex;gap:16px;font-size:12px;color:#64748b;margin-bottom:12px;">
            <span><span style="display:inline-block;width:12px;height:12px;background:#f59e0b;border-radius:3px;margin-right:4px;"></span>Planejamento (50%)</span>
            <span><span style="display:inline-block;width:12px;height:12px;background:#3b82f6;border-radius:3px;margin-right:4px;"></span>Execução (40%)</span>
            <span><span style="display:inline-block;width:12px;height:12px;background:#10b981;border-radius:3px;margin-right:4px;"></span>Encerramento</span>
        </div>
        """, unsafe_allow_html=True)
        for label, (pv, ev, cv), total in [
            ("Cenário Mínimo", (plan_min, exec_min, enc_min), total_min),
            ("Cenário Máximo", (plan_max, exec_max, enc_max), total_max),
        ]:
            if total > 0:
                pp = pv/total*100; ep = ev/total*100; cp = cv/total*100
                st.markdown(f"**{label}** - {total:.2f} meses")
                st.markdown(f"""
                <div style="display:flex;height:28px;border-radius:8px;overflow:hidden;margin-bottom:4px;">
                    <div style="width:{pp:.1f}%;background:#f59e0b;"></div>
                    <div style="width:{ep:.1f}%;background:#3b82f6;"></div>
                    <div style="width:{cp:.1f}%;background:#10b981;"></div>
                </div>
                <div style="display:flex;justify-content:space-between;font-size:11px;color:#94a3b8;margin-bottom:14px;">
                    <span>0</span><span>{total:.2f} meses</span>
                </div>
                """, unsafe_allow_html=True)

        # Metodologia
        enc_met = "10% do tempo de execução (tema SAN)" if r["is_san"] else "10% do tempo total (mínimo 1 mês)"
        st.markdown(f"""
        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:16px;margin-top:8px;">
            <div style="font-weight:700;color:#0f172a;margin-bottom:10px;">Metodologia Kerzner (2009)</div>
            <div style="font-size:13px;color:#475569;line-height:1.8;">
                • <b>Planejamento:</b> 50% do tempo total<br>
                • <b>Execução:</b> 40% do tempo total<br>
                • <b>Encerramento:</b> {enc_met}<br>
                • <b>Método de Cálculo:</b> {r['metodo']}
            </div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Classificação dos projetos
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.72rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#64748b;border-bottom:1px solid #e2e8f0;padding-bottom:6px;margin-bottom:12px;">Projetos incluídos na análise</div>', unsafe_allow_html=True)

    def classificar(prazo, excluido):
        if excluido: return "Excluído"
        if not st_prazos: return "Normal"
        if prazo < st_prazos["lower"]: return "Outlier Baixo"
        if prazo >= st_prazos["upper"]: return "Outlier Alto"
        return "Normal"

    df_class = df_tema.copy()
    df_class["Classificação"] = df_class.apply(
        lambda row: classificar(row.get("prazo_meses", 0), row["_excluido"]), axis=1)

    n_norm = len(df_class[df_class["Classificação"] == "Normal"])
    n_low = len(df_class[df_class["Classificação"] == "Outlier Baixo"])
    n_high = len(df_class[df_class["Classificação"] == "Outlier Alto"])
    rc1, rc2, rc3, rc4 = st.columns(4)
    rc1.metric("Total", len(df_class))
    rc2.metric("Normal", n_norm)
    rc3.metric("Outlier Baixo", n_low)
    rc4.metric("Outlier Alto", n_high)

    st.caption("Marque os projetos que deseja excluir da análise estatística.")
    hc = st.columns([0.5, 3, 1.5, 1.5, 1, 1, 1.5])
    for col, label in zip(hc, ["", "Nome", "País", "Estado", "Esforço", "Prazo (m)", "Classificação"]):
        col.markdown(f"**{label}**")

    for _, row in df_class.iterrows():
        cols = st.columns([0.5, 3, 1.5, 1.5, 1, 1, 1.5])
        excluido = row["id"] in st.session_state[excluir_key]
        with cols[0]:
            novo = st.checkbox("", value=excluido, key=f"excl_{row['id']}_{excluir_key}", label_visibility="collapsed")
            if novo != excluido:
                if novo: st.session_state[excluir_key].add(row["id"])
                else: st.session_state[excluir_key].discard(row["id"])
                st.rerun()
        nome = str(row.get("nome_edital", "-") or "-")
        cols[1].write(f"~~{nome[:60]}~~" if excluido else nome[:60])
        cols[2].write(str(row.get("pais") or "-"))
        cols[3].write(str(row.get("estado") or "-"))
        cols[4].write(f"{row.get('esforco') or 0:.1f}")
        cols[5].write(f"{abs(row.get('prazo_meses') or 0):.1f}")
        cols[6].write(row["Classificação"])

    st.markdown('</div>', unsafe_allow_html=True)

    # Exportação
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    with st.container():
        kr_res = st.session_state.get("kerzner_result", {})
        export_data = {
            "tema": tema_sel if tema_sel != "Todos" else "",
            "subtema": subtema_sel if subtema_sel != "Todos" else tema_sel, "pais_sel": pais_sel, "estado_sel": estado_sel,
            "is_san": is_san, "pearson": pearson, "spearman": spearman,
            "corr_forte": corr_forte,
            "reg": {"type": reg.get("type",""),"eq": reg.get("eq",""),
                    "r2": reg.get("r2",0),"a": reg.get("a",0),"b": reg.get("b",0)} if reg else None,
            "reg_label": reg_type_label,
            "reg_type_display": f"Automático ({reg_type_label})" if reg_type_sel=="auto" else reg_type_label,
            "st_prazos": st_prazos, "st_esforcos": st_esforcos,
            "kerzner": {
                "plan_min": kr_res.get("plan",(0,0))[0],"plan_max": kr_res.get("plan",(0,0))[1],
                "exec_min": kr_res.get("exec",(0,0))[0],"exec_max": kr_res.get("exec",(0,0))[1],
                "enc_min":  kr_res.get("enc",(0,0))[0], "enc_max":  kr_res.get("enc",(0,0))[1],
                "total_min":kr_res.get("total",(0,0))[0],"total_max":kr_res.get("total",(0,0))[1],
            } if kr_res else {},
            "alerts": st.session_state.get("kerzner_alerts", []),
            "projetos": df_class.to_dict("records"),
        }
        try:
            xlsx_bytes = exportar_analise_excel(export_data)
            fname = f"Relatorio_Analise_{subtema_sel.replace(' ','_')}_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
            st.download_button(" Exportar Relatório Excel", xlsx_bytes, file_name=fname,
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               use_container_width=True)
        except Exception as ex:
            st.error(f"Erro ao gerar Excel: {ex}")
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

    if st.session_state.menu == "Base de Prazos":
        pagina_consulta()
    elif st.session_state.menu == "Análise de Prazos":
        pagina_analise_prazos()
    elif st.session_state.menu == "Projetos Concluídos":
        pagina_projetos_concluidos()
    elif st.session_state.menu == "Solicitações" or st.session_state.menu.startswith("Solicitações ("):
        pagina_solicitacoes()
    elif st.session_state.menu == "Base de dados":
        pagina_base()
    elif st.session_state.menu == "Minha conta":
        pagina_minha_conta()
    elif st.session_state.menu == "Usuários":
        pagina_usuarios()


if __name__ == "__main__":
    main()
