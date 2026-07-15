"""Strategy session lifecycle and evaluation fan-out."""

from __future__ import annotations

from dataclasses import dataclass, field

from pydantic import ValidationError

from app.core.clock import Clock
from app.market_data.data_quality.models import QualityAction, QualityAssessment
from app.market_data.envelope import CanonicalMarketEvent
from app.market_data.keys import build_deduplication_key, build_idempotency_key
from app.strategy.audit import (
    InMemoryStrategyAuditSink,
    StrategyAuditSink,
    audit_from_decision,
)
from app.strategy.config import StrategyConfig
from app.strategy.context import StrategyContext
from app.strategy.errors import (
    StrategyClosedError,
    StrategyDownstreamPortMissingError,
    StrategyDownstreamPublishError,
    StrategyEvaluationError,
    StrategyOutputValidationError,
    StrategyPitViolationError,
    StrategyQualityRejectedError,
)
from app.strategy.identity import StrategyIdentity
from app.strategy.metrics import StrategyMetrics
from app.strategy.models import QualitySummary, StrategyDecision, StrategyInput
from app.strategy.ports import StrategyDecisionPort
from app.strategy.protocol import Strategy


@dataclass(frozen=True, slots=True)
class StrategyBinding:
    identity: StrategyIdentity
    config: StrategyConfig
    strategy: Strategy


@dataclass(slots=True)
class StrategySession:
    """Explicit, isolated strategy run. No startup execution."""

    run_id: str
    session_id: str
    clock: Clock
    bindings: tuple[StrategyBinding, ...]
    decision_port: StrategyDecisionPort | None
    max_seen_inputs: int = 100_000
    audit_sink: StrategyAuditSink = field(default_factory=InMemoryStrategyAuditSink)
    metrics: StrategyMetrics = field(default_factory=StrategyMetrics)
    _closed: bool = field(default=False, init=False, repr=False)
    _seen_inputs: set[str] = field(default_factory=set, init=False, repr=False)
    _seen_input_order: list[str] = field(default_factory=list, init=False, repr=False)

    @property
    def closed(self) -> bool:
        return self._closed

    async def aclose(self) -> None:
        if self._closed:
            return
        self._closed = True
        self.audit_sink.clear()
        self.metrics.clear()
        self._seen_inputs.clear()
        self._seen_input_order.clear()

    async def evaluate(
        self,
        event: CanonicalMarketEvent,
        *,
        quality_assessment: QualityAssessment | None = None,
        correlation_id: str | None = None,
        causation_id: str | None = None,
    ) -> tuple[StrategyDecision, ...]:
        if self._closed:
            raise StrategyClosedError()
        if self.decision_port is None:
            raise StrategyDownstreamPortMissingError()
        quality = QualitySummary.from_event_and_assessment(event, quality_assessment)
        if quality.recommended_action not in {
            None,
            QualityAction.ACCEPT,
            QualityAction.ACCEPT_DEGRADED,
        }:
            self.metrics.record_rejected_input()
            raise StrategyQualityRejectedError(detail=str(quality.recommended_action))
        try:
            strategy_input = StrategyInput(
                event=event,
                instrument_id=event.instrument,
                run_id=self.run_id,
                session_id=self.session_id,
                idempotency_key=build_idempotency_key(event),
                deduplication_key=build_deduplication_key(event),
                correlation_id=correlation_id,
                causation_id=causation_id,
                quality_summary=quality,
                received_at=self.clock.now(),
            )
        except ValidationError as exc:
            self.metrics.record_rejected_input()
            raise StrategyPitViolationError(detail="strategy_input_invalid") from exc
        self.metrics.record_input(strategy_input)
        if strategy_input.idempotency_key in self._seen_inputs:
            self.metrics.record_rejected_input()
            return ()
        while len(self._seen_input_order) >= self.max_seen_inputs:
            evicted = self._seen_input_order.pop(0)
            self._seen_inputs.discard(evicted)
        self._seen_inputs.add(strategy_input.idempotency_key)
        self._seen_input_order.append(strategy_input.idempotency_key)

        decisions: list[StrategyDecision] = []
        for binding in self.bindings:
            context = StrategyContext(
                identity=binding.identity,
                run_id=self.run_id,
                session_id=self.session_id,
                clock=self.clock,
                configuration_fingerprint=binding.config.fingerprint(),
                correlation_id=correlation_id,
                causation_id=causation_id,
            )
            try:
                decision = await binding.strategy.evaluate(strategy_input, context)
            except Exception as exc:
                self.metrics.record_strategy_error()
                raise StrategyEvaluationError(detail=type(exc).__name__) from exc
            if not isinstance(decision, StrategyDecision):
                self.metrics.record_strategy_error()
                raise StrategyOutputValidationError(detail=type(decision).__name__)
            try:
                await self.decision_port.publish_decision(decision)
            except Exception as exc:
                self.metrics.record_downstream_error()
                raise StrategyDownstreamPublishError(detail=type(exc).__name__) from exc
            self.metrics.record_decision(decision)
            self.audit_sink.record(
                audit_from_decision(
                    strategy_input.idempotency_key,
                    decision_action=decision.action,
                    decision_reason_codes=decision.reason_codes,
                    decision_id=decision.decision_id,
                    strategy_id=decision.strategy_id,
                    strategy_version=decision.strategy_version,
                    strategy_instance_id=decision.strategy_instance_id,
                    run_id=decision.run_id,
                    instrument_key=decision.instrument_id.instrument_key,
                    occurred_at=decision.occurred_at,
                    decision_timestamp=decision.decision_timestamp,
                    configuration_fingerprint=decision.configuration_fingerprint,
                    quality_assessment_id=decision.quality_summary.assessment_id,
                    quality_status=decision.quality_summary.overall_status,
                    quality_highest_severity=decision.quality_summary.highest_severity,
                    quality_action=(
                        decision.quality_summary.recommended_action.value
                        if decision.quality_summary.recommended_action is not None
                        else None
                    ),
                    correlation_id=decision.correlation_id,
                    causation_id=decision.causation_id,
                )
            )
            decisions.append(decision)
        return tuple(decisions)
