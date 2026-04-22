from django import forms
from catalog.models import Product
from warehouse.models import Location
from warehouse.models import Container
from .models import Movement


class ContainerLocationForm(forms.Form):
    contenedor_id = forms.ModelChoiceField(
        queryset=Container.objects.all().order_by("codigo_contenedor"),
        label="Contenedor",
        empty_label="Seleccione un contenedor"
    )
    ubicacion_id = forms.ModelChoiceField(
        queryset=Location.objects.all().order_by("codigo"),
        label="Ubicación",
        empty_label="Seleccione una ubicación"
    )


class MovementForm(forms.Form):
    contenedor_origen_id = forms.ModelChoiceField(
        queryset=Container.objects.all().order_by("codigo_contenedor"),
        label="Contenedor origen",
        empty_label="Seleccione un contenedor"
    )

    producto_id = forms.ModelChoiceField(
        queryset=Product.objects.none(),
        label="Producto",
        empty_label="Seleccione un producto",
        widget=forms.Select(attrs={"class": "form-select"})
    )

    contenedor_id = forms.ModelChoiceField(
        queryset=Container.objects.all().order_by("codigo_contenedor"),
        label="Contenedor destino",
        empty_label="Seleccione un contenedor"
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
        contenedor = cleaned_data.get("contenedor_id")
        tipo = cleaned_data.get("tipo")
        cantidad = cleaned_data.get("cantidad")

        if not producto:
            raise forms.ValidationError("Debes seleccionar un producto.")
        if not contenedor:
            raise forms.ValidationError("Debes seleccionar un contenedor.")
        if not tipo:
            raise forms.ValidationError(
                "Debes seleccionar un tipo de movimiento.")
        if cantidad is not None and cantidad <= 0:
            raise forms.ValidationError("La cantidad debe ser mayor que 0.")

        return cleaned_data
