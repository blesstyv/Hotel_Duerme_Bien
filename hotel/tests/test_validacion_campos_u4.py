"""
Validación estricta de campos (retroalimentación de la profesora):
teléfono móvil chileno (+569 y 8 dígitos), correo, nombre de usuario,
capacidad y demás campos de formularios, modelos y POST manipulados.
"""
from django.core.exceptions import ValidationError

from hotel.forms import (
    EncargadoCreationForm,
    EncargadoEditForm,
    HabitacionForm,
    LoginForm,
    PasajeroForm,
)
from hotel.models import Habitacion, Pasajero, Usuario
from hotel.validators import (
    normalizar_correo,
    normalizar_telefono,
    validar_nombre_usuario,
    validar_telefono,
)
from hotel.views_asignados import PasajeroAsignadoForm

from django.urls import reverse

from .base import PASSWORD, HotelTestCase, crear_asignacion, rut_for


def url(name, *args):
    return reverse(f"hotel:{name}", args=args)

TELEFONOS_VALIDOS = [
    ("+56912345678", "+56912345678"),
    ("+56 9 1234 5678", "+56912345678"),
    ("+569 12345678", "+56912345678"),
    ("  +56912345678  ", "+56912345678"),
    ("", ""),
]

TELEFONOS_INVALIDOS = [
    "-",
    "--",
    "+56-9-1234-5678",
    "+569-12345678",
    "9-12345678",
    "(9) 12345678",
    "+56 (9) 12345678",
    "+56912345",          # muy corto
    "+5691234567",        # 7 dígitos tras +569
    "+569123456789",      # 9 dígitos tras +569
    "56912345678",        # sin +
    "912345678",          # sin prefijo
    "+56812345678",       # no es móvil (+569)
    "+56212345678",       # fijo
    "+1 555 123 4567",    # otro país
    "+569abcdefgh",
    "+56912345678x",
    "+56.9.1234.5678",
    "++56912345678",
    "+56912345678\n",     # salto de línea intermedio válido solo al borde
    "+569 1234\t5678",
    "1234567",
    "0000000",
    "+",
    "tel",
    "<script>",
    "+569１２３４５６７８",  # dígitos fullwidth
]


