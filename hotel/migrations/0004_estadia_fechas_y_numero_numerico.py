from datetime import timedelta

from django.db import migrations, models
from django.utils import timezone

import hotel.validators


def completar_fechas(apps, schema_editor):
    """
    Las asignaciones anteriores se cobraron como una sola noche
    ($40.000 por pasajero). Se registran con inicio en su fecha de
    ingreso y término al día siguiente, coherente con su costo.
    """
    Asignacion = apps.get_model("hotel", "Asignacion")

    for asignacion in Asignacion.objects.filter(
        fecha_inicio__isnull=True
    ).iterator():
        inicio = timezone.localtime(
            asignacion.fecha_ingreso
        ).date()

        Asignacion.objects.filter(
            pk=asignacion.pk
        ).update(
            fecha_inicio=inicio,
            fecha_termino=inicio + timedelta(days=1),
        )


class Migration(migrations.Migration):

    dependencies = [
        ("hotel", "0003_habitacion_vista"),
    ]

    operations = [
        migrations.AddField(
            model_name="asignacion",
            name="fecha_inicio",
            field=models.DateField(
                null=True,
                verbose_name="Inicio de la estadía",
            ),
        ),
        migrations.AddField(
            model_name="asignacion",
            name="fecha_termino",
            field=models.DateField(
                null=True,
                verbose_name="Término de la estadía",
            ),
        ),
        migrations.RunPython(
            completar_fechas,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="asignacion",
            name="fecha_inicio",
            field=models.DateField(
                verbose_name="Inicio de la estadía",
            ),
        ),
        migrations.AlterField(
            model_name="asignacion",
            name="fecha_termino",
            field=models.DateField(
                verbose_name="Término de la estadía",
            ),
        ),
        migrations.AddConstraint(
            model_name="asignacion",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("fecha_termino__gt", models.F("fecha_inicio"))
                ),
                name="asignacion_estadia_minimo_una_noche",
            ),
        ),
        migrations.AlterField(
            model_name="habitacion",
            name="numero",
            field=models.CharField(
                max_length=10,
                unique=True,
                validators=[
                    hotel.validators.validar_numero_habitacion
                ],
                verbose_name="Número",
            ),
        ),
    ]
