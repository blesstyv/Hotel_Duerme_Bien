from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        (
            "hotel",
            "0002_alter_usuario_managers",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="habitacion",
            name="vista",
            field=models.CharField(
                choices=[
                    (
                        "MAR",
                        "Vista al mar",
                    ),
                    (
                        "CIUDAD",
                        "Vista a la ciudad",
                    ),
                ],
                default="CIUDAD",
                max_length=10,
                verbose_name="Vista",
            ),
        ),

        migrations.AddConstraint(
            model_name="habitacion",
            constraint=(
                models.CheckConstraint(
                    condition=Q(
                        vista__in=[
                            "MAR",
                            "CIUDAD",
                        ]
                    ),
                    name=(
                        "habitacion_vista_valida"
                    ),
                )
            ),
        ),
    ]