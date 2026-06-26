import base64
import json
from pathlib import Path
from collections import defaultdict

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings

from .models import Issuer, Supplier, PO, POItem, POPaymentTerm, LegalRepresentative, POGeneratedPDF, Product
from .mail import send_signing_emails

AVAILABLE_TEMPLATES = [
    {"id": "ids_standard", "label": "IDS Standard", "file": "procurement/po_pdf.html"},
]


def _logo_b64(filename):
    path = Path(settings.BASE_DIR) / "procurement" / "static" / "procurement" / "images" / filename
    return base64.b64encode(path.read_bytes()).decode()


def _generate_pdf_bytes(po, template_file):
    from weasyprint import HTML

    items = list(po.items.all())
    payment_terms = list(po.payment_terms.all())
    supplier_accounts = list(po.supplier.bank_accounts.all())
    currency = items[0].unit_price_currency if items else ""
    total = sum(item.line_total for item in items)

    html_string = render_to_string(
        template_file,
        {
            "po": po,
            "items": items,
            "payment_terms": payment_terms,
            "supplier_accounts": supplier_accounts,
            "currency": currency,
            "total": total,
            "logo_b64": _logo_b64("logo_ids.png"),
        },
    )
    return HTML(string=html_string).write_pdf()


def _legal_reps_json():
    result = defaultdict(list)
    for lr in LegalRepresentative.objects.prefetch_related("issuers").all():
        for issuer in lr.issuers.all():
            result[issuer.pk].append({"id": lr.pk, "name": lr.name})
    return json.dumps(result)


def _issuer_meta_json():
    return json.dumps({
        str(iss.pk): {"prefix": iss.po_prefix, "suffix": iss.po_suffix}
        for iss in Issuer.objects.all()
    })


@staff_member_required
def po_list(request):
    pos = PO.objects.select_related("supplier", "issuer").all()
    return render(request, "procurement/po_list.html", {"pos": pos})


@staff_member_required
def po_detail(request, pk):
    po = get_object_or_404(PO.objects.select_related("supplier", "issuer"), pk=pk)
    return render(request, "procurement/po_detail.html", {"po": po})


@staff_member_required
def po_form(request, pk=None):
    po = None
    items = []
    payment_terms = []

    if pk:
        po = get_object_or_404(PO, pk=pk)
        if po.is_locked:
            messages.error(request, "This PO is locked because it has been sent for signature and cannot be edited.")
            return redirect("po_detail", pk=po.pk)
        items = list(po.items.all())
        payment_terms = list(po.payment_terms.all())

    if request.method == "POST":
        po_data = {
            "po_number": request.POST.get("po_number", "").strip(),
            "product_id": request.POST.get("product") or None,
            "contract_number": request.POST.get("contract_number", "").strip(),
            "issued_at": request.POST.get("issued_at"),
            "issuer_id": request.POST.get("issuer"),
            "supplier_id": request.POST.get("supplier"),
            "requested_delivery_date": request.POST.get("requested_delivery_date") or None,
            "incoterms": request.POST.get("incoterms", "").strip(),
            "port": request.POST.get("port", "").strip(),
            "warranty": request.POST.get("warranty", "").strip(),
            "signer_primary_id": request.POST.get("signer_primary") or None,
            "signer_secondary_id": request.POST.get("signer_secondary") or None,
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
                parsed_items.append({
                    "commercial_model_name": model,
                    "description": desc,
                    "quantity": qty,
                    "unit_price": price,
                    "unit_price_currency": currency,
                })

        # Parse payment terms
        term_count = int(request.POST.get("term-count", 0))
        parsed_terms = []
        for i in range(term_count):
            event = request.POST.get(f"term_event_{i}", "").strip()
            pct = request.POST.get(f"term_pct_{i}", "")
            date = request.POST.get(f"term_date_{i}", "")
            if event and pct and date:
                parsed_terms.append({
                    "event_name": event,
                    "percentage_due": pct,
                    "expected_date": date,
                })

        # Validate
        errors = []
        if not po_data["po_number"]:
            errors.append("PO Number is required.")
        if not po_data["product_id"]:
            errors.append("Product is required.")
        if not po_data["issued_at"]:
            errors.append("Issue Date is required.")
        if not po_data["issuer_id"]:
            errors.append("Issuer is required.")
        if not po_data["supplier_id"]:
            errors.append("Supplier is required.")
        if not po_data["signer_primary_id"]:
            errors.append("Primary Signer is required.")
        if not parsed_items:
            errors.append("At least one item is required.")

        if po_data["po_number"]:
            existing = PO.objects.filter(po_number=po_data["po_number"])
            if pk:
                existing = existing.exclude(pk=pk)
            if existing.exists():
                errors.append(f"PO Number '{po_data['po_number']}' already exists.")

        if errors:
            for e in errors:
                messages.error(request, e)
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
                    "legal_reps_json": _legal_reps_json(),
                    "issuer_meta_json": _issuer_meta_json(),
                    "products": Product.objects.all(),
                },
            )

        if pk:
            po.po_number = po_data["po_number"]
            po.product_id = po_data["product_id"]
            po.contract_number = po_data["contract_number"]
            po.issued_at = po_data["issued_at"]
            po.issuer_id = po_data["issuer_id"]
            po.supplier_id = po_data["supplier_id"]
            po.requested_delivery_date = po_data["requested_delivery_date"]
            po.incoterms = po_data["incoterms"]
            po.port = po_data["port"]
            po.warranty = po_data["warranty"]
            po.signer_primary_id = po_data["signer_primary_id"]
            po.signer_secondary_id = po_data["signer_secondary_id"]
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
            "legal_reps_json": _legal_reps_json(),
            "issuer_meta_json": _issuer_meta_json(),
            "products": Product.objects.all(),
        },
    )


