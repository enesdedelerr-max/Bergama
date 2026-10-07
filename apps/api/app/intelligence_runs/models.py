"""SQLAlchemy ORM model for the ``intelligence_runs`` hybrid envelope (WS1)."""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Index,
    MetaData,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, validates

from app.intelligence_runs.constants import (
    FAILURE_DETAIL_MAX_CHARS,
    PERSISTED_OUTCOMES,
    PERSISTENCE_SCHEMA_VERSION,
    PIPELINE_FINGERPRINT_LENGTH,
    SNAPSHOT_CONTRACT_VERSION,
)

_FINGERPRINT_RE = re.compile(rf"^[0-9a-f]{{{PIPELINE_FINGERPRINT_LENGTH}}}$")
_OUTCOME_SQL_LIST = ", ".join(f"'{value}'" for value in PERSISTED_OUTCOMES)

INTELLIGENCE_RUNS_TABLE = "intelligence_runs"

metadata = MetaData()


class IntelligenceRunsBase(DeclarativeBase):
    metadata = metadata


class IntelligenceRunRecord(IntelligenceRunsBase):
    """Insert-only durable Intelligence Run persistence row."""

    __tablename__ = INTELLIGENCE_RUNS_TABLE
    __table_args__ = (
        CheckConstraint(
            f"outcome IN ({_OUTCOME_SQL_LIST})",
            name="ck_intelligence_runs_outcome",
        ),
        CheckConstraint(
            "pipeline_fingerprint IS NULL OR ("
            f"char_length(pipeline_fingerprint) = {PIPELINE_FINGERPRINT_LENGTH} "
            "AND pipeline_fingerprint ~ '^[0-9a-f]+$'"
            ")",
            name="ck_intelligence_runs_pipeline_fingerprint",
        ),
        CheckConstraint(
            f"failure_detail IS NULL OR char_length(failure_detail) <= {FAILURE_DETAIL_MAX_CHARS}",
            name="ck_intelligence_runs_failure_detail_length",
        ),
        CheckConstraint(
            f"snapshot_contract_version = '{SNAPSHOT_CONTRACT_VERSION}'",
            name="ck_intelligence_runs_snapshot_contract_version",
        ),
        CheckConstraint(
            f"persistence_schema_version = '{PERSISTENCE_SCHEMA_VERSION}'",
            name="ck_intelligence_runs_persistence_schema_version",
        ),
        UniqueConstraint(
            "pipeline_fingerprint",
            "snapshot_contract_version",
            name="uq_intelligence_runs_fingerprint_snapshot_version",
        ),
        Index(
            "ix_intelligence_runs_latest_dashboard",
            "as_of",
            "persisted_at",
            "run_id",
            postgresql_ops={
                "as_of": "DESC NULLS LAST",
                "persisted_at": "DESC",
                "run_id": "ASC",
            },
            postgresql_where=text("dashboard_snapshot_json IS NOT NULL"),
        ),
    )

    run_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    pipeline_fingerprint: Mapped[str | None] = mapped_column(
        String(PIPELINE_FINGERPRINT_LENGTH),
        nullable=True,
    )
    as_of: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    outcome: Mapped[str] = mapped_column(Text, nullable=False)
    failed_stage: Mapped[str | None] = mapped_column(Text, nullable=True)
    failure_error_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    failure_detail: Mapped[str | None] = mapped_column(
        String(FAILURE_DETAIL_MAX_CHARS),
        nullable=True,
    )
    bindings_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    provenance_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    stage_presence_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    dashboard_snapshot_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    human_review_snapshot_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    ade_snapshot_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    snapshot_contract_version: Mapped[str] = mapped_column(Text, nullable=False)
    persistence_schema_version: Mapped[str] = mapped_column(Text, nullable=False)
    persisted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    @validates("pipeline_fingerprint")
    def _validate_fingerprint(self, _key: str, value: str | None) -> str | None:
        if value is None:
            return None
        if not _FINGERPRINT_RE.fullmatch(value):
            msg = (
                "pipeline_fingerprint must be "
                f"{PIPELINE_FINGERPRINT_LENGTH}-char lowercase hex or NULL"
            )
            raise ValueError(msg)
        return value

    @validates("outcome")
    def _validate_outcome(self, _key: str, value: str) -> str:
        if value not in PERSISTED_OUTCOMES:
            msg = f"outcome must be one of {PERSISTED_OUTCOMES}"
            raise ValueError(msg)
        return value

    @validates("failure_detail")
    def _validate_failure_detail(self, _key: str, value: str | None) -> str | None:
        if value is None:
            return None
        if len(value) > FAILURE_DETAIL_MAX_CHARS:
            msg = f"failure_detail exceeds {FAILURE_DETAIL_MAX_CHARS} characters"
            raise ValueError(msg)
        return value

    @validates("snapshot_contract_version")
    def _validate_snapshot_version(self, _key: str, value: str) -> str:
        if value != SNAPSHOT_CONTRACT_VERSION:
            msg = f"snapshot_contract_version must be {SNAPSHOT_CONTRACT_VERSION!r}"
            raise ValueError(msg)
        return value

    @validates("persistence_schema_version")
    def _validate_persistence_version(self, _key: str, value: str) -> str:
        if value != PERSISTENCE_SCHEMA_VERSION:
            msg = f"persistence_schema_version must be {PERSISTENCE_SCHEMA_VERSION!r}"
            raise ValueError(msg)
        return value
