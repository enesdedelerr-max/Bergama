"""Alembic environment for Intelligence Run product persistence (WS1).

Uses synchronous SQLAlchemy + psycopg. DSN is loaded from
``BERGAMA_DATABASE__URL`` / ``AppSettings.database.url`` — never committed.
"""

from __future__ import annotations

import os

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import load_settings
from app.intelligence_runs.models import metadata

config = context.config

# Do not call logging.config.fileConfig here: Alembic runs inside the API
# process/tests and must not mutate the application root logger configuration.

target_metadata = metadata


def _database_url() -> str:
    env_url = os.environ.get("BERGAMA_DATABASE__URL")
    if env_url and env_url.strip():
        return env_url.strip()
    settings = load_settings()
    if settings.database.url is None:
        msg = (
            "BERGAMA_DATABASE__URL (or AppSettings.database.url) is required for Alembic migrations"
        )
        raise RuntimeError(msg)
    return settings.database.url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = _database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode with a sync engine."""
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = _database_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
