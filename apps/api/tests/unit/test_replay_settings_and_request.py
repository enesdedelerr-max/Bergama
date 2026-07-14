"""Replay settings and request validation (#308)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from app.core.config import AppSettings
from app.core.replay_settings import ReplaySettings
from app.market_data.replay.errors import ReplayUnboundedRequestError
from app.market_data.replay.models import ReplayMode, ReplayRequest, validate_replay_request
from pydantic import ValidationError


def test_replay_disabled_by_default() -> None:
    settings = ReplaySettings()
    assert settings.enabled is False
    assert settings.default_mode == "dry_run"


def test_app_settings_no_startup_replay() -> None:
    app = AppSettings(environment="test", bootstrap_auth_enabled=False)
    assert app.replay.enabled is False
    assert "replay" in AppSettings.model_fields


def test_invalid_checkpoint_path_rejected() -> None:
    with pytest.raises(ValidationError):
        ReplaySettings(enabled=True, checkpoint_directory="../escape")
    with pytest.raises(ValidationError):
        ReplaySettings(enabled=True, checkpoint_directory="/etc/passwd")
    with pytest.raises(ValidationError):
        ReplaySettings(enabled=True, checkpoint_directory="relative/path")


def test_enabled_requires_checkpoint_directory() -> None:
    with pytest.raises(ValidationError):
        ReplaySettings(enabled=True, checkpoint_enabled=True, checkpoint_directory=None)


def test_default_mode_cannot_be_side_effect_when_enabled(tmp_path: object) -> None:
    from pathlib import Path

    directory = Path(tmp_path) / "ck"  # type: ignore[arg-type]
    directory.mkdir()
    with pytest.raises(ValidationError):
        ReplaySettings(
            enabled=True,
            default_mode="republish",
            checkpoint_directory=str(directory.resolve()),
        )


def test_request_requires_bounded_utc_range() -> None:
    start = datetime(2026, 7, 13, 12, 0, tzinfo=UTC)
    end = start + timedelta(hours=1)
    req = ReplayRequest(start_time=start, end_time=end, max_records=10, mode=ReplayMode.DRY_RUN)
    assert req.start_time < req.end_time

    with pytest.raises(ValidationError):
        ReplayRequest(start_time=end, end_time=start, max_records=10, mode=ReplayMode.DRY_RUN)
    with pytest.raises(ValidationError):
        ReplayRequest(
            start_time=datetime(2026, 7, 13, 12, 0),
            end_time=end,
            max_records=10,
            mode=ReplayMode.DRY_RUN,
        )


def test_max_records_and_batch_caps() -> None:
    start = datetime(2026, 7, 13, tzinfo=UTC)
    end = start + timedelta(days=1)
    settings = ReplaySettings(max_records=100, max_batch_size=50, default_batch_size=10)
    req = ReplayRequest(
        start_time=start,
        end_time=end,
        max_records=101,
        batch_size=51,
        mode=ReplayMode.DRY_RUN,
    )
    with pytest.raises(ReplayUnboundedRequestError):
        validate_replay_request(req, settings)


def test_arbitrary_event_type_rejected() -> None:
    start = datetime(2026, 7, 13, tzinfo=UTC)
    end = start + timedelta(hours=1)
    with pytest.raises(ValidationError):
        ReplayRequest(
            start_time=start,
            end_time=end,
            max_records=10,
            mode=ReplayMode.DRY_RUN,
            event_types=("market.unknown",),
        )


def test_extra_fields_rejected_for_sql_path_tables() -> None:
    start = datetime(2026, 7, 13, tzinfo=UTC)
    end = start + timedelta(hours=1)
    with pytest.raises(ValidationError):
        ReplayRequest.model_validate(
            {
                "start_time": start,
                "end_time": end,
                "max_records": 10,
                "mode": "dry_run",
                "sql": "SELECT * FROM market_quotes",
            }
        )
    with pytest.raises(ValidationError):
        ReplayRequest.model_validate(
            {
                "start_time": start,
                "end_time": end,
                "max_records": 10,
                "mode": "dry_run",
                "tables": ["market_quotes"],
            }
        )


def test_fingerprint_deterministic() -> None:
    start = datetime(2026, 7, 13, tzinfo=UTC)
    end = start + timedelta(hours=1)
    a = ReplayRequest(
        start_time=start,
        end_time=end,
        max_records=10,
        mode=ReplayMode.DRY_RUN,
        event_types=("market.trade", "market.quote"),
        instrument_keys=("b", "a"),
    )
    b = ReplayRequest(
        start_time=start,
        end_time=end,
        max_records=10,
        mode=ReplayMode.DRY_RUN,
        event_types=("quote", "trade"),
        instrument_keys=("a", "b"),
    )
    assert a.fingerprint(sink_type="none") == b.fingerprint(sink_type="none")
    assert a.resolved_table_bases() == ("market_quotes", "market_trades")


def test_replay_enabled_requires_iceberg_catalog() -> None:
    with pytest.raises(ValueError, match="catalog_uri"):
        AppSettings(
            environment="test",
            bootstrap_auth_enabled=False,
            replay={
                "enabled": True,
                "checkpoint_directory": "/tmp/bergama-replay-ck",
            },
        )
