from django.core.management.base import BaseCommand
from warehouse.models import Container, ProductContainer
from inventory.models import Product


class Command(BaseCommand):
    help = "Sincroniza el stock_actual de cada producto con el contenedor ALMACEN_VIRTUAL"

    def handle(self, *args, **options):
        almacen_virtual, _ = Container.objects.get_or_create(
            codigo_contenedor="ALMACEN_VIRTUAL",
            defaults={"nombre": "Virtual"}
        )

        count = 0
        for p in Product.objects.all():
            pc, created = ProductContainer.objects.get_or_create(
                producto=p,
                contenedor=almacen_virtual,
                defaults={"cantidad": p.stock_actual}
            )
            if not created:
                pc.cantidad = p.stock_actual
                pc.save(update_fields=["cantidad"])
            count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Sincronizados {count} productos con ALMACEN_VIRTUAL."
        ))
