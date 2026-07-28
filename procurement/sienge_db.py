"""
Queries the Sienge PostgreSQL replica for reference data used in PO forms.

Requires CASHFLOW_DB_PASSWORD env var (same credential as kpi_ebm/db).
Fails gracefully on connection errors so form loads still work.
"""
import logging
import os

import psycopg2

logger = logging.getLogger(__name__)

_CONN_PARAMS = dict(
    host="186.195.54.70",
    port=20000,
    dbname="sienge",
    user="cashflow_app",
    connect_timeout=5,
)


def _connect():
    return psycopg2.connect(**_CONN_PARAMS, password=os.environ.get("CASHFLOW_DB_PASSWORD", ""))


def get_departments() -> dict:
    """
    Returns {department_id: department_name} from Sienge replica.
    Used to populate the Department dropdown in the PO form.
    """
    try:
        conn = _connect()
        with conn, conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT department_id, department_name
                FROM department_appropriations
                WHERE department_id IS NOT NULL
                  AND department_name IS NOT NULL
                ORDER BY department_name
            """)
            return {row[0]: row[1] for row in cur.fetchall()}
    except Exception:
        logger.exception("sienge_db.get_departments failed")
        return {}


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
