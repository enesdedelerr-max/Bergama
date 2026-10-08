"""Public Intelligence Run product HTTP errors (WS3).

Internal persistence/materialization codes remain in ``errors.py`` and must not
leak as public product codes.
"""

from __future__ import annotations

from typing import Any


class IntelligenceRunProductError(Exception):
    """Bounded public productization error with frozen HTTP mapping."""

    def __init__(
        self,
        *,
        code: str,
        message: str,
        status_code: int,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


def invalid_identifier(*, detail: str) -> IntelligenceRunProductError:
    return IntelligenceRunProductError(
        code="intelligence.runs.invalid_identifier",
        message="The provided intelligence run identifier is invalid.",
        status_code=400,
        details={"reason": detail},
    )


def run_not_found(*, detail: str | None = None) -> IntelligenceRunProductError:
    return IntelligenceRunProductError(
        code="intelligence.runs.run_not_found",
        message="No matching intelligence run was found.",
        status_code=404,
        details={"reason": detail} if detail else None,
    )


def stage_not_present(*, stage: str) -> IntelligenceRunProductError:
    return IntelligenceRunProductError(
        code="intelligence.runs.stage_not_present",
        message="The requested intelligence run stage is not present.",
        status_code=404,
        details={"stage": stage},
    )


def insufficient_scope() -> IntelligenceRunProductError:
    return IntelligenceRunProductError(
        code="authz.insufficient_scope",
        message="Authenticated principal lacks the required product read scope.",
        status_code=403,
        details={"required_scope": "intelligence:runs:read"},
    )


def unsupported_snapshot_contract(*, version: str) -> IntelligenceRunProductError:
    return IntelligenceRunProductError(
        code="intelligence.runs.unsupported_snapshot_contract",
        message="Stored snapshot contract is not supported by the current reader.",
        status_code=409,
        details={"snapshot_contract_version": version},
    )


def corrupt_persisted_snapshot(*, detail: str | None = None) -> IntelligenceRunProductError:
    return IntelligenceRunProductError(
        code="intelligence.runs.corrupt_persisted_snapshot",
        message="Persisted intelligence run snapshot is corrupt or incomplete.",
        status_code=500,
        details={"reason": detail} if detail else None,
    )


def storage_unavailable() -> IntelligenceRunProductError:
    return IntelligenceRunProductError(
        code="intelligence.runs.storage_unavailable",
        message="Intelligence run durable storage is unavailable.",
        status_code=503,
    )
