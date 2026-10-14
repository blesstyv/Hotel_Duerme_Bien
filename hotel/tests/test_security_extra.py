"""Regresiones de integridad histórica y entradas HTTP manipuladas."""

from datetime import timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import Client, override_settings
from django.urls import reverse
from django.utils import timezone

from hotel.models import Asignacion, DetalleHabitacionAsignada, Habitacion, Hospedaje, LoginIntento, Movimiento, Pasajero, Usuario
from hotel.services import crear_asignacion, liberar_asignacion

from .base import HotelTestCase, PASSWORD


def url(name, pk=None):
    return reverse(f"hotel:{name}", kwargs={"pk": pk} if pk is not None else None)


class HistoricalIntegritySecurityTests(HotelTestCase):
    def assignment(self, closed=False):
        result = crear_asignacion({self.room1.pk: [self.people[0].pk]}, self.people[0].pk, self.encargado)
        return liberar_asignacion(result.pk, self.encargado) if closed else result

    def test_queryset_cannot_physically_delete_room_without_history(self):
        with self.assertRaises(ValidationError):
            Habitacion.objects.filter(pk=self.room3.pk).delete()
        self.assertTrue(Habitacion.objects.filter(pk=self.room3.pk).exists())

    def test_queryset_cannot_physically_delete_passenger_without_history(self):
        with self.assertRaises(ValidationError):
            Pasajero.objects.filter(pk=self.people[-1].pk).delete()
        self.assertTrue(Pasajero.objects.filter(pk=self.people[-1].pk).exists())

    def test_queryset_fk_alias_cannot_change_responsible(self):
        assignment = self.assignment()
        with self.assertRaises(ValidationError):
            Asignacion.objects.filter(pk=assignment.pk).update(responsable=self.people[1])
        assignment.refresh_from_db()
        self.assertEqual(assignment.responsable_id, self.people[0].pk)

    def test_queryset_fk_alias_cannot_change_author(self):
        assignment = self.assignment()
        with self.assertRaises(ValidationError):
            Asignacion.objects.filter(pk=assignment.pk).update(registrada_por=self.admin_user)

    def test_queryset_fk_alias_cannot_change_audit_author(self):
        self.assignment()
        with self.assertRaises(ValidationError):
            Movimiento.objects.all().update(usuario=self.admin_user)

    def test_bulk_update_cannot_change_responsible(self):
        assignment = self.assignment()
        assignment.responsable = self.people[1]
        with self.assertRaises(ValidationError):
            Asignacion.objects.bulk_update([assignment], ["responsable"])

    def test_finalized_exit_timestamp_is_immutable(self):
        assignment = self.assignment(closed=True)
        original_exit = assignment.fecha_salida
        assignment.fecha_salida += timedelta(days=1)
        with self.assertRaises(ValidationError):
            assignment.save(update_fields=["fecha_salida"])
        assignment.refresh_from_db()
        self.assertEqual(assignment.fecha_salida, original_exit)

    def test_finalized_exit_author_is_immutable(self):
        assignment = self.assignment(closed=True)
        assignment.liberada_por = self.inactive
        with self.assertRaises(ValidationError):
            assignment.save(update_fields=["liberada_por"])

    def test_finalized_assignment_cannot_reopen_through_queryset(self):
        assignment = self.assignment(closed=True)
        with self.assertRaises(ValidationError):
            Asignacion.objects.filter(pk=assignment.pk).update(estado=Asignacion.Estado.ACTIVA, fecha_salida=None, liberada_por=None)
        assignment.refresh_from_db()
        self.assertEqual(assignment.estado, Asignacion.Estado.FINALIZADA)

    def test_finalized_room_detail_cannot_be_reactivated(self):
        assignment = self.assignment(closed=True)
        detail = assignment.detalles.get()
        with self.assertRaises(ValidationError):
            DetalleHabitacionAsignada.objects.filter(pk=detail.pk).update(activa=True)

    def test_finalized_stay_cannot_be_reactivated(self):
        assignment = self.assignment(closed=True)
        stay = Hospedaje.objects.get(detalle__asignacion=assignment)
        stay.activa = True
        with self.assertRaises(ValidationError):
            stay.save(update_fields=["activa"])

    def test_snapshot_updates_rejected(self):
        assignment = self.assignment()
        with self.assertRaises(ValidationError):
            assignment.detalles.update(numero_snapshot="999")
        with self.assertRaises(ValidationError):
            Hospedaje.objects.filter(detalle__asignacion=assignment).update(nombre_snapshot="Otro nombre")

    def test_service_rechecks_deactivated_account_despite_stale_object(self):
        self.assertTrue(self.encargado.is_active)
        Usuario.objects.filter(pk=self.encargado.pk).update(is_active=False)
        with self.assertRaises(PermissionDenied):
            self.assignment()
        self.assertFalse(Asignacion.objects.exists())

    def test_service_rechecks_changed_role_despite_stale_object(self):
        self.assertEqual(self.encargado.rol, Usuario.Rol.ENCARGADO)
        Usuario.objects.filter(pk=self.encargado.pk).update(rol=Usuario.Rol.ADMINISTRADOR)
        with self.assertRaises(PermissionDenied):
            self.assignment()
        self.assertFalse(Asignacion.objects.exists())


