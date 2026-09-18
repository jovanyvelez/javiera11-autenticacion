"""Configuración de la aplicación cargada desde el entorno (.env)."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Se carga con ruta absoluta para que funcione desde cualquier directorio
# de trabajo (fastapi dev, uvicorn, scripts, tests, ...).
load_dotenv(Path(__file__).resolve().parent / ".env")


def _obligatoria(nombre: str) -> str:
    valor = os.environ.get(nombre)
    if not valor:
        raise RuntimeError(
            f"Falta la variable de entorno {nombre}. "
            "Copia .env-sample a .env y complétala."
        )
    return valor


# Cadena de conexión a PostgreSQL (asyncpg), p. ej. la de Neon en .env-sample
URL_DATABASE = _obligatoria("URL_DATABASE")

# Firma del JWT. Para generar una nueva: openssl rand -hex 32
SECRET_KEY = _obligatoria("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)

# Nombre de la cookie de sesión, la que transporta el JWT
COOKIE_SESSION = "COOKIE_SESSION"