# Guía del profesor — Autenticación web (demo académica)

Material docente para la demo **javiera11-autenticacion**: un monolito
FastAPI + Jinja2 con login por formulario, sesión JWT en cookie `HttpOnly`,
contraseñas con argon2 (pwdlib) y PostgreSQL vía asyncpg (patrón repositorio
con conexión explícita). Está pensada para alumnos que ya vieron HTTP y
Python; la guía del alumno (`guia_alumno.md`) es el material que se les entrega.

---

## 1. Resultados de aprendizaje

Al finalizar la actividad, el alumnado debe ser capaz de:

- **Explicar** el flujo completo de autenticación web con sesión basada en
  cookie firmada (login → cookie → página protegida → logout).
- **Distinguir** hash de contraseña, firma (JWT) y cifrado, y ubicar cada
  pieza en el código correcto.
- **Usar** la inyección de dependencias de FastAPI para cross-cutting
  concerns (conexión a BD, usuario autenticado).
- **Organizar** el acceso a datos con un repositorio que recibe la conexión,
  y justificarlo (testeabilidad, transacciones, ausencia de estado global).
- **Desplegar** la app en Vercel con variables de entorno y entender el
  modelo serverless (lifespan, pool, cold start).

## 2. Prerrequisitos y estado inicial del repo

- Python 3.14 + `uv`; SQL básico; HTTP (GET/POST/cookies).
- El repo **funciona completo** desde el primer commit útil: es una demo que
  se recorre, se rompe y se extiende, no un esqueleto a medio hacer.
- La base de datos compartida (Neon) tiene usuarios de prueba:
  `prueba@example.com / secreto123` y `prueba2@example.com / clave456`.
  El usuario `test3@example.com` tiene un hash cuyo texto plano no se
  conoce: sirve para demostrar que *no hace falta* para nada (y para el
  punto 401 con credenciales desconocidas).

> **Recomendación logística:** que cada alumno/a cree su propio proyecto
> gratuito en Neon y ejecute el `create table usuarios (...)` que aparece en
  la guía del alumno. Así no colisionan sobre la tabla compartida y la
  rotación de credenciales del proyecto docente no les afecta.

## 3. Decisiones de diseño (y cómo defenderlas en clase)

Estas son las preguntas "por qué" que saldrán. Todas están en el código:

| Decisión | Justificación | Dónde |
|---|---|---|
| **pwdlib + argon2 y no passlib** | passlib está sin mantenimiento y roto en Python ≥3.13 (dependía del módulo `crypt` eliminado). pwdlib es el sucesor recomendado por FastAPI; mismo formato de hash argon2id | `seguridad.py` |
| **JWT en cookie `HttpOnly` y no OAuth2 ni localStorage** | Es un monolito: OAuth2 (Authorization Code) resuelve delegación de identidad entre aplicaciones, aquí sobra. La cookie `HttpOnly` + `SameSite=Lax` blinda el token frente a lectura por JS (XSS) y CSRF básico | `vistas.py` (`set_cookie`), `dependencias.py` |
| **Hash dummy cuando el correo no existe** | Iguala el tiempo de respuesta y evita enumerar correos registrados midiendo latencias | `servicios.py` |
| **Modelo `Usuario` separado de `UsuarioEnBD`** | El hash de contraseña queda confinado al repositorio/servicio; las vistas solo ven el modelo público | `modelos.py`, `dependencias.py` |
| **Repositorio que recibe la conexión** | Las consultas quedan puras y testeables (una conexión cualquiera, incluso en transacción); no hay variable global | `repositorio.py` |
| **Pool en `lifespan`** | Un pool por proceso: en local dura lo que el servidor; en serverless dura lo que la instancia (Fluid compute reutiliza el proceso, y Vercel ya soporta lifespan) | `main.py`, `db.py` |
| **Consultas parametrizadas (`$1`)** | asyncpg usa protocolo extendido: la inyección SQL se corta de raíz; no hay concatenación de strings | `repositorio.py` |
| **303 tras el POST** | Patrón POST-Redirect-GET; evita el reenvío del formulario al recargar | `vistas.py` |
| **`uv.lock` como fuente de verdad, `requirements.txt` solo para Vercel** | El lock es reproducible y con hashes; requirements.txt se *exporta* (`uv export`), nunca se congela a mano (`pip freeze` sobra en un proyecto uv) | README |

