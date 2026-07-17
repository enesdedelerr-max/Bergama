"""Execution budget enforcement (#406)."""

from __future__ import annotations

from dataclasses import dataclass

from bergama_strategy_sdk.config import StrategyConfig
from bergama_strategy_sdk.errors import StrategyBudgetExceededError
from bergama_strategy_sdk.execution import StrategyExecutionOutput
from bergama_strategy_sdk.features import FeatureSnapshot
from bergama_strategy_sdk.manifest import StrategyPluginManifest
from bergama_strategy_sdk.state import NextStrategyState, PreviousStrategyState


@dataclass(frozen=True, slots=True)
class ExecutionBudgets:
    execution_timeout_ms: int = 5_000
    max_feature_payload_bytes: int = 65_536
    max_output_bytes: int = 16_384
    max_safe_metadata_bytes: int = 4_096
    max_state_bytes: int = 16_384
    max_plugin_failures_per_batch: int = 32
    max_required_features: int = 64
    max_manifest_bytes: int = 32_768

    def validate_feature_snapshot(self, snapshot: FeatureSnapshot) -> None:
        if snapshot.payload_byte_length() > self.max_feature_payload_bytes:
            raise StrategyBudgetExceededError(detail="feature_payload")

    def validate_manifest(self, manifest: StrategyPluginManifest) -> None:
        if len(manifest.model_dump_json().encode("utf-8")) > self.max_manifest_bytes:
            raise StrategyBudgetExceededError(detail="manifest")
        if len(manifest.required_features) > self.max_required_features:
            raise StrategyBudgetExceededError(detail="required_features")

    def validate_config(self, config: StrategyConfig) -> None:
        self.validate_safe_metadata(config.safe_metadata)

    def validate_state(self, state: PreviousStrategyState | NextStrategyState) -> None:
        if len(state.model_dump_json().encode("utf-8")) > self.max_state_bytes:
            raise StrategyBudgetExceededError(detail="state")

    def validate_safe_metadata(self, metadata: dict[str, str]) -> None:
        encoded = str(dict(sorted(metadata.items()))).encode("utf-8")
        if len(encoded) > self.max_safe_metadata_bytes:
            raise StrategyBudgetExceededError(detail="safe_metadata")

    def validate_failure_metadata(self, metadata: dict[str, str]) -> None:
        encoded = str(dict(sorted(metadata.items()))).encode("utf-8")
        if len(encoded) > self.max_safe_metadata_bytes:
            raise StrategyBudgetExceededError(detail="runtime_failure_metadata")

    def validate_output(self, output: StrategyExecutionOutput) -> None:
        if len(output.model_dump_json().encode("utf-8")) > self.max_output_bytes:
            raise StrategyBudgetExceededError(detail="output")
        self.validate_safe_metadata(output.decision.safe_metadata)
        if output.next_state is not None:
            self.validate_state(output.next_state)

    def validate_failure_count(self, failure_count: int) -> None:
        if failure_count > self.max_plugin_failures_per_batch:
            raise StrategyBudgetExceededError(detail="plugin_failures_per_batch")
