"""Portfolio Aggregate Foundation public contract tests."""

from __future__ import annotations

import inspect
from datetime import UTC, datetime

from app.portfolio import (
    AccountId,
    FillApplied,
    InMemoryPortfolioRepository,
    PortfolioAggregate,
    PortfolioId,
    PortfolioPolicy,
    PortfolioRepository,
    PortfolioService,
)
from app.portfolio.models import FillSide
from tests.support.portfolio_helpers import fill


def test_public_contract_exports_foundation_types_only() -> None:
    assert AccountId(value="acct-contract").value == "acct-contract"
    assert PortfolioId(value="portfolio-contract").value == "portfolio-contract"
    assert FillApplied is not None
    assert PortfolioAggregate is not None
    assert PortfolioService is not None
    assert PortfolioRepository is not None


def test_fill_output_vocabulary_is_not_broker_order_semantics() -> None:
    assert {item.value for item in FillSide} == {"buy", "sell"}
    names = set(dir(__import__("app.portfolio.models", fromlist=["*"])))
    forbidden = {"OrderIntent", "Order", "RiskApproval", "BrokerOrder"}
    assert names.isdisjoint(forbidden)


def test_repository_contract_has_no_storage_adapter_methods() -> None:
    members = set(dir(InMemoryPortfolioRepository()))
    forbidden = {
        "session",
        "engine",
        "producer",
        "consumer",
        "catalog",
        "database",
        "broker",
    }
    assert members.isdisjoint(forbidden)


def test_aggregate_constructor_accepts_only_snapshot_and_policy() -> None:
    signature = inspect.signature(PortfolioAggregate)
    assert tuple(signature.parameters) == ("snapshot", "policy")


def test_policy_fingerprint_is_deterministic() -> None:
    assert PortfolioPolicy().fingerprint() == PortfolioPolicy().fingerprint()
    assert (
        PortfolioPolicy(allow_short_positions=True).fingerprint() != PortfolioPolicy().fingerprint()
    )


def test_safe_fill_contract_has_provenance_not_strategy_accounting_bucket() -> None:
    item = fill(
        idx=1,
        side=FillSide.BUY,
        quantity="1",
        price="10",
    ).model_copy(update={"ingested_at": datetime(2026, 7, 15, tzinfo=UTC)})
    assert item.provenance.strategy_allocation_id is None
    assert item.instrument.instrument_key == "bergama:equity:us:aapl"
