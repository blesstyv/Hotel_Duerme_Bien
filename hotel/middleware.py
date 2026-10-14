"""Expiración por inactividad y cabeceras para la aplicación interna."""

import time

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout


class SessionSecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        authenticated = request.user.is_authenticated
        if authenticated:
            now = int(time.time())
            previous = request.session.get("ultima_actividad", now)
            timeout = getattr(settings, "SESSION_INACTIVITY_SECONDS", settings.SESSION_COOKIE_AGE)
            if not isinstance(previous, (int, float)) or now - previous > timeout or not request.user.is_active:
                logout(request)
                messages.info(request, "Su sesión expiró. Inicie sesión nuevamente.")
            else:
                request.session["ultima_actividad"] = now
        response = self.get_response(request)
        response.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.setdefault("Referrer-Policy", "same-origin")
        response.setdefault("X-Content-Type-Options", "nosniff")
        response.setdefault("X-Frame-Options", "DENY")
        response.setdefault("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'")
        if authenticated or request.path.startswith("/login"):
            response["Cache-Control"] = "no-store, private"
            response["Pragma"] = "no-cache"
        return response
