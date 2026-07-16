"""Canonical Portfolio Aggregate hashing helpers."""

from __future__ import annotations

import hashlib
from typing import Any

from app.portfolio.decimal import canonical_decimal
from app.portfolio.identity import PortfolioId
from app.portfolio.models import PortfolioSnapshot, PositionState
from app.strategy.keys import strategy_sha256


def snapshot_hash_payload(snapshot: PortfolioSnapshot) -> dict[str, Any]:
    """Approved business-state payload for deterministic snapshot hashes."""
    return {
        "base_currency": snapshot.base_currency,
        "cash": {
            "currency": snapshot.cash.currency,
            "cash_balance": canonical_decimal(snapshot.cash.cash_balance),
            "realized_pnl": canonical_decimal(snapshot.cash.realized_pnl),
            "fees_total": canonical_decimal(snapshot.cash.fees_total),
        },
        "positions": [_position_payload(position) for position in snapshot.positions],
        "realized_pnl": canonical_decimal(snapshot.realized_pnl),
        "unrealized_pnl": canonical_decimal(snapshot.unrealized_pnl),
        "fees_total": canonical_decimal(snapshot.fees_total),
        "market_value": canonical_decimal(snapshot.market_value),
        "gross_exposure": canonical_decimal(snapshot.gross_exposure),
        "net_exposure": canonical_decimal(snapshot.net_exposure),
        "portfolio_version": snapshot.portfolio_version,
        "policy_fingerprint": snapshot.configuration_fingerprint,
    }


def compute_snapshot_hash(snapshot: PortfolioSnapshot) -> str:
    return strategy_sha256(snapshot_hash_payload(snapshot))


def build_ledger_entry_id(
    *,
    portfolio_id: PortfolioId,
    portfolio_version: int,
    event_id: str,
    entry_index: int,
) -> str:
    payload = (
        "portfolio-ledger-entry:v1\n"
        f"{portfolio_id.value}\n"
        f"{portfolio_version}\n"
        f"{event_id}\n"
        f"{entry_index}"
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _position_payload(position: PositionState) -> dict[str, Any]:
    return {
        "instrument_id": position.instrument.instrument_key,
        "currency": position.currency,
        "quantity": canonical_decimal(position.quantity),
        "average_cost": canonical_decimal(position.average_cost),
        "last_mark_price": (
            canonical_decimal(position.last_mark_price)
            if position.last_mark_price is not None
            else None
        ),
        "last_mark_at": position.last_mark_at,
        "market_value": canonical_decimal(position.market_value),
        "unrealized_pnl": canonical_decimal(position.unrealized_pnl),
    }
