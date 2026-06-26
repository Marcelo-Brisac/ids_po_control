from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal


class Issuer(models.Model):
    PO_PREFIX_CHOICES = [("IDS", "IDS"), ("EBM", "EBM"), ("IDSSE", "IDSSE")]
    PO_SUFFIX_CHOICES = [
        ("PA", "PA"), ("HK", "HK"), ("PE", "PE"), ("CL", "CL"),
        ("MX", "MX"), ("BR", "BR"), ("AR", "AR"), ("US", "US"),
    ]

    name = models.CharField(max_length=255)
    address = models.TextField()
    tax_id = models.CharField(max_length=50, verbose_name="Tax ID", blank=True)
    po_prefix = models.CharField(max_length=10, choices=PO_PREFIX_CHOICES, verbose_name="PO Prefix")
    po_suffix = models.CharField(max_length=10, choices=PO_SUFFIX_CHOICES, verbose_name="PO Suffix")
    sienge_company_id = models.IntegerField(null=True, verbose_name="Sienge Company ID")

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
    intermediate_bank_name = models.CharField(max_length=255, blank=True)
    intermediate_bank_address = models.TextField(blank=True)
    intermediate_bank_swift_address = models.CharField(max_length=255, blank=True)
    intermediate_bank_fed_aba = models.CharField(max_length=50, blank=True, verbose_name="Intermediate Bank FED/ABA")
    beneficiary_bank_name = models.CharField(max_length=255, blank=True)
    beneficiary_bank_address = models.TextField(blank=True)
    beneficiary_bank_swift_address = models.CharField(max_length=255, blank=True)
    beneficiary_bank_account_number = models.CharField(max_length=100, blank=True)
    beneficiary_bank_iban = models.CharField(max_length=50, blank=True, verbose_name="Beneficiary Bank IBAN")
    beneficiary_customer_name = models.CharField(max_length=255, blank=True)
    beneficiary_customer_address = models.TextField(blank=True)
    beneficiary_customer_branch = models.CharField(max_length=255, blank=True)
    beneficiary_customer_account = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name_plural = "Bank accounts"
        ordering = ["beneficiary_bank_name"]

    def __str__(self):
        return self.beneficiary_bank_name or f"Bank account #{self.pk}"


class LegalRepresentative(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True, verbose_name="Phone/Celular")
    issuers = models.ManyToManyField(
        Issuer, related_name="legal_representatives", blank=True
    )

    class Meta:
        verbose_name = "Legal Representative"
        verbose_name_plural = "Legal Representatives"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    code = models.CharField(max_length=3, unique=True, verbose_name="Code")
    description = models.TextField()
    financial_category_purchase = models.IntegerField(
        null=True, blank=True, verbose_name="Sienge Financial Category (Purchase)"
    )

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} – {self.description}"

    def save(self, *args, **kwargs):
        self.code = self.code.upper()
        super().save(*args, **kwargs)


class Supplier(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()
    tax_id = models.CharField(max_length=50, verbose_name="Tax ID", blank=True)
    sienge_creditor_id = models.IntegerField(null=True, verbose_name="Sienge Creditor ID")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class SupplierBankAccount(models.Model):
    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, related_name="bank_accounts"
    )
    intermediate_bank_name = models.CharField(max_length=255, blank=True)
    intermediate_bank_address = models.TextField(blank=True)
    intermediate_bank_swift_address = models.CharField(max_length=255, blank=True)
    intermediate_bank_fed_aba = models.CharField(max_length=50, blank=True, verbose_name="Intermediate Bank FED/ABA")
    beneficiary_bank_name = models.CharField(max_length=255, blank=True)
    beneficiary_bank_address = models.TextField(blank=True)
    beneficiary_bank_swift_address = models.CharField(max_length=255, blank=True)
    beneficiary_bank_account_number = models.CharField(max_length=100, blank=True)
    beneficiary_bank_iban = models.CharField(max_length=50, blank=True, verbose_name="Beneficiary Bank IBAN")
    beneficiary_customer_name = models.CharField(max_length=255, blank=True)
    beneficiary_customer_address = models.TextField(blank=True)
    beneficiary_customer_branch = models.CharField(max_length=255, blank=True)
    beneficiary_customer_account = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name_plural = "Supplier bank accounts"
        ordering = ["beneficiary_bank_name"]

    def __str__(self):
        return f"{self.supplier.name} – {self.beneficiary_bank_name or f'Bank account #{self.pk}'}"


class PO(models.Model):
    INCOTERMS_CHOICES = [
        ("EXW", "EXW – Ex Works"),
        ("FCA", "FCA – Free Carrier"),
        ("CPT", "CPT – Carriage Paid To"),
        ("CIP", "CIP – Carriage and Insurance Paid To"),
        ("DAP", "DAP – Delivered at Place"),
        ("DPU", "DPU – Delivered at Place Unloaded"),
        ("DDP", "DDP – Delivered Duty Paid"),
        ("FAS", "FAS – Free Alongside Ship"),
        ("FOB", "FOB – Free on Board"),
        ("CFR", "CFR – Cost and Freight"),
        ("CIF", "CIF – Cost Insurance and Freight"),
    ]

    po_number = models.CharField(max_length=50, unique=True, verbose_name="PO Number")
    product = models.ForeignKey(
        "Product",
        on_delete=models.PROTECT,
        null=True,
        related_name="purchase_orders",
        verbose_name="Product",
    )
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
    incoterms = models.CharField(
        max_length=3, choices=INCOTERMS_CHOICES, blank=True, verbose_name="Incoterms"
    )
    port = models.CharField(max_length=255, blank=True, verbose_name="Port")
    warranty = models.CharField(max_length=255, blank=True)
    signer_primary = models.ForeignKey(
        LegalRepresentative,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="primary_pos",
        verbose_name="Primary Signer",
    )
    signer_secondary = models.ForeignKey(
        LegalRepresentative,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="secondary_pos",
        verbose_name="Secondary Signer",
    )
    sienge_bill_id = models.IntegerField(null=True, blank=True, verbose_name="Sienge Bill ID")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Purchase Order"
        verbose_name_plural = "Purchase Orders"
        ordering = ["-issued_at", "-po_number"]

    def __str__(self):
        return self.po_number

    @property
    def is_locked(self):
        return self.generated_pdfs.filter(autentique_doc_id__gt="").exists()

    @property
    def is_signed(self):
        return self.generated_pdfs.filter(is_signed=True).exists()

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


class POGeneratedPDF(models.Model):
    po = models.ForeignKey(PO, on_delete=models.CASCADE, related_name="generated_pdfs")
    template_name = models.CharField(max_length=100)
    pdf_data = models.BinaryField()
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    autentique_doc_id = models.CharField(max_length=100, blank=True)
    autentique_links = models.JSONField(blank=True, null=True)
    is_signed = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Generated PDF"
        verbose_name_plural = "Generated PDFs"
        ordering = ["-generated_at"]

    def __str__(self):
        return f"{self.po.po_number} – {self.template_name} – {self.generated_at:%Y-%m-%d %H:%M}"
