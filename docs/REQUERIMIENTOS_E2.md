# Especificación y decisiones de implementación

La especificación del prototipo proviene del informe de Evaluación 2, páginas 14 a 18, y la rúbrica de Evaluación 3. Los dos PDF originales se conservan en la raíz; `reference/` contiene extracciones y representaciones visuales auxiliares. Las instrucciones del usuario sobre construcción y pruebas corresponden a E3 y amplían la entrega anterior, que estaba limitada a planificación y diseño.

## Requerimientos funcionales

La tabla conserva el significado de los RF originales y resume su redacción para facilitar la revisión. La correspondencia con archivos y pruebas está en `TRACEABILITY.md`.

| RF | Funcionalidad | Condición de aceptación |
|---|---|---|
| RF-01 | Autenticación de usuarios | Ingreso mediante usuario y contraseña; validar credenciales antes de habilitar funciones. |
| RF-02 | Control de acceso por rol | Mostrar y habilitar únicamente las funciones del perfil autenticado; validar también en servidor. |
| RF-03 | Registro de encargados | El Administrador crea usuarios con perfil Encargado de Hotel. |
| RF-04 | Gestión de encargados | El Administrador consulta, modifica y desactiva encargados. |
| RF-05 | Registro de habitaciones | Número único, capacidad y orientación; estado inicial Vacante. |
| RF-06 | Modificación de habitaciones | Editar una habitación conservando su historial. |
| RF-07 | Consulta de habitaciones | Listar y filtrar por estado y capacidad. |
| RF-08 | Registro de pasajeros | Registro individual con nombre completo y RUT como mínimo. |
| RF-09 | Modificación de pasajeros | Corregir datos conservando su historial. |
| RF-10 | Consulta de pasajeros | Buscar por documento, nombre o apellido. |
| RF-11 | Asignación de habitación | Alojar pasajeros registrados en habitaciones vacantes. |
| RF-12 | Validación de capacidad | Cada habitación debe quedar con exactamente tantos pasajeros como su capacidad; rechazar el grupo completo si una falla. |
| RF-13 | Cálculo automático del costo | Multiplicar $40.000 CLP por el número de pasajeros; calcular en servidor. |
| RF-14 | Registro de fecha y hora | Tomar automáticamente la fecha y hora del sistema al asignar. |
| RF-15 | Actualización del estado | Al confirmar, todas las habitaciones incluidas pasan a Ocupada. |
| RF-16 | Liberación de habitación | Registrar salida, cerrar asignación, dejar Vacantes todas sus habitaciones y conservar los registros. |
| RF-17 | Visualización de la ocupación | Mostrar totales de ocupadas, vacantes y pasajeros actualmente hospedados. |
| RF-18 | Historial por habitación | Consultar asignaciones, fechas, pasajeros y costos asociados a una habitación. |
| RF-19 | Historial por pasajero | Consultar estadías anteriores de un pasajero. |
| RF-20 | Cierre de sesión | Invalidar la sesión y finalizar el acceso. |
| RF-21 | Asignación de múltiples habitaciones | Distribuir un grupo en varias habitaciones, cumpliendo capacidad exacta en cada una. |
| RF-22 | Pasajero responsable | Identificar un responsable para la contratación y asociarlo a las habitaciones del grupo. |
| RF-23 | Eliminación controlada de habitaciones | Impedir la eliminación con hospedaje o asignación activa. |
| RF-24 | Conservación del historial de habitación | La baja de una habitación vacante conserva sus asignaciones y pasajeros históricos. |
| RF-25 | Listado de pasajeros hospedados | Mostrar nombre, habitación y responsable de cada pasajero alojado. |

## Reglas de negocio

| Regla | Aplicación obligatoria |
|---|---|
| RN-01 | Tarifa fija $40.000 por pasajero alojado; sin entrada manual del costo. |
| RN-02 | Cantidad de pasajeros igual a capacidad de cada habitación. |
| RN-03 | Habitación ocupada no admite otra asignación hasta su liberación. |
| RN-04 | Todos los pasajeros deben existir antes de asignar. |
| RN-05 | Número de habitación único en el hotel. |
| RN-06 | Documento del pasajero único; reutilizar el registro existente. |
| RN-07 | Solo Administrador crea, modifica, activa o desactiva encargados. |
| RN-08 | Encargado no administra usuarios; Administrador no realiza operaciones hoteleras. |
| RN-09 | Fecha y hora de asignación automáticas e ineditables. |
| RN-10 | Habitación nueva Vacante. |
| RN-11 | Salida devuelve las habitaciones a Vacante, cierra la asignación y conserva sus registros. |
| RN-12 | Historial de asignaciones no eliminable; las correcciones no borran registros anteriores. |
| RN-13 | Toda función requiere autenticación previa. |
| RN-14 | Habitación con pasajeros o asignación activa no eliminable. |
| RN-15 | Baja de habitación vacante no elimina historial ni pasajeros relacionados. |
| RN-16 | Grupo admite múltiples habitaciones con capacidad exacta individual. |
| RN-17 | Toda contratación identifica un responsable asociado al grupo. |

