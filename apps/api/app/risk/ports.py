"""Risk Engine downstream ports — protocol only, no Kafka/persistence adapters."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from app.risk.models import RiskAssessment


class RiskAssessmentSink(Protocol):
    """Infrastructure-neutral assessment sink. Not an OMS/broker boundary."""

    async def publish_assessment(self, assessment: RiskAssessment) -> None: ...


# Alias for callers that prefer decision naming.
RiskDecisionPort = RiskAssessmentSink


class InMemoryRiskAssessmentSink:
    """Test/local sink that records assessments without side effects."""

    def __init__(self) -> None:
        self._assessments: list[RiskAssessment] = []

    async def publish_assessment(self, assessment: RiskAssessment) -> None:
        self._assessments.append(assessment)

    @property
    def assessments(self) -> Sequence[RiskAssessment]:
        return tuple(self._assessments)

    def clear(self) -> None:
        self._assessments.clear()
