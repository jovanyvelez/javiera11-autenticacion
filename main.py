"""Monolito web de autenticación: FastAPI + Jinja2 + JWT + asyncpg.

- El login es un formulario HTML clásico y la sesión viaja
  en una cookie httpOnly con un JWT firmado.
- Las contraseñas se guardan hasheadas con argon2 (pwdlib).
- Los usuarios viven en la tabla `usuarios` de PostgreSQL (asyncpg).
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

import db
from vistas import router

BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # El pool de conexiones vive lo mismo que la aplicación
    await db.crear_pool()
    yield
    await db.cerrar_pool()


app = FastAPI(title="Ejemplo autenticación", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.include_router(router)
