"""Sincronização de planilhas de oportunidades a partir do Google Drive.

Cada área tem uma Planilha Google própria (sobrescrita semanalmente). As fontes
ficam cadastradas na tabela drive_sync_fontes e cada execução é registrada em
drive_sync_log. Uma planilha só é reimportada quando o modifiedTime do Drive muda.

Autenticação via Service Account: o JSON da chave vai na variável de ambiente
GDRIVE_SA_JSON e cada planilha deve ser compartilhada (Leitor) com o e-mail da
Service Account.

Uso pelo job agendado:  python drive_sync.py
"""
import json
import logging
import os
import re
import sys
from io import BytesIO

from oportunidades_import import (
    agora_str, get_conn, importar_oportunidades, registrar_upload_historico,
)

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
MIME_SHEETS = "application/vnd.google-apps.spreadsheet"
MIME_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
USUARIO_JOB = "drive-sync"


# =========================================================
# CREDENCIAIS / DRIVE
# =========================================================
def _credenciais_info() -> dict | None:
    raw = os.environ.get("GDRIVE_SA_JSON", "").strip()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.error("GDRIVE_SA_JSON não é um JSON válido.")
        return None


def credenciais_configuradas() -> bool:
    return _credenciais_info() is not None


def email_service_account() -> str:
    info = _credenciais_info()
    return (info or {}).get("client_email", "")


def _drive_service():
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    info = _credenciais_info()
    if info is None:
        raise RuntimeError("Variável GDRIVE_SA_JSON não configurada.")
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def extrair_file_id(texto: str) -> str | None:
    """Aceita o link da planilha (…/d/<id>/edit) ou o próprio ID."""
    texto = (texto or "").strip()
    m = re.search(r"/d/([a-zA-Z0-9_-]{20,})", texto) or re.search(r"[?&]id=([a-zA-Z0-9_-]{20,})", texto)
    if m:
        return m.group(1)
    if re.fullmatch(r"[a-zA-Z0-9_-]{20,}", texto):
        return texto
    return None


def _baixar_xlsx(service, file_id: str, mime_type: str) -> BytesIO:
    from googleapiclient.http import MediaIoBaseDownload

    if mime_type == MIME_SHEETS:
        request = service.files().export_media(fileId=file_id, mimeType=MIME_XLSX)
    else:
        request = service.files().get_media(fileId=file_id, supportsAllDrives=True)
    buf = BytesIO()
    downloader = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    buf.seek(0)
    return buf


# =========================================================
# BANCO
# =========================================================
def garantir_tabelas():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS drive_sync_fontes (
            id          SERIAL PRIMARY KEY,
            area        TEXT NOT NULL UNIQUE,
            file_id     TEXT NOT NULL,
            ativo       BOOLEAN NOT NULL DEFAULT TRUE,
            criado_por  TEXT,
            criado_em   TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS drive_sync_log (
            id            SERIAL PRIMARY KEY,
            fonte_id      INTEGER,
            area          TEXT,
            file_id       TEXT,
            nome_arquivo  TEXT,
            modified_time TEXT,
            status        TEXT NOT NULL,
            inseridos     INTEGER DEFAULT 0,
            ignorados     INTEGER DEFAULT 0,
            erros         INTEGER DEFAULT 0,
            mensagem      TEXT,
            executado_por TEXT,
            executado_em  TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def listar_fontes():
    """Fontes cadastradas com o resultado da última execução de cada uma."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT f.id, f.area, f.file_id, f.ativo,
               l.status, l.executado_em, l.inseridos, l.mensagem
        FROM drive_sync_fontes f
        LEFT JOIN LATERAL (
            SELECT status, executado_em, inseridos, mensagem
            FROM drive_sync_log
            WHERE fonte_id = f.id
            ORDER BY id DESC LIMIT 1
        ) l ON TRUE
        ORDER BY f.area
    """)
    cols = ["id", "area", "file_id", "ativo", "ultimo_status", "ultima_execucao",
            "ultimos_inseridos", "ultima_mensagem"]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    conn.close()
    return rows


def salvar_fonte(area: str, file_id: str, usuario: str):
    """Cadastra a planilha da área (ou substitui a existente)."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO drive_sync_fontes (area, file_id, ativo, criado_por, criado_em)
        VALUES (%s, %s, TRUE, %s, %s)
        ON CONFLICT (area) DO UPDATE SET file_id = EXCLUDED.file_id, ativo = TRUE
    """, (area.strip(), file_id, usuario, agora_str()))
    conn.commit()
    conn.close()


