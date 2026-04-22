from django.conf import settings
from django.db import models
from catalog.models import Product
from warehouse.models import Container


class Movement(models.Model):
    class Types(models.TextChoices):
        ENTRADA = "ENTRADA", "Entrada"
        SALIDA = "SALIDA", "Salida"
        MERMA = "MERMA", "Merma"
        UBICACION = "UBICACION", "Ubicación"
        TRANSFERENCIA = "TRANSFERENCIA", "Transferencia"

    producto = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="movimientos",
        null=True, blank=True
    )
    ubicacion = models.ForeignKey(
        "warehouse.Location",
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    contenedor = models.ForeignKey(
        Container, on_delete=models.SET_NULL, null=True, blank=True)

    tipo = models.CharField(max_length=15, choices=Types.choices)
    cantidad = models.PositiveIntegerField()
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT
    )

    def __str__(self):
        producto_str = self.producto.sku if self.producto else "Sin producto"
        return f"{producto_str} - {self.tipo}"


class ProductContainer(models.Model):
    producto = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="inventory_product_containers"   # nombre único
    )
    contenedor = models.ForeignKey(
        Container,
        on_delete=models.CASCADE,
        related_name="inventory_product_containers"   # nombre único
    )
    cantidad = models.IntegerField(default=0)

    class Meta:
        unique_together = ("producto", "contenedor")

    def __str__(self):
        return f"{self.producto.sku} en {self.contenedor.codigo_contenedor} ({self.cantidad})"
