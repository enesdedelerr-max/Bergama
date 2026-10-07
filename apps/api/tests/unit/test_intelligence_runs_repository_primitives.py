"""Unit tests for Intelligence Run repository primitive surface (WS1)."""

from __future__ import annotations

import inspect
import uuid

import pytest
from app.intelligence_runs.errors import IntelligenceRunInvalidPersistedRepresentationError
from app.intelligence_runs.repository import (
    IntelligenceRunRepository,
    SqlAlchemyIntelligenceRunRepository,
)


def test_repository_protocol_exposes_only_ws1_primitives() -> None:
    methods = {
        name
        for name, _ in inspect.getmembers(IntelligenceRunRepository, predicate=inspect.isfunction)
    }
    # Protocol methods appear as functions in typing.Protocol runtime.
    assert "insert" in dir(IntelligenceRunRepository)
    assert "get_by_run_id" in dir(IntelligenceRunRepository)
    assert "get_by_logical_identity" in dir(IntelligenceRunRepository)
    assert "update" not in dir(SqlAlchemyIntelligenceRunRepository)
    assert "delete" not in dir(SqlAlchemyIntelligenceRunRepository)
    assert "upsert" not in dir(SqlAlchemyIntelligenceRunRepository)
    assert not hasattr(SqlAlchemyIntelligenceRunRepository, "materialize")
    assert not hasattr(SqlAlchemyIntelligenceRunRepository, "get_latest_dashboard_capable")
    del methods


def test_get_by_logical_identity_rejects_null_fingerprint() -> None:
    repo = SqlAlchemyIntelligenceRunRepository(session=object())  # type: ignore[arg-type]
    with pytest.raises(IntelligenceRunInvalidPersistedRepresentationError):
        repo.get_by_logical_identity(
            fingerprint="",  # type: ignore[arg-type]
            snapshot_contract_version="intelligence-run-productization.snapshot.v1",
        )


def test_get_by_run_id_rejects_non_uuid4() -> None:
    repo = SqlAlchemyIntelligenceRunRepository(session=object())  # type: ignore[arg-type]
    with pytest.raises(IntelligenceRunInvalidPersistedRepresentationError):
        repo.get_by_run_id(uuid.uuid1())


def test_sync_database_layer_has_no_asyncio_api() -> None:
    from app.intelligence_runs import database, repository

    assert not hasattr(database, "create_async_engine")
    source = inspect.getsource(repository)
    assert "async def" not in source
    assert "await " not in source
    db_source = inspect.getsource(database)
    assert "async def" not in db_source
    assert "AsyncSession" not in db_source
