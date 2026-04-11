from django.urls import path
from . import views

app_name = "receiving"

urlpatterns = [
    path("recepciones/", views.receipt_list, name="receipt_list"),
    path("nueva/", views.receipt_create, name="receipt_create"),
    path("importar/", views.receipt_import, name="receipt_import"),
    path("<int:receipt_id>/", views.receipt_detail, name="receipt_detail"),
    path("<int:receipt_id>/iniciar/", views.receipt_start, name="receipt_start"),
    path("<int:receipt_id>/scan/", views.receipt_scan, name="receipt_scan"),
    path("<int:receipt_id>/finalizar/",
         views.receipt_finish, name="receipt_finish"),
    path("<int:receipt_id>/approve/",
         views.receipt_approve, name="receipt_approve"),
]
