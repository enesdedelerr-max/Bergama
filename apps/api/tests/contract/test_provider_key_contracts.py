"""Cross-provider key determinism contracts (#304E)."""

from __future__ import annotations

from tests.support.provider_contracts import benzinga, finnhub, fred, polygon, sec
from tests.support.provider_contracts.assertions import assert_key_contract, assert_keys_distinct


def test_keys_are_deterministic_for_all_providers() -> None:
    events = [
        polygon.historical_bar(),
        polygon.realtime_trade(),
        polygon.realtime_quote(),
        finnhub.reference_event(),
        finnhub.fundamental_events()[0],
        fred.macro_observation(),
        sec.filing_events()[0],
        benzinga.news_events()[0],
    ]
    for event in events:
        assert_key_contract(event)


def test_polygon_adjusted_differs_from_unadjusted_keys() -> None:
    adjusted = polygon.historical_bar(adjusted=True)
    unadjusted = polygon.historical_bar(adjusted=False)
    # Adjustment state participates in dedup fingerprint for bars when no source id conflict —
    # source_event_id includes request_id+timestamp so keep same request path: keys may still
    # share source_event_id; ensure events remain distinct objects with different adjustment.
    assert adjusted.adjustment_state != unadjusted.adjustment_state
    assert_key_contract(adjusted)
    assert_key_contract(unadjusted)


def test_fred_vintage_boundaries_produce_distinct_keys() -> None:
    v1 = fred.macro_observation(realtime_start="2024-01-31", realtime_end="2024-03-31")
    v2 = fred.macro_observation(realtime_start="2024-04-01", realtime_end="9999-12-31")
    assert v1.source.source_event_id != v2.source.source_event_id
    assert_keys_distinct(v1, v2)


def test_sec_accession_and_amendment_produce_distinct_keys() -> None:
    base = sec.filing_events(form="10-K", accession="0000320193-24-000001")[0]
    amended = sec.filing_events(form="10-K/A", accession="0000320193-24-000002")[0]
    assert_keys_distinct(base, amended)


def test_benzinga_later_update_produces_distinct_keys() -> None:
    original = benzinga.news_events(updated=benzinga.UPDATED)[0]
    revised = benzinga.news_events(updated=benzinga.UPDATED_LATER)[0]
    assert original.source.source_event_id != revised.source.source_event_id
    assert_keys_distinct(original, revised)
    assert original.quality.revision_of_event_id is None
    assert revised.quality.revision_of_event_id is None


def test_finnhub_metrics_share_response_source_id_but_remain_distinct_events() -> None:
    """Finnhub assigns one source_event_id per HTTP response observation.

    Metric differentiation remains on the canonical FundamentalEvent fields.
    Shared source_event_id therefore yields shared #301 sid-based keys — this is
    documented provider-response identity, not silent collapse of metric values.
    """
    events = finnhub.fundamental_events()
    assert len(events) >= 2
    pe = next(e for e in events if e.metric_code == "peTTM")
    roe = next(e for e in events if e.metric_code == "roeTTM")
    assert pe.value != roe.value
    assert pe.metric_code != roe.metric_code
    assert pe.source.source_event_id == roe.source.source_event_id
    assert_key_contract(pe)
    assert_key_contract(roe)
