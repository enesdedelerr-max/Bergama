"""Unit tests for canonical financial Decimal helpers."""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.market_data.money import require_finite_decimal


def test_require_finite_decimal_accepts_decimal_str_and_int() -> None:
    assert require_finite_decimal(Decimal("0.1"), field_name="price") == Decimal("0.1")
    assert require_finite_decimal("0.1", field_name="price") == Decimal("0.1")
    assert require_finite_decimal(1, field_name="price") == Decimal("1")
    assert require_finite_decimal(0, field_name="volume") == Decimal("0")


def test_require_finite_decimal_rejects_python_float() -> None:
    with pytest.raises(ValueError, match="Python float"):
        require_finite_decimal(0.1, field_name="price")  # type: ignore[arg-type]


def test_require_finite_decimal_rejects_python_bool() -> None:
    with pytest.raises(ValueError, match="Python bool"):
        require_finite_decimal(True, field_name="price")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Python bool"):
        require_finite_decimal(False, field_name="volume")  # type: ignore[arg-type]


def test_require_finite_decimal_rejects_unsupported_object() -> None:
    with pytest.raises(ValueError, match="finite Decimal"):
        require_finite_decimal(object(), field_name="price")  # type: ignore[arg-type]


def test_require_finite_decimal_rejects_nan_and_infinity() -> None:
    with pytest.raises(ValueError, match="finite"):
        require_finite_decimal(Decimal("NaN"), field_name="price")
    with pytest.raises(ValueError, match="finite"):
        require_finite_decimal("NaN", field_name="price")
    with pytest.raises(ValueError, match="finite"):
        require_finite_decimal(Decimal("Infinity"), field_name="price")
    with pytest.raises(ValueError, match="finite"):
        require_finite_decimal("Infinity", field_name="price")
    with pytest.raises(ValueError, match="finite"):
        require_finite_decimal("-Infinity", field_name="price")
