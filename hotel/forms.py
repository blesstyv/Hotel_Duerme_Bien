"""
Formularios de aplicación:
cada campo editable se declara explícitamente.
"""

from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from .models import (
    Habitacion,
    Pasajero,
    Usuario,
)

from .validators import (
    normalizar_rut,
    validate_safe_id_list,
    validate_safe_positive_id,
)


class SpanishFormMixin:
    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        for name, field in self.fields.items():
            field.widget.attrs.setdefault(
                "class",
                "input",
            )

            field.error_messages[
                "required"
            ] = "Este campo es obligatorio."

            if isinstance(
                field,
                forms.EmailField,
            ):
                field.error_messages[
                    "invalid"
                ] = (
                    "Ingrese un correo electrónico válido."
                )


class SafeModelChoiceField(
    forms.ModelChoiceField
):
    """
    ModelChoiceField que rechaza IDs
    manipulados antes de consultar la BD.
    """

    def clean(self, value):
        if value in self.empty_values:
            return super().clean(value)

        try:
            safe_value = (
                validate_safe_positive_id(
                    value
                )
            )

        except ValidationError:
            raise ValidationError(
                self.error_messages.get(
                    "invalid_choice",
                    "Seleccione una opción válida.",
                ),
                code="invalid_choice",
            )

        return super().clean(
            safe_value
        )


class SafeModelMultipleChoiceField(
    forms.ModelMultipleChoiceField
):
    """
    ModelMultipleChoiceField que valida
    el rango de PK antes de ejecutar SQL.
    """

    def clean(self, value):
        if not value:
            return super().clean(value)

        try:
            safe_values = (
                validate_safe_id_list(
                    value
                )
            )

        except ValidationError:
            raise ValidationError(
                self.error_messages.get(
                    "invalid_choice",
                    "Seleccione opciones válidas.",
                ),
                code="invalid_choice",
            )

        return super().clean(
            safe_values
        )


class LoginForm(
    SpanishFormMixin,
    forms.Form,
):
    username = forms.CharField(
        label="Usuario",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "autocomplete":
                    "username",
                "autofocus":
                    True,
            }
        ),
    )

    password = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete":
                    "current-password",
            }
        ),
    )


class EncargadoCreationForm(
    SpanishFormMixin,
    UserCreationForm,
):
    class Meta(
        UserCreationForm.Meta
    ):
        model = Usuario

        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
        )

        labels = {
            "username":
                "Usuario",
            "first_name":
                "Nombres",
            "last_name":
                "Apellidos",
            "email":
                "Correo electrónico",
        }

        help_texts = {
            "username":
                "Hasta 150 caracteres. "
                "Letras, números y @ . + - _."
        }

        error_messages = {
            "username": {
                "unique":
                    "Ya existe una cuenta "
                    "con este nombre de usuario."
            }
        }

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        self.fields[
            "first_name"
        ].required = True

        self.fields[
            "last_name"
        ].required = True

        self.fields[
            "password1"
        ].label = "Contraseña"

        self.fields[
            "password2"
        ].label = "Confirmar contraseña"

        self.fields[
            "password1"
        ].widget.attrs[
            "autocomplete"
        ] = "new-password"

        self.fields[
            "password2"
        ].widget.attrs[
            "autocomplete"
        ] = "new-password"

    def clean_username(self):
        username = (
            self.cleaned_data[
                "username"
            ].strip()
        )

        if Usuario.objects.filter(
            username__iexact=username
        ).exists():
            raise ValidationError(
                "Ya existe una cuenta "
                "con este nombre de usuario."
            )

        return username

    def save(
        self,
        commit=True,
    ):
        user = super().save(
            commit=False
        )

        user.rol = (
            Usuario.Rol.ENCARGADO
        )

        user.is_active = True
        user.is_staff = False
        user.is_superuser = False

        if commit:
            user.save()

        return user


