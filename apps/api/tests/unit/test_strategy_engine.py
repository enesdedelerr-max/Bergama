"""Strategy Engine session and lifecycle tests (#401)."""

from __future__ import annotations

import asyncio
from datetime import timedelta

import pytest
from app.core.clock import FixedClock
from app.market_data.data_quality import QualityAction, QualitySeverity, QualityStatus
from app.market_data.identity import InstrumentId
from app.market_data.quality import DataQualityFlags
from app.strategy.config import StrategyConfig
from app.strategy.context import StrategyContext
from app.strategy.engine import build_strategy_engine
from app.strategy.errors import (
    StrategyClosedError,
    StrategyDownstreamPortMissingError,
    StrategyDownstreamPublishError,
    StrategyEvaluationError,
    StrategyOutputValidationError,
    StrategyPitViolationError,
    StrategyQualityRejectedError,
)
from app.strategy.models import StrategyDecision, StrategyInput
from app.strategy.ports import InMemoryStrategyDecisionPort
from app.strategy.reference import NoOpStrategy
from app.strategy.registry import StrategyRegistry
from pydantic import ValidationError
from tests.support.market_data_fixtures import T0, make_bar
from tests.support.strategy_helpers import (
    noop_config,
    quality_assessment,
    strategy_engine,
    strategy_identity,
)


@pytest.mark.asyncio
async def test_noop_strategy_emits_deterministic_decision_once_per_input() -> None:
    engine, port = strategy_engine(clock=FixedClock(T0))
    session = engine.create_session(
        run_id="run-1",
        session_id="session-1",
        strategies=((strategy_identity(), noop_config()),),
    )
    event = make_bar()

    first = await session.evaluate(event, quality_assessment=quality_assessment(event))
    duplicate = await session.evaluate(event, quality_assessment=quality_assessment(event))

    assert len(first) == 1
    assert duplicate == ()
    assert len(port.decisions) == 1
    assert first[0].decision_id == port.decisions[0].decision_id
    assert session.metrics.snapshot()["decisions_emitted_total"] == 1
    assert session.metrics.snapshot()["inputs_rejected_total"] == 1
    audit = session.audit_sink.records()
    assert len(audit) == 1
    assert audit[0].decision_id == first[0].decision_id
    assert "payload" not in audit[0].__dataclass_fields__


@pytest.mark.asyncio
async def test_same_input_config_and_clock_match_across_sessions() -> None:
    event = make_bar()
    identity = strategy_identity()
    config = noop_config()
    engine_a, _ = strategy_engine(clock=FixedClock(T0))
    engine_b, _ = strategy_engine(clock=FixedClock(T0))

    decision_a = (
        await engine_a.create_session(
            run_id="run-1",
            session_id="session-1",
            strategies=((identity, config),),
        ).evaluate(event, quality_assessment=quality_assessment(event))
    )[0]
    decision_b = (
        await engine_b.create_session(
            run_id="run-1",
            session_id="session-1",
            strategies=((identity, config),),
        ).evaluate(event, quality_assessment=quality_assessment(event))
    )[0]

    assert decision_a == decision_b


@pytest.mark.asyncio
async def test_degraded_inputs_are_explicitly_preserved() -> None:
    engine, _ = strategy_engine(clock=FixedClock(T0))
    session = engine.create_session(
        run_id="run-1",
        session_id="session-1",
        strategies=((strategy_identity(), noop_config()),),
    )
    event = make_bar(quality=DataQualityFlags(is_incomplete=True))
    assessment = quality_assessment(
        event,
        action=QualityAction.ACCEPT_DEGRADED,
        status=QualityStatus.DEGRADED,
        severity=QualitySeverity.WARNING,
    )
    decision = (await session.evaluate(event, quality_assessment=assessment))[0]
    assert decision.quality_summary.is_degraded is True
    assert decision.quality_summary.recommended_action is QualityAction.ACCEPT_DEGRADED
    assert session.metrics.snapshot()["inputs_degraded_total"] == 1


@pytest.mark.asyncio
async def test_rejected_quality_never_reaches_strategy_or_port() -> None:
    engine, port = strategy_engine(clock=FixedClock(T0))
    session = engine.create_session(
        run_id="run-1",
        session_id="session-1",
        strategies=((strategy_identity(), noop_config()),),
    )
    event = make_bar()
    assessment = quality_assessment(
        event,
        action=QualityAction.REJECT,
        status=QualityStatus.FAILED,
        severity=QualitySeverity.ERROR,
    )
    with pytest.raises(StrategyQualityRejectedError):
        await session.evaluate(event, quality_assessment=assessment)
    assert port.decisions == ()
    assert session.metrics.snapshot()["inputs_rejected_total"] == 1


