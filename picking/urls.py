from django.urls import path
from . import views

app_name = "picking"

urlpatterns = [
    path("picking/", views.ordenes_list, name="ordenes_list"),
    path("picking/nueva/", views.orden_crear, name="orden_crear"),

    path("picking/<int:orden_id>/", views.orden_detalle, name="orden_detalle"),

    path("mis-pickings/", views.mis_pickings, name="mis_pickings"),
    path("confirmar/<int:detalle_id>/",
         views.confirmar_picking, name="confirmar_picking"),
    path("ubicaciones/<int:producto_id>/",
         views.ubicaciones_por_producto, name="ubicaciones_por_producto"),
]
