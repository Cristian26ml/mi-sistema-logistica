from warehouse.models import ProductLocation, ProductContainer, Container


def run():
    for pl in ProductLocation.objects.select_related("producto", "ubicacion"):
        contenedor, _ = Container.objects.get_or_create(
            ubicacion=pl.ubicacion,
            defaults={"codigo_contenedor": f"CON-{pl.ubicacion.id:06d}"}
        )

        pc, creado = ProductContainer.objects.get_or_create(
            producto=pl.producto,
            contenedor=contenedor,
            defaults={"cantidad": pl.cantidad}
        )

        if creado:
            print(
                f"Migrado {pl.producto.sku} a {contenedor.codigo_contenedor} con stock {pl.cantidad}")
        else:
            print(
                f"Ya existía {pl.producto.sku} en {contenedor.codigo_contenedor}")
