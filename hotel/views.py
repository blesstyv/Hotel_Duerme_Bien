"""Casos de uso HTTP. La distribución y sus reglas viven en services."""

import hashlib
import json
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError, OperationalError, transaction
from django.db.models import Exists, OuterRef, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import constant_time_compare, salted_hmac
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .decorators import admin_required, encargado_required, usuario_required
from .forms import AsignacionForm, EncargadoCreationForm, EncargadoEditForm, HabitacionForm, LoginForm, PasajeroForm
from .models import Asignacion, DetalleHabitacionAsignada, Habitacion, Hospedaje, LoginIntento, Movimiento, Pasajero, Usuario
from .services import crear_asignacion, eliminar_habitacion, liberar_asignacion, registrar_movimiento, resumen_ocupacion, validar_asignacion

logger = logging.getLogger(__name__)
LOGIN_ERROR = "Usuario o contraseña incorrectos, o cuenta no disponible."
CONCURRENT_ERROR = "Los datos cambiaron o hay otra operación en curso. Actualice la página e intente nuevamente."


def _page(request, queryset, per_page=15):
    return Paginator(queryset, per_page).get_page(request.GET.get("page"))


def _q(request):
    return request.GET.get("q", "").strip()[:100]


def _validation_messages(error):
    return list(error.messages) if isinstance(error, ValidationError) else [CONCURRENT_ERROR]


def _add_operation_error(request, error):
    for message in _validation_messages(error):
        messages.error(request, message)


def _form_page(request, form, title, subtitle, cancel_name, nav_active, submit_label="Guardar cambios", objeto=None):
    return render(request, "hotel/entity_form.html", {"form": form, "title": title, "subtitle": subtitle, "cancel_url": reverse(f"hotel:{cancel_name}"), "submit_label": submit_label, "nav_active": nav_active, "objeto": objeto})


def _asignaciones():
    return Asignacion.objects.select_related("responsable", "registrada_por", "liberada_por").prefetch_related("detalles__habitacion", "detalles__hospedajes__pasajero").order_by("-fecha_ingreso")


@csrf_protect
@sensitive_post_parameters("password")
@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated and request.user.is_active:
        return redirect("hotel:inicio")
    form = LoginForm(request.POST if request.method == "POST" else None)
    status = 200
    if request.method == "POST" and form.is_valid():
        username = form.cleaned_data["username"]
        key = salted_hmac("hotel.login.throttle", username.strip().casefold()).hexdigest()
        maximum = getattr(settings, "LOGIN_MAX_FAILURES", 5)
        duration = getattr(settings, "LOGIN_LOCK_SECONDS", 300)
        now = timezone.now()
        user = None
        try:
            with transaction.atomic():
                attempt, _ = LoginIntento.objects.select_for_update().get_or_create(clave=key)
                if attempt.bloqueado_hasta and attempt.bloqueado_hasta > now:
                    form.add_error(None, "Demasiados intentos. Espere unos minutos antes de volver a intentar.")
                    status = 429
                else:
                    if attempt.bloqueado_hasta:
                        attempt.fallos = 0
                        attempt.bloqueado_hasta = None
                    user = authenticate(request, username=username, password=form.cleaned_data["password"])
                    if user is not None and user.is_active and user.rol in (Usuario.Rol.ADMINISTRADOR, Usuario.Rol.ENCARGADO):
                        attempt.fallos = 0
                        attempt.bloqueado_hasta = None
                    else:
                        user = None
                        attempt.fallos += 1
                        if attempt.fallos >= maximum:
                            attempt.bloqueado_hasta = now + timedelta(seconds=duration)
                        form.add_error(None, LOGIN_ERROR)
                    attempt.save(update_fields=["fallos", "bloqueado_hasta"])
            if user is not None:
                login(request, user)
                request.session.set_expiry(getattr(settings, "SESSION_COOKIE_AGE", 1800))
                registrar_movimiento(user, "Inicio de sesión", "Acceso autenticado al sistema.")
                next_url = request.POST.get("next", request.GET.get("next", ""))
                if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()) and next_url not in (reverse("hotel:login"), reverse("hotel:logout")):
                    return redirect(next_url)
                return redirect("hotel:inicio")
        except (IntegrityError, OperationalError):
            logger.warning("No se pudo completar la autenticación por concurrencia.")
            form.add_error(None, CONCURRENT_ERROR)
    return render(request, "hotel/login.html", {"form": form, "next": request.POST.get("next", request.GET.get("next", "")), "title": "Iniciar sesión"}, status=status)


