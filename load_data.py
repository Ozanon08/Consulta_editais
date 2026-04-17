from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import pandas as pd

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "editais.db"
XLSX_PATH = APP_DIR / "Modelo dados.xlsx"
SCHEMA_PATH = APP_DIR / "schema.sql"

COLUMN_MAP = {
    "Tema": "tema",
    "Subtema": "subtema",
    "Serviços": "servicos",
    "País": "pais",
    "Estado": "estado",
    "Município": "municipio",
    "Nome Edital": "nome_edital",
    "Descrição": "descricao",
    "Esforço": "esforco",
    "Unidade": "unidade",
    "Prazo (meses)": "prazo_meses",
    "Tipo de Edital": "tipo_edital",
    "Código Planilha": "codigo_planilha",
    "Fonte de Dados": "fonte_dado",
    "OBS": "observacao",
    "Custo de Execução": "custo_execucao",
    "Data edital (mês/ano)": "data_edital",
    "Min": "valor_min",
    "Máx": "valor_max",
}


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def normalize_service_tokens(value: str) -> list[str]:
    if not value or pd.isna(value):
        return []
    text = str(value).strip().rstrip(".")
    if text == "-":
        return []
    separators = [",", ";", "|", " / ", "\\n"]
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


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns=COLUMN_MAP).copy()
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = (
                df[col]
                .astype(str)
                .str.strip()
                .replace({"nan": None, "None": None, "": None})
            )
    for col in ["prazo_meses", "custo_execucao", "valor_min", "valor_max"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "data_edital" in df.columns:
        dt = pd.to_datetime(df["data_edital"], errors="coerce", dayfirst=True)
        mask = dt.notna()
        df.loc[mask, "data_edital"] = dt.loc[mask].dt.strftime("%Y-%m")
    return df


def run() -> None:
    df = pd.read_excel(XLSX_PATH, sheet_name="Base")
    df = normalize_dataframe(df)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    cur = conn.cursor()
    cur.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

    for table in [
        "edital_servico", "edital", "servico", "fonte_dado", "unidade", "tipo_edital",
        "municipio", "estado", "pais", "subtema", "tema"
    ]:
        cur.execute(f"DELETE FROM {table}")

    def upsert_lookup(table: str, nome: str | None) -> int | None:
        if not nome:
            return None
        row = cur.execute(f"SELECT id FROM {table} WHERE nome = ?", (nome,)).fetchone()
        if row:
            return row[0]
        cur.execute(f"INSERT INTO {table} (nome) VALUES (?)", (nome,))
        return cur.lastrowid

    tema_map = {}
    subtema_map = {}
    pais_map = {}
    estado_map = {}
    municipio_map = {}
    tipo_map = {}
    unidade_map = {}
    fonte_map = {}
    servico_map = {}

    for _, row in df.iterrows():
        tema_id = None
        if row.get("tema"):
            tema_id = tema_map.get(row["tema"])
            if tema_id is None:
                tema_id = upsert_lookup("tema", row["tema"])
                tema_map[row["tema"]] = tema_id

        subtema_id = None
        if row.get("subtema"):
            key = (tema_id, row["subtema"])
            subtema_id = subtema_map.get(key)
            if subtema_id is None:
                found = cur.execute(
                    "SELECT id FROM subtema WHERE tema_id IS ? AND nome IS ?",
                    (tema_id, row["subtema"]),
                ).fetchone()
                if found:
                    subtema_id = found[0]
                else:
                    cur.execute("INSERT INTO subtema (tema_id, nome) VALUES (?, ?)", (tema_id, row["subtema"]))
                    subtema_id = cur.lastrowid
                subtema_map[key] = subtema_id

        pais_id = None
        if row.get("pais"):
            pais_id = pais_map.get(row["pais"])
            if pais_id is None:
                pais_id = upsert_lookup("pais", row["pais"])
                pais_map[row["pais"]] = pais_id

        estado_id = None
        if row.get("estado"):
            estado_id = estado_map.get(row["estado"])
            if estado_id is None:
                found = cur.execute("SELECT id FROM estado WHERE nome = ?", (row["estado"],)).fetchone()
                if found:
                    estado_id = found[0]
                else:
                    cur.execute("INSERT INTO estado (pais_id, nome) VALUES (?, ?)", (pais_id, row["estado"]))
                    estado_id = cur.lastrowid
                estado_map[row["estado"]] = estado_id

        municipio_id = None
        if row.get("municipio"):
            key = (estado_id, row["municipio"])
            municipio_id = municipio_map.get(key)
            if municipio_id is None:
                found = cur.execute(
                    "SELECT id FROM municipio WHERE estado_id IS ? AND nome IS ?",
                    (estado_id, row["municipio"]),
                ).fetchone()
                if found:
                    municipio_id = found[0]
                else:
                    cur.execute("INSERT INTO municipio (estado_id, nome) VALUES (?, ?)", (estado_id, row["municipio"]))
                    municipio_id = cur.lastrowid
                municipio_map[key] = municipio_id

        tipo_id = tipo_map.get(row.get("tipo_edital")) if row.get("tipo_edital") else None
        if row.get("tipo_edital") and tipo_id is None:
            tipo_id = upsert_lookup("tipo_edital", row["tipo_edital"])
            tipo_map[row["tipo_edital"]] = tipo_id

        unidade_id = unidade_map.get(row.get("unidade")) if row.get("unidade") else None
        if row.get("unidade") and unidade_id is None:
            unidade_id = upsert_lookup("unidade", row["unidade"])
            unidade_map[row["unidade"]] = unidade_id

        fonte_id = fonte_map.get(row.get("fonte_dado")) if row.get("fonte_dado") else None
        if row.get("fonte_dado") and fonte_id is None:
            fonte_id = upsert_lookup("fonte_dado", row["fonte_dado"])
            fonte_map[row["fonte_dado"]] = fonte_id

        cur.execute(
            """
            INSERT INTO edital (
                tema_id, subtema_id, pais_id, estado_id, municipio_id, nome_edital,
                descricao, esforco, unidade_id, prazo_meses, tipo_edital_id,
                codigo_planilha, fonte_dado_id, observacao, custo_execucao,
                data_edital, metodo_calculo, valor_min, valor_max
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tema_id, subtema_id, pais_id, estado_id, municipio_id, row.get("nome_edital"),
                row.get("descricao"), row.get("esforco"), unidade_id,
                None if pd.isna(row.get("prazo_meses")) else float(row.get("prazo_meses")),
                tipo_id, row.get("codigo_planilha"), fonte_id, row.get("observacao"),
                None if pd.isna(row.get("custo_execucao")) else float(row.get("custo_execucao")),
                row.get("data_edital"), row.get("metodo_calculo"),
                None if pd.isna(row.get("valor_min")) else float(row.get("valor_min")),
                None if pd.isna(row.get("valor_max")) else float(row.get("valor_max")),
            ),
        )
        edital_id = cur.lastrowid

        for serv in normalize_service_tokens(row.get("servicos")):
            servico_id = servico_map.get(serv)
            if servico_id is None:
                servico_id = upsert_lookup("servico", serv)
                servico_map[serv] = servico_id
            cur.execute("INSERT OR IGNORE INTO edital_servico (edital_id, servico_id) VALUES (?, ?)", (edital_id, servico_id))

    cur.execute(
        "INSERT OR IGNORE INTO user_account (username, display_name, password_hash, role, is_active) VALUES (?, ?, ?, ?, 1)",
        ("ADMIN", "Administrador", hash_password("ADMIN123"), "ADMIN"),
    )

    conn.commit()
    conn.close()
    print("Banco criado com sucesso em", DB_PATH)
    print("Usuário inicial: ADMIN | Senha inicial: ADMIN123")


if __name__ == "__main__":
    run()
