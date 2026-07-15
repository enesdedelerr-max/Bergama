"""Data-quality subsystem contract tests (#310)."""

from __future__ import annotations

import inspect

from app.market_data.data_quality import (
    ALL_RULE_IDS,
    QualityAction,
    QualityAssessment,
    QualityRuleId,
    QualityRuleResult,
    QuarantinePort,
)
from app.market_data.quality import DataQualityFlags


def test_rule_registry_is_closed_to_approved_ids() -> None:
    expected = {
        "schema.required_field",
        "schema.invalid_decimal",
        "pit.invalid_order",
        "identity.key_mismatch",
        "identity.invalid_source",
        "freshness.event_stale",
        "freshness.ingestion_lag",
        "freshness.known_to_ingested_lag",
        "completeness.missing_value",
        "completeness.incomplete_flag",
        "value.invalid_ohlc",
        "value.crossed_quote",
        "value.negative_quantity",
        "value.invalid_price",
        "duplication.duplicate_observation",
        "source.invalid_provenance",
        "source.unsafe_metadata",
        "operational.publish_failed",
        "operational.writer_failed",
        "operational.checkpoint_failed",
        "operational.admission_overflow",
    }
    assert {rule.value for rule in ALL_RULE_IDS} == expected
    assert {rule.value for rule in QualityRuleId} == expected


def test_assessment_and_rule_result_are_payload_free() -> None:
    assessment_fields = set(QualityAssessment.model_fields)
    assert "payload" not in assessment_fields
    assert "raw_payload" not in assessment_fields
    assert "provider_body" not in assessment_fields
    result_fields = set(QualityRuleResult.model_fields)
    assert "payload" not in result_fields
    assert "safe_metadata" in result_fields


def test_quarantine_port_does_not_publish_or_write_provider_payloads() -> None:
    sig = inspect.signature(QuarantinePort.quarantine)
    assert set(sig.parameters) == {"self", "event", "assessment", "correlation_id"}


def test_existing_data_quality_flags_contract_remains_available() -> None:
    flags = DataQualityFlags()
    assert flags.is_late is False
    assert flags.is_revision is False
    assert flags.is_stale is False


def test_action_taxonomy_is_explicit() -> None:
    assert {action.value for action in QualityAction} == {
        "accept",
        "accept_degraded",
        "quarantine",
        "reject",
        "halt_pipeline",
    }
