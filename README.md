# Escalation Tournament Platform Scaffold

This repository provides a minimal yet extensible foundation for running year-long tournaments that mix different pairing formats and scoring systems.

## Stack

- **Frontend** – Next.js 15 (App Router) with TypeScript and Tailwind CSS (located in [`frontend/`](frontend/)).
- **Backend** – FastAPI (async) powered by SQLAlchemy 2.x and Alembic (located in [`api/`](api/)).
- **Database** – PostgreSQL 16 with UUID primary keys and JSONB for flexible metadata.
- **Tooling** – pnpm, Ruff, Black, mypy (strict), ESLint, Prettier, and pytest.
- **Runtime** – Docker Compose orchestrating the web app, API, and PostgreSQL services.
- **CI** – GitHub Actions workflow covering linting, formatting, typing, and tests across the stack.

## Getting Started

```bash
cp .env.example .env
docker compose up --build
```

The frontend is available on <http://localhost:3000> and proxies API requests to the FastAPI service on <http://localhost:8000>.

## Plugin Architecture

Pairing and scoring logic is pluggable through strategy registries defined under [`api/app/core/plugins/`](api/app/core/plugins/). Custom strategies register themselves with a key, allowing events and stages to opt into bespoke behaviour without touching core domain models.

## Database Domain

All tournament entities—from organizations and seasons to rounds, matches, and standings—are modeled in [`api/app/models/domain.py`](api/app/models/domain.py). The schema aligns with the requirements in the project brief and is Alembic-ready for migrations.

## Agents

Workflow automation lives in [`api/app/agents/`](api/app/agents/). Agents act as callable services that the Orchestrator can trigger to build rounds, compute standings, and more.

## Tests & Quality Gates

- Backend: `cd api && pip install .[dev] && ruff check . && black --check . && mypy . && pytest`
- Frontend: `cd frontend && pnpm install && pnpm lint && pnpm type-check && pnpm format`

## License

Distributed under the MIT License. See [`LICENSE`](LICENSE) for details.
