"""Typed Strategy SDK failures for strategy authors."""

from __future__ import annotations


class StrategySdkError(Exception):
    code = "strategy_sdk.error"

    def __init__(self, message: str | None = None, *, detail: str | None = None) -> None:
        super().__init__(message or self.code)
        self.detail = detail


class StrategyValidationError(StrategySdkError):
    code = "strategy_sdk.validation_failed"


class StrategyConfigurationError(StrategySdkError):
    code = "strategy_sdk.configuration_invalid"


class StrategyCompatibilityError(StrategySdkError):
    code = "strategy_sdk.compatibility_failed"


class StrategyTimeoutError(StrategySdkError):
    code = "strategy_sdk.timeout"


class StrategyCancellationError(StrategySdkError):
    code = "strategy_sdk.cancellation"


class StrategyContractViolation(StrategySdkError):
    code = "strategy_sdk.contract_violation"


class StrategyPluginCrash(StrategySdkError):
    code = "strategy_sdk.plugin_crash"


class StrategyExecutionError(StrategySdkError):
    code = "strategy_sdk.execution_failed"


class StrategyBudgetExceededError(StrategySdkError):
    code = "strategy_sdk.budget_exceeded"


class StrategyStateError(StrategySdkError):
    code = "strategy_sdk.state_error"


class StrategyManifestError(StrategySdkError):
    code = "strategy_sdk.manifest_invalid"


class StrategyFeatureSchemaError(StrategySdkError):
    code = "strategy_sdk.feature_schema_error"


class StrategyPermissionError(StrategySdkError):
    code = "strategy_sdk.permission_denied"


class StrategyLifecycleError(StrategySdkError):
    code = "strategy_sdk.lifecycle_error"
