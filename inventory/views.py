from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F, Q
from django.shortcuts import render, redirect
from django.utils import timezone
from django.http import JsonResponse

from accounts.decorators import roles_permitidos
from catalog.models import Product
from picking.models import PickingDetail, PickingOrder
from warehouse.models import Container, ProductContainer

from .forms import MovementForm, ContainerLocationForm
from .models import Movement
from .services import registrar_movimiento, StockError


@login_required
def dashboard(request):
    hoy = timezone.localdate()

    total_productos = Product.objects.count()
    stock_bajo = Product.objects.filter(
        stock_actual__lte=F("stock_minimo")
    ).count()
    movimientos_hoy = Movement.objects.filter(fecha__date=hoy).count()
    pickings_pendientes = PickingDetail.objects.filter(
        estado="PENDIENTE"
    ).count()

    ultimos_movimientos = Movement.objects.select_related(
        "producto", "contenedor", "usuario"
    ).order_by("-fecha")[:10]
    ultimos_movimientos = Movement.objects.exclude(
        producto=None).order_by("-fecha")[:10]

    productos_stock_bajo = Product.objects.select_related(
        "categoria"
    ).filter(
        stock_actual__lte=F("stock_minimo")
    ).order_by("stock_actual", "sku")[:10]

    ultimas_ordenes = PickingOrder.objects.select_related(
        "supervisor"
    ).order_by("-fecha")[:10]

    return render(request, "inventory/dashboard.html", {
        "total_productos": total_productos,
        "stock_bajo": stock_bajo,
        "movimientos_hoy": movimientos_hoy,
        "pickings_pendientes": pickings_pendientes,
        "ultimos_movimientos": ultimos_movimientos,
        "productos_stock_bajo": productos_stock_bajo,
        "ultimas_ordenes": ultimas_ordenes,
    })


@roles_permitidos("ADMIN", "SUPERVISOR", "OPERARIO")
def movimiento_crear(request):
    contenedores = Container.objects.all().order_by("codigo_contenedor")
    productos = Product.objects.none()

    if request.method == "POST":
        form = MovementForm(request.POST)

        # 🔹 Recalcular queryset ANTES de validar
        contenedor_origen_id = request.POST.get("contenedor_origen_id")
        if contenedor_origen_id:
            try:
                contenedor_origen = Container.objects.get(
                    id=contenedor_origen_id)
                productos = Product.objects.filter(
                    inventory_product_containers__contenedor=contenedor_origen,
                    inventory_product_containers__cantidad__gt=0
                ).distinct().order_by("sku")
                form.fields["producto_id"].queryset = productos
            except Container.DoesNotExist:
                form.fields["producto_id"].queryset = Product.objects.none()
                contenedor_origen = None
        else:
            contenedor_origen = None

        print("DEBUG form errors:", form.errors)

        if form.is_valid():
            contenedor_destino = form.cleaned_data.get("contenedor_id")
            producto = form.cleaned_data.get("producto_id")
            tipo = form.cleaned_data.get("tipo")
            cantidad = form.cleaned_data.get("cantidad")

            # 🔹 Depuración: ver qué valores se pasan
            print("DEBUG movimiento:", {
                "producto_id": producto.id if producto else None,
                "contenedor_origen": contenedor_origen.id if contenedor_origen else None,
                "contenedor_destino": contenedor_destino.id if contenedor_destino else None,
                "tipo": tipo,
                "cantidad": cantidad,
            })
            try:
                mov = registrar_movimiento(
                    producto_id=producto.id,
                    contenedor_id=contenedor_destino.id,
                    contenedor_origen_id=contenedor_origen.id if contenedor_origen else None,
                    tipo=tipo,
                    cantidad=cantidad,
                    usuario=request.user,
                )

                origen_nombre = contenedor_origen.codigo_contenedor if contenedor_origen else "ALMACEN_VIRTUAL"
                messages.success(
                    request,
                    f"Producto {mov.producto.sku} movido de {origen_nombre} a {contenedor_destino.codigo_contenedor}."
                )
                return redirect("inventory:movimiento_crear")
            except StockError as e:
                messages.error(request, str(e))
                return redirect("inventory:movimiento_crear")

    else:
        form = MovementForm()
        contenedor_origen_id_str = request.GET.get("contenedor_origen_id")
        if contenedor_origen_id_str:
            try:
                contenedor_origen_id_int = int(contenedor_origen_id_str)
                productos = Product.objects.filter(
                    inventory_product_containers__contenedor_id=contenedor_origen_id_int,
                    inventory_product_containers__cantidad__gt=0
                ).distinct().order_by("sku")
                form.fields["producto_id"].queryset = productos
            except ValueError:
                form.fields["producto_id"].queryset = Product.objects.none()

    bajo_stock = Product.objects.filter(
        stock_actual__lte=F("stock_minimo")).count()

    return render(request, "inventory/movimiento_crear.html", {
        "form": form,
        "productos": productos,
        "contenedores": contenedores,
        "bajo_stock": bajo_stock,
        "tipos_movimiento": Movement.Types.choices,
    })


