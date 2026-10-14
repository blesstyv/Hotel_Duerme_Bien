"""Servidor WSGI multiplataforma; estáticos servidos por WhiteNoise."""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
from config.wsgi import application
from waitress import serve

if __name__ == '__main__':
    serve(application, host=os.getenv('HOST', '127.0.0.1'), port=int(os.getenv('PORT', '8000')), threads=4)
