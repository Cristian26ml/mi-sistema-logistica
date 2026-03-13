from django.urls import path
from . import views

app_name = "warehouse"

urlpatterns = [

    path("ubicaciones/", views.ubicaciones_list, name="ubicaciones_list"),
    # path("ubicaciones/crear/", views.ubicacion_crear, name="ubicacion_crear"),
    path("ubicaciones/generar/", views.ubicacion_generar, name="ubicacion_generar"),
    path("asignaciones/", views.asignaciones_list, name="asignaciones_list"),
    path("asignaciones/nueva/", views.asignacion_crear, name="asignacion_crear"),
    path("consulta-ubicacion/", views.ubicacion_por_sku, name="consulta_ubicacion"),
]
