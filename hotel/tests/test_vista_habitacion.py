from django.urls import reverse

from hotel.forms import (
    HabitacionForm,
)
from hotel.models import (
    Habitacion,
)

from .base import (
    HotelTestCase,
)


class HabitacionVistaTests(
    HotelTestCase
):

    def setUp(self):
        self.client.force_login(
            self.encargado
        )

    def test_habitacion_tiene_vista_por_defecto(
        self,
    ):
        room = (
            Habitacion.objects
            .create(
                numero="901",
                capacidad=2,
                orientacion=(
                    Habitacion
                    .Orientacion
                    .NORTE
                ),
            )
        )

        self.assertEqual(
            room.vista,
            Habitacion.Vista.CIUDAD,
        )

    def test_formulario_guarda_vista_al_mar(
        self,
    ):
        form = HabitacionForm(
            {
                "numero":
                    "902",
                "capacidad":
                    2,
                "orientacion":
                    Habitacion
                    .Orientacion
                    .SUR,
                "vista":
                    Habitacion
                    .Vista
                    .MAR,
            }
        )

        self.assertTrue(
            form.is_valid(),
            form.errors,
        )

        room = form.save()

        self.assertEqual(
            room.vista,
            Habitacion.Vista.MAR,
        )

        self.assertEqual(
            room.get_vista_display(),
            "Vista al mar",
        )

    def test_formulario_antiguo_sin_vista_mantiene_compatibilidad(
        self,
    ):
        form = HabitacionForm(
            {
                "numero":
                    "903",
                "capacidad":
                    1,
                "orientacion":
                    Habitacion
                    .Orientacion
                    .ESTE,
            }
        )

        self.assertTrue(
            form.is_valid(),
            form.errors,
        )

        room = form.save()

        self.assertEqual(
            room.vista,
            Habitacion.Vista.CIUDAD,
        )

    def test_nueva_asignacion_muestra_vistas(
        self,
    ):
        self.room1.vista = (
            Habitacion.Vista.MAR
        )

        self.room1.save(
            update_fields=[
                "vista"
            ]
        )

        response = self.client.get(
            reverse(
                "hotel:asignacion_crear"
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Vista al mar",
        )

        self.assertContains(
            response,
            "Vista a la ciudad",
        )

        self.assertContains(
            response,
            'data-room-view-filter',
        )

        self.assertContains(
            response,
            'data-vista="MAR"',
        )