"""Reglas de negocio. Las escrituras del flujo principal son indivisibles."""
import re
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction, IntegrityError, OperationalError
from django.utils import timezone
from .models import Usuario, Habitacion, Pasajero, Asignacion, DetalleHabitacionAsignada, Hospedaje, Movimiento

TARIFA_PASAJERO = 40000

def exigir_encargado(user):
    if not user or not user.is_authenticated or not user.is_active or user.rol != Usuario.Rol.ENCARGADO or not Usuario.objects.filter(pk=user.pk, is_active=True, rol=Usuario.Rol.ENCARGADO).exists():
        raise PermissionDenied('Esta operación corresponde al Encargado de hotel.')

def registrar_movimiento(user, accion, descripcion):
    return Movimiento.objects.create(usuario=user, accion=accion, descripcion=descripcion)

def _id(value):
    try:
        if isinstance(value, bool) or not isinstance(value, (str, int)) or not re.fullmatch(r'[0-9]+', str(value)) or not 1 <= int(value) <= 9223372036854775807:
            raise ValueError
        return int(value)
    except (TypeError, ValueError, OverflowError):
        raise ValidationError('La selección contiene un identificador inválido.')

def validar_asignacion(distribucion, responsable_id, user):
    exigir_encargado(user)
    if not isinstance(distribucion, dict) or not distribucion:
        raise ValidationError('Selecciona al menos una habitación y sus pasajeros.')
    parsed = {}
    for key, values in distribucion.items():
        rid = _id(key)
        if rid in parsed or not isinstance(values, (list, tuple)):
            raise ValidationError('Revisa la distribución de habitaciones y pasajeros.')
        parsed[rid] = [_id(p) for p in values]
    room_ids = list(parsed)
    rooms = {r.pk: r for r in Habitacion.objects.select_for_update().filter(pk__in=room_ids)}
    if len(rooms) != len(room_ids):
        raise ValidationError('Una habitación seleccionada no existe.')
    all_ids = [pid for ids in parsed.values() for pid in ids]
    if len(all_ids) != len(set(all_ids)):
        raise ValidationError('Un pasajero no puede repetirse entre las habitaciones del grupo.')
    passengers = {p.pk: p for p in Pasajero.objects.select_for_update().filter(pk__in=all_ids)}
    if len(passengers) != len(all_ids):
        raise ValidationError('Un pasajero seleccionado no está registrado. Regístralo antes de asignar.')
    for rid, pids in parsed.items():
        room = rooms[rid]
        if not room.activa or room.estado != Habitacion.Estado.VACANTE or room.detalles.filter(activa=True).exists():
            raise ValidationError(f'La habitación {room.numero} ya no está disponible. Actualiza la selección.')
        if len(pids) != room.capacidad:
            raise ValidationError(f'La habitación {room.numero} exige exactamente {room.capacidad} pasajeros; seleccionaste {len(pids)}.')
    if Hospedaje.objects.filter(pasajero_id__in=all_ids, activa=True).exists():
        raise ValidationError('Uno o más pasajeros ya se encuentran hospedados en una asignación activa.')
    responsible = _id(responsable_id)
    if responsible not in passengers:
        raise ValidationError('El responsable debe ser uno de los pasajeros de este grupo.')
    return {'habitaciones': [{'habitacion': rooms[rid], 'pasajeros': [passengers[p] for p in pids]} for rid, pids in parsed.items()],
            'pasajeros': [passengers[p] for p in all_ids], 'responsable': passengers[responsible],
            'cantidad': len(all_ids), 'costo_total': len(all_ids) * TARIFA_PASAJERO}