class EncargadoEditForm(
    SpanishFormMixin,
    forms.ModelForm,
):
    password1 = forms.CharField(
        label="Nueva contraseña",
        required=False,
        strip=False,
        help_text=(
            "Deje ambos campos vacíos "
            "para conservar la contraseña actual."
        ),
        widget=forms.PasswordInput(
            attrs={
                "autocomplete":
                    "new-password",
            }
        ),
    )

    password2 = forms.CharField(
        label="Confirmar nueva contraseña",
        required=False,
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete":
                    "new-password",
            }
        ),
    )

    class Meta:
        model = Usuario

        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
        )

        labels = {
            "username":
                "Usuario",
            "first_name":
                "Nombres",
            "last_name":
                "Apellidos",
            "email":
                "Correo electrónico",
        }

        help_texts = {
            "username":
                "Hasta 150 caracteres. "
                "Letras, números y @ . + - _."
        }

        error_messages = {
            "username": {
                "unique":
                    "Ya existe una cuenta "
                    "con este nombre de usuario."
            }
        }

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        self.fields[
            "first_name"
        ].required = True

        self.fields[
            "last_name"
        ].required = True

    def clean_username(self):
        username = (
            self.cleaned_data[
                "username"
            ].strip()
        )

        if Usuario.objects.filter(
            username__iexact=username
        ).exclude(
            pk=self.instance.pk
        ).exists():
            raise ValidationError(
                "Ya existe una cuenta "
                "con este nombre de usuario."
            )

        return username

    def clean(self):
        data = super().clean()

        password1 = data.get(
            "password1"
        )

        password2 = data.get(
            "password2"
        )

        if password1 or password2:
            if password1 != password2:
                self.add_error(
                    "password2",
                    "Las contraseñas no coinciden.",
                )

            elif password1:
                candidate = Usuario(
                    username=data.get(
                        "username",
                        "",
                    ),
                    first_name=data.get(
                        "first_name",
                        "",
                    ),
                    last_name=data.get(
                        "last_name",
                        "",
                    ),
                    email=data.get(
                        "email",
                        "",
                    ),
                )

                try:
                    password_validation.validate_password(
                        password1,
                        candidate,
                    )

                except ValidationError as error:
                    self.add_error(
                        "password1",
                        error,
                    )

        return data

    def save(
        self,
        commit=True,
    ):
        user = super().save(
            commit=False
        )

        user.rol = (
            Usuario.Rol.ENCARGADO
        )

        user.is_staff = False
        user.is_superuser = False

        if self.cleaned_data.get(
            "password1"
        ):
            user.set_password(
                self.cleaned_data[
                    "password1"
                ]
            )

        if commit:
            user.save()

        return user


class HabitacionForm(
    SpanishFormMixin,
    forms.ModelForm,
):
    class Meta:
        model = Habitacion

        fields = (
            "numero",
            "capacidad",
            "orientacion",
        )

        labels = {
            "numero":
                "Número de habitación",
            "capacidad":
                "Capacidad exacta de pasajeros",
            "orientacion":
                "Orientación",
        }

        help_texts = {
            "capacidad":
                "Al asignar, debe alojarse "
                "exactamente esta cantidad "
                "de pasajeros."
        }

        widgets = {
            "capacidad":
                forms.NumberInput(
                    attrs={
                        "min": 1,
                    }
                )
        }

        error_messages = {
            "numero": {
                "unique":
                    "Ya existe una habitación "
                    "con este número, incluso "
                    "si está inactiva."
            }
        }

    def clean_numero(self):
        numero = (
            self.cleaned_data[
                "numero"
            ].strip()
        )

        if Habitacion.objects.filter(
            numero__iexact=numero
        ).exclude(
            pk=self.instance.pk
        ).exists():
            raise ValidationError(
                "Ya existe una habitación "
                "con este número, incluso "
                "si está inactiva."
            )

        return numero

    def clean_capacidad(self):
        capacidad = (
            self.cleaned_data[
                "capacidad"
            ]
        )

        if capacidad < 1:
            raise ValidationError(
                "La capacidad debe ser "
                "al menos un pasajero."
            )

        if (
            self.instance.pk
            and
            self.instance.estado
            ==
            Habitacion.Estado.OCUPADA
        ):
            previous = (
                Habitacion.objects
                .filter(
                    pk=self.instance.pk
                )
                .values_list(
                    "capacidad",
                    flat=True,
                )
                .first()
            )

            if capacidad != previous:
                raise ValidationError(
                    "No se puede cambiar la "
                    "capacidad de una habitación "
                    "ocupada. Registre la salida "
                    "primero."
                )

        return capacidad


class PasajeroForm(
    SpanishFormMixin,
    forms.ModelForm,
):
    rut = forms.CharField(
        label="RUT",
        max_length=20,
        help_text=(
            "RUT chileno con dígito "
            "verificador. "
            "Ejemplo: 12.345.678-5."
        ),
        widget=forms.TextInput(
            attrs={
                "placeholder":
                    "12.345.678-5",
            }
        ),
    )

    class Meta:
        model = Pasajero

        fields = (
            "rut",
            "nombre_completo",
            "telefono",
            "correo",
        )

        labels = {
            "rut":
                "RUT",
            "nombre_completo":
                "Nombre completo",
            "telefono":
                "Teléfono (opcional)",
            "correo":
                "Correo electrónico (opcional)",
        }

        help_texts = {
            "rut":
                "RUT chileno con dígito "
                "verificador. "
                "Ejemplo: 12.345.678-5."
        }

        widgets = {
            "rut":
                forms.TextInput(
                    attrs={
                        "placeholder":
                            "12.345.678-5",
                    }
                ),
            "telefono":
                forms.TextInput(
                    attrs={
                        "type":
                            "tel",
                    }
                ),
        }

        error_messages = {
            "rut": {
                "unique":
                    "Este RUT ya está "
                    "registrado. Utilice "
                    "el pasajero existente."
            }
        }

    def clean_rut(self):
        rut = normalizar_rut(
            self.cleaned_data[
                "rut"
            ]
        )

        if Pasajero.objects.filter(
            rut=rut
        ).exclude(
            pk=self.instance.pk
        ).exists():
            raise ValidationError(
                "Este RUT ya está registrado. "
                "Utilice el pasajero existente."
            )

        return rut

    def clean_nombre_completo(self):
        nombre = " ".join(
            self.cleaned_data[
                "nombre_completo"
            ].split()
        )

        if len(nombre) < 3:
            raise ValidationError(
                "Ingrese el nombre completo "
                "del pasajero."
            )

        return nombre


