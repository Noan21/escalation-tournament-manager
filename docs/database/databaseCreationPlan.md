# Database Creation Plan

These steps describe how to bootstrap and operate the PostgreSQL cluster using the credentials stored in `.env`. The platform runs in single-organization mode and relies on DigitalOcean’s managed PostgreSQL with a connection pool.

## 🔑 Environment Variables

The `.env` file (already present at the repo root) defines the following keys:

| Variable | Purpose |
| --- | --- |
| `ANGROM_DB_HOST` | Primary database host (DigitalOcean cluster address). |
| `ANGROM_DB_HOST_DEFAULT_DB` | Default admin database (`defaultdb`) required when connecting as the admin user. |
| `ANGROM_DB_ADMIN_PORT` | Admin port exposed by the cluster; use this with the `doadmin` account. |
| `ANGROM_DB_ADMIN` / `ANGROM_DB_PASSWORD` | Cluster admin credentials. |
| `ANGROM_DB_NAME` | Application database to create/manage (admin connectivity). |
| `ANGROM_TEST_DB_NAME` | Dedicated test database for integration tests (admin connectivity). |
| `ANGROM_DB_USER` / `ANGROM_DB_USER_PASSWORD` | Service account the app uses via the connection pool. |
| `ANGROM_APP_POOL` | Connection pool database name for the live app traffic. |
| `ANGROM_TEST_POOL` | Connection pool database name dedicated to integration tests. |
| `ANGROM_DB_POOL_PORT` | Port to reach the pool (application connections). |

Load these in your shell for ad-hoc commands with `dotenv`:

```bash
# Install the CLI helper once
pip install python-dotenv

# Use the variables for a single command (e.g., psql as admin)
dotenv run -- \
  psql "postgresql://${ANGROM_DB_ADMIN}:${ANGROM_DB_PASSWORD}@${ANGROM_DB_HOST}:${ANGROM_DB_ADMIN_PORT}/${ANGROM_DB_HOST_DEFAULT_DB}"
```

When running Python scripts, `python-dotenv` can auto-load `.env` (see scaffolding script below).

## 🧱 Admin vs Application Connections

- **Admin tasks (setup, grants, migrations)** must use the admin port (`ANGROM_DB_ADMIN_PORT`) and the `defaultdb` database specified by `ANGROM_DB_HOST_DEFAULT_DB`. This is required before the application database exists or when modifying cluster-level privileges.
- **Application traffic** must use the pool port (`ANGROM_DB_POOL_PORT`) on the same host as admin connections. Select the pool-backed database by choosing `ANGROM_APP_POOL` (or `ANGROM_TEST_POOL` for test runs).

## 🚀 Scaffolding Script

`scripts/setup_database.py` automates initial provisioning:

1. Loads `.env`.
2. Connects to the admin endpoint (`ANGROM_DB_HOST` + `ANGROM_DB_ADMIN_PORT`) against `defaultdb`.
3. Creates the target database (`ANGROM_DB_NAME`) if missing.
4. Creates or updates the service user (`ANGROM_DB_USER`) with the supplied password.
5. Grants database-level privileges to the service user.
6. Connects to the new database (still via the admin port) to:
   - enable required extensions (`pgcrypto` for UUID generation),
   - grant schema/table/sequence privileges,
   - configure default privileges so future objects are owned appropriately.

### Running the script

```bash
python -m venv .venv
source .venv/bin/activate
pip install psycopg[binary] python-dotenv
python scripts/setup_database.py
```

The script is idempotent—rerunning it will ensure passwords and grants remain current.

To scaffold the test database defined by `ANGROM_TEST_DB_NAME`, reuse the same script while overriding `ANGROM_DB_NAME` at invocation time:

```bash
dotenv run -- env ANGROM_DB_NAME=$ANGROM_TEST_DB_NAME python scripts/setup_database.py
```

## 🛠️ Post-Setup Tasks

1. **Migrations**: once Alembic migrations exist, run them with the pool connection so the DSN matches production. By default this targets `ANGROM_APP_POOL`:
   ```bash
   dotenv run -- alembic upgrade head
   ```
   For the test database, point the pool override at `ANGROM_TEST_POOL`:
   ```bash
   dotenv run -- env ANGROM_APP_POOL=$ANGROM_TEST_POOL alembic upgrade head
   ```
   When direct admin access is required, continue to use `ANGROM_DB_HOST` + `ANGROM_DB_ADMIN_PORT` and `ANGROM_DB_NAME`.
2. **Application configuration**: point the FastAPI service to the pool with a DSN like
   `postgresql+psycopg://${ANGROM_DB_USER}:${ANGROM_DB_USER_PASSWORD}@${ANGROM_DB_HOST}:${ANGROM_DB_POOL_PORT}/${ANGROM_APP_POOL}?sslmode=require`.
3. **Verification**: connect via the pool and confirm you can list tables, insert data, etc.:
   ```bash
   dotenv run -- \
     psql "postgresql://${ANGROM_DB_USER}:${ANGROM_DB_USER_PASSWORD}@${ANGROM_DB_HOST}:${ANGROM_DB_POOL_PORT}/${ANGROM_APP_POOL}?sslmode=require" \
     -c '\dt'
   ```

## 🚦 Activate Application Services

Once the database is provisioned:

1. Export the `.env` values into your process environment (or rely on `python-dotenv` in your app entrypoints).
2. Start the FastAPI backend with access to the pool connection string:
   ```bash
   ANGROM_DATABASE_URL="postgresql+psycopg://${ANGROM_DB_USER}:${ANGROM_DB_USER_PASSWORD}@${ANGROM_DB_HOST}:${ANGROM_DB_POOL_PORT}/${ANGROM_APP_POOL}?sslmode=require"
   dotenv run -- \
     uvicorn app.main:app --reload
   ```
3. Launch the Next.js frontend with the same `dotenv` wrapper so it can call the API using the correct base URL:
   ```bash
   dotenv run -- pnpm dev
   ```
4. Confirm the admin UI reflects the current season after logging in; the application will read/write via the pool credentials established above.

## ✅ Ongoing Operations

- Whenever rotating credentials, update `.env` and rerun `scripts/setup_database.py`.
- Maintenance policies (cleanup/archive/migration) operate within the application database; ensure the service account retains the necessary rights.
- Keep the `.env` file out of version control (already handled via `.gitignore`) and store the secrets securely in your deployment platform.
