from django.contrib import admin
from .models import (
    Issuer,
    IssuerEmail,
    BankAccount,
    LegalRepresentative,
    Product,
    Counterparty,
    CounterpartyBankAccount,
    PO,
    POItem,
    POPaymentTerm,
    POGeneratedPDF,
)


class BankAccountInline(admin.StackedInline):
    model = BankAccount
    extra = 1


class IssuerEmailInline(admin.TabularInline):
    model = IssuerEmail
    extra = 1


class LegalRepresentativeInline(admin.TabularInline):
    model = LegalRepresentative.issuers.through
    extra = 1
    verbose_name = "Legal Representative"
    verbose_name_plural = "Legal Representatives"


@admin.register(Issuer)
class IssuerAdmin(admin.ModelAdmin):
    list_display = ["name", "tax_id", "sienge_company_id"]
    search_fields = ["name", "tax_id"]
    inlines = [IssuerEmailInline, BankAccountInline, LegalRepresentativeInline]


@admin.register(LegalRepresentative)
class LegalRepresentativeAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "phone"]
    search_fields = ["name", "email"]
    filter_horizontal = ["issuers"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["code", "description", "financial_category_purchase"]
    search_fields = ["code", "description"]


class CounterpartyBankAccountInline(admin.StackedInline):
    model = CounterpartyBankAccount
    extra = 1


@admin.register(Counterparty)
class CounterpartyAdmin(admin.ModelAdmin):
    list_display = ["name", "tax_id", "sienge_creditor_id"]
    search_fields = ["name", "tax_id"]
    inlines = [CounterpartyBankAccountInline]


class POItemInline(admin.TabularInline):
    model = POItem
    extra = 1
    fields = [
        "commercial_model_name",
        "description",
        "quantity",
        "unit_price",
        "unit_price_currency",
    ]


class POPaymentTermInline(admin.TabularInline):
    model = POPaymentTerm
    extra = 1
    fields = ["event_name", "percentage_due", "expected_date"]


class POGeneratedPDFInline(admin.TabularInline):
    model = POGeneratedPDF
    extra = 0
    readonly_fields = ["template_name", "generated_at", "generated_by"]
    fields = ["template_name", "generated_at", "generated_by"]

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(POGeneratedPDF)
class POGeneratedPDFAdmin(admin.ModelAdmin):
    list_display = ["po", "template_name", "is_signed", "generated_at", "generated_by", "autentique_doc_id"]
    list_filter = ["template_name", "generated_at"]
    search_fields = ["po__po_number", "template_name", "autentique_doc_id"]
    readonly_fields = ["po", "template_name", "generated_at", "generated_by", "autentique_doc_id", "autentique_links"]


@admin.register(PO)
class POAdmin(admin.ModelAdmin):
    list_display = [
        "po_number",
        "document_type",
        "counterparty",
        "issued_at",
        "total",
        "requested_delivery_date",
        "sienge_bill_id",
    ]
    list_filter = ["issued_at", "document_type", "counterparty"]
    search_fields = ["po_number", "contract_number", "counterparty__name"]
    date_hierarchy = "issued_at"
    inlines = [POItemInline, POPaymentTermInline, POGeneratedPDFInline]
    fieldsets = (
        (None, {"fields": ("document_type", "po_number", "contract_number", "issued_at")}),
        ("Parties", {"fields": ("issuer", "counterparty", "signer_primary", "signer_secondary")}),
        ("Shipping", {"fields": ("requested_delivery_date", "incoterms", "port", "warranty")}),
        ("Sienge", {"fields": ("sienge_bill_id", "sienge_obra_id", "sienge_cost_center_id", "sienge_department_id", "sienge_payment_category_id")}),
    )
