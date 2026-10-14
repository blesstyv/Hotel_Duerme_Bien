from datetime import timedelta
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import IntegrityError, transaction
from django.utils import timezone
from hotel.models import Habitacion, Pasajero, Asignacion, DetalleHabitacionAsignada, Hospedaje, Movimiento
from hotel.forms import HabitacionForm, PasajeroForm
from hotel.services import crear_asignacion, validar_asignacion, liberar_asignacion, eliminar_habitacion, resumen_ocupacion
from .base import HotelTestCase

class AssignmentTests(HotelTestCase):
    def create_single(self):
        return crear_asignacion({self.room1.pk: [self.people[0].pk]}, self.people[0].pk, self.encargado)

    def test_exact_capacity_success(self):
        assignment = self.create_single()
        self.assertEqual(assignment.cantidad_pasajeros, 1)
        self.room1.refresh_from_db()
        self.assertEqual(self.room1.estado, Habitacion.Estado.OCUPADA)

    def test_capacity_underfilled_rejected(self):
        with self.assertRaises(ValidationError):
            crear_asignacion({self.room3.pk: [self.people[0].pk, self.people[1].pk]}, self.people[0].pk, self.encargado)
        self.assertFalse(Asignacion.objects.exists())

    def test_capacity_overfilled_rejected(self):
        with self.assertRaises(ValidationError):
            crear_asignacion({self.room1.pk: [self.people[0].pk, self.people[1].pk]}, self.people[0].pk, self.encargado)

    def test_occupied_room_rejected(self):
        self.create_single()
        with self.assertRaises(ValidationError):
            crear_asignacion({self.room1.pk: [self.people[1].pk]}, self.people[1].pk, self.encargado)
        self.assertEqual(Asignacion.objects.count(), 1)

    def test_missing_room_rejected(self):
        with self.assertRaises(ValidationError):
            crear_asignacion({99999: [self.people[0].pk]}, self.people[0].pk, self.encargado)

    def test_missing_passenger_rejected(self):
        with self.assertRaises(ValidationError):
            crear_asignacion({self.room1.pk: [99999]}, 99999, self.encargado)

    def test_already_hosted_passenger_rejected(self):
        self.create_single()
        with self.assertRaises(ValidationError):
            crear_asignacion({self.room2.pk: [self.people[0].pk, self.people[1].pk]}, self.people[0].pk, self.encargado)

    def test_responsible_outside_group_rejected(self):
        with self.assertRaises(ValidationError):
            crear_asignacion({self.room1.pk: [self.people[0].pk]}, self.people[1].pk, self.encargado)

    def test_responsible_correct(self):
        assignment = self.create_single()
        self.assertEqual(assignment.responsable, self.people[0])
        self.assertEqual(assignment.responsable_nombre, self.people[0].nombre_completo)

    def test_multiple_rooms_exact_capacity(self):
        assignment = crear_asignacion({self.room3.pk: [p.pk for p in self.people[:3]], self.room2.pk: [p.pk for p in self.people[3:5]]}, self.people[0].pk, self.encargado)
        self.assertEqual(assignment.detalles.count(), 2)
        self.assertEqual(assignment.cantidad_pasajeros, 5)
        self.assertEqual(assignment.costo_total, 200000)
        self.assertEqual(Hospedaje.objects.filter(activa=True).count(), 5)

    def test_duplicate_passenger_between_rooms_rejected(self):
        with self.assertRaises(ValidationError):
            crear_asignacion({self.room1.pk: [self.people[0].pk], self.room2.pk: [self.people[0].pk, self.people[1].pk]}, self.people[0].pk, self.encargado)

    def test_duplicate_passenger_inside_room_rejected(self):
        with self.assertRaises(ValidationError):
            crear_asignacion({self.room2.pk: [self.people[0].pk, self.people[0].pk]}, self.people[0].pk, self.encargado)

    def test_atomic_rejection_preserves_all_rooms(self):
        with self.assertRaises(ValidationError):
            crear_asignacion({self.room1.pk: [self.people[0].pk], self.room3.pk: [self.people[1].pk]}, self.people[0].pk, self.encargado)
        self.assertFalse(Asignacion.objects.exists())
        self.assertFalse(Hospedaje.objects.exists())
        self.assertFalse(Habitacion.objects.filter(estado='OCUPADA').exists())

    def test_cost_automatic(self):
        self.assertEqual(self.create_single().costo_total, 40000)

    def test_timestamp_automatic_and_author(self):
        before = timezone.now()
        assignment = self.create_single()
        self.assertGreaterEqual(assignment.fecha_ingreso, before)
        self.assertLessEqual(assignment.fecha_ingreso, timezone.now())
        self.assertEqual(assignment.registrada_por, self.encargado)

    def test_preview_has_no_side_effect(self):
        quote = validar_asignacion({self.room1.pk: [self.people[0].pk]}, self.people[0].pk, self.encargado)
        self.assertEqual(quote['costo_total'], 40000)
        self.assertFalse(Asignacion.objects.exists())

    def test_service_admin_denied(self):
        with self.assertRaises(PermissionDenied):
            crear_asignacion({self.room1.pk: [self.people[0].pk]}, self.people[0].pk, self.admin_user)

    def test_service_inactive_denied(self):
        with self.assertRaises(PermissionDenied):
            crear_asignacion({self.room1.pk: [self.people[0].pk]}, self.people[0].pk, self.inactive)

    def test_invalid_identifier_rejected(self):
        for invalid in ('oops', None, -1, False, 1.9, float('inf'), '9999999999999999999999999'):
            with self.subTest(value=invalid), self.assertRaises(ValidationError):
                crear_asignacion({self.room1.pk: [invalid]}, self.people[0].pk, self.encargado)

    def test_empty_assignment_rejected(self):
        with self.assertRaises(ValidationError):
            crear_asignacion({}, self.people[0].pk, self.encargado)

    def test_release_all_rooms(self):
        assignment = crear_asignacion({self.room1.pk: [self.people[0].pk], self.room2.pk: [p.pk for p in self.people[1:3]]}, self.people[0].pk, self.encargado)
        result = liberar_asignacion(assignment.pk, self.encargado)
        self.assertEqual(result.estado, Asignacion.Estado.FINALIZADA)
        self.assertIsNotNone(result.fecha_salida)
        self.assertEqual(result.liberada_por, self.encargado)
        self.assertFalse(Hospedaje.objects.filter(activa=True).exists())
        self.assertFalse(DetalleHabitacionAsignada.objects.filter(activa=True).exists())
        self.assertFalse(Habitacion.objects.filter(estado='OCUPADA').exists())
        self.assertEqual(Hospedaje.objects.count(), 3)

    def test_release_twice_rejected(self):
        assignment = self.create_single()
        first = liberar_asignacion(assignment.pk, self.encargado)
        with self.assertRaises(ValidationError):
            liberar_asignacion(assignment.pk, self.encargado)
        first.refresh_from_db()
        self.assertEqual(Movimiento.objects.filter(accion='LIBERACION').count(), 1)

    def test_reassignment_after_release(self):
        assignment = self.create_single()
        liberar_asignacion(assignment.pk, self.encargado)
        self.create_single()
        self.assertEqual(Asignacion.objects.count(), 2)

    def test_occupied_room_logical_deletion_blocked(self):
        self.create_single()
        with self.assertRaises(ValidationError):
            eliminar_habitacion(self.room1.pk, self.encargado)
        self.room1.refresh_from_db()
        self.assertTrue(self.room1.activa)

    def test_vacant_room_logical_deletion_preserves_history(self):
        assignment = self.create_single()
        liberar_asignacion(assignment.pk, self.encargado)
        eliminar_habitacion(self.room1.pk, self.encargado)
        self.room1.refresh_from_db()
        self.assertFalse(self.room1.activa)
        self.assertEqual(self.room1.detalles.count(), 1)
        self.assertEqual(self.people[0].hospedajes.count(), 1)

    def test_inactive_room_cannot_be_assigned(self):
        eliminar_habitacion(self.room1.pk, self.encargado)
        with self.assertRaises(ValidationError):
            self.create_single()

    def test_history_cannot_be_deleted(self):
        assignment = self.create_single()
        for record in (assignment, assignment.detalles.first(), Hospedaje.objects.first(), Movimiento.objects.first()):
            with self.subTest(model=type(record).__name__), self.assertRaises(ValidationError):
                record.delete()
        with self.assertRaises(ValidationError):
            Asignacion.objects.all().delete()

    def test_history_immutable_cost_timestamp(self):
        assignment = self.create_single()
        assignment.costo_total = 1
        with self.assertRaises(ValidationError):
            assignment.save()
        with self.assertRaises(ValidationError):
            Asignacion.objects.filter(pk=assignment.pk).update(fecha_ingreso=timezone.now()-timedelta(days=1))

    def test_history_preserves_original_data_after_edits(self):
        assignment = self.create_single()
        liberar_asignacion(assignment.pk, self.encargado)
        self.people[0].nombre_completo = 'Nombre Corregido'
        self.people[0].save()
        self.room1.numero = '999'
        self.room1.save()
        self.assertEqual(assignment.detalles.first().numero_snapshot, '101')
        self.assertEqual(assignment.detalles.first().hospedajes.first().nombre_snapshot, 'Pasajero 1')

    def test_database_enforces_unique_active_room(self):
        assignment = self.create_single()
        other = crear_asignacion({self.room2.pk: [p.pk for p in self.people[1:3]]}, self.people[1].pk, self.encargado)
        with self.assertRaises(IntegrityError), transaction.atomic():
            DetalleHabitacionAsignada.objects.create(asignacion=other, habitacion=self.room1, numero_snapshot='101', capacidad_snapshot=1)

    def test_database_enforces_unique_active_passenger(self):
        assignment = self.create_single()
        other = crear_asignacion({self.room2.pk: [p.pk for p in self.people[1:3]]}, self.people[1].pk, self.encargado)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Hospedaje.objects.create(detalle=other.detalles.first(), pasajero=self.people[0], nombre_snapshot='Otro', rut_snapshot=self.people[0].rut)

    def test_occupancy_summary_and_inactive_exclusion(self):
        self.create_single()
        eliminar_habitacion(self.room3.pk, self.encargado)
        self.assertEqual(resumen_ocupacion(), {'total': 2, 'vacantes': 1, 'ocupadas': 1, 'pasajeros': 1, 'asignaciones': 1, 'porcentaje': 50.0})

