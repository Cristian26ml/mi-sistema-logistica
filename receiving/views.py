from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .forms import ReceiptForm, ReceiptImportForm
from .models import Receipt
from .services import importar_recepcion_desde_excel, ReceiptImportError


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
            return redirect("receiving:receipt_list")
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

                return redirect("receiving:receipt_list")

            except ReceiptImportError as e:
                messages.error(request, str(e))
    else:
        form = ReceiptImportForm()

    return render(request, "receiving/receipt_import_form.html", {
        "form": form
    })
