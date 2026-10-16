"""Deterministic Premarket Analyst projection engine (no upstream engine re-run)."""

from __future__ import annotations

from app.premarket.catalyst.models import CatalystRecord
from app.premarket.gap.models import GapRecord
from app.premarket_analyst.errors import (
    PremarketAnalystFailClosedError,
    PremarketAnalystValidationError,
)
from app.premarket_analyst.identity import build_analyst_artifact_id
from app.premarket_analyst.models import (
    AnalystProjectionRequest,
    CatalystCoverageAggregates,
    CatalystSummary,
    CatalystSummaryRecord,
    DataCompletenessMarkers,
    EvaluationState,
    GapCoverageAggregates,
    MarketSummary,
    PremarketAnalystArtifact,
    RiskFlag,
    ScoreDashboardRefs,
    StructuredThesis,
)
from app.premarket_analyst.ordering import (
    assert_ordering_policy,
    sort_catalyst_summary_records,
    sort_membership_refs,
    sort_risk_flags,
    sort_theses,
)
from app.premarket_analyst.policy import (
    EVALUATION_STATE_COLLAPSE_ORDER,
    FIELD_COMPLETENESS_MATRIX,
)
from app.premarket_analyst.provenance import build_analyst_provenance
from app.premarket_analyst.validate_input import (
    ValidatedAnalystRequest,
    coerce_analyst_request,
    validate_analyst_request,
)
from app.strategy.keys import strategy_sha256


def project_analyst(request: AnalystProjectionRequest | object) -> PremarketAnalystArtifact:
    """Project PremarketAnalystArtifact from already-produced upstream public outputs."""
    from app.premarket_analyst.pipeline import run_analyst_pipeline

    validated_model = coerce_analyst_request(request)
    validated = validate_analyst_request(validated_model)
    return run_analyst_pipeline(validated)


def collapse_evaluation_states(states: tuple[EvaluationState, ...]) -> EvaluationState:
    """Apply approved EVALUATION_STATE_COLLAPSE_ORDER (not severity / not equivalence)."""
    if not states:
        return "EVALUABLE"
    # Lower index = higher collapse rank (NOT_EVALUABLE wins over EVALUABLE).
    best_rank = min(EVALUATION_STATE_COLLAPSE_ORDER.index(state) for state in states)
    return EVALUATION_STATE_COLLAPSE_ORDER[best_rank]


def _required(field: str) -> bool:
    return FIELD_COMPLETENESS_MATRIX[field] == "required"


