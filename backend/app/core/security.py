from datetime import datetime, timedelta, timezone
from functools import lru_cache
import secrets

import jwt
from pwdlib import PasswordHash

from app.core.config import Settings

password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


@lru_cache
def _dummy_hash() -> str:
    return hash_password(secrets.token_urlsafe(32))


def verify_password(password: str, hashed_password: str | None) -> bool:
    # Perform hashing work even when an account has no password or does not exist.
    valid = password_hasher.verify(password, hashed_password or _dummy_hash())
    return valid and hashed_password is not None


def create_access_token(user_id: int, settings: Settings) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(user_id), "iat": now,
         "exp": now + timedelta(minutes=settings.access_token_expire_minutes)},
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str, settings: Settings) -> int:
    payload = jwt.decode(
        token, settings.jwt_secret_key.get_secret_value(),
        algorithms=[settings.jwt_algorithm], options={"require": ["sub", "exp", "iat"]},
    )
    subject = payload["sub"]
    if not isinstance(subject, str) or not subject.isascii() or not subject.isdecimal():
        raise jwt.InvalidTokenError("Invalid subject")
    # The User model uses a PostgreSQL INTEGER primary key.
    if len(subject) > 10 or not 0 < int(subject) <= 2_147_483_647:
        raise jwt.InvalidTokenError("Invalid subject")
    return int(subject)
