from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F, Q
from django.shortcuts import render, redirect
from django.utils import timezone

from accounts.decorators import roles_permitidos
from catalog.models import Product
from picking.models import PickingDetail, PickingOrder
from warehouse.models import Location, ProductLocation

from .forms import MovementForm
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
        confirmado=False).count()

    ultimos_movimientos = Movement.objects.select_related(
        "producto", "ubicacion", "usuario"
    ).order_by("-fecha")[:10]

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
    ubicaciones = Location.objects.all().order_by("codigo")
    productos = Product.objects.all().order_by("sku")

    if request.method == "POST":
        form = MovementForm(request.POST)
        if form.is_valid():
            try:
                mov = registrar_movimiento(
                    producto_id=form.cleaned_data["producto_id"].id,
                    ubicacion_id=form.cleaned_data["ubicacion_id"].id,
                    tipo=form.cleaned_data["tipo"],
                    cantidad=form.cleaned_data["cantidad"],
                    usuario=request.user,
                )

                if mov.tipo == Movement.Types.UBICACION:
                    messages.success(
                        request,
                        f"Producto {mov.producto.sku} ubicado correctamente en {mov.ubicacion.codigo}."
                    )
                elif mov.producto.stock_actual <= mov.producto.stock_minimo:
                    messages.warning(
                        request,
                        f"⚠ Stock bajo: {mov.producto.sku} ({mov.producto.stock_actual} / mín {mov.producto.stock_minimo})"
                    )
                else:
                    messages.success(
                        request, "Movimiento registrado correctamente.")

                return redirect("inventory:movimiento_crear")

            except StockError as e:
                messages.error(request, str(e))
    else:
        form = MovementForm()

    bajo_stock = Product.objects.filter(
        stock_actual__lte=F("stock_minimo")
    ).count()

    asignaciones = ProductLocation.objects.select_related(
        "ubicacion", "producto"
    ).filter(
        producto__in=productos
    ).order_by(
        "producto__sku", "ubicacion__codigo"
    )

    ubicaciones_por_producto = {}
    for a in asignaciones:
        ubicaciones_por_producto.setdefault(
            a.producto_id, []).append(a.ubicacion.codigo)

    return render(request, "inventory/movimiento_crear.html", {
        "form": form,
        "productos": productos,
        "bajo_stock": bajo_stock,
        "ubicaciones_por_producto": ubicaciones_por_producto,
        "ubicaciones": ubicaciones,
        "tipos_movimiento": Movement.Types.choices,
    })


@roles_permitidos("ADMIN", "SUPERVISOR")
def movimientos_list(request):
    qs = Movement.objects.select_related(
        "producto", "ubicacion", "usuario"
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
