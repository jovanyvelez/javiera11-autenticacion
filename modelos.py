"""Modelos de dominio (Pydantic)."""

from datetime import datetime

from pydantic import BaseModel


class Usuario(BaseModel):
    """Datos de un usuario que pueden circular por la app (sin secretos)."""

    id: int
    nombre_usuario: str
    correo: str


class UsuarioEnBD(Usuario):
    """Fila completa de la tabla `usuarios`: añade el hash de la contraseña."""

    contrasena_hasheada: str
    creado_en: datetime | None = None