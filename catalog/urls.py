from django.urls import path
from . import views


app_name = "catalog"

urlpatterns = [
    path("productos/", views.productos_list, name="productos_list"),
    path("productos/nuevo/", views.producto_crear, name="producto_crear"),
    path("categorias/nuevo/", views.categoria_crear, name="categoria_crear"),
]