@usuario_required
@require_POST
def logout_view(request):
    try:
        registrar_movimiento(request.user, "Cierre de sesión", "La sesión fue cerrada por el usuario.")
    except (IntegrityError, OperationalError):
        logger.warning("No se pudo registrar el cierre de sesión en la bitácora.")
    logout(request)
    messages.success(request, "Sesión cerrada correctamente.")
    return redirect("hotel:login")


@usuario_required
@require_GET
def inicio(request):
    return redirect("hotel:dashboard_admin" if request.user.rol == Usuario.Rol.ADMINISTRADOR else "hotel:dashboard_encargado")


@admin_required
@require_GET
def dashboard_admin(request):
    users = Usuario.objects.filter(rol=Usuario.Rol.ENCARGADO)
    stats = {"total": users.count(), "activos": users.filter(is_active=True).count(), "inactivos": users.filter(is_active=False).count()}
    context = {"stats": stats, "total_encargados": stats["total"], "activos": stats["activos"], "inactivos": stats["inactivos"], "movimientos": Movimiento.objects.filter(Q(usuario__rol=Usuario.Rol.ADMINISTRADOR) | Q(accion__icontains="encargado")).select_related("usuario").order_by("-fecha")[:8], "encargados": users.order_by("-date_joined")[:5], "title": "Panel de administración", "subtitle": "Control de accesos y cuentas del equipo", "nav_active": "dashboard"}
    return render(request, "hotel/dashboard_admin.html", context)


@encargado_required
@require_GET
def dashboard_encargado(request):
    stats = resumen_ocupacion()
    recent = _asignaciones()[:5]
    return render(request, "hotel/dashboard_encargado.html", {"stats": stats, "resumen": stats, "movimientos": Movimiento.objects.filter(usuario__rol=Usuario.Rol.ENCARGADO).select_related("usuario").order_by("-fecha")[:7], "asignaciones_recientes": recent, "asignaciones": recent, "title": "Panel del hotel", "subtitle": "Todo lo que necesita para gestionar la estadía", "nav_active": "dashboard"})


@admin_required
@require_GET
def encargado_list(request):
    q, estado = _q(request), request.GET.get("estado", "")
    queryset = Usuario.objects.filter(rol=Usuario.Rol.ENCARGADO).order_by("first_name", "username")
    if q:
        queryset = queryset.filter(Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q))
    if estado in ("activo", "activos"):
        queryset = queryset.filter(is_active=True)
    elif estado in ("inactivo", "inactivos"):
        queryset = queryset.filter(is_active=False)
    page = _page(request, queryset)
    return render(request, "hotel/encargado_list.html", {"encargados": page, "page_obj": page, "q": q, "estado": estado, "title": "Gestión de encargados", "subtitle": "Administre las cuentas de acceso al hotel", "nav_active": "encargados"})


@admin_required
@sensitive_post_parameters("password1", "password2")
@require_http_methods(["GET", "POST"])
def encargado_crear(request):
    form = EncargadoCreationForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                user = form.save()
                registrar_movimiento(request.user, "Registro de encargado", f"Se registró la cuenta {user.username}.")
            messages.success(request, "Encargado registrado correctamente.")
            return redirect("hotel:encargado_list")
        except (IntegrityError, OperationalError):
            form.add_error(None, "No se pudo registrar la cuenta. Verifique que el usuario sea único e intente nuevamente.")
    return _form_page(request, form, "Registrar encargado", "La nueva cuenta tendrá exclusivamente permisos de Encargado de Hotel.", "encargado_list", "encargados", "Crear encargado")


