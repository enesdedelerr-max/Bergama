"""Unit tests for Human Review Foundation (Policy Version v1)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest
from app.dashboard.engine import assemble_dashboard_from_parts
from app.dashboard.models import (
    DashboardPresentationOutput,
    DashboardPresentationRecord,
    DashboardProvenance,
)
from app.human_review.engine import assemble_human_review, assemble_human_review_from_parts
from app.human_review.errors import (
    HumanReviewDomainError,
    HumanReviewHistoryError,
    HumanReviewHumanAuthorityError,
    HumanReviewIdentityError,
    HumanReviewOrderingError,
    HumanReviewPipelineIsolationError,
    HumanReviewPitConflictError,
    HumanReviewProvenanceError,
    HumanReviewReplayInequalityError,
    HumanReviewUnsupportedPolicyError,
    HumanReviewUpstreamPolicyError,
    HumanReviewValidationError,
)
from app.human_review.models import (
    HumanReviewConfig,
    HumanReviewRecordedAttestation,
    HumanReviewRequest,
)
from app.human_review.pipeline import run_human_review_pipeline
from app.human_review.policy import (
    DIGEST_METHOD_V1,
    HISTORY_SPECIFICATION_V1,
    HUMAN_ATTESTATION_POLICY_V1,
    IDENTITY_SPECIFICATION_V1,
    ORDERING_PRESERVATION_POLICY_V1,
    POLICY_VERSION_V1,
    PRESENTATION_PRESERVATION_POLICY_V1,
    PROVENANCE_SPECIFICATION_V1,
    REQUIRED_UPSTREAM_DASHBOARD_POLICY_VERSION_ID,
)
from app.human_review.replay import assert_replay_equal, reassemble
from app.human_review.validate_input import validate_human_review_request
from app.human_review.validate_output import validate_human_review_output
from app.premarket.morning_briefing import BriefingCollection, assemble_briefing_from_parts
from app.premarket.scoring.engine import scan_scores
from app.premarket.scoring.models import (
    ScoreCollection,
    ScoreComponents,
    ScoreConfig,
    ScoreProvenance,
    ScoreRecord,
    ScoreRequest,
)
from app.premarket.scoring.policy import POLICY_VERSION_V1 as SCORING_POLICY_VERSION_V1
from app.premarket.scoring.policy import WEIGHT_PROFILE_DEFAULT_V1
from app.premarket.watchlist.models import Watchlist, WatchlistEntry, WatchlistProvenance
from app.strategy.keys import strategy_sha256
from pydantic import ValidationError

AS_OF = datetime(2026, 7, 17, 14, 0, 0, tzinfo=UTC)
HEX_A = "a" * 64
HEX_B = "b" * 64
HEX_C = "c" * 64
HEX_D = "d" * 64
ATTESTATION = "recorded-human-authority-v1"


def _watchlist(*keys: tuple[str, str | None]) -> Watchlist:
    entries = tuple(
        WatchlistEntry(
            instrument_key=key,
            local_symbol=symbol,
            evaluation_timestamp=AS_OF,
            rank=index + 1,
            inclusion_reason="core",
            rule_id="allowlist",
        )
        for index, (key, symbol) in enumerate(keys)
    )
    return Watchlist(
        evaluation_timestamp=AS_OF,
        entries=entries,
        provenance=WatchlistProvenance(
            config_fingerprint=HEX_A,
            input_fingerprint=HEX_B,
            ordering_policy_id="rule_priority_asc_instrument_key_asc",
            source_identifiers=tuple(entry.instrument_key for entry in entries),
        ),
    )


def _score_collection(*keys: tuple[str, str | None]) -> ScoreCollection:
    return scan_scores(
        ScoreRequest(
            watchlist=_watchlist(*keys),
            as_of=AS_OF,
            config=ScoreConfig(),
        )
    )


def _briefing(*keys: tuple[str, str | None]) -> BriefingCollection:
    return assemble_briefing_from_parts(scores=_score_collection(*keys), as_of=AS_OF)


def _dashboard(*keys: tuple[str, str | None]) -> DashboardPresentationOutput:
    return assemble_dashboard_from_parts(briefing=_briefing(*keys), as_of=AS_OF)


def _manual_score_record(
    *,
    score_record_id: str,
    instrument_key: str,
    score: Decimal,
    local_symbol: str | None = "AAPL",
    components: ScoreComponents | None = None,
) -> ScoreRecord:
    return ScoreRecord.model_construct(
        score_record_id=score_record_id,
        instrument_key=instrument_key,
        local_symbol=local_symbol,
        score=score,
        components=components
        or ScoreComponents(
            watchlist_rank=Decimal("1"),
            gap_magnitude=None,
            catalyst_presence=None,
        ),
        policy_version_id=SCORING_POLICY_VERSION_V1,
        weight_profile_id=WEIGHT_PROFILE_DEFAULT_V1,
        as_of=AS_OF,
        watchlist_rank=1,
        watchlist_rule_id="allowlist",
        gap_record_id=None,
        catalyst_source_identifiers=(),
    )


def _manual_score_collection(records: tuple[ScoreRecord, ...]) -> ScoreCollection:
    return ScoreCollection.model_construct(
        as_of=AS_OF,
        records=records,
        provenance=ScoreProvenance.model_construct(
            config_fingerprint=HEX_A,
            input_fingerprint=HEX_B,
            ordering_policy_id="score_desc_instrument_key_asc_id_asc",
            policy_version_id=SCORING_POLICY_VERSION_V1,
            weight_profile_id=WEIGHT_PROFILE_DEFAULT_V1,
            source_identifiers=tuple(record.score_record_id for record in records),
        ),
    )


def _dashboard_from_manual_scores(
    records: tuple[ScoreRecord, ...],
) -> DashboardPresentationOutput:
    briefing = assemble_briefing_from_parts(scores=_manual_score_collection(records), as_of=AS_OF)
    return assemble_dashboard_from_parts(briefing=briefing, as_of=AS_OF)


def _construct_dashboard_record(
    base: DashboardPresentationRecord, **updates: object
) -> DashboardPresentationRecord:
    return base.model_copy(update=updates)


def _construct_dashboard(
    base: DashboardPresentationOutput, **updates: object
) -> DashboardPresentationOutput:
    payload = base.model_dump()
    payload.update(updates)
    if "provenance" in updates and isinstance(updates["provenance"], DashboardProvenance):
        payload["provenance"] = updates["provenance"]
    elif "provenance" in updates and isinstance(updates["provenance"], dict):
        payload["provenance"] = DashboardProvenance.model_construct(**updates["provenance"])
    else:
        payload["provenance"] = DashboardProvenance.model_construct(**payload["provenance"])
    if "records" in updates:
        payload["records"] = updates["records"]
    else:
        payload["records"] = tuple(
            DashboardPresentationRecord.model_construct(**record)
            if isinstance(record, dict)
            else record
            for record in payload["records"]
        )
    return DashboardPresentationOutput.model_construct(**payload)


def _independent_expected_human_review_id(
    dashboard: DashboardPresentationOutput,
    as_of: datetime,
    attestation: str,
) -> str:
    """Golden oracle: build identity payload without production identity helpers."""
    payload = {
        "schema": IDENTITY_SPECIFICATION_V1,
        "policy_version_id": POLICY_VERSION_V1,
        "ordering_preservation_policy_id": ORDERING_PRESERVATION_POLICY_V1,
        "presentation_preservation_policy_id": PRESENTATION_PRESERVATION_POLICY_V1,
        "human_attestation_policy_id": HUMAN_ATTESTATION_POLICY_V1,
        "provenance_specification_id": PROVENANCE_SPECIFICATION_V1,
        "history_specification_id": HISTORY_SPECIFICATION_V1,
        "as_of": as_of,
        "configuration": {
            "policy_version_id": POLICY_VERSION_V1,
            "ordering_preservation_policy_id": ORDERING_PRESERVATION_POLICY_V1,
            "presentation_preservation_policy_id": PRESENTATION_PRESERVATION_POLICY_V1,
            "human_attestation_policy_id": HUMAN_ATTESTATION_POLICY_V1,
            "identity_specification_id": IDENTITY_SPECIFICATION_V1,
            "provenance_specification_id": PROVENANCE_SPECIFICATION_V1,
            "history_specification_id": HISTORY_SPECIFICATION_V1,
            "digest_method_id": DIGEST_METHOD_V1,
        },
        "ordered_score_record_ids": [record.score_record_id for record in dashboard.records],
        "upstream_dashboard_output_id": dashboard.dashboard_output_id,
        "upstream_dashboard_provenance": dashboard.provenance.model_dump(mode="python"),
        "recorded_attestation_fingerprint": strategy_sha256({"recorded_payload": attestation}),
    }
    assert set(payload) == {
        "schema",
        "policy_version_id",
        "ordering_preservation_policy_id",
        "presentation_preservation_policy_id",
        "human_attestation_policy_id",
        "provenance_specification_id",
        "history_specification_id",
        "as_of",
        "configuration",
        "ordered_score_record_ids",
        "upstream_dashboard_output_id",
        "upstream_dashboard_provenance",
        "recorded_attestation_fingerprint",
    }
    return strategy_sha256(payload)


def test_empty_dashboard() -> None:
    dashboard = _dashboard()
    result = assemble_human_review_from_parts(
        dashboard=dashboard, as_of=AS_OF, attestation=ATTESTATION
    )
    assert result.records == ()
    assert result.policy_version_id == POLICY_VERSION_V1
    assert result.ordering_preservation_policy_id == ORDERING_PRESERVATION_POLICY_V1
    assert result.presentation_preservation_policy_id == PRESENTATION_PRESERVATION_POLICY_V1
    assert result.human_attestation_policy_id == HUMAN_ATTESTATION_POLICY_V1
    assert len(result.human_review_output_id) == 64
    assert result.provenance.source_identifiers == ()
    assert result.dashboard_output_id == dashboard.dashboard_output_id
    assert result.attestation.recorded_payload == ATTESTATION
    assert result.history.human_review_output_id == result.human_review_output_id
    assert result.history.upstream_dashboard_output_id == dashboard.dashboard_output_id


def test_valid_recorded_attestation_is_bound() -> None:
    dashboard = _dashboard(("bergama:equity:us:aapl", "AAPL"))
    result = assemble_human_review_from_parts(
        dashboard=dashboard, as_of=AS_OF, attestation=ATTESTATION
    )
    assert result.attestation.recorded_payload == ATTESTATION
    assert result.provenance.recorded_attestation_fingerprint == strategy_sha256(
        {"recorded_payload": ATTESTATION}
    )
    assert result.history.recorded_attestation_fingerprint == (
        result.provenance.recorded_attestation_fingerprint
    )


def test_absent_attestation_fail_closed() -> None:
    dashboard = _dashboard(("bergama:equity:us:aapl", "AAPL"))
    with pytest.raises(ValidationError):
        HumanReviewRequest(dashboard=dashboard, as_of=AS_OF, config=HumanReviewConfig())


def test_empty_attestation_fail_closed() -> None:
    dashboard = _dashboard(("bergama:equity:us:aapl", "AAPL"))
    with pytest.raises((HumanReviewValidationError, ValidationError)):
        assemble_human_review_from_parts(dashboard=dashboard, as_of=AS_OF, attestation="")
    with pytest.raises((HumanReviewValidationError, ValidationError)):
        assemble_human_review_from_parts(dashboard=dashboard, as_of=AS_OF, attestation="   ")


def test_attestation_derived_from_dashboard_fail_closed() -> None:
    dashboard = _dashboard(("bergama:equity:us:aapl", "AAPL"))
    with pytest.raises(HumanReviewHumanAuthorityError) as exc_info:
        assemble_human_review_from_parts(
            dashboard=dashboard,
            as_of=AS_OF,
            attestation=dashboard.dashboard_output_id,
        )
    assert exc_info.value.detail == "attestation_derived_from_dashboard"
    with pytest.raises(HumanReviewHumanAuthorityError):
        assemble_human_review_from_parts(
            dashboard=dashboard,
            as_of=AS_OF,
            attestation=dashboard.records[0].score_record_id,
        )


def test_one_record_preserves_public_fields() -> None:
    dashboard = _dashboard(("bergama:equity:us:aapl", "AAPL"))
    result = assemble_human_review(
        HumanReviewRequest(
            dashboard=dashboard,
            as_of=AS_OF,
            config=HumanReviewConfig(),
            attestation=HumanReviewRecordedAttestation(recorded_payload=ATTESTATION),
        )
    )
    assert len(result.records) == 1
    record = result.records[0]
    upstream = dashboard.records[0]
    assert record.sequence_index == 0
    assert record.score_record_id == upstream.score_record_id
    assert record.instrument_key == upstream.instrument_key
    assert record.local_symbol == upstream.local_symbol
    assert record.score == upstream.score
    assert record.components == upstream.components
    assert record.dashboard_policy_version_id == REQUIRED_UPSTREAM_DASHBOARD_POLICY_VERSION_ID
    assert record.scoring_as_of == upstream.scoring_as_of


def test_many_records_preserve_exact_order() -> None:
    dashboard = _dashboard(
        ("bergama:equity:us:aapl", "AAPL"),
        ("bergama:equity:us:msft", "MSFT"),
        ("bergama:equity:us:nvda", "NVDA"),
    )
    result = assemble_human_review_from_parts(
        dashboard=dashboard, as_of=AS_OF, attestation=ATTESTATION
    )
    assert len(result.records) == 3
    for index, (review_record, dashboard_record) in enumerate(
        zip(result.records, dashboard.records, strict=True)
    ):
        assert review_record.sequence_index == index
        assert review_record.score_record_id == dashboard_record.score_record_id
        assert review_record.instrument_key == dashboard_record.instrument_key
        assert review_record.score == dashboard_record.score
    assert result.provenance.source_identifiers == tuple(
        record.score_record_id for record in dashboard.records
    )


def test_equal_scores_do_not_rerank() -> None:
    dashboard = _dashboard_from_manual_scores(
        (
            _manual_score_record(
                score_record_id=HEX_C,
                instrument_key="bergama:equity:us:msft",
                score=Decimal("0.5"),
                local_symbol="MSFT",
            ),
            _manual_score_record(
                score_record_id=HEX_D,
                instrument_key="bergama:equity:us:aapl",
                score=Decimal("0.5"),
                local_symbol="AAPL",
            ),
        )
    )
    result = assemble_human_review_from_parts(
        dashboard=dashboard, as_of=AS_OF, attestation=ATTESTATION
    )
    assert [record.instrument_key for record in result.records] == [
        "bergama:equity:us:msft",
        "bergama:equity:us:aapl",
    ]
    assert [record.sequence_index for record in result.records] == [0, 1]


def test_reversed_upstream_order_preserved_exactly() -> None:
    forward = _dashboard(
        ("bergama:equity:us:aapl", "AAPL"),
        ("bergama:equity:us:msft", "MSFT"),
    )
    reversed_records = tuple(reversed(forward.records))
    reversed_dashboard = _construct_dashboard(
        forward,
        records=reversed_records,
        dashboard_output_id=HEX_A,
        provenance=forward.provenance.model_copy(
            update={
                "source_identifiers": tuple(record.score_record_id for record in reversed_records)
            }
        ),
    )
    result = assemble_human_review_from_parts(
        dashboard=reversed_dashboard, as_of=AS_OF, attestation=ATTESTATION
    )
    assert [record.score_record_id for record in result.records] == [
        record.score_record_id for record in reversed_dashboard.records
    ]
    forward_result = assemble_human_review_from_parts(
        dashboard=forward, as_of=AS_OF, attestation=ATTESTATION
    )
    assert result.provenance.source_identifiers != forward_result.provenance.source_identifiers
    assert result.human_review_output_id != forward_result.human_review_output_id


def test_duplicate_upstream_identity_fail_closed() -> None:
    dashboard = _dashboard(("bergama:equity:us:aapl", "AAPL"))
    duplicate = _construct_dashboard_record(
        dashboard.records[0], instrument_key="bergama:equity:us:msft"
    )
    bad = _construct_dashboard(dashboard, records=(dashboard.records[0], duplicate))
    with pytest.raises(HumanReviewIdentityError) as exc_info:
        assemble_human_review_from_parts(dashboard=bad, as_of=AS_OF, attestation=ATTESTATION)
    assert exc_info.value.detail is not None
    assert "duplicate_score_record_id" in exc_info.value.detail


def test_null_local_symbol_and_optional_components_preserved() -> None:
    dashboard = _dashboard_from_manual_scores(
        (
            _manual_score_record(
                score_record_id=HEX_C,
                instrument_key="bergama:equity:us:aapl",
                score=Decimal("0.25"),
                local_symbol=None,
                components=ScoreComponents(
                    watchlist_rank=Decimal("1"),
                    gap_magnitude=None,
                    catalyst_presence=None,
                ),
            ),
        )
    )
    result = assemble_human_review_from_parts(
        dashboard=dashboard, as_of=AS_OF, attestation=ATTESTATION
    )
    assert result.records[0].local_symbol is None
    assert result.records[0].components.gap_magnitude is None
    assert result.records[0].components.catalyst_presence is None


def test_score_domain_boundaries_negative_zero_and_non_finite() -> None:
    for valid in (Decimal("0"), Decimal("1")):
        dashboard = _dashboard_from_manual_scores(
            (
                _manual_score_record(
                    score_record_id=HEX_C,
                    instrument_key="bergama:equity:us:aapl",
                    score=valid,
                ),
            )
        )
        result = assemble_human_review_from_parts(
            dashboard=dashboard, as_of=AS_OF, attestation=ATTESTATION
        )
        assert result.records[0].score == valid

    negative_zero_dashboard = _dashboard_from_manual_scores(
        (
            _manual_score_record(
                score_record_id=HEX_C,
                instrument_key="bergama:equity:us:aapl",
                score=Decimal("-0"),
            ),
        )
    )
    injected = _construct_dashboard_record(negative_zero_dashboard.records[0], score=Decimal("-0"))
    injected_dashboard = _construct_dashboard(negative_zero_dashboard, records=(injected,))
    zeroed = assemble_human_review_from_parts(
        dashboard=injected_dashboard, as_of=AS_OF, attestation=ATTESTATION
    )
    assert zeroed.records[0].score == Decimal("0")
    assert zeroed.records[0].score.is_zero()
    assert format(zeroed.records[0].score, "f") == "0"
    replayed_zero = assemble_human_review_from_parts(
        dashboard=injected_dashboard,
        as_of=AS_OF,
        attestation=ATTESTATION,
    )
    assert replayed_zero.human_review_output_id == zeroed.human_review_output_id

    base = _dashboard(("bergama:equity:us:aapl", "AAPL"))
    for invalid in (
        Decimal("NaN"),
        Decimal("Infinity"),
        Decimal("-Infinity"),
        Decimal("-0.1"),
        Decimal("1.5"),
    ):
        bad_record = _construct_dashboard_record(base.records[0], score=invalid)
        bad = _construct_dashboard(base, records=(bad_record,))
        with pytest.raises(HumanReviewDomainError):
            assemble_human_review_from_parts(dashboard=bad, as_of=AS_OF, attestation=ATTESTATION)


def test_naive_as_of_rejected() -> None:
    dashboard = _dashboard(("bergama:equity:us:aapl", "AAPL"))
    with pytest.raises((HumanReviewValidationError, ValidationError)):
        assemble_human_review_from_parts(
            dashboard=dashboard,
            as_of=datetime(2026, 7, 17, 14, 0, 0),
            attestation=ATTESTATION,
        )


def test_utc_as_of_accepted() -> None:
    dashboard = _dashboard(("bergama:equity:us:aapl", "AAPL"))
    result = assemble_human_review_from_parts(
        dashboard=dashboard, as_of=AS_OF, attestation=ATTESTATION
    )
    assert result.as_of == AS_OF


def test_fixed_offset_as_of_accepted_when_instant_matches() -> None:
    offset = timezone(timedelta(hours=-4))
    as_of = datetime(2026, 7, 17, 10, 0, 0, tzinfo=offset)
    watchlist = Watchlist(
        evaluation_timestamp=as_of,
        entries=(
            WatchlistEntry(
                instrument_key="bergama:equity:us:aapl",
                local_symbol="AAPL",
                evaluation_timestamp=as_of,
                rank=1,
                inclusion_reason="core",
                rule_id="allowlist",
            ),
        ),
        provenance=WatchlistProvenance(
            config_fingerprint=HEX_A,
            input_fingerprint=HEX_B,
            ordering_policy_id="rule_priority_asc_instrument_key_asc",
            source_identifiers=("bergama:equity:us:aapl",),
        ),
    )
    scores = scan_scores(ScoreRequest(watchlist=watchlist, as_of=as_of, config=ScoreConfig()))
    briefing = assemble_briefing_from_parts(scores=scores, as_of=as_of)
    dashboard = assemble_dashboard_from_parts(briefing=briefing, as_of=as_of)
    result = assemble_human_review_from_parts(
        dashboard=dashboard, as_of=as_of, attestation=ATTESTATION
    )
    assert result.as_of == dashboard.as_of


def test_cross_as_of_mismatch_fail_closed() -> None:
    dashboard = _dashboard(("bergama:equity:us:aapl", "AAPL"))
    other_as_of = AS_OF + timedelta(minutes=1)
    with pytest.raises(HumanReviewPitConflictError) as exc_info:
        assemble_human_review_from_parts(
            dashboard=dashboard, as_of=other_as_of, attestation=ATTESTATION
        )
    assert exc_info.value.detail is not None
    assert "cross_as_of" in exc_info.value.detail


def test_wrong_human_review_policy_fail_closed() -> None:
    with pytest.raises(ValidationError):
        HumanReviewConfig(policy_version_id="human-review.policy.v2")


def test_wrong_subordinate_human_review_config_id_fail_closed() -> None:
    with pytest.raises(ValidationError):
        HumanReviewConfig(identity_specification_id="human-review.identity.v2")
    with pytest.raises(ValidationError):
        HumanReviewConfig(presentation_preservation_policy_id="include_some.v1")
    with pytest.raises(ValidationError):
        HumanReviewConfig(history_specification_id="human-review.history.v2")


def test_wrong_dashboard_policy_fail_closed() -> None:
    dashboard = _dashboard(("bergama:equity:us:aapl", "AAPL"))
    bad = _construct_dashboard(dashboard, policy_version_id="dashboard.policy.v2")
    with pytest.raises(HumanReviewUpstreamPolicyError):
        assemble_human_review_from_parts(dashboard=bad, as_of=AS_OF, attestation=ATTESTATION)


def test_malformed_upstream_identity_fail_closed() -> None:
    dashboard = _dashboard(("bergama:equity:us:aapl", "AAPL"))
    bad_id = _construct_dashboard(dashboard, dashboard_output_id="not-a-digest")
    with pytest.raises(HumanReviewIdentityError):
        assemble_human_review_from_parts(dashboard=bad_id, as_of=AS_OF, attestation=ATTESTATION)
    bad_record = _construct_dashboard_record(dashboard.records[0], score_record_id="short")
    bad_records = _construct_dashboard(dashboard, records=(bad_record,))
    with pytest.raises(HumanReviewIdentityError):
        assemble_human_review_from_parts(
            dashboard=bad_records, as_of=AS_OF, attestation=ATTESTATION
        )


def test_malformed_missing_provenance_fail_closed() -> None:
    dashboard = _dashboard(("bergama:equity:us:aapl", "AAPL"))
    bad_provenance = DashboardProvenance.model_construct(
        **{
            **dashboard.provenance.model_dump(),
            "config_fingerprint": "",
        }
    )
    bad = _construct_dashboard(dashboard, provenance=bad_provenance)
    with pytest.raises(HumanReviewProvenanceError):
        assemble_human_review_from_parts(dashboard=bad, as_of=AS_OF, attestation=ATTESTATION)


def test_ordering_mismatch_fail_closed() -> None:
    dashboard = _dashboard(
        ("bergama:equity:us:aapl", "AAPL"),
        ("bergama:equity:us:msft", "MSFT"),
    )
    request = HumanReviewRequest(
        dashboard=dashboard,
        as_of=AS_OF,
        config=HumanReviewConfig(),
        attestation=HumanReviewRecordedAttestation(recorded_payload=ATTESTATION),
    )
    validated = validate_human_review_request(request)
    output = assemble_human_review(request)
    tampered_records = (
        output.records[0].model_copy(update={"sequence_index": 1}),
        output.records[1],
    )
    tampered = output.model_copy(update={"records": tampered_records})
    with pytest.raises(HumanReviewOrderingError):
        validate_human_review_output(tampered, request=validated)


def test_identity_mismatch_fail_closed() -> None:
    dashboard = _dashboard(("bergama:equity:us:aapl", "AAPL"))
    request = HumanReviewRequest(
        dashboard=dashboard,
        as_of=AS_OF,
        config=HumanReviewConfig(),
        attestation=HumanReviewRecordedAttestation(recorded_payload=ATTESTATION),
    )
    validated = validate_human_review_request(request)
    output = assemble_human_review(request)
    tampered = output.model_copy(update={"human_review_output_id": HEX_A})
    with pytest.raises(HumanReviewIdentityError):
        validate_human_review_output(tampered, request=validated)


def test_provenance_mismatch_fail_closed() -> None:
    dashboard = _dashboard(("bergama:equity:us:aapl", "AAPL"))
    request = HumanReviewRequest(
        dashboard=dashboard,
        as_of=AS_OF,
        config=HumanReviewConfig(),
        attestation=HumanReviewRecordedAttestation(recorded_payload=ATTESTATION),
    )
    validated = validate_human_review_request(request)
    output = assemble_human_review(request)
    tampered_provenance = output.provenance.model_copy(update={"config_fingerprint": HEX_B})
    tampered = output.model_copy(update={"provenance": tampered_provenance})
    with pytest.raises(HumanReviewProvenanceError):
        validate_human_review_output(tampered, request=validated)


def test_history_mismatch_fail_closed() -> None:
    dashboard = _dashboard(("bergama:equity:us:aapl", "AAPL"))
    request = HumanReviewRequest(
        dashboard=dashboard,
        as_of=AS_OF,
        config=HumanReviewConfig(),
        attestation=HumanReviewRecordedAttestation(recorded_payload=ATTESTATION),
    )
    validated = validate_human_review_request(request)
    output = assemble_human_review(request)
    tampered_history = output.history.model_copy(update={"provenance_config_fingerprint": HEX_B})
    tampered = output.model_copy(update={"history": tampered_history})
    with pytest.raises(HumanReviewHistoryError):
        validate_human_review_output(tampered, request=validated)


def test_config_and_output_immutability() -> None:
    dashboard = _dashboard(("bergama:equity:us:aapl", "AAPL"))
    config = HumanReviewConfig()
    result = assemble_human_review_from_parts(
        dashboard=dashboard, as_of=AS_OF, attestation=ATTESTATION, config=config
    )
    with pytest.raises(ValidationError):
        config.policy_version_id = "human-review.policy.v2"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        result.human_review_output_id = HEX_A  # type: ignore[misc]
    with pytest.raises(ValidationError):
        result.records[0].score = result.records[0].score  # type: ignore[misc]


def test_unexpected_extra_fields_fail_closed() -> None:
    dashboard = _dashboard(("bergama:equity:us:aapl", "AAPL"))
    with pytest.raises(ValidationError):
        HumanReviewRequest(
            dashboard=dashboard,
            as_of=AS_OF,
            config=HumanReviewConfig(),
            attestation=HumanReviewRecordedAttestation(recorded_payload=ATTESTATION),
            unauthorized_field="nope",  # type: ignore[call-arg]
        )
    with pytest.raises(ValidationError):
        HumanReviewRequest(
            dashboard=dashboard,
            as_of=AS_OF,
            config=HumanReviewConfig(),
            attestation=HumanReviewRecordedAttestation(recorded_payload=ATTESTATION),
            briefing=_briefing(("bergama:equity:us:aapl", "AAPL")),  # type: ignore[call-arg]
        )
    with pytest.raises(ValidationError):
        HumanReviewRecordedAttestation(recorded_payload=ATTESTATION, outcome="approved")  # type: ignore[call-arg]


def test_pipeline_isolation_requires_validated_request() -> None:
    dashboard = _dashboard(("bergama:equity:us:aapl", "AAPL"))
    raw = HumanReviewRequest(
        dashboard=dashboard,
        as_of=AS_OF,
        config=HumanReviewConfig(),
        attestation=HumanReviewRecordedAttestation(recorded_payload=ATTESTATION),
    )
    with pytest.raises(HumanReviewPipelineIsolationError):
        run_human_review_pipeline(raw)  # type: ignore[arg-type]


def test_output_completeness_exactly_one_output() -> None:
    dashboard = _dashboard(("bergama:equity:us:aapl", "AAPL"))
    result = assemble_human_review_from_parts(
        dashboard=dashboard, as_of=AS_OF, attestation=ATTESTATION
    )
    assert result.__class__.__name__ == "HumanReviewOutput"
    assert isinstance(result.records, tuple)
    assert result.provenance is not None
    assert result.history is not None
    assert result.human_review_output_id


def test_golden_identity_oracle_and_sensitivity() -> None:
    dashboard = _dashboard(
        ("bergama:equity:us:aapl", "AAPL"),
        ("bergama:equity:us:msft", "MSFT"),
    )
    expected = _independent_expected_human_review_id(dashboard, AS_OF, ATTESTATION)
    result = assemble_human_review_from_parts(
        dashboard=dashboard, as_of=AS_OF, attestation=ATTESTATION
    )
    assert result.human_review_output_id == expected
    assert result.human_review_output_id != dashboard.dashboard_output_id
    assert result.human_review_output_id != dashboard.provenance.upstream_briefing_id
    assert result.human_review_output_id != dashboard.records[0].score_record_id

    sensitive = _dashboard(("bergama:equity:us:aapl", "AAPL"))
    assert _independent_expected_human_review_id(sensitive, AS_OF, ATTESTATION) != expected
    sensitive_result = assemble_human_review_from_parts(
        dashboard=sensitive, as_of=AS_OF, attestation=ATTESTATION
    )
    assert sensitive_result.human_review_output_id != result.human_review_output_id

    other_attestation = assemble_human_review_from_parts(
        dashboard=dashboard, as_of=AS_OF, attestation="other-recorded-human-authority-v1"
    )
    assert other_attestation.human_review_output_id != result.human_review_output_id


def test_deterministic_provenance_history_and_sensitivity() -> None:
    dashboard = _dashboard(("bergama:equity:us:aapl", "AAPL"))
    request = HumanReviewRequest(
        dashboard=dashboard,
        as_of=AS_OF,
        config=HumanReviewConfig(),
        attestation=HumanReviewRecordedAttestation(recorded_payload=ATTESTATION),
    )
    first = assemble_human_review(request)
    second = assemble_human_review(request)
    assert first.provenance == second.provenance
    assert first.history == second.history
    assert first.provenance.config_fingerprint == second.provenance.config_fingerprint
    assert first.provenance.input_fingerprint == second.provenance.input_fingerprint
    other = assemble_human_review_from_parts(
        dashboard=_dashboard(
            ("bergama:equity:us:aapl", "AAPL"),
            ("bergama:equity:us:msft", "MSFT"),
        ),
        as_of=AS_OF,
        attestation=ATTESTATION,
    )
    assert first.provenance.input_fingerprint != other.provenance.input_fingerprint
    assert first.human_review_output_id != other.human_review_output_id
    assert first.history != other.history


def test_replay_equality() -> None:
    dashboard = _dashboard(("bergama:equity:us:aapl", "AAPL"))
    request = HumanReviewRequest(
        dashboard=dashboard,
        as_of=AS_OF,
        config=HumanReviewConfig(),
        attestation=HumanReviewRecordedAttestation(recorded_payload=ATTESTATION),
    )
    first = assemble_human_review(request)
    second = reassemble(request)
    assert_replay_equal(first, second)
    assert first.human_review_output_id == second.human_review_output_id
    assert first.provenance == second.provenance
    assert first.history == second.history
    assert first.attestation == second.attestation


def test_replay_inequality_fail_closed() -> None:
    first = assemble_human_review_from_parts(
        dashboard=_dashboard(("bergama:equity:us:aapl", "AAPL")),
        as_of=AS_OF,
        attestation=ATTESTATION,
    )
    second = assemble_human_review_from_parts(
        dashboard=_dashboard(
            ("bergama:equity:us:aapl", "AAPL"),
            ("bergama:equity:us:msft", "MSFT"),
        ),
        as_of=AS_OF,
        attestation=ATTESTATION,
    )
    with pytest.raises(HumanReviewReplayInequalityError) as exc_info:
        assert_replay_equal(first, second)
    assert exc_info.value.detail == "replay_inequality"


def test_default_configuration_constants() -> None:
    config = HumanReviewConfig()
    assert config.policy_version_id == POLICY_VERSION_V1
    assert config.ordering_preservation_policy_id == ORDERING_PRESERVATION_POLICY_V1
    assert config.presentation_preservation_policy_id == PRESENTATION_PRESERVATION_POLICY_V1
    assert config.human_attestation_policy_id == HUMAN_ATTESTATION_POLICY_V1
    assert config.identity_specification_id == IDENTITY_SPECIFICATION_V1
    assert config.provenance_specification_id == PROVENANCE_SPECIFICATION_V1
    assert config.history_specification_id == HISTORY_SPECIFICATION_V1
    assert config.digest_method_id == DIGEST_METHOD_V1


def test_no_float_wall_clock_random_uuid_or_forbidden_imports_in_human_review_sources() -> None:
    root = Path(__file__).resolve().parents[2] / "app" / "human_review"
    forbidden = (
        "datetime.now(",
        "datetime.utcnow(",
        "time.time(",
        "uuid4(",
        "uuid.",
        "random.",
        "float(",
        "app.premarket.scoring",
        "app.premarket.morning_briefing",
        "app.features.",
    )
    for path in root.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, f"{path.name} contains {token}"


def test_coerce_invalid_request_fail_closed() -> None:
    with pytest.raises(HumanReviewValidationError):
        assemble_human_review({"dashboard": "not-a-dashboard"})


def test_unsupported_digest_on_validated_path_fail_closed() -> None:
    dashboard = _dashboard(("bergama:equity:us:aapl", "AAPL"))
    config = HumanReviewConfig.model_construct(
        policy_version_id=POLICY_VERSION_V1,
        ordering_preservation_policy_id=ORDERING_PRESERVATION_POLICY_V1,
        presentation_preservation_policy_id=PRESENTATION_PRESERVATION_POLICY_V1,
        human_attestation_policy_id=HUMAN_ATTESTATION_POLICY_V1,
        identity_specification_id=IDENTITY_SPECIFICATION_V1,
        provenance_specification_id=PROVENANCE_SPECIFICATION_V1,
        history_specification_id=HISTORY_SPECIFICATION_V1,
        digest_method_id="md5",
    )
    request = HumanReviewRequest.model_construct(
        dashboard=dashboard,
        as_of=AS_OF,
        config=config,
        attestation=HumanReviewRecordedAttestation(recorded_payload=ATTESTATION),
    )
    with pytest.raises(HumanReviewUnsupportedPolicyError):
        assemble_human_review(request)
