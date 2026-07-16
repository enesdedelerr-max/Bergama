"""PortfolioService orchestration boundary."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Protocol

from app.core.clock import Clock
from app.portfolio.aggregate import PortfolioAggregate
from app.portfolio.audit import InMemoryPortfolioAuditSink, PortfolioAuditRecord
from app.portfolio.decimal import ZERO
from app.portfolio.errors import (
    PortfolioAccountingInvariantError,
    PortfolioClosedError,
    PortfolioError,
    PortfolioLockTimeoutError,
    PortfolioRepositoryError,
    PortfolioVersionConflictError,
)
from app.portfolio.identity import AccountId, PortfolioId
from app.portfolio.metrics import PortfolioMetrics
from app.portfolio.models import (
    CashAdjustment,
    CashAdjustmentCommand,
    CashDelta,
    FillApplied,
    FillAppliedCommand,
    LedgerEntry,
    MarkPriceUpdate,
    MarkPriceUpdateCommand,
    PortfolioInput,
    PortfolioMutationOutcome,
    PortfolioMutationResult,
    PortfolioMutationType,
    PortfolioSnapshot,
    PositionDelta,
)
from app.portfolio.policies import PortfolioPolicy
from app.portfolio.repository import InMemoryPortfolioRepository, PortfolioRepository
from app.strategy.keys import strategy_sha256


class PortfolioAuditSink(Protocol):
    def record(self, record: PortfolioAuditRecord) -> None: ...


class PortfolioService:
    """Orchestrates repository, idempotency, audit, and metrics only."""

    def __init__(
        self,
        *,
        repository: PortfolioRepository,
        clock: Clock,
        policy: PortfolioPolicy,
        audit_sink: PortfolioAuditSink | None = None,
        metrics: PortfolioMetrics | None = None,
        sequencer: _PortfolioSequencer | None = None,
        lock_timeout_seconds: float | None = None,
    ) -> None:
        self._repository = repository
        self._clock = clock
        self._policy = policy
        self._audit_sink = audit_sink or InMemoryPortfolioAuditSink()
        self._metrics = metrics or PortfolioMetrics()
        self._sequencer = sequencer or _PortfolioSequencer()
        self._lock_timeout_seconds = lock_timeout_seconds
        self._closed = False

    @property
    def metrics(self) -> PortfolioMetrics:
        return self._metrics

    @property
    def audit_sink(self) -> PortfolioAuditSink:
        return self._audit_sink

    async def create_portfolio(
        self,
        *,
        account_id: AccountId,
        portfolio_id: PortfolioId,
        snapshot_at: datetime,
        safe_metadata: dict[str, str] | None = None,
    ) -> PortfolioSnapshot:
        self._ensure_open()
        async with self._sequencer.locked(
            portfolio_id,
            timeout_seconds=self._lock_timeout_seconds,
        ):
            snapshot = PortfolioAggregate.initial_snapshot(
                account_id=account_id,
                portfolio_id=portfolio_id,
                policy=self._policy,
                snapshot_at=snapshot_at,
                safe_metadata=safe_metadata,
            )
            await self._repository.create_portfolio(snapshot)
            return snapshot

    async def apply_fill(self, command: FillAppliedCommand) -> PortfolioMutationResult:
        return await self._apply(command, PortfolioMutationType.FILL_APPLIED)

    async def apply_cash_adjustment(
        self,
        command: CashAdjustmentCommand,
    ) -> PortfolioMutationResult:
        return await self._apply(command, PortfolioMutationType.CASH_ADJUSTMENT)

    async def apply_mark_price(self, command: MarkPriceUpdateCommand) -> PortfolioMutationResult:
        return await self._apply(command, PortfolioMutationType.MARK_PRICE_UPDATE)

    async def get_snapshot(self, portfolio_id: PortfolioId) -> PortfolioSnapshot:
        self._ensure_open()
        return await self._repository.get_snapshot(portfolio_id)

    async def get_ledger(self, portfolio_id: PortfolioId) -> tuple[LedgerEntry, ...]:
        self._ensure_open()
        return await self._repository.get_ledger(portfolio_id)

    async def aclose(self) -> None:
        if self._closed:
            return
        self._closed = True
        await self._repository.aclose()

    async def _apply(
        self,
        command: FillAppliedCommand | CashAdjustmentCommand | MarkPriceUpdateCommand,
        mutation_type: PortfolioMutationType,
    ) -> PortfolioMutationResult:
        self._ensure_open()
        mutation = command.mutation
        async with self._sequencer.locked(
            mutation.portfolio_id,
            timeout_seconds=self._lock_timeout_seconds,
        ):
            self._metrics.mutations_evaluated += 1
            reserved = False
            try:
                reserved = await self._repository.reserve_idempotency_key(
                    mutation.portfolio_id,
                    mutation.idempotency_key,
                )
                if not reserved:
                    snapshot = await self._repository.get_snapshot(mutation.portfolio_id)
                    self._metrics.duplicates += 1
                    result = _duplicate_result(
                        snapshot,
                        idempotency_key=mutation.idempotency_key,
                        mutation_type=mutation_type,
                    )
                    self._audit(mutation, result)
                    return result

                snapshot = await self._repository.load_snapshot(mutation.portfolio_id)
                aggregate = PortfolioAggregate(snapshot, policy=self._policy)
                result = self._evaluate(aggregate, mutation)
                committed = await self._repository.compare_and_commit(
                    portfolio_id=mutation.portfolio_id,
                    expected_version=command.expected_version,
                    mutation=result,
                    idempotency_key=mutation.idempotency_key,
                )
                self._record_success_metrics(committed)
                self._audit(mutation, committed)
                self._metrics.observe_latency(0.0)
                return committed
            except BaseException as exc:
                if reserved:
                    await self._repository.release_idempotency_key(
                        mutation.portfolio_id,
                        mutation.idempotency_key,
                    )
                self._record_error_metrics(exc)
                raise

    def _evaluate(
        self,
        aggregate: PortfolioAggregate,
        mutation: FillApplied | CashAdjustment | MarkPriceUpdate,
    ) -> PortfolioMutationResult:
        if isinstance(mutation, FillApplied):
            return aggregate.apply_fill(mutation)
        if isinstance(mutation, CashAdjustment):
            return aggregate.apply_cash_adjustment(mutation)
        return aggregate.apply_mark_price(mutation)

    def _audit(self, mutation: PortfolioInput, result: PortfolioMutationResult) -> None:
        self._audit_sink.record(
            PortfolioAuditRecord(
                account_id=mutation.account_id,
                portfolio_id=mutation.portfolio_id,
                mutation_type=result.mutation_type,
                outcome=result.outcome,
                portfolio_version=result.next_snapshot.portfolio_version,
                idempotency_key_hash=strategy_sha256(mutation.idempotency_key),
                event_id=mutation.event_id,
                correlation_id=mutation.correlation_id,
                causation_id=mutation.causation_id,
                recorded_at=self._clock.now(),
            )
        )

    def _record_success_metrics(self, result: PortfolioMutationResult) -> None:
        if result.outcome is PortfolioMutationOutcome.DUPLICATE:
            self._metrics.duplicates += 1
            return
        if result.mutation_type is PortfolioMutationType.FILL_APPLIED:
            self._metrics.fills_applied += 1
        elif result.mutation_type is PortfolioMutationType.CASH_ADJUSTMENT:
            self._metrics.cash_adjustments += 1
        elif result.mutation_type is PortfolioMutationType.MARK_PRICE_UPDATE:
            self._metrics.mark_updates += 1
        if result.position_delta.opened:
            self._metrics.positions_opened += 1
        if result.position_delta.closed:
            self._metrics.positions_closed += 1
        if result.position_delta.reversed:
            self._metrics.reversals += 1

    def _record_error_metrics(self, exc: BaseException) -> None:
        if isinstance(exc, PortfolioVersionConflictError):
            self._metrics.version_conflicts += 1
        elif isinstance(exc, PortfolioRepositoryError):
            self._metrics.repository_failures += 1
        elif isinstance(exc, (PortfolioAccountingInvariantError, PortfolioError)):
            self._metrics.accounting_failures += 1
        code = getattr(exc, "code", exc.__class__.__name__)
        self._metrics.record_error(str(code))

    def _ensure_open(self) -> None:
        if self._closed:
            raise PortfolioClosedError()


class _LockEntry:
    def __init__(self) -> None:
        self.lock = asyncio.Lock()
        self.waiters = 0


class _PortfolioSequencer:
    def __init__(self) -> None:
        self._entries: dict[PortfolioId, _LockEntry] = {}

    @property
    def active_lock_count(self) -> int:
        return len(self._entries)

    @asynccontextmanager
    async def locked(
        self,
        portfolio_id: PortfolioId,
        *,
        timeout_seconds: float | None = None,
    ) -> AsyncIterator[None]:
        entry = self._entries.get(portfolio_id)
        if entry is None:
            entry = _LockEntry()
            self._entries[portfolio_id] = entry
        entry.waiters += 1
        try:
            if timeout_seconds is None:
                await entry.lock.acquire()
            else:
                await asyncio.wait_for(entry.lock.acquire(), timeout=timeout_seconds)
        except TimeoutError as exc:
            entry.waiters -= 1
            self._cleanup_if_idle(portfolio_id, entry)
            raise PortfolioLockTimeoutError(detail=portfolio_id.value) from exc
        except BaseException:
            entry.waiters -= 1
            self._cleanup_if_idle(portfolio_id, entry)
            raise
        try:
            yield
        finally:
            entry.lock.release()
            entry.waiters -= 1
            self._cleanup_if_idle(portfolio_id, entry)

    def _cleanup_if_idle(self, portfolio_id: PortfolioId, entry: _LockEntry) -> None:
        if (
            entry.waiters == 0
            and not entry.lock.locked()
            and self._entries.get(portfolio_id) is entry
        ):
            del self._entries[portfolio_id]


def build_portfolio_service(
    *,
    clock: Clock,
    policy: PortfolioPolicy | None = None,
    audit_max_records: int = 10_000,
    lock_timeout_seconds: float | None = None,
) -> PortfolioService:
    return PortfolioService(
        repository=InMemoryPortfolioRepository(),
        clock=clock,
        policy=policy or PortfolioPolicy(),
        audit_sink=InMemoryPortfolioAuditSink(max_records=audit_max_records),
        lock_timeout_seconds=lock_timeout_seconds,
    )


def _duplicate_result(
    snapshot: PortfolioSnapshot,
    *,
    idempotency_key: str,
    mutation_type: PortfolioMutationType,
) -> PortfolioMutationResult:
    return PortfolioMutationResult(
        outcome=PortfolioMutationOutcome.DUPLICATE,
        duplicate=True,
        mutation_type=mutation_type,
        next_snapshot=snapshot,
        ledger_entries=(),
        realized_pnl_delta=ZERO,
        cash_delta=CashDelta(currency=snapshot.base_currency, amount=ZERO),
        position_delta=PositionDelta(),
        idempotency_key=idempotency_key,
        duplicate_of_version=snapshot.portfolio_version,
    )
