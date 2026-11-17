"""
Ingreso efectivo (inicio = hoy) y estadías vencidas.

El sistema gestiona ingresos efectivos, no reservas anticipadas: una asignación
nueva solo puede comenzar hoy, de modo que ninguna habitación se marca ocupada
antes de tiempo. Una estadía vencida nunca libera sola la habitación: la salida
la confirma el Encargado.
"""
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.urls import reverse
from django.utils import timezone

from hotel import services
from hotel.models import Asignacion, Habitacion, Movimiento

from .base import HotelTestCase, estadia


def url(name, *args):
    return reverse(f"hotel:{name}", args=args)


def forzar(modelo, pk, **campos):
    return QuerySet.update(modelo._base_manager.filter(pk=pk), **campos)


class InicioSoloHoyTests(HotelTestCase):
    def setUp(self):
        self.hoy = timezone.localdate()

    def distribucion(self):
        return {self.room1.pk: [self.people[0].pk]}

    def intentar(self, inicio, termino):
        return services.crear_asignacion(self.distribucion(), self.people[0].pk, self.encargado, inicio, termino)

    def assert_sin_efectos(self):
        self.assertFalse(Asignacion.objects.exists())
        self.room1.refresh_from_db()
        self.assertEqual(self.room1.estado, Habitacion.Estado.VACANTE)

    # --- servicios -------------------------------------------------------
    def test_servicio_acepta_inicio_igual_a_hoy(self):
        a = self.intentar(self.hoy, self.hoy + timedelta(days=2))
        self.assertEqual(a.fecha_inicio, self.hoy)
        self.assertEqual(a.costo_total, 80000)
        self.room1.refresh_from_db()
        self.assertEqual(self.room1.estado, Habitacion.Estado.OCUPADA)

    def test_servicio_rechaza_inicio_pasado(self):
        ayer = self.hoy - timedelta(days=1)
        with self.assertRaises(ValidationError) as ctx:
            self.intentar(ayer, self.hoy + timedelta(days=1))
        self.assertIn("anterior a hoy", " ".join(ctx.exception.messages))
        self.assert_sin_efectos()

    def test_servicio_rechaza_inicio_futuro_y_no_ocupa_la_habitacion(self):
        for dias in (1, 2, 30, 365):
            with self.subTest(dias=dias):
                inicio = self.hoy + timedelta(days=dias)
                with self.assertRaises(ValidationError) as ctx:
                    self.intentar(inicio, inicio + timedelta(days=2))
                mensaje = " ".join(ctx.exception.messages)
                self.assertIn("posterior a hoy", mensaje)
                self.assertIn("reservas anticipadas", mensaje)
                self.assert_sin_efectos()
        self.assertFalse(Movimiento.objects.filter(accion="ASIGNACION").exists())

    def test_servicio_valida_fecha_de_termino(self):
        for termino in (self.hoy, self.hoy - timedelta(days=1)):
            with self.subTest(termino=termino):
                with self.assertRaises(ValidationError) as ctx:
                    self.intentar(self.hoy, termino)
                self.assertIn("posterior a la fecha de inicio", " ".join(ctx.exception.messages))
        with self.assertRaises(ValidationError):
            self.intentar(self.hoy, None)
        self.assert_sin_efectos()

    def test_se_conserva_el_maximo_de_365_noches(self):
        a = self.intentar(self.hoy, self.hoy + timedelta(days=365))
        self.assertEqual(a.costo_total, 365 * 40000)
        services.liberar_asignacion(a.pk, self.encargado)
        with self.assertRaises(ValidationError) as ctx:
            self.intentar(self.hoy, self.hoy + timedelta(days=366))
        self.assertIn("365", " ".join(ctx.exception.messages))

    def test_la_vista_previa_tambien_rechaza_inicio_futuro(self):
        inicio = self.hoy + timedelta(days=3)
        with self.assertRaises(ValidationError):
            services.validar_asignacion(self.distribucion(), self.people[0].pk, self.encargado, inicio, inicio + timedelta(days=1))

    # --- formulario y vistas (solicitudes manipuladas) ---------------------
    def datos(self, **extra):
        inicio, termino = estadia(2)
        base = {"rooms": [str(self.room1.pk)], f"pasajeros_{self.room1.pk}": [str(self.people[0].pk)],
                "responsable": str(self.people[0].pk), "fecha_inicio": inicio.isoformat(), "fecha_termino": termino.isoformat()}
        base.update(extra)
        return base

    def test_formulario_muestra_mensaje_claro_con_inicio_futuro(self):
        self.client.force_login(self.encargado)
        futuro = self.hoy + timedelta(days=2)
        datos = self.datos(fecha_inicio=futuro.isoformat(), fecha_termino=(futuro + timedelta(days=2)).isoformat())
        response = self.client.post(url("asignacion_crear"), {**datos, "action": "preview"})
        self.assertEqual(response.status_code, 200)
        errores = " ".join(response.context["form"].errors.get("fecha_inicio", []))
        self.assertIn("posterior a hoy", errores)
        self.assertIn(f"{self.hoy:%d/%m/%Y}", errores)
        self.assertIsNone(response.context["preview"])
        self.assertContains(response, "posterior a hoy")

    def test_formulario_rechaza_inicio_pasado_con_mensaje_claro(self):
        self.client.force_login(self.encargado)
        ayer = self.hoy - timedelta(days=1)
        response = self.client.post(url("asignacion_crear"), {**self.datos(fecha_inicio=ayer.isoformat()), "action": "preview"})
        self.assertIn("anterior a hoy", " ".join(response.context["form"].errors["fecha_inicio"]))

    def test_confirmacion_manipulada_con_inicio_futuro_no_crea_nada(self):
        self.client.force_login(self.encargado)
        preview = self.client.post(url("asignacion_crear"), {**self.datos(), "action": "preview"})
        self.assertIsNotNone(preview.context["preview"])
        futuro = self.hoy + timedelta(days=5)
        alterado = self.datos(fecha_inicio=futuro.isoformat(), fecha_termino=(futuro + timedelta(days=2)).isoformat())
        response = self.client.post(url("asignacion_crear"), {**alterado, "action": "confirm", "preview_token": preview.context["preview_token"]})
        self.assertEqual(response.status_code, 200)
        self.assert_sin_efectos()

    def test_confirmacion_directa_sin_vista_previa_con_inicio_futuro_se_rechaza(self):
        self.client.force_login(self.encargado)
        futuro = self.hoy + timedelta(days=1)
        datos = self.datos(fecha_inicio=futuro.isoformat(), fecha_termino=(futuro + timedelta(days=1)).isoformat())
        response = self.client.post(url("asignacion_crear"), {**datos, "action": "confirm", "preview_token": "x"})
        self.assertEqual(response.status_code, 200)
        self.assert_sin_efectos()

    def test_formato_dd_mm_aaaa_con_hoy_se_acepta_en_la_vista_previa(self):
        self.client.force_login(self.encargado)
        inicio, termino = estadia(1)
        datos = self.datos(fecha_inicio=f"{inicio:%d/%m/%Y}", fecha_termino=f"{termino:%d/%m/%Y}")
        response = self.client.post(url("asignacion_crear"), {**datos, "action": "preview"})
        self.assertIsNotNone(response.context["preview"])

    def test_formulario_explica_la_restriccion(self):
        self.client.force_login(self.encargado)
        response = self.client.get(url("asignacion_crear"))
        self.assertContains(response, "ingresos")
        self.assertContains(response, "reservas anticipadas")
        self.assertContains(response, f"{self.hoy:%d/%m/%Y}")

    # --- datos existentes ----------------------------------------------------
    def test_asignacion_historica_con_inicio_futuro_no_se_modifica(self):
        a = self.intentar(self.hoy, self.hoy + timedelta(days=2))
        futuro = self.hoy + timedelta(days=4)
        forzar(Asignacion, a.pk, fecha_inicio=futuro, fecha_termino=futuro + timedelta(days=2))
        self.client.force_login(self.encargado)
        self.assertEqual(self.client.get(url("asignacion_detalle", a.pk)).status_code, 200)
        a.refresh_from_db()
        self.assertEqual(a.fecha_inicio, futuro)
        self.assertTrue(a.inicio_programado)


