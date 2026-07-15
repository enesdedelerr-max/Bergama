"""Quarantine boundary and local/test implementations (#310)."""

from __future__ import annotations

import contextlib
import json
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from app.market_data.data_quality.models import QualityAssessment
from app.market_data.envelope import CanonicalMarketEvent


@dataclass(frozen=True, slots=True)
class QuarantineResult:
    succeeded: bool
    quarantined_at_id: str | None = None
    safe_metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class QuarantineRecord:
    assessment_id: str
    event_type: str
    instrument_key: str
    idempotency_key: str
    correlation_id: str
    reason_codes: tuple[str, ...]
    policy_fingerprint: str


class QuarantinePort(Protocol):
    async def quarantine(
        self,
        event: CanonicalMarketEvent,
        *,
        assessment: QualityAssessment,
        correlation_id: str,
    ) -> QuarantineResult: ...


class InMemoryQuarantinePort:
    """Bounded local/test quarantine sink. Not production persistence."""

    def __init__(self, *, max_records: int = 1_000) -> None:
        if max_records < 1:
            msg = "max_records must be >= 1"
            raise ValueError(msg)
        self._max_records = max_records
        self._records: list[QuarantineRecord] = []

    @property
    def records(self) -> tuple[QuarantineRecord, ...]:
        return tuple(self._records)

    async def quarantine(
        self,
        event: CanonicalMarketEvent,
        *,
        assessment: QualityAssessment,
        correlation_id: str,
    ) -> QuarantineResult:
        record = _record_for(event, assessment=assessment, correlation_id=correlation_id)
        self._records.append(record)
        overflow = len(self._records) - self._max_records
        if overflow > 0:
            del self._records[0:overflow]
        return QuarantineResult(
            succeeded=True,
            quarantined_at_id=record.assessment_id,
            safe_metadata={"sink": "in_memory"},
        )

    async def aclose(self) -> None:
        self._records.clear()


class FileQuarantinePort:
    """Atomic JSONL local/test quarantine sink. Not a production queue/table."""

    def __init__(self, directory: str | Path) -> None:
        self._root = Path(directory)
        if not self._root.is_absolute():
            msg = "quarantine directory must be absolute"
            raise ValueError(msg)
        self._root.mkdir(parents=True, exist_ok=True)
        with contextlib.suppress(OSError):
            os.chmod(self._root, 0o700)
        self._closed = False

    async def quarantine(
        self,
        event: CanonicalMarketEvent,
        *,
        assessment: QualityAssessment,
        correlation_id: str,
    ) -> QuarantineResult:
        if self._closed:
            return QuarantineResult(succeeded=False, safe_metadata={"reason": "closed"})
        record = _record_for(event, assessment=assessment, correlation_id=correlation_id)
        payload = json.dumps(
            {
                "assessment_id": record.assessment_id,
                "event_type": record.event_type,
                "instrument_key": record.instrument_key,
                "idempotency_key": record.idempotency_key,
                "correlation_id": record.correlation_id,
                "reason_codes": list(record.reason_codes),
                "policy_fingerprint": record.policy_fingerprint,
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
        target = self._root / f"{record.assessment_id}.json"
        fd, tmp_name = tempfile.mkstemp(
            prefix=f".{record.assessment_id}.",
            suffix=".tmp",
            dir=str(self._root),
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, target)
            with contextlib.suppress(OSError):
                os.chmod(target, 0o600)
        finally:
            if os.path.exists(tmp_name):
                with contextlib.suppress(OSError):
                    os.unlink(tmp_name)
        return QuarantineResult(
            succeeded=True,
            quarantined_at_id=record.assessment_id,
            safe_metadata={"sink": "file"},
        )

    async def aclose(self) -> None:
        self._closed = True


def _record_for(
    event: CanonicalMarketEvent,
    *,
    assessment: QualityAssessment,
    correlation_id: str,
) -> QuarantineRecord:
    return QuarantineRecord(
        assessment_id=assessment.assessment_id,
        event_type=event.event_type.value,
        instrument_key=event.instrument.instrument_key,
        idempotency_key=assessment.idempotency_key,
        correlation_id=correlation_id[:128],
        reason_codes=tuple(
            result.reason_code for result in assessment.rule_results if not result.passed
        ),
        policy_fingerprint=assessment.policy_fingerprint,
    )
