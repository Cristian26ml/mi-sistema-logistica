from django.conf import settings
from django.db import models
from catalog.models import Product


class Movement(models.Model):
    class Types(models.TextChoices):
        ENTRADA = "ENTRADA", "Entrada"
        SALIDA = "SALIDA", "Salida"
        MERMA = "MERMA", "Merma"
        UBICACION = "UBICACION", "Ubicación"

    producto = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="movimientos"
    )
    ubicacion = models.ForeignKey(
        "warehouse.Location",
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    tipo = models.CharField(max_length=15, choices=Types.choices)
    cantidad = models.PositiveIntegerField()
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT
    )

    def __str__(self):
        return f"{self.tipo} {self.cantidad} - {self.producto.sku}"
