"""
Correcciones finales de la Evaluación U4.

1. Habitaciones: desactivación y reactivación reversibles, con historial intacto.
2. Pasajeros: nombre y RUT intocables con hospedaje activo (cualquier ruta).
3. Fechas y ocupación: estados de fecha visibles (inicio programado / vencida).
4. Boleta: vista y tarifa congeladas al contratar.
5. Formularios: la capacidad es un máximo (1 a capacidad), no un valor exacto.
"""
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.db.models import QuerySet
from django.test import TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from hotel import services
from hotel.models import Asignacion, Habitacion, Movimiento, Pasajero

from .base import HotelTestCase, crear_asignacion, estadia, rut_for


def url(name, *args):
    return reverse(f"hotel:{name}", args=args)


def forzar(modelo, pk, **campos):
    """Simula datos antiguos escribiendo por debajo de la protección del historial."""
    return QuerySet.update(modelo._base_manager.filter(pk=pk), **campos)


# --------------------------------------------------------------------------
# 1. Habitaciones: desactivar / reactivar
# --------------------------------------------------------------------------
class ReactivacionDeHabitacionesTests(HotelTestCase):
    def desactivar(self, room):
        services.eliminar_habitacion(room.pk, self.encargado)
        room.refresh_from_db()

    def test_reactivar_devuelve_la_habitacion_activa_y_vacante(self):
        self.desactivar(self.room1)
        self.assertFalse(self.room1.activa)
        services.reactivar_habitacion(self.room1.pk, self.encargado)
        self.room1.refresh_from_db()
        self.assertTrue(self.room1.activa)
        self.assertEqual(self.room1.estado, Habitacion.Estado.VACANTE)

    def test_reactivar_registra_movimiento(self):
        self.desactivar(self.room1)
        services.reactivar_habitacion(self.room1.pk, self.encargado)
        movimiento = Movimiento.objects.filter(accion="HABITACION_REACTIVADA").latest("fecha")
        self.assertIn("101", movimiento.descripcion)
        self.assertEqual(movimiento.usuario, self.encargado)

    def test_reactivar_una_habitacion_activa_se_rechaza(self):
        with self.assertRaises(ValidationError):
            services.reactivar_habitacion(self.room1.pk, self.encargado)

    def test_reactivar_habitacion_inexistente(self):
        with self.assertRaises(ValidationError):
            services.reactivar_habitacion(99999, self.encargado)

    def test_reactivar_conserva_el_historial_de_estadias(self):
        persona = self.people[0]
        asignacion = crear_asignacion({self.room1.pk: [persona.pk]}, persona.pk, self.encargado)
        services.liberar_asignacion(asignacion.pk, self.encargado)
        self.desactivar(self.room1)
        services.reactivar_habitacion(self.room1.pk, self.encargado)
        self.assertEqual(self.room1.detalles.count(), 1)
        detalle = self.room1.detalles.get()
        self.assertEqual(detalle.numero_snapshot, "101")
        self.assertEqual(detalle.asignacion_id, asignacion.pk)

    def test_reactivada_vuelve_a_poder_asignarse(self):
        self.desactivar(self.room1)
        with self.assertRaises(ValidationError):
            crear_asignacion({self.room1.pk: [self.people[0].pk]}, self.people[0].pk, self.encargado)
        services.reactivar_habitacion(self.room1.pk, self.encargado)
        crear_asignacion({self.room1.pk: [self.people[0].pk]}, self.people[0].pk, self.encargado)

    def test_no_se_desactiva_una_habitacion_ocupada(self):
        crear_asignacion({self.room1.pk: [self.people[0].pk]}, self.people[0].pk, self.encargado)
        with self.assertRaises(ValidationError):
            services.eliminar_habitacion(self.room1.pk, self.encargado)
        self.room1.refresh_from_db()
        self.assertTrue(self.room1.activa)

    def test_desactivar_dos_veces_se_rechaza(self):
        self.desactivar(self.room1)
        with self.assertRaises(ValidationError):
            services.eliminar_habitacion(self.room1.pk, self.encargado)

    def test_vista_reactivar_funciona_por_post(self):
        self.desactivar(self.room1)
        self.client.force_login(self.encargado)
        response = self.client.post(url("habitacion_reactivar", self.room1.pk), follow=True)
        self.assertContains(response, "reactivada")
        self.room1.refresh_from_db()
        self.assertTrue(self.room1.activa)

    def test_vista_reactivar_no_admite_get(self):
        self.desactivar(self.room1)
        self.client.force_login(self.encargado)
        self.assertEqual(self.client.get(url("habitacion_reactivar", self.room1.pk)).status_code, 405)
        self.room1.refresh_from_db()
        self.assertFalse(self.room1.activa)

    def test_vista_reactivar_exige_sesion_y_rol_encargado(self):
        self.desactivar(self.room1)
        anonimo = self.client.post(url("habitacion_reactivar", self.room1.pk))
        self.assertEqual(anonimo.status_code, 302)
        self.client.force_login(self.admin_user)
        admin = self.client.post(url("habitacion_reactivar", self.room1.pk))
        self.assertIn(admin.status_code, (302, 403))
        self.room1.refresh_from_db()
        self.assertFalse(self.room1.activa)

    def test_vista_reactivar_exige_csrf(self):
        from django.test import Client
        self.desactivar(self.room1)
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.encargado)
        response = cliente.post(url("habitacion_reactivar", self.room1.pk))
        self.assertEqual(response.status_code, 403)
        self.room1.refresh_from_db()
        self.assertFalse(self.room1.activa)

    def test_vista_reactivar_inexistente_da_404(self):
        self.client.force_login(self.encargado)
        self.assertEqual(self.client.post(url("habitacion_reactivar", 99999)).status_code, 404)

    def test_listado_ofrece_reactivar_solo_en_inactivas_con_confirmacion(self):
        self.desactivar(self.room1)
        self.client.force_login(self.encargado)
        inactivas = self.client.get(url("habitacion_list"), {"activa": "inactivas"})
        self.assertContains(inactivas, url("habitacion_reactivar", self.room1.pk))
        self.assertContains(inactivas, "Reactivar habitación 101")
        self.assertContains(inactivas, "data-confirm=")
        activas = self.client.get(url("habitacion_list"))
        self.assertNotContains(activas, url("habitacion_reactivar", self.room1.pk))

    def test_formulario_no_permite_reactivar_por_post_manipulado(self):
        """El campo `activa` no es editable: editar una inactiva no la reactiva."""
        self.desactivar(self.room1)
        self.client.force_login(self.encargado)
        self.client.post(url("habitacion_editar", self.room1.pk), {
            "numero": "101", "capacidad": "1", "orientacion": "NORTE", "vista": "CIUDAD", "activa": "on",
        })
        self.room1.refresh_from_db()
        self.assertFalse(self.room1.activa)


