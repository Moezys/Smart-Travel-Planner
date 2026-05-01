"""Password hashing and JWT helpers.

Kept stateless — no DB calls here.  The route handlers combine these
functions with DB lookups to authenticate users.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from app.config import get_settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


def create_access_token(user_id: int) -> str:
    s = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=s.access_token_expire_minutes
    )
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(
        payload,
        s.jwt_secret_key.get_secret_value(),
        algorithm=s.jwt_algorithm,
    )


def decode_token(token: str) -> int:
    """Decode a JWT and return the user_id (sub).  Raises JWTError on failure."""
    s = get_settings()
    payload = jwt.decode(
        token,
        s.jwt_secret_key.get_secret_value(),
        algorithms=[s.jwt_algorithm],
    )
    return int(payload["sub"])
