"""Deterministic Intelligence Pipeline composition through Dashboard."""

from __future__ import annotations

from datetime import datetime

from app.dashboard.engine import assemble_dashboard
from app.dashboard.models import DashboardRequest
from app.intelligence_pipeline.admit import admit_pipeline_request, pin_bindings
from app.intelligence_pipeline.errors import PipelineAdmissionError
from app.intelligence_pipeline.models import (
    PipelineBindings,
    PipelineOutcome,
    PipelineRequest,
    PipelineResult,
)
from app.intelligence_pipeline.policy import (
    STAGE_BRIEFING,
    STAGE_CATALYST,
    STAGE_DASHBOARD,
    STAGE_GAP,
    STAGE_SCORE,
    STAGE_WATCHLIST,
)
from app.intelligence_pipeline.provenance import build_provenance
from app.premarket.catalyst.engine import normalize_catalysts
from app.premarket.catalyst.models import CatalystCollection, CatalystNormalizationRequest
from app.premarket.gap.engine import scan_gaps
from app.premarket.gap.models import GapCollection, GapScanRequest
from app.premarket.morning_briefing.engine import assemble_briefing
from app.premarket.morning_briefing.models import BriefingCollection, BriefingRequest
from app.premarket.scoring.engine import scan_scores
from app.premarket.scoring.models import ScoreCollection, ScoreRequest
from app.premarket.watchlist.engine import generate_watchlist
from app.premarket.watchlist.models import Watchlist, WatchlistGenerationRequest


def run_intelligence_pipeline(request: PipelineRequest | object) -> PipelineResult:
    """Execute the authorized Issue #126 core path through Dashboard.

    Topology: Watchlist → Gap → Catalyst → Score → Morning Briefing → Dashboard.
    """
    try:
        admitted = admit_pipeline_request(request)
    except PipelineAdmissionError as exc:
        return _admission_rejected(detail=exc.detail or exc.code)

    as_of = admitted.as_of
    bindings = pin_bindings(admitted)
    settings = admitted.settings
    executed: list[str] = []

    try:
        watchlist = generate_watchlist(
            WatchlistGenerationRequest(
                candidates=admitted.candidates,
                as_of=as_of,
                config=admitted.watchlist_config,
            ),
            settings=settings,
        )
        executed.append(STAGE_WATCHLIST)
    except Exception as exc:  # noqa: BLE001 — composition maps any stage failure
        return _stage_failed(
            as_of=as_of,
            bindings=bindings,
            executed_stages=tuple(executed),
            stage=STAGE_WATCHLIST,
            exc=exc,
        )

    try:
        gaps = scan_gaps(
            GapScanRequest(
                watchlist=watchlist,
                bars=admitted.bars,
                as_of=as_of,
                config=admitted.gap_config,
            ),
            settings=settings,
        )
        executed.append(STAGE_GAP)
    except Exception as exc:  # noqa: BLE001
        return _stage_failed(
            as_of=as_of,
            bindings=bindings,
            executed_stages=tuple(executed),
            stage=STAGE_GAP,
            exc=exc,
            watchlist=watchlist,
        )

    try:
        catalysts = normalize_catalysts(
            CatalystNormalizationRequest(
                events=admitted.events,
                as_of=as_of,
                config=admitted.catalyst_config,
            ),
            settings=settings,
        )
        executed.append(STAGE_CATALYST)
    except Exception as exc:  # noqa: BLE001
        return _stage_failed(
            as_of=as_of,
            bindings=bindings,
            executed_stages=tuple(executed),
            stage=STAGE_CATALYST,
            exc=exc,
            watchlist=watchlist,
            gaps=gaps,
        )

    # Preserve actual GapCollection / CatalystCollection objects (empty ≠ None).
    try:
        scores = scan_scores(
            ScoreRequest(
                watchlist=watchlist,
                as_of=as_of,
                config=admitted.score_config,
                gaps=gaps,
                catalysts=catalysts,
            ),
            settings=settings,
        )
        executed.append(STAGE_SCORE)
    except Exception as exc:  # noqa: BLE001
        return _stage_failed(
            as_of=as_of,
            bindings=bindings,
            executed_stages=tuple(executed),
            stage=STAGE_SCORE,
            exc=exc,
            watchlist=watchlist,
            gaps=gaps,
            catalysts=catalysts,
        )

    try:
        briefing = assemble_briefing(
            BriefingRequest(
                scores=scores,
                as_of=as_of,
                config=admitted.briefing_config,
            ),
            settings=settings,
        )
        executed.append(STAGE_BRIEFING)
    except Exception as exc:  # noqa: BLE001
        return _stage_failed(
            as_of=as_of,
            bindings=bindings,
            executed_stages=tuple(executed),
            stage=STAGE_BRIEFING,
            exc=exc,
            watchlist=watchlist,
            gaps=gaps,
            catalysts=catalysts,
            scores=scores,
        )

    try:
        dashboard = assemble_dashboard(
            DashboardRequest(
                briefing=briefing,
                as_of=as_of,
                config=admitted.dashboard_config,
            )
        )
        executed.append(STAGE_DASHBOARD)
    except Exception as exc:  # noqa: BLE001
        return _stage_failed(
            as_of=as_of,
            bindings=bindings,
            executed_stages=tuple(executed),
            stage=STAGE_DASHBOARD,
            exc=exc,
            watchlist=watchlist,
            gaps=gaps,
            catalysts=catalysts,
            scores=scores,
            briefing=briefing,
        )

    outcome = PipelineOutcome.COMPLETED_DASHBOARD
    return PipelineResult(
        outcome=outcome,
        as_of=as_of,
        bindings=bindings,
        provenance=build_provenance(
            as_of=as_of,
            executed_stages=tuple(executed),
            outcome=outcome,
            watchlist=watchlist,
            gaps=gaps,
            catalysts=catalysts,
            scores=scores,
            briefing=briefing,
            dashboard=dashboard,
        ),
        watchlist=watchlist,
        gaps=gaps,
        catalysts=catalysts,
        scores=scores,
        briefing=briefing,
        dashboard=dashboard,
    )


