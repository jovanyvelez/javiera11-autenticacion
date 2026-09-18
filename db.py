"""Ciclo de vida del pool de conexiones asyncpg compartido por la app.

Las consultas en sí viven en `repositorio.py`.
"""

import asyncpg

import config

_pool: asyncpg.Pool | None = None


async def crear_pool() -> asyncpg.Pool:
    """Crea (una sola vez) el pool de conexiones a PostgreSQL."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            config.URL_DATABASE,
            min_size=1,
            max_size=5,
            # Cierra las conexiones inactivas tras 5 min: en serverless
            # (Vercel Fluid) la instancia puede quedar congelada y las
            # conexiones largas pueden morir en el lado de Neon.
            max_inactive_connection_lifetime=300,
        )
    return _pool


async def cerrar_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("El pool de conexiones no está inicializado")
    return _pool