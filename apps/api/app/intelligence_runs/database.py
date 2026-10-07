"""Synchronous SQLAlchemy engine / session foundation for Intelligence Runs (WS1).

Blocking I/O must not run on an async event-loop thread. Future product HTTP
routes (WS3) must use sync FastAPI ``def`` handlers or an approved threadpool.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.intelligence_runs.errors import (
    IntelligenceRunInvalidPersistedRepresentationError,
    IntelligenceRunStorageUnavailableError,
)

_PSYCOPG_PREFIX = "postgresql+psycopg://"


def create_sync_engine(database_url: str, *, echo: bool = False) -> Engine:
    """Create a sync SQLAlchemy engine bound to psycopg 3."""
    url = database_url.strip()
    if not url.startswith(_PSYCOPG_PREFIX):
        raise IntelligenceRunInvalidPersistedRepresentationError(
            detail=(f"database URL must use sync psycopg DSN prefix {_PSYCOPG_PREFIX!r}"),
        )
    try:
        return create_engine(
            url,
            echo=echo,
            pool_pre_ping=True,
            future=True,
        )
    except Exception as exc:  # noqa: BLE001 — boundary conversion
        raise IntelligenceRunStorageUnavailableError(
            detail="failed to create PostgreSQL engine",
        ) from exc


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Return a sync sessionmaker for insert-oriented repository use."""
    return sessionmaker(
        bind=engine,
        class_=Session,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


@contextmanager
def session_scope(session_factory: sessionmaker[Session]) -> Generator[Session]:
    """Provide a transactional session scope with explicit commit/rollback."""
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
