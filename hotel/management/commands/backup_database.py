from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from contextlib import closing
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Respalda SQLite mediante su API online y verifica la integridad del archivo.'
    def add_arguments(self, parser):
        parser.add_argument('--output-dir', default=str(settings.BASE_DIR / 'backups'))
    def handle(self, *args, **options):
        source = Path(settings.DATABASES['default']['NAME'])
        if not source.exists():
            raise CommandError('No existe la base de datos; ejecuta las migraciones.')
        folder = Path(options['output_dir']).resolve()
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f'hotel-{datetime.now(timezone.utc):%Y%m%d-%H%M%S-%f}.sqlite3'
        with closing(sqlite3.connect(source)) as src, closing(sqlite3.connect(path)) as dst:
            src.backup(dst)
            if dst.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise CommandError('El respaldo no pasó la comprobación de integridad.')
        self.stdout.write(self.style.SUCCESS(f'Respaldo verificado: {path}'))
