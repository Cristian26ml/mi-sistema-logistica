from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .forms import ReceiptForm, ReceiptImportForm
from .models import Receipt
from .services import importar_recepcion_desde_excel, ReceiptImportError

from .forms import ReceiptScanForm
from .models import ReceiptDetail
from catalog.models import Product

from .services import (
    aprobar_recepcion,
    ReceiptApprovalError,
)


def usuario_es_administrador(usuario):
    return usuario.is_superuser or getattr(usuario, "rol", "") == "ADMINISTRADOR"


def usuario_puede_recepcionar(usuario):
    return usuario.is_superuser or getattr(usuario, "rol", "") in ["ADMINISTRADOR", "SUPERVISOR", "OPERARIO"]


@login_required
def receipt_list(request):
    recepciones = Receipt.objects.all().order_by("-fecha_creacion")
    return render(request, "receiving/receipt_list.html", {
        "recepciones": recepciones
    })


@login_required
def receipt_create(request):
    if request.method == "POST":
        form = ReceiptForm(request.POST, request.FILES)
        if form.is_valid():
            recepcion = form.save(commit=False)
            recepcion.creado_por = request.user
            recepcion.save()
            messages.success(request, "Recepción creada correctamente.")
            return redirect("receiving:receipt_detail", receipt_id=recepcion.id)
    else:
        form = ReceiptForm()

    return render(request, "receiving/receipt_form.html", {
        "form": form
    })


@login_required
def receipt_import(request):
    if request.method == "POST":
        form = ReceiptImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                recepcion, filas_importadas, errores = importar_recepcion_desde_excel(
                    archivo=form.cleaned_data["archivo"],
                    proveedor=form.cleaned_data["proveedor"],
                    numero_documento=form.cleaned_data["numero_documento"],
                    fecha_documento=form.cleaned_data["fecha_documento"],
                    usuario=request.user,
                )

                if errores:
                    messages.warning(
                        request,
                        f"Recepción importada con {filas_importadas} filas válidas. "
                        f"Se detectaron {len(errores)} observaciones."
                    )
                    for error in errores[:10]:
                        messages.warning(request, error)
                else:
                    messages.success(
                        request,
                        f"Recepción importada correctamente con {filas_importadas} filas."
                    )

                return redirect("receiving:receipt_detail", receipt_id=recepcion.id)

            except ReceiptImportError as e:
                messages.error(request, str(e))
    else:
        form = ReceiptImportForm()

    return render(request, "receiving/receipt_import_form.html", {
        "form": form
    })


@login_required
def receipt_detail(request, receipt_id):
    recepcion = get_object_or_404(
        Receipt.objects.select_related("creado_por", "aprobado_por"),
        id=receipt_id
    )
    detalles = recepcion.detalles.select_related(
        "producto").order_by("producto__sku")

    total_lineas = detalles.count()
    total_unidades = sum(d.cantidad_esperada for d in detalles)

    es_administrador = usuario_es_administrador(request.user)
    puede_recepcionar = usuario_puede_recepcionar(request.user)

    if request.method == "POST" and "finalizar" in request.POST:
        observacion_general = request.POST.get("observacion", "").strip()
        recepcion.observacion = observacion_general
        # o el estado que uses al cerrar
        recepcion.estado = Receipt.Status.PENDIENTE_APROBACION
        recepcion.save(update_fields=["observacion", "estado"])
        messages.success(request, "Recepción finalizada correctamente.")
        return redirect("receiving:receipt_list")

    return render(request, "receiving/receipt_detail.html", {
        "recepcion": recepcion,
        "detalles": detalles,
        "total_lineas": total_lineas,
        "total_unidades": total_unidades,
        "es_administrador": es_administrador,
        "puede_recepcionar": puede_recepcionar,
    })


