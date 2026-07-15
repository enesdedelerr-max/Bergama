"""Unit tests for Backfill settings, capability matrix, and request models (#309)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.core.backfill_settings import BackfillSettings
from app.core.config import AppSettings
from app.core.environment import AppEnvironment
from app.core.secrets import SecretSettings
from app.market_data.backfill.errors import BackfillUnboundedRequestError
from app.market_data.backfill.models import (
    BackfillCapability,
    BackfillMode,
    BackfillProvider,
    BackfillRequest,
    BackfillSourceKind,
    BenzingaSelector,
    FinnhubRefreshSelector,
    FredSelector,
    PolygonSelector,
    SecRefreshSelector,
    capability_for,
    validate_backfill_request,
)
from pydantic import ValidationError
from tests.conftest import VALID_PROD_JWT_SECRET
from tests.support.market_data_fixtures import instrument


def test_backfill_disabled_by_default() -> None:
    settings = BackfillSettings()
    assert settings.enabled is False
    assert settings.default_mode == "dry_run"
    assert settings.max_concurrent_slices == 1


def test_app_settings_includes_disabled_backfill() -> None:
    app = AppSettings(
        environment=AppEnvironment.TEST,
        secrets=SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
    )
    assert app.backfill.enabled is False
    assert app.backfill.default_mode == "dry_run"


def test_unsafe_checkpoint_path_rejected() -> None:
    with pytest.raises(ValidationError):
        BackfillSettings(checkpoint_directory="../escape")
    with pytest.raises(ValidationError):
        BackfillSettings(checkpoint_directory="/etc/passwd")
    with pytest.raises(ValidationError):
        BackfillSettings(checkpoint_directory="relative/path")


def test_enabled_requires_checkpoint_directory() -> None:
    with pytest.raises(ValidationError):
        BackfillSettings(enabled=True, checkpoint_enabled=True, checkpoint_directory=None)


def test_default_mode_publish_rejected_when_enabled(tmp_path) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(ValidationError):
        BackfillSettings(
            enabled=True,
            default_mode="publish",
            checkpoint_directory=str(tmp_path),
        )


@pytest.mark.parametrize(
    ("provider", "kind", "expected"),
    [
        (
            BackfillProvider.POLYGON,
            BackfillSourceKind.AGGREGATES,
            BackfillCapability.HISTORICAL_BACKFILL,
        ),
        (
            BackfillProvider.FRED,
            BackfillSourceKind.OBSERVATIONS,
            BackfillCapability.HISTORICAL_BACKFILL,
        ),
        (
            BackfillProvider.BENZINGA,
            BackfillSourceKind.NEWS,
            BackfillCapability.HISTORICAL_BACKFILL,
        ),
        (
            BackfillProvider.FINNHUB,
            BackfillSourceKind.PROFILE_REFRESH,
            BackfillCapability.BOUNDED_REFRESH,
        ),
        (
            BackfillProvider.FINNHUB,
            BackfillSourceKind.FUNDAMENTALS_REFRESH,
            BackfillCapability.BOUNDED_REFRESH,
        ),
        (
            BackfillProvider.SEC,
            BackfillSourceKind.RECENT_FILINGS,
            BackfillCapability.BOUNDED_REFRESH,
        ),
        (
            BackfillProvider.POLYGON,
            BackfillSourceKind.REALTIME,
            BackfillCapability.UNSUPPORTED,
        ),
        (
            BackfillProvider.SEC,
            BackfillSourceKind.ARCHIVES,
            BackfillCapability.UNSUPPORTED,
        ),
    ],
)
def test_capability_matrix(
    provider: BackfillProvider,
    kind: BackfillSourceKind,
    expected: BackfillCapability,
) -> None:
    assert capability_for(provider, kind) is expected


def test_polygon_request_ok() -> None:
    req = BackfillRequest(
        provider=BackfillProvider.POLYGON,
        source_kind=BackfillSourceKind.AGGREGATES,
        start_time=datetime(2024, 1, 1, tzinfo=UTC),
        end_time=datetime(2024, 1, 2, tzinfo=UTC),
        max_records=10,
        polygon=PolygonSelector(
            ticker="AAPL",
            instrument=instrument(),
            currency="USD",
            timespan="day",
        ),
    )
    assert req.capability() is BackfillCapability.HISTORICAL_BACKFILL
    assert "api_key" not in req.model_dump()
    fp1 = req.fingerprint(sink_type="none")
    fp2 = req.fingerprint(sink_type="none")
    assert fp1 == fp2
    assert len(fp1) == 64


def test_invalid_selector_provider_rejected() -> None:
    with pytest.raises(ValidationError):
        BackfillRequest(
            provider=BackfillProvider.POLYGON,
            source_kind=BackfillSourceKind.AGGREGATES,
            start_time=datetime(2024, 1, 1, tzinfo=UTC),
            end_time=datetime(2024, 1, 2, tzinfo=UTC),
            max_records=10,
            fred=FredSelector(
                fred_series_id="GDP",
                series_id="gdp",
                instrument=instrument(),
            ),
        )


def test_realtime_and_archives_rejected() -> None:
    with pytest.raises(ValidationError):
        BackfillRequest(
            provider=BackfillProvider.POLYGON,
            source_kind=BackfillSourceKind.REALTIME,
            start_time=datetime(2024, 1, 1, tzinfo=UTC),
            end_time=datetime(2024, 1, 2, tzinfo=UTC),
            max_records=10,
            polygon=PolygonSelector(
                ticker="AAPL",
                instrument=instrument(),
                currency="USD",
                timespan="minute",
            ),
        )
    with pytest.raises(ValidationError):
        BackfillRequest(
            provider=BackfillProvider.SEC,
            source_kind=BackfillSourceKind.ARCHIVES,
            start_time=datetime(2024, 1, 1, tzinfo=UTC),
            end_time=datetime(2024, 1, 2, tzinfo=UTC),
            max_records=10,
            sec=SecRefreshSelector(cik="320193", instrument=instrument()),
        )


def test_start_must_precede_end() -> None:
    with pytest.raises(ValidationError):
        BackfillRequest(
            provider=BackfillProvider.POLYGON,
            source_kind=BackfillSourceKind.AGGREGATES,
            start_time=datetime(2024, 1, 2, tzinfo=UTC),
            end_time=datetime(2024, 1, 1, tzinfo=UTC),
            max_records=10,
            polygon=PolygonSelector(
                ticker="AAPL",
                instrument=instrument(),
                currency="USD",
                timespan="day",
            ),
        )


def test_validate_backfill_request_bounds() -> None:
    settings = BackfillSettings(max_time_range_days=7, max_records=100)
    req = BackfillRequest(
        provider=BackfillProvider.FRED,
        source_kind=BackfillSourceKind.OBSERVATIONS,
        start_time=datetime(2024, 1, 1, tzinfo=UTC),
        end_time=datetime(2024, 2, 1, tzinfo=UTC),
        max_records=50,
        fred=FredSelector(
            fred_series_id="GDP",
            series_id="gdp",
            instrument=instrument(),
        ),
    )
    with pytest.raises(BackfillUnboundedRequestError):
        validate_backfill_request(req, settings)


def test_no_arbitrary_fields_on_request() -> None:
    with pytest.raises(ValidationError):
        BackfillRequest.model_validate(
            {
                "provider": "polygon",
                "source_kind": "aggregates",
                "start_time": "2024-01-01T00:00:00Z",
                "end_time": "2024-01-02T00:00:00Z",
                "max_records": 10,
                "url": "https://evil.example",
                "polygon": {
                    "ticker": "AAPL",
                    "instrument": instrument().model_dump(mode="json"),
                    "currency": "USD",
                    "timespan": "day",
                },
            }
        )


def test_finnhub_and_sec_refresh_selectors() -> None:
    fh = BackfillRequest(
        provider=BackfillProvider.FINNHUB,
        source_kind=BackfillSourceKind.PROFILE_REFRESH,
        start_time=datetime(2024, 1, 1, tzinfo=UTC),
        end_time=datetime(2024, 1, 2, tzinfo=UTC),
        max_records=5,
        mode=BackfillMode.VALIDATE_ONLY,
        finnhub=FinnhubRefreshSelector(
            ticker="AAPL",
            instrument=instrument(),
            refresh_type="profile",
        ),
    )
    assert fh.capability() is BackfillCapability.BOUNDED_REFRESH
    sec = BackfillRequest(
        provider=BackfillProvider.SEC,
        source_kind=BackfillSourceKind.RECENT_FILINGS,
        start_time=datetime(2024, 1, 1, tzinfo=UTC),
        end_time=datetime(2024, 1, 2, tzinfo=UTC),
        max_records=5,
        sec=SecRefreshSelector(cik="0000320193", instrument=instrument()),
    )
    assert sec.sec is not None and sec.sec.refresh_type == "recent_filings"


def test_benzinga_selector_fingerprint_stable() -> None:
    sel = BenzingaSelector(
        tickers=("aapl", "MSFT"),
        channels=("News",),
        ticker_to_instrument={"aapl": instrument()},
        anchor_instrument=instrument(),
    )
    a = sel.fingerprint_payload()
    b = sel.fingerprint_payload()
    assert a == b
    assert a["tickers"] == ["AAPL", "MSFT"]
