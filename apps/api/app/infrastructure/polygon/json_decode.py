"""Decimal-preserving JSON decode for Polygon provider payloads.

The loader is JSON-neutral: it raises ``json.JSONDecodeError`` or ``ValueError``.
Call sites map those errors onto Polygon HTTP or WebSocket exception types.
"""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any, NoReturn


def _reject_json_constant(value: str) -> NoReturn:
    msg = f"non-finite JSON constant {value!r} is not admitted"
    raise ValueError(msg)


def loads_polygon_json(raw: str | bytes | bytearray) -> Any:
    """Decode Polygon JSON with Decimal floats and rejected NaN/Infinity."""
    return json.loads(
        raw,
        parse_float=Decimal,
        parse_constant=_reject_json_constant,
    )
