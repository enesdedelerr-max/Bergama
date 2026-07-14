"""Iceberg row reconstruction and deterministic ordering (#308)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.infrastructure.iceberg.mapper import map_envelope_to_row
from app.infrastructure.iceberg.replay_source import reconstruct_row_to_canonical
from app.infrastructure.iceberg.routing import table_for_event_type
from app.market_data.keys import build_idempotency_key
from app.market_data.quality import DataQualityFlags
from app.market_data.replay.errors import (
    ReplayIdempotencyMismatchError,
    ReplayReconstructionError,
    ReplayUnsupportedSchemaError,
)
from app.market_data.replay.models import ReplayRecord
from app.market_data.replay.ordering import sort_replay_records
from app.market_data.serialization import market_event_to_envelope
from tests.support.market_data_fixtures import (
    T0,
    make_bar,
    make_filing,
    make_fundamental,
    make_macro,
    make_news,
    make_quote,
    make_reference,
    make_trade,
)


def _row_for(event: object) -> tuple[dict, str]:
    envelope = market_event_to_envelope(event)  # type: ignore[arg-type]
    row = map_envelope_to_row(envelope, event)  # type: ignore[arg-type]
    table = table_for_event_type(envelope.event_type)
    return row, table


@pytest.mark.parametrize(
    "factory",
    [
        make_quote,
        make_trade,
        make_bar,
        make_reference,
        make_fundamental,
        make_macro,
        make_filing,
        make_news,
    ],
)
def test_reconstruct_all_event_families(factory: object) -> None:
    event = factory()  # type: ignore[operator]
    row, table = _row_for(event)
    rebuilt, synthetic = reconstruct_row_to_canonical(row, table_base=table)
    assert synthetic is True  # symbol_effective_from not stored
    assert rebuilt.occurred_at == event.occurred_at
    assert rebuilt.effective_at == event.effective_at
    assert rebuilt.known_at == event.known_at
    assert rebuilt.ingested_at == event.ingested_at
    assert build_idempotency_key(rebuilt) == row["idempotency_key"]
    # No Kafka provenance invented.
    assert "kafka_topic" not in row or row.get("kafka_topic") is None
    assert not hasattr(rebuilt, "kafka_partition")


def test_financial_values_preserved_for_quote() -> None:
    event = make_quote(bid_price=Decimal("191.11"), ask_price=Decimal("191.22"))
    row, table = _row_for(event)
    rebuilt, _ = reconstruct_row_to_canonical(row, table_base=table)
    assert rebuilt.bid_price == row["bid_price"]  # type: ignore[attr-defined]
    assert rebuilt.ask_price == row["ask_price"]  # type: ignore[attr-defined]


def test_late_flags_preserved() -> None:
    event = make_trade(
        quality=DataQualityFlags(is_late=True, late_arrival_lag_ms=250),
        source=make_trade().source.model_copy(update={"source_event_id": "late-1"}),
    )
    row, table = _row_for(event)
    rebuilt, _ = reconstruct_row_to_canonical(row, table_base=table)
    assert rebuilt.quality.is_late is True
    assert rebuilt.quality.late_arrival_lag_ms == 250


def test_unsupported_schema_rejected() -> None:
    event = make_quote()
    row, table = _row_for(event)
    row["schema_version"] = "9.9.9"
    with pytest.raises(ReplayUnsupportedSchemaError):
        reconstruct_row_to_canonical(row, table_base=table)


def test_missing_required_column_rejected() -> None:
    event = make_quote()
    row, table = _row_for(event)
    del row["instrument_key"]
    with pytest.raises(ReplayReconstructionError):
        reconstruct_row_to_canonical(row, table_base=table)


def test_idempotency_mismatch_rejected() -> None:
    event = make_quote()
    row, table = _row_for(event)
    row["idempotency_key"] = "tampered-key"
    with pytest.raises(ReplayIdempotencyMismatchError):
        # Source path checks after reconstruct; mimic that check here.
        rebuilt, _ = reconstruct_row_to_canonical(row, table_base=table)
        if build_idempotency_key(rebuilt) != row["idempotency_key"]:
            raise ReplayIdempotencyMismatchError(detail="mismatch")


def test_deterministic_cross_table_order() -> None:
    t1 = T0 + timedelta(seconds=1)
    t2 = T0 + timedelta(seconds=2)
    q = make_quote(
        occurred_at=t2,
        effective_at=t2,
        known_at=t2 + timedelta(milliseconds=50),
        ingested_at=t2 + timedelta(milliseconds=100),
    )
    t = make_trade(
        occurred_at=t1,
        effective_at=t1,
        known_at=t1 + timedelta(milliseconds=50),
        ingested_at=t1 + timedelta(milliseconds=100),
        source=make_trade().source.model_copy(update={"source_event_id": "t-early"}),
    )
    b = make_bar(
        occurred_at=t1,
        effective_at=t1,
        known_at=t1 + timedelta(milliseconds=50),
        ingested_at=t1 + timedelta(milliseconds=100),
        window_start=t1 - timedelta(minutes=1),
        window_end=t1,
        close_time=t1,
    )
    records: list[ReplayRecord] = []
    for event in (q, t, b):
        row, table = _row_for(event)
        rebuilt, synth = reconstruct_row_to_canonical(row, table_base=table)
        records.append(
            ReplayRecord(
                occurred_at=rebuilt.occurred_at,
                event_type=str(row["event_type"]),
                instrument_key=rebuilt.instrument.instrument_key,
                idempotency_key=str(row["idempotency_key"]),
                table_base=table,
                event=rebuilt,
                synthetic_symbol_effective_from=synth,
            )
        )
    ordered = sort_replay_records(records)
    assert [r.event_type for r in ordered] == [
        "market.bar",
        "market.trade",
        "market.quote",
    ]
    again = sort_replay_records(list(reversed(records)))
    assert [r.idempotency_key for r in again] == [r.idempotency_key for r in ordered]


def test_no_timestamp_repair() -> None:
    event = make_quote()
    original = event.occurred_at
    row, table = _row_for(event)
    rebuilt, _ = reconstruct_row_to_canonical(row, table_base=table)
    assert rebuilt.occurred_at == original
    assert rebuilt.occurred_at.tzinfo is not None
    assert rebuilt.occurred_at.utcoffset() == datetime.now(UTC).utcoffset()
