"""Canonical ordering helpers for Premarket Scoring determinism."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from app.premarket.catalyst.models import CatalystCollection, CatalystRecord
from app.premarket.errors import ScoreConflictError


def canonical_source_identifiers(identifiers: Iterable[str]) -> tuple[str, ...]:
    """Return unique source identifiers in deterministic ascending order.

    Policy Version v1 treats Catalyst contributing identifiers as set-based
    evidence: membership matters; input iteration order must not.
    """
    return tuple(sorted(set(identifiers)))


def canonicalize_catalyst_collection(collection: CatalystCollection) -> CatalystCollection:
    """Deduplicate and order Catalyst records by ``catalyst_record_id``.

    Fail closed when the same identity carries conflicting payloads.
    Equivalent duplicates (identical dumps) collapse to one record.
    """
    unique: dict[str, CatalystRecord] = {}
    for record in collection.records:
        existing = unique.get(record.catalyst_record_id)
        if existing is not None:
            if existing.model_dump(mode="python") != record.model_dump(mode="python"):
                raise ScoreConflictError(
                    detail=f"conflicting_catalyst_identity:{record.catalyst_record_id}"
                )
            continue
        unique[record.catalyst_record_id] = record

    ordered_ids = tuple(sorted(unique))
    ordered_records = tuple(unique[record_id] for record_id in ordered_ids)
    provenance = collection.provenance.model_copy(update={"source_identifiers": ordered_ids})
    return collection.model_copy(update={"records": ordered_records, "provenance": provenance})


def assert_catalyst_identifiers_canonical(identifiers: Sequence[str]) -> None:
    """Fail closed when catalyst identifiers are not unique+sorted."""
    expected = canonical_source_identifiers(identifiers)
    if tuple(identifiers) != expected:
        raise ScoreConflictError(detail="non_canonical_catalyst_source_identifiers")