@login_required
def receipt_start(request, receipt_id):
    recepcion = get_object_or_404(Receipt, id=receipt_id)

    if request.method != "POST":
        return redirect("receiving:receipt_detail", receipt_id=recepcion.id)

    if not usuario_puede_recepcionar(request.user):
        messages.error(request, "No tienes permiso para iniciar la recepción.")
        return redirect("receiving:receipt_detail", receipt_id=recepcion.id)

    if recepcion.estado != Receipt.Status.BORRADOR:
        messages.warning(
            request,
            "Solo se puede iniciar una recepción que esté en estado Borrador."
        )
        return redirect("receiving:receipt_detail", receipt_id=recepcion.id)

    if not recepcion.detalles.exists():
        messages.error(
            request,
            "No puedes iniciar la recepción porque no tiene líneas cargadas."
        )
        return redirect("receiving:receipt_detail", receipt_id=recepcion.id)

    recepcion.estado = Receipt.Status.EN_RECEPCION
    recepcion.save(update_fields=["estado"])

    messages.success(request, "La recepción fue iniciada correctamente.")
    return redirect("receiving:receipt_detail", receipt_id=recepcion.id)


@login_required
def receipt_scan(request, receipt_id):
    recepcion = get_object_or_404(Receipt, id=receipt_id)

    if not usuario_puede_recepcionar(request.user):
        messages.error(
            request, "No tienes permiso para recepcionar productos.")
        return redirect("receiving:receipt_detail", receipt_id=recepcion.id)

    if recepcion.estado != Receipt.Status.EN_RECEPCION:
        messages.warning(request, "La recepción no está en proceso.")
        return redirect("receiving:receipt_detail", receipt_id=recepcion.id)

    detalle_encontrado = None

    if request.method == "POST":
        form = ReceiptScanForm(request.POST)
        if form.is_valid():
            codigo = form.cleaned_data["codigo"].strip()
            cantidad = form.cleaned_data["cantidad"]
            merma = form.cleaned_data.get("merma") or 0
            observacion = form.cleaned_data.get("observacion", "").strip()

            producto = Product.objects.filter(codigo_barra=codigo).first(
            ) or Product.objects.filter(sku=codigo).first()
            if producto:
                detalle_encontrado = recepcion.detalles.filter(producto=producto).first(
                ) or recepcion.detalles.filter(codigo_barra=codigo).first()
            else:
                detalle_encontrado = recepcion.detalles.filter(
                    codigo_barra=codigo).first()

            if detalle_encontrado:
                # Calcular nueva cantidad según botón
                if "registrar_escaneo" in request.POST:
                    nueva_cantidad = detalle_encontrado.cantidad_recibida + 1
                elif "ingresar_cantidades" in request.POST:
                    nueva_cantidad = detalle_encontrado.cantidad_recibida + cantidad
                elif "confirmar_sobre" in request.POST:
                    codigo = request.POST.get("codigo")
                    cantidad = int(request.POST.get("cantidad") or 0)
                    producto = Product.objects.filter(codigo_barra=codigo).first(
                    ) or Product.objects.filter(sku=codigo).first()
                    detalle_encontrado = recepcion.detalles.filter(producto=producto).first(
                    ) or recepcion.detalles.filter(codigo_barra=codigo).first()
                    nueva_cantidad = detalle_encontrado.cantidad_recibida + cantidad
                    messages.success(request, "Sobre‑recepción confirmada.")
                elif "cancelar_sobre" in request.POST:
                    messages.info(
                        request, "Operación cancelada, no se registró sobre‑recepción.")
                    nueva_cantidad = detalle_encontrado.cantidad_recibida
                else:
                    nueva_cantidad = detalle_encontrado.cantidad_recibida

                # Validar sobre‑recepción
                if nueva_cantidad > detalle_encontrado.cantidad_esperada and "confirmar_sobre" not in request.POST and "cancelar_sobre" not in request.POST:
                    messages.warning(
                        request,
                        f"Está intentando recepcionar más unidades ({nueva_cantidad}) que las solicitadas ({detalle_encontrado.cantidad_esperada}). ¿Desea continuar?"
                    )
                    return render(request, "receiving/receipt_scan.html", {
                        "recepcion": recepcion,
                        "form": form,
                        "detalles": recepcion.detalles.select_related("producto").order_by("id"),
                        "detalle_encontrado": detalle_encontrado,
                        "total_esperado": sum(d.cantidad_esperada for d in recepcion.detalles.all()),
                        "total_recibido": sum(d.cantidad_recibida for d in recepcion.detalles.all()),
                        "progreso": int((sum(d.cantidad_recibida for d in recepcion.detalles.all()) / sum(d.cantidad_esperada for d in recepcion.detalles.all())) * 100) if sum(d.cantidad_esperada for d in recepcion.detalles.all()) > 0 else 0,
                    })

                # Guardar cambios (normal o sobre‑recepción confirmada)
                detalle_encontrado.cantidad_recibida = nueva_cantidad
                detalle_encontrado.incidencia_merma += merma

                # 🔑 Calcular sobrante automáticamente
                if detalle_encontrado.cantidad_recibida > detalle_encontrado.cantidad_esperada:
                    detalle_encontrado.incidencia_sobrante = detalle_encontrado.cantidad_recibida - \
                        detalle_encontrado.cantidad_esperada
                else:
                    detalle_encontrado.incidencia_sobrante = 0

                # Calcular faltante
                detalle_encontrado.incidencia_faltante = max(
                    detalle_encontrado.cantidad_esperada - detalle_encontrado.cantidad_recibida, 0)

                if detalle_encontrado.cantidad_recibida >= detalle_encontrado.cantidad_esperada:
                    detalle_encontrado.recepcionado = True
                if observacion:
                    detalle_encontrado.observacion = observacion

                detalle_encontrado.save(update_fields=[
                    "cantidad_recibida", "incidencia_merma", "incidencia_sobrante",
                    "incidencia_faltante", "recepcionado", "observacion"
                ])
                messages.success(
                    request, f"Recepción registrada para {detalle_encontrado.nombre or detalle_encontrado.producto.nombre}.")
            else:
                messages.error(
                    request, "Código no reconocido en catálogo ni en esta recepción.")

        # Recalcular totales y limpiar form
        detalles = recepcion.detalles.select_related("producto").order_by("id")
        total_esperado = sum(d.cantidad_esperada for d in detalles)
        total_recibido = sum(d.cantidad_recibida for d in detalles)
        progreso = int((total_recibido / total_esperado)
                       * 100) if total_esperado > 0 else 0
        form = ReceiptScanForm()
    else:
        form = ReceiptScanForm()
        detalles = recepcion.detalles.select_related("producto").order_by("id")
        total_esperado = sum(d.cantidad_esperada for d in detalles)
        total_recibido = sum(d.cantidad_recibida for d in detalles)
        progreso = int((total_recibido / total_esperado)
                       * 100) if total_esperado > 0 else 0

    return render(request, "receiving/receipt_scan.html", {
        "recepcion": recepcion,
        "form": form,
        "detalles": detalles,
        "detalle_encontrado": detalle_encontrado,
        "total_esperado": total_esperado,
        "total_recibido": total_recibido,
        "progreso": progreso,
    })


