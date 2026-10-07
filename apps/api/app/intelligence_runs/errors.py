"""Internal Intelligence Run persistence errors (WS1).

These are repository/storage failures only. Public HTTP mapping belongs to WS3.
"""

from __future__ import annotations


class IntelligenceRunPersistenceError(Exception):
    """Base internal persistence failure."""

    code = "intelligence_runs.persistence_error"

    def __init__(self, message: str | None = None, *, detail: str | None = None) -> None:
        super().__init__(message or self.code)
        self.detail = detail


class IntelligenceRunIdentityConflictError(IntelligenceRunPersistenceError):
    """Logical identity uniqueness / integrity conflict."""

    code = "intelligence_runs.identity_conflict"


class IntelligenceRunStorageUnavailableError(IntelligenceRunPersistenceError):
    """Database connectivity or storage unavailable."""

    code = "intelligence_runs.storage_unavailable"


class IntelligenceRunInvalidPersistedRepresentationError(IntelligenceRunPersistenceError):
    """Caller supplied an invalid persistence record or lookup key."""

    code = "intelligence_runs.invalid_persisted_representation"
