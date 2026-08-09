"""Unit tests for Dashboard Foundation (Policy Version v1)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest
from app.dashboard.engine import assemble_dashboard, assemble_dashboard_from_parts
from app.dashboard.errors import (
    DashboardDomainError,
    DashboardIdentityError,
    DashboardOrderingError,
    DashboardPipelineIsolationError,
    DashboardPitConflictError,
    DashboardProvenanceError,
    DashboardReplayInequalityError,
    DashboardUnsupportedPolicyError,
    DashboardUpstreamPolicyError,
    DashboardValidationError,
)
from app.dashboard.models import DashboardConfig, DashboardRequest
from app.dashboard.pipeline import run_dashboard_pipeline
from app.dashboard.policy import (
    DIGEST_METHOD_V1,
    IDENTITY_SPECIFICATION_V1,
    ORDERING_PRESERVATION_POLICY_V1,
    POLICY_VERSION_V1,
    PRESENTATION_SELECTION_POLICY_V1,
    PROVENANCE_SPECIFICATION_V1,
    REQUIRED_UPSTREAM_BRIEFING_POLICY_VERSION_ID,
)
from app.dashboard.replay import assert_replay_equal, reassemble
from app.dashboard.validate_input import validate_dashboard_request
from app.dashboard.validate_output import validate_dashboard_output
from app.premarket.morning_briefing import (
    BriefingCollection,
    BriefingProvenance,
    BriefingRecord,
    assemble_briefing_from_parts,
)
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


def _briefing_from_manual_scores(records: tuple[ScoreRecord, ...]) -> BriefingCollection:
    return assemble_briefing_from_parts(scores=_manual_score_collection(records), as_of=AS_OF)


def _construct_briefing_record(base: BriefingRecord, **updates: object) -> BriefingRecord:
    payload = base.model_dump()
    payload.update(updates)
    return BriefingRecord.model_construct(**payload)


def _construct_briefing(base: BriefingCollection, **updates: object) -> BriefingCollection:
    payload = base.model_dump()
    payload.update(updates)
    if "provenance" in updates and isinstance(updates["provenance"], BriefingProvenance):
        payload["provenance"] = updates["provenance"]
    elif "provenance" in updates and isinstance(updates["provenance"], dict):
        payload["provenance"] = BriefingProvenance.model_construct(**updates["provenance"])
    else:
        payload["provenance"] = BriefingProvenance.model_construct(**payload["provenance"])
    if "records" in updates:
        payload["records"] = updates["records"]
    else:
        payload["records"] = tuple(
            BriefingRecord.model_construct(**record) if isinstance(record, dict) else record
            for record in payload["records"]
        )
    return BriefingCollection.model_construct(**payload)


def _independent_expected_dashboard_id(
    briefing: BriefingCollection,
    as_of: datetime,
) -> str:
    """Golden oracle: build identity payload without production identity helpers."""
    payload = {
        "schema": IDENTITY_SPECIFICATION_V1,
        "policy_version_id": POLICY_VERSION_V1,
        "ordering_preservation_policy_id": ORDERING_PRESERVATION_POLICY_V1,
        "presentation_selection_policy_id": PRESENTATION_SELECTION_POLICY_V1,
        "provenance_specification_id": PROVENANCE_SPECIFICATION_V1,
        "as_of": as_of,
        "configuration": {
            "policy_version_id": POLICY_VERSION_V1,
            "ordering_preservation_policy_id": ORDERING_PRESERVATION_POLICY_V1,
            "identity_specification_id": IDENTITY_SPECIFICATION_V1,
            "provenance_specification_id": PROVENANCE_SPECIFICATION_V1,
            "digest_method_id": DIGEST_METHOD_V1,
            "presentation_selection_policy_id": PRESENTATION_SELECTION_POLICY_V1,
        },
        "ordered_score_record_ids": [record.score_record_id for record in briefing.records],
        "upstream_briefing_id": briefing.briefing_id,
        "upstream_briefing_provenance": briefing.provenance.model_dump(mode="python"),
    }
    assert set(payload) == {
        "schema",
        "policy_version_id",
        "ordering_preservation_policy_id",
        "presentation_selection_policy_id",
        "provenance_specification_id",
        "as_of",
        "configuration",
        "ordered_score_record_ids",
        "upstream_briefing_id",
        "upstream_briefing_provenance",
    }
    return strategy_sha256(payload)


def test_empty_morning_briefing() -> None:
    briefing = _briefing()
    result = assemble_dashboard_from_parts(briefing=briefing, as_of=AS_OF)
    assert result.records == ()
    assert result.policy_version_id == POLICY_VERSION_V1
    assert result.ordering_preservation_policy_id == ORDERING_PRESERVATION_POLICY_V1
    assert result.presentation_selection_policy_id == PRESENTATION_SELECTION_POLICY_V1
    assert len(result.dashboard_output_id) == 64
    assert result.provenance.source_identifiers == ()
    assert result.provenance.upstream_briefing_id == briefing.briefing_id


def test_one_record_preserves_public_fields() -> None:
    briefing = _briefing(("bergama:equity:us:aapl", "AAPL"))
    result = assemble_dashboard(
        DashboardRequest(briefing=briefing, as_of=AS_OF, config=DashboardConfig())
    )
    assert len(result.records) == 1
    record = result.records[0]
    upstream = briefing.records[0]
    assert record.sequence_index == 0
    assert record.score_record_id == upstream.score_record_id
    assert record.instrument_key == upstream.instrument_key
    assert record.local_symbol == upstream.local_symbol
    assert record.score == upstream.score
    assert record.components == upstream.components
    assert record.morning_briefing_policy_version_id == REQUIRED_UPSTREAM_BRIEFING_POLICY_VERSION_ID


def test_many_records_preserve_exact_order() -> None:
    briefing = _briefing(
        ("bergama:equity:us:aapl", "AAPL"),
        ("bergama:equity:us:msft", "MSFT"),
        ("bergama:equity:us:nvda", "NVDA"),
    )
    result = assemble_dashboard_from_parts(briefing=briefing, as_of=AS_OF)
    assert len(result.records) == 3
    for index, (dashboard_record, briefing_record) in enumerate(
        zip(result.records, briefing.records, strict=True)
    ):
        assert dashboard_record.sequence_index == index
        assert dashboard_record.score_record_id == briefing_record.score_record_id
        assert dashboard_record.instrument_key == briefing_record.instrument_key
        assert dashboard_record.score == briefing_record.score
    assert result.provenance.source_identifiers == tuple(
        record.score_record_id for record in briefing.records
    )


def test_equal_scores_do_not_rerank() -> None:
    briefing = _briefing_from_manual_scores(
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
    result = assemble_dashboard_from_parts(briefing=briefing, as_of=AS_OF)
    assert [record.instrument_key for record in result.records] == [
        "bergama:equity:us:msft",
        "bergama:equity:us:aapl",
    ]
    assert [record.sequence_index for record in result.records] == [0, 1]


def test_reversed_upstream_order_preserved_exactly() -> None:
    scores = _score_collection(
        ("bergama:equity:us:aapl", "AAPL"),
        ("bergama:equity:us:msft", "MSFT"),
    )
    forward_briefing = assemble_briefing_from_parts(scores=scores, as_of=AS_OF)
    reversed_records = tuple(reversed(scores.records))
    reversed_scores = ScoreCollection.model_construct(
        as_of=scores.as_of,
        records=reversed_records,
        provenance=scores.provenance.model_copy(
            update={
                "source_identifiers": tuple(record.score_record_id for record in reversed_records)
            }
        ),
    )
    reversed_briefing = assemble_briefing_from_parts(scores=reversed_scores, as_of=AS_OF)
    result = assemble_dashboard_from_parts(briefing=reversed_briefing, as_of=AS_OF)
    assert [record.score_record_id for record in result.records] == [
        record.score_record_id for record in reversed_briefing.records
    ]
    forward = assemble_dashboard_from_parts(briefing=forward_briefing, as_of=AS_OF)
    assert result.provenance.source_identifiers != forward.provenance.source_identifiers
    assert result.dashboard_output_id != forward.dashboard_output_id


def test_duplicate_upstream_identity_fail_closed() -> None:
    base = _briefing(("bergama:equity:us:aapl", "AAPL"))
    duplicate = _construct_briefing_record(base.records[0], instrument_key="bergama:equity:us:msft")
    bad = _construct_briefing(base, records=(base.records[0], duplicate))
    with pytest.raises(DashboardIdentityError) as exc_info:
        assemble_dashboard_from_parts(briefing=bad, as_of=AS_OF)
    assert exc_info.value.detail is not None
    assert "duplicate_score_record_id" in exc_info.value.detail


def test_null_local_symbol_and_optional_components_preserved() -> None:
    briefing = _briefing_from_manual_scores(
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
    result = assemble_dashboard_from_parts(briefing=briefing, as_of=AS_OF)
    assert result.records[0].local_symbol is None
    assert result.records[0].components.gap_magnitude is None
    assert result.records[0].components.catalyst_presence is None


def test_score_domain_boundaries_negative_zero_and_non_finite() -> None:
    for valid in (Decimal("0"), Decimal("1")):
        briefing = _briefing_from_manual_scores(
            (
                _manual_score_record(
                    score_record_id=HEX_C,
                    instrument_key="bergama:equity:us:aapl",
                    score=valid,
                ),
            )
        )
        result = assemble_dashboard_from_parts(briefing=briefing, as_of=AS_OF)
        assert result.records[0].score == valid

    negative_zero_briefing = _briefing_from_manual_scores(
        (
            _manual_score_record(
                score_record_id=HEX_C,
                instrument_key="bergama:equity:us:aapl",
                score=Decimal("-0"),
            ),
        )
    )
    zeroed = assemble_dashboard_from_parts(briefing=negative_zero_briefing, as_of=AS_OF)
    assert zeroed.records[0].score == Decimal("0")
    assert zeroed.records[0].score.is_zero()
    assert format(zeroed.records[0].score, "f") == "0"
    replayed_zero = assemble_dashboard_from_parts(
        briefing=negative_zero_briefing,
        as_of=AS_OF,
    )
    assert replayed_zero.dashboard_output_id == zeroed.dashboard_output_id

    base = _briefing(("bergama:equity:us:aapl", "AAPL"))
    for invalid in (
        Decimal("NaN"),
        Decimal("Infinity"),
        Decimal("-Infinity"),
        Decimal("-0.1"),
        Decimal("1.5"),
    ):
        bad_record = _construct_briefing_record(base.records[0], score=invalid)
        bad = _construct_briefing(base, records=(bad_record,))
        with pytest.raises(DashboardDomainError):
            assemble_dashboard_from_parts(briefing=bad, as_of=AS_OF)


def test_naive_as_of_rejected() -> None:
    briefing = _briefing(("bergama:equity:us:aapl", "AAPL"))
    with pytest.raises((DashboardValidationError, ValidationError)):
        assemble_dashboard_from_parts(
            briefing=briefing,
            as_of=datetime(2026, 7, 17, 14, 0, 0),
        )


def test_utc_as_of_accepted() -> None:
    briefing = _briefing(("bergama:equity:us:aapl", "AAPL"))
    result = assemble_dashboard_from_parts(briefing=briefing, as_of=AS_OF)
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
    result = assemble_dashboard_from_parts(briefing=briefing, as_of=as_of)
    assert result.as_of == as_of


def test_cross_as_of_mismatch_fail_closed() -> None:
    briefing = _briefing(("bergama:equity:us:aapl", "AAPL"))
    other_as_of = AS_OF + timedelta(minutes=1)
    with pytest.raises(DashboardPitConflictError) as exc_info:
        assemble_dashboard_from_parts(briefing=briefing, as_of=other_as_of)
    assert exc_info.value.detail is not None
    assert "cross_as_of" in exc_info.value.detail


def test_wrong_dashboard_policy_fail_closed() -> None:
    with pytest.raises(ValidationError):
        DashboardConfig(policy_version_id="dashboard.policy.v2")


def test_wrong_subordinate_dashboard_config_id_fail_closed() -> None:
    with pytest.raises(ValidationError):
        DashboardConfig(identity_specification_id="dashboard.identity.v2")
    with pytest.raises(ValidationError):
        DashboardConfig(presentation_selection_policy_id="include_some.v1")


def test_wrong_morning_briefing_policy_fail_closed() -> None:
    briefing = _briefing(("bergama:equity:us:aapl", "AAPL"))
    bad = _construct_briefing(briefing, policy_version_id="morning-briefing.policy.v2")
    with pytest.raises(DashboardUpstreamPolicyError):
        assemble_dashboard_from_parts(briefing=bad, as_of=AS_OF)


def test_malformed_upstream_identity_fail_closed() -> None:
    briefing = _briefing(("bergama:equity:us:aapl", "AAPL"))
    bad_id = _construct_briefing(briefing, briefing_id="not-a-digest")
    with pytest.raises(DashboardIdentityError):
        assemble_dashboard_from_parts(briefing=bad_id, as_of=AS_OF)
    bad_record = _construct_briefing_record(briefing.records[0], score_record_id="short")
    bad_records = _construct_briefing(briefing, records=(bad_record,))
    with pytest.raises(DashboardIdentityError):
        assemble_dashboard_from_parts(briefing=bad_records, as_of=AS_OF)


def test_malformed_missing_provenance_fail_closed() -> None:
    briefing = _briefing(("bergama:equity:us:aapl", "AAPL"))
    bad_provenance = BriefingProvenance.model_construct(
        **{
            **briefing.provenance.model_dump(),
            "config_fingerprint": "",
        }
    )
    bad = _construct_briefing(briefing, provenance=bad_provenance)
    with pytest.raises(DashboardProvenanceError):
        assemble_dashboard_from_parts(briefing=bad, as_of=AS_OF)


def test_ordering_mismatch_fail_closed() -> None:
    briefing = _briefing(
        ("bergama:equity:us:aapl", "AAPL"),
        ("bergama:equity:us:msft", "MSFT"),
    )
    request = DashboardRequest(briefing=briefing, as_of=AS_OF, config=DashboardConfig())
    validated = validate_dashboard_request(request)
    output = assemble_dashboard(request)
    tampered_records = (
        output.records[0].model_copy(update={"sequence_index": 1}),
        output.records[1],
    )
    tampered = output.model_copy(update={"records": tampered_records})
    with pytest.raises(DashboardOrderingError):
        validate_dashboard_output(tampered, request=validated)


def test_identity_mismatch_fail_closed() -> None:
    briefing = _briefing(("bergama:equity:us:aapl", "AAPL"))
    request = DashboardRequest(briefing=briefing, as_of=AS_OF, config=DashboardConfig())
    validated = validate_dashboard_request(request)
    output = assemble_dashboard(request)
    tampered = output.model_copy(update={"dashboard_output_id": HEX_A})
    with pytest.raises(DashboardIdentityError):
        validate_dashboard_output(tampered, request=validated)


def test_provenance_mismatch_fail_closed() -> None:
    briefing = _briefing(("bergama:equity:us:aapl", "AAPL"))
    request = DashboardRequest(briefing=briefing, as_of=AS_OF, config=DashboardConfig())
    validated = validate_dashboard_request(request)
    output = assemble_dashboard(request)
    tampered_provenance = output.provenance.model_copy(update={"config_fingerprint": HEX_B})
    tampered = output.model_copy(update={"provenance": tampered_provenance})
    with pytest.raises(DashboardProvenanceError):
        validate_dashboard_output(tampered, request=validated)


def test_config_and_output_immutability() -> None:
    briefing = _briefing(("bergama:equity:us:aapl", "AAPL"))
    config = DashboardConfig()
    result = assemble_dashboard_from_parts(briefing=briefing, as_of=AS_OF, config=config)
    with pytest.raises(ValidationError):
        config.policy_version_id = "dashboard.policy.v2"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        result.dashboard_output_id = HEX_A  # type: ignore[misc]
    with pytest.raises(ValidationError):
        result.records[0].score = result.records[0].score  # type: ignore[misc]


def test_unexpected_extra_fields_fail_closed() -> None:
    briefing = _briefing(("bergama:equity:us:aapl", "AAPL"))
    with pytest.raises(ValidationError):
        DashboardRequest(
            briefing=briefing,
            as_of=AS_OF,
            config=DashboardConfig(),
            unauthorized_field="nope",  # type: ignore[call-arg]
        )
    with pytest.raises(ValidationError):
        DashboardRequest(
            briefing=briefing,
            as_of=AS_OF,
            config=DashboardConfig(),
            scores=_score_collection(("bergama:equity:us:aapl", "AAPL")),  # type: ignore[call-arg]
        )


def test_pipeline_isolation_requires_validated_request() -> None:
    briefing = _briefing(("bergama:equity:us:aapl", "AAPL"))
    raw = DashboardRequest(briefing=briefing, as_of=AS_OF, config=DashboardConfig())
    with pytest.raises(DashboardPipelineIsolationError):
        run_dashboard_pipeline(raw)  # type: ignore[arg-type]


def test_output_completeness_exactly_one_output() -> None:
    briefing = _briefing(("bergama:equity:us:aapl", "AAPL"))
    result = assemble_dashboard_from_parts(briefing=briefing, as_of=AS_OF)
    assert result.__class__.__name__ == "DashboardPresentationOutput"
    assert isinstance(result.records, tuple)
    assert result.provenance is not None
    assert result.dashboard_output_id


def test_golden_identity_oracle_and_sensitivity() -> None:
    briefing = _briefing(
        ("bergama:equity:us:aapl", "AAPL"),
        ("bergama:equity:us:msft", "MSFT"),
    )
    expected = _independent_expected_dashboard_id(briefing, AS_OF)
    result = assemble_dashboard_from_parts(briefing=briefing, as_of=AS_OF)
    assert result.dashboard_output_id == expected
    assert result.dashboard_output_id != briefing.briefing_id
    assert result.dashboard_output_id != briefing.records[0].score_record_id

    sensitive = _briefing(("bergama:equity:us:aapl", "AAPL"))
    assert _independent_expected_dashboard_id(sensitive, AS_OF) != expected
    sensitive_result = assemble_dashboard_from_parts(briefing=sensitive, as_of=AS_OF)
    sensitive_id = sensitive_result.dashboard_output_id
    assert sensitive_id != result.dashboard_output_id


def test_deterministic_provenance_and_sensitivity() -> None:
    briefing = _briefing(("bergama:equity:us:aapl", "AAPL"))
    request = DashboardRequest(briefing=briefing, as_of=AS_OF, config=DashboardConfig())
    first = assemble_dashboard(request)
    second = assemble_dashboard(request)
    assert first.provenance == second.provenance
    assert first.provenance.config_fingerprint == second.provenance.config_fingerprint
    assert first.provenance.input_fingerprint == second.provenance.input_fingerprint
    other = assemble_dashboard_from_parts(
        briefing=_briefing(
            ("bergama:equity:us:aapl", "AAPL"),
            ("bergama:equity:us:msft", "MSFT"),
        ),
        as_of=AS_OF,
    )
    assert first.provenance.input_fingerprint != other.provenance.input_fingerprint
    assert first.dashboard_output_id != other.dashboard_output_id


def test_replay_equality() -> None:
    briefing = _briefing(("bergama:equity:us:aapl", "AAPL"))
    request = DashboardRequest(briefing=briefing, as_of=AS_OF, config=DashboardConfig())
    first = assemble_dashboard(request)
    second = reassemble(request)
    assert_replay_equal(first, second)
    assert first.dashboard_output_id == second.dashboard_output_id
    assert first.provenance == second.provenance


def test_replay_inequality_fail_closed() -> None:
    first = assemble_dashboard_from_parts(
        briefing=_briefing(("bergama:equity:us:aapl", "AAPL")),
        as_of=AS_OF,
    )
    second = assemble_dashboard_from_parts(
        briefing=_briefing(
            ("bergama:equity:us:aapl", "AAPL"),
            ("bergama:equity:us:msft", "MSFT"),
        ),
        as_of=AS_OF,
    )
    with pytest.raises(DashboardReplayInequalityError) as exc_info:
        assert_replay_equal(first, second)
    assert exc_info.value.detail == "replay_inequality"


def test_default_configuration_constants() -> None:
    config = DashboardConfig()
    assert config.policy_version_id == POLICY_VERSION_V1
    assert config.ordering_preservation_policy_id == ORDERING_PRESERVATION_POLICY_V1
    assert config.identity_specification_id == IDENTITY_SPECIFICATION_V1
    assert config.provenance_specification_id == PROVENANCE_SPECIFICATION_V1
    assert config.digest_method_id == DIGEST_METHOD_V1
    assert config.presentation_selection_policy_id == PRESENTATION_SELECTION_POLICY_V1


def test_no_float_wall_clock_random_uuid_or_forbidden_imports_in_dashboard_sources() -> None:
    root = Path(__file__).resolve().parents[2] / "app" / "dashboard"
    forbidden = (
        "datetime.now(",
        "datetime.utcnow(",
        "time.time(",
        "uuid4(",
        "uuid.",
        "random.",
        "float(",
        "app.premarket.scoring",
        "app.premarket.morning_briefing.models",
        "app.premarket.morning_briefing.engine",
        "app.premarket.morning_briefing.pipeline",
        "app.premarket.morning_briefing.identity",
        "app.premarket.morning_briefing.provenance",
        "app.premarket.morning_briefing.validate_input",
        "app.premarket.morning_briefing.validate_output",
        "app.premarket.morning_briefing.ordering",
        "app.premarket.morning_briefing.output",
        "app.features.",
    )
    for path in root.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, f"{path.name} contains {token}"


def test_coerce_invalid_request_fail_closed() -> None:
    with pytest.raises(DashboardValidationError):
        assemble_dashboard({"briefing": "not-a-briefing"})


def test_unsupported_digest_on_validated_path_fail_closed() -> None:
    briefing = _briefing(("bergama:equity:us:aapl", "AAPL"))
    config = DashboardConfig.model_construct(
        policy_version_id=POLICY_VERSION_V1,
        ordering_preservation_policy_id=ORDERING_PRESERVATION_POLICY_V1,
        identity_specification_id=IDENTITY_SPECIFICATION_V1,
        provenance_specification_id=PROVENANCE_SPECIFICATION_V1,
        digest_method_id="md5",
        presentation_selection_policy_id=PRESENTATION_SELECTION_POLICY_V1,
    )
    request = DashboardRequest.model_construct(briefing=briefing, as_of=AS_OF, config=config)
    with pytest.raises(DashboardUnsupportedPolicyError):
        assemble_dashboard(request)
