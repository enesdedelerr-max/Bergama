"""Output construction helpers for Premarket Analyst projection."""

from __future__ import annotations

from app.premarket_analyst.models import PremarketAnalystArtifact


def artifact_to_canonical_dict(artifact: PremarketAnalystArtifact) -> dict[str, object]:
    """Stable python-mode dump for equality / hashing consumers."""
    return artifact.model_dump(mode="python")
