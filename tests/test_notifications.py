from __future__ import annotations

from uuid import UUID

import pytest
from fastapi import status
from sqlalchemy import select

from api.app.models.auth import User
from api.app.models.notifications import NotificationDelivery
from api.app.models.structure import Organization
from api.app.models.enums import NotificationStatus, OrganizationVisibility


async def _create_admin_session(app_client, db_session, seed_factory):  # type: ignore[no-untyped-def]
    admin_payload = {
        "username": "notify-admin",
        "email": "notify-admin@example.com",
        "password": "strongpassword",
    }
    register_resp = await app_client.post("/api/auth/register", json=admin_payload)
    assert register_resp.status_code == status.HTTP_201_CREATED
    admin_id = UUID(register_resp.json()["id"])

    admin_user = await db_session.get(User, admin_id)
    admin_user.roles = ["admin"]
    await db_session.commit()

    login_resp = await app_client.post(
        "/api/auth/login",
        json={"identifier": admin_payload["email"], "password": admin_payload["password"]},
    )
    assert login_resp.status_code == status.HTTP_200_OK
    tokens = login_resp.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    return admin_id, headers


@pytest.mark.asyncio
async def test_notification_preferences_dispatch(app_client, db_session, seed_factory):
    admin_id, headers = await _create_admin_session(app_client, db_session, seed_factory)

    organization = await seed_factory(
        Organization(
            name="Notify Org",
            slug="notify-org",
            visibility=OrganizationVisibility.PRIVATE,
            contact_email="notify@example.com",
            timezone="UTC",
            meta={},
        )
    )

    preference_payload = {
        "organization_id": str(organization.id),
        "subject_type": "admin",
        "subject_id": str(admin_id),
        "triggers": ["round_pairings"],
        "channels": [
            {
                "channel": "email",
                "address": "notify-admin@example.com",
                "enabled": True,
            }
        ],
    }

    upsert_resp = await app_client.post(
        "/api/notifications/preferences",
        json=preference_payload,
        headers=headers,
    )
    assert upsert_resp.status_code == status.HTTP_200_OK
    preference = upsert_resp.json()
    assert preference["triggers"] == ["round_pairings"]

    dispatch_payload = {
        "trigger": "round_pairings",
        "organization_id": str(organization.id),
        "subject": "Round Pairings Released",
        "context": {"source": "integration-test"},
    }

    dispatch_resp = await app_client.post(
        "/api/notifications/dispatch",
        json=dispatch_payload,
        headers=headers,
    )
    assert dispatch_resp.status_code == status.HTTP_200_OK
    deliveries = dispatch_resp.json()
    assert len(deliveries) == 1
    delivery = deliveries[0]
    assert delivery["message"]["subject"] == "Round Pairings Released"
    assert delivery["status"] == NotificationStatus.SENT.value

    result = await db_session.execute(select(NotificationDelivery))
    rows = result.scalars().all()
    assert rows
    assert rows[0].status == NotificationStatus.SENT
