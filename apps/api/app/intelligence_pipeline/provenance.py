"""Thin Intelligence Pipeline composition provenance builders."""

from __future__ import annotations

from datetime import datetime

from app.dashboard.models import DashboardPresentationOutput
from app.intelligence_pipeline.models import PipelineOutcome, PipelineProvenance
from app.intelligence_pipeline.policy import STAGE_ORDER
from app.premarket.catalyst.models import CatalystCollection
from app.premarket.gap.models import GapCollection
from app.premarket.morning_briefing.models import BriefingCollection
from app.premarket.scoring.models import ScoreCollection
from app.premarket.watchlist.models import Watchlist


def build_provenance(
    *,
    as_of: datetime | None,
    executed_stages: tuple[str, ...],
    outcome: PipelineOutcome,
    failed_stage: str | None = None,
    watchlist: Watchlist | None = None,
    gaps: GapCollection | None = None,
    catalysts: CatalystCollection | None = None,
    scores: ScoreCollection | None = None,
    briefing: BriefingCollection | None = None,
    dashboard: DashboardPresentationOutput | None = None,
) -> PipelineProvenance:
    """Compose thin Pipeline provenance from stage public-output references."""
    return PipelineProvenance(
        as_of=as_of,
        stage_order=STAGE_ORDER,
        executed_stages=executed_stages,
        watchlist_config_fingerprint=(
            watchlist.provenance.config_fingerprint if watchlist is not None else None
        ),
        watchlist_input_fingerprint=(
            watchlist.provenance.input_fingerprint if watchlist is not None else None
        ),
        gap_config_fingerprint=(gaps.provenance.config_fingerprint if gaps is not None else None),
        gap_input_fingerprint=(gaps.provenance.input_fingerprint if gaps is not None else None),
        catalyst_config_fingerprint=(
            catalysts.provenance.config_fingerprint if catalysts is not None else None
        ),
        catalyst_input_fingerprint=(
            catalysts.provenance.input_fingerprint if catalysts is not None else None
        ),
        score_config_fingerprint=(
            scores.provenance.config_fingerprint if scores is not None else None
        ),
        score_input_fingerprint=(
            scores.provenance.input_fingerprint if scores is not None else None
        ),
        briefing_config_fingerprint=(
            briefing.provenance.config_fingerprint if briefing is not None else None
        ),
        briefing_input_fingerprint=(
            briefing.provenance.input_fingerprint if briefing is not None else None
        ),
        dashboard_config_fingerprint=(
            dashboard.provenance.config_fingerprint if dashboard is not None else None
        ),
        dashboard_input_fingerprint=(
            dashboard.provenance.input_fingerprint if dashboard is not None else None
        ),
        outcome=outcome,
        failed_stage=failed_stage,
    )