# --------------------------------------------------------------------------
# 1b. Filtro por vista en el listado de habitaciones
# --------------------------------------------------------------------------
class FiltroPorVistaTests(HotelTestCase):
    def setUp(self):
        Habitacion.objects.filter(pk=self.room1.pk).update(vista="MAR")
        Habitacion.objects.filter(pk__in=[self.room2.pk, self.room3.pk]).update(vista="CIUDAD")
        self.client.force_login(self.encargado)

    def numeros(self, **params):
        response = self.client.get(url("habitacion_list"), params)
        return [h.numero for h in response.context["habitaciones"]]

    def test_filtra_vista_al_mar(self):
        self.assertEqual(self.numeros(vista="MAR"), ["101"])

    def test_filtra_vista_a_la_ciudad(self):
        self.assertEqual(self.numeros(vista="CIUDAD"), ["102", "103"])

    def test_sin_filtro_muestra_todas(self):
        self.assertEqual(self.numeros(), ["101", "102", "103"])

    def test_valor_manipulado_se_ignora_sin_error(self):
        for raro in ("OTRA", "' OR 1=1 --", "<script>", "x" * 500):
            with self.subTest(vista=raro[:20]):
                response = self.client.get(url("habitacion_list"), {"vista": raro})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(len(response.context["habitaciones"]), 3)

    def test_se_combina_con_otros_filtros(self):
        self.assertEqual(self.numeros(vista="CIUDAD", capacidad="3"), ["103"])
        self.assertEqual(self.numeros(vista="MAR", capacidad="3"), [])

    def test_el_selector_aparece_en_la_interfaz(self):
        response = self.client.get(url("habitacion_list"), {"vista": "MAR"})
        self.assertContains(response, 'name="vista"')
        self.assertContains(response, "Todas las vistas")


