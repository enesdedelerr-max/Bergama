"""Unit tests for bounded in-flight admission control (#305)."""

from __future__ import annotations

import asyncio

import pytest
from app.market_data.orchestrator.admission import (
    AdmissionTimeoutError,
    InFlightAdmissionController,
)


@pytest.mark.asyncio
async def test_admission_acquire_release_and_stats() -> None:
    ctl = InFlightAdmissionController(max_in_flight=2, timeout_seconds=0.2)
    await ctl.acquire()
    await ctl.acquire()
    assert ctl.stats().in_flight == 2
    ctl.release()
    assert ctl.stats().in_flight == 1
    ctl.release()
    assert ctl.stats().in_flight == 0


@pytest.mark.asyncio
async def test_admission_timeout_fail_closed_under_concurrent_pressure() -> None:
    ctl = InFlightAdmissionController(max_in_flight=1, timeout_seconds=0.05)
    entered = asyncio.Event()
    release_first = asyncio.Event()

    async def hold() -> None:
        await ctl.acquire()
        entered.set()
        await release_first.wait()
        ctl.release()

    holder = asyncio.create_task(hold())
    await entered.wait()

    with pytest.raises(AdmissionTimeoutError, match="admission timeout"):
        await ctl.acquire()
    assert ctl.stats().overflow_count == 1

    release_first.set()
    await holder
    await ctl.acquire()
    ctl.release()
