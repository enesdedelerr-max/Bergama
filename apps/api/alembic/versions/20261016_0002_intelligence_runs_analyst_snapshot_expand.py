"""Expand intelligence_runs for analyst snapshot v1/v2 coexistence (WS2).

Revision ID: 20261016_0002
Revises: 20261007_0001
Create Date: 2026-10-16

Additive expand only:
- nullable analyst_snapshot_json JSONB
- snapshot/persistence version checks accept v1 and v2
- analyst presence governed by snapshot version + outcome

Does not rewrite historical v1 rows.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from app.intelligence_runs.constants import (
    ANALYST_ELIGIBLE_OUTCOMES,
    ANALYST_INELIGIBLE_OUTCOMES,
    PERSISTENCE_SCHEMA_VERSION_V1,
    PERSISTENCE_SCHEMA_VERSION_V2,
    SNAPSHOT_CONTRACT_VERSION_V1,
    SNAPSHOT_CONTRACT_VERSION_V2,
)
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20261016_0002"
down_revision: str | None = "20261007_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ELIGIBLE_SQL_LIST = ", ".join(f"'{value}'" for value in ANALYST_ELIGIBLE_OUTCOMES)
_INELIGIBLE_SQL_LIST = ", ".join(f"'{value}'" for value in ANALYST_INELIGIBLE_OUTCOMES)


def upgrade() -> None:
    op.add_column(
        "intelligence_runs",
        sa.Column(
            "analyst_snapshot_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.drop_constraint(
        "ck_intelligence_runs_snapshot_contract_version",
        "intelligence_runs",
        type_="check",
    )
    op.drop_constraint(
        "ck_intelligence_runs_persistence_schema_version",
        "intelligence_runs",
        type_="check",
    )
    op.create_check_constraint(
        "ck_intelligence_runs_snapshot_contract_version",
        "intelligence_runs",
        "snapshot_contract_version IN ("
        f"'{SNAPSHOT_CONTRACT_VERSION_V1}', "
        f"'{SNAPSHOT_CONTRACT_VERSION_V2}'"
        ")",
    )
    op.create_check_constraint(
        "ck_intelligence_runs_persistence_schema_version",
        "intelligence_runs",
        "persistence_schema_version IN ("
        f"'{PERSISTENCE_SCHEMA_VERSION_V1}', "
        f"'{PERSISTENCE_SCHEMA_VERSION_V2}'"
        ")",
    )
    op.create_check_constraint(
        "ck_intelligence_runs_analyst_snapshot_version_outcome",
        "intelligence_runs",
        "("
        f"snapshot_contract_version = '{SNAPSHOT_CONTRACT_VERSION_V1}' "
        "AND analyst_snapshot_json IS NULL"
        ") OR ("
        f"snapshot_contract_version = '{SNAPSHOT_CONTRACT_VERSION_V2}' "
        f"AND outcome IN ({_INELIGIBLE_SQL_LIST}) "
        "AND analyst_snapshot_json IS NULL"
        ") OR ("
        f"snapshot_contract_version = '{SNAPSHOT_CONTRACT_VERSION_V2}' "
        f"AND outcome IN ({_ELIGIBLE_SQL_LIST}) "
        "AND analyst_snapshot_json IS NOT NULL"
        ")",
    )


def downgrade() -> None:
    """Restore pre-expand schema only when no v2/analyst rows remain."""
    conn = op.get_bind()
    incompatible = conn.execute(
        sa.text(
            "SELECT COUNT(*) FROM intelligence_runs WHERE "
            "analyst_snapshot_json IS NOT NULL "
            f"OR snapshot_contract_version = '{SNAPSHOT_CONTRACT_VERSION_V2}' "
            f"OR persistence_schema_version = '{PERSISTENCE_SCHEMA_VERSION_V2}'"
        )
    ).scalar_one()
    if incompatible:
        msg = (
            "cannot downgrade intelligence_runs analyst expand: "
            f"{incompatible} row(s) carry v2 versions or analyst snapshots"
        )
        raise RuntimeError(msg)

    op.drop_constraint(
        "ck_intelligence_runs_analyst_snapshot_version_outcome",
        "intelligence_runs",
        type_="check",
    )
    op.drop_constraint(
        "ck_intelligence_runs_snapshot_contract_version",
        "intelligence_runs",
        type_="check",
    )
    op.drop_constraint(
        "ck_intelligence_runs_persistence_schema_version",
        "intelligence_runs",
        type_="check",
    )
    op.drop_column("intelligence_runs", "analyst_snapshot_json")
    op.create_check_constraint(
        "ck_intelligence_runs_snapshot_contract_version",
        "intelligence_runs",
        f"snapshot_contract_version = '{SNAPSHOT_CONTRACT_VERSION_V1}'",
    )
    op.create_check_constraint(
        "ck_intelligence_runs_persistence_schema_version",
        "intelligence_runs",
        f"persistence_schema_version = '{PERSISTENCE_SCHEMA_VERSION_V1}'",
    )
