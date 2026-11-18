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

## Ajuste posterior: ingreso efectivo (inicio = hoy)

- **Problema:** una asignación con inicio futuro marcaba la habitación como ocupada desde que se registraba, aunque el huésped aún no hubiera llegado.
- **Solución:** el sistema se define como gestor de ingresos efectivos, no de reservas. La fecha de inicio de una asignación nueva debe ser la de hoy; se rechazan fechas anteriores y posteriores, en el formulario y en el servicio. El término sigue siendo elegible (posterior al inicio, máximo 365 noches) y el costo no cambia ($40.000 por persona y noche).
- **Estadías vencidas:** se detectan y se señalan, pero la habitación no se libera sola; la salida la confirma el Encargado.
- **Datos existentes:** no se modifican; las asignaciones antiguas con inicio futuro siguen mostrando «Inicio programado».
- **Archivos:** `hotel/services.py`, `hotel/forms.py`, `hotel/templates/hotel/asignacion_form.html`, `hotel/tests/test_estadias_hoy_u4.py` y ajustes en dos pruebas existentes.

## Ajuste posterior: validación estricta de todos los campos (retroalimentación de la profesora)

- **Problema:** el campo teléfono aceptaba guiones, paréntesis y cualquier largo o país (por ejemplo `--------` o `+56-9-1234-5678`). En Chile el móvil se escribe `+569` seguido de 8 dígitos. La observación pedía además que todos los campos del proyecto estén validados, sean opcionales o no.
- **Solución:** teléfono móvil chileno estricto (`+569` y 8 dígitos; se admiten espacios como separador y se guarda sin ellos, p. ej. `+56912345678`); sigue siendo opcional, pero si se escribe algo se valida. Se aplica en el formulario de pasajero, en la edición de pasajeros asignados y en el modelo. Correo con formato estricto y guardado en minúsculas (pasajero y cuentas de usuario). Nombre de usuario de 4 a 150 caracteres (letras sin tilde, números y `. _ - + @`). Capacidad de habitación entre 1 y 20. Contraseña de inicio de sesión limitada a 128 caracteres. Atributos HTML (`pattern`, `maxlength`, `inputmode`) como ayuda; la validación real sigue siendo la del servidor.
- **Datos existentes:** no se modifican ni hay migraciones. Un pasajero antiguo con teléfono inválido se puede abrir, pero al editarlo se debe corregir el teléfono.
- **Decisión pendiente de confirmar:** el tope de 20 pasajeros por habitación y el mínimo de 4 caracteres del usuario son límites de validación elegidos por el equipo de desarrollo, no reglas entregadas por el hotel.
- **Archivos:** `hotel/validators.py`, `hotel/models.py`, `hotel/forms.py`, `hotel/views_asignados.py`, `hotel/tests/test_validacion_campos_u4.py`.

