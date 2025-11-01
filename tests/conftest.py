from __future__ import annotations

import os
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from api.app.dependencies.auth import get_auth_notification_backend
from api.app.main import app, get_db_session
from api.app.models import Base
from api.app.services.auth import AuthNotificationBackend


def _database_url() -> str:
    """Return the async PostgreSQL URL using pool configuration."""
    user = os.environ["ANGROM_DB_USER"]
    password = os.environ["ANGROM_DB_USER_PASSWORD"]
    host = os.environ["ANGROM_DB_HOST"]
    port = os.environ["ANGROM_DB_POOL_PORT"]
    database = os.environ.get("ANGROM_APP_POOL", os.environ["ANGROM_DB_NAME"])

    return (
        "postgresql+psycopg_async://"
        f"{user}:{password}@{host}:{port}/{database}?sslmode=require"
    )


@pytest_asyncio.fixture(scope="session")
async def engine() -> AsyncIterator[AsyncEngine]:
    """Create an async engine pointed at the test database."""
    engine = create_async_engine(
        _database_url(),
        echo=False,
        poolclass=NullPool,
        pool_pre_ping=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """Yield a transactional session, rolling back after each test."""
    session_factory = async_sessionmaker(
        engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    async with engine.connect() as connection:
        transaction = await connection.begin()
        session = session_factory(bind=connection)

        await session.begin_nested()

        def _restart_savepoint(sess, trans) -> None:  # type: ignore[no-untyped-def]
            if trans.nested and not trans._parent.nested:
                sess.begin_nested()

        event.listen(session.sync_session, "after_transaction_end", _restart_savepoint)

        try:
            yield session
        finally:
            event.remove(session.sync_session, "after_transaction_end", _restart_savepoint)
            await session.close()
            await transaction.rollback()


class InMemoryAuthDispatcher(AuthNotificationBackend):
    def __init__(self) -> None:
        self.verification_tokens: dict[str, list[str]] = {}
        self.magic_link_tokens: dict[str, list[str]] = {}

    async def send_verification_email(self, email: str, token: str) -> None:
        self.verification_tokens.setdefault(email, []).append(token)

    async def send_magic_link_email(self, email: str, token: str) -> None:
        self.magic_link_tokens.setdefault(email, []).append(token)


@pytest.fixture
def auth_dispatcher() -> InMemoryAuthDispatcher:
    return InMemoryAuthDispatcher()


@pytest_asyncio.fixture
async def app_client(
    db_session: AsyncSession, auth_dispatcher: InMemoryAuthDispatcher
) -> AsyncIterator[AsyncClient]:
    """Provide an HTTP client with overridden dependencies."""

    async def override_session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db_session] = override_session
    app.dependency_overrides[get_auth_notification_backend] = lambda: auth_dispatcher

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def seed_factory(
    db_session: AsyncSession,
) -> Callable[[Any], Awaitable[Any]]:
    """Return a helper that persists a SQLAlchemy model and flushes it."""

    async def _create(model: Any) -> Any:
        db_session.add(model)
        await db_session.flush()
        return model

    return _create
