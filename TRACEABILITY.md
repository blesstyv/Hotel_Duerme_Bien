# Trazabilidad Evaluación 2 → Evaluación 3

La matriz relaciona los 25 RF del informe E2, páginas 14 a 16, con la implementación concreta y sus pruebas. Los resultados ejecutados se registran en `docs/EVIDENCIAS_E3.md`. Las pruebas citadas existen en los archivos indicados; la existencia de una prueba por sí sola no equivale a ejecución aprobada.

Para compactar los identificadores: `V` corresponde a `hotel.tests.test_views` y `S` a `hotel.tests.test_services`. Cada nombre después del prefijo identifica una clase y un método reales.

| RF | Funcionalidad implementada | Archivo / módulo | Prueba asociada |
|---|---|---|---|
| RF-01 | Login real, credenciales, usuario activo y panel según rol. | `hotel/views.py::login_view`, `hotel/forms.py::LoginForm`, `hotel/models.py::Usuario` | `V.AuthenticationTests.test_login_success`, `test_admin_login_and_dashboard`, `test_login_wrong_password`, `test_login_inactive`. |
| RF-02 | Autorización backend por rol y protección de rutas. | `hotel/decorators.py`, `hotel/views.py`, `hotel/services.py::exigir_encargado` | `V.RoleAndCrudTests.test_anonymous_direct_routes_protected`, `test_admin_hotel_routes_denied`, `test_encargado_admin_routes_denied`; `S.AssignmentTests.test_service_admin_denied`. |
| RF-03 | Administrador registra Encargados con campos explícitos. | `hotel/views.py::encargado_crear`, `hotel/forms.py::EncargadoCreationForm` | `V.RoleAndCrudTests.test_admin_creates_encargado_and_ignores_privilege_fields`, `test_encargado_duplicate_username_rejected`. |
| RF-04 | Consulta, edición y activación/desactivación de Encargados. | `hotel/views.py::encargado_list`, `encargado_editar`, `encargado_estado`; `hotel/forms.py::EncargadoEditForm` | `V.RoleAndCrudTests.test_edit_encargado`, `test_activate_deactivate_encargado`, `test_admin_cannot_target_admin_by_url`; `V.AuthenticationTests.test_deactivation_revokes_existing_session`. |
| RF-05 | Habitación con número único, capacidad y orientación; Vacante inicial. | `hotel/models.py::Habitacion`, `hotel/forms.py::HabitacionForm`, `hotel/views.py::habitacion_crear` | `S.ValidationTests.test_valid_room_starts_vacant`, `test_duplicate_room_rejected`, `test_zero_capacity_rejected`; `V.RoleAndCrudTests.test_register_and_edit_room`. |
| RF-06 | Editar datos de habitación conservando historia y capacidad activa. | `hotel/views.py::habitacion_editar`, `hotel/forms.py::HabitacionForm`, snapshots en `hotel/models.py` | `V.RoleAndCrudTests.test_register_and_edit_room`; `S.ValidationTests.test_occupied_room_capacity_change_rejected`; `S.AssignmentTests.test_history_preserves_original_data_after_edits`. |
| RF-07 | Listar, buscar y filtrar habitaciones por estado/capacidad. | `hotel/views.py::habitacion_list`, `hotel/templates/hotel/habitacion_list.html` | `V.RoleAndCrudTests.test_room_search_and_capacity_filter`, `V.FlowTests.test_all_encargado_read_screens`. |
| RF-08 | Registro individual de pasajero, RUT y nombre; contacto opcional. | `hotel/models.py::Pasajero`, `hotel/forms.py::PasajeroForm`, `hotel/validators.py`, `hotel/views.py::pasajero_crear` | `S.ValidationTests.test_valid_passenger_formatted_rut`, `test_duplicate_rut_canonicalized`, `test_wrong_check_digit_rejected`, `test_optional_contact_and_invalid_email`. |
| RF-09 | Editar pasajero sin reescribir datos de estadías anteriores. | `hotel/views.py::pasajero_editar`, `hotel/forms.py::PasajeroForm`, snapshots en `hotel/models.py::Hospedaje` | `V.RoleAndCrudTests.test_register_edit_search_passenger`; `S.AssignmentTests.test_history_preserves_original_data_after_edits`. |
| RF-10 | Búsqueda de pasajeros por RUT y nombre/apellido. | `hotel/views.py::pasajero_list` | `V.RoleAndCrudTests.test_register_edit_search_passenger`. |
| RF-11 | Asignación a habitaciones vacantes con pasajeros registrados. | `hotel/views.py::asignacion_crear`, `hotel/forms.py::AsignacionForm`, `hotel/services.py::validar_asignacion`, `crear_asignacion` | `S.AssignmentTests.test_exact_capacity_success`, `test_occupied_room_rejected`, `test_missing_passenger_rejected`, `test_already_hosted_passenger_rejected`. |
| RF-12 | Igualdad exacta por habitación y rechazo atómico del grupo. | `hotel/forms.py::AsignacionForm.clean`, `hotel/services.py::validar_asignacion`, `crear_asignacion` | `S.AssignmentTests.test_capacity_underfilled_rejected`, `test_capacity_overfilled_rejected`, `test_atomic_rejection_preserves_all_rooms`. |
| RF-13 | Costo de $40.000 por pasajero calculado por backend. | `hotel/services.py::TARIFA_PASAJERO`, `crear_asignacion`; `hotel/models.py::Asignacion.costo_total` | `S.AssignmentTests.test_cost_automatic`; `V.FlowTests.test_preview_confirm_and_server_owned_fields`. |
| RF-14 | Timestamp automático y usuario de registro, ineditables. | `hotel/models.py::Asignacion.fecha_ingreso`, `registrada_por`, `campos_inmutables` | `S.AssignmentTests.test_timestamp_automatic_and_author`, `test_history_immutable_cost_timestamp`; `V.FlowTests.test_preview_confirm_and_server_owned_fields`. |
| RF-15 | Todas las habitaciones pasan a Ocupada tras confirmación. | `hotel/services.py::crear_asignacion`, `hotel/models.py::Habitacion` | `S.AssignmentTests.test_exact_capacity_success`, `test_multiple_rooms_exact_capacity`. |
| RF-16 | Salida completa, fecha/usuario de cierre y habitaciones Vacantes. | `hotel/services.py::liberar_asignacion`, `hotel/views.py::asignacion_liberar` | `S.AssignmentTests.test_release_all_rooms`, `test_release_twice_rejected`, `test_reassignment_after_release`; `V.FlowTests.test_detail_and_release_route`. |
| RF-17 | Totales y porcentaje de ocupación actual sobre habitaciones activas. | `hotel/services.py::resumen_ocupacion`, `hotel/views.py::dashboard_encargado`, `ocupacion` | `S.AssignmentTests.test_occupancy_summary_and_inactive_exclusion`; `V.FlowTests.test_occupancy_panel`. |
| RF-18 | Historial por habitación con datos de estadía y costos. | `hotel/views.py::habitacion_historial`, `hotel/models.py::DetalleHabitacionAsignada` | `V.FlowTests.test_room_history`; `S.AssignmentTests.test_vacant_room_logical_deletion_preserves_history`. |
| RF-19 | Historial por pasajero con sus habitaciones y responsable. | `hotel/views.py::pasajero_historial`, `hotel/models.py::Hospedaje` | `V.FlowTests.test_passenger_history`. |
| RF-20 | Logout seguro por POST e invalidación de sesión. | `hotel/views.py::logout_view`, formularios CSRF en navegación | `V.AuthenticationTests.test_logout_post_and_session_removed`, `test_logout_get_disallowed`. |
| RF-21 | Grupo multihabitación con distribución individual exacta. | `hotel/models.py::Asignacion`, `DetalleHabitacionAsignada`, `Hospedaje`; `hotel/services.py::crear_asignacion` | `S.AssignmentTests.test_multiple_rooms_exact_capacity`, `test_duplicate_passenger_between_rooms_rejected`, `test_duplicate_passenger_inside_room_rejected`, `test_atomic_rejection_preserves_all_rooms`. |
| RF-22 | Responsable único perteneciente al grupo; no atributo permanente. | `hotel/models.py::Asignacion.responsable`, `hotel/services.py::validar_asignacion`, `hotel/forms.py::AsignacionForm` | `S.AssignmentTests.test_responsible_correct`, `test_responsible_outside_group_rejected`; `V.FlowTests.test_current_responsible_badge_derived`. |
| RF-23 | Bloqueo de baja con ocupación o asignación activa. | `hotel/services.py::eliminar_habitacion`, `hotel/views.py::habitacion_eliminar` | `S.AssignmentTests.test_occupied_room_logical_deletion_blocked`. |
| RF-24 | Baja lógica vacante conserva todo historial y excluye disponibilidad. | `hotel/models.py::Habitacion.activa`, relaciones `PROTECT`; `hotel/services.py::eliminar_habitacion` | `S.AssignmentTests.test_vacant_room_logical_deletion_preserves_history`, `test_inactive_room_cannot_be_assigned`, `test_history_cannot_be_deleted`; `V.FlowTests.test_inactive_room_hidden_from_assignment`. |
| RF-25 | Lista actual de pasajeros con habitación y responsable. | `hotel/views.py::ocupacion`, `hotel/templates/hotel/ocupacion.html`, `hotel/models.py::Hospedaje` | `V.FlowTests.test_occupancy_panel`, `test_current_responsible_badge_derived`. |

