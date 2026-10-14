# Demostración y defensa técnica

Guion sugerido para dos integrantes. La distribución debe acordarse antes de la presentación: el integrante 1 muestra administración y seguridad; el integrante 2 muestra la operación hotelera, las reglas y las pruebas. Ambos deben poder explicar las decisiones principales.

## Preparación

- Ejecutar `setup_demo.ps1`, revisar las contraseñas académicas locales y levantar `scripts/serve.py`.
- Abrir el navegador en `http://127.0.0.1:8000/` y disponer de una terminal en la carpeta del proyecto.
- Usar solo datos demo. Mostrar credenciales elegidas para la clase sin proyectar otras variables secretas del `.env`.
- Ejecutar previamente pruebas y `django check`; tener `docs/EVIDENCIAS_E3.md` y `TRACEABILITY.md` disponibles.
- Elegir cinco pasajeros que estén disponibles y habitaciones vacantes de capacidad 3 y 2. Si la demostración anterior dejó ocupación activa, registrar su salida antes de repetir el caso.

## Guion de 10 a 12 minutos

| Tiempo | Integrante | Acción | Evidencia |
|---|---|---|---|
| 0:00-0:45 | 1 | Explicar el reemplazo de planillas por una aplicación interna centralizada. | Propósito y alcance de E2. |
| 0:45-2:00 | 1 | Login como Administrador; mostrar métricas y crear/modificar un encargado académico. | RF-01 a RF-04 y pantalla propia. |
| 2:00-2:45 | 1 | Desactivar y reactivar la cuenta; intentar abrir una ruta hotelera como Administrador. | Permisos efectivos del servidor y usuario inactivo. |
| 2:45-3:30 | 2 | Cerrar sesión e ingresar como Encargado; mostrar su panel y abrir ruta de usuarios. | RF-02, RF-20 y separación inversa. |
| 3:30-4:30 | 2 | Mostrar habitaciones, capacidad, orientación y filtros; mostrar búsqueda de pasajeros por RUT/nombre. | RF-05 a RF-10. |
| 4:30-5:30 | 2 | Iniciar asignación de 5 personas a habitaciones 3+2; elegir responsable del grupo. | RF-11, RF-21, RF-22. |
| 5:30-6:15 | 2 | Dejar solo 2 pasajeros en la habitación de 3 e intentar confirmar. | RF-12: rechazo, sin ninguna ocupación parcial. |
| 6:15-7:00 | 2 | Completar 3+2; confirmar y mostrar costo $200.000 y fecha automática. | RF-13 a RF-15. |
| 7:00-7:45 | 2 | Mostrar ocupación y lista Pasajero / Habitación / Responsable. | RF-17 y RF-25. |
| 7:45-8:15 | 2 | Intentar dar de baja una habitación ocupada. | RF-23: rechazo controlado. |
| 8:15-9:00 | 2 | Registrar salida desde el detalle; verificar ambas habitaciones Vacantes. | RF-16 y conservación de datos. |
| 9:00-9:45 | 2 | Dar de baja una habitación vacante; consultar sus registros y el historial de un pasajero. | RF-18, RF-19, RF-24. |
| 9:45-10:45 | 1 | Mostrar arquitectura y ejecutar suite/`check`, o mostrar el resultado guardado y repetir un caso crítico. | Trazabilidad, pruebas positivas y negativas. |
| 10:45-12:00 | Ambos | Explicar OWASP, normas, ética y preparación Cloud con límites reales. | Rúbrica E3 y defensa fundamentada. |

Los resultados deben verse en la interfaz o en la salida real de terminal. No presentar métricas ficticias, botones sin efecto o resultados pendientes como exitosos. Si se demuestra una baja que altera los datos, reutilizar una habitación de prueba creada para la exposición.

## Preguntas de defensa

**¿Por qué Django y SQLite?** Django proporciona autenticación, CSRF, ORM, validadores y migraciones; permite concentrar el trabajo en las reglas del hotel. SQLite facilita una instalación reproducible para el prototipo académico. Su límite de escritura concurrente debe revisarse antes de escalar.

**¿Por qué un monolito por capas?** Un hotel tiene módulos relacionados por transacciones únicas. Views manejan solicitudes, Services concentran reglas y Models conservan las relaciones. Separar esas responsabilidades mejora la revisión y evita la complejidad de servicios distribuidos en esta escala.

**¿Por qué un grupo de dos personas no puede ocupar una habitación de tres?** La regla RN-02 del informe E2 exige igualdad exacta, aunque difiera de otros hoteles. El servidor rechaza 2 o 4 personas para capacidad 3, incluida una petición manipulada.

**¿Quién calcula el monto?** El servicio del servidor multiplica $40.000 por pasajeros únicos. El usuario no puede escribir ni modificar el costo. El total no incluye noches porque la especificación fija el costo por pasajero de la contratación.

**¿Qué impide que un encargado se convierta en administrador?** Las rutas requieren rol, los formularios exponen campos definidos y la creación de usuarios está limitada a Encargados. Ocultar menús es una ayuda visual; la autorización se vuelve a comprobar en el servidor.

**¿Qué pasa si se asigna una habitación desde dos terminales a la vez?** El servicio vuelve a comprobar la disponibilidad dentro de la transacción. SQLite serializa escrituras breves y las restricciones impiden dos detalles activos por habitación o dos hospedajes activos por pasajero. Deben medirse bloqueos y carga reales antes de usar varias recepciones intensivamente.

**¿Por qué el responsable no es un atributo del pasajero?** Ser responsable depende del grupo y de la estadía. Se almacena como una relación de Asignación a un Pasajero que pertenece a sus hospedajes.

**¿Se pierde el historial al editar o dar de baja?** La baja de una habitación es lógica. Las relaciones se conservan y los datos históricos de habitación/pasajero se copian al crear la estadía. Los cambios posteriores no reescriben el pasado.

**¿El historial es inviolable?** Está protegido desde la aplicación y las relaciones. Quien tenga acceso directo al código o al disco puede alterar el sistema; mayor resistencia exige controles operacionales y eventualmente registros externos. La evidencia académica no se presenta como un archivo forense certificado.

**¿Cómo se relaciona con Ley 21.459?** Permisos efectivos e integridad contribuyen a prevenir acceso y manipulación indebidos. La aplicación usa datos demo y sus pruebas se ejecutan en un entorno autorizado. Los controles no equivalen a una declaración integral de cumplimiento legal.

**¿Está certificado ISO?** No. ISO sirve como referencia para riesgos, controles y mejora continua. Se documentan activos, pruebas y correcciones; certificación requiere un proceso organizacional y evaluación específica.

**¿Cumple HTTPS?** El modo de producción prepara HTTPS y cookies seguras. La demostración en localhost se ejecuta por HTTP; TLS efectivo requiere infraestructura y una verificación del despliegue.

**¿Ya está en Cloud?** No se hizo despliegue público. Se dejó preparado para PaaS mediante WSGI, variables de entorno, dependencias fijadas y propuesta de almacenamiento persistente. Debe mostrarse la URL y evidencia posterior si se exige una implementación Cloud efectiva.

**¿Qué no cubre el prototipo?** Reservas en línea, pagos, facturación, portal de pasajeros, alta disponibilidad, política jurídica de retención y pruebas de carga de producción. Estos límites no sustituyen los 25 RF del alcance implementado.

**¿Cómo se comprueba que funciona?** La matriz une cada RF con código y pruebas; la suite verifica éxito, rechazo y conservación. La demostración recorre operaciones reales, y el documento de evidencia registra las ejecuciones comprobadas y sus límites.
