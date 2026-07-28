"""
Modelos SQLAlchemy — Cashflow PostgreSQL.

Para criar todas as tabelas no banco:
    from db.models import Base
    from db.engine import engine
    Base.metadata.create_all(engine)
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Numeric, Date, DateTime, Boolean, Text,
    ForeignKey, Index, UniqueConstraint, CheckConstraint, func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship, Mapped, mapped_column

Base = declarative_base()


# ============================================================================
# MOEDAS
# ============================================================================

class Currency(Base):
    """Moedas suportadas — tabela lookup para garantir integridade referencial."""
    __tablename__ = "currencies"

    code = Column(String(3), primary_key=True)  # BRL, USD, CLP, MXN, etc.


# ============================================================================
# TAXAS DE CÂMBIO
# ============================================================================

class FxRate(Base):
    """Taxas de câmbio diárias (base USD)."""
    __tablename__ = "fx_rates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[datetime] = mapped_column(Date, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    rate: Mapped[float] = mapped_column(Numeric(20, 6), nullable=False)  # unidades de moeda por 1 USD

    __table_args__ = (
        UniqueConstraint("date", "currency", name="uq_fx_date_currency"),
        Index("ix_fx_date", "date"),
    )


# ============================================================================
# CONTROLE DE IMPORTAÇÃO
# ============================================================================

class Import(Base):
    """Registro de cada importação de dados do Sienge."""
    __tablename__ = "imports"

    id: Mapped[int] = mapped_column(primary_key=True)
    started_at : Mapped[datetime | None] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running")  # running / success / error
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relações
    details = relationship("ImportDetail", back_populates="import_record", cascade="all, delete-orphan")
    bank_movements = relationship("BankMovement", back_populates="import_record", cascade="all, delete-orphan")
    accounts_payable = relationship("AccountPayable", back_populates="import_record", cascade="all, delete-orphan")
    accounts_receivable = relationship("AccountReceivable", back_populates="import_record", cascade="all, delete-orphan")
    account_balances = relationship("AccountBalance", back_populates="import_record", cascade="all, delete-orphan")


class ImportDetail(Base):
    """Detalhes por tabela de cada importação."""
    __tablename__ = "import_details"

    id = Column(Integer, primary_key=True)
    import_id = Column(Integer, ForeignKey("imports.id", ondelete="CASCADE"), nullable=False, index=True)
    table_name = Column(String(50), nullable=False)
    record_count = Column(Integer, default=0)
    status = Column(String(20), nullable=False, default="running")
    error_message = Column(Text)

    import_record = relationship("Import", back_populates="details")


# ============================================================================
# DIMENSÕES
# ============================================================================

class Company(Base):
    """Empresas do grupo EBM."""
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)  # companyId do Sienge
    name = Column(String(200), nullable=False)
    short_name = Column(String(50))
    group_id = Column(Integer)  # 1=Brasil, 2=LATAM, 3=Outros
    currency = Column(String(3))

    # Relações
    bank_movements = relationship("BankMovement", back_populates="company")
    accounts_payable = relationship("AccountPayable", back_populates="company")
    accounts_receivable = relationship("AccountReceivable", back_populates="company")
    account_balances = relationship("AccountBalance", back_populates="company")


class FinancialCategory(Base):
    """Plano financeiro / plano de contas."""
    __tablename__ = "financial_categories"

    id = Column(String(20), primary_key=True)  # Código ex: "101010101"
    name = Column(String(200))
    parent_id = Column(String(20), ForeignKey("financial_categories.id"))
    level = Column(Integer)
    is_totalizer = Column(Boolean, default=False)
    is_reducer = Column(Boolean, default=False)
    is_tax = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # Relações
    parent = relationship("FinancialCategory", remote_side=[id], backref="children")
    financial_appropriations = relationship("FinancialAppropriation", back_populates="category")


class CostCenter(Base):
    """Centros de custo / Obras (cost_center_dict.json)."""
    __tablename__ = "cost_centers"

    id = Column(Integer, primary_key=True)  # costCenterId do Sienge
    name = Column(String(300), nullable=False)
    commercial_name = Column(String(300))
    cnpj = Column(String(20))
    type = Column(String(5))  # 1=Empreendimento, 2=Obra, etc.
    address = Column(String(200))
    company_id = Column(Integer, ForeignKey("companies.id"))
    building_status = Column(String(30))  # IN_PROGRESS, FINISHED, etc.
    cost_database_id = Column(Integer)
    cost_database_description = Column(String(100))
    building_type_id = Column(Integer)
    building_type_description = Column(String(100))
    is_active = Column(Boolean, default=True)
    raw_data = Column(JSONB)

    # Relações
    company = relationship("Company")
    building_appropriations = relationship("BuildingAppropriation",
        primaryjoin="foreign(BuildingAppropriation.building_id)==CostCenter.id",
        viewonly=True)


class Enterprise(Base):
    """Empreendimentos (api_cost-enterprises.json)."""
    __tablename__ = "enterprises"

    id = Column(Integer, primary_key=True)
    name = Column(String(300), nullable=False)
    commercial_name = Column(String(300))
    cnpj = Column(String(20))
    type = Column(String(5))
    address = Column(String(200))
    company_id = Column(Integer, ForeignKey("companies.id"))
    company_name = Column(String(200))
    cost_database_id = Column(Integer)
    cost_database_description = Column(String(100))
    building_type_id = Column(Integer)
    building_type_description = Column(String(100))
    observation = Column(Text)
    is_active = Column(Boolean, default=True)
    raw_data = Column(JSONB)

    # Relações
    company = relationship("Company")


# ============================================================================
# FATOS — MOVIMENTAÇÕES BANCÁRIAS (HISTÓRICO)
# ============================================================================

class BankMovement(Base):
    """Movimentações bancárias realizadas."""
    __tablename__ = "bank_movements"

    id = Column(Integer, primary_key=True)
    import_id = Column(Integer, ForeignKey("imports.id", ondelete="CASCADE"), nullable=False, index=True)
    movement_id = Column(Integer, nullable=False)  # bankMovementId
    movement_date = Column(Date, nullable=False)
    bill_date = Column(Date)
    amount = Column(Numeric(15, 2))
    operation_type = Column(String(1))  # E=Entrada, S=Saída
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    bill_id = Column(Integer)
    installment_id = Column(Integer)
    creditor_id = Column(Integer)
    creditor_name = Column(String(200))
    client_id = Column(Integer)
    client_name = Column(String(200))
    document_type_id = Column(String(10))
    document_type_name = Column(String(100))
    document_number = Column(String(50))
    historic_name = Column(String(100))
    account_number = Column(String(50))
    notes = Column(Text)
    raw_data = Column(JSONB)

    # Relações
    import_record = relationship("Import", back_populates="bank_movements")
    company = relationship("Company", back_populates="bank_movements")
    financial_appropriations = relationship("FinancialAppropriation",
        primaryjoin="and_(FinancialAppropriation.source_table=='bank_movements', "
                    "foreign(FinancialAppropriation.source_id)==BankMovement.id)",
        viewonly=True)
    department_appropriations = relationship("DepartmentAppropriation",
        primaryjoin="and_(DepartmentAppropriation.source_table=='bank_movements', "
                    "foreign(DepartmentAppropriation.source_id)==BankMovement.id)",
        viewonly=True)
    building_appropriations = relationship("BuildingAppropriation",
        primaryjoin="and_(BuildingAppropriation.source_table=='bank_movements', "
                    "foreign(BuildingAppropriation.source_id)==BankMovement.id)",
        viewonly=True)

    __table_args__ = (
        UniqueConstraint("movement_id", "import_id", name="uq_bank_movement_import"),
        Index("ix_bank_movements_date", "movement_date"),
        Index("ix_bank_movements_company_date", "company_id", "movement_date"),
        Index("ix_bank_movements_bill", "bill_id"),
    )


# ============================================================================
# FATOS — CONTAS A PAGAR (FORECAST)
# ============================================================================

class AccountPayable(Base):
    """Títulos do contas a pagar."""
    __tablename__ = "accounts_payable"

    id = Column(Integer, primary_key=True)
    import_id = Column(Integer, ForeignKey("imports.id", ondelete="CASCADE"), nullable=False, index=True)
    bill_id = Column(Integer, nullable=False)
    installment_id = Column(Integer, nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    creditor_id = Column(Integer)
    creditor_name = Column(String(200))
    document_type_id = Column(String(10))
    document_type_name = Column(String(100))
    document_number = Column(String(50))
    is_forecast = Column(Boolean, default=False)
    due_date = Column(Date)
    issue_date = Column(Date)
    bill_date = Column(Date)
    original_amount = Column(Numeric(15, 2))
    balance_amount = Column(Numeric(15, 2))
    corrected_amount = Column(Numeric(15, 2))
    discount_amount = Column(Numeric(15, 2))
    tax_amount = Column(Numeric(15, 2))
    authorization_status = Column(String(20))
    raw_data = Column(JSONB)

    # Relações
    import_record = relationship("Import", back_populates="accounts_payable")
    company = relationship("Company", back_populates="accounts_payable")
    financial_appropriations = relationship("FinancialAppropriation",
        primaryjoin="and_(FinancialAppropriation.source_table=='accounts_payable', "
                    "foreign(FinancialAppropriation.source_id)==AccountPayable.id)",
        viewonly=True)
    department_appropriations = relationship("DepartmentAppropriation",
        primaryjoin="and_(DepartmentAppropriation.source_table=='accounts_payable', "
                    "foreign(DepartmentAppropriation.source_id)==AccountPayable.id)",
        viewonly=True)
    building_appropriations = relationship("BuildingAppropriation",
        primaryjoin="and_(BuildingAppropriation.source_table=='accounts_payable', "
                    "foreign(BuildingAppropriation.source_id)==AccountPayable.id)",
        viewonly=True)

    __table_args__ = (
        UniqueConstraint("bill_id", "installment_id", "import_id", name="uq_payable_bill_import"),
        Index("ix_payable_due_date", "due_date"),
        Index("ix_payable_company_due", "company_id", "due_date"),
        Index("ix_payable_forecast", "is_forecast"),
    )


# ============================================================================
# FATOS — CONTAS A RECEBER (FORECAST)
# ============================================================================

class AccountReceivable(Base):
    """Títulos do contas a receber."""
    __tablename__ = "accounts_receivable"

    id = Column(Integer, primary_key=True)
    import_id = Column(Integer, ForeignKey("imports.id", ondelete="CASCADE"), nullable=False, index=True)
    bill_id = Column(Integer, nullable=False)
    installment_id = Column(Integer, nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    client_id = Column(Integer)
    client_name = Column(String(200))
    document_type_id = Column(String(10))
    document_type_name = Column(String(100))
    document_number = Column(String(50))
    is_forecast = Column(Boolean, default=False)
    due_date = Column(Date)
    issue_date = Column(Date)
    bill_date = Column(Date)
    original_amount = Column(Numeric(15, 2))
    balance_amount = Column(Numeric(15, 2))
    corrected_amount = Column(Numeric(15, 2))
    discount_amount = Column(Numeric(15, 2))
    tax_amount = Column(Numeric(15, 2))
    bearer_id = Column(Integer)
    raw_data = Column(JSONB)

    # Relações
    import_record = relationship("Import", back_populates="accounts_receivable")
    company = relationship("Company", back_populates="accounts_receivable")
    financial_appropriations = relationship("FinancialAppropriation",
        primaryjoin="and_(FinancialAppropriation.source_table=='accounts_receivable', "
                    "foreign(FinancialAppropriation.source_id)==AccountReceivable.id)",
        viewonly=True)
    department_appropriations = relationship("DepartmentAppropriation",
        primaryjoin="and_(DepartmentAppropriation.source_table=='accounts_receivable', "
                    "foreign(DepartmentAppropriation.source_id)==AccountReceivable.id)",
        viewonly=True)
    building_appropriations = relationship("BuildingAppropriation",
        primaryjoin="and_(BuildingAppropriation.source_table=='accounts_receivable', "
                    "foreign(BuildingAppropriation.source_id)==AccountReceivable.id)",
        viewonly=True)

    __table_args__ = (
        UniqueConstraint("bill_id", "installment_id", "import_id", name="uq_receivable_bill_import"),
        Index("ix_receivable_due_date", "due_date"),
        Index("ix_receivable_company_due", "company_id", "due_date"),
        Index("ix_receivable_forecast", "is_forecast"),
    )


# ============================================================================
# FATOS — SALDOS DE CONTAS
# ============================================================================

class AccountBalance(Base):
    """Saldos de contas correntes."""
    __tablename__ = "account_balances"

    id = Column(Integer, primary_key=True)
    import_id = Column(Integer, ForeignKey("imports.id", ondelete="CASCADE"), nullable=False, index=True)
    account_number = Column(String(50), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    balance_date = Column(Date, nullable=False)
    amount = Column(Numeric(15, 2))
    reconciled_amount = Column(Numeric(15, 2))
    account_status = Column(String(10))  # ENABLED / DISABLED
    raw_data = Column(JSONB)

    # Relações
    import_record = relationship("Import", back_populates="account_balances")
    company = relationship("Company", back_populates="account_balances")

    __table_args__ = (
        UniqueConstraint("account_number", "company_id", "balance_date", "import_id",
                        name="uq_balance_account_import"),
        Index("ix_balance_date", "balance_date"),
        Index("ix_balance_company", "company_id"),
        Index("ix_balance_account", "account_number"),
    )


# ============================================================================
# APROPRIAÇÕES (normalizadas dos arrays internos)
# ============================================================================

class FinancialAppropriation(Base):
    """Apropriações financeiras (plano de contas)."""
    __tablename__ = "financial_appropriations"

    id = Column(Integer, primary_key=True)
    source_table = Column(String(30), nullable=False)  # bank_movements / accounts_payable / accounts_receivable
    source_id = Column(Integer, nullable=False)
    bill_id = Column(Integer)
    installment_id = Column(Integer)
    category_id = Column(String(20), ForeignKey("financial_categories.id"))
    category_name = Column(String(200))
    rate = Column(Numeric(15, 12))

    # Relações
    category = relationship("FinancialCategory", back_populates="financial_appropriations")

    __table_args__ = (
        Index("ix_fin_approp_source", "source_table", "source_id"),
        Index("ix_fin_approp_category", "category_id"),
    )


class DepartmentAppropriation(Base):
    """Apropriações por departamento."""
    __tablename__ = "department_appropriations"

    id = Column(Integer, primary_key=True)
    source_table = Column(String(30), nullable=False)
    source_id = Column(Integer, nullable=False)
    department_id = Column(Integer)
    department_name = Column(String(200))
    rate = Column(Numeric(15, 12))

    __table_args__ = (
        Index("ix_dept_approp_source", "source_table", "source_id"),
    )


class BuildingAppropriation(Base):
    """Apropriações por obra."""
    __tablename__ = "building_appropriations"

    id = Column(Integer, primary_key=True)
    source_table = Column(String(30), nullable=False)
    source_id = Column(Integer, nullable=False)
    building_id = Column(Integer)
    building_name = Column(String(200))
    rate = Column(Numeric(15, 12))

    __table_args__ = (
        Index("ix_bldg_approp_source", "source_table", "source_id"),
    )


# ============================================================================
# CACHE DE ENRIQUECIMENTO
# ============================================================================

class MeasurementInfo(Base):
    """Cache de enriquecimento de medições (issue_date e document via API Sienge)."""
    __tablename__ = "measurement_info"

    contract_number    = Column(String(50), primary_key=True)  # "CTC/2026/26"
    building_id        = Column(Integer,    primary_key=True)
    measurement_number = Column(Integer,    primary_key=True)
    measurement_date   = Column(Date)
    due_date           = Column(Date)
    issue_date         = Column(Date, nullable=True)   # None = NF ainda não emitida
    document           = Column(String(50), nullable=True)  # ex: "FAT/285"
    fetched_at         = Column(DateTime, server_default=func.now())


class ContractResponsible(Base):
    """Cache do responsável por contrato (supply-contracts ou purchase-orders)."""
    __tablename__ = "contract_responsibles"

    document_id     = Column(String(10), primary_key=True)   # CT, PPC, CTC, ...
    contract_number = Column(String(50), primary_key=True)   # "467", "2299", "25_0594_01"
    responsible     = Column(String(200))                    # responsibleName ou buyerId
    email           = Column(String(200))                    # email via /v1/users
    fetched_at      = Column(DateTime, server_default=func.now())

# ============================================================================
# CONTRATOS COM CLIENTES (supply-contracts/all)
# ============================================================================

class SupplyContract(Base):
    """Cache de contratos com clientes, espelhando /v1/supply-contracts/all."""
    __tablename__ = "supply_contracts"

    document_id               = Column(String(10),  primary_key=True)   # ADC, CTC, CT, …
    contract_number           = Column(String(50),  primary_key=True)   # "25_0663_12"
    supplier_id               = Column(Integer,     nullable=True)
    supplier_name             = Column(String(300), nullable=True)
    customer_id               = Column(Integer,     nullable=True)
    company_id                = Column(Integer,     nullable=True)
    company_name              = Column(String(300), nullable=True)
    responsible_id            = Column(String(100), nullable=True)
    responsible_name          = Column(String(300), nullable=True)
    status                    = Column(String(50),  nullable=True)
    status_approval           = Column(String(50),  nullable=True)
    is_authorized             = Column(Boolean,     nullable=True)
    contract_date             = Column(Date,        nullable=True)
    start_date                = Column(Date,        nullable=True)
    end_date                  = Column(Date,        nullable=True)
    object                    = Column(Text,        nullable=True)
    internal_notes            = Column(Text,        nullable=True)
    contract_type             = Column(String(50),  nullable=True)
    registration_type         = Column(String(50),  nullable=True)
    item_type                 = Column(String(50),  nullable=True)
    total_labor_value         = Column(Numeric(18, 2), nullable=True)
    total_material_value      = Column(Numeric(18, 2), nullable=True)
    consistent                = Column(Boolean,     nullable=True)
    buildings                 = Column(JSONB,       nullable=True)   # [{buildingId, name}, …]
    contract_template_id      = Column(Integer,     nullable=True)
    contract_template_name    = Column(String(300), nullable=True)
    current_authorization_level = Column(String(50), nullable=True)
    fetched_at                = Column(DateTime,    server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_supply_contracts_company",  "company_id"),
        Index("ix_supply_contracts_customer", "customer_id"),
        Index("ix_supply_contracts_status",   "status"),
    )


# ============================================================================
# IMPORTAÇÃO MANUAL (planilhas)
# ============================================================================


class ManualImport(Base):
    """Cabeçalho de cada importação manual de planilha."""
    __tablename__ = "manual_imports"

    id: Mapped[int] = mapped_column(primary_key=True)
    import_date: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    obra_id: Mapped[int | None] = mapped_column(ForeignKey("cost_centers.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(10), nullable=False)  # override, merge, ignore
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    obra = relationship("CostCenter")
    details = relationship("ManualImportDetail", back_populates="manual_import",
                           cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("action IN ('override', 'merge', 'ignore')", name="ck_manual_import_action"),
        Index("ix_manual_imports_obra", "obra_id"),
    )


class ManualImportDetail(Base):
    """Linhas de cada importação manual (ex-eng_import)."""
    __tablename__ = "manual_import_details"

    id: Mapped[int] = mapped_column(primary_key=True)
    import_id: Mapped[int] = mapped_column(ForeignKey("manual_imports.id", ondelete="CASCADE"), nullable=False, index=True)
    data: Mapped[datetime] = mapped_column(Date, nullable=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    empresa: Mapped[str | None] = mapped_column(String(200), nullable=True)
    contraparte: Mapped[str | None] = mapped_column(String(200), nullable=True)
    valor: Mapped[float | None] = mapped_column(Numeric(20, 2), nullable=True)
    currency: Mapped[str | None] = mapped_column(ForeignKey("currencies.code"), nullable=True)
    tipo_de_documento: Mapped[str | None] = mapped_column(String(50), nullable=True)
    plano_financeiro: Mapped[str | None] = mapped_column(ForeignKey("financial_categories.id"), nullable=True)
    nome_plano_financeiro: Mapped[str | None] = mapped_column(String(200), nullable=True)
    cost_center_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    nome_centro_de_custo: Mapped[str | None] = mapped_column(String(200), nullable=True)

    manual_import = relationship("ManualImport", back_populates="details")
    company = relationship("Company")

    __table_args__ = (
        Index("ix_manual_import_details_data", "data"),
        Index("ix_manual_import_details_company", "company_id"),
    )
