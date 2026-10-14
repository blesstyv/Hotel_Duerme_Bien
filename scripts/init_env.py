"""Genera secretos exclusivamente locales; preserva cualquier .env existente."""
import secrets
from pathlib import Path

root = Path(__file__).resolve().parent.parent
path = root / '.env'
if not path.exists():
    template = (root / '.env.example').read_text(encoding='utf-8')
    template = template.replace('SECRET_KEY=\n', f'SECRET_KEY={secrets.token_urlsafe(64)}\n')
    template = template.replace('DEMO_ADMIN_PASSWORD=\n', f'DEMO_ADMIN_PASSWORD={secrets.token_urlsafe(14)}\n')
    template = template.replace('DEMO_ENCARGADO_PASSWORD=\n', f'DEMO_ENCARGADO_PASSWORD={secrets.token_urlsafe(14)}\n')
    path.write_text(template, encoding='utf-8')
    print('Archivo .env local generado. Las contraseñas demo están dentro; no se imprimen ni se versionan.')
else:
    print('Se conserva el archivo .env existente.')
