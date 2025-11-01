#!/usr/bin/env python3
"""
Create application tables and grant privileges to the service user.

Usage:
    python scripts/bootstrap_schema.py [--database DB_NAME] [--service-user USERNAME]

Defaults:
    --database      ANGROM_DB_NAME
    --service-user  ANGROM_DB_USER
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from psycopg import connect, sql
from sqlalchemy import create_engine

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def load_env() -> None:
    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path)


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable {name} is required")
    return value


def build_sqlalchemy_engine(database: str):
    from api.app.models import Base  # imported lazily to avoid circulars

    admin_user = require_env("ANGROM_DB_ADMIN")
    admin_password = require_env("ANGROM_DB_ADMIN_PASSWORD")
    host = require_env("ANGROM_DB_HOST")
    port = require_env("ANGROM_DB_ADMIN_PORT")

    url = (
        f"postgresql+psycopg://{admin_user}:{admin_password}"
        f"@{host}:{port}/{database}?sslmode=require"
    )
    engine = create_engine(url, future=True)

    with engine.begin() as connection:
        Base.metadata.create_all(bind=connection, checkfirst=True)

    return engine


def grant_privileges(database: str, service_user: str) -> None:
    admin_user = require_env("ANGROM_DB_ADMIN")
    admin_password = require_env("ANGROM_DB_ADMIN_PASSWORD")
    host = require_env("ANGROM_DB_HOST")
    port = require_env("ANGROM_DB_ADMIN_PORT")

    with connect(
        host=host,
        port=int(port),
        dbname=database,
        user=admin_user,
        password=admin_password,
        autocommit=True,
        sslmode="require",
    ) as conn:
        with conn.cursor() as cur:
            identifier = sql.Identifier(service_user)
            cur.execute(
                sql.SQL("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {}").format(
                    identifier
                )
            )
            cur.execute(
                sql.SQL("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO {}").format(
                    identifier
                )
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap application database schema.")
    parser.add_argument(
        "--database",
        default=os.getenv("ANGROM_DB_NAME"),
        help="Target database name (defaults to ANGROM_DB_NAME).",
    )
    parser.add_argument(
        "--service-user",
        default=os.getenv("ANGROM_DB_USER"),
        help="Service user to grant privileges to (defaults to ANGROM_DB_USER).",
    )
    return parser.parse_args()


def main() -> None:
    load_env()
    args = parse_args()

    if not args.database:
        raise RuntimeError("Database name is required (--database or ANGROM_DB_NAME).")
    if not args.service_user:
        raise RuntimeError("Service user is required (--service-user or ANGROM_DB_USER).")

    build_sqlalchemy_engine(args.database)
    grant_privileges(args.database, args.service_user)
    print(f"[ok] schema ensured for database '{args.database}' and grants applied to '{args.service_user}'")


if __name__ == "__main__":
    main()
