"""Typed Portfolio Aggregate failures (#402)."""

from __future__ import annotations


class PortfolioError(Exception):
    code = "portfolio.error"

    def __init__(self, message: str | None = None, *, detail: str | None = None) -> None:
        super().__init__(message or self.code)
        self.detail = detail


class PortfolioInvalidInputError(PortfolioError):
    code = "portfolio.invalid_input"


class PortfolioDecimalError(PortfolioInvalidInputError):
    code = "portfolio.invalid_decimal"


class PortfolioCurrencyMismatchError(PortfolioInvalidInputError):
    code = "portfolio.currency_mismatch"


class PortfolioDuplicateEventError(PortfolioError):
    code = "portfolio.duplicate_event"


class PortfolioIdempotencyConflictError(PortfolioError):
    code = "portfolio.idempotency_conflict"


class PortfolioVersionConflictError(PortfolioError):
    code = "portfolio.version_conflict"


class PortfolioInsufficientCashError(PortfolioError):
    code = "portfolio.insufficient_cash"


class PortfolioShortingDisabledError(PortfolioError):
    code = "portfolio.shorting_disabled"


class PortfolioStaleEventError(PortfolioError):
    code = "portfolio.stale_event"


class PortfolioRepositoryError(PortfolioError):
    code = "portfolio.repository_error"


class PortfolioAccountingInvariantError(PortfolioError):
    code = "portfolio.accounting_invariant"


class PortfolioClosedError(PortfolioError):
    code = "portfolio.closed"


class PortfolioMissingError(PortfolioError):
    code = "portfolio.missing"


class PortfolioAlreadyExistsError(PortfolioError):
    code = "portfolio.already_exists"


class PortfolioCancellationError(PortfolioError):
    code = "portfolio.cancelled"


class PortfolioLockTimeoutError(PortfolioError):
    code = "portfolio.lock_timeout"