@pytest.mark.asyncio
async def test_quarantine_and_halt_quality_never_reach_strategy_or_port() -> None:
    engine, port = strategy_engine(clock=FixedClock(T0))
    session = engine.create_session(
        run_id="run-1",
        session_id="session-1",
        strategies=((strategy_identity(), noop_config()),),
    )
    for action in (QualityAction.QUARANTINE, QualityAction.HALT_PIPELINE):
        event = make_bar(
            source=make_bar().source.model_copy(update={"source_event_id": action.value})
        )
        assessment = quality_assessment(
            event,
            action=action,
            status=QualityStatus.CRITICAL,
            severity=QualitySeverity.CRITICAL,
        )
        with pytest.raises(StrategyQualityRejectedError):
            await session.evaluate(event, quality_assessment=assessment)
    assert port.decisions == ()
    assert session.metrics.snapshot()["inputs_rejected_total"] == 2


@pytest.mark.asyncio
async def test_pit_invalid_input_is_rejected_before_strategy_evaluation() -> None:
    engine, port = strategy_engine(clock=FixedClock(T0))
    session = engine.create_session(
        run_id="run-1",
        session_id="session-1",
        strategies=((strategy_identity(), noop_config()),),
    )
    event = make_bar().model_copy(update={"known_at": T0 - timedelta(seconds=1)})
    with pytest.raises(StrategyPitViolationError):
        await session.evaluate(event, quality_assessment=quality_assessment(event))
    assert port.decisions == ()
    assert session.metrics.snapshot()["inputs_rejected_total"] == 1


@pytest.mark.asyncio
async def test_one_event_dispatches_to_multiple_strategies_in_declared_order() -> None:
    registry = StrategyRegistry()
    registry.register("noop-a", lambda _identity, _config: NoOpStrategy())
    registry.register("noop-b", lambda _identity, _config: NoOpStrategy())
    port = InMemoryStrategyDecisionPort()
    engine = build_strategy_engine(clock=FixedClock(T0), registry=registry, decision_port=port)
    session = engine.create_session(
        run_id="run-1",
        session_id="session-1",
        strategies=(
            (
                strategy_identity(strategy_id="noop-a", strategy_instance_id="noop-a:aapl"),
                noop_config(),
            ),
            (
                strategy_identity(strategy_id="noop-b", strategy_instance_id="noop-b:aapl"),
                noop_config(),
            ),
        ),
    )
    decisions = await session.evaluate(
        make_bar(), quality_assessment=quality_assessment(make_bar())
    )
    assert tuple(decision.strategy_id for decision in decisions) == ("noop-a", "noop-b")
    assert tuple(decision.strategy_id for decision in port.decisions) == ("noop-a", "noop-b")
    assert len(port.decisions) == 2
    assert session.metrics.snapshot()["decisions_emitted_total"] == 2


@pytest.mark.asyncio
async def test_stateful_strategy_instances_are_isolated_by_session_and_instrument() -> None:
    created: list[StatefulNoOpStrategy] = []
    registry = StrategyRegistry()

    def factory(_identity, _config):  # type: ignore[no-untyped-def]
        strategy = StatefulNoOpStrategy()
        created.append(strategy)
        return strategy

    registry.register("stateful", factory)
    engine = build_strategy_engine(
        clock=FixedClock(T0),
        registry=registry,
        decision_port=InMemoryStrategyDecisionPort(),
    )
    identity = strategy_identity(strategy_id="stateful", strategy_instance_id="stateful:aapl")
    session_a = engine.create_session(
        run_id="run-a",
        session_id="session-a",
        strategies=((identity, noop_config()),),
    )
    session_b = engine.create_session(
        run_id="run-b",
        session_id="session-b",
        strategies=((identity, noop_config()),),
    )
    event = make_bar()

    await session_a.evaluate(event, quality_assessment=quality_assessment(event))
    await session_b.evaluate(event, quality_assessment=quality_assessment(event))

    assert len(created) == 2
    assert created[0] is not created[1]
    assert created[0].snapshot() == {
        "evaluations": 1,
        "instrument_key": event.instrument.instrument_key,
    }
    assert created[1].snapshot() == {
        "evaluations": 1,
        "instrument_key": event.instrument.instrument_key,
    }


@pytest.mark.asyncio
async def test_missing_downstream_port_fails_closed() -> None:
    registry = StrategyRegistry()
    registry.register("noop", lambda _identity, _config: BrokenStrategy())
    engine = build_strategy_engine(clock=FixedClock(T0), registry=registry)
    session = engine.create_session(
        run_id="run-1",
        session_id="session-1",
        strategies=((strategy_identity(), StrategyConfig()),),
    )
    with pytest.raises(StrategyDownstreamPortMissingError):
        await session.evaluate(make_bar(), quality_assessment=quality_assessment(make_bar()))


@pytest.mark.asyncio
async def test_strategy_exception_is_contained_with_context() -> None:
    registry = StrategyRegistry()
    registry.register("noop", lambda _identity, _config: BrokenStrategy())
    engine = build_strategy_engine(
        clock=FixedClock(T0),
        registry=registry,
        decision_port=InMemoryStrategyDecisionPort(),
    )
    session = engine.create_session(
        run_id="run-1",
        session_id="session-1",
        strategies=((strategy_identity(), StrategyConfig()),),
    )
    with pytest.raises(StrategyEvaluationError) as exc:
        await session.evaluate(make_bar(), quality_assessment=quality_assessment(make_bar()))
    assert isinstance(exc.value.__cause__, RuntimeError)
    assert session.metrics.snapshot()["strategy_errors_total"] == 1


