"""
db/queries.py — Acesso centralizado ao banco Sienge.

Padrão de snapshot para tabelas importadas (accounts_receivable, accounts_payable,
bank_movements): cada import é um snapshot completo do estado do Sienge naquela data.
O import mais recente anterior a as_of_date contém todos os registros ativos; registros
ausentes foram removidos/cancelados no Sienge.

Query correta: WHERE import_id = (SELECT MAX(id) FROM imports WHERE finished_at::date <= as_of_date)

Nunca usar GROUP BY bill_id/movement_id com MAX(import_id) — isso traz registros
fantasma de imports antigos.

Nenhum outro módulo deve instanciar Session ou escrever ORM/SQL diretamente.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import func

from db.engine import get_session
from db.models import (
    AccountPayable,
    AccountReceivable,
    BankMovement,
    Company,
    CostCenter,
    DepartmentAppropriation,
    FinancialCategory,
    FxRate,
    Import,
    SupplyContract,
)


# ── Helpers internos ─────────────────────────────────────────────────────────

def _to_dict(row) -> dict:
    """Converte instância ORM em dict simples com todos os campos da tabela."""
    return {c.name: getattr(row, c.name) for c in row.__table__.columns}


def _latest_import_id(session, effective_date: date):
    """ID do import mais recente finalizado em ou antes de effective_date."""
    return (
        session.query(func.max(Import.id))
        .filter(
            Import.finished_at.isnot(None),
            func.date(Import.finished_at) <= effective_date,
        )
        .scalar_subquery()
    )


# ── Contas a receber ─────────────────────────────────────────────────────────

def get_accounts_receivable(
    document_types: set[str] | None = None,
    exclude_client_ids: set[int] | None = None,
    as_of_date: date | None = None,
) -> list[dict]:
    """
    Parcelas de contas a receber na versão mais recente de cada bill.

    Args:
        document_types:     {"PO", "OC", "FAT", ...}; None = todos os tipos
        exclude_client_ids: client_ids a excluir (ex.: intercompany)
        as_of_date:         snapshot histórico; None = hoje
    """
    effective_date = as_of_date if as_of_date is not None else date.today()
    session = get_session()
    try:
        latest_import = _latest_import_id(session, effective_date)
        query = session.query(AccountReceivable).filter(
            AccountReceivable.import_id == latest_import
        )
        if document_types:
            query = query.filter(
                func.trim(AccountReceivable.document_type_id).in_(document_types)
            )
        if exclude_client_ids:
            query = query.filter(
                AccountReceivable.client_id.notin_(exclude_client_ids)
            )
        return [_to_dict(r) for r in query.all()]
    finally:
        session.close()


# ── Contas a pagar ───────────────────────────────────────────────────────────

def get_accounts_payable(
    document_types: set[str] | None = None,
    as_of_date: date | None = None,
) -> list[dict]:
    """
    Parcelas de contas a pagar na versão mais recente de cada bill.

    Args:
        document_types: {"PCT", "PPC", ...}; None = todos os tipos
        as_of_date:     snapshot histórico; None = hoje
    """
    effective_date = as_of_date if as_of_date is not None else date.today()
    session = get_session()
    try:
        latest_import = _latest_import_id(session, effective_date)
        query = session.query(AccountPayable).filter(
            AccountPayable.import_id == latest_import
        )
        if document_types:
            query = query.filter(
                func.trim(AccountPayable.document_type_id).in_(document_types)
            )
        return [_to_dict(r) for r in query.all()]
    finally:
        session.close()


# ── Movimentações bancárias ──────────────────────────────────────────────────

def get_bank_movements(
    date_from: date,
    date_to: date,
    as_of_date: date | None = None,
) -> list[dict]:
    """
    Movimentações bancárias no intervalo [date_from, date_to],
    na versão mais recente de cada movement_id.

    Args:
        date_from:  início do período (movement_date >=)
        date_to:    fim do período (movement_date <=)
        as_of_date: snapshot de qual import usar; None = hoje
    """
    effective_date = as_of_date if as_of_date is not None else date.today()
    session = get_session()
    try:
        latest_import = _latest_import_id(session, effective_date)
        rows = (
            session.query(BankMovement)
            .filter(
                BankMovement.import_id == latest_import,
                BankMovement.movement_date >= date_from,
                BankMovement.movement_date <= date_to,
            )
            .all()
        )
        return [_to_dict(r) for r in rows]
    finally:
        session.close()


# ── Taxas de câmbio ──────────────────────────────────────────────────────────

def get_fx_rates() -> list[dict]:
    """
    Série histórica completa de taxas de câmbio.
    Retorna list[dict] com campos: id, date, currency, rate.
    Usado pelo CurrencyConverter para construir sua pivot table.
    """
    session = get_session()
    try:
        rows = session.query(FxRate).order_by(FxRate.date).all()
        return [_to_dict(r) for r in rows]
    finally:
        session.close()


def get_latest_fx_rates() -> dict[str, Decimal]:
    """
    Última taxa disponível por moeda {currency: rate}.
    Útil para conversões pontuais sem instanciar CurrencyConverter.
    """
    session = get_session()
    try:
        latest_sq = (
            session.query(
                FxRate.currency,
                func.max(FxRate.date).label("max_date"),
            )
            .group_by(FxRate.currency)
            .subquery()
        )
        rows = (
            session.query(FxRate)
            .join(
                latest_sq,
                (FxRate.currency == latest_sq.c.currency)
                & (FxRate.date == latest_sq.c.max_date),
            )
            .all()
        )
        return {r.currency: Decimal(str(r.rate)) for r in rows}
    finally:
        session.close()


# ── Empresas ─────────────────────────────────────────────────────────────────

def get_companies() -> list[dict]:
    """
    Todas as empresas do grupo.
    Campos úteis: id, name, short_name, currency, group_id.
    """
    session = get_session()
    try:
        return [_to_dict(r) for r in session.query(Company).all()]
    finally:
        session.close()


# ── Departamentos ────────────────────────────────────────────────────────────

def get_departments() -> list[str]:
    """
    Departamentos ativos: nomes distintos de department_appropriations,
    excluindo os descontinuados definidos em common.DEPARTAMENTOS_ANTIGOS.
    """
    from common import DEPARTAMENTOS_ANTIGOS

    session = get_session()
    try:
        rows = (
            session.query(DepartmentAppropriation.department_name)
            .filter(DepartmentAppropriation.department_name.isnot(None))
            .distinct()
            .order_by(DepartmentAppropriation.department_name)
            .all()
        )
        antigos = set(DEPARTAMENTOS_ANTIGOS)
        return [r.department_name for r in rows if r.department_name not in antigos]
    finally:
        session.close()


# ── Categorias financeiras ───────────────────────────────────────────────────

def get_financial_categories() -> dict[int, str]:
    """Plano de contas: {código_int: nome}. Exclui códigos não numéricos."""
    session = get_session()
    try:
        result = {}
        for r in session.query(FinancialCategory).all():
            raw_id = str(r.id)
            if raw_id.isdigit() and r.name is not None:
                result[int(raw_id)] = str(r.name)
        return result
    finally:
        session.close()


# ── Obras ────────────────────────────────────────────────────────────────────

def get_obras() -> list[dict]:
    """
    Obras ativas (type='2'), excluindo as da EXCLUDE_LIST de common.py.
    Retorna list[dict] com campos: id, name, commercial_name, building_status.
    """
    from common import EXCLUDE_LIST

    session = get_session()
    try:
        rows = (
            session.query(CostCenter)
            .filter(
                CostCenter.type == "2",
                CostCenter.id.notin_(EXCLUDE_LIST),
            )
            .order_by(CostCenter.id)
            .all()
        )
        return [
            {
                "id": r.id,
                "name": r.name,
                "commercial_name": r.commercial_name,
                "building_status": r.building_status,
            }
            for r in rows
        ]
    finally:
        session.close()


def get_cost_centers_for_obra(obra_id: int) -> list[dict]:
    """
    Centros de custo associados a uma obra.
    Retorna list[dict] com campos: id, name (extraídos de raw_data.associatedCostCenters).
    """
    session = get_session()
    try:
        row = session.get(CostCenter, obra_id)
        if row is None or row.raw_data is None:
            return []
        return [
            {"id": cc["id"], "name": cc["name"]}
            for cc in row.raw_data.get("associatedCostCenters", [])
        ]
    finally:
        session.close()


# ── Contratos de fornecimento ────────────────────────────────────────────────

def get_supply_contracts(
    doc_id: str,
    statuses: list[str] | None = None,
) -> list[dict]:
    """
    Contratos de fornecimento de um tipo de documento.

    Args:
        doc_id:   tipo do documento ("CTC", "CT", "ADC", ...)
        statuses: lista de status; None = todos
    """
    session = get_session()
    try:
        query = session.query(SupplyContract).filter(
            SupplyContract.document_id == doc_id
        )
        if statuses:
            query = query.filter(SupplyContract.status.in_(statuses))
        return [_to_dict(r) for r in query.all()]
    finally:
        session.close()
