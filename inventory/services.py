from django.db import transaction
from django.db.models import Sum
from catalog.models import Product
from warehouse.models import Location, ProductLocation
from .models import Movement


class StockError(Exception):
    pass


@transaction.atomic
def registrar_movimiento(*, producto_id: int, ubicacion_id: int, tipo: str, cantidad: int, usuario):
    if cantidad <= 0:
        raise StockError("La cantidad debe ser mayor que 0.")

    producto = Product.objects.select_for_update().get(id=producto_id)
    ubicacion = Location.objects.get(id=ubicacion_id)

    tipos_validos = {choice[0] for choice in Movement.Types.choices}
    if tipo not in tipos_validos:
        raise StockError("Tipo de movimiento no válido.")

    asignacion, _ = ProductLocation.objects.select_for_update().get_or_create(
        producto=producto,
        ubicacion=ubicacion,
        defaults={"cantidad": 0}
    )

    total_ubicado = ProductLocation.objects.filter(
        producto=producto
    ).aggregate(total=Sum("cantidad"))["total"] or 0

    stock_pendiente_ubicar = producto.stock_actual - total_ubicado

    # ENTRADA: aumenta stock total, no ubica automáticamente
    if tipo == Movement.Types.ENTRADA:
        nuevo_stock = producto.stock_actual + cantidad
        producto.stock_actual = nuevo_stock
        producto.save(update_fields=["stock_actual"])

    # UBICACION: mueve stock disponible a una ubicación, no cambia stock total
    elif tipo == Movement.Types.UBICACION:
        if cantidad > stock_pendiente_ubicar:
            raise StockError(
                f"No puedes ubicar {cantidad} unidades. "
                f"Stock pendiente por ubicar: {stock_pendiente_ubicar}."
            )

        asignacion.cantidad += cantidad
        asignacion.save(update_fields=["cantidad"])

    # SALIDA y MERMA: descuentan de ubicación y stock total
    elif tipo in (Movement.Types.SALIDA, Movement.Types.MERMA):
        if asignacion.cantidad < cantidad:
            raise StockError(
                f"No hay stock suficiente en la ubicación {ubicacion.codigo}. "
                f"Disponible: {asignacion.cantidad}."
            )

        nuevo_stock = producto.stock_actual - cantidad
        if nuevo_stock < 0:
            raise StockError("No se permiten stocks negativos.")

        asignacion.cantidad -= cantidad
        asignacion.save(update_fields=["cantidad"])

        producto.stock_actual = nuevo_stock
        producto.save(update_fields=["stock_actual"])

    else:
        raise StockError("Tipo de movimiento no válido.")

    mov = Movement.objects.create(
        producto=producto,
        ubicacion=ubicacion,
        tipo=tipo,
        cantidad=cantidad,
        usuario=usuario,
    )

    return mov
