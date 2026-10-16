"""Deterministic ordering helpers for Premarket Analyst projection."""

from __future__ import annotations

from app.premarket_analyst.errors import PremarketAnalystOrderingError
from app.premarket_analyst.models import CatalystSummaryRecord, RiskFlag, StructuredThesis
from app.premarket_analyst.policy import ORDERING_POLICY_V1


def assert_ordering_policy(policy_id: str) -> None:
    if policy_id != ORDERING_POLICY_V1:
        raise PremarketAnalystOrderingError(detail=f"unsupported_ordering_policy:{policy_id}")


def sort_membership_refs(keys: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted(keys))


def sort_catalyst_summary_records(
    records: tuple[CatalystSummaryRecord, ...],
) -> tuple[CatalystSummaryRecord, ...]:
    return tuple(
        sorted(
            records,
            key=lambda record: (
                record.known_at,
                record.event_time,
                record.catalyst_type,
                record.instrument_key or "",
                record.catalyst_record_id,
            ),
        )
    )


def sort_theses(theses: tuple[StructuredThesis, ...]) -> tuple[StructuredThesis, ...]:
    return tuple(sorted(theses, key=lambda thesis: (thesis.instrument_key, thesis.thesis_id)))


def sort_risk_flags(flags: tuple[RiskFlag, ...]) -> tuple[RiskFlag, ...]:
    return tuple(sorted(flags, key=lambda flag: (flag.category, flag.risk_flag_id)))