@admin_required
@sensitive_post_parameters("password1", "password2")
@require_http_methods(["GET", "POST"])
def encargado_editar(request, pk):
    user = get_object_or_404(Usuario, pk=pk, rol=Usuario.Rol.ENCARGADO)
    form = EncargadoEditForm(instance=user)
    if request.method == "POST":
        try:
            with transaction.atomic():
                user = get_object_or_404(Usuario.objects.select_for_update(), pk=pk, rol=Usuario.Rol.ENCARGADO)
                form = EncargadoEditForm(request.POST, instance=user)
                if form.is_valid():
                    user = form.save()
                    registrar_movimiento(request.user, "Edición de encargado", f"Se actualizaron los datos de la cuenta {user.username}.")
                    messages.success(request, "Encargado actualizado correctamente.")
                    return redirect("hotel:encargado_list")
        except (IntegrityError, OperationalError):
            form.add_error(None, "No se pudo actualizar la cuenta. Verifique el nombre de usuario e intente nuevamente.")
    return _form_page(request, form, "Editar encargado", "Modifique los datos o restablezca la contraseña del encargado.", "encargado_list", "encargados", objeto=user)


@admin_required
@require_POST
def encargado_estado(request, pk):
    try:
        with transaction.atomic():
            user = get_object_or_404(Usuario.objects.select_for_update(), pk=pk, rol=Usuario.Rol.ENCARGADO)
            user.is_active = not user.is_active
            user.save(update_fields=["is_active"])
            state = "activada" if user.is_active else "desactivada"
            registrar_movimiento(request.user, "Estado de encargado", f"Cuenta {user.username} {state}.")
        messages.success(request, f"Cuenta {state} correctamente.")
    except (IntegrityError, OperationalError) as error:
        _add_operation_error(request, error)
    return redirect("hotel:encargado_list")


@encargado_required
@require_GET
def habitacion_list(request):
    q, estado = _q(request), request.GET.get("estado", "")
    activa = request.GET.get("activa", "activas")
    orientacion = request.GET.get("orientacion", "")
    capacidad = request.GET.get("capacidad", "").strip()[:12]
    queryset = Habitacion.objects.all().order_by("numero")
    if activa in ("activas", "1", "true"):
        queryset = queryset.filter(activa=True)
    elif activa in ("inactivas", "0", "false"):
        queryset = queryset.filter(activa=False)
    if q:
        queryset = queryset.filter(numero__icontains=q)
    if estado in Habitacion.Estado.values:
        queryset = queryset.filter(estado=estado)
    if orientacion in dict(Habitacion._meta.get_field("orientacion").choices):
        queryset = queryset.filter(orientacion=orientacion)
    if capacidad:
        try:
            number = int(capacidad)
            if not 1 <= number <= 2147483647:
                raise ValueError
            queryset = queryset.filter(capacidad=number)
        except ValueError:
            messages.error(request, "El filtro de capacidad debe ser un número entero positivo.")
            queryset = queryset.none()
    page = _page(request, queryset)
    return render(request, "hotel/habitacion_list.html", {"habitaciones": page, "page_obj": page, "q": q, "estado": estado, "activa": activa, "orientacion": orientacion, "capacidad": capacidad, "estados": Habitacion.Estado.choices, "orientaciones": Habitacion._meta.get_field("orientacion").choices, "stats": resumen_ocupacion(), "title": "Habitaciones", "subtitle": "Capacidad, disponibilidad y orientación de cada habitación", "nav_active": "habitaciones"})


@encargado_required
@require_http_methods(["GET", "POST"])
def habitacion_crear(request):
    form = HabitacionForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                room = form.save(commit=False)
                room.estado = Habitacion.Estado.VACANTE
                room.activa = True
                room.save()
                registrar_movimiento(request.user, "Registro de habitación", f"Habitación {room.numero} registrada como vacante.")
            messages.success(request, "Habitación registrada como vacante.")
            return redirect("hotel:habitacion_list")
        except (IntegrityError, OperationalError):
            form.add_error(None, "No se pudo registrar la habitación. Verifique que el número sea único e intente nuevamente.")
    return _form_page(request, form, "Registrar habitación", "Toda habitación nueva comienza vacante y activa.", "habitacion_list", "habitaciones", "Registrar habitación")


