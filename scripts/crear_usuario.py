"""Da de alta un usuario en la tabla `usuarios` con argon2.

Uso:
    uv run python scripts/crear_usuario.py "Nombre Apellido" correo@ejemplo.com contraseña
"""

import asyncio
import sys
from pathlib import Path

# Permite importar los módulos del proyecto (config, db, repositorio, ...)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import db  # noqa: E402
import repositorio  # noqa: E402
from seguridad import get_password_hash  # noqa: E402


async def main() -> None:
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)

    nombre_usuario, correo, contrasena = sys.argv[1:4]

    await db.crear_pool()
    try:
        # El script gestiona su propia conexión (aquí no hay dependencias)
        async with db.pool().acquire() as conexion:
            if await repositorio.obtener_usuario_por_correo(conexion, correo) is not None:
                print(f"Ya existe un usuario con el correo {correo!r}.")
                sys.exit(1)

            usuario = await repositorio.crear_usuario(
                conexion,
                nombre_usuario=nombre_usuario,
                correo=correo,
                contrasena_hasheada=get_password_hash(contrasena),
            )
            print(
                f"Usuario creado: id={usuario.id} "
                f"nombre={usuario.nombre_usuario!r} correo={usuario.correo!r}"
            )
    finally:
        await db.cerrar_pool()


asyncio.run(main())