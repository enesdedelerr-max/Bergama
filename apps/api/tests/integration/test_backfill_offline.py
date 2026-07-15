"""Offline integration tests for Historical Backfill (#309) — no real network."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import pytest
from app.core.backfill_settings import BackfillSettings
from app.core.clock import FixedClock
from app.core.config import AppSettings
from app.core.container import build_container
from app.core.environment import AppEnvironment
from app.core.polygon_settings import PolygonSettings
from app.core.secrets import SecretSettings
from app.infrastructure.backfill.file_checkpoint import FileBackfillCheckpointStore
from app.infrastructure.backfill.polygon import PolygonHistoricalBackfillSource
from app.infrastructure.polygon.historical import PolygonHistoricalConnector
from app.infrastructure.polygon.http import PolygonHttpClient
from app.market_data.backfill.engine import StaticSourceRegistry, build_backfill_engine
from app.market_data.backfill.errors import BackfillSinkFailedError, BackfillTruncatedError
from app.market_data.backfill.models import (
    BackfillMode,
    BackfillProvider,
    BackfillRequest,
    BackfillSlice,
    BackfillSourceKind,
    BenzingaSelector,
    FinnhubRefreshSelector,
    FredSelector,
    SecRefreshSelector,
)
from app.market_data.backfill.policies import NoOpBackfillSleeper
from app.market_data.keys import build_idempotency_key
from pydantic import SecretStr
from tests.conftest import VALID_PROD_JWT_SECRET
from tests.support.backfill_helpers import (
    FakeBackfillSource,
    build_engine,
    polygon_request,
    two_day_bar_source,
)
from tests.support.market_data_fixtures import (
    T0,
    instrument,
    make_filing,
    make_fundamental,
    make_macro,
    make_news,
    make_reference,
)
from tests.support.recording_publish_port import RecordingPublishPort


def _settings(tmp_path: Path) -> BackfillSettings:
    return BackfillSettings(
        enabled=True,
        checkpoint_enabled=True,
        checkpoint_directory=str(tmp_path / "ck"),
        max_concurrent_slices=1,
    )


@pytest.mark.asyncio
async def test_synthetic_polygon_adapter_dry_run(tmp_path: Path) -> None:
    t_ms = int(datetime(2024, 1, 2, 15, 0, tzinfo=UTC).timestamp() * 1000)

    def handler(request: httpx.Request) -> httpx.Response:
        _ = request
        return httpx.Response(
            200,
            json={
                "ticker": "AAPL",
                "resultsCount": 1,
                "results": [
                    {
                        "v": 100,
                        "vw": 190.0,
                        "o": 189.0,
                        "c": 191.0,
                        "h": 192.0,
                        "l": 188.0,
                        "t": t_ms,
                        "n": 10,
                    }
                ],
            },
        )

    clock = FixedClock(T0)
    settings = PolygonSettings(
        enabled=True,
        api_key=SecretStr("test-polygon-key-value"),
        base_url="https://api.polygon.io",
        max_retries=1,
        retry_initial_delay_seconds=0.01,
        retry_max_delay_seconds=0.05,
    )
    http = PolygonHttpClient(settings, transport=httpx.MockTransport(handler))
    connector = PolygonHistoricalConnector(http, clock=clock)
    source = PolygonHistoricalBackfillSource(connector, _settings(tmp_path), owns_connector=False)
    store = FileBackfillCheckpointStore(tmp_path / "ck")
    engine = build_backfill_engine(
        _settings(tmp_path),
        clock=clock,
        source_registry=StaticSourceRegistry(sources={("polygon", "aggregates"): source}),
        checkpoint_store=store,
        sleeper=NoOpBackfillSleeper(),
    )
    result = await engine.run(
        polygon_request(
            start_time=datetime(2024, 1, 2, tzinfo=UTC),
            end_time=datetime(2024, 1, 3, tzinfo=UTC),
        ),
        backfill_id="poly-offline",
    )
    assert result.processed_count == 1
    assert result.published_count == 0
    ck = await store.load("poly-offline")
    assert ck is not None and ck.completed is True
    await engine.aclose()
    await http.aclose()


@pytest.mark.asyncio
async def test_synthetic_fred_benzinga_finnhub_sec(tmp_path: Path) -> None:
    cases: list[
        tuple[BackfillProvider, BackfillSourceKind, FakeBackfillSource, BackfillRequest]
    ] = []

    fred_src = FakeBackfillSource(
        events_by_slice={"window-0000": [make_macro()]},
        slices=None,
    )
    # Override build_slices via explicit slices for refresh / one-window cases.
    fred_req = BackfillRequest(
        provider=BackfillProvider.FRED,
        source_kind=BackfillSourceKind.OBSERVATIONS,
        start_time=datetime(2024, 1, 1, tzinfo=UTC),
        end_time=datetime(2024, 1, 2, tzinfo=UTC),
        max_records=10,
        fred=FredSelector(
            fred_series_id="GDP",
            series_id="gdp",
            instrument=instrument(),
        ),
    )
    cases.append((BackfillProvider.FRED, BackfillSourceKind.OBSERVATIONS, fred_src, fred_req))

    bz_slices = FakeBackfillSource(events_by_slice={}).build_slices(
        BackfillRequest(
            provider=BackfillProvider.BENZINGA,
            source_kind=BackfillSourceKind.NEWS,
            start_time=datetime(2024, 1, 2, tzinfo=UTC),
            end_time=datetime(2024, 1, 3, tzinfo=UTC),
            max_records=10,
            benzinga=BenzingaSelector(
                tickers=("AAPL",),
                ticker_to_instrument={"AAPL": instrument()},
                anchor_instrument=instrument(),
            ),
        )
    )
    bz_src = FakeBackfillSource(
        events_by_slice={bz_slices[0].slice_id: [make_news()]},
        slices=bz_slices,
    )
    cases.append(
        (
            BackfillProvider.BENZINGA,
            BackfillSourceKind.NEWS,
            bz_src,
            BackfillRequest(
                provider=BackfillProvider.BENZINGA,
                source_kind=BackfillSourceKind.NEWS,
                start_time=datetime(2024, 1, 2, tzinfo=UTC),
                end_time=datetime(2024, 1, 3, tzinfo=UTC),
                max_records=10,
                benzinga=BenzingaSelector(
                    tickers=("AAPL",),
                    ticker_to_instrument={"AAPL": instrument()},
                    anchor_instrument=instrument(),
                ),
            ),
        )
    )

    refresh_slice = [
        BackfillSlice(
            slice_id="refresh-0",
            start_time=datetime(2024, 1, 1, tzinfo=UTC),
            end_time=datetime(2024, 1, 2, tzinfo=UTC),
        )
    ]
    fh_src = FakeBackfillSource(
        events_by_slice={"refresh-0": [make_reference(), make_fundamental()]},
        slices=refresh_slice,
    )
    cases.append(
        (
            BackfillProvider.FINNHUB,
            BackfillSourceKind.BOTH_REFRESH,
            fh_src,
            BackfillRequest(
                provider=BackfillProvider.FINNHUB,
                source_kind=BackfillSourceKind.BOTH_REFRESH,
                start_time=datetime(2024, 1, 1, tzinfo=UTC),
                end_time=datetime(2024, 1, 2, tzinfo=UTC),
                max_records=10,
                finnhub=FinnhubRefreshSelector(
                    ticker="AAPL",
                    instrument=instrument(),
                    refresh_type="both",
                ),
            ),
        )
    )

    sec_src = FakeBackfillSource(
        events_by_slice={"refresh-0": [make_filing()]},
        slices=refresh_slice,
    )
    cases.append(
        (
            BackfillProvider.SEC,
            BackfillSourceKind.RECENT_FILINGS,
            sec_src,
            BackfillRequest(
                provider=BackfillProvider.SEC,
                source_kind=BackfillSourceKind.RECENT_FILINGS,
                start_time=datetime(2024, 1, 1, tzinfo=UTC),
                end_time=datetime(2024, 1, 2, tzinfo=UTC),
                max_records=10,
                sec=SecRefreshSelector(cik="320193", instrument=instrument()),
            ),
        )
    )

    for provider, kind, source, req in cases:
        engine, store, _ = build_engine(
            tmp_path / provider.value,
            source,
            provider=provider,
            source_kind=kind,
        )
        result = await engine.run(req, backfill_id=f"{provider.value}-bf")
        assert result.processed_count >= 1
        assert result.published_count == 0
        ck = await store.load(f"{provider.value}-bf")
        assert ck is not None and ck.completed is True
        await engine.aclose()


@pytest.mark.asyncio
async def test_publish_and_resume_after_slice_truncation(tmp_path: Path) -> None:
    source = two_day_bar_source()
    source.may_have_more_slices.add("day-0001-2024-01-03")
    engine, store, clock = build_engine(tmp_path, source)
    port = RecordingPublishPort(clock=clock)
    with pytest.raises(BackfillTruncatedError):
        await engine.run(
            polygon_request(mode=BackfillMode.PUBLISH),
            backfill_id="trunc-resume",
            publish_port=port,
        )
    ck = await store.load("trunc-resume")
    assert ck is not None
    assert ck.completed is False
    assert "day-0000-2024-01-02" in ck.completed_slices
    # Clear truncation and resume.
    source.may_have_more_slices.clear()
    port2 = RecordingPublishPort(clock=clock)
    result = await engine.run(
        polygon_request(mode=BackfillMode.PUBLISH, resume=True, checkpoint_id="trunc-resume"),
        backfill_id="trunc-resume",
        publish_port=port2,
    )
    assert result.published_count == 2
    assert len(port2.published) == 1
    await engine.aclose()


@pytest.mark.asyncio
async def test_controlled_sink_failure_resume_preserves_keys(tmp_path: Path) -> None:
    source = two_day_bar_source()
    engine, store, clock = build_engine(tmp_path, source)
    expected = []
    for events in source.events_by_slice.values():
        expected.extend(build_idempotency_key(e) for e in events)

    class FailSecond:
        def __init__(self) -> None:
            self.n = 0
            self.inner = RecordingPublishPort(clock=clock)

        async def publish(self, event: Any, *, routing_key: str, context: Any) -> Any:
            self.n += 1
            if self.n == 2:
                self.inner.set_fail_next(True)
            return await self.inner.publish(event, routing_key=routing_key, context=context)

    with pytest.raises(BackfillSinkFailedError):
        await engine.run(
            polygon_request(mode=BackfillMode.PUBLISH),
            backfill_id="keys",
            publish_port=FailSecond(),
        )
    port = RecordingPublishPort(clock=clock)
    result = await engine.run(
        polygon_request(mode=BackfillMode.PUBLISH, resume=True, checkpoint_id="keys"),
        backfill_id="keys",
        publish_port=port,
    )
    assert result.published_count == 2
    keys = [build_idempotency_key(e) for e, _, _ in port.published]
    assert keys[0] in expected
    ck = await store.load("keys")
    assert ck is not None and ck.completed is True
    await engine.aclose()


@pytest.mark.asyncio
async def test_container_enabled_no_startup_run(tmp_path: Path) -> None:
    settings = AppSettings(
        environment=AppEnvironment.TEST,
        secrets=SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
        backfill=BackfillSettings(
            enabled=True,
            checkpoint_directory=str(tmp_path / "bf"),
        ),
    )
    container = build_container(settings)
    assert container.backfill_engine is not None
    # No run during construction — checkpoint dir empty aside from mkdir.
    assert list((tmp_path / "bf").glob("*.json")) == []
    await container.aclose()


@pytest.mark.asyncio
async def test_separate_containers_isolated(tmp_path: Path) -> None:
    a = build_container(
        AppSettings(
            environment=AppEnvironment.TEST,
            secrets=SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
            backfill=BackfillSettings(
                enabled=True,
                checkpoint_directory=str(tmp_path / "a"),
            ),
        )
    )
    b = build_container(
        AppSettings(
            environment=AppEnvironment.TEST,
            secrets=SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
            backfill=BackfillSettings(
                enabled=True,
                checkpoint_directory=str(tmp_path / "b"),
            ),
        )
    )
    assert a.backfill_engine is not b.backfill_engine
    await a.aclose()
    await b.aclose()


@pytest.mark.asyncio
async def test_audit_deterministic_fixed_clock(tmp_path: Path) -> None:
    clock = FixedClock(T0)
    engine, _, _ = build_engine(tmp_path, two_day_bar_source(), clock=clock)
    await engine.run(polygon_request(), backfill_id="audit")
    events = engine.audit_sink.events  # type: ignore[attr-defined]
    assert all(e.processed_at == T0 for e in events)
    assert all("api_key" not in e.reason for e in events)
    assert all(e.sink_message_id is None for e in events)
    await engine.aclose()