class AsignacionForm(
    SpanishFormMixin,
    forms.Form,
):
    """
    Distribución explícita.

    Costo, fechas, estado y usuario
    no son editables desde el cliente.
    """

    rooms = SafeModelMultipleChoiceField(
        label="Habitaciones",
        queryset=Habitacion.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        error_messages={
            "invalid_choice":
                "Seleccione únicamente "
                "habitaciones vacantes "
                "y activas."
        },
    )

    responsable = SafeModelChoiceField(
        label="Responsable del grupo",
        queryset=Pasajero.objects.none(),
        empty_label=(
            "Seleccione un responsable"
        ),
        error_messages={
            "invalid_choice":
                "El responsable debe ser "
                "un pasajero registrado "
                "y disponible."
        },
    )

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        rooms = (
            Habitacion.objects
            .filter(
                activa=True,
                estado=(
                    Habitacion
                    .Estado
                    .VACANTE
                ),
            )
            .order_by(
                "numero"
            )
        )

        passengers = (
            Pasajero.objects
            .exclude(
                hospedajes__activa=True
            )
            .order_by(
                "nombre_completo"
            )
            .distinct()
        )

        self.fields[
            "rooms"
        ].queryset = rooms

        self.fields[
            "responsable"
        ].queryset = passengers

        # Se crean campos para todas las
        # habitaciones disponibles.
        #
        # El servidor solamente utiliza
        # la distribución de aquellas
        # habitaciones que fueron
        # seleccionadas.

        for room in rooms:
            name = (
                f"pasajeros_{room.pk}"
            )

            self.fields[
                name
            ] = SafeModelMultipleChoiceField(
                label=(
                    "Pasajeros · "
                    f"Habitación "
                    f"{room.numero}"
                ),
                queryset=passengers,
                required=False,
                error_messages={
                    "invalid_choice":
                        "Seleccione pasajeros "
                        "registrados que no "
                        "estén hospedados."
                },
            )

    def clean(self):
        data = super().clean()

        distribution = {}

        selected = data.get(
            "rooms"
        )

        all_ids = []

        if selected is not None:
            raw_rooms = (
                self.data.getlist(
                    "rooms"
                )
                if hasattr(
                    self.data,
                    "getlist",
                )
                else
                self.data.get(
                    "rooms",
                    [],
                )
            )

            if len(
                raw_rooms
            ) != len(
                set(raw_rooms)
            ):
                self.add_error(
                    "rooms",
                    "No repita una habitación "
                    "en la distribución.",
                )

            for room in selected:
                name = (
                    f"pasajeros_{room.pk}"
                )

                raw_ids = (
                    self.data.getlist(
                        name
                    )
                    if hasattr(
                        self.data,
                        "getlist",
                    )
                    else
                    self.data.get(
                        name,
                        [],
                    )
                )

                if len(
                    raw_ids
                ) != len(
                    set(raw_ids)
                ):
                    self.add_error(
                        name,
                        "No repita un pasajero "
                        "en la misma habitación.",
                    )

                people = data.get(
                    name
                )

                if people is None:
                    continue

                ids = [
                    person.pk
                    for person in people
                ]

                distribution[
                    room.pk
                ] = ids

                all_ids.extend(
                    ids
                )

                if (
                    len(ids)
                    !=
                    room.capacidad
                ):
                    self.add_error(
                        name,
                        (
                            f"La habitación "
                            f"{room.numero} "
                            f"requiere exactamente "
                            f"{room.capacidad} "
                            f"pasajeros; "
                            f"se seleccionaron "
                            f"{len(ids)}."
                        ),
                    )

            if len(
                all_ids
            ) != len(
                set(all_ids)
            ):
                raise ValidationError(
                    "Un pasajero no puede "
                    "repetirse entre "
                    "habitaciones."
                )

            responsable = data.get(
                "responsable"
            )

            if (
                responsable
                and
                responsable.pk
                not in all_ids
            ):
                self.add_error(
                    "responsable",
                    "El responsable debe "
                    "pertenecer al grupo "
                    "distribuido en las "
                    "habitaciones.",
                )

        data[
            "distribucion"
        ] = distribution

        return data


# Alias legible para integraciones que utilizan
# el nombre genérico del módulo.
EncargadoForm = EncargadoCreationForm