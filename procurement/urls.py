from django.urls import path
from . import views

urlpatterns = [
    path("", views.po_list, name="po_list"),
    path("po/new/", views.po_form, name="po_create"),
    path("po/<int:pk>/", views.po_detail, name="po_detail"),
    path("po/<int:pk>/edit/", views.po_form, name="po_edit"),
    path("po/<int:pk>/pdf/", views.po_pdf, name="po_pdf"),
    path("po/<int:pk>/pdf/view/", views.po_pdf_view, name="po_pdf_view"),
]
