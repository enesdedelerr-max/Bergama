"""Typed BrokerError hierarchy (#405)."""

from __future__ import annotations

from app.broker.errors import (
    BrokerAdapterClosedError,
    BrokerAuthenticationError,
    BrokerAuthorizationError,
    BrokerCapabilityMismatchError,
    BrokerDuplicateEventError,
    BrokerError,
    BrokerMalformedResponseError,
    BrokerReconciliationRequiredError,
    BrokerSequenceGapError,
    BrokerTimeoutError,
    BrokerTransportFailureError,
    BrokerUnknownOutcomeError,
    BrokerValidationError,
)


def test_broker_error_hierarchy_codes() -> None:
    errors: list[type[BrokerError]] = [
        BrokerAuthenticationError,
        BrokerAuthorizationError,
        BrokerCapabilityMismatchError,
        BrokerValidationError,
        BrokerTransportFailureError,
        BrokerTimeoutError,
        BrokerMalformedResponseError,
        BrokerUnknownOutcomeError,
        BrokerSequenceGapError,
        BrokerDuplicateEventError,
        BrokerAdapterClosedError,
        BrokerReconciliationRequiredError,
    ]
    codes = {cls().code for cls in errors}
    assert len(codes) == len(errors)
    for cls in errors:
        assert issubclass(cls, BrokerError)
        assert not any(token in cls().code.lower() for token in ("password", "token", "secret"))
