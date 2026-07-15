"""Strategy Engine coordinator."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.clock import Clock
from app.strategy.audit import InMemoryStrategyAuditSink
from app.strategy.config import StrategyConfig
from app.strategy.errors import StrategyClosedError, StrategyConfigurationError
from app.strategy.identity import StrategyIdentity
from app.strategy.ports import StrategyDecisionPort
from app.strategy.registry import StrategyRegistry
from app.strategy.session import StrategyBinding, StrategySession


@dataclass(slots=True)
class StrategyEngine:
    """Creates explicit, isolated StrategySession instances."""

    clock: Clock
    registry: StrategyRegistry
    decision_port: StrategyDecisionPort | None = None
    max_strategies_per_session: int = 16
    max_seen_inputs_per_session: int = 100_000
    audit_max_records: int = 10_000
    _closed: bool = False

    async def aclose(self) -> None:
        self._closed = True

    def create_session(
        self,
        *,
        run_id: str,
        session_id: str,
        strategies: tuple[tuple[StrategyIdentity, StrategyConfig], ...],
        decision_port: StrategyDecisionPort | None = None,
    ) -> StrategySession:
        if self._closed:
            raise StrategyClosedError()
        if len(strategies) > self.max_strategies_per_session:
            raise StrategyConfigurationError(detail="too_many_strategies")
        bindings = tuple(
            StrategyBinding(
                identity=identity,
                config=config,
                strategy=self.registry.create(identity, config),
            )
            for identity, config in strategies
        )
        return StrategySession(
            run_id=run_id,
            session_id=session_id,
            clock=self.clock,
            bindings=bindings,
            decision_port=decision_port if decision_port is not None else self.decision_port,
            max_seen_inputs=self.max_seen_inputs_per_session,
            audit_sink=InMemoryStrategyAuditSink(max_records=self.audit_max_records),
        )


def build_strategy_engine(
    *,
    clock: Clock,
    registry: StrategyRegistry | None = None,
    decision_port: StrategyDecisionPort | None = None,
    max_strategies_per_session: int = 16,
    max_seen_inputs_per_session: int = 100_000,
    audit_max_records: int = 10_000,
) -> StrategyEngine:
    return StrategyEngine(
        clock=clock,
        registry=registry if registry is not None else StrategyRegistry(),
        decision_port=decision_port,
        max_strategies_per_session=max_strategies_per_session,
        max_seen_inputs_per_session=max_seen_inputs_per_session,
        audit_max_records=audit_max_records,
    )
