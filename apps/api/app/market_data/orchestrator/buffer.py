"""Deprecated module name retained for import stability.

#305 uses bounded in-flight admission control (`admission.py`), not a durable
buffer or asynchronous queue.
"""

from __future__ import annotations

from app.market_data.orchestrator.admission import (
    AdmissionStats,
    AdmissionTimeoutError,
    InFlightAdmissionController,
)

# Historical aliases — do not treat as a FIFO queue API.
BufferOverflowError = AdmissionTimeoutError
BufferStats = AdmissionStats
BoundedBuffer = InFlightAdmissionController

__all__ = [
    "AdmissionStats",
    "AdmissionTimeoutError",
    "BoundedBuffer",
    "BufferOverflowError",
    "BufferStats",
    "InFlightAdmissionController",
]
