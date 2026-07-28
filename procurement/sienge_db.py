"""
Reference data from Sienge for PO form dropdowns.
"""
import logging
import os

import psycopg2

logger = logging.getLogger(__name__)


def get_departments() -> dict:
    """
    Returns {department_id: department_name} — IDS-relevant departments only.
    IDs confirmed from Sienge replica on 2026-07-28.
    """
    return {
        11: "PRODUTOS",
        12: "IDS SERVICE",
    }


def get_payment_categories() -> dict:
    """
    Returns {category_id: category_name} for financial categories under
    2.01.01.01 (COMPRAS MERCADORIAS). In Sienge the IDs have no dots:
    2.01.01.01 = '2010101', children have parent_id = '2010101'.
    """
    try:
        conn = psycopg2.connect(
            host=os.environ.get("CASHFLOW_DB_HOST", "186.195.54.70"),
            port=int(os.environ.get("CASHFLOW_DB_PORT", "20000")),
            dbname=os.environ.get("CASHFLOW_DB_NAME", "sienge"),
            user=os.environ.get("CASHFLOW_DB_USER", "cashflow_app"),
            password=os.environ.get("CASHFLOW_DB_PASSWORD", ""),
            connect_timeout=5,
        )
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
