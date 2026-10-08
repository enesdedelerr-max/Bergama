"""Request-scoped sync Session dependency for Intelligence Run reads (WS3)."""

from __future__ import annotations

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.clock import Clock, SystemClock
from app.core.config import AppSettings
from app.deps.auth import get_app_settings
from app.deps.container import get_app_container
from app.intelligence_runs.database import create_session_factory, create_sync_engine
from app.intelligence_runs.errors import (
    IntelligenceRunInvalidPersistedRepresentationError,
    IntelligenceRunStorageUnavailableError,
)
from app.intelligence_runs.product_errors import storage_unavailable
from app.intelligence_runs.query_service import IntelligenceRunQueryService

_STATE_ENGINE_ATTR = "intelligence_runs_sync_engine"
_STATE_FACTORY_ATTR = "intelligence_runs_session_factory"


def _resolve_session_factory(request: Request, settings: AppSettings) -> sessionmaker[Session]:
    existing = getattr(request.app.state, _STATE_FACTORY_ATTR, None)
    if isinstance(existing, sessionmaker):
        return existing
    url = settings.database.url
    if url is None:
        raise storage_unavailable()
    try:
        engine = create_sync_engine(url)
        factory = create_session_factory(engine)
    except (
        IntelligenceRunStorageUnavailableError,
        IntelligenceRunInvalidPersistedRepresentationError,
    ) as exc:
        raise storage_unavailable() from exc
    setattr(request.app.state, _STATE_ENGINE_ATTR, engine)
    setattr(request.app.state, _STATE_FACTORY_ATTR, factory)
    return factory


def get_intelligence_run_session(
    request: Request,
    settings: Annotated[AppSettings, Depends(get_app_settings)],
) -> Generator[Session]:
    """Yield a request-scoped sync Session; always close; never reuse across requests."""
    factory = _resolve_session_factory(request, settings)
    session = factory()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_request_clock(request: Request) -> Clock:
    """Resolve injected clock from the application container when available."""
    try:
        return get_app_container(request).clock
    except Exception:  # noqa: BLE001 — fall back for minimal test apps
        return SystemClock()


def get_intelligence_run_query_service(
    session: Annotated[Session, Depends(get_intelligence_run_session)],
    clock: Annotated[Clock, Depends(get_request_clock)],
) -> IntelligenceRunQueryService:
    """Build a request-scoped read-only query service."""
    return IntelligenceRunQueryService(session=session, clock=clock)


def dispose_intelligence_run_engine(request: Request) -> None:
    """Dispose cached engine if present (test teardown helper)."""
    engine = getattr(request.app.state, _STATE_ENGINE_ATTR, None)
    if isinstance(engine, Engine):
        engine.dispose()
    if hasattr(request.app.state, _STATE_ENGINE_ATTR):
        delattr(request.app.state, _STATE_ENGINE_ATTR)
    if hasattr(request.app.state, _STATE_FACTORY_ATTR):
        delattr(request.app.state, _STATE_FACTORY_ATTR)
