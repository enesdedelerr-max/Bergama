"""Cheap, non-mutating Iceberg writer health check (#307)."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from app.core.iceberg_writer_settings import IcebergWriterSettings
from app.infrastructure.iceberg.catalog import table_identifier
from app.infrastructure.iceberg.routing import all_table_bases
from app.schemas.health import DependencyHealthResult, DependencyHealthStatus


@dataclass(slots=True)
class IcebergWriterHealthCheck:
    """Read-only presence checks. Never appends, creates tables, or snapshots."""

    settings: IcebergWriterSettings
    timeout_seconds: float
    catalog_probe: Callable[[], Any] | None
    tables_probe: Callable[[], Any] | None
    worker_started: Callable[[], bool] | None = None
    name: str = "iceberg_writer"

    @property
    def required(self) -> bool:
        return bool(self.settings.required)

    async def check(self) -> DependencyHealthResult:
        if not self.settings.enabled:
            return DependencyHealthResult(
                name=self.name,
                status=DependencyHealthStatus.SKIPPED,
                latency_ms=0.0,
                required=self.required,
                message="iceberg writer disabled",
            )
        started = time.perf_counter()
        try:
            if self.catalog_probe is not None:
                self.catalog_probe()
            if self.tables_probe is not None:
                self.tables_probe()
            if self.worker_started is not None and not self.worker_started():
                return DependencyHealthResult(
                    name=self.name,
                    status=DependencyHealthStatus.FAIL,
                    latency_ms=(time.perf_counter() - started) * 1000.0,
                    required=self.required,
                    message="iceberg writer worker not started",
                )
        except Exception as exc:
            return DependencyHealthResult(
                name=self.name,
                status=DependencyHealthStatus.FAIL,
                latency_ms=(time.perf_counter() - started) * 1000.0,
                required=self.required,
                message=f"iceberg writer health failed: {exc.__class__.__name__}",
            )
        return DependencyHealthResult(
            name=self.name,
            status=DependencyHealthStatus.PASS,
            latency_ms=(time.perf_counter() - started) * 1000.0,
            required=self.required,
            message="catalog reachable; required tables present",
        )


def build_table_list(settings: IcebergWriterSettings) -> list[str]:
    return [
        table_identifier(
            settings.namespace,
            f"{settings.table_prefix}{base}" if settings.table_prefix else base,
        )
        for base in all_table_bases()
    ]
