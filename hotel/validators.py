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


MENSAJE_TELEFONO = (
    "Ingresa un teléfono móvil chileno con el formato +569 seguido de "
    "8 dígitos. Ejemplo: +56912345678. No se admiten guiones, "
    "paréntesis ni letras."
)


def normalizar_telefono(value):
    """
    Teléfono móvil chileno: +569 seguido de exactamente 8 dígitos.

    Se aceptan espacios como separador visual (+56 9 1234 5678), que se
    eliminan al normalizar. Se rechaza cualquier otro carácter (guiones,
    paréntesis, puntos, letras), otros prefijos y otros largos.
    Un valor vacío es válido (campo opcional) y se devuelve como "".
    """
    texto = str(value or "").strip()

    if not texto:
        return ""

    if not re.fullmatch(r"\+[0-9]+(?: [0-9]+)*", texto):
        raise ValidationError(MENSAJE_TELEFONO)

    compacto = texto.replace(" ", "")

    if not re.fullmatch(r"\+569[0-9]{8}", compacto):
        raise ValidationError(MENSAJE_TELEFONO)

    return compacto


def validar_telefono(value):
    normalizar_telefono(value)


MAX_LARGO_CORREO = 254


def normalizar_correo(value):
    """
    Correo opcional: se valida el formato completo (usuario@dominio.tld),
    sin espacios, con dominio que incluya un punto y un TLD de letras.
    Un valor vacío es válido y se devuelve como "".
    """
    texto = str(value or "").strip()

    if not texto:
        return ""

    mensaje = "Ingresa un correo electrónico válido, por ejemplo nombre@dominio.cl."

    if len(texto) > MAX_LARGO_CORREO or re.search(r"\s", texto):
        raise ValidationError(mensaje)

    if not re.fullmatch(
        r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9](?:[A-Za-z0-9\-]*[A-Za-z0-9])?"
        r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9\-]*[A-Za-z0-9])?)*\.[A-Za-z]{2,}",
        texto,
    ) or ".." in texto:
        raise ValidationError(mensaje)

    local = texto.split("@", 1)[0]

    if local.startswith(".") or local.endswith(".") or len(local) > 64:
        raise ValidationError(mensaje)

    return texto.lower()


def validar_correo(value):
    normalizar_correo(value)


def validar_nombre_usuario(value):
    """
    Nombre de usuario de acceso: de 4 a 150 caracteres, solo letras sin
    tilde, números y . _ - + @, con al menos una letra.
    """
    texto = str(value or "")

    if not re.fullmatch(r"[A-Za-z0-9._@+\-]{4,150}", texto):
        raise ValidationError(
            "El usuario debe tener entre 4 y 150 caracteres y usar solo "
            "letras sin tilde, números y los símbolos . _ - + @ "
            "(sin espacios)."
        )

    if not any(c.isalpha() for c in texto):
        raise ValidationError(
            "El usuario debe incluir al menos una letra."
        )

    return texto


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
        str(value),
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