@roles_permitidos("ADMIN", "SUPERVISOR")
def movimientos_list(request):
    qs = Movement.objects.select_related(
        "producto", "contenedor", "usuario"
    ).order_by("-fecha")

    q = request.GET.get("q")
    tipo = request.GET.get("tipo")

    if q:
        qs = qs.filter(
            Q(producto__sku__icontains=q) |
            Q(usuario__username__icontains=q)
        )

    if tipo:
        qs = qs.filter(tipo=tipo)

    return render(request, "inventory/movimientos_list.html", {
        "movimientos": qs[:200],
        "tipos": Movement.Types.choices,
        "q": q or "",
        "tipo": tipo or "",
    })


@roles_permitidos("ADMIN", "SUPERVISOR", "OPERARIO")
def contenedor_a_ubicacion(request):
    if request.method == "POST":
        form = ContainerLocationForm(request.POST)
        if form.is_valid():
            contenedor = form.cleaned_data["contenedor_id"]
            ubicacion = form.cleaned_data["ubicacion_id"]

            contenedor.ubicacion = ubicacion
            contenedor.save(update_fields=["ubicacion"])

            Movement.objects.create(
                contenedor=contenedor,
                ubicacion=ubicacion,
                tipo=Movement.Types.UBICACION,
                cantidad=0,
                usuario=request.user,
            )

            messages.success(
                request,
                f"Contenedor {contenedor.codigo_contenedor} asignado a ubicación {ubicacion.codigo}."
            )
            return redirect("inventory:dashboard")
    else:
        form = ContainerLocationForm()

    return render(request, "inventory/contenedor_a_ubicacion.html", {"form": form})


@roles_permitidos("ADMIN", "SUPERVISOR", "OPERARIO")
def consultar_producto(request):
    """Consulta stock de un producto por SKU o código de barra"""
    sku = request.GET.get("sku")  # o código de barra
    stock = ProductContainer.objects.filter(
        producto__sku=sku).select_related("contenedor__ubicacion")

    data = [
        {
            "sku": s.producto.sku,
            "nombre": s.producto.nombre,
            "contenedor": s.contenedor.codigo_contenedor,
            "ubicacion": s.contenedor.ubicacion.codigo if s.contenedor.ubicacion else "Virtual (sin ubicación física)",
            "cantidad": s.cantidad,
        }
        for s in stock
    ]

    return JsonResponse({"productos": data})
# -------------------------------
# NUEVAS VISTAS PARA ESCANEO
# -------------------------------


@roles_permitidos("ADMIN", "SUPERVISOR", "OPERARIO")
def escanear_contenedor(request):
    """Recibe un código de barra y devuelve los productos del contenedor en JSON"""
    codigo = request.GET.get("codigo")
    contenedor = Container.objects.filter(
        codigo_contenedor__iexact=codigo).select_related("ubicacion").first()
    if not contenedor:
        return JsonResponse({"error": "Contenedor no encontrado"}, status=404)

    productos = ProductContainer.objects.filter(
        contenedor__codigo_contenedor__iexact=codigo
    ).select_related("producto")

    data = [
        {
            "producto_id": pc.producto.id,
            "sku": pc.producto.sku,
            "nombre": pc.producto.nombre,
            "cantidad": pc.cantidad,
            "contenedor_id": contenedor.id,
        }
        for pc in productos
    ]

    return JsonResponse({
        "contenedor": contenedor.codigo_contenedor,
        "contenedor_id": contenedor.id,
        "ubicacion": contenedor.ubicacion.codigo if contenedor.ubicacion else None,
        "productos": data
    })


@roles_permitidos("ADMIN", "SUPERVISOR", "OPERARIO")
def transferir_producto(request):
    """Procesa la transferencia desde un contenedor origen a destino"""
    if request.method == "POST":
        producto_id = request.POST.get("producto_id")
        cantidad = int(request.POST.get("cantidad"))
        contenedor_origen_id = request.POST.get("contenedor_origen_id")
        contenedor_destino_id = request.POST.get("contenedor_destino_id")

        try:
            mov = registrar_movimiento(
                producto_id=producto_id,
                tipo="TRANSFERENCIA",
                cantidad=cantidad,
                usuario=request.user,
                contenedor_id=contenedor_destino_id,
                contenedor_origen_id=contenedor_origen_id
            )
            messages.success(
                request, f"Transferencia exitosa de {cantidad} unidades.")
            return redirect("inventory:movimientos_list")
        except StockError as e:
            messages.error(request, str(e))
            return redirect("inventory:movimiento_crear")

    return JsonResponse({"error": "Método no permitido"}, status=405)


@roles_permitidos("ADMIN", "SUPERVISOR", "OPERARIO")
def movimiento_escaner(request):
    return render(request, "inventory/movimiento_escaner.html")


@roles_permitidos("ADMIN", "SUPERVISOR", "OPERARIO")
def productos_por_contenedor(request):
    contenedor_id = request.GET.get("contenedor_id")
    try:
        contenedor = Container.objects.get(id=contenedor_id)
    except Container.DoesNotExist:
        return JsonResponse({"productos": []})

    # 🔹 Usar el related_name correcto
    productos = Product.objects.filter(
        inventory_product_containers__contenedor=contenedor,
        inventory_product_containers__cantidad__gt=0
    ).distinct().order_by("sku")

    data = [
        {
            "id": p.id,
            "sku": p.sku,
            "nombre": p.nombre,
            "cantidad": p.inventory_product_containers.get(contenedor=contenedor).cantidad

        }
        for p in productos
    ]
    return JsonResponse({"productos": data})