def crear_asignacion(distribucion, responsable_id, user):
    try:
        with transaction.atomic():
            # SQLite BEGIN IMMEDIATE serializa escritores ANTES de comprobar disponibilidad.
            summary = validar_asignacion(distribucion, responsable_id, user)
            responsible = summary['responsable']
            assignment = Asignacion.objects.create(responsable=responsible, responsable_nombre=responsible.nombre_completo,
                            responsable_rut=responsible.rut, registrada_por=user, costo_total=summary['costo_total'])
            for row in summary['habitaciones']:
                room = row['habitacion']
                changed = Habitacion.objects.filter(pk=room.pk, activa=True, estado=Habitacion.Estado.VACANTE).update(estado=Habitacion.Estado.OCUPADA)
                if changed != 1:
                    raise ValidationError('La disponibilidad cambió. Vuelve a revisar la asignación.')
                detail = DetalleHabitacionAsignada.objects.create(asignacion=assignment, habitacion=room,
                                                numero_snapshot=room.numero, capacidad_snapshot=room.capacidad)
                for passenger in row['pasajeros']:
                    Hospedaje.objects.create(detalle=detail, pasajero=passenger, nombre_snapshot=passenger.nombre_completo, rut_snapshot=passenger.rut)
            registrar_movimiento(user, 'ASIGNACION', f'Asignación #{assignment.pk:04d}: {summary["cantidad"]} pasajeros, {len(summary["habitaciones"])} habitaciones.')
            return assignment
    except IntegrityError as exc:
        raise ValidationError('La selección cambió por otra operación. Actualiza e inténtalo nuevamente.') from exc
    except OperationalError as exc:
        if 'locked' in str(exc).lower():
            raise ValidationError('El sistema está procesando otra operación. Inténtalo nuevamente en unos segundos.') from exc
        raise

@transaction.atomic
def liberar_asignacion(asignacion_id, user):
    exigir_encargado(user)
    try:
        assignment = Asignacion.objects.select_for_update().get(pk=_id(asignacion_id))
    except Asignacion.DoesNotExist:
        raise ValidationError('La asignación no existe.')
    if assignment.estado != Asignacion.Estado.ACTIVA:
        raise ValidationError('La salida de esta asignación ya fue registrada.')
    details = list(assignment.detalles.select_related('habitacion'))
    Hospedaje.objects.filter(detalle__asignacion=assignment).update(activa=False)
    assignment.detalles.update(activa=False)
    Habitacion.objects.filter(pk__in=[d.habitacion_id for d in details]).update(estado=Habitacion.Estado.VACANTE)
    assignment.estado = Asignacion.Estado.FINALIZADA
    assignment.fecha_salida = timezone.now()
    assignment.liberada_por = user
    assignment.save(update_fields=['estado', 'fecha_salida', 'liberada_por'])
    registrar_movimiento(user, 'LIBERACION', f'Salida registrada para la asignación #{assignment.pk:04d}; {len(details)} habitaciones vacantes.')
    return assignment

@transaction.atomic
def eliminar_habitacion(habitacion_id, user):
    exigir_encargado(user)
    try:
        room = Habitacion.objects.select_for_update().get(pk=_id(habitacion_id))
    except Habitacion.DoesNotExist:
        raise ValidationError('La habitación no existe.')
    if not room.activa:
        raise ValidationError('La habitación ya se encuentra inactiva.')
    if room.estado == Habitacion.Estado.OCUPADA or room.detalles.filter(activa=True).exists() or Hospedaje.objects.filter(detalle__habitacion=room, activa=True).exists():
        raise ValidationError('No puedes eliminar una habitación ocupada o con una asignación activa.')
    room.activa = False
    room.save(update_fields=['activa'])
    registrar_movimiento(user, 'HABITACION_ELIMINADA', f'Habitación {room.numero} desactivada; se conserva su historial.')
    return room

def resumen_ocupacion():
    rooms = Habitacion.objects.filter(activa=True)
    total = rooms.count()
    occupied = rooms.filter(estado=Habitacion.Estado.OCUPADA).count()
    return {'total': total, 'vacantes': total - occupied, 'ocupadas': occupied,
            'pasajeros': Hospedaje.objects.filter(activa=True).count(),
            'asignaciones': Asignacion.objects.filter(estado=Asignacion.Estado.ACTIVA).count(),
            'porcentaje': round(occupied * 100 / total, 1) if total else 0}
