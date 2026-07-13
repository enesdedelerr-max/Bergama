"""TCP connectivity-only health adapter (no protocol-level validation)."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

from app.health.protocol import ERROR_CHECK_FAILED, ERROR_CHECK_UNAVAILABLE
from app.schemas.health import DependencyHealthResult, DependencyHealthStatus


@dataclass(slots=True)
class TcpConnectivityCheck:
    """Open a TCP connection only — never claim deep protocol health."""

    name: str
    required: bool
    timeout_seconds: float
    host: str | None
    port: int

    async def check(self) -> DependencyHealthResult:
        started = time.perf_counter()
        if self.host is None or not self.host.strip():
            return DependencyHealthResult(
                name=self.name,
                status=DependencyHealthStatus.SKIPPED,
                required=self.required,
                latency_ms=_latency_ms(started),
                message="configuration missing",
                error_code=None,
            )
        try:
            _reader, writer = await asyncio.open_connection(self.host.strip(), self.port)
            writer.close()
            await writer.wait_closed()
            return DependencyHealthResult(
                name=self.name,
                status=DependencyHealthStatus.PASS,
                required=self.required,
                latency_ms=_latency_ms(started),
                message="connectivity_only",
                error_code=None,
            )
        except OSError:
            return DependencyHealthResult(
                name=self.name,
                status=DependencyHealthStatus.FAIL,
                required=self.required,
                latency_ms=_latency_ms(started),
                message="connectivity-only check failed",
                error_code=ERROR_CHECK_UNAVAILABLE,
            )
        except Exception:
            return DependencyHealthResult(
                name=self.name,
                status=DependencyHealthStatus.FAIL,
                required=self.required,
                latency_ms=_latency_ms(started),
                message="dependency unavailable",
                error_code=ERROR_CHECK_FAILED,
            )


def _latency_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000.0, 3)
