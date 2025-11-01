from __future__ import annotations

import pytest
from fastapi import status

from tests.conftest import InMemoryAuthDispatcher


@pytest.mark.asyncio
async def test_registration_verification_and_login(app_client, auth_dispatcher: InMemoryAuthDispatcher):
    payload = {
        "username": "TestUser",
        "email": "test@example.com",
        "password": "supersecurepass",
    }
    resp = await app_client.post("/api/auth/register", json=payload)
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["email"] == payload["email"].lower()
    # Login should succeed immediately (email verification optional)
    resp = await app_client.post(
        "/api/auth/login",
        json={"identifier": payload["email"], "password": payload["password"]},
    )
    assert resp.status_code == status.HTTP_200_OK
    tokens = resp.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    # Refresh tokens
    refresh_resp = await app_client.post(
        "/api/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh_resp.status_code == status.HTTP_200_OK

    # Change password
    access_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    change_payload = {
        "current_password": payload["password"],
        "new_password": "brandnewsecurepass",
    }
    resp = await app_client.post(
        "/api/auth/change-password",
        json=change_payload,
        headers=headers,
    )
    assert resp.status_code == status.HTTP_204_NO_CONTENT

    # Old password should fail
    resp = await app_client.post(
        "/api/auth/login",
        json={"identifier": payload["email"], "password": payload["password"]},
    )
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    # New password should work
    resp = await app_client.post(
        "/api/auth/login",
        json={"identifier": payload["email"], "password": change_payload["new_password"]},
    )
    assert resp.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_magic_link_flow(app_client, auth_dispatcher: InMemoryAuthDispatcher):
    email = "magic@example.com"
    password = "magicpasswordpass"
    # Register and verify user quickly
    await app_client.post(
        "/api/auth/register",
        json={"username": "magic", "email": email, "password": password},
    )

    # Request magic link
    resp = await app_client.post(
        "/api/auth/magic-link",
        json={"email": email},
    )
    assert resp.status_code == status.HTTP_202_ACCEPTED
    token = auth_dispatcher.magic_link_tokens[email][0]

    # Consume link
    resp = await app_client.post(
        "/api/auth/magic-link/consume",
        json={"token": token},
    )
    assert resp.status_code == status.HTTP_200_OK
    tokens = resp.json()
    assert tokens["token_type"].lower() == "bearer"

    # Logout revokes session
    refresh_token = tokens["refresh_token"]
    me_resp = await app_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me_resp.status_code == status.HTTP_200_OK

    await app_client.post(
        "/api/auth/logout",
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    # Refresh should now fail
    resp = await app_client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
