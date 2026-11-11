# Cambios por retroalimentación de la Evaluación U2

Este documento registra los cambios solicitados por la profesora. Varios modifican reglas del informe E2
(RN-01, RN-02, RES-04, MC-05, RF-12, RF-13, RF-21 y RN-16); el texto original de `REQUERIMIENTOS_E2.md` se conserva como referencia histórica
y la regla vigente es la descrita aquí.

| # | Solicitud | Implementación | Archivos | Pruebas |
|---|---|---|---|---|
| 1 | Bloqueo de 5 minutos tras 3 intentos fallidos de inicio de sesión | `LOGIN_MAX_FAILURES=3`, `LOGIN_LOCK_SECONDS=300`; mensajes con intentos restantes y aviso de bloqueo (HTTP 429) | `config/settings.py`, `hotel/views.py` | `BloqueoInicioSesionTests` |
| 2 | El número de habitación no admite letras | Solo dígitos, 1 a 5, sin ceros iniciales; validado en formulario, modelo y con `pattern` HTML | `hotel/validators.py`, `hotel/models.py`, `hotel/forms.py` | `NumeroHabitacionTests` |
| 3 | Fecha de inicio y término obligatorias; costo por persona y noche | Campos `fecha_inicio`/`fecha_termino` (mínimo 1 noche, máximo 365, inicio no anterior a hoy); costo = pasajeros × noches × $40.000; inmutables tras confirmar; restricción de BD | `hotel/models.py`, `hotel/services.py`, `hotel/forms.py`, `hotel/views.py`, plantillas, `app.js`, migración 0004 | `EstadiaYCostoTests`, `EstadiaHttpTests` |
| 4 | No exigir completar la capacidad | Se admite de 1 pasajero hasta la capacidad; se rechaza cero pasajeros y el exceso | `hotel/services.py`, `hotel/forms.py`, plantilla y `app.js` | `CapacidadParcialTests` |

## Migración 0004
- Agrega las fechas y, para asignaciones previas, las completa como una noche desde la fecha de ingreso, coherente con su costo original.
- Es reversible. Verificada sobre una base con datos de demostración anteriores.

## Posibles regresiones
- `crear_asignacion` y `validar_asignacion` ahora exigen fechas; las pruebas usan los atajos de `hotel/tests/base.py`.
- Las habitaciones existentes con letras en el número (si las hubiera) no se modifican, pero no podrán guardarse sin corregirlas.
- Las asignaciones nuevas de la demo (`seed_demo`) tienen 1 a 3 noches.
- La salida anticipada conserva el costo acordado al ingreso.

## Ajuste posterior: formato de las fechas de la estadía

- **Problema:** con el selector nativo de fecha (`type="date"`) no se podían escribir los números directamente; el campo de término quedaba vacío y el de inicio se corrompía, porque el recálculo se disparaba con cada dígito.
- **Solución:** los campos de inicio y término ahora son de texto con formato `dd/mm/aaaa`, con máscara que agrega las barras al escribir solo números. El servidor acepta `dd/mm/aaaa` (y también `aaaa-mm-dd` por compatibilidad) y mantiene las mismas validaciones: obligatorias, inicio no anterior a hoy, mínimo una noche y máximo 365.
- **Archivos:** `hotel/forms.py`, `hotel/views.py`, `hotel/templates/hotel/asignacion_form.html`, `hotel/static/hotel/js/app.js`, `hotel/tests/test_retroalimentacion_u2.py` (3 pruebas nuevas; 162 en total).
