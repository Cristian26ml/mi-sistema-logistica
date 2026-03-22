import random
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

    factura = models.CharField(max_length=20, unique=True, blank=True)
    numero_orden = models.PositiveIntegerField(blank=True, null=True)
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
        # Generar código de guía si no existe
        if not self.factura:
            self.factura = f"{random.randint(10000, 99999)}"

        # Generar número de orden secuencial
        if not self.numero_orden:
            last_order = PickingOrder.objects.order_by("-numero_orden").first()
            self.numero_orden = (
                last_order.numero_orden + 1) if last_order else 1

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.factura} - Orden #{self.numero_orden}"


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
