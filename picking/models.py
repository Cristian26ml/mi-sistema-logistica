import uuid
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

    # código de guía
    factura = models.CharField(max_length=20, blank=True, default="SIN_GUIA")
    numero_orden = models.PositiveIntegerField(default=1)
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

    def save(self, *args, **kwargs):
        # Si no se ingresó manualmente un código de guía, se genera automáticamente
        if not self.factura:
            # Ej: PK-3F9A2C
            self.factura = f"PK-{uuid.uuid4().hex[:6].upper()}"

        # Numeración reiniciada por código de guía
        if not self.numero_orden:
            count = PickingOrder.objects.filter(factura=self.factura).count()
            self.numero_orden = count + 1

        super().save(*args, **kwargs)


class PickingDetail(models.Model):
    producto = models.ForeignKey(Product, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()
    ubicacion = models.ForeignKey(Location, on_delete=models.PROTECT)
    operario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    estado = models.CharField(
        max_length=20,
        choices=[("PENDIENTE", "Pendiente"), ("EN_PROCESO",
                                              "En proceso"), ("COMPLETADO", "Completado")],
        default="PENDIENTE"
    )
    prioridad = models.PositiveIntegerField(default=1)

    orden = models.ForeignKey(
        PickingOrder, on_delete=models.CASCADE, related_name="detalles")
