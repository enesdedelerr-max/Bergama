"""Unit tests for RiskEngine determinism and purity (#403)."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from app.risk.errors import RiskClosedError
from app.risk.hashing import build_assessment_hash
from app.risk.models import RiskFinalAction
from app.risk.ports import InMemoryRiskAssessmentSink
from tests.support.risk_helpers import T0, empty_snapshot, engine, intent, marked_snapshot, policy


def test_approve_path_is_deterministic() -> None:
    risk = engine()
    payload = dict(
        intent=intent(expected_portfolio_version=1, quantity_delta=Decimal("2")),
        snapshot=empty_snapshot(version=1),
        policy=policy(),
        evaluated_at=T0 + timedelta(seconds=1),
    )
    first = risk.evaluate(**payload)
    second = risk.evaluate(**payload)
    assert first.assessment_id == second.assessment_id
    assert first.assessment_hash == second.assessment_hash
    assert first.final_action is RiskFinalAction.APPROVE
    assert first.model_dump(exclude={"evaluated_at"}) == second.model_dump(exclude={"evaluated_at"})


def test_evaluated_at_does_not_change_assessment_id() -> None:
    risk = engine()
    base = dict(
        intent=intent(expected_portfolio_version=1),
        snapshot=empty_snapshot(version=1),
        policy=policy(),
    )
    a = risk.evaluate(**base, evaluated_at=T0 + timedelta(seconds=1))
    b = risk.evaluate(**base, evaluated_at=T0 + timedelta(seconds=10))
    assert a.assessment_id == b.assessment_id
    assert a.assessment_hash == b.assessment_hash
    assert a.evaluated_at != b.evaluated_at


def test_assessment_hash_matches_builder() -> None:
    risk = engine()
    snap = empty_snapshot(version=1)
    pol = policy()
    trade = intent(expected_portfolio_version=1)
    assessment = risk.evaluate(
        intent=trade,
        snapshot=snap,
        policy=pol,
        evaluated_at=T0 + timedelta(seconds=1),
    )
    recomputed = build_assessment_hash(
        assessment_id=assessment.assessment_id,
        intent=trade,
        portfolio_id=snap.portfolio_id.value,
        portfolio_version=snap.portfolio_version,
        policy_fingerprint=pol.fingerprint(),
        policy_id=pol.risk_policy_id,
        policy_version=pol.risk_policy_version,
        policy_schema_version=pol.policy_schema_version,
        rule_results=assessment.rule_results,
        final_action=assessment.final_action.value,
    )
    assert assessment.assessment_hash == recomputed


def test_evaluation_does_not_mutate_snapshot_or_intent() -> None:
    snap = marked_snapshot(version=3)
    trade = intent(expected_portfolio_version=3, quantity_delta=Decimal("1"))
    before_version = snap.portfolio_version
    before_qty = trade.signed_quantity_delta
    before_positions = snap.positions
    assessment = engine().evaluate(
        intent=trade,
        snapshot=snap,
        policy=policy(),
        evaluated_at=T0 + timedelta(seconds=1),
    )
    assert snap.portfolio_version == before_version
    assert trade.signed_quantity_delta == before_qty
    assert snap.positions is before_positions
    assert assessment.final_action in {
        RiskFinalAction.APPROVE,
        RiskFinalAction.REJECT,
        RiskFinalAction.HALT,
    }


def test_rejection_leaves_original_quantity_unchanged() -> None:
    trade = intent(
        expected_portfolio_version=1,
        quantity_delta=Decimal("9999"),
        reference_price=Decimal("100"),
    )
    original = trade.signed_quantity_delta
    assessment = engine().evaluate(
        intent=trade,
        snapshot=empty_snapshot(version=1),
        policy=policy(max_order_notional=Decimal("100")),
        evaluated_at=T0 + timedelta(seconds=1),
    )
    assert assessment.final_action is RiskFinalAction.REJECT
    assert trade.signed_quantity_delta == original


@pytest.mark.asyncio
async def test_evaluate_and_publish_uses_downstream_port() -> None:
    sink = InMemoryRiskAssessmentSink()
    risk = engine()
    risk.assessment_sink = sink
    assessment = await risk.evaluate_and_publish(
        intent=intent(expected_portfolio_version=1),
        snapshot=empty_snapshot(version=1),
        policy=policy(),
        evaluated_at=T0 + timedelta(seconds=1),
    )
    assert sink.assessments == (assessment,)


def test_evaluate_after_close_raises_typed_error() -> None:
    risk = engine()
    risk.close()
    risk.close()  # idempotent
    with pytest.raises(RiskClosedError):
        risk.evaluate(
            intent=intent(expected_portfolio_version=1),
            snapshot=empty_snapshot(version=1),
            policy=policy(),
            evaluated_at=T0 + timedelta(seconds=1),
        )


def test_no_reduce_or_resize_fields_on_assessment() -> None:
    assessment = engine().evaluate(
        intent=intent(expected_portfolio_version=1),
        snapshot=empty_snapshot(version=1),
        policy=policy(),
        evaluated_at=T0 + timedelta(seconds=1),
    )
    dumped = assessment.model_dump()
    assert "reduced_quantity" not in dumped
    assert "resized_quantity" not in dumped
    assert "new_quantity" not in dumped
