from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from .config import settings

password_hasher = PasswordHasher()


def hash_password(plain_password: str) -> str:
    return password_hasher.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return password_hasher.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False


def create_access_token(subject: str, additional_claims: dict[str, Any] | None = None) -> str:
    now = datetime.now(tz=UTC)
    exp = now + timedelta(minutes=settings.access_token_minutes)
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": exp,
        "type": "access",
        "iat": now,
    }
    if additional_claims:
        payload.update(additional_claims)
    return jwt.encode(
        payload,
        settings.jwt_access_secret,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(
    subject: str,
    session_id: str,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(tz=UTC)
    exp = now + timedelta(days=settings.refresh_token_days)
    payload: dict[str, Any] = {
        "sub": subject,
        "sid": session_id,
        "exp": exp,
        "type": "refresh",
        "iat": now,
    }
    if additional_claims:
        payload.update(additional_claims)
    return jwt.encode(
        payload,
        settings.jwt_refresh_secret,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        jwt.decode(
            token,
            settings.jwt_access_secret,
            algorithms=[settings.jwt_algorithm],
        ),
    )


def decode_refresh_token(token: str) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        jwt.decode(
            token,
            settings.jwt_refresh_secret,
            algorithms=[settings.jwt_algorithm],
        ),
    )


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