## Seguridad y operación complementaria

| Condición | Evidencia automática |
|---|---|
| Hash seguro y salt | `hotel.tests.test_views.AuthenticationTests.test_password_is_salted_hash`. |
| CSRF | `hotel.tests.test_views.AuthenticationTests.test_csrf_required`. |
| Escape de HTML | `hotel.tests.test_views.RoleAndCrudTests.test_html_escaped`. |
| Expiración e inactividad | `hotel.tests.test_views.AuthenticationTests.test_inactivity_expiry`. |
| Bloqueo temporal por intentos | `hotel.tests.test_views.AuthenticationTests.test_login_throttle`. |
| Protección de redirección externa | `hotel.tests.test_views.AuthenticationTests.test_external_next_url_blocked`. |
| Recursos activos únicos en base | `hotel.tests.test_services.AssignmentTests.test_database_enforces_unique_active_room`, `test_database_enforces_unique_active_passenger`. |
| Asignaciones concurrentes | `hotel.tests.test_concurrency.ConcurrencyTests.test_simultaneous_assignments_only_one_occupies_room`. |
| Demo idempotente | `hotel.tests.test_commands.CommandTests.test_seed_demo_idempotent_and_coherent`. |
| Demo bloqueada en producción | `hotel.tests.test_commands.CommandTests.test_demo_denied_in_production`. |
| Respaldo con integridad | `hotel.tests.test_commands.CommandTests.test_backup_integrity`. |

La matriz funcional no declara completos los RNF operacionales. HTTPS real, disponibilidad continua, respaldo programado, compatibilidad completa y rendimiento a escala requieren evidencia adicional descrita en `docs/REQUERIMIENTOS_E2.md` y `docs/DESPLIEGUE_CLOUD.md`.
