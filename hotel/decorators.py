"""Autorización excluyente aplicada a cada operación de la aplicación."""

from functools import wraps

from django.contrib.auth import logout
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

from .models import Usuario


def role_required(*roles):
    def decorate(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path(), "hotel:login")
            if not request.user.is_active:
                logout(request)
                return redirect_to_login(request.get_full_path(), "hotel:login")
            if request.user.rol not in roles:
                raise PermissionDenied("Su rol no tiene permiso para acceder a este módulo.")
            return view(request, *args, **kwargs)
        return wrapped
    return decorate


admin_required = role_required(Usuario.Rol.ADMINISTRADOR)
encargado_required = role_required(Usuario.Rol.ENCARGADO)
usuario_required = role_required(Usuario.Rol.ADMINISTRADOR, Usuario.Rol.ENCARGADO)
