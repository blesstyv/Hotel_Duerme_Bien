"""
Pruebas de las mejoras solicitadas en la retroalimentación de la Evaluación U2:

1. Bloqueo de 5 minutos tras 3 intentos fallidos de inicio de sesión.
2. Número de habitación exclusivamente numérico.
3. Fechas de inicio y término obligatorias; costo = pasajeros x noches x $40.000.
4. No se exige completar la capacidad de la habitación.
"""
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from hotel import services
from hotel.forms import HabitacionForm
from hotel.models import Asignacion, Habitacion, Hospedaje, LoginIntento

from .base import PASSWORD, HotelTestCase, crear_asignacion, estadia, validar_asignacion


def url(name, *args):
    return reverse(f"hotel:{name}", args=args)


class BloqueoInicioSesionTests(HotelTestCase):
    def fallar(self, veces, username=None):
        response = None
        for _ in range(veces):
            response = self.client.post(url("login"), {"username": username or self.encargado.username, "password": "incorrecta"})
        return response

    def test_configuracion_por_defecto_es_3_intentos_y_5_minutos(self):
        self.assertEqual(settings.LOGIN_MAX_FAILURES, 3)
        self.assertEqual(settings.LOGIN_LOCK_SECONDS, 300)

    def test_dos_fallos_no_bloquean_y_el_acceso_correcto_funciona(self):
        response = self.fallar(2)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Le queda 1 intento")
        response = self.client.post(url("login"), {"username": self.encargado.username, "password": PASSWORD})
        self.assertEqual(response.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)

    def test_tercer_fallo_bloquea_durante_5_minutos(self):
        antes = timezone.now()
        response = self.fallar(3)
        self.assertEqual(response.status_code, 429)
        self.assertContains(response, "bloqueado durante 5 minutos", status_code=429)
        intento = LoginIntento.objects.get()
        self.assertEqual(intento.fallos, 3)
        duracion = (intento.bloqueado_hasta - antes).total_seconds()
        self.assertGreaterEqual(duracion, 299)
        self.assertLessEqual(duracion, 302)

    def test_durante_el_bloqueo_se_rechaza_incluso_la_clave_correcta(self):
        self.fallar(3)
        response = self.client.post(url("login"), {"username": self.encargado.username, "password": PASSWORD})
        self.assertEqual(response.status_code, 429)
        self.assertContains(response, "bloqueada temporalmente", status_code=429)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_al_vencer_el_bloqueo_se_puede_ingresar_y_el_contador_se_reinicia(self):
        self.fallar(3)
        LoginIntento.objects.update(bloqueado_hasta=timezone.now() - timedelta(seconds=1))
        response = self.client.post(url("login"), {"username": self.encargado.username, "password": PASSWORD})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(LoginIntento.objects.get().fallos, 0)

    def test_acceso_correcto_reinicia_el_contador_de_fallos(self):
        self.fallar(2)
        self.client.post(url("login"), {"username": self.encargado.username, "password": PASSWORD})
        self.client.post(url("logout"))
        response = self.fallar(2)
        self.assertEqual(response.status_code, 200)

    def test_bloqueo_no_afecta_a_otro_usuario(self):
        self.fallar(3)
        response = self.client.post(url("login"), {"username": self.admin_user.username, "password": PASSWORD})
        self.assertEqual(response.status_code, 302)

    def test_usuario_inexistente_tambien_se_bloquea_sin_revelar_existencia(self):
        response = self.fallar(3, username="no_existe")
        self.assertEqual(response.status_code, 429)
        self.assertContains(response, "Usuario o contraseña incorrectos", status_code=429)

    @override_settings(LOGIN_MAX_FAILURES=3)
    def test_bloqueo_no_distingue_mayusculas_en_el_usuario(self):
        self.fallar(2)
        response = self.fallar(1, username=self.encargado.username.upper())
        self.assertEqual(response.status_code, 429)


