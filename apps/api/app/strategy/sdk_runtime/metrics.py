"""Runtime metrics for #406 SDK orchestration."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class StrategySdkRuntimeMetrics:
    plugin_initialized_total: int = 0
    plugin_ready_total: int = 0
    plugin_failed_total: int = 0
    plugin_disabled_total: int = 0
    plugin_incompatible_total: int = 0
    plugin_disposed_total: int = 0
    execution_success_total: int = 0
    execution_timeout_total: int = 0
    contract_violation_total: int = 0
    plugin_crash_total: int = 0
    budget_violation_total: int = 0
    cancellation_total: int = 0
    skipped_plugin_total: int = 0
    batch_partial_success_total: int = 0
    downstream_failure_total: int = 0
    compatibility_rejection_total: int = 0
    experimental_rejection_total: int = 0
    state_error_total: int = 0
    feature_assembly_error_total: int = 0
    feature_schema_rejection_total: int = 0
    plugin_replaced_total: int = 0
    plugin_replace_rejected_total: int = 0
    plugin_replace_cancelled_total: int = 0

    def snapshot(self) -> dict[str, int]:
        return {
            "plugin_initialized_total": self.plugin_initialized_total,
            "plugin_ready_total": self.plugin_ready_total,
            "plugin_failed_total": self.plugin_failed_total,
            "plugin_disabled_total": self.plugin_disabled_total,
            "plugin_incompatible_total": self.plugin_incompatible_total,
            "plugin_disposed_total": self.plugin_disposed_total,
            "plugin_replaced_total": self.plugin_replaced_total,
            "plugin_replace_rejected_total": self.plugin_replace_rejected_total,
            "plugin_replace_cancelled_total": self.plugin_replace_cancelled_total,
            "execution_success_total": self.execution_success_total,
            "execution_timeout_total": self.execution_timeout_total,
            "contract_violation_total": self.contract_violation_total,
            "plugin_crash_total": self.plugin_crash_total,
            "budget_violation_total": self.budget_violation_total,
            "cancellation_total": self.cancellation_total,
            "skipped_plugin_total": self.skipped_plugin_total,
            "batch_partial_success_total": self.batch_partial_success_total,
            "downstream_failure_total": self.downstream_failure_total,
            "compatibility_rejection_total": self.compatibility_rejection_total,
            "experimental_rejection_total": self.experimental_rejection_total,
            "state_error_total": self.state_error_total,
            "feature_assembly_error_total": self.feature_assembly_error_total,
            "feature_schema_rejection_total": self.feature_schema_rejection_total,
        }

    def clear(self) -> None:
        self.plugin_initialized_total = 0
        self.plugin_ready_total = 0
        self.plugin_failed_total = 0
        self.plugin_disabled_total = 0
        self.plugin_incompatible_total = 0
        self.plugin_disposed_total = 0
        self.execution_success_total = 0
        self.execution_timeout_total = 0
        self.contract_violation_total = 0
        self.plugin_crash_total = 0
        self.budget_violation_total = 0
        self.cancellation_total = 0
        self.skipped_plugin_total = 0
        self.batch_partial_success_total = 0
        self.downstream_failure_total = 0
        self.compatibility_rejection_total = 0
        self.experimental_rejection_total = 0
        self.state_error_total = 0
        self.feature_assembly_error_total = 0
        self.feature_schema_rejection_total = 0
        self.plugin_replaced_total = 0
        self.plugin_replace_rejected_total = 0
        self.plugin_replace_cancelled_total = 0
