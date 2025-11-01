from __future__ import annotations

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.core import security
from api.app.core.database import get_db_session
from api.app.models.auth import User
from api.app.schemas.auth import UserProfile
from api.app.services.auth import (
    AuthNotificationBackend,
    AuthService,
    ConsoleAuthNotificationBackend,
)

http_bearer = HTTPBearer(auto_error=True)
CredentialsDep = Annotated[HTTPAuthorizationCredentials, Depends(http_bearer)]


def get_auth_notification_backend() -> AuthNotificationBackend:
    return ConsoleAuthNotificationBackend()


def get_auth_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    backend: Annotated[AuthNotificationBackend, Depends(get_auth_notification_backend)],
) -> AuthService:
    return AuthService(session=session, notification_backend=backend)


async def get_current_user(
    credentials: CredentialsDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    token = credentials.credentials
    try:
        payload = security.decode_access_token(token)
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing subject claim")

    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


async def get_current_user_profile(
    user: Annotated[User, Depends(get_current_user)]
) -> UserProfile:
    return UserProfile.model_validate(user)
