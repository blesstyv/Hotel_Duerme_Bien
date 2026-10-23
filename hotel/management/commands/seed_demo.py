"""
Datos ficticios reproducibles.

Las contraseñas se obtienen únicamente
desde variables de entorno.
"""

import os

from django.conf import settings
from django.contrib.auth.password_validation import (
    validate_password,
)
from django.core.exceptions import (
    ValidationError,
)
from django.core.management.base import (
    BaseCommand,
    CommandError,
)
from django.db import transaction

from hotel.models import (
    Asignacion,
    Habitacion,
    Movimiento,
    Pasajero,
    Usuario,
)
from hotel.services import (
    crear_asignacion,
    liberar_asignacion,
    registrar_movimiento,
)


class Command(BaseCommand):
    help = (
        "Crea datos ficticios exclusivamente "
        "académicos de forma idempotente."
    )

    def add_arguments(
        self,
        parser,
    ):
        parser.add_argument(
            "--reset-passwords",
            action="store_true",
            help=(
                "Actualiza contraseñas demo "
                "desde el entorno, sin borrar datos."
            ),
        )

    @transaction.atomic
    def handle(
        self,
        *args,
        **options,
    ):
        if settings.PRODUCTION:
            raise CommandError(
                "seed_demo solo está permitido "
                "en el entorno de desarrollo "
                "académico."
            )

        usernames = [
            os.getenv(
                "DEMO_ADMIN_USERNAME",
                "admin_demo",
            ),
            os.getenv(
                "DEMO_ENCARGADO_USERNAME",
                "encargado_demo",
            ),
            "recepcion_demo",
            "encargado_inactivo_demo",
        ]

        if (
            len(set(usernames))
            !=
            len(usernames)
        ):
            raise CommandError(
                "Los nombres de usuarios demo "
                "deben ser distintos."
            )

        specs = [
            (
                usernames[0],
                Usuario.Rol.ADMINISTRADOR,
                "DEMO_ADMIN_PASSWORD",
                "Administrador",
                "Demo",
                True,
            ),
            (
                usernames[1],
                Usuario.Rol.ENCARGADO,
                "DEMO_ENCARGADO_PASSWORD",
                "Camila",
                "Rojas",
                True,
            ),
            (
                usernames[2],
                Usuario.Rol.ENCARGADO,
                "DEMO_ENCARGADO_PASSWORD",
                "Tomás",
                "Fuentes",
                True,
            ),
            (
                usernames[3],
                Usuario.Rol.ENCARGADO,
                "DEMO_ENCARGADO_PASSWORD",
                "Daniela",
                "Soto",
                False,
            ),
        ]

        users = []

        for (
            username,
            rol,
            variable,
            first_name,
            last_name,
            active,
        ) in specs:

            password = os.getenv(
                variable,
                "",
            )

            if not password:
                raise CommandError(
                    f"Define {variable} "
                    "en .env antes de "
                    "ejecutar seed_demo."
                )

            try:
                validate_password(
                    password
                )
            except ValidationError as exc:
                raise CommandError(
                    f"{variable}: "
                    f"{' '.join(exc.messages)}"
                )

            user, created = (
                Usuario.objects
                .get_or_create(
                    username=username,
                    defaults={
                        "rol": rol,
                        "first_name":
                            first_name,
                        "last_name":
                            last_name,
                        "is_active":
                            active,
                    },
                )
            )

            if user.rol != rol:
                raise CommandError(
                    "Un nombre de usuario demo "
                    "ya pertenece a otro rol; "
                    "configura nombres distintos."
                )

            if (
                created
                or
                options[
                    "reset_passwords"
                ]
            ):
                user.set_password(
                    password
                )
                user.save()

            users.append(
                user
            )

        room_specs = [
            (
                "101",
                1,
                "NORTE",
                "MAR",
            ),
            (
                "102",
                2,
                "SUR",
                "CIUDAD",
            ),
            (
                "103",
                3,
                "ESTE",
                "MAR",
            ),
            (
                "104",
                2,
                "OESTE",
                "CIUDAD",
            ),
            (
                "201",
                1,
                "NORTE",
                "MAR",
            ),
            (
                "202",
                2,
                "SUR",
                "CIUDAD",
            ),
            (
                "203",
                3,
                "ESTE",
                "MAR",
            ),
            (
                "204",
                2,
                "OESTE",
                "CIUDAD",
            ),
            (
                "301",
                1,
                "NORTE",
                "MAR",
            ),
            (
                "302",
                2,
                "SUR",
                "CIUDAD",
            ),
            (
                "303",
                3,
                "ESTE",
                "MAR",
            ),
            (
                "304",
                2,
                "INTERIOR",
                "CIUDAD",
            ),
        ]

        rooms = []

        for (
            numero,
            capacidad,
            orientacion,
            vista,
        ) in room_specs:

            room, created = (
                Habitacion.objects
                .get_or_create(
                    numero=numero,
                    defaults={
                        "capacidad":
                            capacidad,
                        "orientacion":
                            orientacion,
                        "vista":
                            vista,
                    },
                )
            )

            if (
                not created
                and
                room.vista != vista
            ):
                room.vista = vista

                room.save(
                    update_fields=[
                        "vista"
                    ]
                )

            rooms.append(
                room
            )

        names = [
            "María González",
            "Carlos Ramírez",
            "Ana Torres",
            "Luis Mendoza",
            "Sofía Herrera",
            "Javier Morales",
            "Catalina Vargas",
            "Diego Paredes",
            "Valentina Díaz",
            "Sebastián Reyes",
            "Isidora Silva",
            "Mateo Castillo",
        ]

        passengers = []

        for index, name in enumerate(
            names
        ):
            body = str(
                15000000
                +
                index
            )

            dv_num = (
                11
                -
                sum(
                    int(number)
                    *
                    (
                        2
                        +
                        position
                        %
                        6
                    )
                    for (
                        position,
                        number,
                    )
                    in enumerate(
                        reversed(
                            body
                        )
                    )
                )
                %
                11
            )

            dv = (
                "0"
                if dv_num == 11
                else
                "K"
                if dv_num == 10
                else
                str(dv_num)
            )

            passenger, _ = (
                Pasajero.objects
                .get_or_create(
                    rut=(
                        f"{body}-{dv}"
                    ),
                    defaults={
                        "nombre_completo":
                            name,
                        "telefono":
                            (
                                "+569600000"
                                f"{index:02d}"
                            ),
                        "correo":
                            (
                                f"pasajero"
                                f"{index + 1}"
                                "@example.test"
                            ),
                    },
                )
            )

            passengers.append(
                passenger
            )

        operator = users[1]

        if not (
            Movimiento.objects
            .filter(
                accion=(
                    "DEMO_INICIALIZADA"
                )
            )
            .exists()
        ):
            if (
                Asignacion.objects
                .exists()
            ):
                raise CommandError(
                    "La base ya contiene "
                    "operaciones. seed_demo "
                    "no añade estadías sobre "
                    "datos existentes."
                )

            closed = crear_asignacion(
                {
                    rooms[0].pk: [
                        passengers[5].pk
                    ]
                },
                passengers[5].pk,
                operator,
            )

            liberar_asignacion(
                closed.pk,
                operator,
            )

            closed2 = crear_asignacion(
                {
                    rooms[3].pk: [
                        passengers[6].pk,
                        passengers[7].pk,
                    ]
                },
                passengers[6].pk,
                operator,
            )

            liberar_asignacion(
                closed2.pk,
                operator,
            )

            crear_asignacion(
                {
                    rooms[2].pk: [
                        passenger.pk
                        for passenger
                        in passengers[:3]
                    ],
                    rooms[1].pk: [
                        passenger.pk
                        for passenger
                        in passengers[3:5]
                    ],
                },
                passengers[0].pk,
                operator,
            )

            crear_asignacion(
                {
                    rooms[4].pk: [
                        passengers[8].pk
                    ]
                },
                passengers[8].pk,
                operator,
            )

            registrar_movimiento(
                users[0],
                "ENCARGADO_CREADO",
                (
                    "Cuentas ficticias de "
                    "recepción creadas para "
                    "la demostración."
                ),
            )

            registrar_movimiento(
                users[0],
                "DEMO_INICIALIZADA",
                (
                    "Datos académicos "
                    "ficticios inicializados."
                ),
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Demo preparada: "
                "4 usuarios, "
                "12 habitaciones, "
                "12 pasajeros; "
                "2 estadías finalizadas "
                "y 2 activas iniciales."
            )
        )

        self.stdout.write(
            "Contraseñas configuradas "
            "en el entorno local. "
            "No se muestran en logs."
        )