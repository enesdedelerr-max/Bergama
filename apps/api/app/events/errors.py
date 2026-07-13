"""Canonical event runtime errors (Issue #208A)."""

from __future__ import annotations


class EventRuntimeError(Exception):
    """Base typed error for event/Kafka runtime."""

    code: str = "event.runtime_error"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        if code is not None:
            self.code = code


class EventSerializationError(EventRuntimeError):
    code = "event.serialization_failed"


class EventDeserializationError(EventRuntimeError):
    code = "event.deserialization_failed"


class EventSchemaInvalidError(EventRuntimeError):
    code = "event.schema_invalid"


class EventHashMismatchError(EventRuntimeError):
    code = "event.hash_mismatch"


class EventInvalidError(EventRuntimeError):
    code = "event.invalid"


class EventHandlerFailedError(EventRuntimeError):
    code = "event.handler_failed"


class EventRetryExhaustedError(EventRuntimeError):
    code = "event.retry_exhausted"


class KafkaNotConfiguredError(EventRuntimeError):
    code = "kafka.not_configured"


class KafkaStartFailedError(EventRuntimeError):
    code = "kafka.start_failed"


class KafkaPublishFailedError(EventRuntimeError):
    code = "kafka.publish_failed"


class KafkaConsumeFailedError(EventRuntimeError):
    code = "kafka.consume_failed"


class KafkaCommitFailedError(EventRuntimeError):
    code = "kafka.commit_failed"


class KafkaShutdownFailedError(EventRuntimeError):
    code = "kafka.shutdown_failed"


class DlqUnavailableError(EventRuntimeError):
    code = "dlq.unavailable"


class EventProcessingError(EventRuntimeError):
    """Handler or processing failure carrying the original cause code."""

    code = "event.handler_failed"
