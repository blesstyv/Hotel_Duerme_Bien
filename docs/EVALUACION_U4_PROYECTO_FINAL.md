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
| Fechas de la estadía | Inicio y término obligatorios, término posterior al inicio, inicio igual a hoy (ingreso efectivo, sin reservas anticipadas), máximo 365 noches | `validar_estadia`, `AsignacionForm`, `CheckConstraint` | `EstadiaYCostoTests`, `FormatoFechaEstadiaTests` |
| Boleta de estadía | Documento imprimible con folio, representante, fechas, noches, pasajeros por habitación, vista, tarifa, subtotales y total | `views.asignacion_boleta`, `boleta.html`, `boleta.js` | `BoletaEstadiaTests` |
| Reglas del negocio | Ver la tabla siguiente | — | Suite completa |
| Pruebas, corrección y seguridad | 329 pruebas automatizadas, controles de seguridad y mapeo ISO | `hotel/tests/` | Ejecución registrada abajo |

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
- Fechas futuras: **resuelta** en la rama `feat/estadias-hoy-y-vencidas`: toda asignación nueva debe comenzar hoy (ver «Ingreso efectivo y estadías vencidas» al final). «Inicio programado» solo aparece en datos antiguos.


## Imagen real del hotel

La fotografía fue entregada por el equipo del proyecto (`hotel_foto.jpg`, 1600×1065 px, vista nocturna con la piscina). Se muestra sola, sin recuadros encima, en el inicio de sesión y en el panel de cada rol. Para cambiarla basta copiar otra imagen con el mismo nombre en `hotel/static/hotel/img/`. Se asume que el equipo tiene derecho a usarla en el trabajo académico; si se publica fuera de él conviene confirmar su licencia.


## Correcciones finales (rama `dev/correcciones-finales-u4`)

Resultados de esta etapa (2026-11-11/12), sin merge a `main` ni despliegue:

- `manage.py test`: **260 pruebas, 0 fallos** (200 anteriores + 60 nuevas en `test_correcciones_finales_u4.py`; se actualizaron 2 pruebas antiguas que describían el comportamiento anterior: la vista de la boleta ya no cambia al editar la habitación, y el resumen de ocupación incluye `vencidas`).
- `manage.py check`: sin problemas. `makemigrations --check`: sin cambios pendientes. Nueva migración `0005_congelar_vista_y_tarifa`.
- Migración verificada sobre una copia de una base con datos (5 asignaciones, 6 habitaciones asignadas): todas quedan con tarifa $40.000 y con la vista que tenía su habitación; se probó avanzar, retroceder a 0004 y avanzar de nuevo. Además hay una prueba automática que migra 0004 → 0005 con datos antiguos.

### Qué se encontró y qué se hizo

| Prioridad | Hallazgo en el código | Corrección |
|---|---|---|
| Alta | No existía la reactivación de habitaciones | `reactivar_habitacion` (servicio con bloqueo de fila), vista POST protegida con CSRF y rol, botón «Reactivar» con confirmación en las inactivas, mensaje y registro en movimientos |
| Alta | `pasajero_editar` permitía cambiar nombre y RUT de un pasajero con hospedaje activo (solo la ruta de «pasajeros asignados» lo impedía) | El formulario deshabilita ambos campos (un POST manipulado no los cambia), y `Pasajero.save` rechaza el cambio desde cualquier ruta; teléfono y correo siguen editables |
| Alta | La vista de la habitación y la tarifa de la boleta se leían de datos actuales: una boleta antigua cambiaba al editar la habitación | Se guardan al asignar (`vista_snapshot`, `tarifa_aplicada`), son inmutables, y la boleta, el detalle, el historial y la ocupación leen lo guardado |
| Media | El formulario de habitaciones decía «capacidad exacta… debe alojarse exactamente esa cantidad» | Ahora indica capacidad máxima y que se alojan de 1 pasajero hasta ese máximo |
| Media | El listado de habitaciones no filtraba por vista | Filtro «Todas las vistas / Vista al mar / Vista a la ciudad», validado en el servidor |
| Media | Una estadía vencida o con inicio futuro no se distinguía | Etiquetas «Vencida: registrar salida» e «Inicio programado» en listado y detalle, aviso en el panel, y el detalle separa «Fechas contratadas», «Ingreso efectivo» y «Salida real» |

Ya estaban resueltos y no se tocaron: desactivación que impide habitaciones ocupadas, historiales protegidos, representante obligatorio y del grupo, rechazo de habitaciones vacías o sobreocupadas, duplicidades entre habitaciones, estadías superpuestas de una misma persona y la tarifa de $40.000 por persona y noche.

### Fechas y ocupación: propuesta (implementada después: opción 1)

Antes de la corrección posterior una habitación pasaba a «Ocupada» cuando se registra la asignación, aunque la fecha de inicio sea futura. No se cambió el modelo de negocio. Opciones:

1. **Recomendada, la más simple:** el inicio debe ser hoy (no futuro). El ingreso efectivo coincide con el registro y desaparece la inconsistencia, sin módulo de reservas.
2. Mantener fechas futuras tal como está y solo señalarlas (lo que hace ahora el sistema con «Inicio programado»).
3. Reservas con estados propios («reservada» frente a «ocupada»): excede el alcance y requiere un módulo nuevo.

La estadía vencida sin salida registrada no se cierra sola: se señala y la salida real la registra una persona.

