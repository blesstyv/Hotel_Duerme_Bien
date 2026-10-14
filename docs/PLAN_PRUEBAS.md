# Plan de pruebas del prototipo

El objetivo es demostrar que las operaciones previstas funcionan y que las entradas inválidas no producen ocupación parcial, escalamiento de privilegios ni pérdida de historial. Los casos negativos son exitosos cuando el sistema rechaza la operación, informa una causa útil y conserva los datos anteriores.

## Estrategia y entorno

- Pruebas automáticas con Django `TestCase` y cliente HTTP en una base aislada.
- Revisión del esquema mediante `makemigrations --check --dry-run` y configuración con `check`.
- Comprobación del servidor local y navegación visual de las pantallas principales.
- Revisión manual de distribución multihabitación, confirmaciones y uso en pantalla estrecha.
- Respaldo y recuperación comprobados sobre una copia independiente.

Usar RUT válidos con dígito verificador, nombres académicos, una cuenta Administrador activa, una Encargado activa y otra inactiva. Las pruebas de capacidad emplean habitaciones de 1, 2 y 3 plazas. La suite crea sus propios datos y no requiere modificar la base demo.

## Catálogo funcional

La asociación definitiva a métodos automatizados se encuentra en `TRACEABILITY.md`. Estos identificadores describen escenarios y resultados esperados; no sustituyen la salida de ejecución real.

| Caso | Entrada o acción | Resultado esperado | Requisito |
|---|---|---|---|
| CP-01 | Login con credenciales activas válidas | Sesión creada y panel del rol correcto. | RF-01 |
| CP-02 | Login con contraseña incorrecta | Acceso rechazado sin sesión autenticada. | RF-01 |
| CP-03 | Login de Encargado inactivo | Acceso rechazado. | RF-01, RF-04 |
| CP-04 | Abrir rutas protegidas sin login | Redirección al inicio de sesión. | RF-02, RN-13 |
| CP-05 | Encargado abre URL de usuarios | Rechazo 403, incluso sin usar el menú. | RF-02, RN-07/08 |
| CP-06 | Administrador abre operación hotelera | Rechazo 403, sin acceso a datos de huéspedes. | RF-02, RN-08 |
| CP-07 | Administrador crea Encargado | Cuenta creada con rol Encargado y contraseña con hash. | RF-03 |
| CP-08 | Crear cuenta con username duplicado | Error de validación; no duplicar usuario. | RF-03, RNF-08 |
| CP-09 | Editar nombre/contacto/contraseña de Encargado | Cambios válidos persistidos; sin alterar su rol a Administrador. | RF-04 |
| CP-10 | Desactivar y activar Encargado | Alternar acceso; la cuenta y su actividad se conservan. | RF-04 |
| CP-11 | Registrar habitación válida | Número único, orientación y capacidad; estado Vacante. | RF-05, RN-10 |
| CP-12 | Número de habitación duplicado | Rechazo, incluso si el registro original está inactivo. | RF-05, RN-05 |
| CP-13 | Capacidad cero/negativa | Rechazo de formulario y restricción de integridad. | RF-05, RNF-08 |
| CP-14 | Editar habitación con historia | Cambiar datos actuales; conservar snapshots históricos. | RF-06 |
| CP-15 | Cambiar capacidad de habitación ocupada | Rechazo para mantener integridad de estadía activa. | RF-06, RN-02 |
| CP-16 | Buscar y filtrar habitaciones | Resultado según número, estado, capacidad y actividad. | RF-07 |
| CP-17 | Registrar pasajero con RUT válido | Crear registro normalizado; contacto opcional. | RF-08 |
| CP-18 | Repetir RUT con formato distinto | Rechazar duplicación; reutilizar pasajero existente. | RF-08, RN-06 |
| CP-19 | RUT con dígito verificador incorrecto | Error específico; sin guardar registro. | RF-08, RNF-08 |
| CP-20 | Modificar pasajero con historia | Actualizar registro actual sin cambiar la estadía histórica. | RF-09 |
| CP-21 | Buscar pasajero por RUT o nombre/apellido | Recuperar coincidencias correctas. | RF-10 |
| CP-22 | Capacidad 3 con 3 pasajeros disponibles | Crear asignación, detalles e historial activo. | RF-11/12 |
| CP-23 | Capacidad 3 con 2 pasajeros | Rechazar; no crear asignación ni ocupar ninguna habitación. | RF-12, RN-02 |
| CP-24 | Capacidad 3 con 4 pasajeros | Mismo rechazo completo por exceso. | RF-12, RN-02 |
| CP-25 | Seleccionar habitación ocupada | Rechazo por disponibilidad actual. | RF-11, RN-03 |
| CP-26 | Seleccionar habitación inexistente/inactiva | Rechazo; no crear asignación. | RF-11, RF-24 |
| CP-27 | Pasajero inexistente | Rechazo antes de crear registros. | RF-11, RN-04 |
| CP-28 | Pasajero ya hospedado | Rechazo de doble estadía activa. | RF-11, RNF-08 |
| CP-29 | Responsable ajeno al grupo | Rechazo; debe ser uno de los pasajeros distribuidos. | RF-22, RN-17 |
| CP-30 | Responsable válido | Registrar una persona responsable del grupo y mostrarla. | RF-22 |
| CP-31 | Cinco pasajeros en habitaciones 3+2 | Crear una contratación con dos detalles y cinco hospedajes. | RF-21 |
| CP-32 | Grupo multihabitación con una capacidad inválida | Rollback completo para todas las habitaciones. | RF-12/21 |
| CP-33 | Repetir pasajero en una o varias habitaciones | Rechazo; no contar dos veces ni asignar parcialmente. | RF-21, RNF-08 |
| CP-34 | Enviar costo, fecha, estado o usuario manipulados | Ignorar campos no editables; calcular y registrar en backend. | RF-13/14 |
| CP-35 | Cinco pasajeros | Costo de grupo $200.000; sin ingreso manual ni cálculo por noches. | RF-13, RN-01 |
| CP-36 | Crear asignación | Timestamp automático y usuario real que ejecuta. | RF-14, RNF-09 |
| CP-37 | Confirmar operación exacta | Todas sus habitaciones cambian a Ocupada. | RF-15 |
| CP-38 | Registrar salida multihabitación | Cierre con fecha/usuario; todas las habitaciones Vacantes. | RF-16 |
| CP-39 | Liberar asignación ya finalizada | Rechazo de doble cierre; conservar fecha de salida previa. | RF-16, RNF-08 |
| CP-40 | Panel de ocupación | Totales y porcentaje calculados de habitaciones activas. | RF-17 |
| CP-41 | Lista de huéspedes | Nombre, habitación, responsable y estado actual coherentes. | RF-25 |
| CP-42 | Historial de habitación | Entradas, salidas, pasajeros, responsable y costo conservados. | RF-18 |
| CP-43 | Historial de pasajero | Estadías y distribución de esa persona. | RF-19 |
| CP-44 | Baja de habitación ocupada | Rechazo; habitación permanece activa y ocupada. | RF-23 |
| CP-45 | Baja lógica de habitación vacante con historia | Marcar inactiva, retirar disponibilidad y conservar relaciones. | RF-24 |
| CP-46 | Borrar/asignar sobre historial protegido | Rechazo desde la aplicación/gestores; conservar registros anteriores. | RN-12 |
| CP-47 | Cerrar sesión por POST | Invalidar sesión; siguiente ruta protegida exige login. | RF-20 |

