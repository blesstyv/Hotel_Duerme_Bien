"""
Pruebas de la Evaluación U4 (proyecto final):

- Nombres de personas: no pueden ser solo números.
- Una misma persona no puede estar en dos habitaciones con fechas superpuestas.
- Representante del grupo obligatorio y presente en la boleta.
- Boleta de estadía con pasajeros, noches, tarifa y total.
- Imagen del hotel en la interfaz de inicio.
- Vistas de habitaciones (mar / ciudad).
"""
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from hotel import services
from hotel.models import Asignacion, Habitacion, Pasajero
from hotel.validators import validar_nombre_persona

from .base import PASSWORD, HotelTestCase, crear_asignacion, estadia, rut_for


def url(name, *args):
    return reverse(f"hotel:{name}", args=args)


class NombresDePersonasTests(HotelTestCase):
    def test_validador_rechaza_nombres_solo_numericos_o_simbolos(self):
        for malo in ("12345", "  987 654 ", "0", "---", "...", "!!!", "   ", ""):
            with self.subTest(nombre=malo), self.assertRaises(ValidationError):
                validar_nombre_persona(malo)

    def test_validador_rechaza_digitos_mezclados_con_letras(self):
        for malo in ("Juan2", "Ana 3", "R2D2", "Luis@Perez", "Marta_Soto"):
            with self.subTest(nombre=malo), self.assertRaises(ValidationError):
                validar_nombre_persona(malo)

    def test_validador_acepta_nombres_reales(self):
        for bueno in ("Ana", "María José Pérez", "Nicolás O'Higgins", "Jean-Luc Picard", "Ñandú Ibáñez", "Juan Pérez Jr."):
            with self.subTest(nombre=bueno):
                self.assertEqual(validar_nombre_persona(bueno), " ".join(bueno.split()))

    def test_formulario_pasajero_rechaza_nombre_numerico(self):
        self.client.force_login(self.encargado)
        total = Pasajero.objects.count()
        for malo in ("123456", "000", "$$$"):
            with self.subTest(nombre=malo):
                response = self.client.post(url("pasajero_crear"), {"rut": rut_for(15000001), "nombre_completo": malo})
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context["form"].errors.get("nombre_completo"))
        self.assertEqual(Pasajero.objects.count(), total)

    def test_formulario_pasajero_acepta_nombre_valido(self):
        self.client.force_login(self.encargado)
        response = self.client.post(url("pasajero_crear"), {"rut": rut_for(15000002), "nombre_completo": "  María   José Pérez "})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Pasajero.objects.get(rut=rut_for(15000002)).nombre_completo, "María José Pérez")

    def test_formulario_encargado_rechaza_nombre_numerico(self):
        self.client.force_login(self.admin_user)
        datos = {"username": "nuevo_enc", "first_name": "12345", "last_name": "Soto", "password1": PASSWORD, "password2": PASSWORD}
        response = self.client.post(url("encargado_crear"), datos)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors.get("first_name"))
        datos.update(first_name="Luisa", last_name="999")
        response = self.client.post(url("encargado_crear"), datos)
        self.assertTrue(response.context["form"].errors.get("last_name"))


