# Guía del alumno — Autenticación web (monolito FastAPI + Jinja2)

Bienvenido/a. Este repositorio es una **demo académica**: una aplicación web
pequeña pero completa que implementa *autenticación* (quién eres) con
formulario de login, sesiones con **JWT** en cookie, contraseñas con **argon2**
y una base de datos **PostgreSQL** real.

Al terminar deberías ser capaz de:

1. Montar la app en local y explicar qué hace cada archivo.
2. Narrar el viaje completo de una petición: formulario → verificación →
   cookie → página protegida.
3. Explicar qué es un hash de contraseña y qué es un JWT, y por qué viven en
   sitios distintos.
4. Modificar la app sin romperla (ejercicios del final).

---

## 1. Requisitos previos

- Python 3.14 y [`uv`](https://docs.astral.sh/uv/) (el gestor de dependencias
  del proyecto).
- Nociones básicas de HTTP (GET/POST, códigos de estado, cookies) y de SQL.
- Una base de datos PostgreSQL. Si no tienes ninguna, crea un proyecto gratis
  en [Neon](https://neon.tech) y copia su cadena de conexión.

> **Idea clave:** esto es un *monolito*: el mismo proceso de Python sirve el
> HTML (Jinja2), el CSS y la lógica de sesión. No hay frontend ni backend
> separados, ni OAuth2: el formulario HTML clásico es el mecanismo de login.

## 2. Puesta en marcha

```bash
git clone https://github.com/jovanyvelez/javiera11-autenticacion
cd javiera11-autenticacion

# 1. Configura las variables de entorno
cp .env-sample .env
# Edita .env: URL_DATABASE (tu cadena de PostgreSQL) y SECRET_KEY.
# Para generar un buen SECRET_KEY:  openssl rand -hex 32

# 2. Crea la tabla si tu base de datos está vacía (p. ej. en Neon):
#    create table usuarios (
#        id serial primary key,
#        nombre_usuario varchar(50) not null,
#        correo varchar(255) not null,
#        contrasena_hasheada varchar(255) not null,
#        creado_en timestamptz default now()
#    );

# 3. Instala dependencias
uv sync

# 4. Crea un usuario de prueba (la contraseña nunca se guarda: se hashea)
uv run python scripts/crear_usuario.py "Tu Nombre" tu@correo.com tucontrasena

# 5. Arranca
uv run fastapi dev        # o: uv run uvicorn main:app
```

Abre <http://127.0.0.1:8000>:

- Sin sesión te redirige a `/login` (código **303**).
- Si te equivocas, el formulario vuelve a aparecer con el mensaje
  *"Correo o contraseña incorrectos."* (código **401**).
- Si aciertas, caes en la portada con tu nombre (código **200**) y el botón
  *Cerrar sesión*.

> 💡 Abre las DevTools del navegador (pestaña **Network** y
> **Application → Cookies**) y repite el login. Deberías ver: el `303` con
> cabecera `Set-Cookie: COOKIE_SESSION=...` y la cookie con las banderas
> `HttpOnly` y `SameSite=Lax`. El JWT viaja ahí dentro, no en el HTML.

## 3. Mapa del código

| Archivo | Rol | Qué aprender mirándolo |
|---|---|---|
| `config.py` | Lee `.env` (BD, `SECRET_KEY`, expiración, nombre de cookie) | Por qué la configuración no va escrita en el código |
| `modelos.py` | `Usuario` (público) y `UsuarioEnBD` (fila con hash) | Por qué el hash no debe circular por toda la app |
| `seguridad.py` | Hash argon2 y JWT (crear/validar) | `pwdlib` + `PyJWT`, claim `sub`, `exp` |
| `db.py` | Ciclo de vida del **pool** de conexiones asyncpg | Reutilizar conexiones caras (TLS + autenticación) |
| `repositorio.py` | **Solo consultas SQL**; cada función recibe la conexión | Separar "cómo se accede a los datos" del resto |
| `servicios.py` | `autenticar_usuario`: une BD y hashing | La lógica de negocio, en un solo sitio |
| `dependencias.py` | `ConexionDepend` y `usuario_actual` (cookie → usuario) | La inyección de dependencias de FastAPI |
| `vistas.py` | Rutas HTML: `/`, `/login`, `/logout` | Formularios (`Form`), cookies, redirecciones |
| `main.py` | Ensambla la app y arranca el pool en el `lifespan` | Dónde vive y cuándo muere cada cosa |
| `scripts/crear_usuario.py` | Alta de usuarios desde la terminal | Reutilizar `repositorio` fuera del servidor |

## 4. Anatomía del login (paso a paso)

Sigue el rastro con el código abierto:

1. El formulario de `templates/login.html` envía `POST /login` con
   `correo` y `contrasena` (`application/x-www-form-urlencoded`).
2. FastAPI inyecta en `entrar()` (en `vistas.py`):
   - `conexion: ConexionDepend` → una conexión del pool, prestada solo para
     esta petición (`dependencias.obtener_conexion` la devuelve al terminar).
   - `correo`, `contrasena` → parseados del formulario (`Form()`).
3. `servicios.autenticar_usuario(conexion, correo, contrasena)`:
   - Busca al usuario en la tabla `usuarios` (`repositorio.obtener_usuario_por_correo`).
   - **Si no existe**: verifica la contraseña contra `DUMMY_HASH`. ¿Por qué
     perder el tiempo con un usuario inexistente? Para que el tiempo de
     respuesta sea parecido y nadie pueda descubrir *qué correos están
     registrados* midiendo el reloj (anti-enumeración).
   - **Si existe**: `verify_password` compara con argon2.
4. Si falla: se vuelve a renderizar `login.html` con el error (status **401**).
5. Si acierta: `create_access_token({"sub": correo}, 30 min)` firma el JWT,
   y la respuesta es un **303** a `/` con `Set-Cookie`:
   `COOKIE_SESSION=<jwt>; HttpOnly; SameSite=Lax; Max-Age=1800`.
6. En cada `GET /`, la dependencia `usuario_actual`:
   lee la cookie → valida firma y expiración del JWT (`decode_access_token`)
   → recupera al usuario de la BD → devuelve el modelo público `Usuario`.
   La portada solo se renderiza si todo eso sale bien; si no, **303** a `/login`.
7. `GET /logout` borra la cookie y redirige al login.

### Conceptos que debes dominar

- **Hash de contraseña (argon2id)**: transformación unidireccional y lenta a
  propósito. La base de datos guarda `contrasena_hasheada`, jamás la contraseña.
  Verificar = repetir la transformación y comparar.
- **JWT** (`header.payload.firma`): un *vale* firmado con `SECRET_KEY`. El
  payload (`{"sub": "tu@correo.com", "exp": ...}`) **no está cifrado**: es
  Base64 legible. La firma demuestra que lo emitimos nosotros y que nadie lo
  alteró. Por eso el JWT va en una cookie `HttpOnly` (JavaScript no puede
  leerla) y no en `localStorage`.
- **Pool de conexiones**: abrir una conexión a PostgreSQL es caro; el pool
  (`db.crear_pool`, en el `lifespan` de `main.py`) abre unas pocas y las
  reutiliza. Cada petición toma una prestada y la devuelve.
- **Redirección 303 (See Other)**: tras un `POST` correcto, el navegador
  repite como `GET` en la nueva URL (patrón *POST-Redirect-GET*), evitando
  reenvíos accidentales del formulario.

## 5. Probar sin navegador (curl)

```bash
# Portada sin sesión → 303 hacia /login
curl -i http://127.0.0.1:8000/

# Login fallido → 401
curl -i -X POST -d "correo=tu@correo.com&contrasena=mal" http://127.0.0.1:8000/login

# Login correcto → 303 + Set-Cookie (guarda la cookie en un archivo)
curl -i -c cookies.txt -X POST \
  -d "correo=tu@correo.com&contrasena=laquepusiste" \
  http://127.0.0.1:8000/login

# Portada con sesión → 200 y tu nombre en el HTML
curl -b cookies.txt http://127.0.0.1:8000/

# Logout
curl -i -b cookies.txt http://127.0.0.1:8000/logout
```

## 6. Ejercicios

Hazlos en orden; cada uno indica qué archivos toca y cómo sabes que está bien.

| # | Ejercicio | Dificultad | Toca |
|---|---|---|---|
| 1 | Pon `ACCESS_TOKEN_EXPIRE_MINUTES=1` en `.env`, reinicia, inicia sesión y espera 60–90 s. Explica qué te devuelve `GET /` y por qué. | ⭐ | `.env` |
| 2 | Crea dos usuarios con `scripts/crear_usuario.py` y comprueba (con curl o navegador) que cada uno ve *su* nombre en la portada. | ⭐ | terminal |
| 3 | Añade el nombre a la cookie no… mejor: muestra en `/login` un aviso distinto cuando la sesión caducó. Pista: redirige a `/login?expirada=1` desde `usuario_actual` y lee el query param en la vista con `Annotated[str \| None, Query()]`. | ⭐⭐ | `dependencias.py`, `vistas.py`, `templates/login.html` |
| 4 | Página de **registro**: `GET /registro` (formulario) y `POST /registro` que reutilice `repositorio.crear_usuario`. Si el correo ya existe, vuelve a mostrar el formulario con error (como hace el login). | ⭐⭐ | `vistas.py`, `templates/registro.html`, `servicios.py` |
| 5 | Ruta autenticada `/perfil` que muestre además `id` y fecha de alta (`creado_en`, ya viene en `UsuarioEnBD`). Ojo: ¿qué campos tendrá que exponer el modelo `Usuario`? | ⭐⭐ | `modelos.py`, `vistas.py`, plantilla |
| 6 | `/cambiar-contrasena` (autenticada): formulario con contraseña actual + nueva; verifica la actual, guarda el hash nuevo, borra la cookie y obliga a re-login. | ⭐⭐⭐ | `repositorio.py`, `servicios.py`, `vistas.py` |
| 7 | **Avanzado**: bloquea temporalmente un correo tras 5 intentos fallidos (en memoria, con un `dict` en un módulo nuevo). Discute: ¿qué le pasa a esto en serverless? | ⭐⭐⭐ | módulo nuevo |

**Criterio de "hecho"**: la app arranca, el caso feliz y el caso de error
funcionan, y sabes *explicar por qué* con el código abierto.

## 7. Autoevaluación

Si respondes estas sin mirar, has entendido la demo:

1. ¿Por qué `usuarios.contrasena_hasheada` nunca sale de
   `repositorio.py`/`servicios.py`? ¿Qué modelo lo garantiza?
2. ¿Qué pasaría si alguien roba la base de datos pero no `SECRET_KEY`?
   ¿Y si roba `SECRET_KEY` pero no la BD?
3. Cambias `SECRET_KEY` y despliegas: ¿qué les pasa a los usuarios que estaban
   logueados? ¿Es eso un error o una característica?
4. ¿Por qué el JWT va en una cookie `HttpOnly` y no en `localStorage` ni en
   el HTML de la página?
5. ¿Para qué sirve verificar contra `DUMMY_HASH` si el usuario no existe?
6. ¿Por qué cada función de `repositorio.py` recibe la conexión como
   parámetro en vez de buscarla ella sola?
7. `pip freeze requirements.txt`… ¿funciona? ¿Qué manda en este proyecto:
   `uv.lock`, `requirements.txt` o ambos? (Pista: mira el README).

## 8. Problemas frecuentes

| Síntoma | Causa probable | Solución |
|---|---|---|
| `RuntimeError: Falta la variable de entorno URL_DATABASE` | No existe `.env` | Copia `.env-sample` a `.env` y rellénalo |
| 401 con tus credenciales | El usuario no existe en *esa* base de datos | Créalo con `scripts/crear_usuario.py` |
| 401 siempre tras desplegar en Vercel | Faltan `URL_DATABASE`/`SECRET_KEY` en las variables de entorno del proyecto | Settings → Environment Variables |
| Cambié `.env` y no pasa nada | `load_dotenv` solo corre al arrancar | Reinicia el servidor |
| `address already in use` | Otro proceso ocupa el puerto | Para el proceso viejo o usa `--port` |
| `pip`/`uvicorn` "no such file" | Uso de `uv run` con binarios no instalados | Usa `uv run uvicorn main:app` o `uv run fastapi dev` |

---

*Cualquier duda, abre el código y sigue la petición: el programa es el mejor
profesor de programación que existe.*