from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("usuario/crear/", views.usuario_crear, name="usuario_crear"),
    path("logout/", views.logout_view, name="logout"),
]
