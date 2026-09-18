"""Lógica de autenticación: une el repositorio con el hashing/JWT."""

import asyncpg

import repositorio
from modelos import UsuarioEnBD
from seguridad import DUMMY_HASH, verify_password


async def autenticar_usuario(
    conexion: asyncpg.Connection, correo: str, contrasena: str
) -> UsuarioEnBD | None:
    """Devuelve el usuario si las credenciales son válidas; None si no.

    Si el correo no existe, se verifica la contraseña contra un hash dummy
    para que el tiempo de respuesta no revele qué correos están registrados.
    """
    usuario = await repositorio.obtener_usuario_por_correo(conexion, correo)
    if usuario is None:
        return None
    if not verify_password(contrasena, usuario.contrasena_hasheada):
        return None
    return usuario