## 4. Plan de clase sugerido (4 sesiones de ~2 h)

### Sesión 1 — El monolito y el flujo de sesión
- Recorrido en navegador: `/` → redirección → login → error → acierto →
  portada → logout. Con DevTools abiertos (Network: el 303 y el `Set-Cookie`;
  Application: la cookie y sus banderas).
- Lectura guiada: `main.py`, `vistas.py`, `dependencias.py`.
- **Momento clave:** abrir `seguridad.py` y decodificar a mano el JWT de la
  cookie en [jwt.io](https://jwt.io): *firma ≠ cifrado*.
- Preguntas para lanzar: ¿dónde vive la sesión? (nada en la BD: la sesión
  *es* la cookie firmada), ¿qué pasa si roban la BD?, ¿y `SECRET_KEY`?

### Sesión 2 — Contraseñas y JWT a fondo
- `seguridad.py` línea a línea: argon2id (memoria difícil, lento a propósito),
  `DUMMY_HASH` (¿por qué computar un hash inútil? → cronometrarlo en vivo:
  es del orden de decenas de ms; suficiente para notarlo).
- Firmar/verificar tokens en el REPL de Python; cambiar `exp`; cambiar
  `SECRET_KEY` y ver cómo todos los tokens mueren.
- Ejercicios 1–3 de la guía del alumno.

### Sesión 3 — Datos: asyncpg, pool y repositorio
- De `db.py` a `repositorio.py`: qué es un pool, cuánto cuesta una conexión,
  por qué las consultas reciben la conexión.
- Cada alumno: Neon propio + `create table` + `crear_usuario.py`.
- Demostración de concurrencia: dos peticiones simultáneas usan dos
  conexiones del pool.
- Ejercicios 4–5 (registro y perfil).

### Sesión 4 — Producción y repaso
- Despliegue en Vercel (zero-config: entrypoint `main.py`, `.python-version`
  fija 3.14, `requirements.txt` exportado, `/static` promovido al CDN,
  región `iad1` junto a Neon). Variables de entorno del proyecto.
- Ver en producción: cold start (~1–2 s, argon2 importa con coste al arrancar),
  lifespan en los logs, el CSS servido desde CDN.
- Repaso con la autoevaluación de la guía del alumno; ejercicio 6–7 para
  entrega opcional.

## 5. Guion de demo rápido (10 min)

```bash
uv run uvicorn main:app --port 8000
curl -i localhost:8000/                       # 303 → /login
curl -i -X POST -d 'correo=prueba@example.com&contrasena=mala' localhost:8000/login
                                             # 401 + HTML con el error
curl -i -c /tmp/c -X POST -d 'correo=prueba@example.com&contrasena=secreto123' localhost:8000/login
                                             # 303 + Set-Cookie HttpOnly
curl -b /tmp/c localhost:8000/               # 200: "Hola, Usuario Prueba"
uv run python scripts/crear_usuario.py "Nuevo" nuevo@example.com otraclave
```

Cerrar con el detalle fino: el mensaje de error es idéntico para "correo no
existe" y para "contraseña mal", y el tiempo de respuesta también (dummy hash).

## 6. Errores frecuentes del alumnado (y diagnóstico)

| Síntoma | Diagnóstico | Remedio |
|---|---|---|
| `RuntimeError: Falta la variable de entorno URL_DATABASE` | No hay `.env` (o lo escribieron en otra carpeta) | Copiar `.env-sample` y rellenar |
| 401 siempre | Usuario creado en otra BD (¡Neon de otra persona!), o typo en el correo | `select correo from usuarios;` y reintentar |
| Editaron `.env` y no surte efecto | `load_dotenv` se ejecuta una vez al importar | Reiniciar (con `fastapi dev`, el *reload* solo vigila `.py`) |
| `uv run pip freeze requirements.txt` | Confusión pip/uv (no hay `pip` en el venv de uv; falta `>`; y requirements se exporta del lock) | `uv export --format requirements-txt --no-hashes -o requirements.txt` |
| Token manipulado "a mano" en la cookie | Prueban a cambiar el payload y olvidan la firma | Perfecto: demostración de que `decode_access_token` lo rechaza |
| En Vercel, 500 genérico | Faltan variables de entorno; `config.py` lanza al importar | Logs de la función; settings → env vars |
| Puerto 8000 ocupado | Servidor anterior sin parar | `--port` o matar el proceso |
| "¿Dónde está la tabla de sesiones?" | Confusión JWT vs sesiones de servidor | Dibujo: sesión = cookie firmada; nada en BD |

## 7. Rúbrica de evaluación sugerida

| Criterio | Peso | Qué mirar |
|---|---|---|
| Demo funcionando (login, error, portada, logout) | 30 % | Rúbrica de la sesión 1–2; rehacerlo ante el profesor/a |
| Ejercicios 4–5 (registro, perfil) | 30 % | ¿Reutilizan `repositorio`? ¿Validan correo repetido? ¿Modelo público sin hash? |
| Explicación oral del flujo y del código | 25 % | Preguntas de la autoevaluación de la guía del alumno |
| Calidad y buenas prácticas | 15 % | Sin secretos en el código, mensajes de error razonables, consultas parametrizadas, commits con sentido |

**Nivel de logro básico:** narrar el flujo y montarlo. **Avanzado:**
ejercicio 6 (cambiar contraseña invalida la sesión). **Excelencia:**
ejercicio 7 y su discusión serverless (estado en memoria ≠ serverless).

## 8. Extensión de la demo (temas de debate)

- **JWT vs sesiones de servidor:** aquí no se puede revocar un token vivo
  (salvo cambiar `SECRET_KEY`, que las mata todas). Patrón de rescate:
  *token versioning* (claim `v` + versión en la fila del usuario).
- **Por qué no OAuth2:** el monolito no delega identidad; OAuth2 añade
  complejidad sin beneficio. Contrastar con el tutorial oficial de FastAPI
  (que sí usa OAuth2PasswordBearer para APIs).
- **bcrypt vs argon2:** argon2id es resistente a GPUs (coste de memoria);
  ver `$argon2id$v=19$m=65536,t=3,p=4$...` en la columna hash.
- **Gestión de `SECRET_KEY`:** en `.env` (local) y en variables de entorno
  (Vercel); nunca en el repo. El historial de Git recuerda todo: de ahí la
  lección de `.env-sample` con placeholders.
- **Serverless y estado:** el pool vive mientras viva la instancia;
  `max_inactive_connection_lifetime` en `db.py` evita reusar conexiones
  que Neon pudo cerrar durante una congelación.

## 9. Administración de la demo

- **Crear usuarios:** `uv run python scripts/crear_usuario.py "Nombre" correo clave`
  (idempotente: avisa si el correo existe).
- **Esquema de `usuarios`:** `id` (serial), `nombre_usuario` varchar(50),
  `correo` varchar(255), `contrasena_hasheada` varchar(255), `creado_en`
  timestamptz. El DDL está en la guía del alumno (sección 2).
- **Reiniciar la tabla:** cualquier cliente SQL (`delete from usuarios where ...`).
  No hay FKs ni datos preciados; es una tabla de juguete.
- **Credenciales de la BD:** están en `.env` (gitignored). `.env-sample`
  lleva solo placeholders — **rota la contraseña de Neon** si en algún
  momento se filtró en un commit (lección recomendada para el alumnado).
- **Despliegue:** ver la sección "Despliegue en Vercel" del README; para
  revisar los trabajos, cada alumno despliega su propio fork con sus propias
  variables de entorno.

## 10. Mapa de la evaluación → evidencias

| Resultado de aprendizaje | Evidencia |
|---|---|
| Explicar el flujo de sesión | Explicación oral (sesión 4) + autoevaluación |
| Hash/firma/cifrado | Preguntas 2–3 de la autoevaluación + jwt.io en vivo |
| Dependencias de FastAPI | Ejercicio 3 (query param de sesión caducada) |
| Repositorio y datos | Ejercicios 4–5 en su propia Neon |
| Despliegue | URL de Vercel funcional con su fork |

---

*Material de la demo académica `javiera11-autenticacion`. El programa es el
mejor profesor de programación que existe; esta guía solo le pone horario.*