class ValidationTests(HotelTestCase):
    def test_valid_room_starts_vacant(self):
        form = HabitacionForm({'numero': '204', 'capacidad': 2, 'orientacion': 'NORTE', 'estado': 'OCUPADA', 'activa': False})
        self.assertTrue(form.is_valid(), form.errors)
        room = form.save()
        self.assertEqual(room.estado, 'VACANTE')
        self.assertTrue(room.activa)

    def test_duplicate_room_rejected(self):
        self.assertFalse(HabitacionForm({'numero': '101', 'capacidad': 1, 'orientacion': 'NORTE'}).is_valid())

    def test_zero_capacity_rejected(self):
        self.assertFalse(HabitacionForm({'numero': '900', 'capacidad': 0, 'orientacion': 'NORTE'}).is_valid())

    def test_occupied_room_capacity_change_rejected(self):
        crear_asignacion({self.room1.pk: [self.people[0].pk]}, self.people[0].pk, self.encargado)
        self.room1.refresh_from_db()
        form = HabitacionForm({'numero': '101', 'capacidad': 2, 'orientacion': 'SUR'}, instance=self.room1)
        self.assertFalse(form.is_valid())

    def test_valid_passenger_formatted_rut(self):
        form = PasajeroForm({'rut': '12.345.678-5', 'nombre_completo': 'María Pérez', 'telefono': '', 'correo': ''})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().rut, '12345678-5')

    def test_duplicate_rut_canonicalized(self):
        form = PasajeroForm({'rut': self.people[0].rut, 'nombre_completo': 'Duplicado'})
        self.assertFalse(form.is_valid())

    def test_wrong_check_digit_rejected(self):
        self.assertFalse(PasajeroForm({'rut': '12.345.678-9', 'nombre_completo': 'Inválido'}).is_valid())

    def test_optional_contact_and_invalid_email(self):
        good = PasajeroForm({'rut': '12.345.678-5', 'nombre_completo': 'María Pérez'})
        self.assertTrue(good.is_valid(), good.errors)
        bad = PasajeroForm({'rut': '12.345.678-5', 'nombre_completo': 'María Pérez', 'correo': 'invalid'})
        self.assertFalse(bad.is_valid())
