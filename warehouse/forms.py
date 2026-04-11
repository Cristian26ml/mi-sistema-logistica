from django import forms
from .models import ProductLocation


class ProductLocationForm(forms.ModelForm):
    class Meta:
        model = ProductLocation
        fields = ["producto", "ubicacion"]


class GenerarUbicacionesForm(forms.Form):
    rack = forms.CharField(
        max_length=2,
        label="Rack",
        help_text="Ejemplo: A, B, C"
    )

    cantidad_posiciones = forms.IntegerField(
        min_value=1,
        label="Cantidad de posiciones"
    )

    cantidad_niveles = forms.IntegerField(
        min_value=1,
        label="Cantidad de niveles"
    )

    def clean_rack(self):
        rack = self.cleaned_data["rack"].strip().upper()

        if not rack.isalpha():
            raise forms.ValidationError(
                "El rack debe contener solo letras."
            )

        return rack
