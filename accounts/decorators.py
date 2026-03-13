from django.contrib.auth.decorators import user_passes_test


def roles_permitidos(*roles):
    def check(user):
        return user.is_authenticated and (user.is_superuser or getattr(user, "rol", None) in roles)
    return user_passes_test(check)