# --------------------------------------------------------------------------
# 2. Edición segura de pasajeros
# --------------------------------------------------------------------------
class EdicionSeguraDePasajerosTests(HotelTestCase):
    def setUp(self):
        self.huesped = self.people[0]
        self.libre = self.people[5]
        crear_asignacion({self.room1.pk: [self.huesped.pk]}, self.huesped.pk, self.encargado)
        self.client.force_login(self.encargado)

    def post_editar(self, persona, **cambios):
        datos = {
            "rut": persona.rut, "nombre_completo": persona.nombre_completo,
            "telefono": persona.telefono, "correo": persona.correo,
        }
        datos.update(cambios)
        return self.client.post(url("pasajero_editar", persona.pk), datos)

    def test_post_manipulado_no_cambia_nombre_ni_rut_de_hospedado(self):
        nombre, rut = self.huesped.nombre_completo, self.huesped.rut
        self.post_editar(self.huesped, rut=rut_for(19999999), nombre_completo="Nombre Falso")
        self.huesped.refresh_from_db()
        self.assertEqual((self.huesped.nombre_completo, self.huesped.rut), (nombre, rut))

    def test_post_manipulado_permite_actualizar_telefono_y_correo(self):
        response = self.post_editar(
            self.huesped, nombre_completo="Nombre Falso", rut=rut_for(19999999),
            telefono="+56912345678", correo="nuevo@correo.cl",
        )
        self.assertEqual(response.status_code, 302)
        self.huesped.refresh_from_db()
        self.assertEqual(self.huesped.telefono, "+56912345678")
        self.assertEqual(self.huesped.correo, "nuevo@correo.cl")
        self.assertEqual(self.huesped.nombre_completo, "Pasajero 1")

    def test_formulario_muestra_nombre_y_rut_deshabilitados(self):
        response = self.client.get(url("pasajero_editar", self.huesped.pk))
        form = response.context["form"]
        self.assertTrue(form.fields["rut"].disabled)
        self.assertTrue(form.fields["nombre_completo"].disabled)
        self.assertContains(response, "hospedaje activo")

    def test_pasajero_sin_hospedaje_si_puede_cambiar_nombre_y_rut(self):
        nuevo_rut = rut_for(18888888)
        response = self.post_editar(self.libre, rut=nuevo_rut, nombre_completo="Nombre Nuevo")
        self.assertEqual(response.status_code, 302)
        self.libre.refresh_from_db()
        self.assertEqual(self.libre.nombre_completo, "Nombre Nuevo")
        self.assertEqual(self.libre.rut, nuevo_rut)

    def test_modelo_rechaza_cambio_de_identidad_desde_cualquier_ruta(self):
        """Defensa de integridad independiente del formulario (servicios, consola)."""
        self.huesped.nombre_completo = "Otro Nombre"
        with self.assertRaises(ValidationError):
            self.huesped.save()
        self.huesped.refresh_from_db()
        self.huesped.rut = rut_for(17777777)
        with self.assertRaises(ValidationError):
            self.huesped.save()

    def test_modelo_permite_cambiar_contacto_del_hospedado(self):
        self.huesped.telefono = "+56911112222"
        self.huesped.save()
        self.huesped.refresh_from_db()
        self.assertEqual(self.huesped.telefono, "+56911112222")

    def test_tras_la_salida_se_puede_corregir_el_nombre(self):
        asignacion = Asignacion.objects.get(responsable=self.huesped)
        services.liberar_asignacion(asignacion.pk, self.encargado)
        response = self.post_editar(self.huesped, nombre_completo="Nombre Corregido")
        self.assertEqual(response.status_code, 302)
        self.huesped.refresh_from_db()
        self.assertEqual(self.huesped.nombre_completo, "Nombre Corregido")

    def test_historial_conserva_nombre_y_rut_originales_tras_corregir(self):
        asignacion = Asignacion.objects.get(responsable=self.huesped)
        rut_original = self.huesped.rut
        services.liberar_asignacion(asignacion.pk, self.encargado)
        self.post_editar(self.huesped, nombre_completo="Nombre Corregido", rut=rut_for(16666666))
        hospedaje = asignacion.detalles.get().hospedajes.get()
        self.assertEqual(hospedaje.nombre_snapshot, "Pasajero 1")
        self.assertEqual(hospedaje.rut_snapshot, rut_original)
        asignacion.refresh_from_db()
        self.assertEqual(asignacion.responsable_nombre, "Pasajero 1")
        self.assertEqual(asignacion.responsable_rut, rut_original)

    def test_ruta_de_pasajeros_asignados_tampoco_cambia_identidad(self):
        self.assertTrue(self.huesped.hospedajes.filter(activa=True).exists())
        self.client.post(url("pasajero_asignado_editar", self.huesped.pk), {
            "telefono": "+56933334444", "correo": "a@b.cl",
            "nombre_completo": "Intruso", "rut": rut_for(15555555),
        })
        self.huesped.refresh_from_db()
        self.assertEqual(self.huesped.nombre_completo, "Pasajero 1")
        self.assertEqual(self.huesped.telefono, "+56933334444")

    def test_el_resto_de_validaciones_sigue_vigente(self):
        for malo in ("12345", "Juan2"):
            with self.subTest(nombre=malo):
                response = self.post_editar(self.libre, nombre_completo=malo)
                self.assertEqual(response.status_code, 200)
                self.libre.refresh_from_db()
                self.assertEqual(self.libre.nombre_completo, "Pasajero 6")

    def test_rut_duplicado_sigue_rechazado_en_pasajero_libre(self):
        response = self.post_editar(self.libre, rut=self.huesped.rut)
        self.assertEqual(response.status_code, 200)
        self.libre.refresh_from_db()
        self.assertNotEqual(self.libre.rut, self.huesped.rut)


