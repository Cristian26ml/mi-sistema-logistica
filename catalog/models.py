from django.db import models


class Category(models.Model):
    nombre = models.CharField(max_length=80, unique=True)

    def __str__(self):
        return str(self.nombre)


# def calcular_digito_verificador_ean13(base12: str) -> str:
#    if len(base12) != 12 or not base12.isdigit():
#        raise ValueError(
#            "La base del EAN-13 debe tener exactamente 12 dígitos")

#    suma = 0
#    for i, digito in enumerate(base12):
#        n = int(digito)
#        if i % 2 == 0:
#            suma += n
#        else:
#            suma += n * 3

#    digito_verificador = (10 - (suma % 10)) % 10
#    return str(digito_verificador)


# def generar_ean13_desde_base(base12: str) -> str:
#    return base12 + calcular_digito_verificador_ean13(base12)


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

    def save(self, *args, **kwargs):
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
