"""Broker abstraction package (#405).

Owns provider communication boundaries and typed broker facts only.
Never owns OMS order state, transitions, or versions.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "BrokerAccountId",
    "BrokerAdapterClosedError",
    "BrokerAdapterLifecycle",
    "BrokerAuthenticationError",
    "BrokerAuthorizationError",
    "BrokerCancelResult",
    "BrokerCapabilities",
    "BrokerCapabilityMismatchError",
    "BrokerCommandOutcome",
    "BrokerDuplicateEventError",
    "BrokerError",
    "BrokerFillEvent",
    "BrokerIdentity",
    "BrokerLifecycleEvent",
    "BrokerLifecycleEventType",
    "BrokerMalformedResponseError",
    "BrokerName",
    "BrokerNotConfiguredError",
    "BrokerOrderCommandPort",
    "BrokerOrderPort",
    "BrokerReconciliationRequiredError",
    "BrokerSequenceGapError",
    "BrokerSubmissionResult",
    "BrokerTimeoutError",
    "BrokerTransportFailureError",
    "BrokerUnknownOutcomeError",
    "BrokerValidationError",
    "CancelExecutableOrder",
    "PaperBroker",
    "PaperBrokerOrderPort",
    "PaperBrokerPolicy",
    "SubmitExecutableOrder",
    "paper_broker_capabilities",
    "validate_before_submit",
]


def __getattr__(name: str) -> Any:
    if name in {
        "BrokerCapabilities",
        "paper_broker_capabilities",
    }:
        from app.broker import capabilities as capabilities_mod

        return getattr(capabilities_mod, name)
    if name in {
        "BrokerError",
        "BrokerAuthenticationError",
        "BrokerAuthorizationError",
        "BrokerCapabilityMismatchError",
        "BrokerValidationError",
        "BrokerTransportFailureError",
        "BrokerTimeoutError",
        "BrokerMalformedResponseError",
        "BrokerUnknownOutcomeError",
        "BrokerSequenceGapError",
        "BrokerDuplicateEventError",
        "BrokerAdapterClosedError",
        "BrokerReconciliationRequiredError",
        "BrokerNotConfiguredError",
    }:
        from app.broker import errors as errors_mod

        return getattr(errors_mod, name)
    if name in {"BrokerAccountId", "BrokerIdentity", "BrokerName"}:
        from app.broker import identity as identity_mod

        return getattr(identity_mod, name)
    if name == "BrokerAdapterLifecycle":
        from app.broker.lifecycle import BrokerAdapterLifecycle

        return BrokerAdapterLifecycle
    if name == "BrokerCommandOutcome":
        from app.broker.outcomes import BrokerCommandOutcome

        return BrokerCommandOutcome
    if name in {
        "BrokerCancelResult",
        "BrokerFillEvent",
        "BrokerLifecycleEvent",
        "BrokerLifecycleEventType",
        "BrokerSubmissionResult",
        "CancelExecutableOrder",
        "SubmitExecutableOrder",
    }:
        from app.broker import models as models_mod

        return getattr(models_mod, name)
    if name in {"BrokerOrderPort", "BrokerOrderCommandPort"}:
        from app.broker import ports as ports_mod

        return getattr(ports_mod, name)
    if name in {"PaperBroker", "PaperBrokerOrderPort", "PaperBrokerPolicy"}:
        from app.broker import paper_adapter as paper_mod

        return getattr(paper_mod, name)
    if name == "validate_before_submit":
        from app.broker.reference import validate_before_submit

        return validate_before_submit
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
