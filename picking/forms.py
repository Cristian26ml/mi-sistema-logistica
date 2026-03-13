from django import forms
from .models import PickingOrder, PickingDetail
from warehouse.models import ProductLocation


class PickingOrderForm(forms.ModelForm):
    class Meta:
        model = PickingOrder
        fields = []  # solo se crea la orden con el supervisor (request.user)


class PickingDetailForm(forms.ModelForm):
    class Meta:
        model = PickingDetail
        fields = ["producto", "cantidad", "ubicacion", "operario"]

    def clean(self):
        cleaned_data = super().clean()
        producto = cleaned_data.get("producto")
        ubicacion = cleaned_data.get("ubicacion")

        if producto and ubicacion:
            existe = ProductLocation.objects.filter(
                producto=producto,
                ubicacion=ubicacion
            ).exists()

            if not existe:
                raise forms.ValidationError(
                    "La ubicación seleccionada no está asignada a ese producto."
                )

        return cleaned_data
