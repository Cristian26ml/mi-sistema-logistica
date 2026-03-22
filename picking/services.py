from .models import PickingOrder


def actualizar_estado_orden(orden):
    detalles = orden.detalles.all()

    if not detalles.exists():
        orden.estado = PickingOrder.Status.CREADA
    elif detalles.filter(estado="PENDIENTE").exists():
        # Si hay pendientes, la orden sigue creada
        orden.estado = PickingOrder.Status.CREADA
    elif detalles.filter(estado="EN_PROCESO").exists():
        # Si hay alguno en proceso, la orden está en proceso
        orden.estado = PickingOrder.Status.EN_PROCESO
    elif detalles.filter(estado="COMPLETADO").count() == detalles.count():
        # Si todos están completados, la orden se completa
        orden.estado = PickingOrder.Status.COMPLETADA

    orden.save(update_fields=["estado"])
