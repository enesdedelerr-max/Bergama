"""Risk Engine identity constants and stable tokens."""

from __future__ import annotations

from typing import Final

from app.portfolio.identity import AccountId, PortfolioId

RULE_SET_VERSION: Final[str] = "risk-ruleset-v1"
POLICY_SCHEMA_VERSION: Final[str] = "1.0.0"
ASSESSMENT_ID_VERSION: Final[str] = "risk-assessment-id-v1"
ASSESSMENT_HASH_VERSION: Final[str] = "risk-assessment-hash-v1"

__all__ = [
    "ASSESSMENT_HASH_VERSION",
    "ASSESSMENT_ID_VERSION",
    "AccountId",
    "POLICY_SCHEMA_VERSION",
    "PortfolioId",
    "RULE_SET_VERSION",
]
