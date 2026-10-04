"""Deterministic Intelligence Pipeline composition through optional HR/ADE terminals."""

from __future__ import annotations

from datetime import datetime

from app.ai_decision_engine.engine import evaluate_ade
from app.ai_decision_engine.models import AdeEvaluationRequest, AdeOutcomeKind
from app.dashboard.engine import assemble_dashboard
from app.dashboard.models import DashboardPresentationOutput, DashboardRequest
from app.human_review.engine import assemble_human_review
from app.human_review.models import HumanReviewOutput, HumanReviewRequest
from app.intelligence_pipeline.admit import (
    admit_pipeline_request,
    pin_bindings,
    resolve_ade_config,
    resolve_hr_config,
)
from app.intelligence_pipeline.errors import PipelineAdmissionError
from app.intelligence_pipeline.models import (
    PipelineBindings,
    PipelineOutcome,
    PipelineRequest,
    PipelineResult,
)
from app.intelligence_pipeline.policy import (
    STAGE_ADE,
    STAGE_BRIEFING,
    STAGE_CATALYST,
    STAGE_DASHBOARD,
    STAGE_GAP,
    STAGE_HUMAN_REVIEW,
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
    """Execute the authorized Intelligence Pipeline through Dashboard and optional terminals.

    Topology: Watchlist → Gap → Catalyst → Score → Morning Briefing → Dashboard
    → optional Human Review → optional ADE.
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

    if not admitted.hr_requested:
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

    # Attestation presence is enforced at admission; assert for type narrowing.
    if admitted.hr_attestation is None:
        return _admission_rejected(detail="human_review_attestation_required")

    hr_config = resolve_hr_config(admitted)
    try:
        human_review = assemble_human_review(
            HumanReviewRequest(
                dashboard=dashboard,
                as_of=as_of,
                config=hr_config,
                attestation=admitted.hr_attestation,
            )
        )
        executed.append(STAGE_HUMAN_REVIEW)
    except Exception as exc:  # noqa: BLE001
        return _stage_failed(
            as_of=as_of,
            bindings=bindings,
            executed_stages=tuple(executed),
            stage=STAGE_HUMAN_REVIEW,
            exc=exc,
            watchlist=watchlist,
            gaps=gaps,
            catalysts=catalysts,
            scores=scores,
            briefing=briefing,
            dashboard=dashboard,
        )

    if not admitted.ade_requested:
        outcome = PipelineOutcome.COMPLETED_HUMAN_REVIEW
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
                human_review=human_review,
            ),
            watchlist=watchlist,
            gaps=gaps,
            catalysts=catalysts,
            scores=scores,
            briefing=briefing,
            dashboard=dashboard,
            human_review=human_review,
        )

    ade_config = resolve_ade_config(admitted)
    try:
        ade = evaluate_ade(
            AdeEvaluationRequest(
                human_review=human_review,
                as_of=as_of,
                config=ade_config,
            )
        )
        executed.append(STAGE_ADE)
    except Exception as exc:  # noqa: BLE001
        return _stage_failed(
            as_of=as_of,
            bindings=bindings,
            executed_stages=tuple(executed),
            stage=STAGE_ADE,
            exc=exc,
            watchlist=watchlist,
            gaps=gaps,
            catalysts=catalysts,
            scores=scores,
            briefing=briefing,
            dashboard=dashboard,
            human_review=human_review,
        )

    if ade.outcome_kind is AdeOutcomeKind.AUTHORITATIVE_DECISION:
        outcome = PipelineOutcome.COMPLETED_ADE_ACCEPT
    elif ade.outcome_kind is AdeOutcomeKind.EXPLICIT_ABSTENTION:
        outcome = PipelineOutcome.COMPLETED_ADE_ABSTAIN
    else:
        return _stage_failed(
            as_of=as_of,
            bindings=bindings,
            executed_stages=tuple(executed),
            stage=STAGE_ADE,
            exc=RuntimeError(f"unexpected_ade_outcome_kind:{ade.outcome_kind!r}"),
            watchlist=watchlist,
            gaps=gaps,
            catalysts=catalysts,
            scores=scores,
            briefing=briefing,
            dashboard=dashboard,
            human_review=human_review,
        )

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
            human_review=human_review,
            ade=ade,
        ),
        watchlist=watchlist,
        gaps=gaps,
        catalysts=catalysts,
        scores=scores,
        briefing=briefing,
        dashboard=dashboard,
        human_review=human_review,
        ade=ade,
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
    dashboard: DashboardPresentationOutput | None = None,
    human_review: HumanReviewOutput | None = None,
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
            dashboard=dashboard,
            human_review=human_review,
        ),
        watchlist=watchlist,
        gaps=gaps,
        catalysts=catalysts,
        scores=scores,
        briefing=briefing,
        dashboard=dashboard,
        human_review=human_review,
        failed_stage=stage,
        failure_detail=str(detail),
        failure_error_type=type(exc).__name__,
    )
