"""Bounded process-local Risk Engine metrics."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from app.risk.models import RiskAssessment, RiskFinalAction


@dataclass(slots=True)
class RiskMetrics:
    assessments_evaluated: int = 0
    approvals: int = 0
    rejections: int = 0
    halts: int = 0
    rule_failures: Counter[str] = field(default_factory=Counter)
    final_actions: Counter[str] = field(default_factory=Counter)

    def record_assessment(self, assessment: RiskAssessment) -> None:
        self.assessments_evaluated += 1
        self.final_actions[assessment.final_action.value] += 1
        if assessment.final_action is RiskFinalAction.APPROVE:
            self.approvals += 1
        elif assessment.final_action is RiskFinalAction.REJECT:
            self.rejections += 1
        else:
            self.halts += 1
        for result in assessment.rule_results:
            if result.status.value == "FAIL":
                self.rule_failures[result.rule_id.value] += 1
