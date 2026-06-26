from django.urls import path
from . import views

urlpatterns = [
    path("", views.po_list, name="po_list"),
    path("po/new/", views.po_form, name="po_create"),
    path("po/<int:pk>/", views.po_detail, name="po_detail"),
    path("po/<int:pk>/edit/", views.po_form, name="po_edit"),
    path("po/<int:pk>/pdf/generate/", views.po_pdf_generate, name="po_pdf_generate"),
    path("po/<int:pk>/pdf/versions/", views.po_pdf_versions, name="po_pdf_versions"),
    path("pdf/<int:pdf_pk>/download/", views.po_pdf_download, name="po_pdf_download"),
    path("pdf/<int:pdf_pk>/view/", views.po_pdf_view, name="po_pdf_view"),
    path("pdf/<int:pdf_pk>/autentique/send/", views.po_autentique_send, name="po_autentique_send"),
    path("pdf/<int:pdf_pk>/autentique/check/", views.po_autentique_check, name="po_autentique_check"),
    path("pdf/<int:pdf_pk>/autentique/resend/", views.po_autentique_resend, name="po_autentique_resend"),
    path("po/suggest-number/", views.po_suggest_number, name="po_suggest_number"),
    path("po/<int:pk>/sienge/send/", views.po_sienge_send, name="po_sienge_send"),
    path("webhook/autentique/", views.autentique_webhook, name="autentique_webhook"),
]