# --------------------------------------------------------------------------
# 3. Fechas y ocupación
# --------------------------------------------------------------------------
class EstadosDeFechaTests(HotelTestCase):
    def crear(self, desde, noches=2, persona=0, room=None):
        room = room or self.room1
        p = self.people[persona]
        inicio = timezone.localdate() + timedelta(days=desde)
        a = services.crear_asignacion({room.pk: [p.pk]}, p.pk, self.encargado, inicio, inicio + timedelta(days=noches))
        return a

    def test_estadia_que_empieza_hoy_no_es_programada_ni_vencida(self):
        a = self.crear(0)
        self.assertFalse(a.inicio_programado)
        self.assertFalse(a.vencida)

    def test_estadia_con_inicio_futuro_se_marca_como_programada(self):
        a = self.crear(5)
        self.assertTrue(a.inicio_programado)
        self.assertFalse(a.vencida)

    def test_estadia_con_termino_pasado_y_sin_salida_se_marca_vencida(self):
        a = self.crear(0, noches=1)
        forzar(Asignacion, a.pk, 
            fecha_inicio=timezone.localdate() - timedelta(days=5),
            fecha_termino=timezone.localdate() - timedelta(days=2),
        )
        a.refresh_from_db()
        self.assertTrue(a.vencida)
        self.assertEqual(services.resumen_ocupacion()["vencidas"], 1)

    def test_estadia_finalizada_nunca_es_vencida_ni_programada(self):
        a = self.crear(0, noches=1)
        services.liberar_asignacion(a.pk, self.encargado)
        forzar(Asignacion, a.pk, 
            fecha_inicio=timezone.localdate() - timedelta(days=5),
            fecha_termino=timezone.localdate() - timedelta(days=2),
        )
        a.refresh_from_db()
        self.assertFalse(a.vencida)
        self.assertFalse(a.inicio_programado)
        self.assertEqual(services.resumen_ocupacion()["vencidas"], 0)

    def test_etiquetas_visibles_en_detalle_listado_y_panel(self):
        vencida = self.crear(0, noches=1, persona=0, room=self.room1)
        forzar(Asignacion, vencida.pk, 
            fecha_inicio=timezone.localdate() - timedelta(days=5),
            fecha_termino=timezone.localdate() - timedelta(days=2),
        )
        programada = self.crear(4, persona=1, room=self.room2)
        self.client.force_login(self.encargado)
        self.assertContains(self.client.get(url("asignacion_detalle", vencida.pk)), "Vencida: registrar salida")
        self.assertContains(self.client.get(url("asignacion_detalle", programada.pk)), "Inicio programado")
        listado = self.client.get(url("asignacion_list"))
        self.assertContains(listado, "Vencida: registrar salida")
        self.assertContains(listado, "Inicio programado")
        self.assertContains(self.client.get(url("dashboard_encargado")), "fecha de término vencida")

    def test_detalle_distingue_contratadas_ingreso_efectivo_y_salida_real(self):
        a = self.crear(0)
        self.client.force_login(self.encargado)
        response = self.client.get(url("asignacion_detalle", a.pk))
        for texto in ("Fechas contratadas", "Ingreso efectivo", "Salida real", "Aún no registrada"):
            self.assertContains(response, texto)
        services.liberar_asignacion(a.pk, self.encargado)
        self.assertNotContains(self.client.get(url("asignacion_detalle", a.pk)), "Aún no registrada")

    def test_una_habitacion_no_admite_dos_estadias_activas_superpuestas(self):
        self.crear(0, noches=3, persona=0, room=self.room2)
        with self.assertRaises(ValidationError):
            self.crear(1, noches=2, persona=1, room=self.room2)

    def test_la_salida_libera_la_habitacion_y_actualiza_ocupacion(self):
        a = self.crear(0)
        self.assertEqual(services.resumen_ocupacion()["ocupadas"], 1)
        services.liberar_asignacion(a.pk, self.encargado)
        resumen = services.resumen_ocupacion()
        self.assertEqual((resumen["ocupadas"], resumen["pasajeros"], resumen["asignaciones"]), (0, 0, 0))

    def test_fechas_pasadas_se_siguen_rechazando(self):
        inicio = timezone.localdate() - timedelta(days=1)
        with self.assertRaises(ValidationError):
            services.crear_asignacion({self.room1.pk: [self.people[0].pk]}, self.people[0].pk, self.encargado,
                                      inicio, inicio + timedelta(days=2))


