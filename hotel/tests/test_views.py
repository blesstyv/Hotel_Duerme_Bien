import time
from django.contrib.auth.hashers import identify_hasher
from django.test import Client, override_settings
from django.urls import reverse
from hotel.models import Usuario, Habitacion, Pasajero, Asignacion, LoginIntento, Hospedaje
from hotel.services import crear_asignacion, liberar_asignacion
from .base import HotelTestCase, PASSWORD

def url(name, pk=None):
    return reverse('hotel:' + name, kwargs={'pk': pk} if pk is not None else None)

class AuthenticationTests(HotelTestCase):
    def test_login_success(self):
        response = self.client.post(url('login'), {'username': self.encargado.username, 'password': PASSWORD})
        self.assertRedirects(response, url('inicio'), fetch_redirect_response=False)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.encargado.pk)

    def test_admin_login_and_dashboard(self):
        self.client.login(username=self.admin_user.username, password=PASSWORD)
        self.assertRedirects(self.client.get(url('inicio')), url('dashboard_admin'))

    def test_login_wrong_password(self):
        response = self.client.post(url('login'), {'username': self.encargado.username, 'password': 'incorrecta'})
        self.assertContains(response, 'Usuario o contraseña incorrectos')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_inactive(self):
        response = self.client.post(url('login'), {'username': self.inactive.username, 'password': PASSWORD})
        self.assertContains(response, 'Usuario o contraseña incorrectos')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_unknown_account_same_error(self):
        response = self.client.post(url('login'), {'username': 'no_existe', 'password': PASSWORD})
        self.assertContains(response, 'Usuario o contraseña incorrectos')

    @override_settings(LOGIN_MAX_FAILURES=2)
    def test_login_throttle(self):
        for _ in range(2):
            self.client.post(url('login'), {'username': self.encargado.username, 'password': 'mala'})
        response = self.client.post(url('login'), {'username': self.encargado.username, 'password': PASSWORD})
        self.assertEqual(response.status_code, 429)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_password_is_salted_hash(self):
        self.assertNotEqual(self.encargado.password, PASSWORD)
        self.assertEqual(identify_hasher(self.encargado.password).algorithm, 'pbkdf2_sha256')
        self.assertTrue(self.encargado.check_password(PASSWORD))

    def test_external_next_url_blocked(self):
        response = self.client.post(url('login'), {'username': self.encargado.username, 'password': PASSWORD, 'next': 'https://evil.example/'})
        self.assertEqual(response.url, url('inicio'))

    def test_logout_post_and_session_removed(self):
        self.client.force_login(self.encargado)
        response = self.client.post(url('logout'))
        self.assertRedirects(response, url('login'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_get_disallowed(self):
        self.client.force_login(self.encargado)
        self.assertEqual(self.client.get(url('logout')).status_code, 405)
        self.assertIn('_auth_user_id', self.client.session)

    @override_settings(SESSION_INACTIVITY_SECONDS=10)
    def test_inactivity_expiry(self):
        self.client.force_login(self.encargado)
        session = self.client.session
        session['ultima_actividad'] = int(time.time()) - 20
        session.save()
        self.assertEqual(self.client.get(url('dashboard_encargado')).status_code, 302)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_deactivation_revokes_existing_session(self):
        self.client.force_login(self.encargado)
        self.encargado.is_active = False
        self.encargado.save(update_fields=['is_active'])
        self.assertEqual(self.client.get(url('habitacion_list')).status_code, 302)

    def test_csrf_required(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(url('login'), {'username': self.encargado.username, 'password': PASSWORD})
        self.assertEqual(response.status_code, 403)

    def test_security_headers_and_cache(self):
        self.client.force_login(self.encargado)
        response = self.client.get(url('dashboard_encargado'))
        self.assertEqual(response['X-Frame-Options'], 'DENY')
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.assertIn("default-src 'self'", response['Content-Security-Policy'])
        self.assertIn('no-store', response['Cache-Control'])

class RoleAndCrudTests(HotelTestCase):
    def test_initial_superuser_has_administrator_role_and_no_hotel_access(self):
        user = Usuario.objects.create_superuser(username='initial_admin', password=PASSWORD)
        self.assertEqual(user.rol, 'ADMINISTRADOR')
        self.client.force_login(user)
        self.assertEqual(self.client.get(url('habitacion_list')).status_code, 403)

    def test_anonymous_direct_routes_protected(self):
        routes = [('dashboard_admin', None), ('encargado_list', None), ('encargado_crear', None), ('encargado_editar', self.encargado.pk),
                  ('dashboard_encargado', None), ('habitacion_list', None), ('habitacion_crear', None), ('habitacion_editar', self.room1.pk),
                  ('pasajero_list', None), ('pasajero_crear', None), ('pasajero_editar', self.people[0].pk), ('asignacion_list', None),
                  ('asignacion_crear', None), ('ocupacion', None), ('historiales', None), ('habitacion_historial', self.room1.pk), ('pasajero_historial', self.people[0].pk)]
        for name, pk in routes:
            with self.subTest(route=name):
                response = self.client.get(url(name, pk))
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith(url('login')))

    def test_admin_hotel_routes_denied(self):
        self.client.force_login(self.admin_user)
        for name in ('dashboard_encargado', 'habitacion_list', 'habitacion_crear', 'pasajero_list', 'pasajero_crear', 'asignacion_list', 'asignacion_crear', 'ocupacion', 'historiales'):
            with self.subTest(route=name):
                self.assertEqual(self.client.get(url(name)).status_code, 403)
        self.assertEqual(self.client.post(url('habitacion_eliminar', self.room1.pk)).status_code, 403)

    def test_encargado_admin_routes_denied(self):
        self.client.force_login(self.encargado)
        for name in ('dashboard_admin', 'encargado_list', 'encargado_crear'):
            with self.subTest(route=name):
                self.assertEqual(self.client.get(url(name)).status_code, 403)
        self.assertEqual(self.client.post(url('encargado_estado', self.inactive.pk)).status_code, 403)
        self.assertEqual(self.client.post(url('encargado_editar', self.inactive.pk), {'username': 'hack'}).status_code, 403)

    def test_admin_creates_encargado_and_ignores_privilege_fields(self):
        self.client.force_login(self.admin_user)
        data = {'username': 'nuevo', 'first_name': 'Ana', 'last_name': 'Pérez', 'email': 'ana@example.test', 'password1': PASSWORD, 'password2': PASSWORD, 'rol': 'ADMINISTRADOR', 'is_staff': 'on', 'is_superuser': 'on'}
        response = self.client.post(url('encargado_crear'), data)
        self.assertRedirects(response, url('encargado_list'))
        user = Usuario.objects.get(username='nuevo')
        self.assertEqual(user.rol, 'ENCARGADO')
        self.assertFalse(user.is_staff or user.is_superuser)
        self.assertTrue(user.check_password(PASSWORD))

    def test_encargado_duplicate_username_rejected(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(url('encargado_crear'), {'username': self.encargado.username, 'first_name': 'Ana', 'last_name': 'Pérez', 'password1': PASSWORD, 'password2': PASSWORD})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)

    def test_encargado_weak_password_rejected(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(url('encargado_crear'), {'username': 'nuevo', 'first_name': 'Ana', 'last_name': 'Pérez', 'password1': '123', 'password2': '123'})
        self.assertTrue(response.context['form'].errors)
        self.assertFalse(Usuario.objects.filter(username='nuevo').exists())

    def test_edit_encargado(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(url('encargado_editar', self.encargado.pk), {'username': self.encargado.username, 'first_name': 'Nombre', 'last_name': 'Nuevo', 'email': 'nuevo@example.test', 'rol': 'ADMINISTRADOR'})
        self.assertRedirects(response, url('encargado_list'))
        self.encargado.refresh_from_db()
        self.assertEqual(self.encargado.first_name, 'Nombre')
        self.assertEqual(self.encargado.rol, 'ENCARGADO')

    def test_admin_cannot_target_admin_by_url(self):
        self.client.force_login(self.admin_user)
        self.assertEqual(self.client.get(url('encargado_editar', self.admin_user.pk)).status_code, 404)
        self.assertEqual(self.client.post(url('encargado_estado', self.admin_user.pk)).status_code, 404)

    def test_activate_deactivate_encargado(self):
        self.client.force_login(self.admin_user)
        self.client.post(url('encargado_estado', self.encargado.pk))
        self.encargado.refresh_from_db()
        self.assertFalse(self.encargado.is_active)
        self.client.post(url('encargado_estado', self.encargado.pk))
        self.encargado.refresh_from_db()
        self.assertTrue(self.encargado.is_active)

    def test_mutations_require_post(self):
        self.client.force_login(self.admin_user)
        self.assertEqual(self.client.get(url('encargado_estado', self.encargado.pk)).status_code, 405)
        self.client.force_login(self.encargado)
        self.assertEqual(self.client.get(url('habitacion_eliminar', self.room1.pk)).status_code, 405)

    def test_register_and_edit_room(self):
        self.client.force_login(self.encargado)
        self.assertRedirects(self.client.post(url('habitacion_crear'), {'numero': '900', 'capacidad': 2, 'orientacion': 'NORTE'}), url('habitacion_list'))
        room = Habitacion.objects.get(numero='900')
        self.assertRedirects(self.client.post(url('habitacion_editar', room.pk), {'numero': '901', 'capacidad': 3, 'orientacion': 'SUR'}), url('habitacion_list'))
        room.refresh_from_db()
        self.assertEqual(room.numero, '901')

    def test_room_search_and_capacity_filter(self):
        self.client.force_login(self.encargado)
        response = self.client.get(url('habitacion_list'), {'capacidad': 2, 'estado': 'VACANTE'})
        self.assertEqual(list(response.context['habitaciones']), [self.room2])
        response = self.client.get(url('habitacion_list'), {'q': '103'})
        self.assertEqual(list(response.context['habitaciones']), [self.room3])

    def test_register_edit_search_passenger(self):
        self.client.force_login(self.encargado)
        response = self.client.post(url('pasajero_crear'), {'rut': '12.345.678-5', 'nombre_completo': 'María Pérez'})
        self.assertRedirects(response, url('pasajero_list'))
        passenger = Pasajero.objects.get(rut='12345678-5')
        self.assertRedirects(self.client.post(url('pasajero_editar', passenger.pk), {'rut': passenger.rut, 'nombre_completo': 'María Corregida'}), url('pasajero_list'))
        response = self.client.get(url('pasajero_list'), {'q': 'Corregida'})
        self.assertEqual(len(response.context['pasajeros']), 1)

    def test_html_escaped(self):
        self.people[0].nombre_completo = '<script>alert(1)</script>'
        self.people[0].save()
        self.client.force_login(self.encargado)
        response = self.client.get(url('pasajero_list'))
        self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;')
        self.assertNotContains(response, '<script>alert(1)</script>')

class FlowTests(HotelTestCase):
    def setUp(self):
        self.client.force_login(self.encargado)

    def distribution(self):
        return {'rooms': [str(self.room1.pk)], f'pasajeros_{self.room1.pk}': [str(self.people[0].pk)], 'responsable': str(self.people[0].pk)}

    def test_preview_confirm_and_server_owned_fields(self):
        data = self.distribution()
        response = self.client.post(url('asignacion_crear'), {**data, 'action': 'preview', 'costo_total': 1, 'fecha_ingreso': '2000-01-01'})
        self.assertFalse(Asignacion.objects.exists())
        self.assertEqual(response.context['preview']['costo_total'], 40000)
        response = self.client.post(url('asignacion_crear'), {**data, 'action': 'confirm', 'preview_token': response.context['preview_token'], 'costo_total': 1, 'fecha_ingreso': '2000-01-01'})
        assignment = Asignacion.objects.get()
        self.assertRedirects(response, url('asignacion_detalle', assignment.pk))
        self.assertEqual(assignment.costo_total, 40000)
        self.assertGreater(assignment.fecha_ingreso.year, 2000)

    def test_confirm_without_preview_rejected(self):
        response = self.client.post(url('asignacion_crear'), {**self.distribution(), 'action': 'confirm'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Asignacion.objects.exists())
        self.assertTrue(response.context['form'].errors)

    def test_preview_revalidated_when_room_taken(self):
        data = self.distribution()
        response = self.client.post(url('asignacion_crear'), {**data, 'action': 'preview'})
        token = response.context['preview_token']
        crear_asignacion({self.room1.pk: [self.people[1].pk]}, self.people[1].pk, self.encargado)
        response = self.client.post(url('asignacion_crear'), {**data, 'action': 'confirm', 'preview_token': token})
        self.assertTrue(response.context['form'].errors)
        self.assertEqual(Asignacion.objects.count(), 1)

    def test_preview_distribution_tampering_rejected(self):
        data = self.distribution()
        response = self.client.post(url('asignacion_crear'), {**data, 'action': 'preview'})
        tampered = {**data, f'pasajeros_{self.room1.pk}': [str(self.people[1].pk)], 'responsable': str(self.people[1].pk)}
        response = self.client.post(url('asignacion_crear'), {**tampered, 'action': 'confirm', 'preview_token': response.context['preview_token']})
        self.assertTrue(response.context['form'].errors)
        self.assertFalse(Asignacion.objects.exists())

    def test_malformed_preview_token_safe(self):
        response = self.client.post(url('asignacion_crear'), {**self.distribution(), 'action': 'confirm', 'preview_token': 'é'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Asignacion.objects.exists())

    def test_inactive_room_hidden_from_assignment(self):
        from hotel.services import eliminar_habitacion
        eliminar_habitacion(self.room1.pk, self.encargado)
        response = self.client.get(url('asignacion_crear'))
        self.assertNotIn(self.room1, response.context['available_rooms'])

    def test_occupancy_panel(self):
        assignment = crear_asignacion({self.room1.pk: [self.people[0].pk]}, self.people[0].pk, self.encargado)
        response = self.client.get(url('ocupacion'))
        self.assertEqual(response.context['stats']['ocupadas'], 1)
        self.assertEqual(len(response.context['hospedajes']), 1)
        self.assertContains(response, self.people[0].nombre_completo)

    def test_current_responsible_badge_derived(self):
        assignment = crear_asignacion({self.room1.pk: [self.people[0].pk]}, self.people[0].pk, self.encargado)
        response = self.client.get(url('pasajero_list'))
        passenger = next(p for p in response.context['pasajeros'] if p.pk == self.people[0].pk)
        self.assertTrue(passenger.es_responsable)
        liberar_asignacion(assignment.pk, self.encargado)
        response = self.client.get(url('pasajero_list'))
        passenger = next(p for p in response.context['pasajeros'] if p.pk == self.people[0].pk)
        self.assertFalse(passenger.es_responsable)

    def test_room_history(self):
        assignment = crear_asignacion({self.room1.pk: [self.people[0].pk]}, self.people[0].pk, self.encargado)
        liberar_asignacion(assignment.pk, self.encargado)
        response = self.client.get(url('habitacion_historial', self.room1.pk))
        self.assertEqual(len(response.context['detalles']), 1)
        self.assertContains(response, '40.000')

    def test_passenger_history(self):
        assignment = crear_asignacion({self.room1.pk: [self.people[0].pk]}, self.people[0].pk, self.encargado)
        liberar_asignacion(assignment.pk, self.encargado)
        response = self.client.get(url('pasajero_historial', self.people[0].pk))
        self.assertEqual(len(response.context['hospedajes']), 1)
        self.assertContains(response, self.people[0].rut)

    def test_detail_and_release_route(self):
        assignment = crear_asignacion({self.room1.pk: [self.people[0].pk]}, self.people[0].pk, self.encargado)
        self.assertEqual(self.client.get(url('asignacion_liberar', assignment.pk)).status_code, 405)
        self.assertRedirects(self.client.post(url('asignacion_liberar', assignment.pk)), url('asignacion_detalle', assignment.pk))
        self.room1.refresh_from_db()
        self.assertEqual(self.room1.estado, 'VACANTE')

    def test_all_encargado_read_screens(self):
        for name in ('dashboard_encargado', 'habitacion_list', 'habitacion_crear', 'pasajero_list', 'pasajero_crear', 'asignacion_list', 'asignacion_crear', 'ocupacion', 'historiales'):
            with self.subTest(route=name):
                self.assertEqual(self.client.get(url(name)).status_code, 200)