El responsable se almacena en la asignación. Una misma persona puede ser responsable en una estadía y acompañante en otra. No existe un atributo permanente de “líder” en Pasajero. Para impedir inconsistencias adicionales, un pasajero no puede aparecer dos veces dentro de la misma contratación ni permanecer en dos asignaciones activas.

El costo corresponde a la contratación completa: un grupo de cinco pasajeros cuesta $200.000, aunque utilice dos habitaciones. No se multiplica por noches ni se cobran nuevamente los $200.000 por cada fila del historial. Los listados históricos identifican cuando muestran el costo total del grupo.

## Requerimientos no funcionales

| RNF | Requisito E2 | Alcance de la evidencia E3 |
|---|---|---|
| RNF-01 | Usabilidad uniforme y capacitación breve | Navegación común, español, formularios etiquetados y mensajes específicos; revisión visual y guion de usuario. |
| RNF-02 | Consultas principales en máximo 3 segundos | Medición local documentada; el resultado depende del conjunto de datos y equipo utilizados. |
| RNF-03 | Hash de contraseñas con salt | Hashers y validadores de Django. Un hash no es cifrado reversible. |
| RNF-04 | HTTPS | Configuración de producción preparada; la demostración local por HTTP no acredita transporte TLS. |
| RNF-05 | Expiración por inactividad | Sesión de 1.800 segundos configurables; renovación por actividad. |
| RNF-06 | Disponibilidad durante horario del hotel | Servidor local para demostración; disponibilidad operativa continua requiere infraestructura y supervisión. |
| RNF-07 | Navegadores vigentes sin instalación en clientes | Interfaz HTML/CSS/JavaScript y revisión de navegador; no equivale a certificación de todos los navegadores. |
| RNF-08 | Integridad, sin duplicados | Validadores, servicios, transacciones y restricciones de base de datos. |
| RNF-09 | Fecha, hora y usuario en asignación y liberación | Registro de operación e historial protegido desde la aplicación. |
| RNF-10 | Módulos mantenibles | Separación de presentación, aplicación, servicios, dominio y persistencia. |
| RNF-11 | Crecimiento de habitaciones e historial | Consultas relacionales y estructura extensible; SQLite tiene límites de concurrencia y escalado. |
| RNF-12 | Respaldos periódicos recuperables | Comando de respaldo y procedimiento de restauración; la periodicidad requiere programación operacional. |
| RNF-13 | Español y pesos chilenos | Interfaz localizada; separador de miles y zona horaria America/Santiago. |

## Interpretación de los mockups

Se revisaron visualmente las páginas 33 a 43 del informe E2. El diseño conserva blanco predominante, rojo del hotel, texto azul oscuro, fondos suaves, barra lateral, encabezado con usuario y rol, tarjetas de métricas, tablas y distintivos de estado. Los indicadores se alimentan de la base de datos del prototipo.

| Referencia visual | Decisión coherente con E2 y petición del usuario |
|---|---|
| Login, p.33 | Acceso común para ambos roles y error controlado. |
| Administrador, pp.34-35 | Panel separado, actividad de cuentas, búsqueda y administración de encargados. |
| Encargado, p.36 | Métricas de habitaciones, pasajeros, asignaciones y movimientos recientes. |
| Habitaciones, p.37 | Usar orientación exigida por RF-05 y solo los estados Vacante/Ocupada; la baja se representa mediante activo/inactivo. |
| Pasajeros, p.38 | RUT, nombre, contacto opcional y situación actual derivada de estadías activas. |
| Detalle, p.39 | Responsable, distribución del grupo, costo y cierre de todas las habitaciones en una operación. |
| Asignación, p.40 | Distribución explícita por habitación y validación exacta. Los timestamps se generan en servidor conforme a RF-14 y RN-09. |
| Ocupación, p.41 | Totales actuales y lista de pasajeros con responsable, requerida por RF-25. |
| Historiales, pp.42-43 | Fechas, habitaciones, responsable, pasajeros y costo, accesible incluso tras una baja lógica. |

Los campos de piso, mantenimiento, fecha editable o salida estimada que aparecen en algunas imágenes no sustituyen los requerimientos textuales. No se introducen reservas, pasarela de pago, facturación ni acceso directo de pasajeros. La entrega E3 construye el prototipo; la restricción E2 que limitaba la entrega a diseño describía aquella etapa anterior.
