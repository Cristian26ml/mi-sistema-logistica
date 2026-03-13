from django.urls import path
from . import views

app_name = "receiving"

urlpatterns = [
    path("", views.receipt_list, name="receipt_list"),
    path("nueva/", views.receipt_create, name="receipt_create"),
    path("importar/", views.receipt_import, name="receipt_import"),
]
