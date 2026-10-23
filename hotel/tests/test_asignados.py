from django.urls import reverse

from hotel.models import Hospedaje
from hotel.services import (
    crear_asignacion,
    liberar_asignacion,
)

from .base import HotelTestCase


def url(name, pk=None):
    return reverse(
        "hotel:" + name,
        kwargs={
            "pk": pk
        } if pk is not None else None,
    )


class PasajerosAsignadosTests(
    HotelTestCase
):

    def setUp(self):
        self.client.force_login(
            self.encargado
        )

    def test_pasajero_activo_no_aparece_en_nueva_asignacion(
        self,
    ):
        crear_asignacion(
            {
                self.room1.pk: [
                    self.people[0].pk
                ]
            },
            self.people[0].pk,
            self.encargado,
        )

        response = self.client.get(
            url(
                "asignacion_crear"
            )
        )

        disponibles = list(
            response.context[
                "passengers"
            ].values_list(
                "pk",
                flat=True,
            )
        )

        self.assertNotIn(
            self.people[0].pk,
            disponibles,
        )

        self.assertIn(
            self.people[1].pk,
            disponibles,
        )

    def test_listado_muestra_solo_pasajeros_asignados(
        self,
    ):
        crear_asignacion(
            {
                self.room1.pk: [
                    self.people[0].pk
                ]
            },
            self.people[0].pk,
            self.encargado,
        )

        response = self.client.get(
            url(
                "pasajeros_asignados"
            )
        )

        hospedajes = list(
            response.context[
                "hospedajes"
            ]
        )

        self.assertEqual(
            len(hospedajes),
            1,
        )

        self.assertEqual(
            hospedajes[
                0
            ].pasajero_id,
            self.people[0].pk,
        )

        self.assertNotContains(
            response,
            self.people[1].nombre_completo,
        )

    def test_editar_contacto_pasajero_asignado(
        self,
    ):
        crear_asignacion(
            {
                self.room1.pk: [
                    self.people[0].pk
                ]
            },
            self.people[0].pk,
            self.encargado,
        )

        response = self.client.post(
            url(
                "pasajero_asignado_editar",
                self.people[0].pk,
            ),
            {
                "telefono":
                    "+56912345678",
                "correo":
                    "pasajero@hotel.test",
            },
        )

        self.assertRedirects(
            response,
            url(
                "pasajeros_asignados"
            ),
        )

        self.people[
            0
        ].refresh_from_db()

        self.assertEqual(
            self.people[
                0
            ].telefono,
            "+56912345678",
        )

        self.assertEqual(
            self.people[
                0
            ].correo,
            "pasajero@hotel.test",
        )

    def test_no_se_puede_editar_como_asignado_un_pasajero_libre(
        self,
    ):
        response = self.client.get(
            url(
                "pasajero_asignado_editar",
                self.people[0].pk,
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_pasajero_liberado_vuelve_a_estar_disponible(
        self,
    ):
        asignacion = crear_asignacion(
            {
                self.room1.pk: [
                    self.people[0].pk
                ]
            },
            self.people[0].pk,
            self.encargado,
        )

        liberar_asignacion(
            asignacion.pk,
            self.encargado,
        )

        self.assertFalse(
            Hospedaje.objects.filter(
                pasajero=self.people[0],
                activa=True,
            ).exists()
        )

        response = self.client.get(
            url(
                "asignacion_crear"
            )
        )

        disponibles = list(
            response.context[
                "passengers"
            ].values_list(
                "pk",
                flat=True,
            )
        )

        self.assertIn(
            self.people[0].pk,
            disponibles,
        )