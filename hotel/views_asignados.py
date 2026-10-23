from django import forms
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import IntegrityError, OperationalError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from .decorators import encargado_required
from .models import Hospedaje, Pasajero
from .services import registrar_movimiento


class PasajeroAsignadoForm(forms.ModelForm):
    """
    Edición operativa de pasajeros con hospedaje activo.

    No permite modificar RUT ni nombre durante una estadía activa,
    evitando inconsistencias con la asignación y su historial.
    """

    class Meta:
        model = Pasajero

        fields = (
            "telefono",
            "correo",
        )

        labels = {
            "telefono": "Teléfono",
            "correo": "Correo electrónico",
        }

        widgets = {
            "telefono": forms.TextInput(
                attrs={
                    "class": "input",
                    "type": "tel",
                    "placeholder": "+56 9 1234 5678",
                }
            ),
            "correo": forms.EmailInput(
                attrs={
                    "class": "input",
                    "placeholder": "pasajero@correo.cl",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["telefono"].required = False
        self.fields["correo"].required = False

        self.fields["telefono"].error_messages[
            "invalid"
        ] = "Ingrese un teléfono válido."

        self.fields["correo"].error_messages[
            "invalid"
        ] = "Ingrese un correo electrónico válido."


def _query(request):
    return request.GET.get("q", "").strip()[:100]


@encargado_required
@require_GET
def pasajeros_asignados(request):
    """
    Lista exclusivamente pasajeros que actualmente
    tienen un hospedaje activo.
    """

    q = _query(request)

    hospedajes = (
        Hospedaje.objects
        .filter(activa=True)
        .select_related(
            "pasajero",
            "detalle__habitacion",
            "detalle__asignacion",
            "detalle__asignacion__responsable",
        )
        .order_by(
            "detalle__habitacion__numero",
            "pasajero__nombre_completo",
        )
    )

    if q:
        rut_query = (
            q.replace(".", "")
            .replace(" ", "")
            .upper()
        )

        hospedajes = hospedajes.filter(
            Q(
                pasajero__nombre_completo__icontains=q
            )
            | Q(
                pasajero__rut__icontains=rut_query
            )
            | Q(
                pasajero__correo__icontains=q
            )
            | Q(
                detalle__habitacion__numero__icontains=q
            )
        )

    paginator = Paginator(
        hospedajes,
        15,
    )

    page = paginator.get_page(
        request.GET.get("page")
    )

    return render(
        request,
        "hotel/pasajeros_asignados.html",
        {
            "hospedajes": page,
            "page_obj": page,
            "q": q,
            "title": "Pasajeros asignados",
            "subtitle": (
                "Pasajeros que actualmente se encuentran "
                "hospedados y no pueden utilizarse en una "
                "nueva asignación."
            ),
            "nav_active": "asignaciones",
        },
    )


@encargado_required
@require_http_methods(["GET", "POST"])
def pasajero_asignado_editar(request, pk):
    """
    Solo permite editar pasajeros que mantengan
    actualmente un hospedaje activo.
    """

    queryset = (
        Pasajero.objects
        .filter(
            hospedajes__activa=True
        )
        .distinct()
    )

    pasajero = get_object_or_404(
        queryset,
        pk=pk,
    )

    hospedaje = (
        Hospedaje.objects
        .filter(
            pasajero=pasajero,
            activa=True,
        )
        .select_related(
            "detalle__habitacion",
            "detalle__asignacion",
            "detalle__asignacion__responsable",
        )
        .first()
    )

    form = PasajeroAsignadoForm(
        instance=pasajero
    )

    if request.method == "POST":
        try:
            with transaction.atomic():
                pasajero = get_object_or_404(
                    Pasajero.objects
                    .select_for_update()
                    .filter(
                        hospedajes__activa=True
                    )
                    .distinct(),
                    pk=pk,
                )

                form = PasajeroAsignadoForm(
                    request.POST,
                    instance=pasajero,
                )

                if form.is_valid():
                    pasajero = form.save()

                    registrar_movimiento(
                        request.user,
                        "Edición de pasajero asignado",
                        (
                            "Se actualizaron los datos "
                            f"de contacto de "
                            f"{pasajero.nombre_completo}."
                        ),
                    )

                    messages.success(
                        request,
                        (
                            "Datos del pasajero asignado "
                            "actualizados correctamente."
                        ),
                    )

                    return redirect(
                        "hotel:pasajeros_asignados"
                    )

        except (
            IntegrityError,
            OperationalError,
        ):
            form.add_error(
                None,
                (
                    "No se pudo actualizar el pasajero. "
                    "Intente nuevamente."
                ),
            )

    return render(
        request,
        "hotel/pasajero_asignado_form.html",
        {
            "form": form,
            "pasajero": pasajero,
            "hospedaje": hospedaje,
            "title": "Editar pasajero asignado",
            "subtitle": (
                "Modifique los datos de contacto del "
                "pasajero durante su estadía activa."
            ),
            "nav_active": "asignaciones",
        },
    )