# --------------------------------------------------------------------------
# 4. Boletas: vista y tarifa congeladas
# --------------------------------------------------------------------------
class IntegridadHistoricaDeBoletasTests(HotelTestCase):
    def setUp(self):
        Habitacion.objects.filter(pk=self.room1.pk).update(vista="MAR")
        grupo = self.people[:3]
        self.asignacion = crear_asignacion(
            {self.room1.pk: [grupo[0].pk], self.room3.pk: [grupo[1].pk, grupo[2].pk]},
            grupo[1].pk, self.encargado, *estadia(3),
        )
        self.client.force_login(self.encargado)

    def boleta(self):
        return self.client.get(url("asignacion_boleta", self.asignacion.pk))

    def test_la_asignacion_guarda_vista_y_tarifa_al_crearse(self):
        detalle = self.asignacion.detalles.get(habitacion=self.room1)
        self.assertEqual(detalle.vista_snapshot, "MAR")
        self.assertEqual(self.asignacion.tarifa_aplicada, 40000)

    def test_cambiar_la_vista_de_la_habitacion_no_altera_la_boleta(self):
        self.assertContains(self.boleta(), "Vista al mar")
        Habitacion.objects.filter(pk=self.room1.pk).update(vista="CIUDAD")
        respuesta = self.boleta()
        self.assertContains(respuesta, "Vista al mar")
        detalle = self.asignacion.detalles.get(habitacion=self.room1)
        self.assertEqual(detalle.vista_display, "Vista al mar")

    def test_editar_la_habitacion_desde_el_formulario_no_altera_la_boleta(self):
        services.liberar_asignacion(self.asignacion.pk, self.encargado)
        self.client.post(url("habitacion_editar", self.room1.pk), {
            "numero": "101", "capacidad": "1", "orientacion": "NORTE", "vista": "CIUDAD",
        })
        self.room1.refresh_from_db()
        self.assertEqual(self.room1.vista, "CIUDAD")
        self.assertContains(self.boleta(), "Vista al mar")

    def test_cambiar_el_numero_de_la_habitacion_no_altera_la_boleta(self):
        services.liberar_asignacion(self.asignacion.pk, self.encargado)
        Habitacion.objects.filter(pk=self.room3.pk).update(numero="909")
        self.assertContains(self.boleta(), "N° 103")
        self.assertNotContains(self.boleta(), "N° 909")

    def test_boleta_usa_la_tarifa_guardada_y_no_la_constante(self):
        """Si la tarifa vigente cambiara en el futuro, las boletas antiguas conservan la suya."""
        forzar(Asignacion, self.asignacion.pk, tarifa_aplicada=30000)
        respuesta = self.boleta()
        self.assertContains(respuesta, "$30.000")
        self.assertNotContains(respuesta, "$40.000")
        # Subtotales de cada habitación con la tarifa guardada.
        self.assertContains(respuesta, "$90.000")   # 101: 1 x 3 x 30.000
        self.assertContains(respuesta, "$180.000")  # 103: 2 x 3 x 30.000

    def test_tarifa_y_vista_son_inmutables(self):
        self.asignacion.tarifa_aplicada = 1
        with self.assertRaises(ValidationError):
            self.asignacion.save()
        detalle = self.asignacion.detalles.get(habitacion=self.room1)
        detalle.vista_snapshot = "CIUDAD"
        with self.assertRaises(ValidationError):
            detalle.save()

    def test_total_subtotales_noches_y_pasajeros_son_correctos(self):
        respuesta = self.boleta()
        self.assertEqual(self.asignacion.noches, 3)
        self.assertEqual(self.asignacion.cantidad_pasajeros, 3)
        self.assertEqual(self.asignacion.costo_total, 3 * 3 * 40000)
        subtotales = sum(d.costo for d in self.asignacion.detalles.all())
        self.assertEqual(subtotales, self.asignacion.costo_total)
        self.assertContains(respuesta, "$360.000")

    def test_detalle_de_la_asignacion_muestra_la_tarifa_guardada(self):
        forzar(Asignacion, self.asignacion.pk, tarifa_aplicada=30000)
        respuesta = self.client.get(url("asignacion_detalle", self.asignacion.pk))
        self.assertContains(respuesta, "$30.000")

    def test_nuevas_asignaciones_siguen_cobrando_40000(self):
        persona = self.people[5]
        a = crear_asignacion({self.room2.pk: [persona.pk]}, persona.pk, self.encargado, *estadia(2))
        self.assertEqual(a.tarifa_aplicada, 40000)
        self.assertEqual(a.costo_total, 80000)

    def test_historial_de_habitacion_y_ocupacion_usan_la_vista_guardada(self):
        Habitacion.objects.filter(pk=self.room1.pk).update(vista="CIUDAD")
        historial = self.client.get(url("habitacion_historial", self.room1.pk))
        self.assertContains(historial, "Vista al mar")
        self.assertContains(self.client.get(url("ocupacion")), "Vista al mar")


