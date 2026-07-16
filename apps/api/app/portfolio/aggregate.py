"""Pure Portfolio Aggregate transitions."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from app.market_data.identity import InstrumentId
from app.portfolio.accounting import apply_fill_to_position, mark_position
from app.portfolio.decimal import ZERO, quantize_money, quantize_pnl, quantize_quantity
from app.portfolio.errors import (
    PortfolioAccountingInvariantError,
    PortfolioCurrencyMismatchError,
    PortfolioMissingError,
)
from app.portfolio.hashing import build_ledger_entry_id, compute_snapshot_hash
from app.portfolio.identity import AccountId, PortfolioId
from app.portfolio.models import (
    CashAdjustment,
    CashDelta,
    CashState,
    FillApplied,
    LedgerEntry,
    MarkPriceUpdate,
    PortfolioMutationOutcome,
    PortfolioMutationResult,
    PortfolioMutationType,
    PortfolioProvenance,
    PortfolioSnapshot,
    PositionDelta,
    PositionState,
)
from app.portfolio.policies import PortfolioPolicy


class PortfolioAggregate:
    """Clock-free, repository-free aggregate for deterministic accounting."""

    def __init__(self, snapshot: PortfolioSnapshot, *, policy: PortfolioPolicy) -> None:
        self._snapshot = snapshot
        self._policy = policy

    @property
    def snapshot(self) -> PortfolioSnapshot:
        return self._snapshot

    @classmethod
    def initial_snapshot(
        cls,
        *,
        account_id: AccountId,
        portfolio_id: PortfolioId,
        policy: PortfolioPolicy,
        snapshot_at: datetime,
        safe_metadata: dict[str, str] | None = None,
    ) -> PortfolioSnapshot:
        snapshot = PortfolioSnapshot(
            account_id=account_id,
            portfolio_id=portfolio_id,
            base_currency=policy.base_currency,
            cash=CashState(currency=policy.base_currency),
            positions=(),
            portfolio_version=0,
            last_applied_event_key=None,
            configuration_fingerprint=policy.fingerprint(),
            snapshot_at=snapshot_at,
            safe_metadata=safe_metadata or {},
        )
        return snapshot.model_copy(update={"snapshot_hash": compute_snapshot_hash(snapshot)})

    def apply_fill(self, fill: FillApplied) -> PortfolioMutationResult:
        self._validate_input(
            fill.account_id,
            fill.portfolio_id,
            fill.currency,
        )
        position = self._position(fill.instrument.instrument_key)
        result = apply_fill_to_position(position=position, fill=fill, policy=self._policy)
        cash = self._snapshot.cash.model_copy(
            update={
                "cash_balance": quantize_money(
                    self._snapshot.cash.cash_balance + result.cash_delta
                ),
                "realized_pnl": quantize_pnl(
                    self._snapshot.cash.realized_pnl + result.realized_pnl_delta
                ),
                "fees_total": quantize_money(self._snapshot.cash.fees_total + fill.fee),
            }
        )
        if self._policy.enforce_non_negative_cash and cash.cash_balance < ZERO:
            from app.portfolio.errors import PortfolioInsufficientCashError

            raise PortfolioInsufficientCashError(detail=self._snapshot.portfolio_id.value)
        positions = self._replace_position(fill.instrument.instrument_key, result.next_position)
        next_snapshot = self._next_snapshot(
            cash=cash,
            positions=positions,
            event_key=fill.idempotency_key,
            snapshot_at=fill.ingested_at,
        )
        position_delta = PositionDelta(
            instrument=fill.instrument,
            quantity_delta=result.quantity_delta,
            opened=result.opened,
            closed=result.closed,
            reversed=result.reversed,
        )
        cash_delta = CashDelta(currency=fill.currency, amount=result.cash_delta)
        ledger = self._ledger_entry(
            mutation_type=PortfolioMutationType.FILL_APPLIED,
            portfolio_id=self._snapshot.portfolio_id,
            source_event_id=fill.event_id,
            idempotency_key=fill.idempotency_key,
            instrument=fill.instrument,
            cash_delta=cash_delta,
            quantity_delta=result.quantity_delta,
            realized_pnl_delta=result.realized_pnl_delta,
            fee=fill.fee,
            occurred_at=fill.occurred_at,
            correlation_id=fill.correlation_id,
            causation_id=fill.causation_id,
            provenance=fill.provenance,
            safe_metadata=fill.safe_metadata,
            portfolio_version=next_snapshot.portfolio_version,
            entry_index=0,
        )
        return PortfolioMutationResult(
            outcome=PortfolioMutationOutcome.APPLIED,
            mutation_type=PortfolioMutationType.FILL_APPLIED,
            next_snapshot=next_snapshot,
            ledger_entries=(ledger,),
            realized_pnl_delta=result.realized_pnl_delta,
            cash_delta=cash_delta,
            position_delta=position_delta,
            idempotency_key=fill.idempotency_key,
        )

    def apply_cash_adjustment(self, adjustment: CashAdjustment) -> PortfolioMutationResult:
        self._validate_input(
            adjustment.account_id,
            adjustment.portfolio_id,
            adjustment.currency,
        )
        cash = self._snapshot.cash.model_copy(
            update={
                "cash_balance": quantize_money(self._snapshot.cash.cash_balance + adjustment.amount)
            }
        )
        next_snapshot = self._next_snapshot(
            cash=cash,
            positions=self._snapshot.positions,
            event_key=adjustment.idempotency_key,
            snapshot_at=adjustment.ingested_at,
        )
        cash_delta = CashDelta(currency=adjustment.currency, amount=adjustment.amount)
        ledger = self._ledger_entry(
            mutation_type=PortfolioMutationType.CASH_ADJUSTMENT,
            portfolio_id=self._snapshot.portfolio_id,
            source_event_id=adjustment.event_id,
            idempotency_key=adjustment.idempotency_key,
            instrument=None,
            cash_delta=cash_delta,
            quantity_delta=ZERO,
            realized_pnl_delta=ZERO,
            fee=ZERO,
            occurred_at=adjustment.occurred_at,
            correlation_id=adjustment.correlation_id,
            causation_id=adjustment.causation_id,
            safe_metadata={
                **adjustment.safe_metadata,
                "reason": adjustment.reason.value,
            },
            portfolio_version=next_snapshot.portfolio_version,
            entry_index=0,
        )
        return PortfolioMutationResult(
            outcome=PortfolioMutationOutcome.APPLIED,
            mutation_type=PortfolioMutationType.CASH_ADJUSTMENT,
            next_snapshot=next_snapshot,
            ledger_entries=(ledger,),
            realized_pnl_delta=ZERO,
            cash_delta=cash_delta,
            position_delta=PositionDelta(),
            idempotency_key=adjustment.idempotency_key,
        )

    def apply_mark_price(self, mark: MarkPriceUpdate) -> PortfolioMutationResult:
        self._validate_input(
            mark.account_id,
            mark.portfolio_id,
            mark.currency,
        )
        position = self._position(mark.instrument.instrument_key)
        if position is None:
            raise PortfolioMissingError(detail=f"position:{mark.instrument.instrument_key}")
        marked = mark_position(position, mark_price=mark.mark_price).model_copy(
            update={"last_mark_at": mark.mark_time}
        )
        positions = self._replace_position(mark.instrument.instrument_key, marked)
        next_snapshot = self._next_snapshot(
            cash=self._snapshot.cash,
            positions=positions,
            event_key=mark.idempotency_key,
            snapshot_at=mark.ingested_at,
        )
        cash_delta = CashDelta(currency=mark.currency, amount=ZERO)
        ledger = self._ledger_entry(
            mutation_type=PortfolioMutationType.MARK_PRICE_UPDATE,
            portfolio_id=self._snapshot.portfolio_id,
            source_event_id=mark.event_id,
            idempotency_key=mark.idempotency_key,
            instrument=mark.instrument,
            cash_delta=cash_delta,
            quantity_delta=ZERO,
            realized_pnl_delta=ZERO,
            fee=ZERO,
            occurred_at=mark.occurred_at,
            correlation_id=mark.correlation_id,
            causation_id=mark.causation_id,
            safe_metadata=mark.safe_metadata,
            portfolio_version=next_snapshot.portfolio_version,
            entry_index=0,
        )
        return PortfolioMutationResult(
            outcome=PortfolioMutationOutcome.APPLIED,
            mutation_type=PortfolioMutationType.MARK_PRICE_UPDATE,
            next_snapshot=next_snapshot,
            ledger_entries=(ledger,),
            realized_pnl_delta=ZERO,
            cash_delta=cash_delta,
            position_delta=PositionDelta(instrument=mark.instrument),
            idempotency_key=mark.idempotency_key,
        )

    def _validate_input(
        self,
        account_id: AccountId,
        portfolio_id: PortfolioId,
        currency: str,
    ) -> None:
        if account_id != self._snapshot.account_id or portfolio_id != self._snapshot.portfolio_id:
            raise PortfolioMissingError(detail=portfolio_id.value)
        if currency != self._snapshot.base_currency:
            raise PortfolioCurrencyMismatchError(detail=currency)

    def _position(self, instrument_key: str) -> PositionState | None:
        for position in self._snapshot.positions:
            if position.instrument.instrument_key == instrument_key:
                return position
        return None

    def _replace_position(
        self,
        instrument_key: str,
        next_position: PositionState | None,
    ) -> tuple[PositionState, ...]:
        positions = [
            p for p in self._snapshot.positions if p.instrument.instrument_key != instrument_key
        ]
        if next_position is not None and next_position.quantity != ZERO:
            positions.append(next_position)
        return tuple(sorted(positions, key=lambda p: p.instrument.instrument_key))

    def _next_snapshot(
        self,
        *,
        cash: CashState,
        positions: tuple[PositionState, ...],
        event_key: str,
        snapshot_at: datetime,
    ) -> PortfolioSnapshot:
        unrealized = quantize_pnl(sum((p.unrealized_pnl for p in positions), ZERO))
        market_value = quantize_money(sum((p.market_value for p in positions), ZERO))
        gross = quantize_money(sum((abs(p.market_value) for p in positions), ZERO))
        net = market_value
        snapshot = PortfolioSnapshot(
            account_id=self._snapshot.account_id,
            portfolio_id=self._snapshot.portfolio_id,
            base_currency=self._snapshot.base_currency,
            cash=cash,
            positions=positions,
            realized_pnl=cash.realized_pnl,
            unrealized_pnl=unrealized,
            fees_total=cash.fees_total,
            market_value=market_value,
            gross_exposure=gross,
            net_exposure=net,
            portfolio_version=self._snapshot.portfolio_version + 1,
            last_applied_event_key=event_key,
            configuration_fingerprint=self._snapshot.configuration_fingerprint,
            snapshot_at=snapshot_at,
            safe_metadata=self._snapshot.safe_metadata,
        )
        return snapshot.model_copy(update={"snapshot_hash": compute_snapshot_hash(snapshot)})

    def _ledger_entry(
        self,
        *,
        mutation_type: PortfolioMutationType,
        portfolio_id: PortfolioId,
        source_event_id: str,
        idempotency_key: str,
        instrument: InstrumentId | None,
        cash_delta: CashDelta,
        quantity_delta: Decimal,
        realized_pnl_delta: Decimal,
        fee: Decimal,
        occurred_at: datetime,
        correlation_id: str | None,
        causation_id: str | None,
        portfolio_version: int,
        entry_index: int,
        provenance: PortfolioProvenance | None = None,
        safe_metadata: dict[str, str] | None = None,
    ) -> LedgerEntry:
        entry = LedgerEntry(
            ledger_entry_id=build_ledger_entry_id(
                portfolio_id=portfolio_id,
                portfolio_version=portfolio_version,
                event_id=source_event_id,
                entry_index=entry_index,
            ),
            ledger_version=portfolio_version,
            portfolio_version=portfolio_version,
            mutation_type=mutation_type,
            source_event_id=source_event_id,
            idempotency_key=idempotency_key,
            instrument=instrument,
            cash_delta=cash_delta,
            quantity_delta=quantize_quantity(quantity_delta),
            realized_pnl_delta=quantize_pnl(realized_pnl_delta),
            fee=quantize_money(fee),
            occurred_at=occurred_at,
            correlation_id=correlation_id,
            causation_id=causation_id,
            provenance=provenance or PortfolioProvenance(),
            safe_metadata=safe_metadata or {},
        )
        return entry


def assert_snapshot_integrity(snapshot: PortfolioSnapshot) -> None:
    if snapshot.snapshot_hash != compute_snapshot_hash(snapshot):
        raise PortfolioAccountingInvariantError(detail="snapshot_hash_mismatch")
