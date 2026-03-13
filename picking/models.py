from django.conf import settings
from django.db import models
from catalog.models import Product
from warehouse.models import Location


class PickingOrder(models.Model):
    class Status(models.TextChoices):
        CREADA = "CREADA", "Creada"
        EN_PROCESO = "EN_PROCESO", "En proceso"
        COMPLETADA = "COMPLETADA", "Completada"
        CANCELADA = "CANCELADA", "Cancelada"

    fecha = models.DateTimeField(auto_now_add=True)
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="ordenes_supervisor"
    )
    estado = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CREADA
    )


class PickingDetail(models.Model):
    orden = models.ForeignKey(
        PickingOrder,
        on_delete=models.CASCADE,
        related_name="detalles"
    )
    producto = models.ForeignKey(Product, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()
    ubicacion = models.ForeignKey(Location, on_delete=models.PROTECT)
    operario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="pickings_operario"
    )
    confirmado = models.BooleanField(default=False)
    confirmado_en = models.DateTimeField(null=True, blank=True)
