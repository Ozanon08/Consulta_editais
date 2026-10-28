"""Importação de oportunidades (editais em aberto) para o banco.

Módulo sem dependência do Streamlit, para ser usado tanto pelo app quanto
pelo job agendado de sincronização com o Google Drive (drive_sync.py).
"""
import logging
import math
import os
from datetime import date, datetime, timedelta, timezone

import pandas as pd
import psycopg2

logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL", "")


def get_conn():
    return psycopg2.connect(DATABASE_URL)


def agora_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def registrar_upload_historico(tipo: str, qtd_registros: int, usuario: str):
    """Registra um upload no historico."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO upload_historico (tipo, qtd_registros, usuario, criado_em)
            VALUES (%s, %s, %s, %s)
        """, (tipo, qtd_registros, usuario, agora_str()))
        conn.commit()
    except Exception:
        conn.rollback()
    finally:
        conn.close()


def _parse_data_oportunidade(val):
    """Converte número serial Excel, datetime, date ou string para date ISO (ou None)."""
    if val is None:
        return None
    # Verifica pd.NaT e outros valores nulos do pandas ANTES de qualquer str()
    try:
        if pd.isnull(val):
            return None
    except Exception:
        pass
    # Tipos nativos Python
    if isinstance(val, datetime):
        return val.date().isoformat()
    if isinstance(val, date):
        return val.isoformat()
    # String: verifica marcadores nulos e faz parse
    if isinstance(val, str):
        s = val.strip()
        if s in ("", "nan", "None", "NaT", "NaN", "NAT", "N/A", "NA", "-"):
            return None
        try:
            parsed = pd.to_datetime(s, dayfirst=False, errors="coerce")
            if pd.isnull(parsed):
                return None
            return parsed.date().isoformat()
        except Exception:
            return None
    # Número serial Excel (int ou float)
    try:
        fval = float(val)
        if math.isnan(fval):
            return None
        return (date(1899, 12, 30) + timedelta(days=int(fval))).isoformat()
    except Exception:
        pass
    # Fallback: tenta converter como string
    try:
        s = str(val).strip()
        if s in ("", "nan", "None", "NaT", "NaN", "NAT", "N/A", "NA", "-"):
            return None
        parsed = pd.to_datetime(s, dayfirst=False, errors="coerce")
        if pd.isnull(parsed):
            return None
        return parsed.date().isoformat()
    except Exception:
        return None


def importar_oportunidades(arquivo, area_importacao: str, usuario: str):
    """Lê planilha Controle-Oportunidades e insere registros em editais_oportunidades.
    Deduplicação por (area, tema, orgao, data_identificacao).
    Retorna (inseridos, ignorados, erros).
    """
    COLUMN_MAP_OPP = {
        "Área": "area",
        "Perfil (A/B/C)": "perfil_aderencia",
        "Tema do edital": "tema",
        "Órgão/empresa publicador": "orgao",
        "Macro escopo do projeto": "macro_escopo",
        "Prazo para submissão": "prazo_submissao",
        "Valor do financiamento (quando disponível)": "valor_financiamento",
        "Status (Novo/Atualização/Encerrado)": "status",
        "Status": "status",
        "Link direto": "link",
        "Data de identificação": "data_identificacao",
        "Semana de referência": "semana_referencia",
    }

    xl = pd.ExcelFile(arquivo)
    sheet = xl.sheet_names[0]
    # Primeira linha já é o cabeçalho (header=0)
    df = pd.read_excel(arquivo, sheet_name=sheet, header=0)
    df = df[[c for c in df.columns if not str(c).startswith("Unnamed:")]]
    df = df.rename(columns=COLUMN_MAP_OPP)

    # Descarta linhas completamente vazias
    df = df.dropna(how="all")

    conn = get_conn()
    conn.autocommit = False
    cur = conn.cursor()
    inseridos = ignorados = erros = 0

    for _, row in df.iterrows():
        # Savepoint por linha: um erro numa linha não aborta a transação das demais
        cur.execute("SAVEPOINT linha_opp")
        try:
            r_area = str(row.get("area", "") or area_importacao or "").strip() or area_importacao
            r_tema = str(row.get("tema", "") or "").strip() or None
            r_orgao = str(row.get("orgao", "") or "").strip() or None
            r_data_id = _parse_data_oportunidade(row.get("data_identificacao"))
            r_semana = _parse_data_oportunidade(row.get("semana_referencia"))
            r_prazo = _parse_data_oportunidade(row.get("prazo_submissao"))

            if not r_tema:
                ignorados += 1
                continue

            r_novo_status = str(row.get("status", "") or "").strip() or None
            r_perfil      = str(row.get("perfil_aderencia", "") or "").strip() or None
            r_escopo      = str(row.get("macro_escopo", "") or "").strip() or None
            r_valor       = str(row.get("valor_financiamento", "") or "").strip() or None
            r_link        = str(row.get("link", "") or "").strip() or None

            # Verifica se já existe (deduplicação por area+tema+orgao+data_id)
            cur.execute("""
                SELECT id, status FROM editais_oportunidades
                WHERE area IS NOT DISTINCT FROM %s
                  AND tema IS NOT DISTINCT FROM %s
                  AND orgao IS NOT DISTINCT FROM %s
                  AND data_identificacao IS NOT DISTINCT FROM %s
            """, (r_area, r_tema, r_orgao, r_data_id))
            existing = cur.fetchone()

            if existing:
                _ex_id, _ex_status = existing
                # Atualiza campos que podem ter mudado
                cur.execute("""
                    UPDATE editais_oportunidades
                    SET perfil_aderencia=%s, macro_escopo=%s, prazo_submissao=%s,
                        valor_financiamento=%s, status=%s, link=%s,
                        semana_referencia=%s, importado_por=%s
                    WHERE id=%s
                """, (r_perfil, r_escopo, r_prazo, r_valor, r_novo_status, r_link, r_semana, usuario, _ex_id))
                # Registra histórico se status mudou
                if r_novo_status and _ex_status != r_novo_status:
                    cur.execute("""
                        INSERT INTO editais_oportunidades_historico
                            (oportunidade_id, status_anterior, status_novo, alterado_por, alterado_em)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (_ex_id, _ex_status, r_novo_status, usuario, agora_str()))
                    inseridos += 1  # conta como atualização
                else:
                    ignorados += 1
            else:
                cur.execute("""
                    INSERT INTO editais_oportunidades
                        (area, perfil_aderencia, tema, orgao, macro_escopo,
                         prazo_submissao, valor_financiamento, status, link,
                         data_identificacao, semana_referencia, criado_em, importado_por)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    RETURNING id
                """, (
                    r_area, r_perfil, r_tema, r_orgao, r_escopo, r_prazo, r_valor,
                    r_novo_status, r_link, r_data_id, r_semana, agora_str(), usuario,
                ))
                new_id = cur.fetchone()[0]
                # Registra status inicial no histórico
                if r_novo_status:
                    cur.execute("""
                        INSERT INTO editais_oportunidades_historico
                            (oportunidade_id, status_anterior, status_novo, alterado_por, alterado_em)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (new_id, None, r_novo_status, usuario, agora_str()))
                inseridos += 1
        except Exception as e:
            logger.warning("Erro ao importar linha de oportunidades: %s", e)
            cur.execute("ROLLBACK TO SAVEPOINT linha_opp")
            erros += 1
            continue

    conn.commit()
    conn.close()
    return inseridos, ignorados, erros
