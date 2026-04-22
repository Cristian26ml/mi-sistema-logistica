from django.db import transaction
from catalog.models import Product
from warehouse.models import Container
from .models import Movement, ProductContainer


class StockError(Exception):
    pass


@transaction.atomic
def registrar_movimiento(
    *, producto_id: int, tipo: str, cantidad: int, usuario,
    contenedor_id: int = None, contenedor_origen_id: int = None
):
    if cantidad <= 0:
        raise StockError("La cantidad debe ser mayor que 0.")

    producto = Product.objects.select_for_update().get(id=producto_id)

    tipos_validos = {choice[0] for choice in Movement.Types.choices}
    if tipo not in tipos_validos:
        raise StockError("Tipo de movimiento no válido.")

    contenedor = None
    if contenedor_id:
        contenedor = Container.objects.get(id=contenedor_id)

    # ENTRADA → suma stock al ALMACEN_VIRTUAL
    if tipo == Movement.Types.ENTRADA:
        producto.stock_actual += cantidad
        producto.save(update_fields=["stock_actual"])

        almacen_virtual = Container.objects.get(
            codigo_contenedor="ALMACEN_VIRTUAL")
        asignacion, _ = ProductContainer.objects.select_for_update().get_or_create(
            producto=producto,
            contenedor=almacen_virtual,
            defaults={"cantidad": 0}
        )
        asignacion.cantidad += cantidad
        asignacion.save(update_fields=["cantidad"])

        return Movement.objects.create(
            producto=producto, contenedor=almacen_virtual,
            tipo=tipo, cantidad=cantidad, usuario=usuario
        )

    # SALIDA → descuenta stock de un contenedor físico
    elif tipo == Movement.Types.SALIDA:
        if not contenedor:
            raise StockError(
                "Debes indicar un contenedor origen para la salida.")

        asignacion, _ = ProductContainer.objects.select_for_update().get_or_create(
            producto=producto,
            contenedor=contenedor,
            defaults={"cantidad": 0}
        )
        if asignacion.cantidad < cantidad:
            raise StockError(
                f"No hay stock suficiente en {contenedor.codigo_contenedor}. Disponible: {asignacion.cantidad}."
            )
        # Se agrego esto para probar.
        asignacion.cantidad -= cantidad
        asignacion.save(update_fields=["cantidad"])

        producto.stock_actual = max(producto.stock_actual - cantidad, 0)
        producto.save(update_fields=["stock_actual"])

        return Movement.objects.create(
            producto=producto, contenedor=contenedor,
            tipo=tipo, cantidad=cantidad, usuario=usuario
        )

        # asignacion.cantidad -= cantidad
        # if asignacion.cantidad <= 0:
        #    asignacion.delete()
        # else:
        #    asignacion.save(update_fields=["cantidad"])

        # producto.stock_actual = max(producto.stock_actual - cantidad, 0)
        # producto.save(update_fields=["stock_actual"])

        # return Movement.objects.create(
        #    producto=producto, contenedor=contenedor,
        #    tipo=tipo, cantidad=cantidad, usuario=usuario
        # )

    # MERMA → descuenta stock del ALMACEN_VIRTUAL
    elif tipo == Movement.Types.MERMA:
        if cantidad > producto.stock_actual:
            raise StockError(
                f"No puedes registrar merma de {cantidad}. Stock disponible: {producto.stock_actual}."
            )
        producto.stock_actual -= cantidad
        producto.save(update_fields=["stock_actual"])

        almacen_virtual = Container.objects.get(
            codigo_contenedor="ALMACEN_VIRTUAL")
        asignacion, _ = ProductContainer.objects.select_for_update().get_or_create(
            producto=producto,
            contenedor=almacen_virtual,
            defaults={"cantidad": 0}
        )
        if asignacion.cantidad < cantidad:
            raise StockError(
                f"No hay stock suficiente en ALMACEN_VIRTUAL. Disponible: {asignacion.cantidad}."
            )
        asignacion.cantidad -= cantidad
        # se agrego esto para probar.
        asignacion.save(update_fields=["cantidad"])

        # if asignacion.cantidad <= 0:
        #    asignacion.delete()
        # else:
        #    asignacion.save(update_fields=["cantidad"])

        return Movement.objects.create(
            producto=producto, contenedor=almacen_virtual,
            tipo=tipo, cantidad=cantidad, usuario=usuario
        )

    # UBICACIÓN → mueve stock del ALMACEN_VIRTUAL a un contenedor físico
    elif tipo == Movement.Types.UBICACION:
        if not contenedor:
            raise StockError("Debes indicar un contenedor destino.")

        almacen_virtual = Container.objects.get(
            codigo_contenedor="ALMACEN_VIRTUAL")

        if contenedor_origen_id and contenedor_origen_id != almacen_virtual.id:
            raise StockError(
                "La acción UBICACIÓN solo es posible desde ALMACEN_VIRTUAL hacia un contenedor físico.")

        asignacion_virtual = ProductContainer.objects.select_for_update().filter(
            producto=producto, contenedor=almacen_virtual
        ).first()

        if not asignacion_virtual or asignacion_virtual.cantidad < cantidad:
            raise StockError(
                f"No hay stock suficiente en ALMACEN_VIRTUAL. Disponible: {asignacion_virtual.cantidad if asignacion_virtual else 0}."
            )

        # Descontar del virtual
        # Se agrego esto para probar.
        asignacion_virtual.cantidad -= cantidad
        asignacion_virtual.save(update_fields=["cantidad"])

        # asignacion_virtual.cantidad -= cantidad
        # if asignacion_virtual.cantidad < 0:
        #    asignacion_virtual.delete()
        # else:
        #    asignacion_virtual.save(update_fields=["cantidad"])

        # Sumar al destino
        asignacion_dest, _ = ProductContainer.objects.select_for_update().get_or_create(
            producto=producto, contenedor=contenedor, defaults={"cantidad": 0}
        )
        asignacion_dest.cantidad += cantidad
        asignacion_dest.save(update_fields=["cantidad"])

        return Movement.objects.create(
            producto=producto, contenedor=contenedor,
            tipo=tipo, cantidad=cantidad, usuario=usuario
        )

    # TRANSFERENCIA → mueve stock entre dos contenedores físicos
    elif tipo == Movement.Types.TRANSFERENCIA:
        if not contenedor:
            raise StockError("Debes indicar un contenedor destino.")
        if not contenedor_origen_id:
            raise StockError("Debes indicar un contenedor origen.")

        contenedor_origen = Container.objects.get(id=contenedor_origen_id)
        asignacion_origen, _ = ProductContainer.objects.select_for_update().get_or_create(
            producto=producto, contenedor=contenedor_origen, defaults={
                "cantidad": 0}
        )
        if asignacion_origen.cantidad < cantidad:
            raise StockError(
                f"No hay stock suficiente en {contenedor_origen.codigo_contenedor}. Disponible: {asignacion_origen.cantidad}."
            )

        # Se agrego esto para probar.
        asignacion_origen.cantidad -= cantidad
        asignacion_origen.save(update_fields=["cantidad"])

        asignacion_dest, _ = ProductContainer.objects.select_for_update().get_or_create(
            producto=producto, contenedor=contenedor, defaults={"cantidad": 0}
        )
        asignacion_dest.cantidad += cantidad
        asignacion_dest.save(update_fields=["cantidad"])

        return Movement.objects.create(
            producto=producto, contenedor=contenedor,
            tipo=tipo, cantidad=cantidad, usuario=usuario
        )

        # asignacion_origen.cantidad -= cantidad
        # if asignacion_origen.cantidad < 0:
        #    asignacion_origen.delete()
        # else:
        #    asignacion_origen.save(update_fields=["cantidad"])

        # asignacion_dest, _ = ProductContainer.objects.select_for_update().get_or_create(
        #    producto=producto, contenedor=contenedor, defaults={"cantidad": 0}
        # )
        # asignacion_dest.cantidad += cantidad
        # asignacion_dest.save(update_fields=["cantidad"])

        # return Movement.objects.create(
        #    producto=producto, contenedor=contenedor,
        #    tipo=tipo, cantidad=cantidad, usuario=usuario
        # )
