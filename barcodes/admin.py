from django.utils.html import format_html


def mostrar_codigo_barra(obj):
    if obj.codigo_barra_imagen:
        return format_html('<img src="/{}" width="200" />', obj.codigo_barra_imagen)
    return "Sin código"


mostrar_codigo_barra.short_description = "Código de barras"