class TelefonoChilenoTests(HotelTestCase):
    def test_telefonos_validos_se_normalizan(self):
        for entrada, esperado in TELEFONOS_VALIDOS:
            with self.subTest(entrada=entrada):
                self.assertEqual(normalizar_telefono(entrada), esperado)

    def test_telefonos_invalidos_se_rechazan(self):
        for entrada in TELEFONOS_INVALIDOS:
            if entrada == "+56912345678\n":
                continue  # se recorta al borde: es el mismo número válido
            with self.subTest(entrada=entrada):
                with self.assertRaises(ValidationError):
                    normalizar_telefono(entrada)
                with self.assertRaises(ValidationError):
                    validar_telefono(entrada)

    def test_mensaje_de_error_indica_formato_correcto(self):
        with self.assertRaises(ValidationError) as ctx:
            normalizar_telefono("-")
        self.assertIn("+569", ctx.exception.messages[0])

    def form_pasajero(self, telefono, **extra):
        datos = {
            "rut": rut_for(15000001),
            "nombre_completo": "Ana María Soto",
            "telefono": telefono,
            "correo": "",
        }
        datos.update(extra)
        return PasajeroForm(datos)

    def test_pasajeroform_rechaza_guion_y_formatos_invalidos(self):
        for entrada in TELEFONOS_INVALIDOS:
            if entrada == "+56912345678\n":
                continue
            with self.subTest(entrada=entrada):
                form = self.form_pasajero(entrada)
                self.assertFalse(form.is_valid())
                self.assertIn("telefono", form.errors)

    def test_pasajeroform_telefono_opcional_vacio_es_valido(self):
        form = self.form_pasajero("")
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["telefono"], "")

    def test_pasajeroform_guarda_telefono_normalizado(self):
        form = self.form_pasajero("+56 9 8765 4321")
        self.assertTrue(form.is_valid(), form.errors)
        pasajero = form.save()
        self.assertEqual(pasajero.telefono, "+56987654321")

    def test_modelo_rechaza_telefono_invalido_en_full_clean(self):
        persona = Pasajero(
            rut=rut_for(15000002), nombre_completo="Luis Pérez", telefono="-"
        )
        with self.assertRaises(ValidationError) as ctx:
            persona.full_clean()
        self.assertIn("telefono", ctx.exception.message_dict)

    def test_modelo_normaliza_telefono_con_espacios(self):
        persona = Pasajero(
            rut=rut_for(15000003),
            nombre_completo="Luis Pérez",
            telefono="+56 9 1111 2222",
        )
        persona.full_clean()
        self.assertEqual(persona.telefono, "+56911112222")

    def test_formulario_html_declara_pattern_y_tipo_tel(self):
        html = str(PasajeroForm()["telefono"])
        self.assertIn('type="tel"', html)
        self.assertIn("pattern=", html)
        self.assertIn("maxlength", html)

    def test_crear_pasajero_por_vista_rechaza_guion(self):
        self.client.force_login(self.encargado)
        antes = Pasajero.objects.count()
        respuesta = self.client.post(
            url("pasajero_crear"),
            {
                "rut": rut_for(15000004),
                "nombre_completo": "Pedro Rojas",
                "telefono": "-",
                "correo": "",
            },
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("telefono", respuesta.context["form"].errors)
        self.assertEqual(Pasajero.objects.count(), antes)

    def test_crear_pasajero_por_vista_acepta_formato_chileno(self):
        self.client.force_login(self.encargado)
        respuesta = self.client.post(
            url("pasajero_crear"),
            {
                "rut": rut_for(15000005),
                "nombre_completo": "Pedro Rojas",
                "telefono": "+56 9 1234 5678",
                "correo": "pedro@correo.cl",
            },
        )
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(
            Pasajero.objects.get(rut=rut_for(15000005)).telefono,
            "+56912345678",
        )

    def test_editar_pasajero_rechaza_telefono_invalido(self):
        self.client.force_login(self.encargado)
        persona = self.people[1]
        respuesta = self.client.post(
            url("pasajero_editar", persona.pk),
            {
                "rut": persona.rut,
                "nombre_completo": persona.nombre_completo,
                "telefono": "9-1234-5678",
                "correo": "",
            },
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("telefono", respuesta.context["form"].errors)
        persona.refresh_from_db()
        self.assertEqual(persona.telefono, "")


class PasajeroAsignadoValidacionTests(HotelTestCase):
    def setUp(self):
        self.huesped = self.people[0]
        crear_asignacion(
            {self.room1.pk: [self.huesped.pk]}, self.huesped.pk, self.encargado
        )
        self.client.force_login(self.encargado)

    def test_edicion_operativa_rechaza_telefono_con_guion(self):
        form = PasajeroAsignadoForm(
            {"telefono": "-", "correo": ""}, instance=self.huesped
        )
        self.assertFalse(form.is_valid())
        self.assertIn("telefono", form.errors)

    def test_edicion_operativa_rechaza_formatos_invalidos(self):
        for entrada in ("+56-9-12345678", "912345678", "+5691234", "abc"):
            with self.subTest(entrada=entrada):
                form = PasajeroAsignadoForm(
                    {"telefono": entrada, "correo": ""}, instance=self.huesped
                )
                self.assertFalse(form.is_valid())
                self.assertIn("telefono", form.errors)

    def test_edicion_operativa_por_vista_no_guarda_telefono_invalido(self):
        respuesta = self.client.post(
            url("pasajero_asignado_editar", self.huesped.pk),
            {"telefono": "-", "correo": "ok@correo.cl"},
        )
        self.assertEqual(respuesta.status_code, 200)
        self.huesped.refresh_from_db()
        self.assertEqual(self.huesped.telefono, "")
        self.assertEqual(self.huesped.correo, "")

    def test_edicion_operativa_acepta_y_normaliza(self):
        respuesta = self.client.post(
            url("pasajero_asignado_editar", self.huesped.pk),
            {"telefono": "+56 9 1234 5678", "correo": "Ok@Correo.CL"},
        )
        self.assertEqual(respuesta.status_code, 302)
        self.huesped.refresh_from_db()
        self.assertEqual(self.huesped.telefono, "+56912345678")
        self.assertEqual(self.huesped.correo, "ok@correo.cl")

    def test_edicion_operativa_permite_vaciar_campos_opcionales(self):
        Pasajero.objects.filter(pk=self.huesped.pk).update(
            telefono="+56912345678", correo="a@b.cl"
        )
        respuesta = self.client.post(
            url("pasajero_asignado_editar", self.huesped.pk),
            {"telefono": "", "correo": ""},
        )
        self.assertEqual(respuesta.status_code, 302)
        self.huesped.refresh_from_db()
        self.assertEqual(self.huesped.telefono, "")
        self.assertEqual(self.huesped.correo, "")


class CorreoTests(HotelTestCase):
    VALIDOS = [
        ("ana@correo.cl", "ana@correo.cl"),
        ("Ana.Perez+hotel@Mail.Example.COM", "ana.perez+hotel@mail.example.com"),
        ("a_b-c@sub.dominio.cl", "a_b-c@sub.dominio.cl"),
        ("", ""),
    ]
    INVALIDOS = [
        "ana",
        "ana@",
        "@correo.cl",
        "ana@correo",
        "ana@correo.",
        "ana@.cl",
        "ana@@correo.cl",
        "ana correo@correo.cl",
        "ana@correo .cl",
        ".ana@correo.cl",
        "ana.@correo.cl",
        "ana..perez@correo.cl",
        "ana@correo..cl",
        "ana@correo.c",
        "ana@correo.c1",
        "ana@-correo.cl",
        "<ana>@correo.cl",
        "ana@correo.cl;otro@correo.cl",
        "a" * 65 + "@correo.cl",
        "a@" + "b" * 250 + ".cl",
    ]

    def test_correos_validos(self):
        for entrada, esperado in self.VALIDOS:
            with self.subTest(entrada=entrada):
                self.assertEqual(normalizar_correo(entrada), esperado)

    def test_correos_invalidos(self):
        for entrada in self.INVALIDOS:
            with self.subTest(entrada=entrada):
                with self.assertRaises(ValidationError):
                    normalizar_correo(entrada)

    def test_pasajeroform_valida_correo(self):
        for entrada in self.INVALIDOS:
            with self.subTest(entrada=entrada):
                form = PasajeroForm(
                    {
                        "rut": rut_for(15000010),
                        "nombre_completo": "Ana Soto",
                        "telefono": "",
                        "correo": entrada,
                    }
                )
                self.assertFalse(form.is_valid())
                self.assertIn("correo", form.errors)

    def test_pasajeroform_correo_opcional(self):
        form = PasajeroForm(
            {
                "rut": rut_for(15000011),
                "nombre_completo": "Ana Soto",
                "telefono": "",
                "correo": "",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_modelo_rechaza_correo_sin_tld(self):
        persona = Pasajero(
            rut=rut_for(15000012), nombre_completo="Ana Soto", correo="ana@correo"
        )
        with self.assertRaises(ValidationError) as ctx:
            persona.full_clean()
        self.assertIn("correo", ctx.exception.message_dict)

    def test_encargado_crear_valida_correo(self):
        for entrada in ("sin-arroba", "ana@correo", "ana@correo..cl"):
            with self.subTest(entrada=entrada):
                form = EncargadoCreationForm(
                    {
                        "username": "nuevo_enc",
                        "first_name": "Ana",
                        "last_name": "Pérez",
                        "email": entrada,
                        "password1": PASSWORD,
                        "password2": PASSWORD,
                    }
                )
                self.assertFalse(form.is_valid())
                self.assertIn("email", form.errors)

    def test_encargado_editar_valida_correo(self):
        form = EncargadoEditForm(
            {
                "username": self.encargado.username,
                "first_name": "Camila",
                "last_name": "Rojas",
                "email": "mal@correo",
            },
            instance=self.encargado,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)


class UsuarioValidacionTests(HotelTestCase):
    def datos(self, **cambios):
        base = {
            "username": "nuevo_enc",
            "first_name": "Ana",
            "last_name": "Pérez",
            "email": "ana@correo.cl",
            "password1": PASSWORD,
            "password2": PASSWORD,
        }
        base.update(cambios)
        return base

    def test_crear_usuario_valido(self):
        form = EncargadoCreationForm(self.datos())
        self.assertTrue(form.is_valid(), form.errors)

    def test_nombre_usuario_invalido(self):
        for usuario in (
            "ab",            # muy corto
            "abc",           # muy corto
            "con espacio",
            "ñandú_01",      # caracteres fuera de ASCII
            "1234",          # sin letras
            "usuario!",
            "<script>",
            "a" * 151,
            "usu/ario",
        ):
            with self.subTest(usuario=usuario):
                form = EncargadoCreationForm(self.datos(username=usuario))
                self.assertFalse(form.is_valid())
                self.assertIn("username", form.errors)

    def test_nombre_usuario_validador_directo(self):
        self.assertEqual(validar_nombre_usuario("ana.perez-01"), "ana.perez-01")
        with self.assertRaises(ValidationError):
            validar_nombre_usuario("a b c d")

    def test_nombres_y_apellidos_con_numeros_o_simbolos(self):
        for campo in ("first_name", "last_name"):
            for valor in ("Ana123", "1234", "Ana@", "<b>Ana</b>", "   ", "A_na"):
                with self.subTest(campo=campo, valor=valor):
                    form = EncargadoCreationForm(self.datos(**{campo: valor}))
                    self.assertFalse(form.is_valid())
                    self.assertIn(campo, form.errors)

    def test_nombres_obligatorios(self):
        for campo in ("first_name", "last_name", "username"):
            with self.subTest(campo=campo):
                form = EncargadoCreationForm(self.datos(**{campo: ""}))
                self.assertFalse(form.is_valid())
                self.assertIn(campo, form.errors)

    def test_nombre_demasiado_largo(self):
        form = EncargadoCreationForm(self.datos(first_name="A" * 151))
        self.assertFalse(form.is_valid())
        self.assertIn("first_name", form.errors)

    def test_contrasenas_no_coinciden_o_debiles(self):
        form = EncargadoCreationForm(self.datos(password2="Otra#Clave2026"))
        self.assertFalse(form.is_valid())
        form = EncargadoCreationForm(
            self.datos(password1="12345678", password2="12345678")
        )
        self.assertFalse(form.is_valid())

    def test_usuario_duplicado_ignora_mayusculas(self):
        form = EncargadoCreationForm(
            self.datos(username=self.encargado.username.upper())
        )
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

    def test_crear_por_vista_no_guarda_datos_invalidos(self):
        self.client.force_login(self.admin_user)
        antes = Usuario.objects.count()
        respuesta = self.client.post(
            url("encargado_crear"), self.datos(username="ab", email="x@y")
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Usuario.objects.count(), antes)

    def test_login_limita_largo_de_campos(self):
        form = LoginForm({"username": "a" * 151, "password": "x"})
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)
        form = LoginForm({"username": "ana", "password": "x" * 129})
        self.assertFalse(form.is_valid())
        self.assertIn("password", form.errors)


class HabitacionValidacionTests(HotelTestCase):
    def datos(self, **cambios):
        base = {
            "numero": "250",
            "capacidad": "2",
            "orientacion": "NORTE",
            "vista": "MAR",
        }
        base.update(cambios)
        return base

    def test_habitacion_valida(self):
        self.assertTrue(HabitacionForm(self.datos()).is_valid())

    def test_numero_invalido(self):
        for numero in ("", "0", "012", "10A", "1 0", "-5", "123456", "1.5", "１２３"):
            with self.subTest(numero=numero):
                form = HabitacionForm(self.datos(numero=numero))
                self.assertFalse(form.is_valid())
                self.assertIn("numero", form.errors)

    def test_capacidad_invalida(self):
        for capacidad in ("", "0", "-1", "abc", "1.5", "21", "99999", "2147483647"):
            with self.subTest(capacidad=capacidad):
                form = HabitacionForm(self.datos(capacidad=capacidad))
                self.assertFalse(form.is_valid())
                self.assertIn("capacidad", form.errors)

    def test_capacidad_limite_superior_valida(self):
        self.assertTrue(HabitacionForm(self.datos(capacidad="20")).is_valid())

    def test_orientacion_y_vista_fuera_de_catalogo(self):
        form = HabitacionForm(self.datos(orientacion="ARRIBA"))
        self.assertFalse(form.is_valid())
        self.assertIn("orientacion", form.errors)
        form = HabitacionForm(self.datos(vista="LUNA"))
        self.assertFalse(form.is_valid())
        self.assertIn("vista", form.errors)

    def test_modelo_rechaza_capacidad_excesiva(self):
        habitacion = Habitacion(numero="300", capacidad=21, orientacion="SUR")
        with self.assertRaises(ValidationError) as ctx:
            habitacion.full_clean()
        self.assertIn("capacidad", ctx.exception.message_dict)

    def test_crear_por_vista_no_guarda_capacidad_absurda(self):
        self.client.force_login(self.encargado)
        antes = Habitacion.objects.count()
        respuesta = self.client.post(
            url("habitacion_crear"), self.datos(capacidad="2147483647")
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Habitacion.objects.count(), antes)


class PasajeroCamposTests(HotelTestCase):
    def datos(self, **cambios):
        base = {
            "rut": rut_for(15000020),
            "nombre_completo": "Ana María Soto",
            "telefono": "+56912345678",
            "correo": "ana@correo.cl",
        }
        base.update(cambios)
        return base

    def test_pasajero_valido(self):
        form = PasajeroForm(self.datos())
        self.assertTrue(form.is_valid(), form.errors)

    def test_rut_invalido(self):
        for rut in ("", "1", "12345678-0", "abc", "12.345.678-9", "0-0", "12 345", "<x>"):
            with self.subTest(rut=rut):
                form = PasajeroForm(self.datos(rut=rut))
                self.assertFalse(form.is_valid())
                self.assertIn("rut", form.errors)

    def test_nombre_invalido(self):
        for nombre in ("", "  ", "AB", "123456", "Ana 123", "Ana@Soto", "<b>Ana</b>", "A" * 151):
            with self.subTest(nombre=nombre):
                form = PasajeroForm(self.datos(nombre_completo=nombre))
                self.assertFalse(form.is_valid())
                self.assertIn("nombre_completo", form.errors)

    def test_nombre_con_tildes_enie_y_apostrofe_es_valido(self):
        form = PasajeroForm(
            self.datos(nombre_completo="María José O'Higgins-Núñez")
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_rut_duplicado(self):
        persona = self.people[0]
        form = PasajeroForm(self.datos(rut=persona.rut))
        self.assertFalse(form.is_valid())
        self.assertIn("rut", form.errors)

    def test_registro_antiguo_con_telefono_invalido_exige_corregirlo_al_editar(self):
        persona = self.people[2]
        Pasajero.objects.filter(pk=persona.pk).update(
            nombre_completo="Persona Antigua", telefono="(9) 1234-5678"
        )
        persona.refresh_from_db()
        form = PasajeroForm(
            {
                "rut": persona.rut,
                "nombre_completo": persona.nombre_completo,
                "telefono": persona.telefono,
                "correo": "",
            },
            instance=persona,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("telefono", form.errors)
        corregido = PasajeroForm(
            {
                "rut": persona.rut,
                "nombre_completo": persona.nombre_completo,
                "telefono": "+56912345678",
                "correo": "",
            },
            instance=persona,
        )
        self.assertTrue(corregido.is_valid(), corregido.errors)

    def test_hospedado_conserva_identidad_pero_valida_contacto(self):
        persona = self.people[3]
        crear_asignacion(
            {self.room2.pk: [persona.pk]}, persona.pk, self.encargado
        )
        form = PasajeroForm(
            {
                "rut": rut_for(19999999),
                "nombre_completo": "Otro Nombre",
                "telefono": "-",
                "correo": "no-es-correo",
            },
            instance=persona,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("telefono", form.errors)
        self.assertIn("correo", form.errors)
        self.assertNotIn("rut", form.errors)
        self.assertNotIn("nombre_completo", form.errors)


class ConsultasYParametrosTests(HotelTestCase):
    """Parámetros GET manipulados no rompen las vistas."""

    def setUp(self):
        self.client.force_login(self.encargado)

    def test_filtros_con_valores_hostiles_responden_200(self):
        rutas = ["habitacion_list", "pasajero_list"]
        hostiles = [
            {"q": "x" * 5000},
            {"q": "<script>alert(1)</script>"},
            {"q": "' OR 1=1 --"},
            {"page": "abc"},
            {"page": "-1"},
            {"page": "999999999999999999999"},
            {"estado": "NO_EXISTE"},
            {"capacidad": "abc"},
            {"capacidad": "-3"},
            {"capacidad": "99999999999999999999"},
            {"vista": "LUNA"},
            {"orientacion": "ARRIBA"},
            {"activa": "quizas"},
        ]
        for ruta in rutas:
            for params in hostiles:
                with self.subTest(ruta=ruta, params=params):
                    respuesta = self.client.get(url(ruta), params)
                    self.assertEqual(respuesta.status_code, 200)
