from django.utils.html import format_html
from django.contrib import admin
from .models import Location, ProductLocation, Container


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("codigo", "descripcion",
                    "codigo_ubicacion", "mostrar_codigo_barra")
    search_fields = ("codigo", "codigo_ubicacion")
    list_filter = ("descripcion",)

    def mostrar_codigo_barra(self, obj):
        if obj.codigo_barra_imagen:
            return format_html('<img src="/{}" width="200" />', obj.codigo_barra_imagen)
        return "Sin código"
    mostrar_codigo_barra.short_description = "Código de barras"

    # 🔒 Restricciones de acceso
    def has_view_permission(self, request, obj=None):
        return request.user.groups.filter(name__in=["Supervisor", "Administrador"]).exists()

    def has_change_permission(self, request, obj=None):
        return request.user.groups.filter(name__in=["Supervisor", "Administrador"]).exists()

    def has_add_permission(self, request):
        return request.user.groups.filter(name__in=["Supervisor", "Administrador"]).exists()

    def has_delete_permission(self, request, obj=None):
        return request.user.groups.filter(name__in=["Supervisor", "Administrador"]).exists()


@admin.register(ProductLocation)
class ProductLocationAdmin(admin.ModelAdmin):
    list_display = ("producto", "ubicacion", "cantidad")
    search_fields = ("producto__nombre", "ubicacion__codigo")
    list_filter = ("ubicacion",)


@admin.register(Container)
class ContainerAdmin(admin.ModelAdmin):
    list_display = ("codigo_contenedor", "ubicacion")
    search_fields = ("codigo_contenedor",)
    list_filter = ("ubicacion",)

    def mostrar_codigo_barra(self, obj):
        if obj.codigo_barra_imagen:
            return format_html('<img src="/{}" width="200" />', obj.codigo_barra_imagen)
        return "Sin código"
    mostrar_codigo_barra.short_description = "Código de barras"