class HttpSecurityEdgeCaseTests(HotelTestCase):
    def setUp(self):
        self.client.force_login(self.encargado)

    def distribution(self):
        return {"rooms": [str(self.room1.pk)], f"pasajeros_{self.room1.pk}": [str(self.people[0].pk)], "responsable": str(self.people[0].pk)}

    def test_huge_and_malformed_assignment_ids_rejected_safely(self):
        for invalid in ("9" * 100, "1.5", "NaN", "-1", "²"):
            with self.subTest(identifier=invalid):
                response = self.client.post(url("asignacion_crear"), {**self.distribution(), "rooms": [invalid], "action": "preview"})
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context["form"].errors)
        self.assertFalse(Asignacion.objects.exists())

    def test_malformed_capacity_filter_does_not_crash(self):
        for invalid in ("-1", "0", "9" * 100, "NaN", "²", "1.5"):
            with self.subTest(capacity=invalid):
                response = self.client.get(url("habitacion_list"), {"capacidad": invalid})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(len(response.context["habitaciones"]), 0)

    def test_unusual_numeric_assignment_search_does_not_crash(self):
        for query in ("9" * 100, "²", "٠١٢"):
            with self.subTest(query=query):
                self.assertEqual(self.client.get(url("asignacion_list"), {"q": query}).status_code, 200)

    def test_duplicate_raw_passenger_selection_rejected(self):
        response = self.client.post(url("asignacion_crear"), {**self.distribution(), f"pasajeros_{self.room1.pk}": [str(self.people[0].pk)] * 2, "action": "preview"})
        self.assertTrue(response.context["form"].errors)
        self.assertFalse(Asignacion.objects.exists())

    def test_preview_token_cannot_be_reused_after_confirmation(self):
        data = self.distribution()
        preview = self.client.post(url("asignacion_crear"), {**data, "action": "preview"})
        token = preview.context["preview_token"]
        response = self.client.post(url("asignacion_crear"), {**data, "action": "confirm", "preview_token": token})
        self.assertEqual(response.status_code, 302)
        assignment = Asignacion.objects.get()
        liberar_asignacion(assignment.pk, self.encargado)
        response = self.client.post(url("asignacion_crear"), {**data, "action": "confirm", "preview_token": token})
        self.assertTrue(response.context["form"].errors)
        self.assertEqual(Asignacion.objects.count(), 1)

    def test_password_reset_revokes_existing_session(self):
        admin_client = Client()
        admin_client.force_login(self.admin_user)
        response = admin_client.post(url("encargado_editar", self.encargado.pk), {"username": self.encargado.username, "first_name": "Camila", "last_name": "Prueba", "email": "", "password1": "NuevaClave#Academica2026", "password2": "NuevaClave#Academica2026"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get(url("habitacion_list")).status_code, 302)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_active_responsible_not_permanent_after_departure(self):
        assignment = crear_asignacion({self.room1.pk: [self.people[0].pk]}, self.people[0].pk, self.encargado)
        liberar_asignacion(assignment.pk, self.encargado)
        response = self.client.get(url("pasajero_list"), {"estado": "responsables"})
        self.assertEqual(len(response.context["pasajeros"]), 0)

    @override_settings(LOGIN_MAX_FAILURES=2, LOGIN_LOCK_SECONDS=300)
    def test_throttle_lock_expiry_allows_correct_login(self):
        self.client.logout()
        for _ in range(2):
            self.client.post(url("login"), {"username": self.encargado.username, "password": "errada"})
        LoginIntento.objects.update(bloqueado_hasta=timezone.now() - timedelta(seconds=1))
        response = self.client.post(url("login"), {"username": self.encargado.username, "password": PASSWORD})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(LoginIntento.objects.get().fallos, 0)

    def test_csrf_required_for_assignment_confirmation(self):
        protected_client = Client(enforce_csrf_checks=True)
        protected_client.force_login(self.encargado)
        response = protected_client.post(url("asignacion_crear"), {**self.distribution(), "action": "confirm"})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Asignacion.objects.exists())
