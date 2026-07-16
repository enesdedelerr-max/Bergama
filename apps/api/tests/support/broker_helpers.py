"""Shared broker abstraction test helpers (#405)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.broker import (
    BrokerAccountId,
    BrokerIdentity,
    BrokerName,
    PaperBroker,
    PaperBrokerOrderPort,
    PaperBrokerPolicy,
    SubmitExecutableOrder,
)
from app.broker.hashing import executable_order_hash
from app.broker.outcomes import BrokerCommandOutcome
from app.core.clock import FixedClock
from app.orders.aggregate import OrderAggregate
from app.orders.models import ExecutableOrder
from app.orders.policies import OrderPolicy
from tests.support.order_helpers import submit_cmd

T0 = datetime(2026, 7, 16, 12, 0, tzinfo=UTC)


def executable_order_from_submit(command=None) -> ExecutableOrder:
    command = command or submit_cmd(client_order_id="broker-client-1")
    result = OrderAggregate(None, policy=OrderPolicy()).submit(command, created_at=T0)
    assert result.broker_commands
    assert result.broker_commands[0].executable_order is not None
    return result.broker_commands[0].executable_order


def paper_broker(
    *,
    seed: int = 0,
    force_outcome: BrokerCommandOutcome | None = None,
    auto_fill_market: bool = False,
) -> PaperBroker:
    return PaperBroker(
        clock=FixedClock(T0),
        identity=BrokerIdentity(
            broker_name=BrokerName(value="paper"),
            broker_account_id=BrokerAccountId(value="paper-account-1"),
        ),
        policy=PaperBrokerPolicy(
            auto_accept=True,
            auto_fill_market=auto_fill_market,
            force_outcome=force_outcome,
        ),
        simulation_seed=seed,
    )


def submit_executable(
    order: ExecutableOrder | None = None,
    *,
    idempotency_key: str = "broker-submit-1",
) -> SubmitExecutableOrder:
    order = order or executable_order_from_submit()
    return SubmitExecutableOrder(
        executable_order=order,
        idempotency_key=idempotency_key,
        correlation_id="corr-broker-1",
        causation_id="cause-broker-1",
    )


def oms_paper_port(broker: PaperBroker | None = None) -> tuple[PaperBroker, PaperBrokerOrderPort]:
    paper = broker or paper_broker()
    return paper, PaperBrokerOrderPort(paper)


__all__ = [
    "T0",
    "executable_order_from_submit",
    "executable_order_hash",
    "oms_paper_port",
    "paper_broker",
    "submit_executable",
    "timedelta",
    "Decimal",
]
