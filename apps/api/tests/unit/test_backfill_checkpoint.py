"""Unit tests for FileBackfillCheckpointStore (#309)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.infrastructure.backfill.file_checkpoint import FileBackfillCheckpointStore
from app.market_data.backfill.checkpoint import BackfillCheckpoint
from app.market_data.backfill.errors import BackfillCheckpointCorruptError, BackfillError
from app.market_data.backfill.models import BackfillProvider, BackfillSourceKind


def _checkpoint(**overrides: object) -> BackfillCheckpoint:
    data: dict[str, object] = {
        "backfill_id": "ck-1",
        "request_fingerprint": "a" * 64,
        "provider": BackfillProvider.POLYGON,
        "source_kind": BackfillSourceKind.AGGREGATES,
        "started_at": datetime(2024, 1, 1, tzinfo=UTC),
        "updated_at": datetime(2024, 1, 1, tzinfo=UTC),
    }
    data.update(overrides)
    return BackfillCheckpoint.model_validate(data)


@pytest.mark.asyncio
async def test_atomic_roundtrip(tmp_path: Path) -> None:
    store = FileBackfillCheckpointStore(tmp_path)
    ck = _checkpoint(processed_count=3, published_count=1)
    await store.save(ck)
    loaded = await store.load("ck-1")
    assert loaded is not None
    assert loaded.processed_count == 3
    assert loaded.published_count == 1
    raw = (tmp_path / "ck-1.json").read_text(encoding="utf-8")
    payload = json.loads(raw)
    assert "api_key" not in json.dumps(payload)
    assert "Authorization" not in json.dumps(payload)
    assert "payload" not in payload
    await store.aclose()


@pytest.mark.asyncio
async def test_corrupt_fails_closed(tmp_path: Path) -> None:
    store = FileBackfillCheckpointStore(tmp_path)
    (tmp_path / "bad.json").write_text("{not-json", encoding="utf-8")
    with pytest.raises(BackfillCheckpointCorruptError):
        await store.load("bad")
    await store.aclose()


@pytest.mark.asyncio
async def test_unsafe_backfill_id_rejected(tmp_path: Path) -> None:
    store = FileBackfillCheckpointStore(tmp_path)
    with pytest.raises(BackfillError):
        await store.load("../escape")
    await store.aclose()


@pytest.mark.asyncio
async def test_relative_directory_rejected() -> None:
    with pytest.raises(BackfillError):
        FileBackfillCheckpointStore("relative-ck")
