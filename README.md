# Autenticación web (monolito)

Ejemplo de autenticación para un monolito web con **FastAPI + Jinja2**, sesiones
con **JWT** en cookie `httpOnly`, contraseñas hasheadas con **argon2** (vía
`pwdlib`, el sucesor mantenido de `passlib`) y usuarios en **PostgreSQL**
con **asyncpg** (tabla `usuarios`).

> 📚 **Demo académica** — material docente:
> [Guía del alumno](guia_alumno.md) ·
> [Guía del profesor](guia_profesor.md)

## Puesta en marcha

```bash
cp .env-sample .env        # rellena URL_DATABASE y SECRET_KEY (openssl rand -hex 32)
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

## Despliegue en Vercel

Vercel detecta el `app` de FastAPI en `main.py` sin configuración (zero-config).

- **Dependencias**: `requirements.txt` (generado desde el lock, sin hashes):

  ```bash
  uv export --format requirements-txt --no-hashes --no-dev -o requirements.txt
  ```

- **Python**: fijado por `.python-version` (3.14).
- **Función única**: todas las rutas las sirve el `app`; el lifespan crea el
  pool de asyncpg al arrancar la instancia (Fluid compute reutiliza el proceso).
- **Estáticos**: `app.mount("/static", ...)` se promueve al CDN en el build.
- **Región**: `vercel.json` fija `iad1` (US East), junto al endpoint de Neon.

Variables a definir en el proyecto de Vercel (Settings → Environment Variables,
en Production y Preview): `URL_DATABASE` y `SECRET_KEY`.

Despliega importando el repo en [vercel.com/new](https://vercel.com/new) o con
la CLI (`vercel`, mínimo 48.1.8; para desarrollo local `vercel dev`).

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