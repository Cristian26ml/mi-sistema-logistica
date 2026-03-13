from functools import wraps
from django.http import HttpResponseForbidden


def es_admin(user):
    return user.is_authenticated and (
        user.is_superuser or user.rol == "ADMIN"
    )


def es_supervisor(user):
    return user.is_authenticated and user.rol == "SUPERVISOR"


def es_operario(user):
    return user.is_authenticated and user.rol == "OPERARIO"


def es_admin_o_supervisor(user):
    return user.is_authenticated and (
        user.is_superuser or user.rol in ["ADMIN", "SUPERVISOR"]
    )


def es_usuario_logistico(user):
    return user.is_authenticated and (
        user.is_superuser or user.rol in ["ADMIN", "SUPERVISOR", "OPERARIO"]
    )


# CATÁLOGO
def puede_ver_productos(user):
    return es_admin_o_supervisor(user)


def puede_gestionar_catalogo(user):
    return es_admin_o_supervisor(user)


# INVENTARIO
def puede_registrar_movimiento(user):
    return es_usuario_logistico(user)


def puede_ver_movimientos(user):
    return es_admin_o_supervisor(user)

# ALMACÉN


def puede_consultar_ubicaciones(user):
    return user.is_authenticated and (
        user.is_superuser or user.rol in ["ADMIN", "SUPERVISOR", "OPERARIO"]
    )


def puede_gestionar_ubicaciones(user):
    return es_admin_o_supervisor(user)


def puede_gestionar_asignaciones(user):
    return es_admin_o_supervisor(user)


# PICKING
def puede_crear_picking(user):
    return es_admin_o_supervisor(user)


def puede_ver_ordenes_picking(user):
    return es_admin_o_supervisor(user)


def puede_ver_mis_pickings(user):
    return es_usuario_logistico(user)


def puede_confirmar_picking(user, detalle):
    if not user.is_authenticated:
        return False

    if user.is_superuser or user.rol in ["ADMIN", "SUPERVISOR"]:
        return True

    return detalle.operario_id == user.id


# USUARIOS
def puede_gestionar_usuarios(user):
    return es_admin(user)


def permiso_requerido(func_permiso):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not func_permiso(request.user):
                return HttpResponseForbidden(
                    "No tienes permiso para acceder a esta sección."
                )
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
