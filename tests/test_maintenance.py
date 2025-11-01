from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from fastapi import status

from api.app.models.auth import User
from api.app.models.events import Event, Registration
from api.app.models.enums import (
    ArchiveMode,
    CleanupTarget,
    EventStatus,
    OrganizationVisibility,
    ParticipantStatus,
    RegistrationStatus,
    RegistrationSubjectType,
    SeasonStatus,
)
from api.app.models.maintenance import ArchivePolicy, CleanupPolicy
from api.app.models.participants import Participant
from api.app.models.structure import Organization, Season


async def _bootstrap_admin(app_client, db_session):  # type: ignore[no-untyped-def]
    payload = {
        "username": "maintenance-admin",
        "email": "maintenance@example.com",
        "password": "maintenance123",
    }
    register_resp = await app_client.post("/api/auth/register", json=payload)
    assert register_resp.status_code == status.HTTP_201_CREATED
    admin_id = UUID(register_resp.json()["id"])
    admin = await db_session.get(User, admin_id)
    admin.roles = ["admin"]
    await db_session.commit()

    login_resp = await app_client.post(
        "/api/auth/login",
        json={"identifier": payload["email"], "password": payload["password"]},
    )
    assert login_resp.status_code == status.HTTP_200_OK
    tokens = login_resp.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    return admin_id, headers


@pytest.mark.asyncio
async def test_maintenance_cleanup_and_archive(app_client, db_session, seed_factory):
    _, headers = await _bootstrap_admin(app_client, db_session)

    now = datetime.now(tz=UTC)
    organization = await seed_factory(
        Organization(
            name="Maintenance Org",
            slug="maintenance-org",
            visibility=OrganizationVisibility.PUBLIC,
            contact_email="ops@example.com",
            timezone="UTC",
            meta={},
        )
    )

    season = await seed_factory(
        Season(
            organization_id=organization.id,
            name="Maintenance Season",
            slug="maintenance-season",
            year=2025,
            status=SeasonStatus.ACTIVE,
            is_current=True,
            starts_on=now - timedelta(days=30),
            ends_on=now + timedelta(days=60),
            description="Maintenance test season",
            leaderboard_url=None,
            meta={},
        )
    )

    event = await seed_factory(
        Event(
            season_id=season.id,
            organization_id=organization.id,
            name="Maintenance Event",
            slug="maintenance-event",
            status=EventStatus.COMPLETE,
            starts_at=now - timedelta(days=10),
            ends_at=now - timedelta(days=5),
            registration_opens_at=now - timedelta(days=20),
            registration_closes_at=now - timedelta(days=15),
            registration_capacity=32,
            waitlist_enabled=False,
            auto_promote_waitlist=False,
            default_format_key="swiss",
            default_scoring_key="standard",
            location_name="HQ",
            location_url=None,
            max_rounds_override=None,
            published_at=now - timedelta(days=12),
            meta={},
        )
    )

    participant = await seed_factory(
        Participant(
            organization_id=organization.id,
            display_name="Cleanup Player",
            status=ParticipantStatus.ACTIVE,
            email="cleanup@example.com",
            handles=[],
            meta={},
        )
    )

    registration = await seed_factory(
        Registration(
            event_id=event.id,
            subject_type=RegistrationSubjectType.PARTICIPANT,
            participant_id=participant.id,
            team_id=None,
            status=RegistrationStatus.PENDING,
            seeding_score=None,
            notes=None,
            registered_at=now - timedelta(days=14),
            confirmed_at=None,
            checked_in_at=None,
            meta={},
        )
    )

    cleanup_policy = await seed_factory(
        CleanupPolicy(
            organization_id=organization.id,
            target=CleanupTarget.STALE_REGISTRATIONS,
            run_every_hours=24,
            retention_days=7,
            enabled=True,
            last_run_at=None,
            meta={},
        )
    )

    archive_policy = await seed_factory(
        ArchivePolicy(
            organization_id=organization.id,
            apply_to_events_older_than_days=1,
            mode=ArchiveMode.SOFT_DELETE,
            include_event_ids=[event.id],
            exclude_event_ids=[],
            notify_contacts=False,
            enabled=True,
        )
    )

    cleanup_resp = await app_client.post(
        "/api/maintenance/run-cleanup",
        json={"targets": [CleanupTarget.STALE_REGISTRATIONS.value]},
        headers=headers,
    )
    assert cleanup_resp.status_code == status.HTTP_200_OK
    summary = cleanup_resp.json()
    assert summary["items_processed"] >= 1

    removed_registration = await db_session.get(Registration, registration.id)
    assert removed_registration is None

    archive_resp = await app_client.post(
        "/api/maintenance/run-archive",
        json={"policy_ids": [str(archive_policy.id)]},
        headers=headers,
    )
    assert archive_resp.status_code == status.HTTP_200_OK
    archived_event = await db_session.get(Event, event.id)
    assert archived_event.status == EventStatus.ARCHIVED

    migration_resp = await app_client.post(
        "/api/maintenance/run-migrations",
        json={},
        headers=headers,
    )
    assert migration_resp.status_code == status.HTTP_200_OK
