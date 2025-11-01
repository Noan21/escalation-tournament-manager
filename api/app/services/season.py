from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from api.app.models.events import Event, Stage
from api.app.models.enums import StandingSubjectType
from api.app.models.standings import Standing
from api.app.models.structure import Season
from api.app.schemas.events import EventProfile, RegistrationWindow
from api.app.schemas.season import SeasonLeaderboard, SeasonLeaderboardRow
from api.app.schemas.structure import SeasonProfile
from api.app.services.exceptions import NotFoundError


class SeasonService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _load_season(self, season_id: UUID) -> Season:
        result = await self.session.execute(
            select(Season).where(Season.id == season_id)
        )
        season = result.scalar_one_or_none()
        if not season:
            raise NotFoundError("Season not found")
        return season

    async def set_current_season(self, season_id: UUID, *, actor_id: UUID) -> SeasonProfile:
        season = await self._load_season(season_id)
        await self.session.execute(update(Season).values(is_current=False))
        season.is_current = True
        await self.session.commit()
        await self.session.refresh(season)
        return SeasonProfile.model_validate(season)

    async def recompute_season_leaderboard(
        self,
        season_id: UUID,
        *,
        actor_id: UUID | None = None,
    ) -> SeasonLeaderboard:
        season = await self._load_season(season_id)
        events_result = await self.session.execute(
            select(Event.id).where(Event.season_id == season_id)
        )
        event_ids = [row[0] for row in events_result]
        if not event_ids:
            return SeasonLeaderboard(
                season_id=season_id,
                computed_at=datetime.now(tz=UTC),
                scoring_profile_key="default",
                rows=[],
            )

        stage_ids_result = await self.session.execute(
            select(Stage.id).where(Stage.event_id.in_(event_ids))
        )
        stage_ids = [row[0] for row in stage_ids_result]

        standings_result = await self.session.execute(
            select(Standing)
            .where(Standing.stage_id.in_(stage_ids))
        )
        standings = standings_result.scalars().all()

        aggregates: dict[UUID, SeasonLeaderboardRow] = {}
        for standing in standings:
            if standing.subject_type != StandingSubjectType.PARTICIPANT:
                continue
            row = aggregates.get(standing.subject_id)
            if not row:
                row = SeasonLeaderboardRow(
                    subject_id=standing.subject_id,
                    subject_type=standing.subject_type.value,
                    display_name=str(standing.subject_id),
                    events_played=0,
                    match_points=0,
                    wins=0,
                    losses=0,
                    draws=0,
                )
                aggregates[standing.subject_id] = row
            row.events_played += 1
            row.match_points += standing.match_points
            row.wins += standing.wins
            row.losses += standing.losses
            row.draws += standing.draws

        leaderboard_rows = sorted(
            aggregates.values(),
            key=lambda row: (-row.match_points, -row.wins),
        )

        return SeasonLeaderboard(
            season_id=season_id,
            computed_at=datetime.now(tz=UTC),
            scoring_profile_key="season_default",
            rows=leaderboard_rows,
        )

    async def list_season_events(self, season_id: UUID) -> list[EventProfile]:
        await self._load_season(season_id)
        events_result = await self.session.execute(
            select(Event).where(Event.season_id == season_id)
        )
        events = events_result.scalars().all()
        profiles: list[EventProfile] = []
        for event in events:
            registration_window = RegistrationWindow(
                opens_at=event.registration_opens_at,
                closes_at=event.registration_closes_at,
                waitlist_enabled=event.waitlist_enabled,
                capacity=event.registration_capacity,
                auto_promote_waitlist=event.auto_promote_waitlist,
            )
            profile = EventProfile(
                id=event.id,
                season_id=event.season_id,
                organization_id=event.organization_id,
                name=event.name,
                slug=event.slug or f"event-{event.id.hex[:10]}",
                status=event.status,
                starts_at=event.starts_at,
                ends_at=event.ends_at,
                registration=registration_window,
                default_format_key=event.default_format_key,
                default_scoring_key=event.default_scoring_key,
                location_name=event.location_name,
                location_url=event.location_url,
                max_rounds_override=event.max_rounds_override,
                published_at=event.published_at,
                meta=event.meta or {},
            )
            profiles.append(profile)
        return profiles


__all__ = ["SeasonService"]
