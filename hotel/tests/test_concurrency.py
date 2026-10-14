from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from django.core.exceptions import ValidationError
from django.db import connections, close_old_connections
from django.test import TransactionTestCase
from hotel.models import Usuario, Habitacion, Pasajero, Asignacion, Hospedaje
from hotel.services import crear_asignacion
from .base import PASSWORD, rut_for

class ConcurrencyTests(TransactionTestCase):
    def test_simultaneous_assignments_only_one_occupies_room(self):
        user = Usuario.objects.create_user(username='concurrent', password=PASSWORD, rol='ENCARGADO')
        room = Habitacion.objects.create(numero='500', capacidad=1, orientacion='SUR')
        people = [Pasajero.objects.create(rut=rut_for(16000000+i), nombre_completo=f'Concurrente {i}') for i in range(2)]
        barrier = Barrier(2)
        def run(passenger_id):
            close_old_connections()
            operator = Usuario.objects.get(pk=user.pk)
            barrier.wait(timeout=10)
            try:
                crear_asignacion({room.pk: [passenger_id]}, passenger_id, operator)
                return 'created'
            except ValidationError:
                return 'rejected'
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(run, [p.pk for p in people]))
        self.assertCountEqual(results, ['created', 'rejected'])
        self.assertEqual(Asignacion.objects.count(), 1)
        self.assertEqual(Hospedaje.objects.filter(activa=True).count(), 1)
