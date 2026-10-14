# Hotel Duerme Bien

Aplicación web interna de gestión de pasajeros para la Evaluación 3 de Ingeniería de Software. Implementa los RF-01 a RF-25 de la Evaluación 2 con autenticación real, permisos por rol, asignaciones transaccionales y conservación del historial. Los PDF de referencia se conservan en la raíz.

La tarifa es **$40.000 CLP por pasajero**. Cada habitación debe recibir **exactamente su capacidad**. Un grupo de cinco personas puede ocupar una habitación de tres plazas y otra de dos; el total de la contratación es $200.000. El responsable pertenece al grupo y se registra por asignación.

## Inicio en Windows

Desde una terminal PowerShell dentro de esta carpeta:

```powershell
.\setup_demo.ps1
.\.venv\Scripts\python.exe scripts\serve.py
```

Abrir [Hotel Duerme Bien](http://127.0.0.1:8000/). La preparación instala dependencias, configura un `.env` local, aplica las migraciones y carga datos académicos. Consultar en ese `.env` los valores `DEMO_ADMIN_PASSWORD` y `DEMO_ENCARGADO_PASSWORD` generados para iniciar sesión:

| Usuario predeterminado | Rol | Contraseña |
|---|---|---|
| `admin_demo` | Administrador | Valor local de `DEMO_ADMIN_PASSWORD`. |
| `encargado_demo` | Encargado de Hotel | Valor local de `DEMO_ENCARGADO_PASSWORD`. |

Los nombres y contraseñas pueden configurarse antes de ejecutar `seed_demo`. Son cuentas exclusivas de demostración. No compartir `.env` ni usar estas cuentas en producción. El comando de carga es idempotente: ejecutarlo otra vez no duplica los datos ni elimina registros del hotel. Si cambia las contraseñas del entorno después de crear las cuentas, ejecutar `manage.py seed_demo --reset-passwords` para actualizarlas sin borrar estadías. El comando demo se bloquea en producción.

## Instalación manual

Requiere Python 3.10 o posterior y acceso a los paquetes indicados en `requirements.txt`. El prototipo se ha verificado con el intérprete disponible en este entorno; las versiones efectivas y el resultado de las comprobaciones se documentan en `docs/EVIDENCIAS_E3.md`.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Editar `.env` y definir `SECRET_KEY`, `DEMO_ADMIN_PASSWORD` y `DEMO_ENCARGADO_PASSWORD` con valores locales. Generar una clave aleatoria, si se necesita:

```powershell
.\.venv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Completar preparación y levantar el servidor:

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo
.\.venv\Scripts\python.exe manage.py collectstatic --noinput
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe scripts\serve.py
```

Para desarrollo con recarga automática:

```powershell
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

En macOS/Linux, crear el entorno con `python3 -m venv .venv` y usar `.venv/bin/python` en los mismos comandos. La interfaz del cliente solo necesita un navegador.

## Tecnologías y arquitectura

Python, Django 5.2, Django Templates, HTML5, CSS3 y JavaScript; Django ORM y SQLite; python-dotenv para variables de entorno, WhiteNoise para archivos estáticos y Waitress como servidor WSGI. No se requieren CDNs para el diseño ni servicios externos para la operación local.

| Capa | Implementación |
|---|---|
| Presentación | Templates, CSS y JavaScript de `hotel/`. |
| Aplicación | Views, Forms y Decorators. |
| Negocio | Services para asignación, salida, baja y ocupación. |
| Dominio | Usuario, Habitación, Pasajero, Asignación, DetalleHabitaciónAsignada y Hospedaje. |
| Persistencia | ORM y SQLite con restricciones y migraciones. |

La descripción de las relaciones, adaptación del UML y control transaccional está en `docs/ARQUITECTURA.md`.

## Roles y funcionalidades

**Administrador:** panel propio con métricas y actividad de cuentas; consulta, creación, modificación, activación y desactivación de encargados. No puede realizar operaciones hoteleras ni consultar los módulos de pasajeros o asignaciones.

**Encargado de Hotel:** panel de operación; habitaciones con filtros, edición y baja lógica; pasajeros con RUT único y contacto opcional; asignación de grupos a una o varias habitaciones; distribución individual; responsable; costo y fechas automáticas; detalle y salida del grupo; ocupación actual e historiales por habitación y pasajero. No puede administrar cuentas.

La baja lógica de una habitación vacante mantiene su historial y la excluye de nuevas asignaciones. La salida finaliza la contratación completa y libera todas sus habitaciones. El nombre y los datos de identificación históricos se preservan aunque se corrija después el registro actual de una persona.

## Variables de entorno

| Variable | Uso |
|---|---|
| `SECRET_KEY` | Clave secreta de Django; definir fuera del código. |
| `DJANGO_ENV` | `development` o `production`. |
| `DEBUG` | Diagnóstico local; usar `False` en producción. |
| `ALLOWED_HOSTS` | Hosts autorizados, separados por comas. |
| `CSRF_TRUSTED_ORIGINS` | Orígenes HTTPS autorizados cuando la infraestructura lo requiera. |
| `SESSION_COOKIE_AGE` | Inactividad máxima en segundos; valor recomendado del prototipo: `1800`. |
| `DB_PATH` | Ubicación del archivo SQLite; usar disco persistente en nube. |
| `TRUST_PROXY_HTTPS` | Confiar en la cabecera HTTPS del proxy solo cuando este sea controlado. |
| `HOST` / `PORT` | Interfaz y puerto para `scripts/serve.py`; predeterminados `127.0.0.1` / `8000`. |
| `DEMO_ADMIN_USERNAME` | Usuario académico Administrador; predeterminado `admin_demo`. |
| `DEMO_ENCARGADO_USERNAME` | Usuario académico Encargado; predeterminado `encargado_demo`. |
| `DEMO_ADMIN_PASSWORD` | Contraseña demo elegida o generada localmente. |
| `DEMO_ENCARGADO_PASSWORD` | Contraseña demo elegida o generada localmente. |

El archivo `.env.example` documenta las opciones disponibles; `.env` contiene valores privados y está ignorado por Git. La zona horaria del negocio es `America/Santiago` y los montos se presentan en pesos chilenos.

## Pruebas y comprobaciones

```powershell
.\.venv\Scripts\python.exe manage.py test hotel.tests --verbosity 2
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

Las pruebas crean una base independiente; no borran la base de demostración. Cubren casos de éxito y rechazo, autorización por URL, integridad, costo, timestamps, liberación y conservación del historial. `TRACEABILITY.md` vincula cada RF con módulos y pruebas. `docs/PLAN_PRUEBAS.md` describe los datos, resultados esperados y procedimientos manuales. El resultado ejecutado se registra en `docs/EVIDENCIAS_E3.md`.

## Seguridad

Autenticación y hash con salt de Django, CSRF, autorización del servidor para ambos roles, formularios con campos explícitos, consultas ORM, autoescape, sesiones por inactividad, validadores de RUT y restricciones de unicidad. Las reglas críticas se comprueban en backend y la asignación se confirma en una transacción atómica. No se publica el panel genérico de administración de Django.

La configuración de producción prepara HTTPS, cookies seguras y manejo de errores sin información técnica. La demostración local usa HTTP sobre localhost y no acredita TLS real, certificación ISO ni disponibilidad continua. `docs/SEGURIDAD_Y_ETICA.md` relaciona los controles con OWASP, Ley 21.459 e ISO y describe las responsabilidades restantes.

## Respaldo y recuperación

Crear una copia consistente de SQLite con el comando del proyecto:

```powershell
.\.venv\Scripts\python.exe manage.py backup_database
```

Para recuperar, detener el servidor, conservar una copia del archivo actual, restaurar el respaldo en la ubicación configurada en `DB_PATH` y reiniciar. Verificar login, ocupación y una asignación histórica antes de reabrir el uso. Los respaldos contienen datos y requieren protección equivalente a la base original. La ejecución periódica y la copia fuera del equipo se deben configurar operacionalmente; el comando por sí solo no las programa.

## Despliegue futuro Cloud/PaaS

El proyecto incluye una ruta WSGI, dependencias fijadas, estáticos autocontenidos y configuración por entorno. La propuesta usa una instancia de aplicación con almacenamiento persistente para SQLite, HTTPS, secretos administrados y respaldos. Los comandos y requisitos están en `docs/DESPLIEGUE_CLOUD.md`.

No se realizó un despliegue público ni se creó una cuenta Cloud. La preparación es evidencia de portabilidad y planificación PaaS; para cumplir una exigencia de despliegue efectivo debe ejecutarse y verificarse esa etapa en una plataforma elegida. SQLite se conserva para este prototipo y requiere revisar la base de datos antes de un escalado a múltiples instancias.

## Estructura

```text
config/                       Configuración, URLs y WSGI/ASGI
hotel/
    migrations/               Esquema versionado
    management/commands/      seed_demo y backup_database
    static/hotel/             CSS, JavaScript e imágenes locales
    templates/hotel/          Pantallas por rol
    tests/                    Pruebas automáticas
    models.py                 Dominio y restricciones
    services.py               Reglas y transacciones
    forms.py                  Validaciones de entrada
    decorators.py             Permisos
    views.py                  Aplicación
    urls.py                   Rutas
scripts/serve.py              Servidor WSGI para demostración
setup_demo.ps1                Preparación local de Windows
Procfile                      Proceso web para PaaS
docs/                        Arquitectura, pruebas, Cloud y defensa
reference/                   Extracciones y mockups de los PDF
manage.py
requirements.txt
.env.example
.gitignore
TRACEABILITY.md
README.md
```

## Documentación académica

| Documento | Propósito |
|---|---|
| `TRACEABILITY.md` | RF-01 a RF-25, implementación y pruebas concretas. |
| `docs/REQUERIMIENTOS_E2.md` | RF, reglas, RNF y decisiones frente a los mockups. |
| `docs/ARQUITECTURA.md` | Capas, entidades y transacciones. |
| `docs/PLAN_PRUEBAS.md` | Casos, resultados esperados y verificaciones manuales. |
| `docs/EVIDENCIAS_E3.md` | Resultados reales y correspondencia con la rúbrica de 50 puntos. |
| `docs/SEGURIDAD_Y_ETICA.md` | Principios, controles, fuentes jurídicas y normas. |
| `docs/DESPLIEGUE_CLOUD.md` | Preparación y operación futura en PaaS. |
| `docs/DEMOSTRACION_Y_DEFENSA.md` | Guion de dos integrantes y respuestas técnicas. |

Esta documentación sirve como contenido técnico para el informe E3. No sustituye una presentación institucional final con portada, índice y formato vertical solicitado por la asignatura.
