from django.db import models
from catalog.models import Product


class Location(models.Model):
    codigo = models.CharField(max_length=30, unique=True)
    descripcion = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return str(self.codigo)


class ProductLocation(models.Model):
    producto = models.ForeignKey(Product, on_delete=models.CASCADE)
    ubicacion = models.ForeignKey(Location, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("producto", "ubicacion")

    def __str__(self):
        return f"{self.producto} -> {self.ubicacion} ({self.cantidad})"
