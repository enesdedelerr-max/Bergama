"""Optional live SEC EDGAR smoke — SKIPPED unless explicitly enabled."""

from __future__ import annotations

import os
from datetime import UTC, datetime

import pytest
from app.core.clock import SystemClock
from app.core.sec_settings import SecSettings
from app.infrastructure.sec.http import SecHttpClient
from app.infrastructure.sec.submissions import SecSubmissionsConnector, SubmissionsRequest
from app.market_data.enums import AssetClass
from app.market_data.identity import InstrumentId
from app.market_data.serialization import market_event_to_envelope, market_event_to_payload


def _live_enabled() -> bool:
    return os.environ.get("BERGAMA_SEC_SMOKE") == "1"


@pytest.mark.asyncio
async def test_sec_filings_live_smoke() -> None:
    """
    Live policy:
    - SKIPPED when BERGAMA_SEC_SMOKE is not exactly \"1\".
    - PASS only when a real submissions call succeeds.
    - FAIL when explicitly enabled and the provider call fails.
    - Never hammers SEC endpoints (bounded max filings).
    """
    if not _live_enabled():
        pytest.skip("smoke-api-sec SKIPPED (set BERGAMA_SEC_SMOKE=1 and SEC User-Agent)")

    contact = os.environ.get("BERGAMA_SEC__CONTACT_EMAIL", "").strip()
    user_agent = os.environ.get("BERGAMA_SEC__USER_AGENT", "").strip()
    if not contact and not user_agent:
        pytest.fail(
            "BERGAMA_SEC_SMOKE=1 requires BERGAMA_SEC__CONTACT_EMAIL or BERGAMA_SEC__USER_AGENT"
        )

    settings = SecSettings(
        enabled=True,
        contact_email=contact or None,
        user_agent=user_agent or None,
        max_retries=2,
        min_request_interval_seconds=0.5,
        max_filings_per_request=5,
    )
    http = SecHttpClient(settings)
    connector = SecSubmissionsConnector(http, clock=SystemClock())
    instrument = InstrumentId(
        instrument_key="bergama:equity:us:aapl",
        asset_class=AssetClass.EQUITY,
        local_symbol="AAPL",
        symbol_effective_from=datetime(2020, 1, 1, tzinfo=UTC),
    )
    try:
        result = await connector.fetch_submissions(
            SubmissionsRequest(
                cik="320193",
                instrument=instrument,
                max_filings=5,
            )
        )
    finally:
        await http.aclose()

    assert result.cik == "0000320193"
    assert result.filings_mapped >= 1
    first = result.events[0]
    assert first.source.provider == "sec_edgar"
    assert first.accession_number
    payload = market_event_to_payload(first)
    envelope = market_event_to_envelope(first)
    assert payload["accession_number"] == first.accession_number
    assert envelope.schema_version == first.schema_version
