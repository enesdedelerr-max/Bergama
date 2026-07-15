"""Data-quality settings and policy tests (#310)."""

from __future__ import annotations

import json

import pytest
from app.core.config import AppSettings
from app.core.data_quality_settings import DataQualitySettings
from app.core.environment import AppEnvironment
from app.core.secrets import SecretSettings
from app.market_data.data_quality import (
    QualityPolicy,
    QualityRuleId,
    QualitySeverity,
    default_quality_policy,
    load_quality_policy_file,
)
from tests.conftest import VALID_PROD_JWT_SECRET


def test_data_quality_settings_are_safe_by_default() -> None:
    settings = DataQualitySettings()
    assert settings.enabled is False
    assert settings.observe_only is True
    assert settings.reject_on_error is False
    assert settings.halt_on_critical is False
    assert settings.quarantine_enabled is False


def test_app_settings_include_data_quality_safe_summary() -> None:
    settings = AppSettings(
        environment=AppEnvironment.TEST,
        bootstrap_auth_enabled=True,
        secrets=SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
    )
    summary = settings.safe_summary()["data_quality"]
    assert summary["enabled"] is False
    assert summary["observe_only"] is True
    assert summary["policy_file_configured"] is False


def test_required_policy_file_must_be_configured() -> None:
    with pytest.raises(ValueError, match="POLICY_FILE"):
        DataQualitySettings(enabled=True, policy_required=True)


def test_policy_fingerprint_is_deterministic() -> None:
    p1 = default_quality_policy()
    p2 = default_quality_policy()
    assert p1.fingerprint() == p2.fingerprint()
    assert len(p1.fingerprint()) == 64


def test_observe_only_action_resolution_degrades_without_enforcement() -> None:
    policy = default_quality_policy(observe_only=True, reject_on_error=True, halt_on_critical=True)
    action = policy.resolve_action(
        status="critical",  # type: ignore[arg-type]
        highest_severity=QualitySeverity.CRITICAL,
    )
    assert action.value == "accept_degraded"


def test_policy_loader_accepts_json_and_rejects_duplicate_yaml(tmp_path) -> None:
    policy_file = tmp_path / "quality-policy.json"
    policy_file.write_text(
        json.dumps(
            {
                "policy_version": "1.0.0",
                "enabled_rules": [QualityRuleId.FRESHNESS_EVENT_STALE.value],
                "observe_only": True,
            }
        ),
        encoding="utf-8",
    )
    loaded = load_quality_policy_file(str(policy_file), max_file_size_bytes=10_000)
    assert loaded.enabled_rules == (QualityRuleId.FRESHNESS_EVENT_STALE,)

    duplicate = tmp_path / "bad.yaml"
    duplicate.write_text("policy_version: 1.0.0\npolicy_version: 1.0.1\n", encoding="utf-8")
    with pytest.raises(Exception, match="duplicate"):
        load_quality_policy_file(str(duplicate), max_file_size_bytes=10_000)


def test_policy_rejects_unknown_rule_id() -> None:
    with pytest.raises(ValueError):
        QualityPolicy(enabled_rules=["not.a.rule"])  # type: ignore[list-item]