class CompatibilidadConAsignacionesAnterioresTests(TransactionTestCase):
    """Migración real 0004 -> 0005 con datos creados antes de congelar vista y tarifa."""

    ANTES = [("hotel", "0004_estadia_fechas_y_numero_numerico")]
    DESPUES = [("hotel", "0005_congelar_vista_y_tarifa")]

    def test_asignaciones_anteriores_quedan_con_tarifa_y_vista(self):
        executor = MigrationExecutor(connection)
        executor.migrate(self.ANTES)
        if True:
            viejo = executor.loader.project_state(self.ANTES).apps
            Usuario = viejo.get_model("hotel", "Usuario")
            Habitacion_ = viejo.get_model("hotel", "Habitacion")
            Pasajero_ = viejo.get_model("hotel", "Pasajero")
            Asignacion_ = viejo.get_model("hotel", "Asignacion")
            Detalle_ = viejo.get_model("hotel", "DetalleHabitacionAsignada")

            usuario = Usuario.objects.create(username="enc_migracion", rol="ENCARGADO")
            mar = Habitacion_.objects.create(numero="701", capacidad=2, orientacion="NORTE", vista="MAR")
            persona = Pasajero_.objects.create(rut=rut_for(13000001), nombre_completo="Persona Antigua")
            hoy = timezone.localdate()
            asignacion = Asignacion_.objects.create(
                responsable=persona, responsable_nombre="Persona Antigua", responsable_rut=persona.rut,
                registrada_por=usuario, fecha_inicio=hoy, fecha_termino=hoy + timedelta(days=2),
                costo_total=80000,
            )
            detalle = Detalle_.objects.create(
                asignacion=asignacion, habitacion=mar, numero_snapshot="701", capacidad_snapshot=2,
            )

            executor = MigrationExecutor(connection)
            executor.migrate(self.DESPUES)

        nuevo = Asignacion.objects.get(pk=asignacion.pk)
        self.assertEqual(nuevo.tarifa_aplicada, 40000)
        self.assertEqual(nuevo.costo_total, 80000)
        self.assertEqual(nuevo.detalles.get(pk=detalle.pk).vista_snapshot, "MAR")
        self.assertEqual(nuevo.detalles.get().vista_display, "Vista al mar")

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        MigrationExecutor(connection).migrate(
            MigrationExecutor(connection).loader.graph.leaf_nodes()
        )


