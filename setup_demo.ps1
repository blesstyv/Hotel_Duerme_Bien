$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    python -m venv .venv
}
$hotelPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
& $hotelPython -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'No se pudieron instalar las dependencias.' }
& $hotelPython scripts\init_env.py
if ($LASTEXITCODE -ne 0) { throw 'No se pudo preparar el entorno local.' }
& $hotelPython manage.py migrate
if ($LASTEXITCODE -ne 0) { throw 'Fallaron las migraciones.' }
& $hotelPython manage.py seed_demo
if ($LASTEXITCODE -ne 0) { throw 'Falló la creación de datos demo.' }
& $hotelPython manage.py collectstatic --noinput
if ($LASTEXITCODE -ne 0) { throw 'Falló la preparación de archivos estáticos.' }
& $hotelPython manage.py check
if ($LASTEXITCODE -ne 0) { throw 'La configuración no pasó la validación.' }
Write-Host 'Demo lista. Ejecuta .venv\Scripts\python.exe scripts\serve.py y abre http://127.0.0.1:8000'
Write-Host 'Usuarios: admin_demo / encargado_demo. Contraseñas académicas en .env (archivo local excluido de Git).'
