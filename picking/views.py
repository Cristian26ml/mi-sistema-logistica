from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import PickingOrder, PickingDetail
from accounts.decorators import roles_permitidos
from .forms import PickingDetailForm
from inventory.services import registrar_movimiento, StockError
from .services import actualizar_estado_orden


@roles_permitidos("ADMIN", "SUPERVISOR")
def ordenes_list(request):
    ordenes = PickingOrder.objects.select_related(
        "supervisor").order_by("-fecha")
    return render(request, "picking/ordenes_list.html", {"ordenes": ordenes})


@roles_permitidos("ADMIN", "SUPERVISOR")
def orden_crear(request):
    if request.method == "POST":
        factura_id = request.POST.get("factura")  # puede venir vacío
        orden = PickingOrder.objects.create(
            supervisor=request.user,
            factura=factura_id,  # si está vacío, el modelo genera uno automático
            estado=PickingOrder.Status.CREADA
        )
        messages.success(
            request, f"Orden N°{orden.numero_orden} creada para guía {orden.factura}.")
        return redirect("picking:orden_detalle", orden_id=orden.id)

    return render(request, "picking/orden_crear.html")


@roles_permitidos("ADMIN", "SUPERVISOR")
def orden_detalle(request, orden_id):
    orden = get_object_or_404(PickingOrder, id=orden_id)

    if request.method == "POST":
        form = PickingDetailForm(request.POST)
        if form.is_valid():
            detalle = form.save(commit=False)
            detalle.orden = orden
            detalle.save()

            actualizar_estado_orden(orden)

            messages.success(request, "Detalle agregado.")
            return redirect("picking:orden_detalle", orden_id=orden.id)
    else:
        form = PickingDetailForm()

    detalles = orden.detalles.select_related(
        "producto", "ubicacion", "operario")

    return render(request, "picking/orden_detalle.html", {
        "orden": orden,
        "form": form,
        "detalles": detalles,
    })


@roles_permitidos("ADMIN", "SUPERVISOR", "OPERARIO")
def mis_pickings(request):
    detalles = PickingDetail.objects.select_related(
        "producto", "ubicacion", "orden"
    ).filter(operario=request.user, estado="PENDIENTE")

    return render(request, "picking/mis_pickings.html", {
        "detalles": detalles
    })


@login_required
def confirmar_picking(request, detalle_id):
    detalle = get_object_or_404(PickingDetail, id=detalle_id)

    if detalle.confirmado:
        messages.warning(request, "Este picking ya fue confirmado.")
        return redirect("picking:mis_pickings")

    if request.user != detalle.operario and not request.user.is_superuser:
        messages.error(
            request, "No tienes permiso para confirmar este picking.")
        return redirect("picking:mis_pickings")

    try:
        registrar_movimiento(
            producto_id=detalle.producto.id,
            ubicacion_id=detalle.ubicacion.id,
            tipo="SALIDA",
            cantidad=detalle.cantidad,
            usuario=request.user,
        )

        detalle.confirmado = True
        detalle.confirmado_en = timezone.now()
        detalle.save(update_fields=["confirmado", "confirmado_en"])

        actualizar_estado_orden(detalle.orden)

        messages.success(request, "Picking confirmado y stock descontado.")

    except StockError as e:
        messages.error(request, str(e))

    return redirect("picking:mis_pickings")
