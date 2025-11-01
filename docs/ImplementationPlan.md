# Implementation Phased Plan

Step-by-step roadmap for moving from documentation to a functioning platform.

## Phase 0 – Environment Prep
- [ ] Ensure `.env` defines `ANGROM_TEST_DB_NAME` / `ANGROM_TEST_POOL` and run `dotenv run -- env ANGROM_DB_NAME=$ANGROM_TEST_DB_NAME python scripts/setup_database.py` to provision the test database (override `ANGROM_APP_POOL=$ANGROM_TEST_POOL` when running tests).
- [x] Set up Python/Node toolchains (`python -m venv .venv`, `pnpm install` once package manifests exist).
- [x] Create a dependency manifest (`pyproject.toml` + lockfile or `requirements.txt`) capturing baseline backend packages (FastAPI, SQLAlchemy, pytest, etc.).
- [x] Configure linting/formatting (`ruff`, `black`, `mypy`, `eslint`, `prettier`) baseline configs.

## Phase 1 – Database & Models
- [x] Define SQLAlchemy models matching `docs/database/DatabaseSchema.md`.
- [x] Implement `scripts/bootstrap_schema.py` to materialize tables and apply grants.
- [x] Implement Pydantic schemas mirroring `docs/classes/`.
- [x] Add fixtures/utilities for integration tests (transactional session, seed helpers).

## Phase 2 – Auth Foundation
- [ ] Implement `AuthService` (password hashing, tokens, email verification, magic links).
- [ ] Build `/api/auth` routes and middleware for role enforcement.
- [ ] Wire email sending via placeholder adapter (console/log) pending real provider.
- [ ] Write integration tests covering register → verify → login → magic link → logout.
- [ ] Implement frontend auth hooks (`useRegister`, `useLogin`, etc.) with simple pages.

## Phase 3 – Core Domain Services
- [ ] Implement RegistrationService, PairingService, ScoringService, StandingsService, SeasonService.
- [ ] Back services with SQLAlchemy repositories + transaction management.
- [ ] Create FastAPI routers per `docs/api/EndpointMap.md` (registrations, stages, rounds, seasons, etc.).
- [ ] Add integration tests for event lifecycle (registration → pairing → scoring → standings).
- [ ] Build minimal admin UI views for managing events/stages.

## Phase 4 – Agents & Background Jobs
- [ ] Implement agent entrypoints using services (RegistrationAgent, PairingAgent, etc.).
- [ ] Integrate scheduling mechanism (e.g., APScheduler or Celery) following `docs/background/SchedulingPlan.md`.
- [ ] Expose orchestrator APIs and CLI commands.
- [ ] Add tests ensuring agents run idempotently and produce expected states.

## Phase 5 – Notifications & Maintenance
- [ ] Implement NotificationService/Agent (preference management, delivery logging).
- [ ] Integrate email/webhook providers (start with log-based stub).
- [ ] Implement MaintenanceAgent cleanup/archive routines.
- [ ] Extend frontend admin console for notifications/maintenance controls.

## Phase 6 – Frontend UX Polish
- [ ] Flesh out player-facing pages (registration, pairings, standings, season leaderboard).
- [ ] Enhance admin dashboards (event builder, round control panel, season switcher).
- [ ] Add real-time touches (polling or websocket) for pairings/standings updates.
- [ ] Apply design system (Tailwind components) and accessibility considerations.

## Phase 7 – Ops & Deployment
- [ ] Write deployment playbook (systemd services or container definitions).
- [ ] Configure Nginx reverse proxy + Cloudflare DNS.
- [ ] Set up CI pipeline (lint, type-check, integration tests).
- [ ] Prepare secrets management and environment promotion strategy (dev → staging → prod).

## Phase 8 – Launch Checklist
- [ ] Seed initial data (organization, season, admin user) via scripts or admin UI.
- [ ] Run full integration test suite against staging environment.
- [ ] Conduct manual QA of core flows with 2–3 test players.
- [ ] Finalize documentation (runbooks, onboarding, FAQ).
- [ ] Deploy to production and monitor logs/metrics during first events.

Phases can overlap, but completing early phases de-risks later work. Adjust as priorities or resources shift.
