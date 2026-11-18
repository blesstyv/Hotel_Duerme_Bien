"""Sidebar plegable y boleta con datos de la empresa."""
from django.urls import reverse

from hotel.empresa import EMPRESA
from hotel.validators import validar_rut

from .base import HotelTestCase, crear_asignacion


def url(name, *args):
    return reverse(f"hotel:{name}", args=args)


class EmpresaTests(HotelTestCase):
    def test_rut_de_la_empresa_es_valido(self):
        validar_rut(EMPRESA["rut"])

    def test_datos_obligatorios_presentes(self):
        for clave in ("razon_social", "rut", "giro", "direccion", "telefono", "correo"):
            self.assertTrue(EMPRESA[clave], clave)


class BoletaEmpresaTests(HotelTestCase):
    def setUp(self):
        self.huesped = self.people[0]
        self.asignacion = crear_asignacion(
            {self.room1.pk: [self.huesped.pk]}, self.huesped.pk, self.encargado
        )
        self.client.force_login(self.encargado)

    def boleta(self):
        return self.client.get(url("asignacion_boleta", self.asignacion.pk))

    def test_muestra_datos_de_la_empresa(self):
        r = self.boleta()
        self.assertEqual(r.status_code, 200)
        for clave in ("razon_social", "rut", "giro", "direccion", "telefono", "correo"):
            self.assertContains(r, EMPRESA[clave])

    def test_muestra_folio_y_asignacion(self):
        r = self.boleta()
        self.assertContains(r, f"N° {self.asignacion.pk:06d}")
        self.assertContains(r, f"Asignación N°")
        self.assertContains(r, "Atendido por")

    def test_mantiene_aviso_no_tributario_y_calculo(self):
        r = self.boleta()
        self.assertContains(r, "no corresponde a un documento tributario electrónico")
        self.assertContains(r, "ficticios")
        self.assertContains(r, "$40.000")

    def test_boleta_sigue_exigiendo_sesion(self):
        self.client.logout()
        r = self.client.get(url("asignacion_boleta", self.asignacion.pk))
        self.assertEqual(r.status_code, 302)


class SidebarPlegableTests(HotelTestCase):
    def test_boton_presente_para_encargado_y_admin(self):
        for usuario, ruta in ((self.encargado, "dashboard_encargado"), (self.admin_user, "dashboard_admin")):
            with self.subTest(rol=usuario.rol):
                self.client.force_login(usuario)
                r = self.client.get(url(ruta))
                self.assertContains(r, "data-sidebar-collapse")
                self.assertContains(r, "sidebar_init.js")

    def test_enlaces_tienen_titulo_para_modo_compacto(self):
        self.client.force_login(self.encargado)
        r = self.client.get(url("dashboard_encargado"))
        for texto in ("Habitaciones", "Pasajeros", "Asignaciones", "Cerrar sesión"):
            self.assertContains(r, f'title="{texto}"')

    def test_scripts_son_externos_sin_inline(self):
        self.client.force_login(self.encargado)
        r = self.client.get(url("dashboard_encargado"))
        self.assertNotContains(r, "localStorage")