### Límites declarados

- Para las asignaciones anteriores a la migración, la vista guardada es la que tenía la habitación al migrar (es el único dato disponible).
- Simulación de producción (modo producción, HTTPS local, `collectstatic`, `migrate` y `seed_demo` sobre una copia de una base antigua con datos): 46 de 46 comprobaciones previas y 11 de 11 nuevas aprobadas con Chrome (desactivar y reactivar con sus confirmaciones, filtro por vista, edición manipulada de un pasajero hospedado, boleta antigua migrada).
- Las pruebas se ejecutaron en entorno local con SQLite; no se probó contra la base de Render ni con el sitio público.

## Ingreso efectivo (inicio = hoy) y estadías vencidas

Etapa de la rama `feat/estadias-hoy-y-vencidas` (2026-11-17), pendiente de revisión y autorización de publicación.

**1. Por qué las asignaciones nuevas solo permiten ingresar el día actual.** Hotel Duerme Bien es un gestor de ingresos efectivos, no una plataforma de reservas anticipadas. Una asignación registra a un grupo que llega y ocupa la habitación en ese momento; por eso la fecha de inicio debe ser la de hoy. La fecha de término sigue siendo elegible, siempre posterior al inicio (mínimo una noche) y con un máximo de 365 noches. El cálculo se mantiene: pasajeros × noches × $40.000.

**2. Cómo se evita la ocupación anticipada.** La regla se valida en tres niveles: el formulario (`AsignacionForm.clean`), el servicio (`services.validar_estadia`, usado por la vista previa y por la confirmación) y la interfaz (texto de ayuda del formulario). Un inicio anterior a hoy se rechaza con «no puede ser anterior a hoy» y uno posterior con «no puede ser posterior a hoy… no reservas anticipadas», ambos indicando la fecha de hoy. Una solicitud manipulada (confirmar con fechas alteradas, enviar la confirmación sin vista previa o llamar al servicio directamente) también se rechaza, y no se crea la asignación ni cambia el estado de la habitación. Si el formulario se abre un día y se confirma otro, el servidor lo rechaza y pide volver a revisar.

**3. Cómo se detectan las estadías vencidas.** Una asignación activa cuya fecha de término ya pasó se considera vencida (`Asignacion.vencida`, evaluada al consultar, sin procesos programados). Se muestra el aviso en el panel del Encargado, la etiqueta «Vencida: registrar salida» en listado y detalle, y el detalle separa fechas contratadas, ingreso efectivo y salida real. El resumen de ocupación cuenta las vencidas.

**4. Por qué las salidas vencidas requieren confirmación del Encargado.** Que la fecha contratada haya pasado no prueba que el huésped dejó la habitación. Liberarla sola podría ofrecerla a otro grupo estando ocupada, de modo que la habitación sigue ocupada hasta que el Encargado registra la salida (`services.liberar_asignacion`). Al registrarla se actualizan los indicadores y desaparece el aviso.

**5. Cómo se conserva la integridad de los datos históricos.** No se modificaron asignaciones ni datos existentes y no hay migraciones nuevas. Las asignaciones anteriores con inicio futuro (si las hubiera) conservan sus fechas y siguen mostrando «Inicio programado». Las boletas mantienen vista y tarifa congeladas, el historial sigue protegido y la salida conserva costo, detalles y movimientos.

**6. Criterios de la rúbrica que se refuerzan.** Fechas de la estadía y registros simultáneos (validación consistente en formulario y servicio), cálculo del valor (sin cambios, $40.000 por persona y noche), reglas del negocio (la ocupación solo comienza con el ingreso efectivo y la salida es una confirmación humana) y pruebas y seguridad (solicitudes manipuladas rechazadas, 20 pruebas nuevas).

**7. Limitaciones que se mantienen.** El sistema no ofrece reservas ni ingresos programados. Las estadías vencidas se señalan, pero dependen de que alguien registre la salida. La base sigue siendo SQLite (la migración a otro motor es una etapa posterior y separada). Los datos de Render no están verificados como persistentes. Las pruebas manuales de interfaz y del sitio publicado las realiza el equipo.

**Verificación técnica realizada (entorno local, SQLite):** `manage.py test hotel`: **280 pruebas, 0 fallos** (260 anteriores + 20 nuevas en `test_estadias_hoy_u4.py`; se ajustaron 2 pruebas anteriores que creaban estadías con inicio futuro: ahora crean la asignación con inicio hoy y desplazan las fechas para simular datos antiguos, y una de superposición usa el mismo día de ingreso). Se comprobó que las pruebas nuevas fallan sin el cambio. `check` y `makemigrations --check`: sin problemas. Simulación de producción con Chrome: 46 de 46 y 11 de 11 comprobaciones aprobadas.

**Actualización 2026-11-17 (retroalimentación de la profesora: validación de campos).** El teléfono ahora exige formato móvil chileno `+569` + 8 dígitos (antes aceptaba guiones y otros formatos), y se reforzaron correo, usuario, capacidad y contraseña de acceso (detalle en `docs/CAMBIOS_RETROALIMENTACION_U2.md`). `manage.py test hotel`: **329 pruebas, 0 fallos** (280 anteriores + 49 nuevas en `test_validacion_campos_u4.py`); `check` y `makemigrations --check` sin cambios. No hay migraciones nuevas. Pendiente a cargo del equipo: pruebas manuales en el sitio publicado.

