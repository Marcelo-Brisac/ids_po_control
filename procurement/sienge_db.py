"""
Queries the Sienge PostgreSQL replica for reference data used in PO forms.

Requires CASHFLOW_DB_PASSWORD env var (same credential as kpi_ebm/db).
Fails gracefully on connection errors so form loads still work.
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
    Returns {department_id: department_name} — only IDS-relevant departments.
    IDs confirmed from Sienge replica on 2026-07-28.
    """
    return {
        11: "PRODUTOS",
        12: "IDS SERVICE",
    }


def get_payment_categories() -> dict:
    """
    Returns {category_id: category_name} for financial categories
    that are children of the 2.01.01.01 group (procurement group).
    Used to populate the Payment Category dropdown in the PO form.
    """
    try:
        conn = _connect()
        with conn, conn.cursor() as cur:
            # Find direct children of any parent whose id or name starts with 2.01.01.01
            cur.execute("""
                SELECT fc.id, fc.name
                FROM financial_categories fc
                WHERE fc.is_active = true
                  AND fc.name IS NOT NULL
                  AND fc.parent_id IN (
                      SELECT id
                      FROM financial_categories
                      WHERE id ILIKE '2.01.01.01%'
                         OR name ILIKE '2.01.01.01%'
                  )
                ORDER BY fc.id
            """)
            return {row[0]: row[1] for row in cur.fetchall()}
    except Exception:
        logger.exception("sienge_db.get_payment_categories failed")
        return {}
