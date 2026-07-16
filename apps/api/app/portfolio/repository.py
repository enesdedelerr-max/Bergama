"""Portfolio repository protocol and atomic in-memory implementation."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import Sequence
from enum import StrEnum
from typing import Protocol

from app.portfolio.errors import (
    PortfolioAlreadyExistsError,
    PortfolioIdempotencyConflictError,
    PortfolioMissingError,
    PortfolioRepositoryError,
    PortfolioVersionConflictError,
)
from app.portfolio.identity import PortfolioId
from app.portfolio.models import (
    LedgerEntry,
    PortfolioMutationOutcome,
    PortfolioMutationResult,
    PortfolioSnapshot,
)


class RepositoryFailureStage(StrEnum):
    BEFORE_SNAPSHOT_UPDATE = "before_snapshot_update"
    BEFORE_LEDGER_APPEND = "before_ledger_append"
    BEFORE_IDEMPOTENCY_COMMIT = "before_idempotency_commit"


class PortfolioRepository(Protocol):
    async def create_portfolio(self, snapshot: PortfolioSnapshot) -> None: ...

    async def load_snapshot(self, portfolio_id: PortfolioId) -> PortfolioSnapshot: ...

    async def reserve_idempotency_key(
        self,
        portfolio_id: PortfolioId,
        idempotency_key: str,
    ) -> bool: ...

    async def release_idempotency_key(
        self,
        portfolio_id: PortfolioId,
        idempotency_key: str,
    ) -> None: ...

    async def compare_and_commit(
        self,
        *,
        portfolio_id: PortfolioId,
        expected_version: int,
        mutation: PortfolioMutationResult,
        idempotency_key: str,
    ) -> PortfolioMutationResult: ...

    async def get_snapshot(self, portfolio_id: PortfolioId) -> PortfolioSnapshot: ...

    async def get_ledger(self, portfolio_id: PortfolioId) -> tuple[LedgerEntry, ...]: ...

    async def is_idempotency_committed(
        self,
        portfolio_id: PortfolioId,
        idempotency_key: str,
    ) -> bool: ...

    async def aclose(self) -> None: ...


class InMemoryPortfolioRepository:
    """Process-local repository with atomic compare-and-commit semantics."""

    def __init__(self) -> None:
        self._snapshots: dict[PortfolioId, PortfolioSnapshot] = {}
        self._ledger: dict[PortfolioId, list[LedgerEntry]] = defaultdict(list)
        self._committed_idempotency: dict[PortfolioId, set[str]] = defaultdict(set)
        self._reserved_idempotency: dict[PortfolioId, set[str]] = defaultdict(set)
        self._locks: dict[PortfolioId, asyncio.Lock] = {}
        self._failure_stages: list[RepositoryFailureStage] = []
        self._closed = False

    def inject_failure_once(self, stage: RepositoryFailureStage) -> None:
        self._failure_stages.append(stage)

    async def create_portfolio(self, snapshot: PortfolioSnapshot) -> None:
        async with self._lock_for(snapshot.portfolio_id):
            self._ensure_open()
            if snapshot.portfolio_id in self._snapshots:
                raise PortfolioAlreadyExistsError(detail=snapshot.portfolio_id.value)
            self._snapshots[snapshot.portfolio_id] = snapshot

    async def load_snapshot(self, portfolio_id: PortfolioId) -> PortfolioSnapshot:
        async with self._lock_for(portfolio_id):
            self._ensure_open()
            return self._snapshot_or_raise(portfolio_id)

    async def reserve_idempotency_key(
        self,
        portfolio_id: PortfolioId,
        idempotency_key: str,
    ) -> bool:
        async with self._lock_for(portfolio_id):
            self._ensure_open()
            if idempotency_key in self._committed_idempotency[portfolio_id]:
                return False
            if idempotency_key in self._reserved_idempotency[portfolio_id]:
                raise PortfolioIdempotencyConflictError(detail=idempotency_key)
            self._reserved_idempotency[portfolio_id].add(idempotency_key)
            return True

    async def release_idempotency_key(
        self,
        portfolio_id: PortfolioId,
        idempotency_key: str,
    ) -> None:
        async with self._lock_for(portfolio_id):
            self._reserved_idempotency[portfolio_id].discard(idempotency_key)

    async def compare_and_commit(
        self,
        *,
        portfolio_id: PortfolioId,
        expected_version: int,
        mutation: PortfolioMutationResult,
        idempotency_key: str,
    ) -> PortfolioMutationResult:
        async with self._lock_for(portfolio_id):
            self._ensure_open()
            current = self._snapshot_or_raise(portfolio_id)
            if idempotency_key in self._committed_idempotency[portfolio_id]:
                return mutation.model_copy(
                    update={
                        "outcome": PortfolioMutationOutcome.DUPLICATE,
                        "duplicate": True,
                        "ledger_entries": (),
                        "duplicate_of_version": current.portfolio_version,
                    }
                )
            if idempotency_key not in self._reserved_idempotency[portfolio_id]:
                raise PortfolioIdempotencyConflictError(detail=idempotency_key)
            if current.portfolio_version != expected_version:
                raise PortfolioVersionConflictError(detail=str(expected_version))

            self._fail_if_requested(RepositoryFailureStage.BEFORE_SNAPSHOT_UPDATE)
            next_snapshot = mutation.next_snapshot
            next_ledger = [*self._ledger[portfolio_id]]
            self._fail_if_requested(RepositoryFailureStage.BEFORE_LEDGER_APPEND)
            next_ledger.extend(mutation.ledger_entries)
            next_committed = {*self._committed_idempotency[portfolio_id]}
            self._fail_if_requested(RepositoryFailureStage.BEFORE_IDEMPOTENCY_COMMIT)
            next_committed.add(idempotency_key)

            self._snapshots[portfolio_id] = next_snapshot
            self._ledger[portfolio_id] = next_ledger
            self._committed_idempotency[portfolio_id] = next_committed
            self._reserved_idempotency[portfolio_id].discard(idempotency_key)
            return mutation

    async def get_snapshot(self, portfolio_id: PortfolioId) -> PortfolioSnapshot:
        return await self.load_snapshot(portfolio_id)

    async def get_ledger(self, portfolio_id: PortfolioId) -> tuple[LedgerEntry, ...]:
        async with self._lock_for(portfolio_id):
            self._ensure_open()
            self._snapshot_or_raise(portfolio_id)
            return tuple(self._ledger[portfolio_id])

    async def is_idempotency_committed(
        self,
        portfolio_id: PortfolioId,
        idempotency_key: str,
    ) -> bool:
        async with self._lock_for(portfolio_id):
            self._ensure_open()
            return idempotency_key in self._committed_idempotency[portfolio_id]

    async def aclose(self) -> None:
        self._closed = True

    def committed_keys(self, portfolio_id: PortfolioId) -> frozenset[str]:
        return frozenset(self._committed_idempotency[portfolio_id])

    def reserved_keys(self, portfolio_id: PortfolioId) -> frozenset[str]:
        return frozenset(self._reserved_idempotency[portfolio_id])

    def _lock_for(self, portfolio_id: PortfolioId) -> asyncio.Lock:
        lock = self._locks.get(portfolio_id)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[portfolio_id] = lock
        return lock

    def _snapshot_or_raise(self, portfolio_id: PortfolioId) -> PortfolioSnapshot:
        snapshot = self._snapshots.get(portfolio_id)
        if snapshot is None:
            raise PortfolioMissingError(detail=portfolio_id.value)
        return snapshot

    def _fail_if_requested(self, stage: RepositoryFailureStage) -> None:
        if stage in self._failure_stages:
            self._failure_stages.remove(stage)
            raise PortfolioRepositoryError(detail=stage.value)

    def _ensure_open(self) -> None:
        if self._closed:
            raise PortfolioRepositoryError(detail="closed")


def assert_same_ledger(left: Sequence[LedgerEntry], right: Sequence[LedgerEntry]) -> bool:
    return tuple(left) == tuple(right)
