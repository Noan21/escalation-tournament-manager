import os
from logging.config import fileConfig
from pathlib import Path
from typing import Any

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import URL

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config


def _load_dotenv() -> None:
    """Load .env if present so Alembic picks up ANGROM_* variables."""
    project_root = Path(__file__).resolve().parents[1]
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)


def _build_database_url() -> str:
    """Prefer ANGROM_DATABASE_URL; otherwise assemble from discrete vars."""
    explicit = os.getenv("ANGROM_DATABASE_URL")
    if explicit:
        return explicit

    required = {
        "ANGROM_DB_USER": os.getenv("ANGROM_DB_USER"),
        "ANGROM_DB_USER_PASSWORD": os.getenv("ANGROM_DB_USER_PASSWORD"),
        "ANGROM_HOST_POOL": os.getenv("ANGROM_HOST_POOL"),
        "ANGROM_DB_POOL_PORT": os.getenv("ANGROM_DB_POOL_PORT"),
        "ANGROM_DB_NAME": os.getenv("ANGROM_DB_NAME"),
    }

    missing = [key for key, value in required.items() if not value]
    if missing:
        raise RuntimeError(
            "Missing database environment variables for Alembic: "
            + ", ".join(missing)
        )

    return str(
        URL.create(
            "postgresql+psycopg",
            username=required["ANGROM_DB_USER"],
            password=required["ANGROM_DB_USER_PASSWORD"],
            host=required["ANGROM_HOST_POOL"],
            port=int(required["ANGROM_DB_POOL_PORT"]),  # type: ignore[arg-type]
            database=required["ANGROM_DB_NAME"],
        )
    )

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

_load_dotenv()
config.set_main_option("sqlalchemy.url", _build_database_url())

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata: Any = None

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
