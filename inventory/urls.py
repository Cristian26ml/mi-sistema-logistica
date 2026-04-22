from django.urls import path
from . import views

app_name = "inventory"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("movimientos/nuevo/", views.movimiento_crear, name="movimiento_crear"),
    path("movimientos/", views.movimientos_list, name="movimientos_list"),
    path("contenedor-a-ubicacion/", views.contenedor_a_ubicacion,
         name="contenedor_a_ubicacion"),
    path("escanear_contenedor/", views.escanear_contenedor,
         name="escanear_contenedor"),
    # Transferir producto entre contenedores
    path("transferir_producto/", views.transferir_producto,
         name="transferir_producto"),
    path("movimiento/escaner/", views.movimiento_escaner,
         name="movimiento_escaner"),
    path("consultar_producto/", views.consultar_producto,
         name="consultar_producto"),

    path("productos_por_contenedor/", views.productos_por_contenedor,
         name="productos_por_contenedor"),

]