def collect_condition_states(
    request: ValidatedAnalystRequest,
) -> tuple[tuple[EvaluationState, ...], tuple[RiskFlag, ...], dict[str, object]]:
    """Map Policy conditions to evaluation states and risk flags (OIA-04 approved)."""
    states: list[EvaluationState] = []
    flags: list[RiskFlag] = []
    markers: dict[str, object] = {
        "catalyst_absence": False,
        "catalyst_unavailable": request.catalysts is None,
        "stale_catalyst_ids": (),
        "usable_catalysts": (),
        "usable_gaps": (),
        "propagate_failure": False,
    }

    membership = tuple(entry.instrument_key for entry in request.watchlist.entries)
    membership_set = set(membership)

    # Partial watchlist — approved: INSUFFICIENT_EVIDENCE; never invent membership
    if not request.membership_complete:
        states.append("INSUFFICIENT_EVIDENCE")
        flags.append(
            _risk_flag(
                category="MISSING_DATA",
                as_of=request.as_of,
                evidence_refs=("membership_complete=false",),
                provenance_refs=(request.watchlist.provenance.input_fingerprint,),
            )
        )

    # Unsupported securities
    for key in request.unsupported_instrument_keys:
        states.append("NOT_EVALUABLE")
        flags.append(
            _risk_flag(
                category="UNSUPPORTED_EVALUATION",
                as_of=request.as_of,
                evidence_refs=(f"unsupported:{key}",),
                provenance_refs=(request.watchlist.provenance.input_fingerprint,),
            )
        )

    # Watchlist required concepts
    if _required("market_summary.watchlist_membership_refs") and not membership:
        states.append("NOT_EVALUABLE")
        flags.append(
            _risk_flag(
                category="NOT_EVALUABLE_INPUT",
                as_of=request.as_of,
                evidence_refs=("watchlist_membership_empty",),
                provenance_refs=(request.watchlist.provenance.input_fingerprint,),
            )
        )

    # Gap coverage (required for market summary)
    usable_gaps: list[GapRecord] = []
    if request.gaps is None:
        if _required("market_summary.gap_coverage_aggregates"):
            states.append("NOT_EVALUABLE")
            flags.append(
                _risk_flag(
                    category="MISSING_DATA",
                    as_of=request.as_of,
                    evidence_refs=("gaps_collection_absent",),
                    provenance_refs=(),
                )
            )
    else:
        for gap_record in request.gaps.records:
            if gap_record.known_at > request.as_of:
                states.append("NOT_EVALUABLE")
                flags.append(
                    _risk_flag(
                        category="STALE_DATA",
                        as_of=request.as_of,
                        evidence_refs=(f"gap_stale:{gap_record.gap_record_id}",),
                        provenance_refs=(request.gaps.provenance.input_fingerprint,),
                    )
                )
                continue
            usable_gaps.append(gap_record)
        if not usable_gaps:
            states.append("INSUFFICIENT_EVIDENCE")
            flags.append(
                _risk_flag(
                    category="MISSING_DATA",
                    as_of=request.as_of,
                    evidence_refs=("gap_evidence_empty",),
                    provenance_refs=(request.gaps.provenance.input_fingerprint,),
                )
            )

    # Catalysts
    usable_catalysts: list[CatalystRecord] = []
    stale_ids: list[str] = []
    if request.catalysts is None:
        markers["catalyst_absence"] = True
        markers["catalyst_unavailable"] = True
        states.append("INSUFFICIENT_EVIDENCE")
        flags.append(
            _risk_flag(
                category="WEAK_CATALYST_COVERAGE",
                as_of=request.as_of,
                evidence_refs=("catalysts_unavailable",),
                provenance_refs=(),
            )
        )
    else:
        for catalyst_record in request.catalysts.records:
            if catalyst_record.known_at > request.as_of:
                stale_ids.append(catalyst_record.catalyst_record_id)
                continue
            usable_catalysts.append(catalyst_record)
        if stale_ids:
            states.append("NOT_EVALUABLE")
            flags.append(
                _risk_flag(
                    category="STALE_DATA",
                    as_of=request.as_of,
                    evidence_refs=tuple(f"catalyst_stale:{cid}" for cid in sorted(stale_ids)),
                    provenance_refs=(request.catalysts.provenance.input_fingerprint,),
                )
            )
        if not usable_catalysts:
            markers["catalyst_absence"] = True
            states.append("INSUFFICIENT_EVIDENCE")
            flags.append(
                _risk_flag(
                    category="WEAK_CATALYST_COVERAGE",
                    as_of=request.as_of,
                    evidence_refs=("catalyst_records_absent",),
                    provenance_refs=(request.catalysts.provenance.input_fingerprint,),
                )
            )

    # Score / dashboard refs (required)
    if request.scores is None and request.dashboard is None:
        if _required("market_summary.score_dashboard_refs"):
            states.append("NOT_EVALUABLE")
            flags.append(
                _risk_flag(
                    category="NOT_EVALUABLE_INPUT",
                    as_of=request.as_of,
                    evidence_refs=("score_and_dashboard_absent",),
                    provenance_refs=(),
                )
            )
    elif request.scores is not None and not request.scores.records:
        states.append("INSUFFICIENT_EVIDENCE")
        flags.append(
            _risk_flag(
                category="MISSING_DATA",
                as_of=request.as_of,
                evidence_refs=("score_records_empty",),
                provenance_refs=(request.scores.provenance.input_fingerprint,),
            )
        )

    # Conflicting evidence — approved: CONFLICTING_EVIDENCE + INSUFFICIENT_EVIDENCE (never ABSTAIN)
    conflicts: list[str] = []
    if request.scores is not None:
        for score in request.scores.records:
            if score.instrument_key not in membership_set:
                conflicts.append(f"score_outside_watchlist:{score.score_record_id}")
    for gap in usable_gaps:
        if gap.instrument_key not in membership_set:
            conflicts.append(f"gap_outside_watchlist:{gap.gap_record_id}")
    if conflicts:
        states.append("INSUFFICIENT_EVIDENCE")
        flags.append(
            _risk_flag(
                category="CONFLICTING_EVIDENCE",
                as_of=request.as_of,
                evidence_refs=tuple(sorted(conflicts)),
                provenance_refs=(request.watchlist.provenance.input_fingerprint,),
            )
        )

    # Upstream stage failure — both PROPAGATE identity and STAGE_FAILURE_PRESENT
    if request.upstream_pipeline_failure_identity is not None:
        markers["propagate_failure"] = True
        flags.append(
            _risk_flag(
                category="STAGE_FAILURE_PRESENT",
                as_of=request.as_of,
                evidence_refs=(f"upstream_failure:{request.upstream_pipeline_failure_identity}",),
                provenance_refs=(request.upstream_pipeline_failure_identity,),
            )
        )
        states.append("NOT_EVALUABLE")

    markers["stale_catalyst_ids"] = tuple(sorted(stale_ids))
    markers["usable_catalysts"] = tuple(usable_catalysts)
    markers["usable_gaps"] = tuple(usable_gaps)
    return tuple(states), tuple(flags), markers


