"""Create intelligence_runs hybrid persistence table.

Revision ID: 20261007_0001
Revises:
Create Date: 2026-10-07

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.intelligence_runs.constants import (
    FAILURE_DETAIL_MAX_CHARS,
    PERSISTED_OUTCOMES,
    PERSISTENCE_SCHEMA_VERSION,
    PIPELINE_FINGERPRINT_LENGTH,
    SNAPSHOT_CONTRACT_VERSION,
)

# revision identifiers, used by Alembic.
revision: str = "20261007_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_OUTCOME_SQL_LIST = ", ".join(f"'{value}'" for value in PERSISTED_OUTCOMES)


def upgrade() -> None:
    op.create_table(
        "intelligence_runs",
        sa.Column("run_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column(
            "pipeline_fingerprint",
            sa.String(length=PIPELINE_FINGERPRINT_LENGTH),
            nullable=True,
        ),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=True),
        sa.Column("outcome", sa.Text(), nullable=False),
        sa.Column("failed_stage", sa.Text(), nullable=True),
        sa.Column("failure_error_type", sa.Text(), nullable=True),
        sa.Column(
            "failure_detail",
            sa.String(length=FAILURE_DETAIL_MAX_CHARS),
            nullable=True,
        ),
        sa.Column("bindings_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("provenance_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "stage_presence_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "dashboard_snapshot_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "human_review_snapshot_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "ade_snapshot_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("snapshot_contract_version", sa.Text(), nullable=False),
        sa.Column("persistence_schema_version", sa.Text(), nullable=False),
        sa.Column(
            "persisted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            f"outcome IN ({_OUTCOME_SQL_LIST})",
            name="ck_intelligence_runs_outcome",
        ),
        sa.CheckConstraint(
            "pipeline_fingerprint IS NULL OR ("
            f"char_length(pipeline_fingerprint) = {PIPELINE_FINGERPRINT_LENGTH} "
            "AND pipeline_fingerprint ~ '^[0-9a-f]+$'"
            ")",
            name="ck_intelligence_runs_pipeline_fingerprint",
        ),
        sa.CheckConstraint(
            f"failure_detail IS NULL OR char_length(failure_detail) <= {FAILURE_DETAIL_MAX_CHARS}",
            name="ck_intelligence_runs_failure_detail_length",
        ),
        sa.CheckConstraint(
            f"snapshot_contract_version = '{SNAPSHOT_CONTRACT_VERSION}'",
            name="ck_intelligence_runs_snapshot_contract_version",
        ),
        sa.CheckConstraint(
            f"persistence_schema_version = '{PERSISTENCE_SCHEMA_VERSION}'",
            name="ck_intelligence_runs_persistence_schema_version",
        ),
        sa.PrimaryKeyConstraint("run_id"),
        sa.UniqueConstraint(
            "pipeline_fingerprint",
            "snapshot_contract_version",
            name="uq_intelligence_runs_fingerprint_snapshot_version",
        ),
    )
    op.execute(
        """
        CREATE INDEX ix_intelligence_runs_latest_dashboard
        ON intelligence_runs (as_of DESC NULLS LAST, persisted_at DESC, run_id ASC)
        WHERE dashboard_snapshot_json IS NOT NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_intelligence_runs_latest_dashboard")
    op.drop_table("intelligence_runs")