class NumeroHabitacionTests(HotelTestCase):
    def setUp(self):
        self.client.force_login(self.encargado)

    def datos(self, numero):
        return {"numero": numero, "capacidad": 2, "orientacion": "NORTE", "vista": "MAR"}

    def test_numero_solo_digitos_se_registra(self):
        response = self.client.post(url("habitacion_crear"), self.datos("405"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Habitacion.objects.filter(numero="405").exists())

    def test_numeros_con_letras_o_simbolos_se_rechazan(self):
        for numero in ("10A", "A10", "B", "10-1", "10.5", "1 0", "１０１", "+12", "1e3", "10a"):
            with self.subTest(numero=numero):
                response = self.client.post(url("habitacion_crear"), self.datos(numero))
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context["form"].errors.get("numero"))
        self.assertEqual(Habitacion.objects.count(), 3)

    def test_cero_y_ceros_iniciales_se_rechazan(self):
        for numero in ("0", "00", "0101"):
            with self.subTest(numero=numero):
                self.assertFalse(HabitacionForm(self.datos(numero)).is_valid())

    def test_numero_de_mas_de_cinco_digitos_se_rechaza(self):
        self.assertFalse(HabitacionForm(self.datos("123456")).is_valid())

    def test_edicion_tampoco_admite_letras(self):
        response = self.client.post(url("habitacion_editar", self.room1.pk), self.datos("101B"))
        self.assertEqual(response.status_code, 200)
        self.room1.refresh_from_db()
        self.assertEqual(self.room1.numero, "101")

    def test_modelo_rechaza_letras_en_validacion_completa(self):
        room = Habitacion(numero="20A", capacidad=1, orientacion="NORTE")
        with self.assertRaises(ValidationError):
            room.full_clean()


class EstadiaYCostoTests(HotelTestCase):
    def uno(self, **kwargs):
        return crear_asignacion({self.room1.pk: [self.people[0].pk]}, self.people[0].pk, self.encargado, **kwargs)

    def test_una_persona_una_noche_40000(self):
        assignment = self.uno(noches=1)
        self.assertEqual(assignment.noches, 1)
        self.assertEqual(assignment.costo_total, 40000)

    def test_una_persona_dos_noches_80000(self):
        self.assertEqual(self.uno(noches=2).costo_total, 80000)

    def test_una_persona_tres_noches_120000(self):
        self.assertEqual(self.uno(noches=3).costo_total, 120000)

    def test_tres_personas_cuatro_noches_480000(self):
        assignment = crear_asignacion({self.room3.pk: [p.pk for p in self.people[:3]]}, self.people[0].pk, self.encargado, noches=4)
        self.assertEqual(assignment.costo_total, 480000)

    def test_grupo_en_varias_habitaciones_suma_personas_por_noche(self):
        assignment = crear_asignacion({self.room3.pk: [p.pk for p in self.people[:3]], self.room2.pk: [self.people[3].pk]}, self.people[0].pk, self.encargado, noches=2)
        self.assertEqual(assignment.costo_total, 4 * 2 * 40000)
        costos = sorted(d.costo for d in assignment.detalles.all())
        self.assertEqual(costos, [80000, 240000])
        self.assertEqual(sum(costos), assignment.costo_total)

    def test_fechas_quedan_registradas(self):
        inicio, termino = estadia(noches=5)
        assignment = self.uno(fecha_inicio=inicio, fecha_termino=termino)
        assignment.refresh_from_db()
        self.assertEqual((assignment.fecha_inicio, assignment.fecha_termino), (inicio, termino))

    def test_fechas_obligatorias_en_servicio(self):
        hoy = timezone.localdate()
        for inicio, termino in ((None, hoy + timedelta(days=1)), (hoy, None), ("2030-01-01", "2030-01-02")):
            with self.subTest(inicio=inicio, termino=termino):
                with self.assertRaises(ValidationError):
                    services.crear_asignacion({self.room1.pk: [self.people[0].pk]}, self.people[0].pk, self.encargado, inicio, termino)
        self.assertFalse(Asignacion.objects.exists())

    def test_termino_igual_o_anterior_al_inicio_se_rechaza(self):
        hoy = timezone.localdate()
        for termino in (hoy, hoy - timedelta(days=1)):
            with self.assertRaises(ValidationError):
                self.uno(fecha_inicio=hoy, fecha_termino=termino)
        self.assertFalse(Asignacion.objects.exists())

    def test_inicio_anterior_a_hoy_se_rechaza(self):
        ayer = timezone.localdate() - timedelta(days=1)
        with self.assertRaises(ValidationError):
            self.uno(fecha_inicio=ayer, fecha_termino=ayer + timedelta(days=2))

    def test_estadia_excesiva_se_rechaza(self):
        hoy = timezone.localdate()
        with self.assertRaises(ValidationError):
            self.uno(fecha_inicio=hoy, fecha_termino=hoy + timedelta(days=366))

    def test_vista_previa_calcula_noches_y_costo_sin_efectos(self):
        quote = validar_asignacion({self.room2.pk: [self.people[0].pk, self.people[1].pk]}, self.people[0].pk, self.encargado, noches=3)
        self.assertEqual((quote["noches"], quote["costo_total"]), (3, 240000))
        self.assertFalse(Asignacion.objects.exists())

    def test_fechas_y_costo_son_inmutables(self):
        assignment = self.uno(noches=2)
        assignment.fecha_termino = assignment.fecha_termino + timedelta(days=5)
        with self.assertRaises(ValidationError):
            assignment.save()
        with self.assertRaises(ValidationError):
            Asignacion.objects.filter(pk=assignment.pk).update(fecha_inicio=timezone.localdate() + timedelta(days=1))
        assignment.refresh_from_db()
        self.assertEqual(assignment.noches, 2)
        self.assertEqual(assignment.costo_total, 80000)

    def test_base_de_datos_exige_al_menos_una_noche(self):
        hoy = timezone.localdate()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Asignacion.objects.create(responsable=self.people[0], responsable_nombre="X", responsable_rut=self.people[0].rut,
                                      registrada_por=self.encargado, fecha_inicio=hoy, fecha_termino=hoy, costo_total=40000)

    def test_salida_anticipada_conserva_el_costo_acordado(self):
        assignment = self.uno(noches=3)
        services.liberar_asignacion(assignment.pk, self.encargado)
        assignment.refresh_from_db()
        self.assertEqual(assignment.estado, Asignacion.Estado.FINALIZADA)
        self.assertEqual(assignment.costo_total, 120000)


