from django import forms
from .models import PickingOrder, PickingDetail
from warehouse.models import ProductLocation, Location


class PickingOrderForm(forms.ModelForm):
    class Meta:
        model = PickingOrder
        fields = []  # solo se crea la orden con el supervisor (request.user)


class PickingDetailForm(forms.ModelForm):
    class Meta:
        model = PickingDetail
        fields = ["producto", "cantidad", "ubicacion",
                  "operario", "estado", "prioridad"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        producto_id = None

        # Caso 1: producto viene en POST
        if "producto" in self.data:
            try:
                producto_id = int(self.data.get("producto"))
            except (ValueError, TypeError):
                pass

        # Caso 2: producto ya existe en la instancia (edición)
        elif self.instance and self.instance.pk:
            producto_id = self.instance.producto_id

        # Si tenemos producto, filtramos ubicaciones
        if producto_id:
            qs = ProductLocation.objects.filter(producto_id=producto_id)
            ubicaciones = Location.objects.filter(
                id__in=qs.values("ubicacion_id"))
            self.fields["ubicacion"].queryset = ubicaciones

            def label_with_stock(obj):
                stock = qs.filter(ubicacion=obj).first()
                return f"{obj.codigo} (Stock: {stock.cantidad if stock else 0})"

            self.fields["ubicacion"].label_from_instance = label_with_stock
        else:
            self.fields["ubicacion"].queryset = Location.objects.none()

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
