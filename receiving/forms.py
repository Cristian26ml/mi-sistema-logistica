from django import forms
from .models import Receipt


class ReceiptForm(forms.ModelForm):
    class Meta:
        model = Receipt
        fields = [
            "proveedor",
            "numero_documento",
            "fecha_documento",
            "archivo",
            "observacion",
        ]
        widgets = {
            "fecha_documento": forms.DateInput(attrs={"type": "date"}),
            "observacion": forms.Textarea(attrs={"rows": 3}),
        }


class ReceiptImportForm(forms.Form):
    proveedor = forms.CharField(max_length=150, label="Proveedor")
    numero_documento = forms.CharField(max_length=50, label="Número documento")
    fecha_documento = forms.DateField(
        label="Fecha documento",
        widget=forms.DateInput(attrs={"type": "date"})
    )
    archivo = forms.FileField(label="Archivo Excel")

    def clean_archivo(self):
        archivo = self.cleaned_data["archivo"]
        nombre = archivo.name.lower()

        if not nombre.endswith(".xlsx"):
            raise forms.ValidationError("Debes subir un archivo .xlsx")

        return archivo


class ReceiptScanForm(forms.Form):
    codigo = forms.CharField(label="Código escaneado", max_length=100)

    cantidad = forms.IntegerField(
        min_value=1,
        initial=1,
        label="Cantidad recibida"
    )

    merma = forms.IntegerField(
        required=False,
        initial=0,
        min_value=0,
        label="Merma"
    )

    sobrante = forms.IntegerField(
        required=False,
        initial=0,
        min_value=0,
        label="Sobrante"
    )

    observacion = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2})
    )