@staff_member_required
def po_suggest_number(request):
    import re
    from datetime import date
    from django.http import JsonResponse

    issuer_id = request.GET.get("issuer_id", "")
    product_code = request.GET.get("product_code", "").upper()
    date_str = request.GET.get("date", "")

    if not issuer_id or not product_code:
        return JsonResponse({"error": "issuer_id and product_code are required."}, status=400)

    issuer = get_object_or_404(Issuer, pk=issuer_id)
    if not issuer.po_prefix or not issuer.po_suffix:
        return JsonResponse({"error": "Issuer has no PO prefix/suffix configured."}, status=400)

    try:
        ref_date = date.fromisoformat(date_str) if date_str else date.today()
    except ValueError:
        ref_date = date.today()

    yyyymm = ref_date.strftime("%Y%m")
    prefix_part = f"{issuer.po_prefix}_{yyyymm}_{product_code}"
    pattern = re.compile(rf"^{re.escape(prefix_part)}(\d+)_")

    max_seq = 0
    for pn in PO.objects.filter(po_number__startswith=prefix_part).values_list("po_number", flat=True):
        m = pattern.match(pn)
        if m:
            max_seq = max(max_seq, int(m.group(1)))

    next_seq = max_seq + 1
    suggested = f"{issuer.po_prefix}_{yyyymm}_{product_code}{next_seq:02d}_{issuer.po_suffix}"
    return JsonResponse({"suggested": suggested})


@staff_member_required
def po_pdf_generate(request, pk):
    po = get_object_or_404(PO.objects.select_related("supplier", "issuer"), pk=pk)

    if request.method == "POST":
        template_id = request.POST.get("template_id", "ids_standard")
        template = next((t for t in AVAILABLE_TEMPLATES if t["id"] == template_id), AVAILABLE_TEMPLATES[0])

        pdf_bytes = _generate_pdf_bytes(po, template["file"])
        POGeneratedPDF.objects.create(
            po=po,
            template_name=template["label"],
            pdf_data=pdf_bytes,
            generated_by=request.user,
        )
        messages.success(request, f"PDF '{template['label']}' generated successfully.")
        return redirect("po_pdf_versions", pk=po.pk)

    return render(request, "procurement/po_pdf_generate.html", {
        "po": po,
        "templates": AVAILABLE_TEMPLATES,
    })


@staff_member_required
def po_pdf_versions(request, pk):
    po = get_object_or_404(PO, pk=pk)
    versions = po.generated_pdfs.select_related("generated_by").all()
    return render(request, "procurement/po_pdf_versions.html", {
        "po": po,
        "versions": versions,
    })


@staff_member_required
def po_pdf_download(request, pdf_pk):
    pdf = get_object_or_404(POGeneratedPDF, pk=pdf_pk)
    response = HttpResponse(bytes(pdf.pdf_data), content_type="application/pdf")
    filename = f"PO_{pdf.po.po_number}_{pdf.generated_at:%Y%m%d_%H%M}.pdf"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@staff_member_required
def po_pdf_view(request, pdf_pk):
    pdf = get_object_or_404(POGeneratedPDF, pk=pdf_pk)
    response = HttpResponse(bytes(pdf.pdf_data), content_type="application/pdf")
    filename = f"PO_{pdf.po.po_number}_{pdf.generated_at:%Y%m%d_%H%M}.pdf"
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response


