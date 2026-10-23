"""Servidor WSGI multiplataforma para Hotel Duerme Bien."""

import os
import sys
from pathlib import Path

from waitress import serve


ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(
    0,
    str(ROOT),
)


os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)


from config.wsgi import application


def main():
    host = os.getenv(
        "HOST",
        "127.0.0.1",
    )

    port = int(
        os.getenv(
            "PORT",
            "8000",
        )
    )

    render_hostname = os.getenv(
        "RENDER_EXTERNAL_HOSTNAME",
        "",
    ).strip()


    server_options = {
        "host": host,
        "port": port,
        "threads": 4,
    }


    # Render termina TLS/HTTPS en su proxy
    # y reenvía la solicitud hacia Waitress.
    #
    # Waitress 3.x elimina por defecto
    # encabezados X-Forwarded-* que no
    # provengan de un proxy declarado
    # como confiable.
    #
    # En Render confiamos exclusivamente
    # en X-Forwarded-Proto para que Django
    # pueda reconocer correctamente que la
    # petición pública original usa HTTPS.
    if render_hostname:
        server_options.update(
            {
                "trusted_proxy": "*",
                "trusted_proxy_headers": {
                    "x-forwarded-proto",
                },
                "clear_untrusted_proxy_headers": True,
            }
        )


    serve(
        application,
        **server_options,
    )


if __name__ == "__main__":
    main()