@pytest.mark.asyncio
async def test_invalid_strategy_output_is_typed_and_not_published() -> None:
    registry = StrategyRegistry()
    registry.register("noop", lambda _identity, _config: InvalidOutputStrategy())
    port = InMemoryStrategyDecisionPort()
    engine = build_strategy_engine(clock=FixedClock(T0), registry=registry, decision_port=port)
    session = engine.create_session(
        run_id="run-1",
        session_id="session-1",
        strategies=((strategy_identity(), StrategyConfig()),),
    )
    with pytest.raises(StrategyOutputValidationError):
        await session.evaluate(make_bar(), quality_assessment=quality_assessment(make_bar()))
    assert port.decisions == ()
    assert session.metrics.snapshot()["strategy_errors_total"] == 1


@pytest.mark.asyncio
async def test_cancellation_propagates_without_strategy_error_conversion() -> None:
    registry = StrategyRegistry()
    registry.register("noop", lambda _identity, _config: CancelledStrategy())
    engine = build_strategy_engine(
        clock=FixedClock(T0),
        registry=registry,
        decision_port=InMemoryStrategyDecisionPort(),
    )
    session = engine.create_session(
        run_id="run-1",
        session_id="session-1",
        strategies=((strategy_identity(), StrategyConfig()),),
    )
    with pytest.raises(asyncio.CancelledError):
        await session.evaluate(make_bar(), quality_assessment=quality_assessment(make_bar()))
    assert session.metrics.snapshot()["strategy_errors_total"] == 0


@pytest.mark.asyncio
async def test_downstream_failure_is_typed_and_decision_not_audited() -> None:
    engine, _ = strategy_engine(clock=FixedClock(T0), port=FailingDecisionPort())
    session = engine.create_session(
        run_id="run-1",
        session_id="session-1",
        strategies=((strategy_identity(), noop_config()),),
    )
    with pytest.raises(StrategyDownstreamPublishError):
        await session.evaluate(make_bar(), quality_assessment=quality_assessment(make_bar()))
    assert session.audit_sink.records() == ()
    assert session.metrics.snapshot()["downstream_errors_total"] == 1


@pytest.mark.asyncio
async def test_close_is_idempotent_and_blocks_new_work() -> None:
    engine, _ = strategy_engine(clock=FixedClock(T0))
    session = engine.create_session(
        run_id="run-1",
        session_id="session-1",
        strategies=((strategy_identity(), noop_config()),),
    )
    await session.aclose()
    await session.aclose()
    with pytest.raises(StrategyClosedError):
        await session.evaluate(make_bar(), quality_assessment=quality_assessment(make_bar()))
    await engine.aclose()
    with pytest.raises(StrategyClosedError):
        engine.create_session(
            run_id="run-2",
            session_id="session-2",
            strategies=((strategy_identity(), noop_config()),),
        )


def test_registry_rejects_duplicate_and_unknown_strategies() -> None:
    registry = StrategyRegistry()
    registry.register("noop", lambda _identity, _config: BrokenStrategy())
    with pytest.raises(Exception, match="strategy.already_registered"):
        registry.register("noop", lambda _identity, _config: BrokenStrategy())
    with pytest.raises(Exception, match="strategy.not_found"):
        registry.create(strategy_identity(strategy_id="missing"), StrategyConfig())
    with pytest.raises(ValidationError):
        registry.register("NoOp", lambda _identity, _config: BrokenStrategy())


class BrokenStrategy:
    async def evaluate(
        self,
        strategy_input: StrategyInput,
        context: StrategyContext,
    ) -> StrategyDecision:
        _ = strategy_input, context
        raise RuntimeError("strategy boom")


class InvalidOutputStrategy:
    async def evaluate(
        self,
        strategy_input: StrategyInput,
        context: StrategyContext,
    ) -> StrategyDecision:
        _ = strategy_input, context
        return "not-a-decision"  # type: ignore[return-value]


class CancelledStrategy:
    async def evaluate(
        self,
        strategy_input: StrategyInput,
        context: StrategyContext,
    ) -> StrategyDecision:
        _ = strategy_input, context
        raise asyncio.CancelledError


class StatefulNoOpStrategy:
    def __init__(self) -> None:
        self.strategy_instance_id = "stateful:aapl"
        self.instrument_id: InstrumentId | None = None
        self.evaluations = 0
        self._inner = NoOpStrategy()

    async def evaluate(
        self,
        strategy_input: StrategyInput,
        context: StrategyContext,
    ) -> StrategyDecision:
        self.instrument_id = strategy_input.instrument_id
        self.evaluations += 1
        return await self._inner.evaluate(strategy_input, context)

    def snapshot(self) -> dict[str, object]:
        return {
            "evaluations": self.evaluations,
            "instrument_key": self.instrument_id.instrument_key if self.instrument_id else None,
        }

    def restore(self, snapshot: dict[str, object]) -> None:
        self.evaluations = int(snapshot["evaluations"])


class FailingDecisionPort:
    async def publish_decision(self, decision: StrategyDecision) -> None:
        _ = decision
        raise RuntimeError("sink boom")
