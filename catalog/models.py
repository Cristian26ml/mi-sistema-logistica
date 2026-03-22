from django.db import models


class Category(models.Model):
    nombre = models.CharField(max_length=80, unique=True)

    def __str__(self):
        return str(self.nombre)


class Product(models.Model):
    codigo_barra = models.CharField(max_length=50, unique=True)
    codigo_interno = models.CharField(max_length=13, unique=True, blank=True)

    sku = models.CharField(max_length=40, unique=True)
    nombre = models.CharField(max_length=120)
    categoria = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="productos"
    )
    stock_minimo = models.PositiveIntegerField(default=0)
    stock_actual = models.IntegerField(default=0)
    estado = models.CharField(
        max_length=20,
        choices=[("OK", "OK"), ("ALERTA", "ALERTA")],
        default="OK"
    )

    def save(self, *args, **kwargs):
        # Actualizar estado antes de guardar
        if self.stock_actual <= self.stock_minimo:
            self.estado = "ALERTA"
        else:
            self.estado = "OK"

        creando = self.pk is None
        super().save(*args, **kwargs)

        updates = {}
        if creando and not self.codigo_interno:
            updates["codigo_interno"] = f"INT-{self.id:06d}"

        if updates:
            Product.objects.filter(pk=self.pk).update(**updates)
            for key, value in updates.items():
                setattr(self, key, value)

    def __str__(self):
        return f"{self.codigo_interno} - {self.nombre}"
