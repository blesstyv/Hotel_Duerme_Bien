# Seguridad, confiabilidad y ética

La información del hotel incluye identificadores de pasajeros, contactos, credenciales e historial de estadías. Los controles del prototipo buscan restringir acceso, impedir inconsistencias y permitir revisar las operaciones. Son evidencia técnica de una implementación académica; no constituyen certificación ISO ni declaración de conformidad jurídica integral.

## Principios y evidencias

| Principio | Aplicación verificable | Límite operativo |
|---|---|---|
| Confidencialidad | Autenticación y autorización del servidor por roles; datos de pasajeros para Encargado. | Requiere protección de equipos, respaldos y canal TLS en producción. |
| Integridad | Unicidad, exactitud de capacidad, costo en servidor, transacciones y protección histórica. | El administrador del sistema operativo conserva acceso al archivo SQLite. |
| Disponibilidad | Comando de respaldo y ejecución WSGI. | Una instancia local no acredita continuidad 24/7 ni recuperación ante desastre. |
| Responsabilidad | Usuario y timestamp en asignación/salida; registro de eventos. | Revisión de eventos y respuesta a incidentes requieren responsables humanos. |
| Transparencia | Métricas provenientes de datos, pruebas reproducibles y límites declarados. | No usar resultados locales como garantía universal. |
| Minimización | RUT y nombre; contacto opcional; datos demo sintéticos. | Uso real requiere políticas de finalidad, acceso, conservación y derechos del titular. |

## Referencia jurídica

La Ley 21.459 establece delitos informáticos. El acceso fuera de la autorización y las alteraciones indebidas de sistemas o datos motivan permisos verificables, protección histórica y pruebas limitadas al entorno autorizado. Esta relación entre normas y controles es una interpretación para el proyecto, no un análisis de responsabilidades penales particulares. Fuente: [BCN, Ley 21.459, versión vigente consultada](https://www.bcn.cl/leychile/Navegar?idNorma=1177743&idVersion=2025-04-01).

Los datos de pasajeros también exigen considerar protección de la vida privada, finalidad de tratamiento y derechos de las personas. Al 14 de octubre de 2026, la ficha de BCN mantiene la versión actual de la Ley 19.628 hasta el 30 de noviembre; las modificaciones de la Ley 21.719 tienen vigencia diferida al 1 de diciembre de 2026. Antes de una operación real se debe revisar esa transición y definir una política de retención, atención de solicitudes y responsabilidad del hotel. La regla académica de historial no eliminable no justifica conservar datos personales indefinidamente. Fuentes: [BCN, Ley 19.628 aplicable en esta fecha](https://www.bcn.cl/leychile/Navegar?idNorma=141599&idVersion=2023-05-09) y [texto con vigencia diferida](https://www.bcn.cl/leychile/navegar?idNorma=141599&idVersion=2026-12-01).

## ISO como marco de trabajo

ISO/IEC 27000 ofrece el marco conceptual de la familia de seguridad de la información; ISO/IEC 27001 especifica requisitos para un sistema de gestión. La aplicación adopta un análisis de activos, riesgos y controles, junto con revisión de evidencias. Estas tareas técnicas son solo una parte de un sistema organizacional de gestión. Las referencias públicas consultadas son [ISO/IEC 27000:2026](https://www.iso.org/standard/27000) e [ISO/IEC 27001:2022](https://www.iso.org/standard/27001).

ISO 9001 aporta un enfoque de gestión de calidad y mejora continua. En este proyecto se aplica mediante requerimientos identificados, criterios de aceptación, pruebas, corrección de defectos y actualización de la trazabilidad. No se realizaron auditorías de certificación. La ficha oficial consultada corresponde a [ISO 9001:2026](https://www.iso.org/es/norma/9001).

| Ciclo de mejora | Evidencia del proyecto |
|---|---|
| Planificar | RF/RN/RNF del E2, riesgos y diseño por capas. |
| Hacer | Servicios, autorización, restricciones y configuración. |
| Verificar | Suite automática, `django check`, inspección de rutas y revisión visual. |
| Actuar | Reparar errores encontrados y repetir las pruebas afectadas. |

## OWASP Top 10:2025

La numeración se basa en la [lista oficial OWASP Top 10:2025](https://top10.owasp.org/2025/0x00_2025-Introduction/), consistente con la tabla de seguridad del informe E2. La columna de controles describe decisiones de este proyecto.

| Riesgo | Control del prototipo | Evidencia o trabajo operacional |
|---|---|---|
| A01 Control de acceso roto | Decoradores y validaciones de rol en servidor, incluso por URL directa. | Pruebas de permisos para ambos perfiles. |
| A02 Configuración insegura | Secretos por entorno, DEBUG separable, hosts explícitos y ajustes de producción. | Revisión de `.env.example` y `check --deploy`. |
| A03 Fallas de suministro de software | Dependencias fijadas en `requirements.txt`. | Actualización y revisión de vulnerabilidades antes del despliegue. |
| A04 Fallas criptográficas | Hash con salt de Django; cookies y redirección HTTPS en producción. | Pruebas de hash y configuración; TLS real pendiente de infraestructura. |
| A05 Inyección | ORM parametrizado, autoescape y CSRF en operaciones de escritura. | Validaciones y pruebas de escape/CSRF. |
| A06 Diseño inseguro | Capacidad, responsable y costo validados por servicios atómicos. | Pruebas negativas y rollback completo. |
| A07 Fallas de autenticación | Autenticación Django, bloqueo de cuentas inactivas y expiración por actividad. | Pruebas de login y sesión; revisión del manejo de intentos fallidos. |
| A08 Integridad de software o datos | Historial protegido, baja lógica y restricciones de base de datos. | Pruebas de conservación y relaciones históricas. |
| A09 Registro y alertas | Eventos y usuario de operación. | Alertas externas y revisión sistemática de logs requieren configuración operacional. |
| A10 Condiciones excepcionales | Errores controlados, rollback y páginas seguras con DEBUG desactivado. | Pruebas de fallas de negocio y verificación de páginas de error. |

No se presenta esta tabla como cobertura exhaustiva del Top 10 o pentest. El sistema debe revisarse después de cada cambio y antes de su uso con datos reales.

## Separación de desarrollo y producción

En desarrollo se permite HTTP sobre `127.0.0.1` y DEBUG para diagnóstico. En producción se requiere un SECRET_KEY aleatorio, DEBUG desactivado, hosts concretos, HTTPS terminado por infraestructura confiable y cookies seguras. La sesión tiene duración configurable; los secretos y contraseñas demo se guardan en `.env`, excluido de Git.

Nunca incluir `.env`, base de datos real, respaldos o logs con datos personales en una entrega pública. Las pruebas de acceso y entradas maliciosas descritas en el plan se ejecutan exclusivamente en este prototipo autorizado. Los datos demo no deben utilizarse en un hotel real.
