"""Typed broker errors — provider exceptions never cross BrokerOrderPort (#405)."""

from __future__ import annotations


class BrokerError(Exception):
    """Base broker-safe error. Never wraps raw provider payloads/secrets."""

    code: str = "broker.error"

    def __init__(self, detail: str = "") -> None:
        self.detail = detail
        super().__init__(f"{self.code}:{detail}" if detail else self.code)


class BrokerAuthenticationError(BrokerError):
    code = "broker.authentication"


class BrokerAuthorizationError(BrokerError):
    code = "broker.authorization"


class BrokerCapabilityMismatchError(BrokerError):
    code = "broker.capability_mismatch"


class BrokerValidationError(BrokerError):
    code = "broker.validation"


class BrokerTransportFailureError(BrokerError):
    code = "broker.transport_failure"


class BrokerTimeoutError(BrokerError):
    code = "broker.timeout"


class BrokerMalformedResponseError(BrokerError):
    code = "broker.malformed_response"


class BrokerUnknownOutcomeError(BrokerError):
    code = "broker.unknown_outcome"


class BrokerSequenceGapError(BrokerError):
    code = "broker.sequence_gap"


class BrokerDuplicateEventError(BrokerError):
    code = "broker.duplicate_event"


class BrokerAdapterClosedError(BrokerError):
    code = "broker.adapter_closed"


class BrokerReconciliationRequiredError(BrokerError):
    code = "broker.reconciliation_required"


class BrokerNotConfiguredError(BrokerError):
    code = "broker.not_configured"