@encargado_required
@require_http_methods(["GET", "POST"])
def habitacion_editar(request, pk):
    room = get_object_or_404(Habitacion, pk=pk)
    form = HabitacionForm(instance=room)
    if request.method == "POST":
        try:
            with transaction.atomic():
                room = get_object_or_404(Habitacion.objects.select_for_update(), pk=pk)
                form = HabitacionForm(request.POST, instance=room)
                if form.is_valid():
                    room = form.save()
                    registrar_movimiento(request.user, "Edición de habitación", f"Se actualizaron los datos de la habitación {room.numero}.")
                    messages.success(request, "Habitación actualizada correctamente.")
                    return redirect("hotel:habitacion_list")
        except (IntegrityError, OperationalError):
            form.add_error(None, "No se pudo actualizar la habitación. Verifique el número o actualice para consultar su estado actual.")
    return _form_page(request, form, "Editar habitación", "La capacidad de una habitación ocupada se conserva hasta registrar la salida.", "habitacion_list", "habitaciones", objeto=room)


@encargado_required
@require_POST
def habitacion_eliminar(request, pk):
    get_object_or_404(Habitacion, pk=pk)
    try:
        eliminar_habitacion(pk, request.user)
        messages.success(request, "Habitación desactivada. Su historial se conserva íntegramente.")
    except (ValidationError, IntegrityError, OperationalError) as error:
        _add_operation_error(request, error)
    return redirect("hotel:habitacion_list")


@encargado_required
@require_GET
def pasajero_list(request):
    q = _q(request)
    queryset = Pasajero.objects.annotate(es_responsable=Exists(Asignacion.objects.filter(responsable_id=OuterRef("pk"), estado=Asignacion.Estado.ACTIVA)), esta_hospedado=Exists(Hospedaje.objects.filter(pasajero_id=OuterRef("pk"), activa=True))).order_by("nombre_completo")
    if q:
        normalized = q.replace(".", "").replace(" ", "").upper()
        queryset = queryset.filter(Q(nombre_completo__icontains=q) | Q(rut__icontains=normalized) | Q(correo__icontains=q))
    estado = request.GET.get("estado", "")
    if estado == "hospedados":
        queryset = queryset.filter(esta_hospedado=True)
    elif estado == "responsables":
        queryset = queryset.filter(es_responsable=True)
    page = _page(request, queryset)
    return render(request, "hotel/pasajero_list.html", {"pasajeros": page, "page_obj": page, "q": q, "estado": estado, "title": "Pasajeros", "subtitle": "Registro único y consulta de huéspedes", "nav_active": "pasajeros"})


@encargado_required
@require_http_methods(["GET", "POST"])
def pasajero_crear(request):
    form = PasajeroForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                passenger = form.save()
                registrar_movimiento(request.user, "Registro de pasajero", f"Se registró el pasajero {passenger.nombre_completo}.")
            messages.success(request, "Pasajero registrado correctamente.")
            return redirect("hotel:pasajero_list")
        except (IntegrityError, OperationalError):
            form.add_error(None, "No se pudo registrar el pasajero. Verifique que su RUT no esté registrado e intente nuevamente.")
    return _form_page(request, form, "Registrar pasajero", "Cada RUT se registra una sola vez y conserva su historial.", "pasajero_list", "pasajeros", "Registrar pasajero")


@encargado_required
@require_http_methods(["GET", "POST"])
def pasajero_editar(request, pk):
    passenger = get_object_or_404(Pasajero, pk=pk)
    form = PasajeroForm(instance=passenger)
    if request.method == "POST":
        try:
            with transaction.atomic():
                passenger = get_object_or_404(Pasajero.objects.select_for_update(), pk=pk)
                form = PasajeroForm(request.POST, instance=passenger)
                if form.is_valid():
                    passenger = form.save()
                    registrar_movimiento(request.user, "Edición de pasajero", f"Se actualizaron los datos de {passenger.nombre_completo}.")
                    messages.success(request, "Pasajero actualizado correctamente.")
                    return redirect("hotel:pasajero_list")
        except (IntegrityError, OperationalError):
            form.add_error(None, "No se pudo actualizar el pasajero. Verifique el RUT e intente nuevamente.")
    return _form_page(request, form, "Editar pasajero", "Los registros históricos mantienen los datos de la estadía original.", "pasajero_list", "pasajeros", objeto=passenger)


