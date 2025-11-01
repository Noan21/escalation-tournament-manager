# Auth Models

Pydantic models supporting the custom authentication flows.

```python
from datetime import datetime
from uuid import UUID
from typing import Optional, Literal

from pydantic import BaseModel, EmailStr, Field, constr


class UserProfile(BaseModel):
    id: UUID
    username: constr(strip_whitespace=True, to_lower=True, min_length=3, max_length=50)
    email: EmailStr
    email_verified_at: Optional[datetime] = None
    roles: list[Literal["admin", "staff", "player"]] = Field(default_factory=lambda: ["player"])
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class RegisterRequest(BaseModel):
    username: constr(strip_whitespace=True, to_lower=True, min_length=3, max_length=50)
    email: EmailStr
    password: constr(min_length=12)


class LoginRequest(BaseModel):
    identifier: str  # username or email
    password: constr(min_length=1)


class AuthTokens(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["Bearer"] = "Bearer"
    expires_in: int  # seconds until access token expiry


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
```

These models integrate with the `AuthService` and FastAPI routes described in `docs/api/EndpointMap.md`. Adjust password policy or additional fields (e.g., MFA) as needs evolve.
