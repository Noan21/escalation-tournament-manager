from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status

from api.app.dependencies.auth import (
    get_auth_service,
    get_current_user,
    get_current_user_profile,
    service_call,
)
from api.app.models.auth import User
from api.app.schemas.auth import (
    AuthTokens,
    ChangePasswordRequest,
    LoginRequest,
    MagicLinkConsumeRequest,
    MagicLinkRequest,
    RefreshRequest,
    RegisterRequest,
    UserProfile,
)
from api.app.services.auth import AuthService

AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
UserProfileDep = Annotated[UserProfile, Depends(get_current_user_profile)]

router = APIRouter()


def _extract_context(request: Request) -> dict[str, str | None]:
    return {
        "user_agent": request.headers.get("User-Agent"),
        "ip_address": request.client.host if request.client else None,
    }


@router.post("/register", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
async def register_user(payload: RegisterRequest, service: AuthServiceDep) -> UserProfile:
    return await service_call(service.register_user, payload)


@router.get("/verify-email", status_code=status.HTTP_204_NO_CONTENT)
async def verify_email(token: str, service: AuthServiceDep) -> Response:
    await service_call(service.verify_email, token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/login", response_model=AuthTokens)
async def login(
    payload: LoginRequest,
    request: Request,
    service: AuthServiceDep,
) -> AuthTokens:
    context = _extract_context(request)
    return await service_call(
        service.authenticate_user,
        payload,
        user_agent=context["user_agent"],
        ip_address=context["ip_address"],
    )


@router.post("/refresh", response_model=AuthTokens)
async def refresh_tokens(
    payload: RefreshRequest,
    request: Request,
    service: AuthServiceDep,
) -> AuthTokens:
    context = _extract_context(request)
    return await service_call(
        service.refresh_tokens,
        payload.refresh_token,
        user_agent=context["user_agent"],
        ip_address=context["ip_address"],
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: RefreshRequest,
    current_user: CurrentUserDep,
    service: AuthServiceDep,
) -> Response:
    await service_call(service.logout, current_user.id, payload.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/magic-link", status_code=status.HTTP_202_ACCEPTED)
async def request_magic_link(
    payload: MagicLinkRequest,
    request: Request,
    service: AuthServiceDep,
) -> Response:
    context = _extract_context(request)
    await service_call(
        service.issue_magic_link,
        payload,
        user_agent=context["user_agent"],
        ip_address=context["ip_address"],
    )
    return Response(status_code=status.HTTP_202_ACCEPTED)


@router.post("/magic-link/consume", response_model=AuthTokens)
async def consume_magic_link(
    payload: MagicLinkConsumeRequest,
    request: Request,
    service: AuthServiceDep,
) -> AuthTokens:
    context = _extract_context(request)
    return await service_call(
        service.consume_magic_link,
        payload,
        user_agent=context["user_agent"],
        ip_address=context["ip_address"],
    )


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: CurrentUserDep,
    service: AuthServiceDep,
) -> Response:
    await service_call(service.change_password, current_user.id, payload)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserProfile)
async def me(profile: UserProfileDep) -> UserProfile:
    return profile
