from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from django.db.models import F
from .models import Product, Category
from .forms import ProductForm, CategoryForm
from accounts.permissions import puede_gestionar_catalogo, puede_ver_productos


def productos_list(request):
    if not puede_ver_productos(request.user):
        return HttpResponseForbidden("No tienes permiso para ver productos.")

    productos = Product.objects.select_related(
        "categoria").all().order_by("sku")
    alerta_count = productos.filter(
        stock_actual__lte=F("stock_minimo")).count()

    return render(request, "catalog/productos_list.html", {
        "productos": productos,
        "alerta_count": alerta_count,
    })


def producto_crear(request):
    if not puede_gestionar_catalogo(request.user):
        return HttpResponseForbidden("No tienes permiso para crear productos.")

    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Producto creado correctamente.")
            return redirect("catalog:productos_list")
    else:
        form = ProductForm()

    return render(request, "catalog/producto_form.html", {"form": form})


def categoria_crear(request):
    if not puede_gestionar_catalogo(request.user):
        return HttpResponseForbidden("No tienes permiso para crear categorías.")

    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoría creada correctamente.")
            return redirect("catalog:productos_list")
    else:
        form = CategoryForm()

    return render(request, "catalog/categoria_form.html", {"form": form})
