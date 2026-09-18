"""Consultas SQL a la tabla `usuarios`.

Cada función recibe la conexión de forma explícita: quien llama decide si la
toma del pool (la dependencia `ConexionDepend`), la abre a mano (scripts) o
la envuelve en una transacción.
"""

import asyncpg

from modelos import UsuarioEnBD


def _a_usuario(fila: asyncpg.Record | None) -> UsuarioEnBD | None:
    if fila is None:
        return None
    return UsuarioEnBD.model_validate(dict(fila))


async def obtener_usuario_por_correo(
    conexion: asyncpg.Connection, correo: str
) -> UsuarioEnBD | None:
    fila = await conexion.fetchrow(
        "select * from usuarios where correo = $1", correo
    )
    return _a_usuario(fila)


async def crear_usuario(
    conexion: asyncpg.Connection,
    nombre_usuario: str,
    correo: str,
    contrasena_hasheada: str,
) -> UsuarioEnBD:
    fila = await conexion.fetchrow(
        """insert into usuarios (nombre_usuario, correo, contrasena_hasheada)
           values ($1, $2, $3)
           returning id, nombre_usuario, correo, contrasena_hasheada, creado_en""",
        nombre_usuario,
        correo,
        contrasena_hasheada,
    )
    usuario = _a_usuario(fila)
    if usuario is None:
        raise RuntimeError("La inserción del usuario no devolvió ninguna fila")
    return usuario