"""Deterministic catalyst collection ordering policy."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.premarket.catalyst.models import CatalystRecord

ORDERING_POLICY_KNOWN_AT_ASC_EVENT_TIME_ASC_TYPE_ASC_INSTRUMENT_KEY_ASC_ID_ASC = (
    "known_at_asc_event_time_asc_type_asc_instrument_key_asc_id_asc"
)

UNLINKED_INSTRUMENT_KEY_SENTINEL = "__unlinked__"


def catalyst_sort_key(record: CatalystRecord) -> tuple[object, ...]:
    """Stable total order for normalized catalyst records."""
    return (
        record.known_at,
        record.event_time,
        record.catalyst_type,
        record.instrument_key or UNLINKED_INSTRUMENT_KEY_SENTINEL,
        record.catalyst_record_id,
    )
