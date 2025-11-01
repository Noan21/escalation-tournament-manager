from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from fastapi import status
from sqlalchemy import select

from api.app.models.auth import User
from api.app.models.events import Event, Match, Stage
from api.app.models.enums import (
    EventStatus,
    OrganizationVisibility,
    ParticipantStatus,
    SeasonStatus,
    StageStatus,
)
from api.app.models.participants import Participant
from api.app.models.structure import Organization, Season


@pytest.mark.asyncio
async def test_event_lifecycle(
    app_client,
    db_session,
    seed_factory,
):
    admin_payload = {
        "username": "tournament-admin",
        "email": "admin@example.com",
        "password": "verysecurepassword",
    }
    register_resp = await app_client.post("/api/auth/register", json=admin_payload)
    assert register_resp.status_code == status.HTTP_201_CREATED
    admin_id = UUID(register_resp.json()["id"])

    admin_user = await db_session.get(User, admin_id)
    admin_user.roles = ["admin", "staff"]
    await db_session.commit()

    login_resp = await app_client.post(
        "/api/auth/login",
        json={"identifier": admin_payload["email"], "password": admin_payload["password"]},
    )
    assert login_resp.status_code == status.HTTP_200_OK
    tokens = login_resp.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    organization = await seed_factory(
        Organization(
            name="Escalation League",
            slug="escalation",
            visibility=OrganizationVisibility.PUBLIC,
            contact_email="league@example.com",
            timezone="UTC",
            meta={},
        )
    )

    now = datetime.now(tz=UTC)
    season = await seed_factory(
        Season(
            organization_id=organization.id,
            name="2025 Season",
            slug="2025",
            year=2025,
            status=SeasonStatus.ACTIVE,
            is_current=True,
            starts_on=now - timedelta(days=10),
            ends_on=now + timedelta(days=60),
            description="Spring league",
            leaderboard_url=None,
            meta={},
        )
    )

    event = await seed_factory(
        Event(
            season_id=season.id,
            organization_id=organization.id,
            name="Monthly Throwdown",
            slug="monthly-throwdown",
            status=EventStatus.ACTIVE,
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=2),
            registration_opens_at=now - timedelta(days=5),
            registration_closes_at=now + timedelta(hours=6),
            registration_capacity=32,
            waitlist_enabled=False,
            auto_promote_waitlist=False,
            default_format_key="swiss",
            default_scoring_key="standard",
            location_name="HQ",
            location_url="https://example.com",
            max_rounds_override=None,
            published_at=now - timedelta(days=1),
            meta={},
        )
    )

    stage = await seed_factory(
        Stage(
            event_id=event.id,
            order=1,
            name="Swiss Stage",
            status=StageStatus.PENDING,
            format_key="swiss",
            scoring_key="standard",
            round_count=4,
            advance_top=None,
            drop_cut=None,
            start_after_stage_id=None,
            config={},
        )
    )

    participants = []
    for index in range(4):
        participant = await seed_factory(
            Participant(
                organization_id=organization.id,
                display_name=f"Player {index+1}",
                status=ParticipantStatus.ACTIVE,
                email=f"player{index+1}@example.com",
                handles=[],
                meta={},
            )
        )
        participants.append(participant)

    registration_ids: list[UUID] = []
    for participant in participants:
        payload = {
            "subject_type": "participant",
            "participant_id": str(participant.id),
        }
        create_resp = await app_client.post(
            f"/api/registrations/events/{event.id}",
            json=payload,
            headers=headers,
        )
        assert create_resp.status_code == status.HTTP_201_CREATED
        registration = create_resp.json()
        registration_ids.append(UUID(registration["id"]))

        confirm_resp = await app_client.patch(
            f"/api/registrations/{registration['id']}/status",
            json={"status": "confirmed"},
            headers=headers,
        )
        assert confirm_resp.status_code == status.HTTP_200_OK

    pairing_resp = await app_client.post(
        f"/api/orchestrator/events/{event.id}/run",
        json={"action": "generate_round", "stage_id": str(stage.id)},
        headers=headers,
    )
    assert pairing_resp.status_code == status.HTTP_200_OK
    round_profile = pairing_resp.json()
    round_id = UUID(round_profile["round_id"])

    # Idempotency check: second generate is a noop
    pairing_second = await app_client.post(
        f"/api/orchestrator/events/{event.id}/run",
        json={"action": "generate_round", "stage_id": str(stage.id)},
        headers=headers,
    )
    assert pairing_second.status_code == status.HTTP_200_OK
    assert pairing_second.json()["status"] in {"ok", "noop"}

    matches_result = await db_session.execute(select(Match).where(Match.round_id == round_id))
    matches = matches_result.scalars().all()
    assert matches, "Round generation should create matches"

    assignments = {
        str(match.id): index + 1 for index, match in enumerate(matches)
    }
    assign_payload = {
        "assignments": [
            {"match_id": match_id, "table_number": table_no}
            for match_id, table_no in assignments.items()
        ]
    }
    assign_resp = await app_client.post(
        f"/api/stages/{stage.id}/pairings/rounds/{round_id}/assign-tables",
        json=assign_payload,
        headers=headers,
    )
    assert assign_resp.status_code == status.HTTP_200_OK

    for index, match in enumerate(matches, start=1):
        if match.slot_b_participant_id is None:
            continue
        result_payload = {
            "match_id": str(match.id),
            "reported_by": str(participants[0].id),
            "wins_a": 2 if index % 2 == 1 else 1,
            "wins_b": 1 if index % 2 == 1 else 2,
            "draws": 0,
            "total_points_a": 5 if index % 2 == 1 else 3,
            "total_points_b": 3 if index % 2 == 1 else 5,
        }
        result_resp = await app_client.post(
            f"/api/matches/{match.id}/result",
            json=result_payload,
            headers=headers,
        )
        assert result_resp.status_code == status.HTTP_200_OK

    lock_resp = await app_client.post(
        f"/api/orchestrator/events/{event.id}/run",
        json={"action": "lock_round", "round_id": str(round_id)},
        headers=headers,
    )
    assert lock_resp.status_code == status.HTTP_200_OK
    # Locking a second time should be treated as noop
    lock_second = await app_client.post(
        f"/api/orchestrator/events/{event.id}/run",
        json={"action": "lock_round", "round_id": str(round_id)},
        headers=headers,
    )
    assert lock_second.status_code == status.HTTP_200_OK
    assert lock_second.json()["status"] in {"ok", "noop"}

    standings_resp = await app_client.get(
        f"/api/stages/{stage.id}/standings",
        headers=headers,
    )
    assert standings_resp.status_code == status.HTTP_200_OK
    standings = standings_resp.json()
    assert standings["rows"], "Standings should include rows"

    leaderboard_resp = await app_client.post(
        f"/api/orchestrator/events/{event.id}/run",
        json={"action": "recompute_season", "season_id": str(season.id)},
        headers=headers,
    )
    assert leaderboard_resp.status_code == status.HTTP_200_OK
    orchestration_result = leaderboard_resp.json()
    assert orchestration_result["season_id"] == str(season.id)

    leaderboard = await app_client.post(
        f"/api/seasons/{season.id}/recompute",
        headers=headers,
    )
    assert leaderboard.status_code == status.HTTP_200_OK
    assert leaderboard.json()["rows"], "Season leaderboard should aggregate standings"

    events_resp = await app_client.get(
        f"/api/seasons/{season.id}/events",
        headers=headers,
    )
    assert events_resp.status_code == status.HTTP_200_OK
    events_payload = events_resp.json()
    assert any(event_item["id"] == str(event.id) for event_item in events_payload)