@login_required
def receipt_finish(request, receipt_id):
    recepcion = get_object_or_404(Receipt, id=receipt_id)

    if not usuario_puede_recepcionar(request.user):
        messages.error(
            request, "No tienes permiso para finalizar recepciones.")
        return redirect("receiving:receipt_detail", receipt_id=recepcion.id)

    if recepcion.estado != Receipt.Status.EN_RECEPCION:
        messages.warning(request, "La recepción no está en proceso.")
        return redirect("receiving:receipt_detail", receipt_id=recepcion.id)

    if request.method == "POST":
        observacion_general = request.POST.get("observacion", "").strip()
        recepcion.observacion = observacion_general
        recepcion.estado = Receipt.Status.PENDIENTE_APROBACION  # o el estado que uses
        recepcion.save(update_fields=["observacion", "estado"])
        messages.success(request, "Recepción finalizada correctamente.")
        return redirect("receiving:receipt_list")

    return redirect("receiving:receipt_detail", receipt_id=recepcion.id)


@login_required
def receipt_approve(request, receipt_id):
    recepcion = get_object_or_404(Receipt, id=receipt_id)

    if request.method != "POST":
        return redirect("receiving:receipt_detail", receipt_id=receipt_id)

    if not usuario_es_administrador(request.user):
        messages.error(
            request, "Solo el Administrador puede aprobar la recepción.")
        return redirect("receiving:receipt_detail", receipt_id=receipt_id)

    try:
        aprobar_recepcion(
            recepcion=recepcion,
            usuario=request.user,
        )
        messages.success(request, "Recepción aprobada correctamente.")
    except ReceiptApprovalError as e:
        messages.error(request, str(e))

    return redirect("receiving:receipt_detail", receipt_id=receipt_id)