class EstadiasSuperpuestasTests(HotelTestCase):
    def test_misma_persona_no_puede_estar_en_dos_habitaciones_con_fechas_superpuestas(self):
        persona = self.people[0]
        crear_asignacion({self.room1.pk: [persona.pk]}, persona.pk, self.encargado, *estadia(3))
        inicio, termino = estadia(2, desde=1)  # se superpone con la estadía anterior
        with self.assertRaises(ValidationError) as ctx:
            crear_asignacion({self.room2.pk: [persona.pk]}, persona.pk, self.encargado, inicio, termino)
        mensaje = " ".join(ctx.exception.messages)
        self.assertIn("101", mensaje)
        self.assertIn("se superponen", mensaje)
        self.assertEqual(Asignacion.objects.count(), 1)

    def test_el_mensaje_indica_fechas_de_la_otra_estadia(self):
        persona = self.people[1]
        a = crear_asignacion({self.room1.pk: [persona.pk]}, persona.pk, self.encargado, *estadia(2))
        with self.assertRaises(ValidationError) as ctx:
            crear_asignacion({self.room2.pk: [persona.pk]}, persona.pk, self.encargado, *estadia(1))
        mensaje = " ".join(ctx.exception.messages)
        self.assertIn(f"{a.fecha_inicio:%d/%m/%Y}", mensaje)
        self.assertIn(f"{a.fecha_termino:%d/%m/%Y}", mensaje)

    def test_persona_con_estadia_activa_sigue_bloqueada_sin_superposicion(self):
        persona = self.people[2]
        crear_asignacion({self.room1.pk: [persona.pk]}, persona.pk, self.encargado, *estadia(1))
        inicio, termino = estadia(2, desde=10)  # fechas posteriores, sin superposición
        with self.assertRaises(ValidationError):
            crear_asignacion({self.room2.pk: [persona.pk]}, persona.pk, self.encargado, inicio, termino)

    def test_persona_puede_volver_tras_registrar_la_salida(self):
        persona = self.people[3]
        a = crear_asignacion({self.room1.pk: [persona.pk]}, persona.pk, self.encargado, *estadia(1))
        services.liberar_asignacion(a.pk, self.encargado)
        b = crear_asignacion({self.room2.pk: [persona.pk]}, persona.pk, self.encargado, *estadia(2))
        self.assertEqual(b.costo_total, 80000)

    def test_no_se_repite_una_persona_entre_habitaciones_del_mismo_grupo(self):
        persona = self.people[4]
        with self.assertRaises(ValidationError):
            crear_asignacion({self.room2.pk: [persona.pk], self.room3.pk: [persona.pk]}, persona.pk, self.encargado)