def _admission_rejected(*, detail: str | None) -> PipelineResult:
    outcome = PipelineOutcome.ADMISSION_REJECTED
    return PipelineResult(
        outcome=outcome,
        as_of=None,
        bindings=None,
        provenance=build_provenance(
            as_of=None,
            executed_stages=(),
            outcome=outcome,
        ),
        failure_detail=detail,
        failure_error_type=PipelineAdmissionError.__name__,
    )


def _stage_failed(
    *,
    as_of: datetime,
    bindings: PipelineBindings,
    executed_stages: tuple[str, ...],
    stage: str,
    exc: BaseException,
    watchlist: Watchlist | None = None,
    gaps: GapCollection | None = None,
    catalysts: CatalystCollection | None = None,
    scores: ScoreCollection | None = None,
    briefing: BriefingCollection | None = None,
) -> PipelineResult:
    outcome = PipelineOutcome.REQUIRED_STAGE_FAILED
    detail = getattr(exc, "detail", None)
    if detail is None:
        detail = str(exc) or type(exc).__name__
    return PipelineResult(
        outcome=outcome,
        as_of=as_of,
        bindings=bindings,
        provenance=build_provenance(
            as_of=as_of,
            executed_stages=executed_stages,
            outcome=outcome,
            failed_stage=stage,
            watchlist=watchlist,
            gaps=gaps,
            catalysts=catalysts,
            scores=scores,
            briefing=briefing,
        ),
        watchlist=watchlist,
        gaps=gaps,
        catalysts=catalysts,
        scores=scores,
        briefing=briefing,
        failed_stage=stage,
        failure_detail=str(detail),
        failure_error_type=type(exc).__name__,
    )
