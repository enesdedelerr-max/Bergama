"""Optional live Historical Backfill smoke (#309).

Opt-in: BERGAMA_BACKFILL_SMOKE=1

Exactly one provider via BERGAMA_BACKFILL_SMOKE_PROVIDER
(polygon|fred|benzinga|finnhub|sec). Tiny bounded dry_run. No production sink.
"""

from __future__ import annotations

import os
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from app.core.backfill_settings import BackfillSettings
from app.core.clock import SystemClock
from app.core.polygon_settings import PolygonSettings
from app.infrastructure.backfill.file_checkpoint import FileBackfillCheckpointStore
from app.infrastructure.backfill.polygon import PolygonHistoricalBackfillSource
from app.infrastructure.polygon.historical import PolygonHistoricalConnector
from app.infrastructure.polygon.http import PolygonHttpClient
from app.market_data.backfill.engine import StaticSourceRegistry, build_backfill_engine
from app.market_data.backfill.models import (
    BackfillMode,
    BackfillProvider,
    BackfillRequest,
    BackfillSourceKind,
    PolygonSelector,
)
from app.market_data.backfill.policies import NoOpBackfillSleeper
from app.market_data.enums import AssetClass
from app.market_data.identity import InstrumentId
from pydantic import SecretStr

pytestmark = pytest.mark.backfill_smoke

_ALLOWED = frozenset({"polygon", "fred", "benzinga", "finnhub", "sec"})


def _live_enabled() -> bool:
    return os.environ.get("BERGAMA_BACKFILL_SMOKE") == "1"


@pytest.mark.asyncio
async def test_backfill_live_smoke() -> None:
    if not _live_enabled():
        pytest.skip("BERGAMA_BACKFILL_SMOKE not set")

    provider = os.environ.get("BERGAMA_BACKFILL_SMOKE_PROVIDER", "").strip().lower()
    if provider not in _ALLOWED:
        pytest.fail(
            "BERGAMA_BACKFILL_SMOKE=1 requires BERGAMA_BACKFILL_SMOKE_PROVIDER="
            "polygon|fred|benzinga|finnhub|sec (exactly one)"
        )

    if provider != "polygon":
        pytest.fail(
            f"live smoke for provider={provider} is not wired in this MVP; "
            "use polygon or run offline make test-api-backfill"
        )

    raw_key = os.environ.get("BERGAMA_POLYGON__API_KEY", "").strip()
    if not raw_key:
        pytest.fail("BERGAMA_BACKFILL_SMOKE with polygon requires BERGAMA_POLYGON__API_KEY")

    end = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    start = end - timedelta(days=2)
    clock = SystemClock()
    poly_settings = PolygonSettings(
        enabled=True,
        api_key=SecretStr(raw_key),
        max_retries=2,
        max_pages=1,
        max_results_per_page=5,
    )
    http = PolygonHttpClient(poly_settings)
    connector = PolygonHistoricalConnector(http, clock=clock)

    with tempfile.TemporaryDirectory(prefix="bergama-backfill-smoke-") as tmp:
        ck_dir = Path(tmp) / "ck"
        settings = BackfillSettings(
            enabled=True,
            default_mode="dry_run",
            checkpoint_enabled=True,
            checkpoint_directory=str(ck_dir),
            max_time_range_days=7,
            max_records=20,
            max_slices=10,
            max_concurrent_slices=1,
        )
        source = PolygonHistoricalBackfillSource(
            connector,
            settings,
            owns_connector=False,
        )
        store = FileBackfillCheckpointStore(ck_dir)
        engine = build_backfill_engine(
            settings,
            clock=clock,
            source_registry=StaticSourceRegistry(sources={("polygon", "aggregates"): source}),
            checkpoint_store=store,
            sleeper=NoOpBackfillSleeper(),
        )
        request = BackfillRequest(
            provider=BackfillProvider.POLYGON,
            source_kind=BackfillSourceKind.AGGREGATES,
            start_time=start,
            end_time=end,
            max_records=20,
            mode=BackfillMode.DRY_RUN,
            polygon=PolygonSelector(
                ticker="AAPL",
                instrument=InstrumentId(
                    instrument_key="bergama:equity:us:aapl",
                    asset_class=AssetClass.EQUITY,
                    local_symbol="AAPL",
                    symbol_effective_from=datetime(2020, 1, 1, tzinfo=UTC),
                ),
                currency="USD",
                venue="XNAS",
                multiplier=1,
                timespan="day",
                adjusted=True,
            ),
        )
        try:
            result = await engine.run(request, backfill_id="smoke-backfill-1")
            ck = await store.load("smoke-backfill-1")
        finally:
            await engine.aclose()
            await http.aclose()

    assert result.sink_type == "none"
    assert result.published_count == 0
    assert result.terminal_status in {"completed", "completed_empty"}
    assert ck is not None and ck.completed is True
    assert ck.request_fingerprint == result.request_fingerprint