class BoletaEstadiaTests(HotelTestCase):
    def setUp(self):
        grupo = self.people[:3]
        self.asignacion = crear_asignacion(
            {self.room1.pk: [grupo[0].pk], self.room3.pk: [grupo[1].pk, grupo[2].pk]},
            grupo[1].pk, self.encargado, *estadia(3),
        )

    def test_boleta_incluye_toda_la_informacion(self):
        self.client.force_login(self.encargado)
        response = self.client.get(url("asignacion_boleta", self.asignacion.pk))
        self.assertEqual(response.status_code, 200)
        a = self.asignacion
        self.assertContains(response, f"{a.pk:06d}")
        self.assertContains(response, "Pasajero 2")  # representante
        self.assertContains(response, "(representante)")
        self.assertContains(response, f"{a.fecha_inicio:%d/%m/%Y}")
        self.assertContains(response, f"{a.fecha_termino:%d/%m/%Y}")
        self.assertContains(response, "$40.000")
        self.assertContains(response, "$360.000")  # 3 pasajeros x 3 noches x 40.000
        self.assertContains(response, "3 pasajeros")
        self.assertContains(response, "3 noches")
        for nombre in ("Pasajero 1", "Pasajero 2", "Pasajero 3"):
            self.assertContains(response, nombre)
        for numero in ("101", "103"):
            self.assertContains(response, f"N° {numero}")
        self.assertContains(response, "Vista a la ciudad")

    def test_subtotales_por_habitacion_suman_el_total(self):
        self.client.force_login(self.encargado)
        response = self.client.get(url("asignacion_boleta", self.asignacion.pk))
        self.assertContains(response, "$120.000")  # habitación 101: 1 x 3 x 40.000
        self.assertContains(response, "$240.000")  # habitación 103: 2 x 3 x 40.000
        self.assertEqual(self.asignacion.costo_total, 360000)

    def test_boleta_muestra_vista_al_mar(self):
        Habitacion.objects.filter(pk=self.room1.pk).update(vista="MAR")
        self.client.force_login(self.encargado)
        self.assertContains(self.client.get(url("asignacion_boleta", self.asignacion.pk)), "Vista al mar")

    def test_boleta_requiere_sesion(self):
        response = self.client.get(url("asignacion_boleta", self.asignacion.pk))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response["Location"])

    def test_administrador_no_accede_a_la_boleta(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(url("asignacion_boleta", self.asignacion.pk))
        self.assertIn(response.status_code, (302, 403))
        self.assertNotContains(response, "Boleta de estadía", status_code=response.status_code)

    def test_boleta_inexistente_da_404(self):
        self.client.force_login(self.encargado)
        self.assertEqual(self.client.get(url("asignacion_boleta", 99999)).status_code, 404)

    def test_boleta_solo_admite_get(self):
        self.client.force_login(self.encargado)
        self.assertEqual(self.client.post(url("asignacion_boleta", self.asignacion.pk)).status_code, 405)

    def test_enlaces_a_la_boleta_en_detalle_y_listado(self):
        self.client.force_login(self.encargado)
        enlace = url("asignacion_boleta", self.asignacion.pk)
        self.assertContains(self.client.get(url("asignacion_detalle", self.asignacion.pk)), enlace)
        self.assertContains(self.client.get(url("asignacion_list")), enlace)

    def test_boleta_finalizada_conserva_los_datos(self):
        services.liberar_asignacion(self.asignacion.pk, self.encargado)
        self.client.force_login(self.encargado)
        response = self.client.get(url("asignacion_boleta", self.asignacion.pk))
        self.assertContains(response, "$360.000")
        self.assertContains(response, "Finalizada")


class ImagenDelHotelTests(HotelTestCase):
    def test_login_muestra_la_imagen_del_hotel(self):
        response = self.client.get(url("login"))
        self.assertContains(response, "hotel_fachada")
        self.assertContains(response, "Fachada del Hotel Duerme Bien")

    def test_panel_del_encargado_muestra_la_imagen_del_hotel(self):
        self.client.force_login(self.encargado)
        self.assertContains(self.client.get(url("inicio"), follow=True), "hotel_fachada")

    def test_panel_del_administrador_muestra_la_imagen_del_hotel(self):
        self.client.force_login(self.admin_user)
        self.assertContains(self.client.get(url("inicio"), follow=True), "hotel_fachada")


class RepresentanteDelGrupoTests(HotelTestCase):
    def test_formulario_usa_el_termino_representante(self):
        self.client.force_login(self.encargado)
        self.assertContains(self.client.get(url("asignacion_crear")), "Representante")

    def test_el_representante_debe_pertenecer_al_grupo(self):
        with self.assertRaises(ValidationError):
            crear_asignacion({self.room1.pk: [self.people[0].pk]}, self.people[5].pk, self.encargado)

    def test_el_representante_es_obligatorio(self):
        with self.assertRaises(ValidationError):
            crear_asignacion({self.room1.pk: [self.people[0].pk]}, None, self.encargado)


class NumeroHabitacionCasosLimiteTests(HotelTestCase):
    """Solo números naturales positivos: se prueban entradas hostiles."""

    def test_rechaza_entradas_que_no_son_naturales_positivos(self):
        from hotel.validators import validar_numero_habitacion
        for malo in ("0", "00", "01", "-5", "+5", "1.5", "1,5", "1e3", "12A", "A12", "1 2", "10-1",
                     "١٢٣", "１２３", "²", "½", "123456", "", " ", "12 ", " 12", "12\n", "0x1F", "1_0"):
            with self.subTest(numero=repr(malo)), self.assertRaises(ValidationError):
                validar_numero_habitacion(malo)

    def test_acepta_naturales_positivos(self):
        from hotel.validators import validar_numero_habitacion
        for bueno in ("1", "7", "101", "999", "12345"):
            with self.subTest(numero=bueno):
                validar_numero_habitacion(bueno)

    def test_el_formulario_normaliza_espacios_y_rechaza_letras(self):
        from hotel.forms import HabitacionForm
        datos = {"capacidad": "2", "orientacion": "NORTE", "vista": "MAR"}
        form = HabitacionForm(data={**datos, "numero": "  205  "})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["numero"], "205")
        for malo in ("20A", "٢٠٥", "0205", "2 05"):
            with self.subTest(numero=malo):
                self.assertFalse(HabitacionForm(data={**datos, "numero": malo}).is_valid())

    def test_editar_una_habitacion_tampoco_permite_letras(self):
        self.client.force_login(self.encargado)
        response = self.client.post(
            url("habitacion_editar", self.room2.pk),
            {"numero": "10B", "capacidad": "2", "orientacion": "SUR", "vista": "MAR"},
        )
        self.assertEqual(response.status_code, 200)
        self.room2.refresh_from_db()
        self.assertEqual(self.room2.numero, "102")


