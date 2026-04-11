from django import forms
from .models import User


class UserCreateForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ["username", "first_name",
                  "last_name", "email", "rol", "activo"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Inputs normales
        self.fields["username"].widget.attrs.update({"class": "form-control"})
        self.fields["first_name"].widget.attrs.update(
            {"class": "form-control"})
        self.fields["last_name"].widget.attrs.update({"class": "form-control"})
        self.fields["email"].widget.attrs.update({"class": "form-control"})

        # Select
        self.fields["rol"].widget.attrs.update({"class": "form-select"})

        # Checkbox
        self.fields["activo"].widget.attrs.update(
            {"class": "form-check-input"})

        # Passwords
        self.fields["password1"].widget.attrs.update({"class": "form-control"})
        self.fields["password2"].widget.attrs.update({"class": "form-control"})

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = self.cleaned_data.get("activo", True)
        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()

        return user