def build_market_summary(
    request: ValidatedAnalystRequest,
    *,
    usable_gaps: tuple[GapRecord, ...],
    usable_catalysts: tuple[CatalystRecord, ...],
    catalyst_absence: bool,
) -> MarketSummary:
    membership = sort_membership_refs(
        tuple(entry.instrument_key for entry in request.watchlist.entries)
    )
    direction_up = sum(1 for gap in usable_gaps if gap.gap_direction == "up")
    direction_down = sum(1 for gap in usable_gaps if gap.gap_direction == "down")
    direction_flat = sum(1 for gap in usable_gaps if gap.gap_direction == "flat")
    gap_ids = tuple(sorted(gap.gap_record_id for gap in usable_gaps))
    gap_instruments = {gap.instrument_key for gap in usable_gaps}
    catalyst_ids = tuple(sorted(record.catalyst_record_id for record in usable_catalysts))
    linked = {record.instrument_key for record in usable_catalysts if record.instrument_key}

    score_ids: tuple[str, ...] = ()
    score_fp: str | None = None
    if request.scores is not None:
        score_ids = tuple(sorted(record.score_record_id for record in request.scores.records))
        score_fp = request.scores.provenance.input_fingerprint

    return MarketSummary(
        as_of=request.as_of,
        watchlist_count=len(membership),
        watchlist_membership_refs=membership,
        gap_coverage=GapCoverageAggregates(
            record_count=len(usable_gaps),
            instrument_count=len(gap_instruments),
            direction_up_count=direction_up,
            direction_down_count=direction_down,
            direction_flat_count=direction_flat,
            gap_record_ids=gap_ids,
        ),
        catalyst_coverage=CatalystCoverageAggregates(
            record_count=len(usable_catalysts),
            linked_instrument_count=len(linked),
            catalyst_record_ids=catalyst_ids,
            absence_marker=catalyst_absence,
        ),
        score_dashboard_refs=ScoreDashboardRefs(
            score_record_ids=score_ids,
            score_collection_input_fingerprint=score_fp,
            dashboard_output_id=(
                None if request.dashboard is None else request.dashboard.dashboard_output_id
            ),
            briefing_id=None if request.briefing is None else request.briefing.briefing_id,
        ),
        completeness=DataCompletenessMarkers(
            watchlist_present=True,
            gaps_present=request.gaps is not None,
            catalysts_present=request.catalysts is not None,
            scores_present=request.scores is not None,
            dashboard_present=request.dashboard is not None,
            briefing_present=request.briefing is not None,
            membership_complete=request.membership_complete,
        ),
    )


def build_catalyst_summary(
    request: ValidatedAnalystRequest,
    *,
    usable_catalysts: tuple[CatalystRecord, ...],
    absence_marker: bool,
    unavailable_marker: bool,
) -> CatalystSummary:
    records = sort_catalyst_summary_records(
        tuple(
            CatalystSummaryRecord(
                catalyst_record_id=record.catalyst_record_id,
                instrument_key=record.instrument_key,
                catalyst_type=record.catalyst_type,
                event_time=record.event_time,
                known_at=record.known_at,
                as_of=record.as_of,
                source_provider=record.source_provider,
                source_event_id=record.source_event_id,
                source_content_fingerprint=record.source_content_fingerprint,
                rule_id=record.rule_id,
            )
            for record in usable_catalysts
        )
    )
    return CatalystSummary(
        as_of=request.as_of,
        records=records,
        absence_marker=absence_marker,
        unavailable_marker=unavailable_marker,
    )