def _autentique_gql(api_key, payload, timeout=30):
    import requests as http_requests
    resp = http_requests.post(
        "https://api.autentique.com.br/v2/graphql",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()


@staff_member_required
def po_autentique_send(request, pdf_pk):
    import io
    import json
    import requests as http_requests
    from django.urls import reverse

    pdf_record = get_object_or_404(POGeneratedPDF, pk=pdf_pk)
    po = pdf_record.po

    if request.method != "POST":
        return redirect("po_pdf_versions", pk=po.pk)

    api_key = settings.AUTENTIQUE_API_KEY
    if not api_key:
        messages.error(request, "AUTENTIQUE_API_KEY is not configured.")
        return redirect("po_pdf_versions", pk=po.pk)

    if pdf_record.autentique_doc_id:
        messages.warning(request, "This PDF has already been sent to Autentique.")
        return redirect("po_pdf_versions", pk=po.pk)

    signers_reps = [s for s in [po.signer_primary, po.signer_secondary] if s]
    if not signers_reps:
        messages.error(request, "No signers defined on this PO.")
        return redirect("po_pdf_versions", pk=po.pk)

    # Folder lookup
    folder_id = None
    folder_name = settings.AUTENTIQUE_FOLDER
    if folder_name:
        try:
            fdata = _autentique_gql(api_key, {"query": "{ folders(limit: 60, page: 1) { data { id name } } }"})
            folders = fdata["data"]["folders"]["data"]
            match = next((f for f in folders if f["name"].lower() == folder_name.lower()), None)
            if match:
                folder_id = match["id"]
        except Exception:
            pass

    pdf_bytes = bytes(pdf_record.pdf_data)

    signers = []
    for rep in signers_reps:
        # if rep.phone and rep.phone.startswith("+"):
        #     signers.append({
        #         "name": rep.name,
        #         "phone": rep.phone,
        #         "action": "SIGN",
        #         "delivery_method": "DELIVERY_METHOD_WHATSAPP",
        #     })
        # else:
        signers.append({
            "name": rep.name,
            "email": rep.email,
            "action": "SIGN",
            "delivery_method": "DELIVERY_METHOD_EMAIL",
        })

    mutation = """
        mutation CreateDocument($document: DocumentInput!, $signers: [SignerInput!]!, $file: Upload!, $folder_id: UUID) {
            createDocument(document: $document, signers: $signers, file: $file, folder_id: $folder_id) {
                id name
                signatures {
                    public_id name email
                    action { name }
                    link { short_link }
                }
            }
        }
    """
    operations = json.dumps({
        "query": mutation,
        "variables": {
            "document": {"name": f"PO {po.po_number}", "reminder": "WEEKLY", "refusable": True},
            "signers": signers,
            "file": None,
            "folder_id": folder_id,
        },
    })

    try:
        resp = http_requests.post(
            "https://api.autentique.com.br/v2/graphql",
            headers={"Authorization": f"Bearer {api_key}"},
            data={"operations": operations, "map": json.dumps({"file": ["variables.file"]})},
            files={"file": (f"PO_{po.po_number}.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
            timeout=60,
        )
        resp.raise_for_status()
        result = resp.json()
    except Exception as exc:
        messages.error(request, f"Autentique API error: {exc}")
        return redirect("po_pdf_versions", pk=po.pk)

    if "errors" in result:
        messages.error(request, f"Autentique error: {result['errors'][0]['message']}")
        return redirect("po_pdf_versions", pk=po.pk)

    doc = result["data"]["createDocument"]
    doc_id = doc["id"]

    _CREATE_LINK_QUERY = """
        mutation CreateLink($public_id: UUID!) {
            createLinkToSignature(public_id: $public_id) { short_link }
        }
    """

    links = []
    for sig in doc.get("signatures", []):
        public_id = sig.get("public_id", "")
        short_link = ""
        if public_id:
            try:
                ldata = _autentique_gql(api_key, {
                    "query": _CREATE_LINK_QUERY,
                    "variables": {"public_id": public_id},
                })
                short_link = (ldata.get("data", {}).get("createLinkToSignature") or {}).get("short_link", "")
            except Exception:
                pass
        links.append({
            "name": sig["name"],
            "email": sig["email"],
            "short_link": short_link,
        })

    pdf_record.autentique_doc_id = doc_id
    pdf_record.autentique_links = links
    pdf_record.save(update_fields=["autentique_doc_id", "autentique_links"])

    try:
        send_signing_emails(po, links)
        messages.success(request, "Document created and signing emails sent successfully.")
    except Exception as exc:
        messages.warning(request, f"Document created, but email sending failed: {exc}")

    url = reverse("po_pdf_versions", kwargs={"pk": po.pk})
    return redirect(f"{url}?signed={pdf_record.pk}")


@staff_member_required
def po_autentique_check(request, pdf_pk):
    import requests as http_requests

    pdf_record = get_object_or_404(POGeneratedPDF, pk=pdf_pk)
    po = pdf_record.po

    if not pdf_record.autentique_doc_id:
        messages.error(request, "This PDF has no Autentique document associated.")
        return redirect("po_pdf_versions", pk=po.pk)

    if pdf_record.is_signed:
        messages.info(request, "This document is already marked as signed.")
        return redirect("po_pdf_versions", pk=po.pk)

    api_key = settings.AUTENTIQUE_API_KEY
    try:
        gdata = _autentique_gql(api_key, {
            "query": """
                query GetDocument($id: UUID!) {
                    document(id: $id) {
                        files { signed }
                        signatures { name signed { created_at } }
                    }
                }
            """,
            "variables": {"id": pdf_record.autentique_doc_id},
        })
        doc = gdata["data"]["document"]
        signed_url = (doc.get("files") or {}).get("signed", "")
    except Exception as exc:
        messages.error(request, f"Autentique API error: {exc}")
        return redirect("po_pdf_versions", pk=po.pk)

    if not signed_url:
        pending = [s["name"] for s in doc.get("signatures", []) if not s.get("signed")]
        if pending:
            messages.warning(request, f"Document not fully signed yet. Pending: {', '.join(pending)}.")
        else:
            messages.warning(request, "Document not fully signed yet.")
        return redirect("po_pdf_versions", pk=po.pk)

    try:
        pdf_resp = http_requests.get(signed_url, timeout=60)
        if not pdf_resp.ok:
            pending = [s["name"] for s in doc.get("signatures", []) if not s.get("signed")]
            if pending:
                messages.warning(request, f"Document not yet signed. Pending: {', '.join(pending)}.")
            else:
                messages.warning(request, "Document not yet fully signed.")
            return redirect("po_pdf_versions", pk=po.pk)
        pdf_record.pdf_data = pdf_resp.content
        pdf_record.is_signed = True
        pdf_record.template_name = f"{pdf_record.template_name} (Signed)"
        pdf_record.autentique_doc_id = ""
        pdf_record.save(update_fields=["pdf_data", "is_signed", "template_name", "autentique_doc_id"])
    except Exception as exc:
        messages.error(request, f"Autentique connection error: {exc}")
        return redirect("po_pdf_versions", pk=po.pk)

    messages.success(request, "Signed PDF downloaded and saved successfully.")
    return redirect("po_pdf_versions", pk=po.pk)


@staff_member_required
def po_autentique_resend(request, pdf_pk):
    pdf_record = get_object_or_404(POGeneratedPDF, pk=pdf_pk)
    po = pdf_record.po

    if request.method != "POST":
        return redirect("po_pdf_versions", pk=po.pk)

    if not pdf_record.autentique_doc_id:
        messages.error(request, "This PDF has no Autentique document associated.")
        return redirect("po_pdf_versions", pk=po.pk)

    if pdf_record.is_signed:
        messages.info(request, "Document is already fully signed.")
        return redirect("po_pdf_versions", pk=po.pk)

    api_key = settings.AUTENTIQUE_API_KEY
    try:
        gdata = _autentique_gql(api_key, {
            "query": """
                query GetDocument($id: UUID!) {
                    document(id: $id) {
                        signatures { name email signed { created_at } }
                    }
                }
            """,
            "variables": {"id": pdf_record.autentique_doc_id},
        })
        autentique_sigs = gdata["data"]["document"]["signatures"]
    except Exception as exc:
        messages.error(request, f"Autentique API error: {exc}")
        return redirect("po_pdf_versions", pk=po.pk)

    signed_emails = {s["email"] for s in autentique_sigs if s.get("signed")}

    pending_links = [
        link for link in (pdf_record.autentique_links or [])
        if link.get("email") not in signed_emails
    ]

    if not pending_links:
        messages.info(request, "All signers have already signed.")
        return redirect("po_pdf_versions", pk=po.pk)

    try:
        send_signing_emails(po, pending_links)
        names = ", ".join(lnk["name"] for lnk in pending_links)
        messages.success(request, f"Emails resent to: {names}.")
    except Exception as exc:
        messages.warning(request, f"Email sending failed: {exc}")

    return redirect("po_pdf_versions", pk=po.pk)


@staff_member_required
@require_POST
def po_sienge_send(request, pk):
    import requests as http_requests

    po = get_object_or_404(
        PO.objects.select_related("issuer", "supplier").prefetch_related("payment_terms"),
        pk=pk,
    )

    if not po.is_signed:
        messages.error(request, "PO must be signed before sending to Sienge.")
        return redirect("po_detail", pk=po.pk)

    if po.sienge_bill_id:
        messages.warning(request, f"PO already sent to Sienge (Bill ID: {po.sienge_bill_id}).")
        return redirect("po_detail", pk=po.pk)

    if not po.issuer.sienge_company_id:
        messages.error(request, f"Issuer '{po.issuer.name}' has no Sienge Company ID configured.")
        return redirect("po_detail", pk=po.pk)

    if not po.supplier.sienge_creditor_id:
        messages.error(request, f"Supplier '{po.supplier.name}' has no Sienge Creditor ID configured.")
        return redirect("po_detail", pk=po.pk)

    auth_key = settings.SIENGE_AUTH_KEY
    if not auth_key:
        messages.error(request, "SIENGE_AUTH_KEY is not configured.")
        return redirect("po_detail", pk=po.pk)

    terms = list(po.payment_terms.order_by("expected_date"))
    if not terms:
        messages.error(request, "PO has no payment terms — cannot create bill in Sienge.")
        return redirect("po_detail", pk=po.pk)

    fin_cat_id = (
        po.product.financial_category_purchase
        if po.product and po.product.financial_category_purchase
        else None
    )

    installments = []
    for term in terms:
        installment = {
            "dueDate": term.expected_date.isoformat(),
            "netValue": float((term.percentage_due / 100) * po.total),
            "description": f"{po.po_number} – {term.event_name}",
        }
        if fin_cat_id:
            installment["financialCategoryId"] = fin_cat_id
        installments.append(installment)

    payload = {
        "companyId": po.issuer.sienge_company_id,
        "creditorId": po.supplier.sienge_creditor_id,
        "documentId": "PO",
        "documentNumber": po.po_number,
        "issueDate": po.issued_at.isoformat(),
        "installments": installments,
    }

    url = "https://api.sienge.com.br/ebmengenharia/public/api/v1/bills"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Basic {auth_key}",
    }

    try:
        resp = http_requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        messages.error(request, f"Sienge API error: {exc}")
        return redirect("po_detail", pk=po.pk)

    bill_id = data.get("billId") or data.get("id")
    if bill_id:
        po.sienge_bill_id = bill_id
        po.save(update_fields=["sienge_bill_id"])
        messages.success(request, f"Bill created in Sienge (ID: {bill_id}).")
    else:
        messages.success(request, "Bill created in Sienge.")

    return redirect("po_detail", pk=po.pk)


@csrf_exempt
@require_POST
def autentique_webhook(request):
    import hmac
    import hashlib
    import requests as http_requests

    # Verify HMAC-SHA256 signature if secret is configured
    secret = settings.AUTENTIQUE_WEBHOOK_SECRET
    if secret:
        received = request.headers.get("x-autentique-signature", "")
        expected = hmac.new(secret.encode(), request.body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, received):
            return HttpResponse(status=403)

    try:
        payload = json.loads(request.body)
    except Exception:
        return HttpResponse(status=400)

    event_type = payload.get("event", {}).get("type", "")

    if event_type == "document.finished":
        doc_obj = payload.get("event", {}).get("data", {}).get("object", {})
        doc_id = doc_obj.get("id", "")

        if not doc_id:
            return HttpResponse(status=200)

        pdf_record = POGeneratedPDF.objects.filter(autentique_doc_id=doc_id).first()
        if not pdf_record:
            return HttpResponse(status=200)

        api_key = settings.AUTENTIQUE_API_KEY
        try:
            gdata = _autentique_gql(api_key, {
                "query": "query GetDocument($id: UUID!) { document(id: $id) { files { signed } } }",
                "variables": {"id": doc_id},
            })
            signed_url = gdata["data"]["document"]["files"]["signed"]
            pdf_resp = http_requests.get(signed_url, timeout=60)
            pdf_resp.raise_for_status()

            pdf_record.pdf_data = pdf_resp.content
            pdf_record.is_signed = True
            pdf_record.template_name = f"{pdf_record.template_name} (Signed)"
            pdf_record.autentique_doc_id = ""
            pdf_record.save(update_fields=["pdf_data", "is_signed", "template_name", "autentique_doc_id"])
        except Exception:
            pass

    return HttpResponse(status=200)