class EstadiaHttpTests(HotelTestCase):
    def setUp(self):
        self.client.force_login(self.encargado)

    def datos(self, noches=2, **extra):
        inicio, termino = estadia(noches)
        base = {"rooms": [str(self.room1.pk)], f"pasajeros_{self.room1.pk}": [str(self.people[0].pk)], "responsable": str(self.people[0].pk),
                "fecha_inicio": inicio.isoformat(), "fecha_termino": termino.isoformat()}
        base.update(extra)
        return base

    def test_flujo_completo_dos_noches(self):
        data = self.datos(noches=2)
        preview = self.client.post(url("asignacion_crear"), {**data, "action": "preview"})
        self.assertEqual(preview.context["preview"]["noches"], 2)
        self.assertEqual(preview.context["preview"]["costo_total"], 80000)
        self.assertContains(preview, "$80.000")
        response = self.client.post(url("asignacion_crear"), {**data, "action": "confirm", "preview_token": preview.context["preview_token"]})
        assignment = Asignacion.objects.get()
        self.assertRedirects(response, url("asignacion_detalle", assignment.pk))
        self.assertEqual(assignment.costo_total, 80000)
        detail = self.client.get(url("asignacion_detalle", assignment.pk))
        self.assertContains(detail, "2\n        noches")
        self.assertContains(detail, "$80.000")

    def test_fechas_obligatorias_en_formulario(self):
        for campo in ("fecha_inicio", "fecha_termino"):
            with self.subTest(campo=campo):
                data = self.datos()
                data.pop(campo)
                response = self.client.post(url("asignacion_crear"), {**data, "action": "preview"})
                self.assertTrue(response.context["form"].errors.get(campo))
                self.assertIsNone(response.context["preview"])
        self.assertFalse(Asignacion.objects.exists())

    def test_fechas_invalidas_se_rechazan(self):
        hoy = timezone.localdate()
        casos = (
            {"fecha_inicio": "no-es-fecha"},
            {"fecha_termino": "2026-02-31"},
            {"fecha_inicio": hoy.isoformat(), "fecha_termino": hoy.isoformat()},
            {"fecha_inicio": (hoy - timedelta(days=1)).isoformat()},
            {"fecha_termino": (hoy + timedelta(days=400)).isoformat()},
        )
        for extra in casos:
            with self.subTest(extra=extra):
                response = self.client.post(url("asignacion_crear"), {**self.datos(**extra), "action": "preview"})
                self.assertTrue(response.context["form"].errors)
                self.assertIsNone(response.context["preview"])

    def test_cambiar_fechas_despues_de_la_vista_previa_invalida_la_confirmacion(self):
        data = self.datos(noches=1)
        preview = self.client.post(url("asignacion_crear"), {**data, "action": "preview"})
        alterado = self.datos(noches=1)
        alterado["fecha_termino"] = (timezone.localdate() + timedelta(days=10)).isoformat()
        response = self.client.post(url("asignacion_crear"), {**alterado, "action": "confirm", "preview_token": preview.context["preview_token"]})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Asignacion.objects.exists())

    def test_costo_enviado_por_el_cliente_se_ignora(self):
        data = self.datos(noches=2)
        preview = self.client.post(url("asignacion_crear"), {**data, "action": "preview", "costo_total": 1, "noches": 1})
        self.client.post(url("asignacion_crear"), {**data, "action": "confirm", "preview_token": preview.context["preview_token"], "costo_total": 1, "noches": 1})
        self.assertEqual(Asignacion.objects.get().costo_total, 80000)


