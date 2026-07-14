"""Routing, mapping, decimal, and envelope tests (#307)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from app.events.envelope import EventEnvelope
from app.infrastructure.iceberg.errors import (
    IcebergCanonicalError,
    IcebergDecimalError,
    IcebergMappingError,
    IcebergSchemaVersionError,
    IcebergUnknownRouteError,
)
from app.infrastructure.iceberg.mapper import (
    map_envelope_to_row,
    reconstruct_canonical_event,
    to_iceberg_decimal,
)
from app.infrastructure.iceberg.routing import approved_event_types, table_for_event_type
from app.infrastructure.iceberg.schemas import DECIMAL_PRECISION, DECIMAL_SCALE
from app.market_data.keys import build_idempotency_key
from app.market_data.serialization import market_event_to_envelope
from tests.support.market_data_fixtures import (
    make_bar,
    make_filing,
    make_fundamental,
    make_macro,
    make_news,
    make_quote,
    make_reference,
    make_trade,
)

_FACTORIES = (
    ("market.quote", "market_quotes", make_quote),
    ("market.trade", "market_trades", make_trade),
    ("market.bar", "market_bars", make_bar),
    ("market.reference_data", "market_reference_data", make_reference),
    ("market.fundamental", "market_fundamentals", make_fundamental),
    ("market.macro", "market_macro", make_macro),
    ("market.filing", "market_filings", make_filing),
    ("market.news", "market_news", make_news),
)


def test_all_eight_routes_and_no_provider_influence() -> None:
    assert len(approved_event_types()) == 8
    for event_type, table, factory in _FACTORIES:
        assert table_for_event_type(event_type) == table
        event = factory(source=factory().source.model_copy(update={"provider": "other"}))
        assert table_for_event_type(f"market.{event.event_type.value}") == table
    assert table_for_event_type("market.quote", table_prefix="dev_") == "dev_market_quotes"


def test_unknown_route_fails_closed() -> None:
    with pytest.raises(IcebergUnknownRouteError):
        table_for_event_type("market.unknown")
    with pytest.raises(IcebergUnknownRouteError):
        table_for_event_type("events.foo")


@pytest.mark.parametrize(("event_type", "table", "factory"), _FACTORIES)
def test_map_all_event_families(event_type: str, table: str, factory: object) -> None:
    event = factory()  # type: ignore[operator]
    envelope = market_event_to_envelope(event)
    assert envelope.event_type == event_type
    reconstructed = reconstruct_canonical_event(envelope)
    row = map_envelope_to_row(envelope, reconstructed)
    assert row["event_id"] == str(envelope.event_id)
    assert row["event_type"] == event_type
    assert row["idempotency_key"] == build_idempotency_key(event)
    assert row["source_provider"] == event.source.provider
    assert row["instrument_key"] == event.instrument.instrument_key
    assert row["occurred_at"].tzinfo is not None
    assert "password" not in (row.get("metadata_json") or "")
    assert table_for_event_type(event_type) == table


def test_unsupported_schema_version_rejected() -> None:
    event = make_quote()
    envelope = market_event_to_envelope(event)
    bad = envelope.model_copy(update={"schema_version": "9.9.9"})
    with pytest.raises(IcebergSchemaVersionError):
        reconstruct_canonical_event(bad)


def test_malformed_payload_rejected() -> None:
    envelope = EventEnvelope(
        event_id=uuid4(),
        event_type="market.quote",
        schema_version="1.0.0",
        source_system="bergama-market-data",
        occurred_at=datetime(2026, 7, 13, 14, 30, tzinfo=UTC),
        ingested_at=datetime(2026, 7, 13, 14, 30, tzinfo=UTC),
        idempotency_key="k",
        payload={"event_type": "quote"},
    )
    with pytest.raises(IcebergCanonicalError):
        reconstruct_canonical_event(envelope)


def test_idempotency_mismatch_fails_closed() -> None:
    event = make_quote()
    envelope = market_event_to_envelope(event)
    bad = envelope.model_copy(update={"idempotency_key": "tampered"})
    with pytest.raises(IcebergMappingError):
        map_envelope_to_row(bad, event)


def test_decimal_policy_bounds() -> None:
    assert to_iceberg_decimal(Decimal("1.5")) == Decimal("1.500000000000000000")
    with pytest.raises(IcebergDecimalError):
        to_iceberg_decimal(Decimal("1." + ("0" * DECIMAL_SCALE) + "1"))
    # precision overflow: 39 significant digits
    huge = Decimal("1" + ("0" * DECIMAL_PRECISION))
    with pytest.raises(IcebergDecimalError):
        to_iceberg_decimal(huge)


def test_no_float_coercion() -> None:
    with pytest.raises(IcebergDecimalError):
        to_iceberg_decimal(1.25)  # type: ignore[arg-type]