class FlujoHttpGrupoGrandeTests(HotelTestCase):
    def setUp(self):
        self.client.force_login(self.encargado)

    def datos(self, rooms_people, representante, inicio, termino, action="preview", extra=None):
        data = {"rooms": [str(r.pk) for r, _ in rooms_people], "responsable": str(representante.pk),
                "fecha_inicio": inicio.strftime("%d/%m/%Y"), "fecha_termino": termino.strftime("%d/%m/%Y"),
                "action": action}
        for room, people in rooms_people:
            data[f"pasajeros_{room.pk}"] = [str(p.pk) for p in people]
        if extra:
            data.update(extra)
        return data

    def test_grupo_grande_en_varias_habitaciones_con_representante_y_boleta(self):
        p = self.people
        inicio, termino = estadia(4)
        distribucion = [(self.room3, p[0:3]), (self.room2, p[3:5])]  # 5 personas, habitaciones sin llenar la capacidad exacta
        data = self.datos(distribucion, p[3], inicio, termino)
        preview = self.client.post(url("asignacion_crear"), data)
        self.assertEqual(preview.context["preview"]["costo_total"], 5 * 4 * 40000)
        confirm = self.client.post(url("asignacion_crear"), {**data, "action": "confirm", "preview_token": preview.context["preview_token"]})
        asignacion = Asignacion.objects.get()
        self.assertRedirects(confirm, url("asignacion_detalle", asignacion.pk))
        self.assertEqual(asignacion.responsable_id, p[3].pk)
        self.assertEqual(asignacion.costo_total, 800000)
        boleta = self.client.get(url("asignacion_boleta", asignacion.pk))
        self.assertContains(boleta, "$800.000")
        self.assertContains(boleta, "5 pasajeros")
        self.assertContains(boleta, "4 noches")
        self.assertContains(boleta, "(representante)")
        self.assertContains(boleta, "Boleta emitida el")

    def test_un_pasajero_de_otro_grupo_no_puede_ser_representante(self):
        p = self.people
        inicio, termino = estadia(2)
        data = self.datos([(self.room2, p[0:2])], p[5], inicio, termino)
        response = self.client.post(url("asignacion_crear"), data)
        self.assertFalse(Asignacion.objects.exists())
        self.assertIsNone(response.context["preview"])

    def test_intento_manipulado_de_hospedar_a_una_persona_en_dos_habitaciones(self):
        p = self.people
        crear_asignacion({self.room1.pk: [p[0].pk]}, p[0].pk, self.encargado, *estadia(3))
        inicio, termino = estadia(2, desde=1)
        data = self.datos([(self.room2, [p[0], p[1]])], p[1], inicio, termino)  # se fuerza el POST con una persona ya hospedada
        response = self.client.post(url("asignacion_crear"), data)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["preview"])
        self.assertEqual(Asignacion.objects.count(), 1)
        self.assertContains(response, "no estén hospedados")  # lo bloquea ya el formulario; el servicio lo vuelve a validar


class VistaVisibleEnElSistemaTests(HotelTestCase):
    def test_vista_aparece_en_ocupacion_detalle_y_boleta(self):
        Habitacion.objects.filter(pk=self.room1.pk).update(vista="MAR")
        persona = self.people[0]
        a = crear_asignacion({self.room1.pk: [persona.pk]}, persona.pk, self.encargado)
        self.client.force_login(self.encargado)
        self.assertContains(self.client.get(url("ocupacion")), "Vista al mar")
        self.assertContains(self.client.get(url("asignacion_detalle", a.pk)), "Vista al mar")
        self.assertContains(self.client.get(url("asignacion_boleta", a.pk)), "Vista al mar")
        self.assertContains(self.client.get(url("habitacion_list")), "Vista a la ciudad")

    def test_se_puede_crear_una_habitacion_con_cada_vista(self):
        self.client.force_login(self.encargado)
        for numero, vista in (("301", "MAR"), ("302", "CIUDAD")):
            self.client.post(url("habitacion_crear"), {"numero": numero, "capacidad": "2", "orientacion": "NORTE", "vista": vista})
            self.assertEqual(Habitacion.objects.get(numero=numero).vista, vista)

    def test_vista_invalida_se_rechaza(self):
        self.client.force_login(self.encargado)
        self.client.post(url("habitacion_crear"), {"numero": "303", "capacidad": "2", "orientacion": "NORTE", "vista": "BOSQUE"})
        self.assertFalse(Habitacion.objects.filter(numero="303").exists())
