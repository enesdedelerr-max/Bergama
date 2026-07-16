"""Pure deterministic Risk Engine evaluator."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.portfolio.models import PortfolioSnapshot
from app.risk.audit import InMemoryRiskAuditSink, RiskAuditRecord
from app.risk.context import build_evaluation_context
from app.risk.errors import RiskClosedError, RiskDownstreamPublishError, RiskError
from app.risk.hashing import build_assessment_hash, build_assessment_id
from app.risk.metrics import RiskMetrics
from app.risk.models import (
    ProposedTradeIntent,
    RiskAssessment,
    RiskFinalAction,
    RiskRuleResult,
    RiskRuleStatus,
)
from app.risk.policy import RiskPolicy
from app.risk.ports import RiskAssessmentSink
from app.risk.rules import RULE_ORDER, evaluate_rules


@dataclass(slots=True)
class RiskEngine:
    """Side-effect-free risk evaluator. Does not size, mutate, or execute."""

    assessment_sink: RiskAssessmentSink | None = None
    audit_sink: InMemoryRiskAuditSink = field(default_factory=InMemoryRiskAuditSink)
    metrics: RiskMetrics = field(default_factory=RiskMetrics)
    _closed: bool = False

    async def aclose(self) -> None:
        self.close()

    def close(self) -> None:
        self._closed = True

    @property
    def closed(self) -> bool:
        return self._closed

    def evaluate(
        self,
        *,
        intent: ProposedTradeIntent,
        snapshot: PortfolioSnapshot,
        policy: RiskPolicy,
        evaluated_at: datetime,
    ) -> RiskAssessment:
        if self._closed:
            raise RiskClosedError()

        # Defensive copy identity: never mutate caller inputs.
        snapshot_version = snapshot.portfolio_version
        intent_quantity = intent.signed_quantity_delta

        context = build_evaluation_context(
            intent=intent,
            snapshot=snapshot,
            policy=policy,
            evaluated_at=evaluated_at,
        )
        rule_results, final_context = evaluate_rules(context)
        final_action = _resolve_final_action(rule_results, halt=final_context.halt)

        policy_fingerprint = policy.fingerprint()
        assessment_id = build_assessment_id(
            intent=intent,
            portfolio_id=snapshot.portfolio_id.value,
            portfolio_version=snapshot.portfolio_version,
            policy_fingerprint=policy_fingerprint,
        )
        assessment_hash = build_assessment_hash(
            assessment_id=assessment_id,
            intent=intent,
            portfolio_id=snapshot.portfolio_id.value,
            portfolio_version=snapshot.portfolio_version,
            policy_fingerprint=policy_fingerprint,
            policy_id=policy.risk_policy_id,
            policy_version=policy.risk_policy_version,
            policy_schema_version=policy.policy_schema_version,
            rule_results=rule_results,
            final_action=final_action.value,
        )
        assessment = RiskAssessment(
            assessment_id=assessment_id,
            assessment_hash=assessment_hash,
            policy_id=policy.risk_policy_id,
            policy_version=policy.risk_policy_version,
            policy_schema_version=policy.policy_schema_version,
            policy_fingerprint=policy_fingerprint,
            intent_id=intent.intent_id,
            portfolio_id=snapshot.portfolio_id,
            portfolio_version=snapshot.portfolio_version,
            rule_results=rule_results,
            final_action=final_action,
            evaluated_at=evaluated_at,
            correlation_id=intent.correlation_id,
            causation_id=intent.causation_id,
        )

        # Invariants: evaluation must not mutate inputs.
        if snapshot.portfolio_version != snapshot_version:
            msg = "portfolio snapshot mutated during risk evaluation"
            raise RuntimeError(msg)
        if intent.signed_quantity_delta != intent_quantity:
            msg = "proposed trade intent mutated during risk evaluation"
            raise RuntimeError(msg)
        if tuple(result.rule_id for result in rule_results) != RULE_ORDER:
            msg = "risk rule order invariant violated"
            raise RuntimeError(msg)

        self.metrics.record_assessment(assessment)
        self.audit_sink.record(
            RiskAuditRecord(
                assessment_id=assessment.assessment_id,
                intent_id=assessment.intent_id,
                portfolio_id=assessment.portfolio_id,
                portfolio_version=assessment.portfolio_version,
                final_action=assessment.final_action,
                policy_fingerprint=assessment.policy_fingerprint,
                recorded_at=evaluated_at,
                correlation_id=assessment.correlation_id,
                causation_id=assessment.causation_id,
            )
        )
        return assessment

    async def evaluate_and_publish(
        self,
        *,
        intent: ProposedTradeIntent,
        snapshot: PortfolioSnapshot,
        policy: RiskPolicy,
        evaluated_at: datetime,
    ) -> RiskAssessment:
        assessment = self.evaluate(
            intent=intent,
            snapshot=snapshot,
            policy=policy,
            evaluated_at=evaluated_at,
        )
        if self.assessment_sink is not None:
            try:
                await self.assessment_sink.publish_assessment(assessment)
            except RiskError:
                raise
            except Exception as exc:
                raise RiskDownstreamPublishError(detail=type(exc).__name__) from exc
        return assessment


def build_risk_engine(
    *,
    assessment_sink: RiskAssessmentSink | None = None,
    audit_max_records: int = 10_000,
) -> RiskEngine:
    return RiskEngine(
        assessment_sink=assessment_sink,
        audit_sink=InMemoryRiskAuditSink(max_records=audit_max_records),
    )


def _kill_switch_halt(rule_results: tuple[RiskRuleResult, ...]) -> bool:
    return any(
        result.rule_id.value == "risk.kill_switch" and result.status is RiskRuleStatus.FAIL
        for result in rule_results
    )


def _resolve_final_action(
    rule_results: tuple[RiskRuleResult, ...],
    *,
    halt: bool,
) -> RiskFinalAction:
    if halt or _kill_switch_halt(rule_results):
        return RiskFinalAction.HALT
    if any(result.status is RiskRuleStatus.FAIL for result in rule_results):
        return RiskFinalAction.REJECT
    return RiskFinalAction.APPROVE
