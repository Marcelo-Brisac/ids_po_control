from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required

from .models import Issuer, Supplier, PO, POItem, POPaymentTerm

try:
    from weasyprint import HTML

    HAS_WEASYPRINT = True
except Exception:
    HAS_WEASYPRINT = False


def po_list(request):
    pos = PO.objects.select_related("supplier", "issuer").all()
    return render(request, "procurement/po_list.html", {"pos": pos})


def po_detail(request, pk):
    po = get_object_or_404(PO.objects.select_related("supplier", "issuer"), pk=pk)
    return render(request, "procurement/po_detail.html", {"po": po})


def po_form(request, pk=None):
    po = None
    items = []
    payment_terms = []

    if pk:
        po = get_object_or_404(PO, pk=pk)
        items = list(po.items.all())
        payment_terms = list(po.payment_terms.all())

    if request.method == "POST":
        # Build PO from form data
        po_data = {
            "po_number": request.POST.get("po_number", "").strip(),
            "contract_number": request.POST.get("contract_number", "").strip(),
            "issued_at": request.POST.get("issued_at"),
            "issuer_id": request.POST.get("issuer"),
            "supplier_id": request.POST.get("supplier"),
            "requested_delivery_date": request.POST.get("requested_delivery_date")
            or None,
            "warranty": request.POST.get("warranty", "").strip(),
        }

        # Parse items
        item_count = int(request.POST.get("item-count", 0))
        parsed_items = []
        for i in range(item_count):
            model = request.POST.get(f"item_model_{i}", "").strip()
            desc = request.POST.get(f"item_description_{i}", "").strip()
            qty = request.POST.get(f"item_qty_{i}", "")
            price = request.POST.get(f"item_price_{i}", "")
            currency = request.POST.get(f"item_currency_{i}", "USD")
            if model and qty and price:
                parsed_items.append(
                    {
                        "commercial_model_name": model,
                        "description": desc,
                        "quantity": qty,
                        "unit_price": price,
                        "unit_price_currency": currency,
                    }
                )

        # Parse payment terms
        term_count = int(request.POST.get("term-count", 0))
        parsed_terms = []
        for i in range(term_count):
            event = request.POST.get(f"term_event_{i}", "").strip()
            pct = request.POST.get(f"term_pct_{i}", "")
            date = request.POST.get(f"term_date_{i}", "")
            if event and pct and date:
                parsed_terms.append(
                    {
                        "event_name": event,
                        "percentage_due": pct,
                        "expected_date": date,
                    }
                )

        # Validate
        errors = []
        if not po_data["po_number"]:
            errors.append("PO Number is required.")
        if not po_data["issued_at"]:
            errors.append("Issue Date is required.")
        if not po_data["issuer_id"]:
            errors.append("Issuer is required.")
        if not po_data["supplier_id"]:
            errors.append("Supplier is required.")
        if not parsed_items:
            errors.append("At least one item is required.")

        # Check PO number uniqueness (on create or if changed)
        if po_data["po_number"]:
            existing = PO.objects.filter(po_number=po_data["po_number"])
            if pk:
                existing = existing.exclude(pk=pk)
            if existing.exists():
                errors.append(f"PO Number '{po_data['po_number']}' already exists.")

        if errors:
            for e in errors:
                messages.error(request, e)
            # Re-render with submitted data
            issuers = Issuer.objects.all()
            suppliers = Supplier.objects.all()
            return render(
                request,
                "procurement/po_form.html",
                {
                    "po": type("PO", (), po_data)(),
                    "issuers": issuers,
                    "suppliers": suppliers,
                    "items": [type("Item", (), d)() for d in parsed_items],
                    "payment_terms": [type("Term", (), d)() for d in parsed_terms],
                },
            )

        # Save PO
        if pk:
            po.po_number = po_data["po_number"]
            po.contract_number = po_data["contract_number"]
            po.issued_at = po_data["issued_at"]
            po.issuer_id = po_data["issuer_id"]
            po.supplier_id = po_data["supplier_id"]
            po.requested_delivery_date = po_data["requested_delivery_date"]
            po.warranty = po_data["warranty"]
            po.save()
            po.items.all().delete()
            po.payment_terms.all().delete()
        else:
            po = PO.objects.create(**po_data)

        for item_data in parsed_items:
            POItem.objects.create(po=po, **item_data)

        for term_data in parsed_terms:
            POPaymentTerm.objects.create(po=po, **term_data)

        messages.success(request, f"PO {po.po_number} saved successfully.")
        return redirect("po_detail", pk=po.pk)

    # GET
    issuers = Issuer.objects.all()
    suppliers = Supplier.objects.all()
    return render(
        request,
        "procurement/po_form.html",
        {
            "po": po,
            "issuers": issuers,
            "suppliers": suppliers,
            "items": items,
            "payment_terms": payment_terms,
        },
    )


def po_pdf_view(request, pk):
    po = get_object_or_404(PO.objects.select_related("supplier", "issuer"), pk=pk)
    items = po.items.all()
    payment_terms = po.payment_terms.all()
    issuer_accounts = po.issuer.bank_accounts.all()
    supplier_accounts = po.supplier.bank_accounts.all()

    currency = ""
    total = sum(item.line_total for item in items)
    if items:
        currency = items.first().unit_price_currency

    return render(
        request,
        "procurement/po_pdf_view.html",
        {
            "po": po,
            "items": items,
            "payment_terms": payment_terms,
            "issuer_accounts": issuer_accounts,
            "supplier_accounts": supplier_accounts,
            "total": total,
            "currency": currency,
        },
    )


def po_pdf(request, pk):
    po = get_object_or_404(PO.objects.select_related("supplier", "issuer"), pk=pk)
    items = po.items.all()
    payment_terms = po.payment_terms.all()
    issuer_accounts = po.issuer.bank_accounts.all()
    supplier_accounts = po.supplier.bank_accounts.all()

    currency = ""
    if items:
        currency = items.first().unit_price_currency

    html_string = render_to_string(
        "procurement/po_pdf.html",
        {
            "po": po,
            "items": items,
            "payment_terms": payment_terms,
            "issuer_accounts": issuer_accounts,
            "supplier_accounts": supplier_accounts,
            "currency": currency,
        },
    )

    if HAS_WEASYPRINT:
        pdf = HTML(string=html_string).write_pdf()
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="PO_{po.po_number}.pdf"'
        return response
    else:
        return HttpResponse(html_string)
