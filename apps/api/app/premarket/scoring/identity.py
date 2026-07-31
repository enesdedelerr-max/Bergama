"""Identity Builder facade for Premarket Scoring."""

from __future__ import annotations

from app.premarket.scoring.ports import IdentityBuilder, ScoreIdentityInput


def build_score_record_id(builder: IdentityBuilder, draft: ScoreIdentityInput) -> str:
    """Build a deterministic score record identity via the bound Identity Spec."""
    return builder.build_id(draft)
