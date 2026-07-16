"""Portfolio model contract tests."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.portfolio.aggregate import PortfolioAggregate
from app.portfolio.decimal import canonical_decimal
from app.portfolio.errors import PortfolioDecimalError
from app.portfolio.hashing import build_ledger_entry_id, compute_snapshot_hash
from app.portfolio.models import FillApplied, PortfolioMutationType
from app.portfolio.policies import PortfolioPolicy
from pydantic import ValidationError
from tests.support.portfolio_helpers import account_id, fill, portfolio_id


def test_fill_model_forbids_extra_fields() -> None:
    data = fill().model_dump(mode="python")
    data["raw_broker_payload"] = {"secret": "nope"}
    with pytest.raises(ValidationError):
        FillApplied.model_validate(data)


def test_models_are_immutable() -> None:
    item = fill()
    with pytest.raises(ValidationError):
        item.quantity = Decimal("2")  # type: ignore[misc]


def test_decimal_policy_rejects_float_nan_inf_and_negative_values() -> None:
    with pytest.raises(PortfolioDecimalError):
        fill(quantity=1.0)
    with pytest.raises(PortfolioDecimalError):
        fill(price=Decimal("NaN"))
    with pytest.raises(PortfolioDecimalError):
        fill(fee=Decimal("Infinity"))
    with pytest.raises(PortfolioDecimalError):
        fill(price=Decimal("-1"))
    with pytest.raises(PortfolioDecimalError):
        fill(quantity=Decimal("0"))
    with pytest.raises(PortfolioDecimalError):
        fill(fee=Decimal("-0.01"))


def test_utc_and_pit_timestamps_required() -> None:
    data = fill().model_dump(mode="python")
    data["occurred_at"] = datetime(2026, 7, 15)
    with pytest.raises(ValidationError, match="timezone-aware"):
        FillApplied.model_validate(data)
    data = fill().model_dump(mode="python")
    data["known_at"] = data["occurred_at"]
    data["occurred_at"] = data["ingested_at"]
    with pytest.raises(ValidationError, match="occurred_at must be <= known_at"):
        FillApplied.model_validate(data)


def test_safe_metadata_is_bounded_and_rejects_sensitive_keys() -> None:
    data = fill().model_dump(mode="python")
    data["safe_metadata"] = {"api_token": "secret"}
    with pytest.raises(ValidationError, match="forbidden"):
        FillApplied.model_validate(data)


def test_snapshot_hash_is_deterministic_and_excludes_safe_metadata() -> None:
    policy = PortfolioPolicy()
    base = PortfolioAggregate.initial_snapshot(
        account_id=account_id(),
        portfolio_id=portfolio_id(),
        policy=policy,
        snapshot_at=datetime(2026, 7, 15, tzinfo=UTC),
        safe_metadata={"note": "one"},
    )
    other = base.model_copy(update={"safe_metadata": {"note": "two"}, "snapshot_hash": None})
    assert compute_snapshot_hash(base) == compute_snapshot_hash(other)


def test_snapshot_hash_excludes_approved_runtime_and_identity_fields() -> None:
    policy = PortfolioPolicy()
    base = PortfolioAggregate.initial_snapshot(
        account_id=account_id(),
        portfolio_id=portfolio_id(),
        policy=policy,
        snapshot_at=datetime(2026, 7, 15, tzinfo=UTC),
        safe_metadata={"note": "one"},
    )
    changed_excluded = base.model_copy(
        update={
            "account_id": account_id("acct-other"),
            "portfolio_id": portfolio_id("portfolio-other"),
            "last_applied_event_key": "different",
            "snapshot_at": datetime(2026, 7, 16, tzinfo=UTC),
            "safe_metadata": {"note": "two"},
            "snapshot_hash": None,
        }
    )
    changed_business = base.model_copy(
        update={"portfolio_version": base.portfolio_version + 1, "snapshot_hash": None}
    )
    assert compute_snapshot_hash(base) == compute_snapshot_hash(changed_excluded)
    assert compute_snapshot_hash(base) != compute_snapshot_hash(changed_business)


def test_ledger_entry_id_uses_approved_deterministic_inputs() -> None:
    base = build_ledger_entry_id(
        portfolio_id=portfolio_id(),
        portfolio_version=7,
        event_id="event-1",
        entry_index=0,
    )
    assert base == build_ledger_entry_id(
        portfolio_id=portfolio_id(),
        portfolio_version=7,
        event_id="event-1",
        entry_index=0,
    )
    assert base != build_ledger_entry_id(
        portfolio_id=portfolio_id("portfolio-other"),
        portfolio_version=7,
        event_id="event-1",
        entry_index=0,
    )
    assert base != build_ledger_entry_id(
        portfolio_id=portfolio_id(),
        portfolio_version=8,
        event_id="event-1",
        entry_index=0,
    )
    assert base != build_ledger_entry_id(
        portfolio_id=portfolio_id(),
        portfolio_version=7,
        event_id="event-2",
        entry_index=0,
    )
    assert base != build_ledger_entry_id(
        portfolio_id=portfolio_id(),
        portfolio_version=7,
        event_id="event-1",
        entry_index=1,
    )


def test_canonical_decimal_serialization_is_stable() -> None:
    assert canonical_decimal(Decimal("100.000000")) == "100"
    assert canonical_decimal(Decimal("0.0100")) == "0.01"


def test_ledger_entry_has_closed_mutation_vocabulary() -> None:
    assert PortfolioMutationType.FILL_APPLIED.value == "FILL_APPLIED"
