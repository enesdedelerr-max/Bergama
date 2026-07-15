"""Contract tests for Historical Backfill Pipeline (#309)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.core.config import AppSettings
from app.core.container import build_container
from app.core.environment import AppEnvironment
from app.core.secrets import SecretSettings
from app.market_data.backfill.errors import BackfillClosedError, BackfillDisabledError
from app.market_data.backfill.models import (
    BackfillCapability,
    BackfillMode,
    BackfillProvider,
    BackfillRequest,
    BackfillSourceKind,
    PolygonSelector,
    capability_for,
)
from pydantic import ValidationError
from tests.conftest import VALID_PROD_JWT_SECRET
from tests.support.backfill_helpers import build_engine, polygon_request, two_day_bar_source
from tests.support.market_data_fixtures import instrument


def test_no_exactly_once_claim_in_result_surface() -> None:
    # Result model must not expose exactly-once semantics.
    fields = set(BackfillRequest.model_fields)
    assert "exactly_once" not in fields
    assert "eos" not in fields


def test_capability_matrix_contract() -> None:
    assert (
        capability_for(BackfillProvider.POLYGON, BackfillSourceKind.AGGREGATES)
        is BackfillCapability.HISTORICAL_BACKFILL
    )
    assert (
        capability_for(BackfillProvider.FINNHUB, BackfillSourceKind.PROFILE_REFRESH)
        is BackfillCapability.BOUNDED_REFRESH
    )
    assert (
        capability_for(BackfillProvider.POLYGON, BackfillSourceKind.REALTIME)
        is BackfillCapability.UNSUPPORTED
    )
    assert (
        capability_for(BackfillProvider.SEC, BackfillSourceKind.ARCHIVES)
        is BackfillCapability.UNSUPPORTED
    )


def test_request_forbids_credentials_and_paths() -> None:
    with pytest.raises(ValidationError):
        BackfillRequest.model_validate(
            {
                "provider": "polygon",
                "source_kind": "aggregates",
                "start_time": "2024-01-01T00:00:00Z",
                "end_time": "2024-01-02T00:00:00Z",
                "max_records": 1,
                "api_key": "secret",
                "polygon": {
                    "ticker": "AAPL",
                    "instrument": instrument().model_dump(mode="json"),
                    "currency": "USD",
                    "timespan": "day",
                },
            }
        )


@pytest.mark.asyncio
async def test_fingerprint_stable_across_rerun(tmp_path: Path) -> None:
    source = two_day_bar_source()
    engine, _, _ = build_engine(tmp_path, source)
    req = polygon_request()
    r1 = await engine.run(req, backfill_id="fp-a")
    r2 = await engine.run(
        polygon_request(allow_completed_rerun=True),
        backfill_id="fp-a",
    )
    assert r1.request_fingerprint == r2.request_fingerprint
    keys1 = [e.idempotency_key for e in engine.audit_sink.events if e.backfill_id == "fp-a"]  # type: ignore[attr-defined]
    # Second run appends more audits; last two keys match first two event keys.
    events = [e for e in engine.audit_sink.events if e.decision.value.startswith("DRY_RUN")]  # type: ignore[attr-defined]
    assert len(events) >= 4
    assert events[0].idempotency_key == events[2].idempotency_key
    assert events[1].idempotency_key == events[3].idempotency_key
    await engine.aclose()
    _ = keys1


@pytest.mark.asyncio
async def test_container_no_startup_run_and_disabled_default() -> None:
    settings = AppSettings(
        environment=AppEnvironment.TEST,
        secrets=SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
    )
    container = build_container(settings)
    assert container.backfill_engine is None
    assert container.settings.backfill.enabled is False
    await container.aclose()


@pytest.mark.asyncio
async def test_engine_construct_disabled_fails() -> None:
    from app.core.backfill_settings import BackfillSettings
    from app.core.clock import FixedClock
    from app.market_data.backfill.engine import StaticSourceRegistry, build_backfill_engine
    from tests.support.market_data_fixtures import T0

    with pytest.raises(BackfillDisabledError):
        build_backfill_engine(
            BackfillSettings(enabled=False),
            clock=FixedClock(T0),
            source_registry=StaticSourceRegistry(sources={}),
        )


@pytest.mark.asyncio
async def test_close_then_run_rejected(tmp_path: Path) -> None:
    engine, _, _ = build_engine(tmp_path, two_day_bar_source())
    await engine.aclose()
    with pytest.raises(BackfillClosedError):
        await engine.run(polygon_request(), backfill_id="x")


def test_selector_summary_has_no_secrets() -> None:
    req = BackfillRequest(
        provider=BackfillProvider.POLYGON,
        source_kind=BackfillSourceKind.AGGREGATES,
        start_time=datetime(2024, 1, 1, tzinfo=UTC),
        end_time=datetime(2024, 1, 2, tzinfo=UTC),
        max_records=1,
        mode=BackfillMode.DRY_RUN,
        polygon=PolygonSelector(
            ticker="AAPL",
            instrument=instrument(),
            currency="USD",
            timespan="day",
        ),
    )
    summary = json_safe(req.selector_summary())
    assert "api_key" not in summary
    assert "authorization" not in summary.lower()


def json_safe(obj: object) -> str:
    import json

    return json.dumps(obj, default=str)
