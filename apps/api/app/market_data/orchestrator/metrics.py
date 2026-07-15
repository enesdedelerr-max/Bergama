"""Process-local orchestrator metrics (#305). No Prometheus dependency."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass(slots=True)
class OrchestratorMetrics:
    """In-process counters and gauges owned by one orchestrator instance."""

    admitted_total: int = 0
    published_total: int = 0
    dry_run_total: int = 0
    duplicate_suppressed_total: int = 0
    rejected_validation_total: int = 0
    rejected_pit_total: int = 0
    quality_degraded_total: int = 0
    quality_rejected_total: int = 0
    quality_quarantined_total: int = 0
    quality_halt_total: int = 0
    admission_overflow_total: int = 0
    publish_failed_total: int = 0
    in_flight_current: int = 0
    publish_latency_ms_total: float = 0.0
    publish_latency_samples: int = 0
    _latency_samples: list[float] = field(default_factory=list, repr=False)

    def record_publish_latency_ms(self, latency_ms: float) -> None:
        if latency_ms < 0:
            latency_ms = 0.0
        self.publish_latency_ms_total += latency_ms
        self.publish_latency_samples += 1
        self._latency_samples.append(latency_ms)

    def snapshot(self) -> Mapping[str, float | int]:
        avg = (
            self.publish_latency_ms_total / self.publish_latency_samples
            if self.publish_latency_samples
            else 0.0
        )
        return {
            "admitted_total": self.admitted_total,
            "published_total": self.published_total,
            "dry_run_total": self.dry_run_total,
            "duplicate_suppressed_total": self.duplicate_suppressed_total,
            "rejected_validation_total": self.rejected_validation_total,
            "rejected_pit_total": self.rejected_pit_total,
            "quality_degraded_total": self.quality_degraded_total,
            "quality_rejected_total": self.quality_rejected_total,
            "quality_quarantined_total": self.quality_quarantined_total,
            "quality_halt_total": self.quality_halt_total,
            "admission_overflow_total": self.admission_overflow_total,
            "publish_failed_total": self.publish_failed_total,
            "in_flight_current": self.in_flight_current,
            "publish_latency_ms_avg": avg,
            "publish_latency_samples": self.publish_latency_samples,
        }

    def clear(self) -> None:
        self.admitted_total = 0
        self.published_total = 0
        self.dry_run_total = 0
        self.duplicate_suppressed_total = 0
        self.rejected_validation_total = 0
        self.rejected_pit_total = 0
        self.quality_degraded_total = 0
        self.quality_rejected_total = 0
        self.quality_quarantined_total = 0
        self.quality_halt_total = 0
        self.admission_overflow_total = 0
        self.publish_failed_total = 0
        self.in_flight_current = 0
        self.publish_latency_ms_total = 0.0
        self.publish_latency_samples = 0
        self._latency_samples.clear()
