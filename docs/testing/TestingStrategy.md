# Testing Strategy

All automated tests run as integration tests against a real PostgreSQL instance. We forego isolated unit tests in favor of end-to-end coverage of service layers, agents, and API routes.

## 🧪 Guiding Principles

- Use pytest exclusively with the `asyncio` plugin where needed.
- Spin up a dedicated test database (`ANGROM_TEST_DB_NAME`) on the same cluster; never mock the database.
- Each test runs inside a transaction that is rolled back after completion to preserve a clean state.
- Seed data through fixtures using the same service interfaces the application uses.
- Prefer exercising FastAPI endpoints via `httpx.AsyncClient` against the ASGI app for realistic request handling.

## 🏗️ Environment Setup

1. Ensure `.env` includes `ANGROM_TEST_DB_NAME` alongside the primary database settings.
2. Provision the test database by reusing `scripts/setup_database.py` while overriding the target database:
   ```bash
   dotenv run -- env ANGROM_DB_NAME=$ANGROM_TEST_DB_NAME python scripts/setup_database.py
   ```
3. Run Alembic migrations against the test database before executing tests (override `ANGROM_DB_NAME` or full DSN to point at `ANGROM_TEST_DB_NAME`).

## 🔁 Test Lifecycle

- `pytest` fixture `db_session`:
  - Opens a transaction, yields a SQLAlchemy session / AsyncSession.
  - Rolls back at fixture teardown.
- `app_client` fixture:
  - Uses FastAPI `TestClient` or `httpx.AsyncClient` with dependency overrides to inject the transactional session and test-specific settings.
- `seed_data` fixtures create canonical objects (users, seasons, events) via service calls.

## 📋 Test Coverage Expectations

- **Auth flows**: registration → email verification → login → magic link → logout.
- **Registration -> Pairing -> Scoring**: simulate an event lifecycle end-to-end, verifying DB state and responses.
- **Standings & Season recomputes**: ensure agents produce accurate standings and season leaderboards.
- **Notification triggers**: verify that events queue notification deliveries (actual sending can be mocked but persistence is real).
- **Maintenance jobs**: run cleanup/archive tasks against seeded data to confirm retention policies.

## ⚙️ Running Tests

```bash
dotenv run -- env ANGROM_DB_NAME=$ANGROM_TEST_DB_NAME pytest
```

Add `--maxfail=1` and `-vv` for detailed output when debugging.

## 🔒 Data Isolation & Cleanup

- Transactions ensure isolation; if long-running jobs require commit, use database savepoints or explicit cleanup steps.
- Periodically drop and recreate the test database to avoid schema drift:
  ```bash
  psql ... -c "DROP DATABASE IF EXISTS ${ANGROM_TEST_DB_NAME} WITH (FORCE);"
  ```

## 🚫 What We’re Not Doing

- No mocked repositories or unit tests without the database.
- No SQLite or in-memory substitutes; always target PostgreSQL to match production behavior.
