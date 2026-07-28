"""
Reference data from Sienge for PO form dropdowns.
"""
import logging
import os

import psycopg2

logger = logging.getLogger(__name__)


def _connect():
    return psycopg2.connect(
        host=os.environ.get("CASHFLOW_DB_HOST", "186.195.54.70"),
        port=int(os.environ.get("CASHFLOW_DB_PORT", "20000")),
        dbname=os.environ.get("CASHFLOW_DB_NAME", "sienge"),
        user=os.environ.get("CASHFLOW_DB_USER", "cashflow_app"),
        password=os.environ.get("CASHFLOW_DB_PASSWORD", ""),
        connect_timeout=5,
    )


def get_departments() -> dict:
    """
    Returns {department_id: department_name} — IDS-relevant departments only.
    IDs confirmed from Sienge replica on 2026-07-28.
    """
    return {
        11: "PRODUTOS",
        12: "IDS SERVICE",
    }


def get_obras() -> list:
    """
    Returns [{id, name}] of active obras (cost_centers with is_active=true),
    ordered by name. Used to populate the Obra dropdown.
    """
    try:
        conn = _connect()
        with conn, conn.cursor() as cur:
            cur.execute("""
                SELECT id, name
                FROM cost_centers
                WHERE is_active = true
                ORDER BY name
            """)
            return [{"id": row[0], "name": row[1]} for row in cur.fetchall()]
    except Exception:
        logger.exception("sienge_db.get_obras failed")
        return []


def get_obra_cost_centers_map() -> dict:
    """
    Returns {obra_id: [{id, name}]} — all associated cost centers per obra.
    Used to pre-load the cascading cost center dropdown via JS.
    """
    try:
        conn = _connect()
        with conn, conn.cursor() as cur:
            cur.execute("""
                SELECT id, raw_data->'associatedCostCenters'
                FROM cost_centers
                WHERE is_active = true
                  AND raw_data IS NOT NULL
            """)
            result = {}
            for obra_id, assoc in cur.fetchall():
                if not assoc:
                    continue
                result[obra_id] = [
                    {"id": cc["id"], "name": cc.get("name", "")}
                    for cc in assoc
                    if cc.get("id") is not None
                ]
            return result
    except Exception:
        logger.exception("sienge_db.get_obra_cost_centers_map failed")
        return {}


def get_payment_categories() -> dict:
    """
    Returns {category_id: category_name} for financial categories under
    2.01.01.01 (COMPRAS MERCADORIAS). In Sienge the IDs have no dots:
    2.01.01.01 = '2010101', children have parent_id = '2010101'.
    """
    try:
        conn = _connect()
        with conn, conn.cursor() as cur:
            cur.execute("""
                SELECT id, name
                FROM financial_categories
                WHERE parent_id = '2010101'
                  AND is_active = true
                  AND name IS NOT NULL
                ORDER BY id
            """)
            return {row[0]: row[1] for row in cur.fetchall()}
    except Exception:
        logger.exception("sienge_db.get_payment_categories failed")
        return {}
