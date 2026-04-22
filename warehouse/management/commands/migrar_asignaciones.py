from django.core.management.base import BaseCommand
from warehouse.models import ProductLocation, ProductContainer, Container


class Command(BaseCommand):
    help = "Migra asignaciones de ProductLocation a ProductContainer usando contenedores existentes"

    def handle(self, *args, **options):
        migradas = 0
        for asignacion in ProductLocation.objects.all():
            producto = asignacion.producto
            ubicacion = asignacion.ubicacion

            # Buscar un contenedor ya existente en esa ubicación
            contenedor = Container.objects.filter(ubicacion=ubicacion).first()
            if not contenedor:
                # Si no existe, crear uno nuevo vinculado a la ubicación
                contenedor = Container.objects.create(
                    ubicacion=ubicacion,
                    codigo_contenedor=f"CON-{ubicacion.codigo}"
                )

            # Crear o actualizar la asignación en ProductContainer
            pc, created = ProductContainer.objects.get_or_create(
                producto=producto,
                contenedor=contenedor,
                defaults={"cantidad": asignacion.cantidad}
            )
            if not created:
                pc.cantidad += asignacion.cantidad
                pc.save(update_fields=["cantidad"])

            migradas += 1

        self.stdout.write(self.style.SUCCESS(
            f"Se migraron {migradas} asignaciones de ProductLocation a ProductContainer."
        ))
