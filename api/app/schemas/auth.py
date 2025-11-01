from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, constr


class UserProfile(BaseModel):
    id: UUID
    username: constr(strip_whitespace=True, to_lower=True, min_length=3, max_length=50)
    email: EmailStr
    email_verified_at: datetime | None = None
    roles: list[Literal["admin", "staff", "player"]] = Field(
        default_factory=lambda: ["player"]
    )
    last_login_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RegisterRequest(BaseModel):
    username: constr(strip_whitespace=True, to_lower=True, min_length=3, max_length=50)
    email: EmailStr
    password: constr(min_length=12)


class LoginRequest(BaseModel):
    identifier: str
    password: constr(min_length=1)


class AuthTokens(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["Bearer"] = "Bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class MagicLinkRequest(BaseModel):
    email: EmailStr


class MagicLinkConsumeRequest(BaseModel):
    token: str


class ChangePasswordRequest(BaseModel):
    current_password: constr(min_length=1)
    new_password: constr(min_length=12)


__all__ = [
    "AuthTokens",
    "ChangePasswordRequest",
    "LoginRequest",
    "LogoutRequest",
    "MagicLinkConsumeRequest",
    "MagicLinkRequest",
    "RefreshRequest",
    "RegisterRequest",
    "UserProfile",
]
