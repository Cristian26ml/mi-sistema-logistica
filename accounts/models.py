from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = "ADMIN", "Administrador"
        SUPERVISOR = "SUPERVISOR", "Supervisor"
        OPERARIO = "OPERARIO", "Operario"

    rol = models.CharField(
        max_length=20, choices=Roles.choices, default=Roles.OPERARIO)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.username} ({self.rol})"
