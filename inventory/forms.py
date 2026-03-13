from django import forms
from catalog.models import Product
from warehouse.models import Location
from .models import Movement


class MovementForm(forms.Form):
    producto_id = forms.ModelChoiceField(
        queryset=Product.objects.all().order_by("sku"),
        label="Producto",
        empty_label="Seleccione un producto"
    )
    ubicacion_id = forms.ModelChoiceField(
        queryset=Location.objects.all().order_by("codigo"),
        label="Ubicación",
        empty_label="Seleccione una ubicación"
    )
    tipo = forms.ChoiceField(
        choices=Movement.Types.choices,
        label="Tipo de movimiento"
    )
    cantidad = forms.IntegerField(
        min_value=1,
        label="Cantidad"
    )

    def clean(self):
        cleaned_data = super().clean()
        producto = cleaned_data.get("producto_id")
        ubicacion = cleaned_data.get("ubicacion_id")
        tipo = cleaned_data.get("tipo")
        cantidad = cleaned_data.get("cantidad")

        if not producto:
            raise forms.ValidationError("Debes seleccionar un producto.")

        if not ubicacion:
            raise forms.ValidationError("Debes seleccionar una ubicación.")

        if not tipo:
            raise forms.ValidationError(
                "Debes seleccionar un tipo de movimiento.")

        if cantidad is not None and cantidad <= 0:
            raise forms.ValidationError("La cantidad debe ser mayor que 0.")

        return cleaned_data
