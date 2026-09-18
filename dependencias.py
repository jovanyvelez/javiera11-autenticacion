"""Dependencias compartidas de FastAPI (inyección de dependencias)."""

from collections.abc import AsyncIterator
from typing import Annotated

import asyncpg
from fastapi import Depends, HTTPException, Request

import config
import db
import repositorio
from modelos import Usuario
from seguridad import decode_access_token


async def obtener_conexion() -> AsyncIterator[asyncpg.Connection]:
    """Toma una conexión del pool y la libera al terminar la petición.

    FastAPI la ejecuta una vez por petición y reutiliza el resultado en
    todas las dependencias que la necesiten (use_cache).
    """
    async with db.pool().acquire() as conexion:
        yield conexion


ConexionDepend = Annotated[asyncpg.Connection, Depends(obtener_conexion)]


async def usuario_actual(request: Request, conexion: ConexionDepend) -> Usuario:
    """Resuelve el usuario autenticado a partir de la cookie de sesión.

    No basta con que
    exista la cookie; se valida el JWT, se extrae el correo del claim `sub`
    y se comprueba que el usuario siga existiendo en la base de datos.
    Si algo falla, se redirige a /login con 303.
    """
    token = request.cookies.get(config.COOKIE_SESSION)
    if token is None:
        raise HTTPException(status_code=303, headers={"Location": "/login"})

    # Payload del JWT: {'sub': 'prueba@example.com', 'exp': 1789745617}
    payload = decode_access_token(token)

    correo = payload.get("sub") if payload else None

    if not isinstance(correo, str):
        raise HTTPException(status_code=303, headers={"Location": "/login"})

    usuario_bd = await repositorio.obtener_usuario_por_correo(conexion, correo)
    if usuario_bd is None:
        raise HTTPException(status_code=303, headers={"Location": "/login"})

    # Se devuelve el modelo público: el hash de la contraseña no circula
    # por la aplicación más allá de este punto.
    return Usuario.model_validate(usuario_bd)


UserDepend = Annotated[Usuario, Depends(usuario_actual)]
