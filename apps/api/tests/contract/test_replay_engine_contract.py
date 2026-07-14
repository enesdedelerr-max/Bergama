"""Replay Engine contracts (#308)."""

from __future__ import annotations

import inspect

from app.market_data.orchestrator.ports import PublishPort
from app.market_data.replay.engine import ReplayEngine
from app.market_data.replay.models import ReplayMode, ReplayRequest
from app.market_data.replay.ports import CheckpointStore, ReplayCustomSink, ReplaySource


def test_replay_source_and_checkpoint_protocols() -> None:
    assert hasattr(ReplaySource, "fetch")
    assert hasattr(CheckpointStore, "load")
    assert hasattr(CheckpointStore, "save")


def test_custom_sink_matches_publish_port_shape() -> None:
    pub = inspect.signature(PublishPort.publish)
    custom = inspect.signature(ReplayCustomSink.publish)
    assert list(pub.parameters) == list(custom.parameters)


def test_engine_run_is_explicit() -> None:
    sig = inspect.signature(ReplayEngine.run)
    assert "request" in sig.parameters
    assert "publish_port" in sig.parameters
    assert "custom_sink" in sig.parameters


def test_default_mode_dry_run() -> None:
    assert ReplayMode.DRY_RUN.value == "dry_run"
    # ReplayRequest defaults to dry_run
    from datetime import UTC, datetime, timedelta

    start = datetime(2026, 7, 13, tzinfo=UTC)
    req = ReplayRequest(start_time=start, end_time=start + timedelta(hours=1), max_records=1)
    assert req.mode is ReplayMode.DRY_RUN
