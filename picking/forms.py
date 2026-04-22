from django import forms
from .models import PickingOrder, PickingDetail
from inventory.models import ProductContainer
from warehouse.models import Container


class PickingOrderForm(forms.ModelForm):
    class Meta:
        model = PickingOrder
        fields = ["supervisor"]


class PickingDetailForm(forms.ModelForm):
    class Meta:
        model = PickingDetail
        fields = ["producto", "cantidad", "contenedor",
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

        # Si tenemos producto, filtramos contenedores
        if producto_id:
            qs = ProductContainer.objects.filter(
                producto_id=producto_id).select_related("contenedor")
            contenedores = Container.objects.filter(
                id__in=qs.values("contenedor_id"))
            self.fields["contenedor"].queryset = contenedores

            def label_with_stock(obj):
                stock = qs.filter(contenedor=obj).first()
                return f"{obj.codigo_contenedor} (Stock: {stock.cantidad if stock else 0})"

            self.fields["contenedor"].label_from_instance = label_with_stock
        else:
            self.fields["contenedor"].queryset = Container.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        producto = cleaned_data.get("producto")
        contenedor = cleaned_data.get("contenedor")

        if producto and contenedor:
            existe = ProductContainer.objects.filter(
                producto=producto,
                contenedor=contenedor
            ).exists()

            if not existe:
                raise forms.ValidationError(
                    "El contenedor seleccionado no tiene asignado ese producto."
                )

        return cleaned_data
