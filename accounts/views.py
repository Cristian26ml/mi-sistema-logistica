from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import UserCreateForm
from accounts.permissions import es_admin


def login_view(request):
    if request.user.is_authenticated:
        return redirect("inventory:dashboard")

    form = AuthenticationForm(request, data=request.POST or None)

    form.fields["username"].widget.attrs.update({
        "placeholder": "Ingresa tu usuario",
        "autocomplete": "username",
    })

    form.fields["password"].widget.attrs.update({
        "placeholder": "Ingresa tu contraseña",
        "autocomplete": "current-password",
    })

    if request.method == "POST":
        if form.is_valid():
            user = form.get_user()

            if not getattr(user, "activo", True):
                messages.error(request, "Tu cuenta está desactivada.")
                return render(request, "accounts/login.html", {"form": form})

            login(request, user)
            messages.success(request, f"Bienvenido, {user.username}.")
            return redirect("inventory:dashboard")
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")

    return render(request, "accounts/login.html", {"form": form})


@login_required
def usuario_crear(request):
    if not es_admin(request.user):
        messages.error(request, "No tienes permiso para crear usuarios.")
        return redirect("inventory:dashboard")

    if request.method == "POST":
        form = UserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario creado correctamente.")
            return redirect("inventory:dashboard")
    else:
        form = UserCreateForm()

    return render(request, "accounts/usuario_form.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.success(request, "Sesión cerrada correctamente.")
    return redirect("accounts:login")
