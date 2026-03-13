from .models import PickingOrder


def actualizar_estado_orden(orden):
    detalles = orden.detalles.all()

    if not detalles.exists():
        orden.estado = PickingOrder.Status.CREADA
    elif detalles.filter(confirmado=False).exists():
        if detalles.filter(confirmado=True).exists():
            orden.estado = PickingOrder.Status.EN_PROCESO
        else:
            orden.estado = PickingOrder.Status.CREADA
    else:
        orden.estado = PickingOrder.Status.COMPLETADA

    orden.save(update_fields=["estado"])
