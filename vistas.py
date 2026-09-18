"""Vistas del monolito (Jinja2): portada protegida, login y logout."""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Form, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

import config
from dependencias import ConexionDepend, UserDepend
from seguridad import create_access_token
from servicios import autenticar_usuario

templates = Jinja2Templates(directory="templates")
router = APIRouter()


@router.get("/")
async def home(request: Request, usuario: UserDepend):
    return templates.TemplateResponse(
        request=request, name="index.html", context={"usuario": usuario}
    )


@router.get("/login")
async def login(request: Request):
    return templates.TemplateResponse(
        request=request, name="login.html", context={"error": None}
    )


@router.post("/login")
async def entrar(
    request: Request,
    conexion: ConexionDepend,
    correo: Annotated[str, Form()],
    contrasena: Annotated[str, Form()],
):
    usuario = await autenticar_usuario(conexion, correo, contrasena)
    if usuario is None:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": "Correo o contraseña incorrectos."},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    token = create_access_token(
        data={"sub": usuario.correo},
        expires_delta=timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    respuesta = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    respuesta.set_cookie(
        key=config.COOKIE_SESSION,
        value=token,
        max_age=config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        samesite="lax",
        # En producción, servir la app tras HTTPS y añadir secure=True.
    )
    return respuesta


@router.get("/logout")
async def salir():
    respuesta = RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    respuesta.delete_cookie(config.COOKIE_SESSION)
    return respuesta