@encargado_required
@require_GET
def asignacion_list(request):
    q, estado = _q(request), request.GET.get("estado", "")
    queryset = _asignaciones()
    if q:
        search = Q(responsable__nombre_completo__icontains=q) | Q(responsable__rut__icontains=q) | Q(detalles__numero_snapshot__icontains=q)
        if q.isascii() and q.isdecimal() and len(q) <= 19:
            identifier = int(q)
            if identifier <= 9223372036854775807:
                search |= Q(pk=identifier)
        queryset = queryset.filter(search).distinct()
    if estado in Asignacion.Estado.values:
        queryset = queryset.filter(estado=estado)
    page = _page(request, queryset)
    return render(request, "hotel/asignacion_list.html", {"asignaciones": page, "page_obj": page, "q": q, "estado": estado, "estados": Asignacion.Estado.choices, "title": "Asignaciones", "subtitle": "Ingresos, grupos y salidas del hotel", "nav_active": "asignaciones"})


def _distribution_fingerprint(distribution, responsible):
    canonical = {"distribucion": {str(key): sorted(values) for key, values in sorted(distribution.items())}, "responsable": responsible}
    return hashlib.sha256(json.dumps(canonical, sort_keys=True).encode()).hexdigest()


@encargado_required
@require_http_methods(["GET", "POST"])
def asignacion_crear(request):
    form = AsignacionForm(request.POST if request.method == "POST" else None)
    preview, preview_token = None, ""
    if request.method == "POST":
        action = request.POST.get("action", "preview")
        if action not in ("preview", "confirm"):
            form.add_error(None, "Seleccione una acción válida para la asignación.")
        elif form.is_valid():
            distribution = form.cleaned_data["distribucion"]
            responsible = form.cleaned_data["responsable"].pk
            fingerprint = _distribution_fingerprint(distribution, responsible)
            try:
                if action == "confirm":
                    previous = request.session.get("asignacion_preview", {})
                    token = request.POST.get("preview_token", "")
                    if not token or not constant_time_compare(token, previous.get("token", "")) or previous.get("fingerprint") != fingerprint:
                        raise ValidationError("Revise el resumen actualizado antes de confirmar la asignación.")
                    assignment = crear_asignacion(distribution, responsible, request.user)
                    request.session.pop("asignacion_preview", None)
                    messages.success(request, "Asignación confirmada. Las habitaciones quedaron ocupadas y el costo se calculó automáticamente.")
                    return redirect("hotel:asignacion_detalle", pk=assignment.pk)
                with transaction.atomic():
                    preview = validar_asignacion(distribution, responsible, request.user)
                preview_token = secrets.token_urlsafe(32)
                request.session["asignacion_preview"] = {"token": preview_token, "fingerprint": fingerprint}
            except (ValidationError, IntegrityError, OperationalError) as error:
                for message in _validation_messages(error):
                    form.add_error(None, message)
    rooms = Habitacion.objects.filter(activa=True, estado=Habitacion.Estado.VACANTE).order_by("numero")
    passengers = Pasajero.objects.exclude(hospedajes__activa=True).order_by("nombre_completo").distinct()
    selected_rooms = request.POST.getlist("rooms") if request.method == "POST" else []
    selected_by_room = {str(room.pk): request.POST.getlist(f"pasajeros_{room.pk}") for room in rooms}
    # El frontend recibe errores de todos los campos, incluidos los controles
    # de distribución que se renderizan manualmente.
    errors = [message for field_errors in form.errors.values() for message in field_errors] if form.is_bound else []
    return render(request, "hotel/asignacion_form.html", {"form": form, "errors": errors, "available_rooms": rooms, "passengers": passengers, "habitaciones_disponibles": rooms, "pasajeros_disponibles": passengers, "selected_rooms": selected_rooms, "selected_by_room": selected_by_room, "selected_responsable": request.POST.get("responsable", ""), "preview": preview, "preview_token": preview_token, "title": "Nueva asignación", "subtitle": "Distribuya el grupo y revise el resumen antes de confirmar", "nav_active": "asignaciones"})


