"""Independent deterministic fingerprints."""

from __future__ import annotations

from typing import Any

from bergama_strategy_sdk.serialization import sha256_hex


def strategy_fingerprint(
    *,
    strategy_id: str,
    strategy_version: str,
    strategy_instance_id: str,
    sdk_schema_version: str,
) -> str:
    return sha256_hex(
        {
            "sdk_schema_version": sdk_schema_version,
            "strategy_id": strategy_id,
            "strategy_instance_id": strategy_instance_id,
            "strategy_version": strategy_version,
        }
    )


def feature_fingerprint(snapshot_payload: dict[str, Any]) -> str:
    return sha256_hex(snapshot_payload)


def configuration_fingerprint(config_payload: dict[str, Any]) -> str:
    return sha256_hex(config_payload)


def state_fingerprint(state_payload: dict[str, Any]) -> str:
    return sha256_hex(state_payload)


def execution_fingerprint(
    *,
    strategy_fingerprint_value: str,
    feature_fingerprint_value: str,
    configuration_fingerprint_value: str,
    runtime_protocol_version: str,
    previous_state_fingerprint: str | None,
    fingerprint_rule_version: str = "1.0.0",
) -> str:
    return sha256_hex(
        {
            "configuration_fingerprint": configuration_fingerprint_value,
            "feature_fingerprint": feature_fingerprint_value,
            "fingerprint_rule_version": fingerprint_rule_version,
            "previous_state_fingerprint": previous_state_fingerprint,
            "runtime_protocol_version": runtime_protocol_version,
            "strategy_fingerprint": strategy_fingerprint_value,
        }
    )


def build_decision_id(
    *,
    strategy_id: str,
    strategy_version: str,
    strategy_instance_id: str,
    run_id: str,
    execution_fingerprint_value: str,
    action: str,
    runtime_protocol_version: str,
) -> str:
    """#406 decision identity relates to execution fingerprint without collapsing it."""
    return sha256_hex(
        {
            "action": action,
            "execution_fingerprint": execution_fingerprint_value,
            "runtime_protocol_version": runtime_protocol_version,
            "run_id": run_id,
            "strategy_id": strategy_id,
            "strategy_instance_id": strategy_instance_id,
            "strategy_version": strategy_version,
        }
    )
