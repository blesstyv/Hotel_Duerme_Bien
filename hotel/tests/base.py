from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from hotel import services
from hotel.models import Usuario, Habitacion, Pasajero

PASSWORD = 'ClaveAcademica#2026'


def estadia(noches=1, desde=0):
    """Periodo válido: inicia hoy (+desde días) y dura `noches`."""
    inicio = timezone.localdate() + timedelta(days=desde)
    return inicio, inicio + timedelta(days=noches)


def crear_asignacion(distribucion, responsable_id, user, fecha_inicio=None, fecha_termino=None, noches=1):
    """Atajo de pruebas: usa una estadía de una noche si no se indican fechas."""
    if fecha_inicio is None and fecha_termino is None:
        fecha_inicio, fecha_termino = estadia(noches)
    return services.crear_asignacion(distribucion, responsable_id, user, fecha_inicio, fecha_termino)


def validar_asignacion(distribucion, responsable_id, user, fecha_inicio=None, fecha_termino=None, noches=1):
    if fecha_inicio is None and fecha_termino is None:
        fecha_inicio, fecha_termino = estadia(noches)
    return services.validar_asignacion(distribucion, responsable_id, user, fecha_inicio, fecha_termino)

def rut_for(number):
    body = str(number)
    result = 11 - sum(int(n) * (2 + i % 6) for i, n in enumerate(reversed(body))) % 11
    return f'{body}-' + ('0' if result == 11 else 'K' if result == 10 else str(result))

class HotelTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = Usuario.objects.create_user(username='admin_test', password=PASSWORD, rol=Usuario.Rol.ADMINISTRADOR, first_name='Admin')
        cls.encargado = Usuario.objects.create_user(username='encargado_test', password=PASSWORD, rol=Usuario.Rol.ENCARGADO, first_name='Camila')
        cls.inactive = Usuario.objects.create_user(username='inactive_test', password=PASSWORD, rol=Usuario.Rol.ENCARGADO, is_active=False)
        cls.room1 = Habitacion.objects.create(numero='101', capacidad=1, orientacion='NORTE')
        cls.room2 = Habitacion.objects.create(numero='102', capacidad=2, orientacion='SUR')
        cls.room3 = Habitacion.objects.create(numero='103', capacidad=3, orientacion='ESTE')
        cls.people = [Pasajero.objects.create(rut=rut_for(12000000+i), nombre_completo=f'Pasajero {i+1}') for i in range(7)]
