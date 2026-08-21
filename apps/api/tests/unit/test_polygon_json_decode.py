"""Unit tests for Polygon Decimal-preserving JSON decode."""

from __future__ import annotations

import json
from decimal import Decimal

import pytest
from app.infrastructure.polygon.json_decode import loads_polygon_json

HIGH_PRECISION = "1.234567890123456789012345"


def test_loads_polygon_json_preserves_zero_point_one() -> None:
    payload = loads_polygon_json('{"c": 0.1}')
    assert payload["c"] == Decimal("0.1")
    assert payload["c"] != Decimal(0.1)
    assert type(payload["c"]) is Decimal


def test_loads_polygon_json_preserves_high_precision_token() -> None:
    payload = loads_polygon_json(f'{{"c": {HIGH_PRECISION}}}')
    assert payload["c"] == Decimal(HIGH_PRECISION)
    assert type(payload["c"]) is Decimal


def test_loads_polygon_json_rejects_non_finite_constants() -> None:
    for raw in ('{"c": NaN}', '{"c": Infinity}', '{"c": -Infinity}'):
        with pytest.raises(ValueError, match="non-finite JSON constant"):
            loads_polygon_json(raw)


def test_loads_polygon_json_invalid_json_is_json_decode_error() -> None:
    with pytest.raises(json.JSONDecodeError):
        loads_polygon_json("{")
