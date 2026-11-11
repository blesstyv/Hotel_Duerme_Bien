# Evaluación U4 · Proyecto final — Hotel Duerme Bien

Aprendizaje esperado 3.1.5: corregir el código del prototipo a partir de los resultados de las pruebas y de los estándares de seguridad ISO 27000. Este documento relaciona cada criterio de la rúbrica (88 puntos) con lo implementado, dónde está en el código y con qué prueba se verifica.

## Resumen por criterio

| Criterio de la rúbrica | Implementación | Archivos principales | Pruebas |
|---|---|---|---|
| Corrección según evaluación 3 / retroalimentación | Bloqueo de login 5 min tras 3 fallos; habitación solo con números; fechas obligatorias; no se exige llenar la capacidad; fechas escribibles `dd/mm/aaaa` | `views.py`, `validators.py`, `forms.py`, `services.py`, `app.js` | `test_retroalimentacion_u2.py` |
| Número de habitación | Solo dígitos 1–5, sin ceros iniciales, sin letras ni símbolos (naturales positivos) | `validators.validar_numero_habitacion`, `HabitacionForm`, `Habitacion.clean` | `NumeroHabitacionTests` |
| Nombres de personas | Un nombre debe contener letras; se rechazan nombres solo numéricos, símbolos y dígitos mezclados. Aplica a pasajeros y a encargados | `validators.validar_nombre_persona`, `PasajeroForm`, formularios de encargado, `Pasajero.clean_fields` | `NombresDePersonasTests` |
| Registros simultáneos | Una persona no puede estar en dos habitaciones con fechas superpuestas; el mensaje indica habitación y fechas de la otra estadía. Además, restricción en base de datos: un solo hospedaje activo por pasajero | `services.validar_asignacion`, `Hospedaje` (`un_hospedaje_activo_por_pasajero`) | `EstadiasSuperpuestasTests`, `test_concurrency.py` |
| Representante del grupo | Es obligatorio, debe pertenecer al grupo y figura en el detalle, el listado y la boleta | `validar_asignacion`, `asignacion_form.html` | `RepresentanteDelGrupoTests` |
| Cálculo del valor | Pasajeros × noches × $40.000, calculado en el servidor | `services.calcular_costo`, `DetalleHabitacionAsignada.costo` | `EstadiaYCostoTests` |
| Vistas de habitaciones | Cada habitación tiene vista al mar o a la ciudad; se elige al crear/editar, se filtra al asignar y aparece en la boleta | `Habitacion.vista`, formularios y plantillas | `test_vista_habitacion.py`, `BoletaEstadiaTests` |
| Interfaz de inicio | Fotografía real del hotel en el inicio de sesión y en el panel de cada rol (la ilustración `hotel_fachada.svg` queda solo como respaldo si falta la foto) | `img/hotel_foto.jpg`, `hotel_image` (hotel_tags), `login.html`, dashboards, `improvements.css` | `ImagenDelHotelTests` |
| Fechas de la estadía | Inicio y término obligatorios, término posterior al inicio, inicio no anterior a hoy, máximo 365 noches | `validar_estadia`, `AsignacionForm`, `CheckConstraint` | `EstadiaYCostoTests`, `FormatoFechaEstadiaTests` |
| Boleta de estadía | Documento imprimible con folio, representante, fechas, noches, pasajeros por habitación, vista, tarifa, subtotales y total | `views.asignacion_boleta`, `boleta.html`, `boleta.js` | `BoletaEstadiaTests` |
| Reglas del negocio | Ver la tabla siguiente | — | Suite completa |
| Pruebas, corrección y seguridad | 198 pruebas automatizadas, controles de seguridad y mapeo ISO | `hotel/tests/` | Ejecución registrada abajo |

## Reglas del negocio verificadas

- Tarifa única de $40.000 por persona y noche; el costo nunca se ingresa a mano.
- Una habitación ocupada o inactiva no recibe nuevas asignaciones.
- Se pueden hospedar de 1 hasta la capacidad de cada habitación; no se exige completarla (cambio pedido por la profesora respecto a la regla RN-02 del informe E2).
- Todo grupo tiene un representante (pasajero responsable) que pertenece al grupo.
- Los pasajeros deben estar registrados antes de asignarse; el RUT es único.
- El historial de asignaciones, hospedajes y movimientos no se edita ni se elimina.
- Al registrar la salida, las habitaciones vuelven a vacantes y la asignación queda finalizada con su registro.
- Solo el Encargado opera asignaciones y boletas; el Administrador gestiona encargados.

## Decisiones de diseño que conviene explicar en la defensa

1. **Nombres:** se aceptan letras con tildes y ñ, espacios, apóstrofe, guion y punto. Se rechaza cualquier dígito, no solo los nombres totalmente numéricos, porque un dígito dentro de un nombre de persona es casi siempre un error de ingreso. Si la profesora prefiere una regla más amplia, se cambia en `validar_nombre_persona`.
2. **Estadías superpuestas:** el sistema conserva el modelo de ocupación por estado (una habitación ocupada no se reasigna hasta registrar la salida). Por eso una persona con una estadía activa tampoco puede registrarse en fechas posteriores sin superposición; es más estricto que lo pedido y se mantiene a propósito.
3. **Boleta:** es un comprobante interno del sistema. No incluye IVA ni folio tributario porque la tarifa definida ($40.000) es el valor total y el enunciado no pide un documento tributario electrónico. La boleta lo declara en su pie.
4. **Vista en la boleta:** se lee desde la habitación actual (no se guarda una copia por asignación). Si se cambiara la vista de una habitación después de una estadía, la boleta histórica mostraría la vista nueva. Si se quiere congelar, habría que agregar un campo de copia con migración.

