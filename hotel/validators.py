import re

from django.core.exceptions import ValidationError


SQLITE_MAX_INTEGER = 9223372036854775807


def normalizar_rut(value):
    compact = re.sub(
        r"[.\s-]",
        "",
        str(value),
    ).upper()

    if not re.fullmatch(
        r"[1-9][0-9]{0,7}[0-9K]",
        compact,
    ):
        raise ValidationError(
            "Ingresa un RUT válido, por ejemplo 12.345.678-5."
        )

    body, dv = compact[:-1], compact[-1]

    total = sum(
        int(numero) * (2 + indice % 6)
        for indice, numero in enumerate(
            reversed(body)
        )
    )

    result = 11 - total % 11

    expected = (
        "0"
        if result == 11
        else "K"
        if result == 10
        else str(result)
    )

    if dv != expected:
        raise ValidationError(
            "El dígito verificador del RUT es incorrecto."
        )

    return f"{int(body)}-{dv}"


def validar_rut(value):
    normalizar_rut(value)


def validar_telefono(value):
    if value and not re.fullmatch(
        r"\+?[0-9 ()-]{7,20}",
        value,
    ):
        raise ValidationError(
            "Ingresa un teléfono válido de 7 a 20 caracteres."
        )


def validate_safe_positive_id(value):
    """
    Valida identificadores provenientes del cliente
    antes de utilizarlos en consultas ORM.

    Evita IDs negativos, no numéricos o mayores
    al rango soportado por SQLite INTEGER.
    """

    try:
        value = int(value)

    except (TypeError, ValueError):
        raise ValidationError(
            "El identificador ingresado no es válido."
        )

    if (
        value <= 0
        or value > SQLITE_MAX_INTEGER
    ):
        raise ValidationError(
            "El identificador ingresado no es válido."
        )

    return value


def validate_safe_id_list(values):
    """
    Valida una lista completa de identificadores
    antes de consultar la base de datos.
    """

    return [
        validate_safe_positive_id(value)
        for value in values
    ]

def validar_numero_habitacion(value):
    """
    El número de habitación es exclusivamente numérico:
    de 1 a 5 dígitos, sin letras, símbolos ni ceros iniciales.
    """
    if not re.fullmatch(
        r"[1-9][0-9]{0,4}",
        str(value).strip(),
    ):
        raise ValidationError(
            "El número de habitación debe contener solo "
            "dígitos (1 a 5), sin letras ni símbolos y "
            "sin ceros iniciales. Ejemplo: 101."
        )


def validar_nombre_persona(value, etiqueta="nombre"):
    """
    Un nombre de persona debe contener letras. No se aceptan nombres
    formados solo por números ni dígitos o símbolos mezclados con el
    nombre. Se permiten letras (con tildes y ñ), espacios, apóstrofe,
    guion y punto (ej.: María José O'Higgins-Pérez Jr.).
    """
    texto = " ".join(str(value or "").split())

    if not any(c.isalpha() for c in texto):
        raise ValidationError(
            f"El {etiqueta} debe contener letras; "
            "no puede estar formado solo por números "
            "ni por símbolos."
        )

    if not re.fullmatch(r"[^\W\d_]+(?:[ '\-.][^\W\d_]+)*\.?", texto):
        raise ValidationError(
            f"El {etiqueta} solo puede incluir letras, "
            "espacios, apóstrofe, guion y punto; "
            "no se admiten números ni otros símbolos."
        )

    return texto