def build_theses(
    request: ValidatedAnalystRequest,
    *,
    usable_gaps: tuple[GapRecord, ...],
    usable_catalysts: tuple[CatalystRecord, ...],
    artifact_state: EvaluationState,
) -> tuple[StructuredThesis, ...]:
    gaps_by_instrument: dict[str, list[GapRecord]] = {}
    for gap in usable_gaps:
        gaps_by_instrument.setdefault(gap.instrument_key, []).append(gap)
    catalysts_by_instrument: dict[str, list[CatalystRecord]] = {}
    for catalyst in usable_catalysts:
        if catalyst.instrument_key:
            catalysts_by_instrument.setdefault(catalyst.instrument_key, []).append(catalyst)
    scores_by_instrument = {
        record.instrument_key: record
        for record in (request.scores.records if request.scores is not None else ())
    }

    theses: list[StructuredThesis] = []
    for entry in request.watchlist.entries:
        key = entry.instrument_key
        if key in request.unsupported_instrument_keys:
            thesis_state: EvaluationState = "NOT_EVALUABLE"
        else:
            thesis_state = artifact_state if artifact_state != "EVALUABLE" else "EVALUABLE"

        supporting: list[str] = [f"watchlist:{key}"]
        counter: list[str] = []
        conditions: list[str] = [f"watchlist_rank:{entry.rank}"]
        uncertainty: list[str] = []
        invalidation: list[str] = ["evidence_conditions_no_longer_satisfied"]

        if key in gaps_by_instrument:
            for gap in gaps_by_instrument[key]:
                supporting.append(f"gap:{gap.gap_record_id}")
                conditions.append(f"gap_direction:{gap.gap_direction}")
        else:
            uncertainty.append("missing_gap_evidence")
            counter.append("gap_evidence_absent")

        if key in scores_by_instrument:
            score = scores_by_instrument[key]
            supporting.append(f"score:{score.score_record_id}")
            conditions.append("score_ref_present")
        else:
            uncertainty.append("missing_score_ref")

        if key in catalysts_by_instrument:
            for catalyst in catalysts_by_instrument[key]:
                supporting.append(f"catalyst:{catalyst.catalyst_record_id}")
            conditions.append("catalyst_linked")
        else:
            uncertainty.append("catalyst_absence_for_instrument")
            invalidation.append("linked_catalyst_evidence_absent")

        if not request.membership_complete:
            uncertainty.append("partial_watchlist_membership")

        thesis_id = strategy_sha256(
            {
                "instrument_key": key,
                "as_of": request.as_of,
                "supporting": sorted(supporting),
                "definition": request.config.analyst_definition_version,
            }
        )
        theses.append(
            StructuredThesis(
                thesis_id=thesis_id,
                instrument_key=key,
                as_of=request.as_of,
                supporting_evidence_refs=tuple(sorted(supporting)),
                counter_evidence_refs=tuple(sorted(counter)),
                observed_conditions=tuple(sorted(conditions)),
                informational_invalidation_conditions=tuple(sorted(set(invalidation))),
                uncertainty_markers=tuple(sorted(set(uncertainty))),
                evaluation_state=thesis_state,
                provenance_refs=(request.watchlist.provenance.input_fingerprint,),
            )
        )
    return sort_theses(tuple(theses))


def assemble_projection(request: ValidatedAnalystRequest) -> PremarketAnalystArtifact:
    """Assemble artifact from validated upstream outputs only."""
    assert_ordering_policy(request.config.ordering_policy_id)
    states, flags, markers = collect_condition_states(request)
    evaluation_state = collapse_evaluation_states(states)
    usable_gaps = markers["usable_gaps"]
    usable_catalysts = markers["usable_catalysts"]
    assert isinstance(usable_gaps, tuple)
    assert isinstance(usable_catalysts, tuple)

    market_summary = build_market_summary(
        request,
        usable_gaps=usable_gaps,
        usable_catalysts=usable_catalysts,
        catalyst_absence=bool(markers["catalyst_absence"]),
    )
    catalyst_summary = build_catalyst_summary(
        request,
        usable_catalysts=usable_catalysts,
        absence_marker=bool(markers["catalyst_absence"]),
        unavailable_marker=bool(markers["catalyst_unavailable"]),
    )
    theses = build_theses(
        request,
        usable_gaps=usable_gaps,
        usable_catalysts=usable_catalysts,
        artifact_state=evaluation_state,
    )
    risk_flags = sort_risk_flags(flags)
    provenance = build_analyst_provenance(request)
    artifact_id = build_analyst_artifact_id(request)
    return PremarketAnalystArtifact(
        analyst_artifact_id=artifact_id,
        analyst_definition_version=request.config.analyst_definition_version,
        as_of=request.as_of,
        evaluation_state=evaluation_state,
        market_summary=market_summary,
        catalyst_summary=catalyst_summary,
        theses=theses,
        risk_flags=risk_flags,
        provenance=provenance,
    )


def _risk_flag(
    *,
    category: str,
    as_of: object,
    evidence_refs: tuple[str, ...],
    provenance_refs: tuple[str, ...],
) -> RiskFlag:
    from datetime import datetime

    if not isinstance(as_of, datetime):
        raise PremarketAnalystFailClosedError(detail="invalid_risk_flag_as_of")
    risk_flag_id = strategy_sha256(
        {
            "category": category,
            "as_of": as_of,
            "evidence_refs": list(evidence_refs),
            "provenance_refs": list(provenance_refs),
        }
    )
    return RiskFlag(
        risk_flag_id=risk_flag_id,
        category=category,  # type: ignore[arg-type]
        evidence_refs=evidence_refs,
        as_of=as_of,
        provenance_refs=provenance_refs,
    )


def require_no_engine_rerun_markers(request: ValidatedAnalystRequest) -> None:
    """Guardrail documentation helper — projection never calls upstream engines."""
    if request is None:
        raise PremarketAnalystValidationError(detail="missing_request")