class CapacidadParcialTests(HotelTestCase):
    def test_una_persona_en_habitacion_de_tres(self):
        assignment = crear_asignacion({self.room3.pk: [self.people[0].pk]}, self.people[0].pk, self.encargado)
        self.assertEqual(assignment.cantidad_pasajeros, 1)
        self.assertEqual(assignment.costo_total, 40000)
        self.room3.refresh_from_db()
        self.assertEqual(self.room3.estado, Habitacion.Estado.OCUPADA)

    def test_capacidad_completa_sigue_permitida(self):
        assignment = crear_asignacion({self.room3.pk: [p.pk for p in self.people[:3]]}, self.people[0].pk, self.encargado)
        self.assertEqual(assignment.cantidad_pasajeros, 3)

    def test_superar_la_capacidad_se_rechaza(self):
        with self.assertRaises(ValidationError):
            crear_asignacion({self.room2.pk: [p.pk for p in self.people[:3]]}, self.people[0].pk, self.encargado)
        self.assertFalse(Hospedaje.objects.exists())

    def test_habitacion_sin_pasajeros_se_rechaza(self):
        with self.assertRaises(ValidationError):
            crear_asignacion({self.room2.pk: []}, self.people[0].pk, self.encargado)

    def test_habitacion_parcial_queda_ocupada_y_no_admite_otra_asignacion(self):
        crear_asignacion({self.room3.pk: [self.people[0].pk]}, self.people[0].pk, self.encargado)
        with self.assertRaises(ValidationError):
            crear_asignacion({self.room3.pk: [self.people[1].pk]}, self.people[1].pk, self.encargado)

    def test_costo_del_historial_usa_pasajeros_reales_y_no_la_capacidad(self):
        assignment = crear_asignacion({self.room3.pk: [self.people[0].pk]}, self.people[0].pk, self.encargado, noches=2)
        self.assertEqual(assignment.detalles.get().costo, 80000)

    def test_formulario_http_acepta_ocupacion_parcial_y_rechaza_exceso(self):
        self.client.force_login(self.encargado)
        inicio, termino = estadia()
        base = {"rooms": [str(self.room2.pk)], "responsable": str(self.people[0].pk), "fecha_inicio": inicio.isoformat(), "fecha_termino": termino.isoformat(), "action": "preview"}
        parcial = self.client.post(url("asignacion_crear"), {**base, f"pasajeros_{self.room2.pk}": [str(self.people[0].pk)]})
        self.assertEqual(parcial.context["preview"]["cantidad"], 1)
        exceso = self.client.post(url("asignacion_crear"), {**base, f"pasajeros_{self.room2.pk}": [str(p.pk) for p in self.people[:3]]})
        self.assertIsNone(exceso.context["preview"])
        self.assertTrue(exceso.context["form"].errors)


class FormatoFechaEstadiaTests(HotelTestCase):
    """Las fechas se escriben a mano como dd/mm/aaaa."""

    def setUp(self):
        self.client.force_login(self.encargado)

    def datos(self, inicio, termino):
        return {
            "rooms": [str(self.room1.pk)],
            f"pasajeros_{self.room1.pk}": [str(self.people[0].pk)],
            "responsable": str(self.people[0].pk),
            "fecha_inicio": inicio,
            "fecha_termino": termino,
            "action": "preview",
        }

    def test_formulario_muestra_campos_de_texto_dd_mm_aaaa(self):
        response = self.client.get(url("asignacion_crear"))
        hoy = timezone.localdate().strftime("%d/%m/%Y")
        self.assertContains(response, 'id="id_fecha_inicio"')
        self.assertContains(response, f'value="{hoy}"')
        self.assertContains(response, 'placeholder="dd/mm/aaaa"')
        self.assertNotContains(response, 'type="date"')

    def test_acepta_fechas_escritas_dd_mm_aaaa(self):
        inicio, termino = estadia(2)
        response = self.client.post(
            url("asignacion_crear"),
            self.datos(inicio.strftime("%d/%m/%Y"), termino.strftime("%d/%m/%Y")),
        )
        self.assertFalse(response.context["form"].errors)
        self.assertEqual(response.context["preview"]["noches"], 2)
        self.assertEqual(response.context["preview"]["costo_total"], 80000)

    def test_rechaza_fecha_inexistente_o_incompleta(self):
        inicio, _ = estadia(1)
        for malo in ("31/02/2027", "1/1/27", "12/2026", "ab/cd/efgh"):
            with self.subTest(malo=malo):
                response = self.client.post(
                    url("asignacion_crear"),
                    self.datos(inicio.strftime("%d/%m/%Y"), malo),
                )
                self.assertTrue(response.context["form"].errors.get("fecha_termino"))
                self.assertIsNone(response.context["preview"])
