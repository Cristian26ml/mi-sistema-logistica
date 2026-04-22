from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import user_passes_test
from .forms import ProductContainerForm
import uuid
from accounts.decorators import roles_permitidos
from accounts.permissions import (
    permiso_requerido,
    puede_consultar_ubicaciones,
    puede_gestionar_ubicaciones,
)
from django.db import models
from .models import Location, Container, ProductContainer
from catalog.models import Product
from .forms import GenerarUbicacionesForm
from django.contrib.auth.decorators import login_required
import io
import base64


def es_supervisor_o_admin(user):
    return user.rol in ["SUPERVISOR", "ADMIN"]


def generar_barcode(request):
    if request.method == "POST":
        codigo = request.POST.get("codigo")

        # Generar código de barras en memoria
        ean = barcode.get('code128', codigo, writer=ImageWriter())
        buffer = io.BytesIO()
        ean.write(buffer)

        # Convertir a base64 para incrustar en HTML
        image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return render(request, "warehouse/barcode_imprimir.html", {
            "codigo": codigo,
            "imagen_base64": image_base64
        })

    return render(request, "warehouse/generar_barcode.html")


@roles_permitidos("ADMIN", "SUPERVISOR")
def ubicaciones_list(request):
    if not puede_gestionar_ubicaciones(request.user):
        return HttpResponseForbidden("No tienes permiso para gestionar ubicaciones.")
    ubicaciones = Location.objects.all().order_by("codigo")
    return render(request, "warehouse/ubicaciones_list.html", {"ubicaciones": ubicaciones})


@roles_permitidos("ADMIN", "SUPERVISOR")
def asignaciones_list(request):
    asignaciones = ProductContainer.objects.select_related("producto", "contenedor") \
        .order_by("producto__sku", "contenedor__codigo_contenedor")
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
    messages.success(
        request, f"Contenedor {codigo} generado por {request.user.username}.")
    return redirect("warehouse:barcodes_dashboard")


@roles_permitidos("ADMIN", "SUPERVISOR")
def asignacion_crear(request):
    if request.method == "POST":
        form = ProductContainerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request, "Asignación producto → contenedor creada.")
            return redirect("warehouse:asignaciones_list")
        else:
            messages.error(request, f"Formulario inválido: {form.errors}")
    else:
        form = ProductContainerForm()

    return render(request, "warehouse/asignacion_form.html", {"form": form})


@roles_permitidos("ADMIN", "SUPERVISOR", "OPERARIO")
def ubicacion_por_codigo_barra(request):
    codigo_barra = (request.GET.get("codigo_barra") or "").strip()
    producto = None
    ubicaciones = []
    tipo = None  # 🔹 nuevo flag

    if codigo_barra:
        # 1. Producto
        producto = Product.objects.filter(
            models.Q(codigo_barra__iexact=codigo_barra) |
            models.Q(sku__iexact=codigo_barra)
        ).first()
        if producto:
            ubicaciones = ProductContainer.objects.select_related(
                "contenedor__ubicacion"
            ).filter(producto=producto)
            tipo = "producto"

        else:
            # 2. Ubicación
            ubicacion = Location.objects.filter(
                models.Q(codigo__iexact=codigo_barra) |
                models.Q(codigo_ubicacion__iexact=codigo_barra)
            ).first()
            if ubicacion:
                ubicaciones = ProductContainer.objects.select_related(
                    "producto", "contenedor__ubicacion"
                ).filter(contenedor__ubicacion=ubicacion)
                tipo = "ubicacion"

            else:
                # 3. Contenedor
                contenedor = Container.objects.filter(
                    codigo_contenedor__iexact=codigo_barra
                ).select_related("ubicacion").first()
                if contenedor:
                    ubicaciones = ProductContainer.objects.select_related(
                        "producto", "contenedor__ubicacion"
                    ).filter(contenedor=contenedor)
                    tipo = "contenedor"

    return render(request, "warehouse/consulta_ubicacion.html", {
        "codigo_barra": codigo_barra,
        "producto": producto,
        "ubicaciones": ubicaciones,
        "tipo": tipo,  # 🔹 pasamos el flag
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
