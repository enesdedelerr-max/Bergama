"""Deterministic Morning Briefing Assembly Pipeline."""

from __future__ import annotations

from app.premarket.morning_briefing.identity import build_briefing_id
from app.premarket.morning_briefing.models import BriefingCollection, BriefingRecord
from app.premarket.morning_briefing.ordering import preserve_scoring_order
from app.premarket.morning_briefing.output import to_briefing_collection, to_briefing_record
from app.premarket.morning_briefing.provenance import build_briefing_provenance
from app.premarket.morning_briefing.validate_input import ValidatedBriefingRequest
from app.premarket.morning_briefing.validate_output import validate_briefing_collection


def run_briefing_pipeline(request: ValidatedBriefingRequest) -> BriefingCollection:
    """Execute the immutable Policy Version v1 Assembly Pipeline once.

    Stage order is immutable:
    Input Validation (already applied) → Policy Version Binding (already applied) →
    PIT Validation (already applied) → Authorized Input Admission (already applied) →
    Score Reference Preservation → Ordering Preservation → Briefing Assembly →
    Identity Generation → Provenance Generation → Output Construction →
    Post-Validation → Emission.
    """
    ordered_pairs = preserve_scoring_order(request.scores)
    records: list[BriefingRecord] = []
    for sequence_index, score_record in ordered_pairs:
        records.append(to_briefing_record(sequence_index=sequence_index, score_record=score_record))
    preserved_records = tuple(records)

    briefing_id = build_briefing_id(request)
    provenance = build_briefing_provenance(request)
    collection = to_briefing_collection(
        briefing_id=briefing_id,
        as_of=request.as_of,
        records=preserved_records,
        provenance=provenance,
    )
    return validate_briefing_collection(collection, request=request)
