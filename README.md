# Autenticación web (monolito)

Ejemplo de autenticación para un monolito web con **FastAPI + Jinja2**, sesiones
con **JWT** en cookie `httpOnly`, contraseñas hasheadas con **argon2** (vía
`pwdlib`, el sucesor mantenido de `passlib`) y usuarios en **PostgreSQL**
con **asyncpg** (tabla `usuarios`).

## Puesta en marcha

```bash
cp .env-sample .env        # y rellena SECRET_KEY: openssl rand -hex 32
uv sync
uv run fastapi dev          # o: uv run uvicorn main:app
```

## Crear un usuario

```bash
uv run python scripts/crear_usuario.py "Nombre Apellido" correo@ejemplo.com contraseña
```

## Flujo

1. `GET /` — portada protegida; sin sesión redirige a `/login` (303).
2. `GET /login` — formulario; `POST /login` valida contra la tabla `usuarios`
   (correo + contrasena, con hash dummy para no filtrar correos existentes).
3. Si es válido: firma un JWT (`sub` = correo) y lo deja en la cookie
   `COOKIE_SESSION` (`httpOnly`, `SameSite=lax`, 30 min).
4. `GET /logout` — borra la cookie y vuelve al login.

## Estructura

| Archivo | Responsabilidad |
|---|---|
| `config.py` | Variables de entorno (`.env`): BD, secreto JWT, expiración |
| `modelos.py` | Modelos Pydantic (`Usuario`, `UsuarioEnBD`) |
| `seguridad.py` | Hash argon2 + crear/validar JWT |
| `db.py` | Pool de conexiones asyncpg (ciclo de vida) |
| `repositorio.py` | Consultas SQL a `usuarios`; cada función recibe la conexión |
| `servicios.py` | `autenticar_usuario` (une repositorio y hashing) |
| `dependencias.py` | `ConexionDepend` (pool→conexión) y `usuario_actual` (cookie JWT) |
| `vistas.py` | Rutas HTML: `/`, `/login`, `/logout` |
| `main.py` | Ensamblado de la app (lifespan crea/cierra el pool) |