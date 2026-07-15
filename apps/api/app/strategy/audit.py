"""Immutable Strategy Engine audit records."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.strategy.models import StrategyAction, StrategyReasonCode


@dataclass(frozen=True, slots=True)
class StrategyDecisionAudit:
    """Payload-free audit entry for one emitted strategy decision."""

    decision_id: str
    strategy_id: str
    strategy_version: str
    strategy_instance_id: str
    run_id: str
    instrument_key: str
    input_idempotency_key: str
    action: StrategyAction
    reason_codes: tuple[StrategyReasonCode, ...]
    occurred_at: datetime
    decision_timestamp: datetime
    configuration_fingerprint: str
    quality_assessment_id: str | None
    quality_status: str | None
    quality_highest_severity: str | None
    quality_action: str | None
    correlation_id: str | None
    causation_id: str | None


class StrategyAuditSink(Protocol):
    def record(self, entry: StrategyDecisionAudit) -> None: ...

    def records(self) -> Sequence[StrategyDecisionAudit]: ...

    def clear(self) -> None: ...


class InMemoryStrategyAuditSink:
    """Bounded in-memory strategy audit trail for application and tests."""

    def __init__(self, *, max_records: int = 10_000) -> None:
        if max_records < 1:
            msg = "max_records must be >= 1"
            raise ValueError(msg)
        self._max_records = max_records
        self._records: list[StrategyDecisionAudit] = []

    def record(self, entry: StrategyDecisionAudit) -> None:
        self._records.append(entry)
        overflow = len(self._records) - self._max_records
        if overflow > 0:
            del self._records[0:overflow]

    def records(self) -> Sequence[StrategyDecisionAudit]:
        return tuple(self._records)

    def clear(self) -> None:
        self._records.clear()


def audit_from_decision(
    decision_idempotency_key: str,
    *,
    decision_action: StrategyAction,
    decision_reason_codes: tuple[StrategyReasonCode, ...],
    decision_id: str,
    strategy_id: str,
    strategy_version: str,
    strategy_instance_id: str,
    run_id: str,
    instrument_key: str,
    occurred_at: datetime,
    decision_timestamp: datetime,
    configuration_fingerprint: str,
    quality_assessment_id: str | None,
    quality_status: str | None,
    quality_highest_severity: str | None,
    quality_action: str | None,
    correlation_id: str | None,
    causation_id: str | None,
) -> StrategyDecisionAudit:
    return StrategyDecisionAudit(
        decision_id=decision_id,
        strategy_id=strategy_id,
        strategy_version=strategy_version,
        strategy_instance_id=strategy_instance_id,
        run_id=run_id,
        instrument_key=instrument_key,
        input_idempotency_key=decision_idempotency_key,
        action=decision_action,
        reason_codes=decision_reason_codes,
        occurred_at=occurred_at,
        decision_timestamp=decision_timestamp,
        configuration_fingerprint=configuration_fingerprint,
        quality_assessment_id=quality_assessment_id,
        quality_status=quality_status,
        quality_highest_severity=quality_highest_severity,
        quality_action=quality_action,
        correlation_id=correlation_id,
        causation_id=causation_id,
    )
