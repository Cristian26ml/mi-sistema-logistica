from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import user_passes_test
import uuid

from accounts.decorators import roles_permitidos
from accounts.permissions import (
    permiso_requerido,
    puede_consultar_ubicaciones,
    puede_gestionar_ubicaciones,
)
from .models import Location, ProductLocation, Container
from catalog.models import Product
from .forms import ProductLocationForm, GenerarUbicacionesForm
from django.contrib.auth.decorators import login_required


def es_supervisor_o_admin(user):
    return user.rol in ["SUPERVISOR", "ADMIN"]


@roles_permitidos("ADMIN", "SUPERVISOR")
def ubicaciones_list(request):
    if not puede_gestionar_ubicaciones(request.user):
        return HttpResponseForbidden("No tienes permiso para gestionar ubicaciones.")
    ubicaciones = Location.objects.all().order_by("codigo")
    return render(request, "warehouse/ubicaciones_list.html", {"ubicaciones": ubicaciones})


@roles_permitidos("ADMIN", "SUPERVISOR")
def asignaciones_list(request):
    if not puede_gestionar_ubicaciones(request.user):
        return HttpResponseForbidden("No tienes permiso para gestionar asignaciones.")
    asignaciones = ProductLocation.objects.select_related("producto", "ubicacion") \
        .order_by("producto__sku", "ubicacion__codigo")
    return render(request, "warehouse/asignaciones_list.html", {"asignaciones": asignaciones})


@roles_permitidos("ADMIN", "SUPERVISOR")
def ubicacion_generar(request):
    if not puede_gestionar_ubicaciones(request.user):
        return HttpResponseForbidden("No tienes permiso para gestionar ubicaciones.")

    if request.method == "POST":
        form = GenerarUbicacionesForm(request.POST)
        if form.is_valid():
            rack = form.cleaned_data["rack"]
            cantidad_posiciones = form.cleaned_data["cantidad_posiciones"]
            cantidad_niveles = form.cleaned_data["cantidad_niveles"]

            creadas = 0
            existentes = 0

            for posicion in range(1, cantidad_posiciones + 1):
                for nivel in range(1, cantidad_niveles + 1):
                    codigo = f"R{rack}-{posicion:02d}-{nivel:02d}"
                    descripcion = f"Rack {rack}, posición {posicion}, nivel {nivel}"

                    _, created = Location.objects.get_or_create(
                        codigo=codigo,
                        defaults={"descripcion": descripcion}
                    )

                    if created:
                        creadas += 1
                    else:
                        existentes += 1

            if creadas > 0 and existentes > 0:
                messages.warning(
                    request,
                    f"Se crearon {creadas} ubicaciones. {existentes} ya existían."
                )
            elif creadas > 0:
                messages.success(
                    request,
                    f"Se crearon correctamente {creadas} ubicaciones."
                )
            else:
                messages.info(
                    request,
                    "No se crearon ubicaciones nuevas porque ya existían."
                )

            return redirect("warehouse:ubicaciones_list")
    else:
        form = GenerarUbicacionesForm()

    return render(request, "warehouse/ubicacion_generar_form.html", {"form": form})


@user_passes_test(es_supervisor_o_admin)
def contenedor_generar(request):
    codigo = f"CON-{uuid.uuid4().int >> 64}"[:15]
    cont = Container.objects.create(codigo_contenedor=codigo)
    return redirect("warehouse:barcodes_dashboard")


@roles_permitidos("ADMIN", "SUPERVISOR")
def asignacion_crear(request):
    if request.method == "POST":
        form = ProductLocationForm(request.POST)
        if form.is_valid():
            asignacion = form.save()
            print("ASIGNACION GUARDADA:", asignacion.id,
                  asignacion.producto_id, asignacion.ubicacion_id)
            messages.success(
                request, "Asignación producto → ubicación creada.")
            return redirect("warehouse:asignaciones_list")
        else:
            print("ERRORES DEL FORMULARIO:", form.errors)
            messages.error(request, f"Formulario inválido: {form.errors}")
    else:
        form = ProductLocationForm()

    return render(request, "warehouse/asignacion_form.html", {"form": form})


@permiso_requerido(puede_consultar_ubicaciones)
def ubicacion_por_sku(request):
    sku = (request.GET.get("sku") or "").strip()
    producto = None
    ubicaciones = []

    if sku:
        producto = Product.objects.filter(sku__iexact=sku).first()

        if producto:
            ubicaciones = ProductLocation.objects.select_related("ubicacion") \
                .filter(producto=producto) \
                .order_by("ubicacion__codigo")

    return render(request, "warehouse/consulta_ubicacion.html", {
        "sku": sku,
        "producto": producto,
        "ubicaciones": ubicaciones,
    })


@login_required
def barcodes_dashboard(request):
    if request.user.rol not in ["ADMIN", "SUPERVISOR"]:
        return render(request, "403.html")

    locations = Location.objects.all()
    containers = Container.objects.all()
    return render(request, "warehouse/barcodes_dashboard.html", {
        "locations": locations,
        "containers": containers
    })
