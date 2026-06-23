from django.db import models
from decimal import Decimal


class Issuer(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()
    tax_id = models.CharField(max_length=50, verbose_name="Tax ID", blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class IssuerEmail(models.Model):
    issuer = models.ForeignKey(Issuer, on_delete=models.CASCADE, related_name="emails")
    email = models.EmailField()

    class Meta:
        verbose_name_plural = "Issuer emails"
        ordering = ["email"]

    def __str__(self):
        return self.email


class BankAccount(models.Model):
    issuer = models.ForeignKey(
        Issuer, on_delete=models.CASCADE, related_name="bank_accounts"
    )
    account_number = models.CharField(max_length=100)
    account_currency = models.CharField(max_length=10)
    bank_name = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = "Bank accounts"
        ordering = ["bank_name"]

    def __str__(self):
        return f"{self.bank_name} - {self.account_number}"


class Supplier(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()
    tax_id = models.CharField(max_length=50, verbose_name="Tax ID", blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class SupplierBankAccount(models.Model):
    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, related_name="bank_accounts"
    )
    account_address = models.TextField(blank=True)
    account_number = models.CharField(max_length=100)
    account_currency = models.CharField(max_length=10)
    bank_name = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = "Supplier bank accounts"
        ordering = ["bank_name"]

    def __str__(self):
        return f"{self.supplier.name} - {self.bank_name}"


class PO(models.Model):
    po_number = models.CharField(max_length=50, unique=True, verbose_name="PO Number")
    contract_number = models.CharField(max_length=100, blank=True)
    issued_at = models.DateField(verbose_name="Issue Date")
    issuer = models.ForeignKey(
        Issuer, on_delete=models.PROTECT, related_name="purchase_orders"
    )
    supplier = models.ForeignKey(
        Supplier, on_delete=models.PROTECT, related_name="purchase_orders"
    )
    requested_delivery_date = models.DateField(
        blank=True, null=True, verbose_name="Lead Time Requested"
    )
    warranty = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Purchase Order"
        verbose_name_plural = "Purchase Orders"
        ordering = ["-issued_at", "-po_number"]

    def __str__(self):
        return self.po_number

    @property
    def total(self):
        items = self.items.all()
        return sum(item.line_total for item in items)

    @property
    def currency(self):
        first_item = self.items.first()
        if first_item and hasattr(first_item, "unit_price_currency"):
            return first_item.unit_price_currency
        return ""


class POItem(models.Model):
    po = models.ForeignKey(PO, on_delete=models.CASCADE, related_name="items")
    commercial_model_name = models.CharField(max_length=255)
    description = models.TextField()
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price_currency = models.CharField(max_length=10, default="USD")

    class Meta:
        verbose_name = "PO Item"
        verbose_name_plural = "PO Items"

    def __str__(self):
        return f"{self.commercial_model_name} ({self.quantity})"

    @property
    def line_total(self):
        return self.quantity * self.unit_price


class POPaymentTerm(models.Model):
    po = models.ForeignKey(PO, on_delete=models.CASCADE, related_name="payment_terms")
    event_name = models.CharField(max_length=255)
    percentage_due = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name="% Due"
    )
    expected_date = models.DateField()

    class Meta:
        verbose_name = "PO Payment Term"
        verbose_name_plural = "PO Payment Terms"
        ordering = ["expected_date"]

    def __str__(self):
        return f"{self.event_name} - {self.percentage_due}%"
