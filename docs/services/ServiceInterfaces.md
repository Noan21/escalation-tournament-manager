# Service Layer Interfaces

High-level interfaces for the core services. These signatures use the Pydantic models defined under `docs/classes/` and represent the contract that FastAPI endpoints and agents will consume.

## 🎫 RegistrationService

```python
class RegistrationServiceProtocol(Protocol):
    def create_registration(
        self,
        event_id: UUID,
        payload: EventRegistrationCreate,
        *,
        actor_id: UUID,
    ) -> EventRegistration: ...

    def update_registration_status(
        self,
        registration_id: UUID,
        status: RegistrationStatus,
        *,
        actor_id: UUID,
    ) -> EventRegistration: ...

    def list_event_registrations(
        self,
        event_id: UUID,
        *,
        include_waitlist: bool = False,
    ) -> list[EventRegistration]: ...

    def record_check_in(
        self,
        registration_id: UUID,
        method: CheckInMethod,
        *,
        actor_id: UUID,
        note: str | None = None,
    ) -> CheckInRecord: ...

    def seed_event_roster(
        self,
        event: EventProfile,
        *,
        actor_id: UUID,
    ) -> SeedRosterResult: ...
```

- `EventRegistrationCreate`, `EventRegistration`, `CheckInRecord` originate from `docs/classes/Players.md`.
- `SeedRosterResult` is a helper returning counts of created vs skipped records.

## 🤝 PairingService

```python
class PairingServiceProtocol(Protocol):
    def generate_round_pairings(
        self,
        stage: StageConfig,
        round_number: int,
        *,
        actor_id: UUID,
        pairing_seed: str | None = None,
    ) -> RoundProfile: ...

    def preview_pairings(
        self,
        stage: StageConfig,
        round_number: int,
        *,
        actor_id: UUID,
        pairing_seed: str | None = None,
    ) -> PairingPreview: ...

    def assign_tables(
        self,
        round_id: UUID,
        assignments: list[TableAssignment],
        *,
        actor_id: UUID,
    ) -> RoundProfile: ...
```

- `StageConfig` from `docs/classes/EventsAndStages.md`.
- `RoundProfile` from `docs/classes/RoundsAndMatches.md`.
- `PairingPreview` and `TableAssignment` are lightweight DTOs summarizing matchups before persistence.

## 🧮 ScoringService

```python
class ScoringServiceProtocol(Protocol):
    def submit_match_result(
        self,
        payload: MatchResultSubmit,
        *,
        actor_id: UUID,
    ) -> MatchProfile: ...

    def lock_round(
        self,
        round_id: UUID,
        *,
        actor_id: UUID,
    ) -> RoundProfile: ...

    def reopen_round(
        self,
        round_id: UUID,
        *,
        actor_id: UUID,
        reason: str,
    ) -> RoundProfile: ...
```

- `MatchResultSubmit` and `MatchProfile` from `docs/classes/RoundsAndMatches.md`.
- `lock_round` triggers scoring + standings updates via the ScoringAgent.

## 📈 StandingsService

```python
class StandingsServiceProtocol(Protocol):
    def compute_stage_standings(
        self,
        stage_id: UUID,
        *,
        scoring_profile: ScoringProfile,
        actor_id: UUID | None = None,
    ) -> StandingsPayload: ...

    def get_stage_standings(
        self,
        stage_id: UUID,
    ) -> StandingsPayload: ...

    def publish_stage_standings(
        self,
        stage_id: UUID,
        *,
        actor_id: UUID,
    ) -> StandingsPayload: ...
```

- `ScoringProfile` from `docs/classes/FormatAndScoring.md`.
- `StandingsPayload` from `docs/classes/StandingsAndTiebreak.md`.
- Publishing may simply flag the standings as visible and notify participants.

## 🗓️ SeasonService

```python
class SeasonServiceProtocol(Protocol):
    def set_current_season(
        self,
        season_id: UUID,
        *,
        actor_id: UUID,
    ) -> SeasonProfile: ...

    def recompute_season_leaderboard(
        self,
        season_id: UUID,
        *,
        actor_id: UUID | None = None,
    ) -> SeasonLeaderboard: ...

    def list_season_events(
        self,
        season_id: UUID,
    ) -> list[EventProfile]: ...
```

- `SeasonProfile` from `docs/classes/SeasonAndOrganization.md`.
- `SeasonLeaderboard` is a DTO summarizing aggregate standings produced by the SeasonAgent.

## 🔐 AuthService

```python
class AuthServiceProtocol(Protocol):
    def register_user(
        self,
        payload: RegisterRequest,
    ) -> UserProfile: ...

    def verify_email(
        self,
        token: str,
    ) -> None: ...

    def authenticate_user(
        self,
        identifier: str,
        password: str,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> AuthTokens: ...

    def issue_magic_link(
        self,
        email: EmailStr,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> None: ...

    def consume_magic_link(
        self,
        token: str,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> AuthTokens: ...

    def refresh_tokens(
        self,
        refresh_token: str,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> AuthTokens: ...

    def change_password(
        self,
        user_id: UUID,
        payload: ChangePasswordRequest,
    ) -> None: ...

    def logout(
        self,
        user_id: UUID,
        refresh_token: str,
    ) -> None: ...
```

- `RegisterRequest`, `UserProfile`, `AuthTokens`, `ChangePasswordRequest` defined in auth schemas (to be implemented).
- `identifier` allows username or email login.
- Methods are responsible for hashing passwords, issuing tokens, and recording sessions.

## 🧰 Cross-Cutting Notes

- Most domain service methods accept an `actor_id` for audit logging; automated tasks may pass `None`. Auth methods manage their own context via tokens.
- Interfaces are defined as `Protocol`s to allow multiple implementations (e.g., direct DB vs. cached variants).
- Agents (PairingAgent, ScoringAgent, StandingAgent, SeasonAgent, RegistrationAgent) use these services internally, ensuring all orchestration flows share consistent contracts.
