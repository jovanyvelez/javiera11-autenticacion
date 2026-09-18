"""Hash de contraseñas con argon2 (pwdlib) y creación/validación de JWT.

pwdlib es el sucesor mantenido de passlib (passlib dejó de funcionar en
Python >= 3.13 porque depende del módulo `crypt`, eliminado del stdlib).
Con el extra `pwdlib[argon2]`, `PasswordHash.recommended()` usa argon2id.
"""

from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

import config

password_hash = PasswordHash.recommended()

# Hash "dummy": si el usuario no existe se verifica la contraseña contra
# este hash igualmente, para que el tiempo de respuesta no delate qué
# correos están registrados en la base de datos.
DUMMY_HASH = password_hash.hash("dummypassword")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """Devuelve el payload de un JWT válido, o None si caducó o es inválido."""
    try:
        return jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
    except InvalidTokenError:
        return None