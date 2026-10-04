"""Frozen Policy Version v1 reason semantic families."""

from __future__ import annotations

from enum import StrEnum


class AdeReasonFamily(StrEnum):
    """Semantic reason categories frozen by ``ai-decision-engine.policy.v1``."""

    ACCEPTED_GOVERNED_EVIDENCE = "accepted_governed_evidence"
    MISSING_AUTHORIZED_EVIDENCE = "missing_authorized_evidence"
    INVALID_AUTHORIZED_EVIDENCE = "invalid_authorized_evidence"
    STALE_EVIDENCE = "stale_evidence"
    CONFLICTING_OR_AMBIGUOUS_EVIDENCE = "conflicting_or_ambiguous_evidence"
    TEMPORAL_PIT_MISMATCH = "temporal_pit_mismatch"
    IDENTITY_INSUFFICIENCY = "identity_insufficiency"
    PROVENANCE_INSUFFICIENCY = "provenance_insufficiency"
    DETERMINISTIC_ACCEPTANCE_NOT_ESTABLISHED = "deterministic_acceptance_not_established"
    POLICY_CONTEXT_INSUFFICIENCY = "policy_context_insufficiency"


FROZEN_REASON_FAMILIES: frozenset[str] = frozenset(member.value for member in AdeReasonFamily)
