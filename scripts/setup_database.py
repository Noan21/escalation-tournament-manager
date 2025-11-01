#!/usr/bin/env python3
"""
Bootstrap database roles, database, and privileges for the tournament platform.

Usage:
    python scripts/setup_database.py

Prereqs:
    pip install psycopg[binary] python-dotenv
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from psycopg import connect, sql

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = REPO_ROOT / ".env"


def load_env() -> None:
    if not ENV_PATH.exists():
        raise FileNotFoundError(f"Missing .env file at {ENV_PATH}")
    load_dotenv(ENV_PATH)


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable {name} is required")
    return value


def connect_admin():
    host = require_env("ANGROM_DB_HOST")
    port = require_env("ANGROM_DB_ADMIN_PORT")
    user = require_env("ANGROM_DB_ADMIN")
    password = require_env("ANGROM_DB_PASSWORD")
    default_db = require_env("ANGROM_DB_HOST_DEFAULT_DB")

    return connect(
        host=host,
        port=port,
        user=user,
        password=password,
        dbname=default_db,
        autocommit=True,
    )


def ensure_database(cur, db_name: str):
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
    if cur.fetchone():
        print(f"[ok] database {db_name} already exists")
        return

    cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
    print(f"[create] database {db_name}")


def ensure_user(cur, username: str, password: str):
    cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (username,))
    if cur.fetchone():
        cur.execute(
            sql.SQL("ALTER USER {} WITH PASSWORD {}").format(
                sql.Identifier(username), sql.Literal(password)
            )
        )
        print(f"[alter] user {username} password updated")
        return

    cur.execute(
        sql.SQL("CREATE USER {} WITH PASSWORD {}").format(
            sql.Identifier(username), sql.Literal(password)
        ),
    )
    print(f"[create] user {username}")


def grant_database_privileges(cur, db_name: str, username: str):
    cur.execute(
        sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO {}").format(
            sql.Identifier(db_name), sql.Identifier(username)
        )
    )
    print(f"[grant] database privileges on {db_name} to {username}")


def setup_inside_database(db_name: str, username: str):
    host = require_env("ANGROM_DB_HOST")
    port = require_env("ANGROM_DB_ADMIN_PORT")
    admin_user = require_env("ANGROM_DB_ADMIN")
    admin_password = require_env("ANGROM_DB_PASSWORD")

    with connect(
        host=host,
        port=port,
        user=admin_user,
        password=admin_password,
        dbname=db_name,
        autocommit=True,
    ) as conn:
        with conn.cursor() as cur:
            # Ensure useful extensions exist
            for extension in ("pgcrypto",):
                cur.execute(
                    sql.SQL("CREATE EXTENSION IF NOT EXISTS {}").format(
                        sql.Identifier(extension)
                    )
                )

            cur.execute(
                sql.SQL("GRANT ALL PRIVILEGES ON SCHEMA public TO {}").format(
                    sql.Identifier(username)
                )
            )
            cur.execute(
                sql.SQL("ALTER USER {} IN DATABASE {} SET search_path TO public").format(
                    sql.Identifier(username), sql.Identifier(db_name)
                )
            )
            cur.execute(
                sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                    sql.Identifier(db_name), sql.Identifier(username)
                )
            )
            cur.execute(
                sql.SQL(
                    "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {}"
                ).format(sql.Identifier(username))
            )
            cur.execute(
                sql.SQL(
                    "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO {}"
                ).format(sql.Identifier(username))
            )
            cur.execute(
                sql.SQL(
                    "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
                    "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {}"
                ).format(sql.Identifier(username))
            )
            cur.execute(
                sql.SQL(
                    "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
                    "GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO {}"
                ).format(sql.Identifier(username))
            )

    print(f"[grant] schema privileges granted to {username}")


def main():
    load_env()

    db_name = require_env("ANGROM_DB_NAME")
    app_user = require_env("ANGROM_DB_USER")
    app_password = require_env("ANGROM_DB_USER_PASSWORD")

    with connect_admin() as conn:
        with conn.cursor() as cur:
            ensure_database(cur, db_name)
            ensure_user(cur, app_user, app_password)
            grant_database_privileges(cur, db_name, app_user)

    setup_inside_database(db_name, app_user)

    print("[done] database scaffolding complete")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[error] {exc}", file=sys.stderr)
        sys.exit(1)