## Catálogo de seguridad y operación

| Caso | Acción | Resultado esperado |
|---|---|---|
| CS-01 | POST protegido sin CSRF usando cliente con comprobación activada | 403 y ausencia de cambios. |
| CS-02 | Nombre con etiquetas HTML | Contenido escapado en salida, sin ejecución de script. |
| CS-03 | Enviar `rol`, `is_staff`, `is_superuser` en gestión de encargados | Sin escalamiento de privilegios. |
| CS-04 | Repetir credenciales inválidas | Bloqueo temporal según configuración y mensaje controlado. |
| CS-05 | Sesión supera tiempo de inactividad | Logout y necesidad de reautenticación. |
| CS-06 | Usuario desactivado con sesión abierta | No permite continuar las operaciones. |
| CS-07 | Consultar hash guardado | No coincide con contraseña; `check_password` verifica contraseña válida. |
| CS-08 | Error 403/404/500 con DEBUG desactivado | Mensaje seguro sin traceback, SQL ni secretos. |
| CO-01 | Ejecutar `seed_demo` dos veces | Sin duplicados ni eliminación de historia existente. |
| CO-02 | Crear respaldo | Archivo SQLite consistente que supera integridad. |
| CO-03 | Restaurar respaldo en copia aislada | Login y consultas reproducibles con conteos conservados. |
| CO-04 | Dos operaciones compiten por el mismo recurso | Una confirmación válida; rechazo de la otra sin duplicación. |
| CO-05 | Servir estáticos y páginas con WSGI | Respuesta correcta de HTML, CSS y JavaScript. |

CO-04 requiere evidencia específica de transacciones/concurrencia; pruebas secuenciales de duplicación acreditan restricciones, pero no deben presentarse como una prueba de carga concurrente.

## Revisión manual de experiencia y desempeño

Recorrer ambos roles, formularios, tabla de ocupación, detalle, liberación e historiales. Confirmar navegación activa, usuario/rol visibles, mensajes legibles, campos obligatorios, confirmaciones de baja/salida y recuperación después de un error. Revisar una pantalla estrecha y verificar que la selección de habitaciones y pasajeros siga accesible.

Para RNF-02, registrar equipo, tamaño de base, ruta, número de mediciones y duración. Medir consultas de habitaciones, pasajeros y ocupación en la instancia local. El resultado local no es una prueba de rendimiento en Cloud o a gran escala. RNF-06 y RNF-11 requieren una verificación operacional y de carga adicional antes de declarar disponibilidad o escalabilidad.

## Ejecución y registro

```powershell
.\.venv\Scripts\python.exe manage.py test hotel.tests --verbosity 2
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

Guardar evidencia con fecha, comando, número de casos, salida final, fallos y correcciones. Solo marcar un RF como implementado verificado cuando existen su comportamiento, prueba adecuada y ejecución exitosa. Los resultados efectivos de esta entrega se encuentran en `docs/EVIDENCIAS_E3.md`.
