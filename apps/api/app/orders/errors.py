"""Order Management System typed failures (#404)."""

from __future__ import annotations


class OrderError(Exception):
    code = "order.error"

    def __init__(self, message: str | None = None, *, detail: str | None = None) -> None:
        super().__init__(message or self.code)
        self.detail = detail


class OrderConfigurationError(OrderError):
    code = "order.configuration_invalid"


class OrderClosedError(OrderError):
    code = "order.closed"


class OrderAdmissionError(OrderError):
    code = "order.admission_rejected"


class OrderNotFoundError(OrderError):
    code = "order.not_found"


class OrderAlreadyExistsError(OrderError):
    code = "order.already_exists"


class OrderIllegalTransitionError(OrderError):
    code = "order.illegal_transition"


class OrderTerminalMutationError(OrderError):
    code = "order.terminal_mutation"


class OrderVersionConflictError(OrderError):
    code = "order.version_conflict"


class OrderIdempotencyConflictError(OrderError):
    code = "order.idempotency_conflict"


class OrderOverfillError(OrderError):
    code = "order.overfill"


class OrderOutOfOrderEventError(OrderError):
    code = "order.out_of_order_event"


class OrderDecimalError(OrderError):
    code = "order.decimal_invalid"


class OrderRepositoryError(OrderError):
    code = "order.repository_failure"


class OrderLockTimeoutError(OrderError):
    code = "order.lock_timeout"


class OrderBrokerPortError(OrderError):
    code = "order.broker_port_failed"


class OrderFillPortError(OrderError):
    code = "order.fill_port_failed"


class OrderMissingError(OrderNotFoundError):
    code = "order.missing"
