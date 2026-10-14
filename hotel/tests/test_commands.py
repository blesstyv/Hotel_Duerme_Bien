import os
import sqlite3
import tempfile
from io import StringIO
from pathlib import Path
from contextlib import closing
from types import SimpleNamespace
from unittest.mock import patch
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from hotel.models import Usuario, Habitacion, Pasajero, Asignacion

class CommandTests(TestCase):
    @patch.dict(os.environ, {'DEMO_ADMIN_PASSWORD': 'DemoAdministracion#2026', 'DEMO_ENCARGADO_PASSWORD': 'DemoRecepcion#2026', 'DEMO_ADMIN_USERNAME': 'admin_demo', 'DEMO_ENCARGADO_USERNAME': 'encargado_demo'})
    def test_seed_demo_idempotent_and_coherent(self):
        call_command('seed_demo', stdout=StringIO())
        counts = (Usuario.objects.count(), Habitacion.objects.count(), Pasajero.objects.count(), Asignacion.objects.count())
        self.assertEqual(counts, (4, 12, 12, 4))
        call_command('seed_demo', stdout=StringIO())
        self.assertEqual(counts, (Usuario.objects.count(), Habitacion.objects.count(), Pasajero.objects.count(), Asignacion.objects.count()))
        self.assertEqual(Asignacion.objects.filter(estado='ACTIVA').count(), 2)

    @override_settings(PRODUCTION=True)
    def test_demo_denied_in_production(self):
        with self.assertRaises(CommandError):
            call_command('seed_demo', stdout=StringIO())

    def test_backup_integrity(self):
        # Base independiente: permite probar la API online sin transacción TestCase.
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'source.sqlite3'
            with closing(sqlite3.connect(source)) as connection:
                connection.execute('CREATE TABLE evidence(value TEXT)')
                connection.execute("INSERT INTO evidence VALUES ('verified')")
                connection.commit()
            command_settings = SimpleNamespace(BASE_DIR=Path(folder), DATABASES={'default': {'NAME': str(source)}})
            with patch('hotel.management.commands.backup_database.settings', command_settings):
                call_command('backup_database', output_dir=str(Path(folder)/'backups'), stdout=StringIO())
            backup = next((Path(folder)/'backups').glob('*.sqlite3'))
            with closing(sqlite3.connect(backup)) as connection:
                self.assertEqual(connection.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
                self.assertEqual(connection.execute('SELECT value FROM evidence').fetchone()[0], 'verified')
