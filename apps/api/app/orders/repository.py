"""Order repository protocol and atomic in-memory implementation (#404)."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from enum import StrEnum
from typing import Protocol

from app.orders.errors import (
    OrderAlreadyExistsError,
    OrderClosedError,
    OrderIdempotencyConflictError,
    OrderMissingError,
    OrderRepositoryError,
    OrderVersionConflictError,
)
from app.orders.events import DomainEvent, FillEvent
from app.orders.identity import OrderId
from app.orders.models import OrderMutationOutcome, OrderSnapshot
from app.orders.result import OrderMutationResult


class RepositoryFailureStage(StrEnum):
    BEFORE_SNAPSHOT_UPDATE = "before_snapshot_update"
    BEFORE_HISTORY_APPEND = "before_history_append"
    BEFORE_FILL_APPEND = "before_fill_append"
    BEFORE_IDEMPOTENCY_COMMIT = "before_idempotency_commit"


class OrderRepository(Protocol):
    async def create_order(self, snapshot: OrderSnapshot) -> None: ...

    async def load_snapshot(self, order_id: OrderId) -> OrderSnapshot | None: ...

    async def get_snapshot(self, order_id: OrderId) -> OrderSnapshot: ...

    async def reserve_idempotency_key(self, order_id: OrderId, idempotency_key: str) -> bool: ...

    async def release_idempotency_key(self, order_id: OrderId, idempotency_key: str) -> None: ...

    async def is_idempotency_committed(self, order_id: OrderId, idempotency_key: str) -> bool: ...

    async def compare_and_commit(
        self,
        *,
        order_id: OrderId,
        expected_version: int,
        mutation: OrderMutationResult,
        idempotency_key: str,
    ) -> OrderMutationResult: ...

    async def get_domain_events(self, order_id: OrderId) -> tuple[DomainEvent, ...]: ...

    async def get_fill_events(self, order_id: OrderId) -> tuple[FillEvent, ...]: ...

    async def aclose(self) -> None: ...


class InMemoryOrderRepository:
    """Process-local repository with atomic compare-and-commit semantics."""

    def __init__(self, *, max_history: int = 2_000) -> None:
        self._snapshots: dict[str, OrderSnapshot] = {}
        self._domain_events: dict[str, list[DomainEvent]] = defaultdict(list)
        self._fill_events: dict[str, list[FillEvent]] = defaultdict(list)
        self._committed_idempotency: dict[str, set[str]] = defaultdict(set)
        self._reserved_idempotency: dict[str, set[str]] = defaultdict(set)
        self._locks: dict[str, asyncio.Lock] = {}
        self._failure_stages: list[RepositoryFailureStage] = []
        self._max_history = max_history
        self._closed = False

    def inject_failure_once(self, stage: RepositoryFailureStage) -> None:
        self._failure_stages.append(stage)

    async def create_order(self, snapshot: OrderSnapshot) -> None:
        key = snapshot.order_id.value
        async with self._lock_for(key):
            self._ensure_open()
            if key in self._snapshots:
                raise OrderAlreadyExistsError(detail=key)
            self._snapshots[key] = snapshot

    async def load_snapshot(self, order_id: OrderId) -> OrderSnapshot | None:
        async with self._lock_for(order_id.value):
            self._ensure_open()
            return self._snapshots.get(order_id.value)

    async def get_snapshot(self, order_id: OrderId) -> OrderSnapshot:
        snapshot = await self.load_snapshot(order_id)
        if snapshot is None:
            raise OrderMissingError(detail=order_id.value)
        return snapshot

    async def reserve_idempotency_key(self, order_id: OrderId, idempotency_key: str) -> bool:
        key = order_id.value
        async with self._lock_for(key):
            self._ensure_open()
            if idempotency_key in self._committed_idempotency[key]:
                return False
            if idempotency_key in self._reserved_idempotency[key]:
                raise OrderIdempotencyConflictError(detail=idempotency_key)
            self._reserved_idempotency[key].add(idempotency_key)
            return True

    async def release_idempotency_key(self, order_id: OrderId, idempotency_key: str) -> None:
        key = order_id.value
        async with self._lock_for(key):
            self._reserved_idempotency[key].discard(idempotency_key)

    async def is_idempotency_committed(self, order_id: OrderId, idempotency_key: str) -> bool:
        key = order_id.value
        async with self._lock_for(key):
            return idempotency_key in self._committed_idempotency[key]

    async def compare_and_commit(
        self,
        *,
        order_id: OrderId,
        expected_version: int,
        mutation: OrderMutationResult,
        idempotency_key: str,
    ) -> OrderMutationResult:
        key = order_id.value
        async with self._lock_for(key):
            self._ensure_open()
            if idempotency_key in self._committed_idempotency[key]:
                snapshot = self._snapshots.get(key)
                if snapshot is None:
                    raise OrderMissingError(detail=key)
                return OrderMutationResult(
                    outcome=OrderMutationOutcome.DUPLICATE,
                    duplicate=True,
                    next_snapshot=snapshot,
                    idempotency_key=idempotency_key,
                )
            if idempotency_key not in self._reserved_idempotency[key]:
                raise OrderIdempotencyConflictError(detail=idempotency_key)

            current = self._snapshots.get(key)
            if current is None:
                if expected_version != 0:
                    raise OrderVersionConflictError(detail=str(expected_version))
            elif current.order_version != expected_version:
                raise OrderVersionConflictError(detail=str(expected_version))

            self._maybe_fail(RepositoryFailureStage.BEFORE_SNAPSHOT_UPDATE)
            next_snapshots = dict(self._snapshots)
            next_snapshots[key] = mutation.next_snapshot

            self._maybe_fail(RepositoryFailureStage.BEFORE_HISTORY_APPEND)
            next_domain = list(self._domain_events[key])
            next_domain.extend(mutation.domain_events)
            if len(next_domain) > self._max_history:
                next_domain = next_domain[-self._max_history :]

            self._maybe_fail(RepositoryFailureStage.BEFORE_FILL_APPEND)
            next_fills = list(self._fill_events[key])
            next_fills.extend(mutation.fill_events)
            if len(next_fills) > self._max_history:
                next_fills = next_fills[-self._max_history :]

            self._maybe_fail(RepositoryFailureStage.BEFORE_IDEMPOTENCY_COMMIT)
            next_committed = set(self._committed_idempotency[key])
            next_committed.add(idempotency_key)

            self._snapshots = next_snapshots
            self._domain_events[key] = next_domain
            self._fill_events[key] = next_fills
            self._committed_idempotency[key] = next_committed
            self._reserved_idempotency[key].discard(idempotency_key)
            return mutation

    async def get_domain_events(self, order_id: OrderId) -> tuple[DomainEvent, ...]:
        async with self._lock_for(order_id.value):
            return tuple(self._domain_events[order_id.value])

    async def get_fill_events(self, order_id: OrderId) -> tuple[FillEvent, ...]:
        async with self._lock_for(order_id.value):
            return tuple(self._fill_events[order_id.value])

    async def aclose(self) -> None:
        self._closed = True

    def _maybe_fail(self, stage: RepositoryFailureStage) -> None:
        if self._failure_stages and self._failure_stages[0] is stage:
            self._failure_stages.pop(0)
            raise OrderRepositoryError(detail=stage.value)

    def _lock_for(self, key: str) -> asyncio.Lock:
        lock = self._locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[key] = lock
        return lock

    def _ensure_open(self) -> None:
        if self._closed:
            raise OrderClosedError()
