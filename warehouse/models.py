from django.db import models
from catalog.models import Product
import uuid
import barcode
from barcode.writer import ImageWriter
import os

from django.utils.html import format_html


def generar_codigo(tipo="GEN"):
    return f"{tipo}-{uuid.uuid4().int >> 64}"[:15]


def generar_codigo_barra(codigo, nombre_archivo):
    ruta = os.path.join("media", "barcode")
    os.makedirs(ruta, exist_ok=True)
    code128 = barcode.get("code128", codigo, writer=ImageWriter())
    filename = os.path.join(ruta, nombre_archivo)
    code128.save(filename)
    return filename + ".png"


class Location(models.Model):
    codigo = models.CharField(max_length=30, unique=True)  # Ej: A-01-01

    descripcion = models.CharField(max_length=200, blank=True)
    codigo_ubicacion = models.CharField(
        max_length=50, unique=True, blank=True, null=True)
    codigo_barra_imagen = models.ImageField(
        max_length=200, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.codigo_ubicacion:
            self.codigo_ubicacion = generar_codigo("LOC")
        super().save(*args, **kwargs)

        self.codigo_barra_imagen = generar_codigo_barra(
            self.codigo_ubicacion, f"location_{self.id}")
        super().save(update_fields=["codigo_barra_imagen"])

    def mostrar_codigo_barra(self):
        if self.codigo_barra_imagen:
            return format_html('<img src="/{}" width="200" />', self.codigo_barra_imagen)
        return "Sin código"
    mostrar_codigo_barra.short_description = "Código de barras"

    def __str__(self):
        return f"{self.codigo} ({self.codigo_ubicacion})"


class ProductLocation(models.Model):
    producto = models.ForeignKey(Product, on_delete=models.CASCADE)
    ubicacion = models.ForeignKey(Location, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("producto", "ubicacion")

    def __str__(self):
        return f"{self.producto} -> {self.ubicacion} ({self.cantidad})"


class Container(models.Model):
    codigo_contenedor = models.CharField(
        max_length=50, unique=True, blank=True, null=True)
    ubicacion = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True, blank=True)
    codigo_barra_imagen = models.ImageField(
        max_length=200, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.codigo_contenedor:
            self.codigo_contenedor = generar_codigo("CON")
        super().save(*args, **kwargs)

        self.codigo_barra_imagen = generar_codigo_barra(
            self.codigo_contenedor, f"container_{self.id}")
        super().save(update_fields=["codigo_barra_imagen"])

    def __str__(self):
        return f"Contenedor {self.codigo_contenedor}"
