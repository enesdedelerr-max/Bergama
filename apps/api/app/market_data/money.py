"""Decimal helpers for monetary and size fields."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any


def require_finite_decimal(value: Decimal | int | str, *, field_name: str) -> Decimal:
    """Parse and reject NaN / Infinity."""
    try:
        decimal_value = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        msg = f"{field_name} must be a finite Decimal"
        raise ValueError(msg) from exc
    if not decimal_value.is_finite():
        msg = f"{field_name} must be finite (no NaN or Infinity)"
        raise ValueError(msg)
    return decimal_value


def canonical_decimal_str(value: Decimal) -> str:
    """Deterministic non-scientific Decimal string for transport payloads."""
    if not value.is_finite():
        msg = "Decimal must be finite"
        raise ValueError(msg)
    normalized = value.normalize()
    text = format(normalized, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if text in {"", "-0"}:
        return "0"
    if text == "-":
        return "0"
    return text


def decimal_from_canonical_str(text: str) -> Decimal:
    """Parse a canonical Decimal string back to Decimal."""
    return require_finite_decimal(text, field_name="decimal")


def is_decimal_like(value: Any) -> bool:
    return isinstance(value, Decimal)