@encargado_required
@require_GET
def asignacion_detalle(request, pk):
    assignment = get_object_or_404(_asignaciones(), pk=pk)
    return render(request, "hotel/asignacion_detail.html", {"asignacion": assignment, "detalles": assignment.detalles.all(), "title": f"Asignación #{assignment.pk}", "subtitle": "Detalle de la estadía y distribución del grupo", "nav_active": "asignaciones"})


@encargado_required
@require_POST
def asignacion_liberar(request, pk):
    get_object_or_404(Asignacion, pk=pk)
    try:
        liberar_asignacion(pk, request.user)
        messages.success(request, "Salida registrada. Todas las habitaciones de la asignación quedaron vacantes.")
    except (ValidationError, IntegrityError, OperationalError) as error:
        _add_operation_error(request, error)
    return redirect("hotel:asignacion_detalle", pk=pk)


@encargado_required
@require_GET
def ocupacion(request):
    stats = resumen_ocupacion()
    stays = Hospedaje.objects.filter(activa=True).select_related("pasajero", "detalle__habitacion", "detalle__asignacion__responsable").order_by("detalle__habitacion__numero", "pasajero__nombre_completo")
    return render(request, "hotel/ocupacion.html", {"stats": stats, "resumen": stats, "hospedajes": stays, "habitaciones": Habitacion.objects.filter(activa=True).order_by("numero"), "title": "Panel de ocupación", "subtitle": "Disponibilidad del hotel y huéspedes actualmente alojados", "nav_active": "ocupacion"})


@encargado_required
@require_GET
def historiales(request):
    q = _q(request)
    rooms = Habitacion.objects.order_by("numero")
    passengers = Pasajero.objects.order_by("nombre_completo")
    if q:
        rooms = rooms.filter(numero__icontains=q)
        passengers = passengers.filter(Q(nombre_completo__icontains=q) | Q(rut__icontains=q.replace(".", "").upper()))
    return render(request, "hotel/historiales.html", {"habitaciones": rooms, "pasajeros": passengers, "q": q, "title": "Historiales", "subtitle": "Consulte estadías anteriores y actuales sin alterar los registros", "nav_active": "historiales"})


@encargado_required
@require_GET
def habitacion_historial(request, pk):
    room = get_object_or_404(Habitacion, pk=pk)
    details = DetalleHabitacionAsignada.objects.filter(habitacion=room).select_related("asignacion__responsable", "habitacion").prefetch_related("hospedajes__pasajero").order_by("-asignacion__fecha_ingreso")
    page = _page(request, details)
    return render(request, "hotel/habitacion_historial.html", {"habitacion": room, "detalles": page, "page_obj": page, "title": f"Historial · Habitación {room.numero}", "subtitle": "Las habitaciones inactivas también conservan todas sus estadías", "nav_active": "historiales"})


@encargado_required
@require_GET
def pasajero_historial(request, pk):
    passenger = get_object_or_404(Pasajero, pk=pk)
    stays = Hospedaje.objects.filter(pasajero=passenger).select_related("detalle__habitacion", "detalle__asignacion__responsable", "pasajero").order_by("-detalle__asignacion__fecha_ingreso")
    page = _page(request, stays)
    return render(request, "hotel/pasajero_historial.html", {"pasajero": passenger, "hospedajes": page, "page_obj": page, "title": f"Historial · {passenger.nombre_completo}", "subtitle": "RUT, habitaciones, ingresos y salidas registrados", "nav_active": "historiales"})


def error_403(request, exception=None):
    return render(request, "hotel/error.html", {"code": 403, "title": "Acceso restringido", "message": "Su cuenta no tiene permiso para acceder a esta página."}, status=403)


def error_404(request, exception=None):
    return render(request, "hotel/error.html", {"code": 404, "title": "Página no encontrada", "message": "El registro o la página solicitada no existe."}, status=404)


def error_500(request):
    return render(request, "hotel/error.html", {"code": 500, "title": "No se pudo completar la solicitud", "message": "Intente nuevamente o contacte al administrador del sistema."}, status=500)


def csrf_failure(request, reason=""):
    return render(request, "hotel/error.html", {"code": 403, "title": "Formulario expirado", "message": "Actualice la página y vuelva a enviar el formulario."}, status=403)