# --------------------------------------------------------------------------
# 5. Formularios y reglas de negocio
# --------------------------------------------------------------------------
class CapacidadMaximaTests(HotelTestCase):
    def test_formulario_de_habitaciones_ya_no_exige_capacidad_exacta(self):
        self.client.force_login(self.encargado)
        for nombre in ("habitacion_crear",):
            html = self.client.get(url(nombre)).content.decode().lower()
            self.assertNotIn("exactamente", html)
            self.assertNotIn("capacidad exacta", html)
            self.assertIn("capacidad máxima", html)
            self.assertIn("desde 1 pasajero", html)

    def test_ninguna_pantalla_pide_completar_la_capacidad(self):
        self.client.force_login(self.encargado)
        for nombre in ("asignacion_crear", "habitacion_list", "ocupacion", "asignacion_list"):
            html = self.client.get(url(nombre)).content.decode().lower()
            for frase in ("exactamente esta cantidad", "capacidad exacta", "completar la capacidad"):
                self.assertNotIn(frase, html, f"{nombre}: {frase}")

    def test_se_permite_entre_uno_y_la_capacidad_maxima(self):
        for cantidad in (1, 2, 3):
            room = Habitacion.objects.create(numero=str(500 + cantidad), capacidad=3, orientacion="NORTE")
            ids = [Pasajero.objects.create(rut=rut_for(14000000 + cantidad * 10 + i), nombre_completo=f"Huesped {cantidad} {chr(65 + i)}").pk
                   for i in range(cantidad)]
            asignacion = crear_asignacion({room.pk: ids}, ids[0], self.encargado)
            self.assertEqual(asignacion.cantidad_pasajeros, cantidad)
            self.assertEqual(asignacion.costo_total, cantidad * 40000)

    def test_se_rechaza_habitacion_sin_pasajeros(self):
        with self.assertRaises(ValidationError):
            crear_asignacion({self.room2.pk: []}, self.people[0].pk, self.encargado)

    def test_se_rechaza_sobreocupacion(self):
        ids = [p.pk for p in self.people[:3]]
        with self.assertRaises(ValidationError):
            crear_asignacion({self.room2.pk: ids}, ids[0], self.encargado)

    def test_representante_obligatorio_y_del_grupo(self):
        with self.assertRaises(ValidationError):
            crear_asignacion({self.room2.pk: [self.people[0].pk]}, None, self.encargado)
        with self.assertRaises(ValidationError):
            crear_asignacion({self.room2.pk: [self.people[0].pk]}, self.people[6].pk, self.encargado)

    def test_no_hay_duplicidad_de_pasajero_entre_habitaciones(self):
        p = self.people[0]
        with self.assertRaises(ValidationError):
            crear_asignacion({self.room2.pk: [p.pk], self.room3.pk: [p.pk]}, p.pk, self.encargado)

    def test_fallo_de_validacion_no_deja_cambios_parciales(self):
        antes = (Asignacion.objects.count(), Habitacion.objects.filter(estado="OCUPADA").count())
        p = self.people
        with self.assertRaises(ValidationError):
            crear_asignacion({self.room2.pk: [p[0].pk], self.room3.pk: []}, p[0].pk, self.encargado)
        despues = (Asignacion.objects.count(), Habitacion.objects.filter(estado="OCUPADA").count())
        self.assertEqual(antes, despues)
