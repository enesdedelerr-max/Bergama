"""Typed Strategy Engine failures."""

from __future__ import annotations


class StrategyError(Exception):
    code = "strategy.error"

    def __init__(self, message: str | None = None, *, detail: str | None = None) -> None:
        super().__init__(message or self.code)
        self.detail = detail


class StrategyConfigurationError(StrategyError):
    code = "strategy.configuration_invalid"


class StrategyUnsupportedEventError(StrategyError):
    code = "strategy.unsupported_event"


class StrategyPitViolationError(StrategyError):
    code = "strategy.pit_violation"


class StrategyQualityRejectedError(StrategyError):
    code = "strategy.quality_rejected"


class StrategyDuplicateInputError(StrategyError):
    code = "strategy.duplicate_input"


class StrategyStateConflictError(StrategyError):
    code = "strategy.state_conflict"


class StrategyEvaluationError(StrategyError):
    code = "strategy.evaluation_failed"


class StrategyOutputValidationError(StrategyError):
    code = "strategy.output_invalid"


class StrategyClosedError(StrategyError):
    code = "strategy.closed"


class StrategyDownstreamPortMissingError(StrategyError):
    code = "strategy.downstream_port_missing"


class StrategyDownstreamPublishError(StrategyError):
    """Typed downstream delivery failure.

    Optional safe delivery context is for the #406 runtime path only.
    Legacy #401 callers may omit all optional fields.
    """

    code = "strategy.downstream_publish_failed"

    def __init__(
        self,
        message: str | None = None,
        *,
        detail: str | None = None,
        published_decision_ids: tuple[str, ...] = (),
        failed_decision_id: str | None = None,
        strategy_id: str | None = None,
        strategy_version: str | None = None,
        strategy_instance_id: str | None = None,
        correlation_id: str | None = None,
        causation_id: str | None = None,
    ) -> None:
        super().__init__(message, detail=detail)
        self.published_decision_ids = published_decision_ids
        self.failed_decision_id = failed_decision_id
        self.strategy_id = strategy_id
        self.strategy_version = strategy_version
        self.strategy_instance_id = strategy_instance_id
        self.correlation_id = correlation_id
        self.causation_id = causation_id


class StrategyRegistryError(StrategyError):
    code = "strategy.registry_error"


class StrategyAlreadyRegisteredError(StrategyRegistryError):
    code = "strategy.already_registered"


class StrategyNotFoundError(StrategyRegistryError):
    code = "strategy.not_found"
