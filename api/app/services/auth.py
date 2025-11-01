from __future__ import annotations

import logging
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Protocol

from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.core import security
from api.app.core.config import settings
from api.app.models.auth import (
    EmailVerificationToken,
    MagicLinkToken,
    Session,
    User,
)
from api.app.schemas.auth import (
    AuthTokens,
    ChangePasswordRequest,
    LoginRequest,
    MagicLinkConsumeRequest,
    MagicLinkRequest,
    RegisterRequest,
    UserProfile,
)
from api.app.services.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)

logger = logging.getLogger(__name__)


class AuthNotificationBackend(Protocol):
    async def send_verification_email(self, email: str, token: str) -> None: ...

    async def send_magic_link_email(self, email: str, token: str) -> None: ...


class ConsoleAuthNotificationBackend:
    async def send_verification_email(self, email: str, token: str) -> None:
        logger.info("Email verification token for %s: %s", email, token)

    async def send_magic_link_email(self, email: str, token: str) -> None:
        logger.info("Magic link token for %s: %s", email, token)


class AuthService:
    def __init__(
        self,
        session: AsyncSession,
        notification_backend: AuthNotificationBackend | None = None,
    ) -> None:
        self.session = session
        self.notifications = notification_backend or ConsoleAuthNotificationBackend()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def register_user(self, payload: RegisterRequest) -> UserProfile:
        username = payload.username.lower()
        email = payload.email.lower()

        existing = await self.session.execute(
            select(User).where(
                or_(
                    User.username == username,
                    User.email == email,
                )
            )
        )
        if existing.scalars().first():
            raise ConflictError("Username or email already in use")

        hashed_password = security.hash_password(payload.password)
        user = User(
            username=username,
            email=email,
            password_hash=hashed_password,
        )
        self.session.add(user)
        await self.session.flush()

        # Optional email verification is not required; mark as verified immediately.
        user.email_verified_at = datetime.now(tz=UTC)
        await self.session.commit()
        await self.session.refresh(user)
        return UserProfile.model_validate(user)

    async def verify_email(self, token: str) -> None:
        token_hash = security.hash_token(token)
        now = datetime.now(tz=UTC)

        result = await self.session.execute(
            select(EmailVerificationToken).where(EmailVerificationToken.token_hash == token_hash)
        )
        record = result.scalars().first()
        if not record:
            raise UnauthorizedError("Invalid or expired verification token")

        if record.expires_at < now:
            await self.session.delete(record)
            await self.session.commit()
            raise UnauthorizedError("Verification token has expired")

        user = await self.session.get(User, record.user_id)
        if not user:
            await self.session.delete(record)
            await self.session.commit()
            raise NotFoundError("User linked to token not found")

        user.email_verified_at = now
        await self.session.delete(record)
        await self.session.commit()

    async def authenticate_user(
        self,
        payload: LoginRequest,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> AuthTokens:
        identifier = payload.identifier.lower()
        user = await self._get_user_by_identifier(identifier)
        if not user:
            raise UnauthorizedError("Invalid credentials")

        if not security.verify_password(payload.password, user.password_hash):
            raise UnauthorizedError("Invalid credentials")

        tokens = await self._issue_session_tokens(user, user_agent=user_agent, ip_address=ip_address)
        user.last_login_at = datetime.now(tz=UTC)
        await self.session.commit()
        return tokens

    async def issue_magic_link(
        self,
        payload: MagicLinkRequest,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> None:
        email = payload.email.lower()
        result = await self.session.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        if not user:
            raise NotFoundError("No user found for that email")
        if not user.email_verified_at:
            raise ForbiddenError("Email must be verified before requesting magic link")

        await self._issue_magic_link(user, user_agent=user_agent, ip_address=ip_address)
        await self.session.commit()

    async def consume_magic_link(
        self,
        payload: MagicLinkConsumeRequest,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> AuthTokens:
        token_hash = security.hash_token(payload.token)
        now = datetime.now(tz=UTC)

        result = await self.session.execute(
            select(MagicLinkToken).where(MagicLinkToken.token_hash == token_hash)
        )
        record = result.scalars().first()
        if not record or record.consumed_at is not None:
            raise UnauthorizedError("Invalid or expired magic link")

        if record.expires_at < now:
            await self.session.delete(record)
            await self.session.commit()
            raise UnauthorizedError("Magic link has expired")

        user = await self.session.get(User, record.user_id)
        if not user:
            await self.session.delete(record)
            await self.session.commit()
            raise NotFoundError("User linked to token not found")

        record.consumed_at = now
        tokens = await self._issue_session_tokens(user, user_agent=user_agent, ip_address=ip_address)
        await self.session.commit()
        return tokens

    async def refresh_tokens(
        self,
        refresh_token: str,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> AuthTokens:
        payload = security.decode_refresh_token(refresh_token)
        if payload.get("type") != "refresh":
            raise UnauthorizedError("Invalid token type")

        user_id = payload.get("sub")
        session_id = payload.get("sid")
        if not user_id or not session_id:
            raise UnauthorizedError("Invalid refresh token")

        token_hash = security.hash_token(refresh_token)
        result = await self.session.execute(
            select(Session).where(
                and_(
                    Session.user_id == uuid.UUID(str(user_id)),
                    Session.refresh_token_hash == token_hash,
                )
            )
        )
        session_record = result.scalars().first()
        if not session_record:
            raise UnauthorizedError("Refresh session not found")

        now = datetime.now(tz=UTC)
        if session_record.expires_at < now or session_record.revoked_at is not None:
            await self.session.delete(session_record)
            await self.session.commit()
            raise UnauthorizedError("Refresh token expired")

        user = await self.session.get(User, session_record.user_id)
        if not user:
            await self.session.delete(session_record)
            await self.session.commit()
            raise NotFoundError("User linked to session not found")

        await self.session.delete(session_record)
        tokens = await self._issue_session_tokens(user, user_agent=user_agent, ip_address=ip_address)
        await self.session.commit()
        return tokens

    async def change_password(self, user_id: uuid.UUID, payload: ChangePasswordRequest) -> None:
        user = await self.session.get(User, user_id)
        if not user:
            raise NotFoundError("User not found")

        if not security.verify_password(payload.current_password, user.password_hash):
            raise UnauthorizedError("Current password is incorrect")

        user.password_hash = security.hash_password(payload.new_password)
        await self._revoke_all_sessions(user)
        await self.session.commit()

    async def logout(self, user_id: uuid.UUID, refresh_token: str) -> None:
        token_hash = security.hash_token(refresh_token)
        result = await self.session.execute(
            select(Session).where(
                and_(Session.user_id == user_id, Session.refresh_token_hash == token_hash)
            )
        )
        session_record = result.scalars().first()
        if not session_record:
            raise UnauthorizedError("Session not found")

        session_record.revoked_at = datetime.now(tz=UTC)
        await self.session.commit()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    async def _get_user_by_identifier(self, identifier: str) -> User | None:
        result = await self.session.execute(
            select(User).where(
                or_(
                    User.username == identifier,
                    User.email == identifier,
                )
            )
        )
        return result.scalars().first()

    async def _issue_email_verification(self, user: User) -> None:
        token = secrets.token_urlsafe(48)
        token_hash = security.hash_token(token)
        expires_at = datetime.now(tz=UTC) + timedelta(hours=settings.email_verification_hours)

        await self.session.execute(
            update(EmailVerificationToken)
            .where(EmailVerificationToken.user_id == user.id)
            .values(expires_at=datetime.now(tz=UTC) - timedelta(seconds=1))
        )

        record = EmailVerificationToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.session.add(record)
        await self.notifications.send_verification_email(user.email, token)

    async def _issue_magic_link(
        self,
        user: User,
        *,
        user_agent: str | None,
        ip_address: str | None,
    ) -> None:
        token = secrets.token_urlsafe(48)
        token_hash = security.hash_token(token)
        expires_at = datetime.now(tz=UTC) + timedelta(minutes=settings.magic_link_minutes)

        await self.session.execute(
            update(MagicLinkToken)
            .where(MagicLinkToken.user_id == user.id, MagicLinkToken.consumed_at.is_(None))
            .values(consumed_at=datetime.now(tz=UTC))
        )

        record = MagicLinkToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            request_ip=ip_address,
            user_agent=user_agent,
        )
        self.session.add(record)
        await self.notifications.send_magic_link_email(user.email, token)

    async def _issue_session_tokens(
        self,
        user: User,
        *,
        user_agent: str | None,
        ip_address: str | None,
    ) -> AuthTokens:
        now = datetime.now(tz=UTC)
        session_uuid = uuid.uuid4()

        access_token = security.create_access_token(str(user.id))
        refresh_token = security.create_refresh_token(str(user.id), str(session_uuid))
        refresh_hash = security.hash_token(refresh_token)

        session_record = Session(
            id=session_uuid,
            user_id=user.id,
            refresh_token_hash=refresh_hash,
            device_name=user_agent,
            ip_address=ip_address,
            expires_at=now + timedelta(days=settings.refresh_token_days),
        )
        self.session.add(session_record)

        expires_in_seconds = settings.access_token_minutes * 60
        return AuthTokens(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=expires_in_seconds,
        )

    async def _revoke_all_sessions(self, user: User) -> None:
        now = datetime.now(tz=UTC)
        await self.session.execute(
            update(Session)
            .where(and_(Session.user_id == user.id, Session.revoked_at.is_(None)))
            .values(revoked_at=now)
        )


__all__ = ["AuthService", "AuthNotificationBackend", "ConsoleAuthNotificationBackend"]
