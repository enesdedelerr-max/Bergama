"""Broker command outcomes (#405). Mutually exclusive typed results."""

from __future__ import annotations

from enum import StrEnum


class BrokerCommandOutcome(StrEnum):
    """Typed broker command outcomes. Mutually exclusive."""

    ACKNOWLEDGED = "ACKNOWLEDGED"
    REJECTED = "REJECTED"
    FAILED_BEFORE_SEND = "FAILED_BEFORE_SEND"
    OUTCOME_UNKNOWN = "OUTCOME_UNKNOWN"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