def remover_fonte(fonte_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM drive_sync_fontes WHERE id = %s", (fonte_id,))
    conn.commit()
    conn.close()


def _ultimo_modified_time_importado(cur, fonte_id: int, file_id: str):
    cur.execute("""
        SELECT modified_time FROM drive_sync_log
        WHERE fonte_id = %s AND file_id = %s AND status = 'importado'
        ORDER BY id DESC LIMIT 1
    """, (fonte_id, file_id))
    row = cur.fetchone()
    return row[0] if row else None


def _registrar_log(**campos):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO drive_sync_log
            (fonte_id, area, file_id, nome_arquivo, modified_time, status,
             inseridos, ignorados, erros, mensagem, executado_por, executado_em)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        campos.get("fonte_id"), campos.get("area"), campos.get("file_id"),
        campos.get("nome_arquivo"), campos.get("modified_time"), campos["status"],
        campos.get("inseridos", 0), campos.get("ignorados", 0), campos.get("erros", 0),
        campos.get("mensagem"), campos.get("executado_por"), agora_str(),
    ))
    conn.commit()
    conn.close()


# =========================================================
# SINCRONIZAÇÃO
# =========================================================
def sincronizar(usuario: str = USUARIO_JOB, forcar: bool = False) -> list[dict]:
    """Importa a planilha de cada fonte ativa. Retorna um resumo por área.

    status: 'importado', 'sem_alteracao' ou 'erro'.
    """
    garantir_tabelas()
    service = _drive_service()

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, area, file_id FROM drive_sync_fontes WHERE ativo ORDER BY area")
    fontes = cur.fetchall()

    resultados = []
    for fonte_id, area, file_id in fontes:
        res = {"fonte_id": fonte_id, "area": area, "file_id": file_id, "executado_por": usuario}
        try:
            meta = service.files().get(
                fileId=file_id, fields="id,name,mimeType,modifiedTime", supportsAllDrives=True
            ).execute()
            res["nome_arquivo"] = meta.get("name")
            res["modified_time"] = meta.get("modifiedTime")

            if not forcar and res["modified_time"] == _ultimo_modified_time_importado(cur, fonte_id, file_id):
                res.update(status="sem_alteracao",
                           mensagem="Planilha não foi alterada desde a última importação.")
            else:
                arquivo = _baixar_xlsx(service, file_id, meta.get("mimeType"))
                ins, ign, err = importar_oportunidades(arquivo, area, usuario)
                res.update(status="importado", inseridos=ins, ignorados=ign, erros=err)
                if ins > 0:
                    registrar_upload_historico("oportunidades (drive)", ins, usuario)
        except Exception as e:
            logger.error("Falha ao sincronizar área %s: %s", area, e)
            res.update(status="erro", mensagem=str(e)[:500])
        _registrar_log(**res)
        resultados.append(res)

    conn.close()
    return resultados


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if not os.environ.get("DATABASE_URL"):
        sys.exit("DATABASE_URL não configurada.")
    if not credenciais_configuradas():
        sys.exit("GDRIVE_SA_JSON não configurada.")

    resultados = sincronizar()
    if not resultados:
        print("Nenhuma fonte ativa cadastrada em drive_sync_fontes.")
    for r in resultados:
        print(f"[{r['status']}] {r['area']}: inseridos/atualizados={r.get('inseridos', 0)} "
              f"ignorados={r.get('ignorados', 0)} erros={r.get('erros', 0)} {r.get('mensagem') or ''}")
    if any(r["status"] == "erro" for r in resultados):
        sys.exit(1)