class EstadiasVencidasTests(HotelTestCase):
    def setUp(self):
        self.hoy = timezone.localdate()
        self.a = services.crear_asignacion({self.room2.pk: [self.people[0].pk, self.people[1].pk]}, self.people[0].pk,
                                           self.encargado, self.hoy, self.hoy + timedelta(days=1))
        self.contratado_inicio = self.a.fecha_inicio

    def vencer(self):
        forzar(Asignacion, self.a.pk, fecha_inicio=self.hoy - timedelta(days=4), fecha_termino=self.hoy - timedelta(days=2))
        self.a.refresh_from_db()

    def test_estadia_vigente_no_esta_vencida(self):
        self.assertFalse(self.a.vencida)
        self.assertEqual(services.resumen_ocupacion()["vencidas"], 0)

    def test_se_detecta_la_estadia_vencida_sin_liberar_la_habitacion(self):
        self.vencer()
        self.assertTrue(self.a.vencida)
        self.client.force_login(self.encargado)
        for nombre in ("dashboard_encargado", "asignacion_list", "ocupacion"):
            self.assertEqual(self.client.get(url(nombre)).status_code, 200)
        self.room2.refresh_from_db()
        self.a.refresh_from_db()
        self.assertEqual(self.room2.estado, Habitacion.Estado.OCUPADA)
        self.assertEqual(self.a.estado, Asignacion.Estado.ACTIVA)
        self.assertIsNone(self.a.fecha_salida)

    def test_avisos_visibles_en_panel_listado_y_detalle(self):
        self.vencer()
        self.client.force_login(self.encargado)
        self.assertContains(self.client.get(url("dashboard_encargado")), "fecha de término vencida")
        self.assertContains(self.client.get(url("asignacion_list")), "Vencida: registrar salida")
        detalle = self.client.get(url("asignacion_detalle", self.a.pk))
        self.assertContains(detalle, "Vencida: registrar salida")
        self.assertContains(detalle, f"{self.a.fecha_termino:%d/%m/%Y}")

    def test_la_habitacion_vencida_sigue_sin_estar_disponible_para_nuevas_asignaciones(self):
        self.vencer()
        with self.assertRaises(ValidationError):
            services.crear_asignacion({self.room2.pk: [self.people[2].pk]}, self.people[2].pk, self.encargado,
                                      self.hoy, self.hoy + timedelta(days=1))

    def test_salida_manual_libera_y_actualiza_indicadores(self):
        self.vencer()
        antes = services.resumen_ocupacion()
        self.assertEqual((antes["vencidas"], antes["ocupadas"]), (1, 1))
        services.liberar_asignacion(self.a.pk, self.encargado)
        self.room2.refresh_from_db()
        self.a.refresh_from_db()
        self.assertEqual(self.room2.estado, Habitacion.Estado.VACANTE)
        self.assertEqual(self.a.estado, Asignacion.Estado.FINALIZADA)
        self.assertEqual(self.a.liberada_por, self.encargado)
        self.assertFalse(self.a.vencida)
        despues = services.resumen_ocupacion()
        self.assertEqual((despues["vencidas"], despues["ocupadas"], despues["asignaciones"]), (0, 0, 0))
        self.client.force_login(self.encargado)
        self.assertNotContains(self.client.get(url("dashboard_encargado")), "fecha de término vencida")

    def test_la_salida_conserva_historial_boleta_y_datos_originales(self):
        self.vencer()
        costo, tarifa = self.a.costo_total, list(self.a.detalles.values_list("numero_snapshot", flat=True))
        services.liberar_asignacion(self.a.pk, self.encargado)
        self.a.refresh_from_db()
        self.assertEqual(self.a.costo_total, costo)
        self.assertEqual(list(self.a.detalles.values_list("numero_snapshot", flat=True)), tarifa)
        self.assertEqual(self.a.detalles.count(), 1)
        self.assertTrue(Movimiento.objects.filter(accion="LIBERACION").exists())
        self.client.force_login(self.encargado)
        self.assertEqual(self.client.get(url("asignacion_boleta", self.a.pk)).status_code, 200)
        self.assertEqual(self.client.get(url("asignacion_detalle", self.a.pk)).status_code, 200)

    def test_no_se_puede_registrar_la_salida_dos_veces(self):
        services.liberar_asignacion(self.a.pk, self.encargado)
        with self.assertRaises(ValidationError):
            services.liberar_asignacion(self.a.pk, self.encargado)
