from django.conf import settings
from django.db import models
from catalog.models import Product


class Receipt(models.Model):
    class Status(models.TextChoices):
        BORRADOR = "BORRADOR", "Borrador"
        EN_RECEPCION = "EN_RECEPCION", "En recepción"
        PENDIENTE_APROBACION = "PENDIENTE_APROBACION", "Pendiente aprobación"
        APROBADA = "APROBADA", "Aprobada"
        RECHAZADA = "RECHAZADA", "Rechazada"

    proveedor = models.CharField(max_length=150)
    numero_documento = models.CharField(max_length=50)
    fecha_documento = models.DateField()
    archivo = models.FileField(upload_to="recepciones/", null=True, blank=True)
    estado = models.CharField(
        max_length=30, choices=Status.choices, default=Status.BORRADOR)
    observacion = models.TextField(blank=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="recepciones_creadas"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.numero_documento} - {self.proveedor}"


class ReceiptDetail(models.Model):
    recepcion = models.ForeignKey(
        Receipt, on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey(Product, on_delete=models.PROTECT)
    cantidad_esperada = models.PositiveIntegerField()
    cantidad_recibida = models.PositiveIntegerField(default=0)
    observacion = models.TextField(blank=True)

    def __str__(self):
        return f"{self.recepcion.numero_documento} - {self.producto.sku}"
