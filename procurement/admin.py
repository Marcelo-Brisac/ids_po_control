from django.contrib import admin
from .models import (
    Issuer,
    IssuerEmail,
    BankAccount,
    Supplier,
    SupplierBankAccount,
    PO,
    POItem,
    POPaymentTerm,
)


class BankAccountInline(admin.TabularInline):
    model = BankAccount
    extra = 1


class IssuerEmailInline(admin.TabularInline):
    model = IssuerEmail
    extra = 1


@admin.register(Issuer)
class IssuerAdmin(admin.ModelAdmin):
    list_display = ["name", "tax_id"]
    search_fields = ["name", "tax_id"]
    inlines = [IssuerEmailInline, BankAccountInline]


class SupplierBankAccountInline(admin.TabularInline):
    model = SupplierBankAccount
    extra = 1


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ["name", "tax_id"]
    search_fields = ["name", "tax_id"]
    inlines = [SupplierBankAccountInline]


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


@admin.register(PO)
class POAdmin(admin.ModelAdmin):
    list_display = [
        "po_number",
        "supplier",
        "issued_at",
        "total",
        "requested_delivery_date",
    ]
    list_filter = ["issued_at", "supplier"]
    search_fields = ["po_number", "contract_number", "supplier__name"]
    date_hierarchy = "issued_at"
    inlines = [POItemInline, POPaymentTermInline]
    fieldsets = (
        (None, {"fields": ("po_number", "contract_number", "issued_at")}),
        ("Parties", {"fields": ("issuer", "supplier")}),
        ("Lead Time & Warranty", {"fields": ("requested_delivery_date", "warranty")}),
    )