## Seguridad y marco ISO/IEC 27000

Esto es evidencia técnica de un prototipo académico, no una certificación ni una declaración de conformidad. Controles implementados y su relación con los controles del Anexo A de ISO/IEC 27001:2022:

| Control del prototipo | Control ISO/IEC 27001:2022 relacionado |
|---|---|
| Autenticación con contraseñas guardadas con hash y bloqueo de 5 minutos tras 3 fallos | 8.5 Autenticación segura; 5.17 Información de autenticación |
| Dos roles con validación en el servidor (también por URL directa) | 5.15 Control de acceso; 8.2 Derechos de acceso privilegiado; 8.3 Restricción de acceso a la información |
| Validación de entradas en formularios y servicios (número de habitación, nombres, RUT, fechas, capacidades) | 8.28 Codificación segura |
| Historial protegido contra edición y borrado; registro de movimientos con usuario y fecha | 8.15 Registro de actividad |
| Cabeceras de seguridad (CSP, HSTS en producción, nosniff, X-Frame-Options), protección CSRF, cookies seguras en producción | 8.9 Gestión de la configuración; 8.26 Requisitos de seguridad de las aplicaciones |
| Secretos y credenciales solo desde variables de entorno | 5.17; 8.9 |
| Pruebas automatizadas antes de cada entrega | 8.29 Pruebas de seguridad en desarrollo y aceptación |

Limitaciones declaradas: la demostración local usa HTTP; la protección TLS real depende del despliegue en Render; no se realizaron auditorías ni pruebas de carga.

## Ejecución de pruebas

```powershell
python manage.py test
python manage.py check
python manage.py makemigrations --check --dry-run
```

Resultados de esta etapa (2026-11-11, rama `feat/eval4-u3-boleta-validaciones`):

- `manage.py test`: 198 pruebas, 0 fallos (162 anteriores + 36 nuevas de la evaluación U4).
- `manage.py check`: sin problemas. `makemigrations --check`: sin cambios pendientes (esta etapa no agrega migraciones).
- Simulación del despliegue de Render (modo producción, HTTPS local, `collectstatic`, `migrate` y `seed_demo` sobre una copia de una base creada con la versión anterior, que contenía datos): 46 de 46 comprobaciones aprobadas con Chrome, incluida la boleta de una asignación antigua migrada.

## Auditoría rigurosa previa a la entrega

Se revisó cada criterio de la rúbrica con entradas hostiles y no solo con el camino feliz. Hallazgos y correcciones:

| Hallazgo | Corrección |
|---|---|
| La vista (mar/ciudad) solo se mostraba en el listado de habitaciones y en la boleta; faltaba en la ocupación, el detalle de asignación y el historial de habitación | Se muestra en todas esas pantallas |
| El texto "responsable" seguía en varias pantallas y mensajes, mientras la evaluación habla de representante | Unificado como "representante" en formularios, mensajes y tablas |
| El validador del número de habitación toleraba espacios o tabulaciones alrededor del número | Ahora es estricto; el formulario normaliza los espacios antes de validar |
| La boleta no indicaba cuándo se emitió | Se agregó "Boleta emitida el" |

Entradas probadas y rechazadas para el número de habitación: `0`, `00`, `01`, `007`, `-5`, `+5`, `1.5`, `1,5`, `1e3`, `12A`, `A12`, `1 2`, `10-1`, dígitos árabes (`١٢٣`) y de ancho completo, `²`, `½`, `123456`, vacío y espacios o saltos de línea. Para nombres: `123`, `12 34`, `Juan2`, `R2D2`, `Ana_`, `<script>`, `'; DROP TABLE`, dígitos árabes, `①②` y caracteres de control; y aceptados: nombres con tildes, ñ, apóstrofe, guion, punto y alfabetos no latinos.

Observación honesta sobre las estadías superpuestas: por la interfaz, el formulario ya bloquea a cualquier persona con un hospedaje activo (no aparece en la lista y un envío manipulado se rechaza); el servicio repite la validación y, cuando hay fechas superpuestas, informa la habitación y las fechas de la otra estadía.

## Decisiones abiertas

- Regla 4.6 del caso (varias habitaciones solo si el grupo supera la habitación más grande disponible): el sistema permite usar varias habitaciones siempre. No se endureció para no bloquear asignaciones legítimas; queda como decisión del equipo.
- La vista que se imprime en la boleta se lee de la habitación actual; congelarla por asignación requeriría una migración.


## Imagen real del hotel

La fotografía fue entregada por el equipo del proyecto (`hotel_foto.jpg`, 1600×1065 px, vista nocturna con la piscina). Se muestra sola, sin recuadros encima, en el inicio de sesión y en el panel de cada rol. Para cambiarla basta copiar otra imagen con el mismo nombre en `hotel/static/hotel/img/`. Se asume que el equipo tiene derecho a usarla en el trabajo académico; si se publica fuera de él conviene confirmar su licencia.
