"""Decimal helpers for monetary and size fields."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

_FINITE_DECIMAL_REQUIRED = "must be a finite Decimal"
_NON_FINITE_DECIMAL = "must be finite (no NaN or Infinity)"
_PYTHON_FLOAT_REJECTED = "must not be a Python float"
_PYTHON_BOOL_REJECTED = "must not be a Python bool"


def require_finite_decimal(value: Decimal | int | str, *, field_name: str) -> Decimal:
    """Parse a finite Decimal from Decimal, non-bool int, or str.

    Rejects Python ``float`` and ``bool`` before construction. Does not parse
    arbitrary objects via ``Decimal(str(value))``.
    """
    return _parse_finite_decimal(value, field_name=field_name)


def _parse_finite_decimal(value: object, *, field_name: str) -> Decimal:
    if type(value) is bool:
        msg = f"{field_name} {_PYTHON_BOOL_REJECTED}"
        raise ValueError(msg)
    if type(value) is float:
        msg = f"{field_name} {_PYTHON_FLOAT_REJECTED}"
        raise ValueError(msg)
    if isinstance(value, Decimal):
        decimal_value = value
    elif type(value) is int:
        decimal_value = Decimal(value)
    elif isinstance(value, str):
        try:
            decimal_value = Decimal(value)
        except (InvalidOperation, ValueError, TypeError) as exc:
            msg = f"{field_name} {_FINITE_DECIMAL_REQUIRED}"
            raise ValueError(msg) from exc
    else:
        msg = f"{field_name} {_FINITE_DECIMAL_REQUIRED}"
        raise ValueError(msg)
    if not decimal_value.is_finite():
        msg = f"{field_name} {_NON_FINITE_DECIMAL}"
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
