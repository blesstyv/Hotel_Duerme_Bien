#!/usr/bin/env bash

set -o errexit

echo "Instalando dependencias..."
pip install -r requirements.txt

echo "Preparando archivos estáticos..."
python manage.py collectstatic --noinput

echo "Aplicando migraciones..."
python manage.py migrate

echo "Cargando datos académicos de demostración..."
DJANGO_ENV=development python manage.py seed_demo --reset-passwords

echo "Validando configuración Django..."
python manage.py check

echo "Build completado correctamente."