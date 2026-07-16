"""OrderManagementService orchestration boundary (#404)."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Protocol

from app.core.clock import Clock
from app.orders.aggregate import OrderAggregate
from app.orders.audit import InMemoryOrderAuditSink, OrderAuditRecord
from app.orders.commands import ApplyBrokerEvent, RequestCancel, SubmitOrder
from app.orders.errors import (
    OrderBrokerPortError,
    OrderClosedError,
    OrderError,
    OrderFillPortError,
    OrderLockTimeoutError,
    OrderVersionConflictError,
)
from app.orders.events import BrokerCommandType, BrokerOrderCommand
from app.orders.hashing import (
    broker_idempotency_key,
    build_order_id,
    cancel_idempotency_key,
    fill_idempotency_key,
    submit_idempotency_key,
)
from app.orders.identity import OrderId
from app.orders.metrics import OrderMetrics
from app.orders.models import (
    OrderMutationOutcome,
    OrderSnapshot,
    absolute_quantity,
    side_from_intent,
)
from app.orders.policies import OrderPolicy
from app.orders.ports import BrokerOrderPort, FillEventPort
from app.orders.repository import InMemoryOrderRepository, OrderRepository
from app.orders.result import OrderMutationResult


class OrderAuditSink(Protocol):
    def record(self, record: OrderAuditRecord) -> None: ...


class OrderManagementService:
    """Orchestrates locks, idempotency, CAS, and typed ports only."""

    def __init__(
        self,
        *,
        repository: OrderRepository,
        clock: Clock,
        policy: OrderPolicy | None = None,
        broker_port: BrokerOrderPort | None = None,
        fill_port: FillEventPort | None = None,
        audit_sink: OrderAuditSink | None = None,
        metrics: OrderMetrics | None = None,
        lock_timeout_seconds: float | None = None,
    ) -> None:
        self._repository = repository
        self._clock = clock
        self._policy = policy or OrderPolicy()
        self._broker_port = broker_port
        self._fill_port = fill_port
        self._audit_sink = audit_sink or InMemoryOrderAuditSink()
        self._metrics = metrics or OrderMetrics()
        self._sequencer = _OrderSequencer()
        self._lock_timeout_seconds = lock_timeout_seconds
        self._closed = False

    @property
    def metrics(self) -> OrderMetrics:
        return self._metrics

    @property
    def audit_sink(self) -> OrderAuditSink:
        return self._audit_sink

    async def submit(self, command: SubmitOrder) -> OrderMutationResult:
        self._ensure_open()
        self._metrics.commands_evaluated += 1
        qty = absolute_quantity(command.intent.signed_quantity_delta)
        side = side_from_intent(command.intent.direction, command.intent.signed_quantity_delta)
        order_id = OrderId(
            value=build_order_id(
                intent=command.intent,
                assessment=command.assessment,
                client_order_id=command.client_order_id,
                order_type=command.order_type,
                time_in_force=command.time_in_force,
                side=side,
                quantity=qty,
                limit_price=command.limit_price,
            )
        )
        idem_key = submit_idempotency_key(
            command.client_order_id.value,
            command.idempotency_key,
        )
        return await self._mutate(
            order_id=order_id,
            expected_version=0,
            idempotency_key=idem_key,
            kind="command",
            evaluate=lambda snap: OrderAggregate(snap, policy=self._policy).submit(
                command,
                created_at=self._clock.now(),
            ),
        )

    async def request_cancel(self, command: RequestCancel) -> OrderMutationResult:
        self._ensure_open()
        self._metrics.commands_evaluated += 1
        idem_key = cancel_idempotency_key(
            order_id=command.order_id.value,
            cancel_request_id=command.cancel_request_id,
        )
        return await self._mutate(
            order_id=command.order_id,
            expected_version=command.expected_version,
            idempotency_key=idem_key,
            kind="command",
            evaluate=lambda snap: OrderAggregate(snap, policy=self._policy).request_cancel(
                command,
                updated_at=self._clock.now(),
            ),
        )

    async def apply_broker_event(self, command: ApplyBrokerEvent) -> OrderMutationResult:
        self._ensure_open()
        self._metrics.commands_evaluated += 1
        if command.fill_event is not None:
            assert command.fill_event.fill_identity is not None
            idem_key = fill_idempotency_key(command.fill_event.fill_identity)
            kind = "fill"
        else:
            assert command.broker_event is not None
            assert command.broker_event.event_identity is not None
            idem_key = broker_idempotency_key(command.broker_event.event_identity)
            kind = "broker"
        return await self._mutate(
            order_id=command.order_id,
            expected_version=command.expected_version,
            idempotency_key=idem_key,
            kind=kind,
            evaluate=lambda snap: OrderAggregate(snap, policy=self._policy).apply_broker_event(
                command,
                updated_at=self._clock.now(),
            ),
        )

    async def get_snapshot(self, order_id: OrderId) -> OrderSnapshot:
        self._ensure_open()
        return await self._repository.get_snapshot(order_id)

    async def aclose(self) -> None:
        if self._closed:
            return
        self._closed = True
        await self._repository.aclose()

    async def _mutate(
        self,
        *,
        order_id: OrderId,
        expected_version: int,
        idempotency_key: str,
        kind: str,
        evaluate: Callable[[OrderSnapshot | None], OrderMutationResult],
    ) -> OrderMutationResult:
        async with self._sequencer.locked(
            order_id,
            timeout_seconds=self._lock_timeout_seconds,
        ):
            reserved = False
            try:
                reserved = await self._repository.reserve_idempotency_key(
                    order_id,
                    idempotency_key,
                )
                if not reserved:
                    existing = await self._repository.get_snapshot(order_id)
                    self._metrics.record_outcome(OrderMutationOutcome.DUPLICATE, kind=kind)
                    return OrderMutationResult(
                        outcome=OrderMutationOutcome.DUPLICATE,
                        duplicate=True,
                        next_snapshot=existing,
                        idempotency_key=idempotency_key,
                    )

                loaded = await self._repository.load_snapshot(order_id)
                result = evaluate(loaded)
                committed = await self._repository.compare_and_commit(
                    order_id=order_id,
                    expected_version=expected_version,
                    mutation=result,
                    idempotency_key=idempotency_key,
                )
                if not committed.duplicate:
                    await self._dispatch_ports(committed)
                    self._record_success(committed, kind=kind)
                else:
                    self._metrics.record_outcome(OrderMutationOutcome.DUPLICATE, kind=kind)
                for record in committed.audit_records:
                    self._audit_sink.record(record)
                return committed
            except BaseException as exc:
                if reserved:
                    await self._repository.release_idempotency_key(order_id, idempotency_key)
                self._record_error(exc)
                raise

    async def _dispatch_ports(self, result: OrderMutationResult) -> None:
        if self._broker_port is not None:
            for command in result.broker_commands:
                try:
                    await self._invoke_broker(command)
                except OrderError:
                    raise
                except Exception as exc:
                    self._metrics.broker_port_failures += 1
                    raise OrderBrokerPortError(detail=type(exc).__name__) from exc
        if self._fill_port is not None:
            for fill in result.fill_events:
                try:
                    await self._fill_port.publish_fill(fill)
                except OrderError:
                    raise
                except Exception as exc:
                    raise OrderFillPortError(detail=type(exc).__name__) from exc

    async def _invoke_broker(self, command: BrokerOrderCommand) -> None:
        assert self._broker_port is not None
        if command.command_type is BrokerCommandType.SUBMIT:
            await self._broker_port.submit(command)
        else:
            await self._broker_port.cancel(command)

    def _record_success(self, result: OrderMutationResult, *, kind: str) -> None:
        self._metrics.record_outcome(result.outcome, kind=kind)
        self._metrics.record_status(result.next_snapshot.status)
        for event in result.domain_events:
            self._metrics.record_domain_event(event.event_type)
        self._metrics.observe_latency(0.0)

    def _record_error(self, exc: BaseException) -> None:
        if isinstance(exc, OrderError):
            self._metrics.record_error(exc.code)
            if isinstance(exc, OrderVersionConflictError):
                self._metrics.version_conflicts += 1
        else:
            self._metrics.record_error(type(exc).__name__)

    def _ensure_open(self) -> None:
        if self._closed:
            raise OrderClosedError()


class _OrderSequencer:
    def __init__(self) -> None:
        self._locks: dict[str, asyncio.Lock] = {}

    @asynccontextmanager
    async def locked(
        self,
        order_id: OrderId,
        *,
        timeout_seconds: float | None,
    ) -> AsyncIterator[None]:
        key = order_id.value
        lock = self._locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[key] = lock
        try:
            if timeout_seconds is None:
                await lock.acquire()
            else:
                try:
                    await asyncio.wait_for(lock.acquire(), timeout=timeout_seconds)
                except TimeoutError as exc:
                    raise OrderLockTimeoutError(detail=key) from exc
            try:
                yield
            finally:
                lock.release()
        finally:
            if key in self._locks and not self._locks[key].locked():
                # idle cleanup when no waiters
                current = self._locks.get(key)
                if current is lock and not current.locked():
                    self._locks.pop(key, None)


def build_order_management_service(
    *,
    clock: Clock,
    repository: OrderRepository | None = None,
    policy: OrderPolicy | None = None,
    broker_port: BrokerOrderPort | None = None,
    fill_port: FillEventPort | None = None,
    audit_max_records: int = 10_000,
    lock_timeout_seconds: float | None = 5.0,
) -> OrderManagementService:
    return OrderManagementService(
        repository=repository or InMemoryOrderRepository(),
        clock=clock,
        policy=policy or OrderPolicy(),
        broker_port=broker_port,
        fill_port=fill_port,
        audit_sink=InMemoryOrderAuditSink(max_records=audit_max_records),
        lock_timeout_seconds=lock_timeout_seconds,
    )
