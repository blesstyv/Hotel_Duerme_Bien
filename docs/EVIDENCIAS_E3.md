# Evidencias de la Evaluación 3

Proyecto: Sistema de Gestión de Pasajeros, Hotel Duerme Bien. Fecha de la entrega técnica: 14 de octubre de 2026, zona horaria America/Santiago.

Este documento distingue los archivos implementados de los resultados ejecutados. Las fuentes de requisitos son los dos PDF originales conservados en la raíz y los mockups del informe E2. La calificación corresponde a la profesora; los puntajes de la tabla son los máximos definidos por la rúbrica, no una autoevaluación otorgada.

## Correspondencia con la rúbrica de 50 puntos

| Criterio E3 | Máximo | Evidencia concreta | Alcance y límite |
|---|---:|---|---|
| Nuevas tendencias: SaaS/IaaS/PaaS/Cloud | 6 | WSGI, Waitress, WhiteNoise, Procfile, variables por entorno y `DESPLIEGUE_CLOUD.md`. | Preparación y propuesta PaaS verificables; no se realizó despliegue público. |
| Confiabilidad y ética: Ley 21.459, ISO 27000/9001 y OWASP | 6 | Permisos, integridad, historial, eventos, pruebas y `SEGURIDAD_Y_ETICA.md` con fuentes primarias. | Aplicación de principios; sin certificación ni conformidad jurídica integral. |
| Prototipo según requerimientos, seguridad y OWASP | 11 | Módulos reales para ambos roles, servicios, modelos y `TRACEABILITY.md`. | Verificar comportamiento mediante pruebas y recorrido del prototipo. |
| Arquitectura apropiada | 6 | Cliente-servidor por capas, servicios transaccionales y `ARQUITECTURA.md`. | Adecuada para un hotel y una instancia académica; sin alta disponibilidad. |
| Respuestas claras y fundamentadas | 9 | Preguntas y respuestas en `DEMOSTRACION_Y_DEFENSA.md`. | Material de preparación; la defensa oral aún corresponde al equipo. |
| Prototipo con reparto de roles y demostración | 6 | Guion de dos integrantes con operación Administrador y Encargado. | El guion debe ejecutarse en la presentación y adaptarse a sus participantes. |
| Pruebas documentadas, esperado, éxito y fracaso | 6 | Suite `hotel/tests/`, `PLAN_PRUEBAS.md` y resultados de esta entrega. | Cobertura funcional y de seguridad académica; no sustituye pentest o carga operacional. |

## Resultados ejecutados

| Verificación | Resultado registrado | Alcance |
|---|---|---|
| Servicios, validadores, comandos y concurrencia | 44 pruebas aprobadas en 6,926 segundos; sin problemas en `check` durante la ejecución. | Primer incremento verificado, antes del cierre de la UI. |
| Competencia real por una habitación | Dos hilos concurrentes: una asignación creada y la otra rechazada; una sola estadía activa. | Prueba de integración específica sobre SQLite; no es prueba de carga. |
| Matriz de trazabilidad | 25 filas de RF y métodos referenciados contrastados con los archivos de tests. | Revisión de correspondencia documental. |

El cierre de la suite completa, comprobación del esquema y revisión visual se incorpora tras su ejecución. Los resultados aún pendientes no se consideran aprobados.

## Cómo reproducir las evidencias

Desde la raíz del proyecto:

```powershell
.\.venv\Scripts\python.exe manage.py test hotel.tests --verbosity 2
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py seed_demo
.\.venv\Scripts\python.exe manage.py collectstatic --noinput
.\.venv\Scripts\python.exe scripts\serve.py
```

Usar las contraseñas demo del `.env` local y seguir el guion de demostración. La suite ejecuta escenarios de éxito y rechazos esperados en una base independiente. Para revisión por la profesora, abrir `TRACEABILITY.md` junto a la salida de tests y mostrar una prueba concreta asociada al RF solicitado.

## Límites que permanecen

- Transporte HTTPS, volumen persistente Cloud y servicio público: preparados mediante configuración, pendientes de despliegue real.
- Disponibilidad continua, recuperación ante desastre y alertas: requieren operación, responsables y programación fuera del prototipo.
- Escalabilidad: SQLite conserva un único escritor; se necesita evaluación de carga y eventualmente otro motor antes de múltiples instancias.
- Certificación ISO y evaluación jurídica integral: no realizadas. Los documentos aplican principios y señalan responsabilidades del hotel.
- Informe institucional E3: el contenido técnico está disponible en Markdown; portada, índice y formato vertical institucional deben integrarse en la entrega académica si se solicita ese documento final.
- Compatibilidad y desempeño: las mediciones y revisión local deben interpretarse en el equipo, navegador y volumen de datos reportados.
