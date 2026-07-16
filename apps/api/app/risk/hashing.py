"""Deterministic Risk Engine hashing helpers."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any

from app.portfolio.decimal import canonical_decimal
from app.risk.identity import (
    ASSESSMENT_HASH_VERSION,
    ASSESSMENT_ID_VERSION,
    RULE_SET_VERSION,
)
from app.strategy.keys import strategy_sha256

if TYPE_CHECKING:
    from app.risk.models import ProposedTradeIntent, RiskRuleResult
    from app.risk.policy import RiskPolicy


def compute_policy_fingerprint(policy: RiskPolicy) -> str:
    return strategy_sha256(policy.fingerprint_payload())


def build_assessment_id(
    *,
    intent: ProposedTradeIntent,
    portfolio_id: str,
    portfolio_version: int,
    policy_fingerprint: str,
) -> str:
    return strategy_sha256(
        {
            "currency": intent.currency,
            "intent_id": intent.intent_id,
            "policy_fingerprint": policy_fingerprint,
            "portfolio_id": portfolio_id,
            "portfolio_version": portfolio_version,
            "quantity": canonical_decimal(intent.signed_quantity_delta),
            "reference_price": canonical_decimal(intent.reference_price),
            "rule_set_version": RULE_SET_VERSION,
            "version": ASSESSMENT_ID_VERSION,
        }
    )


def build_assessment_hash_payload(
    *,
    assessment_id: str,
    intent_id: str,
    portfolio_id: str,
    portfolio_version: int,
    policy_id: str,
    policy_version: str,
    policy_schema_version: str,
    policy_fingerprint: str,
    currency: str,
    quantity: Decimal,
    reference_price: Decimal,
    rule_results: tuple[RiskRuleResult, ...],
    final_action: str,
) -> dict[str, Any]:
    return {
        "assessment_id": assessment_id,
        "currency": currency,
        "final_action": final_action,
        "intent_id": intent_id,
        "policy_fingerprint": policy_fingerprint,
        "policy_id": policy_id,
        "policy_schema_version": policy_schema_version,
        "policy_version": policy_version,
        "portfolio_id": portfolio_id,
        "portfolio_version": portfolio_version,
        "quantity": canonical_decimal(quantity),
        "reference_price": canonical_decimal(reference_price),
        "rule_results": [_rule_hash_payload(result) for result in rule_results],
        "rule_set_version": RULE_SET_VERSION,
        "version": ASSESSMENT_HASH_VERSION,
    }


def build_assessment_hash(
    *,
    assessment_id: str,
    intent: ProposedTradeIntent,
    portfolio_id: str,
    portfolio_version: int,
    policy_fingerprint: str,
    policy_id: str,
    policy_version: str,
    policy_schema_version: str,
    rule_results: tuple[RiskRuleResult, ...],
    final_action: str,
) -> str:
    return strategy_sha256(
        build_assessment_hash_payload(
            assessment_id=assessment_id,
            intent_id=intent.intent_id,
            portfolio_id=portfolio_id,
            portfolio_version=portfolio_version,
            policy_id=policy_id,
            policy_version=policy_version,
            policy_schema_version=policy_schema_version,
            policy_fingerprint=policy_fingerprint,
            currency=intent.currency,
            quantity=intent.signed_quantity_delta,
            reference_price=intent.reference_price,
            rule_results=rule_results,
            final_action=final_action,
        )
    )


def _rule_hash_payload(result: RiskRuleResult) -> dict[str, Any]:
    return {
        "limit_value": result.limit_value,
        "observed_value": result.observed_value,
        "rule_id": result.rule_id.value,
        "severity": result.severity.value,
        "status": result.status.value,
    }
