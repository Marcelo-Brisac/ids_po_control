import requests as http_requests
from django.conf import settings


def _get_graph_token():
    resp = http_requests.post(
        f"https://login.microsoftonline.com/{settings.GRAPH_TENANT_ID}/oauth2/v2.0/token",
        data={
            "grant_type": "client_credentials",
            "client_id": settings.GRAPH_CLIENT_ID,
            "client_secret": settings.GRAPH_CLIENT_SECRET,
            "scope": "https://graph.microsoft.com/.default",
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def send_email(to_address, to_name, subject, body_html):
    token = _get_graph_token()
    http_requests.post(
        f"https://graph.microsoft.com/v1.0/users/{settings.GRAPH_SENDER_EMAIL}/sendMail",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={
            "message": {
                "subject": subject,
                "body": {"contentType": "HTML", "content": body_html},
                "toRecipients": [{"emailAddress": {"address": to_address, "name": to_name}}],
            }
        },
        timeout=30,
    ).raise_for_status()


def send_signing_emails(po, links):
    """Send one email per signer with their individual Autentique signing link."""
    if not all([settings.GRAPH_TENANT_ID, settings.GRAPH_CLIENT_ID,
                settings.GRAPH_CLIENT_SECRET, settings.GRAPH_SENDER_EMAIL]):
        raise RuntimeError("Microsoft Graph email settings are not fully configured.")

    token = _get_graph_token()

    for link_entry in links:
        name = link_entry.get("name", "")
        email = link_entry.get("email", "")
        signing_link = link_entry.get("short_link", "")
        if not email:
            continue

        body_html = _build_signing_email_html(po, name, signing_link)

        http_requests.post(
            f"https://graph.microsoft.com/v1.0/users/{settings.GRAPH_SENDER_EMAIL}/sendMail",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={
                "message": {
                    "subject": f"Solicitação de assinatura – PO {po.po_number}",
                    "body": {"contentType": "HTML", "content": body_html},
                    "toRecipients": [{"emailAddress": {"address": email, "name": name}}],
                }
            },
            timeout=30,
        ).raise_for_status()


def _build_signing_email_html(po, signer_name, signing_link):
    issuer_name = po.issuer.name if po.issuer else ""
    supplier_name = po.supplier.name if po.supplier else ""

    link_block = (
        f'<p style="margin:24px 0;">'
        f'<a href="{signing_link}" style="background:#1a56db;color:#fff;padding:12px 24px;'
        f'border-radius:6px;text-decoration:none;font-weight:600;font-size:15px;">'
        f'Assinar documento</a></p>'
        if signing_link else
        '<p style="color:#c53030;">Link de assinatura não disponível. Entre em contato com o remetente.</p>'
    )

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;font-size:14px;color:#1a1a1a;margin:0;padding:0;background:#f4f4f4;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4;padding:32px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
        <tr><td style="background:#1a56db;padding:24px 32px;">
          <span style="color:#fff;font-size:18px;font-weight:700;">EBM Engenharia</span>
        </td></tr>
        <tr><td style="padding:32px;">
          <p>Olá, <strong>{signer_name}</strong>,</p>
          <p>Você foi indicado como signatário da seguinte Purchase Order:</p>
          <table cellpadding="0" cellspacing="0" style="margin:16px 0;border-left:3px solid #1a56db;padding-left:16px;">
            <tr><td><strong>PO:</strong> {po.po_number}</td></tr>
            {"<tr><td><strong>Contrato:</strong> " + po.contract_number + "</td></tr>" if po.contract_number else ""}
            <tr><td><strong>Emitente:</strong> {issuer_name}</td></tr>
            <tr><td><strong>Fornecedor:</strong> {supplier_name}</td></tr>
          </table>
          <p>Por favor, acesse o link abaixo para revisar e assinar o documento:</p>
          {link_block}
          {"<p>Ou copie e cole este link no navegador:<br><span style='font-size:12px;color:#4a5568;'>" + signing_link + "</span></p>" if signing_link else ""}
          <hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0;">
          <p style="font-size:12px;color:#718096;">Este email foi gerado automaticamente pelo sistema IDS PO Control da EBM Engenharia. Por favor, não responda a este email.</p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""
