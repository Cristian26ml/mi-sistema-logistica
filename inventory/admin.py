from django.contrib import admin
from .models import Movement


@admin.register(Movement)
class MovementAdmin(admin.ModelAdmin):
    list_display = ("producto", "contenedor", "tipo",
                    "cantidad", "fecha", "usuario")
    list_filter = ("tipo", "fecha", "usuario")
    search_fields = ("producto__sku", "producto__nombre",
                     "contenedor__codigo_contenedor")
# Register your models here.
