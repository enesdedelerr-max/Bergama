"""Unit tests for Morning Briefing Engine (Policy Version v1)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from app.core.premarket_settings import PremarketSettings
from app.premarket.errors import (
    BriefingConflictError,
    BriefingDomainError,
    BriefingInvariantError,
    BriefingUnsupportedPolicyError,
    BriefingValidationError,
    PremarketDisabledError,
)
from app.premarket.morning_briefing.engine import (
    assemble_briefing,
    assemble_briefing_from_parts,
)
from app.premarket.morning_briefing.models import BriefingConfig, BriefingRequest
from app.premarket.morning_briefing.policy import (
    DIGEST_METHOD_V1,
    IDENTITY_SPECIFICATION_V1,
    ORDERING_PRESERVATION_POLICY_V1,
    POLICY_VERSION_V1,
    PROVENANCE_SPECIFICATION_V1,
)
from app.premarket.morning_briefing.replay import assert_replay_equal, reassemble
from app.premarket.scoring.engine import scan_scores
from app.premarket.scoring.models import (
    ScoreCollection,
    ScoreComponents,
    ScoreConfig,
    ScoreProvenance,
    ScoreRecord,
    ScoreRequest,
)
from app.premarket.scoring.policy import (
    POLICY_VERSION_V1 as SCORING_POLICY_VERSION_V1,
)
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


def _manual_record(
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


def _manual_collection(records: tuple[ScoreRecord, ...]) -> ScoreCollection:
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


def _independent_expected_briefing_id(scores: ScoreCollection, as_of: datetime) -> str:
    """Golden oracle: build identity payload without production identity helpers."""
    payload = {
        "schema": IDENTITY_SPECIFICATION_V1,
        "policy_version_id": POLICY_VERSION_V1,
        "ordering_preservation_policy_id": ORDERING_PRESERVATION_POLICY_V1,
        "provenance_specification_id": PROVENANCE_SPECIFICATION_V1,
        "as_of": as_of,
        "configuration": {
            "policy_version_id": POLICY_VERSION_V1,
            "ordering_preservation_policy_id": ORDERING_PRESERVATION_POLICY_V1,
            "identity_specification_id": IDENTITY_SPECIFICATION_V1,
            "provenance_specification_id": PROVENANCE_SPECIFICATION_V1,
            "digest_method_id": DIGEST_METHOD_V1,
        },
        "upstream_scoring_policy_version_id": SCORING_POLICY_VERSION_V1,
        "ordered_score_record_ids": [record.score_record_id for record in scores.records],
        "upstream_scoring_collection_provenance": scores.provenance.model_dump(mode="python"),
    }
    assert set(payload) == {
        "schema",
        "policy_version_id",
        "ordering_preservation_policy_id",
        "provenance_specification_id",
        "as_of",
        "configuration",
        "upstream_scoring_policy_version_id",
        "ordered_score_record_ids",
        "upstream_scoring_collection_provenance",
    }
    return strategy_sha256(payload)


def test_empty_universe_briefing() -> None:
    scores = _score_collection()
    result = assemble_briefing_from_parts(scores=scores, as_of=AS_OF)
    assert result.records == ()
    assert result.policy_version_id == POLICY_VERSION_V1
    assert result.ordering_preservation_policy_id == ORDERING_PRESERVATION_POLICY_V1
    assert len(result.briefing_id) == 64
    assert result.provenance.source_identifiers == ()


def test_preserves_scoring_order_and_values() -> None:
    scores = _score_collection(
        ("bergama:equity:us:aapl", "AAPL"),
        ("bergama:equity:us:msft", "MSFT"),
    )
    result = assemble_briefing(BriefingRequest(scores=scores, as_of=AS_OF, config=BriefingConfig()))
    assert len(result.records) == 2
    for index, (briefing_record, score_record) in enumerate(
        zip(result.records, scores.records, strict=True)
    ):
        assert briefing_record.sequence_index == index
        assert briefing_record.score_record_id == score_record.score_record_id
        assert briefing_record.instrument_key == score_record.instrument_key
        assert briefing_record.score == score_record.score
        assert briefing_record.components == score_record.components
        assert briefing_record.scoring_policy_version_id == SCORING_POLICY_VERSION_V1
        assert briefing_record.scoring_weight_profile_id == WEIGHT_PROFILE_DEFAULT_V1
    assert result.provenance.source_identifiers == tuple(
        record.score_record_id for record in scores.records
    )


def test_golden_identity_oracle_matches_briefing_id() -> None:
    scores = _score_collection(
        ("bergama:equity:us:aapl", "AAPL"),
        ("bergama:equity:us:msft", "MSFT"),
    )
    expected = _independent_expected_briefing_id(scores, AS_OF)
    result = assemble_briefing_from_parts(scores=scores, as_of=AS_OF)
    assert result.briefing_id == expected
    assert result.briefing_id != scores.records[0].score_record_id

    sensitive = _score_collection(("bergama:equity:us:aapl", "AAPL"))
    assert _independent_expected_briefing_id(sensitive, AS_OF) != expected
    sensitive_id = assemble_briefing_from_parts(scores=sensitive, as_of=AS_OF).briefing_id
    assert sensitive_id != result.briefing_id


def test_replay_equality() -> None:
    scores = _score_collection(("bergama:equity:us:aapl", "AAPL"))
    request = BriefingRequest(scores=scores, as_of=AS_OF, config=BriefingConfig())
    first = assemble_briefing(request)
    second = reassemble(request)
    assert_replay_equal(first, second)
    assert first.briefing_id == second.briefing_id
    assert first.provenance == second.provenance


def test_replay_inequality_fail_closed() -> None:
    first = assemble_briefing_from_parts(
        scores=_score_collection(("bergama:equity:us:aapl", "AAPL")),
        as_of=AS_OF,
    )
    second = assemble_briefing_from_parts(
        scores=_score_collection(
            ("bergama:equity:us:aapl", "AAPL"),
            ("bergama:equity:us:msft", "MSFT"),
        ),
        as_of=AS_OF,
    )
    with pytest.raises(BriefingInvariantError) as exc_info:
        assert_replay_equal(first, second)
    assert exc_info.value.detail == "replay_inequality"


def test_identical_inputs_preserve_identity_and_fingerprints() -> None:
    scores = _score_collection(("bergama:equity:us:aapl", "AAPL"))
    request = BriefingRequest(scores=scores, as_of=AS_OF, config=BriefingConfig())
    first = assemble_briefing(request)
    second = assemble_briefing(request)
    assert first.briefing_id == second.briefing_id
    assert first.provenance.config_fingerprint == second.provenance.config_fingerprint
    assert first.provenance.input_fingerprint == second.provenance.input_fingerprint


def test_material_score_change_changes_input_fingerprint() -> None:
    first = assemble_briefing_from_parts(
        scores=_score_collection(("bergama:equity:us:aapl", "AAPL")),
        as_of=AS_OF,
    )
    second = assemble_briefing_from_parts(
        scores=_score_collection(
            ("bergama:equity:us:aapl", "AAPL"),
            ("bergama:equity:us:msft", "MSFT"),
        ),
        as_of=AS_OF,
    )
    assert first.provenance.input_fingerprint != second.provenance.input_fingerprint
    assert first.briefing_id != second.briefing_id


def test_settings_disabled_fail_closed() -> None:
    scores = _score_collection(("bergama:equity:us:aapl", "AAPL"))
    with pytest.raises(PremarketDisabledError):
        assemble_briefing_from_parts(
            scores=scores,
            as_of=AS_OF,
            settings=PremarketSettings(enabled=False),
        )


def test_settings_enabled_succeeds() -> None:
    scores = _score_collection(("bergama:equity:us:aapl", "AAPL"))
    result = assemble_briefing_from_parts(
        scores=scores,
        as_of=AS_OF,
        settings=PremarketSettings(enabled=True),
    )
    assert len(result.records) == 1
    assert len(result.briefing_id) == 64


def test_cross_pit_fail_closed() -> None:
    scores = _score_collection(("bergama:equity:us:aapl", "AAPL"))
    other_as_of = AS_OF + timedelta(minutes=1)
    with pytest.raises(BriefingConflictError) as exc_info:
        assemble_briefing_from_parts(scores=scores, as_of=other_as_of)
    assert exc_info.value.detail is not None
    assert "cross_pit" in exc_info.value.detail


def test_naive_as_of_rejected() -> None:
    scores = _score_collection(("bergama:equity:us:aapl", "AAPL"))
    with pytest.raises((BriefingValidationError, ValidationError)):
        assemble_briefing_from_parts(
            scores=scores,
            as_of=datetime(2026, 7, 17, 14, 0, 0),
        )


def test_fixed_offset_as_of_accepted_when_matching_scores() -> None:
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
    result = assemble_briefing_from_parts(scores=scores, as_of=as_of)
    assert result.as_of == as_of


def test_unsupported_policy_fail_closed() -> None:
    with pytest.raises(ValidationError):
        BriefingConfig(policy_version_id="morning-briefing.policy.v2")


def test_upstream_scoring_policy_mismatch_fail_closed() -> None:
    scores = _score_collection(("bergama:equity:us:aapl", "AAPL"))
    bad = ScoreCollection.model_construct(
        as_of=scores.as_of,
        records=scores.records,
        provenance=ScoreProvenance.model_construct(
            config_fingerprint=scores.provenance.config_fingerprint,
            input_fingerprint=scores.provenance.input_fingerprint,
            ordering_policy_id=scores.provenance.ordering_policy_id,
            policy_version_id="premarket.scoring.policy.v2",
            weight_profile_id=scores.provenance.weight_profile_id,
            source_identifiers=scores.provenance.source_identifiers,
        ),
    )
    with pytest.raises(BriefingUnsupportedPolicyError):
        assemble_briefing_from_parts(scores=bad, as_of=AS_OF)


def test_score_domain_boundaries_and_non_finite() -> None:
    base = _score_collection(("bergama:equity:us:aapl", "AAPL")).records[0]

    for valid in (Decimal("0"), Decimal("1")):
        scores = _manual_collection(
            (
                _manual_record(
                    score_record_id=HEX_C,
                    instrument_key="bergama:equity:us:aapl",
                    score=valid,
                    components=base.components,
                ),
            )
        )
        result = assemble_briefing_from_parts(scores=scores, as_of=AS_OF)
        assert result.records[0].score == valid

    negative_zero = _manual_collection(
        (
            _manual_record(
                score_record_id=HEX_C,
                instrument_key="bergama:equity:us:aapl",
                score=Decimal("-0"),
                components=base.components,
            ),
        )
    )
    zeroed = assemble_briefing_from_parts(scores=negative_zero, as_of=AS_OF)
    assert zeroed.records[0].score == Decimal("0")
    assert zeroed.records[0].score.is_zero()
    assert format(zeroed.records[0].score, "f") == "0"
    assert assemble_briefing_from_parts(scores=negative_zero, as_of=AS_OF).briefing_id == (
        zeroed.briefing_id
    )

    for invalid in (Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity"), Decimal("1.5")):
        bad = _manual_collection(
            (
                _manual_record(
                    score_record_id=HEX_C,
                    instrument_key="bergama:equity:us:aapl",
                    score=invalid,
                    components=base.components,
                ),
            )
        )
        with pytest.raises(BriefingDomainError):
            assemble_briefing_from_parts(scores=bad, as_of=AS_OF)


def test_duplicate_score_record_id_fail_closed() -> None:
    record = _manual_record(
        score_record_id=HEX_C,
        instrument_key="bergama:equity:us:aapl",
        score=Decimal("0.5"),
    )
    duplicate = _manual_record(
        score_record_id=HEX_C,
        instrument_key="bergama:equity:us:msft",
        score=Decimal("0.4"),
    )
    with pytest.raises(BriefingValidationError) as exc_info:
        assemble_briefing_from_parts(
            scores=_manual_collection((record, duplicate)),
            as_of=AS_OF,
        )
    assert exc_info.value.detail is not None
    assert "duplicate_score_record_id" in exc_info.value.detail


def test_equal_scores_preserve_upstream_sequence_without_rerank() -> None:
    first = _manual_record(
        score_record_id=HEX_C,
        instrument_key="bergama:equity:us:msft",
        score=Decimal("0.5"),
        local_symbol="MSFT",
    )
    second = _manual_record(
        score_record_id=HEX_D,
        instrument_key="bergama:equity:us:aapl",
        score=Decimal("0.5"),
        local_symbol="AAPL",
    )
    # Equal scores: briefing must not invent a tie-break (e.g. instrument_key asc).
    scores = _manual_collection((first, second))
    result = assemble_briefing_from_parts(scores=scores, as_of=AS_OF)
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
    result = assemble_briefing_from_parts(scores=reversed_scores, as_of=AS_OF)
    assert [record.score_record_id for record in result.records] == [
        record.score_record_id for record in reversed_records
    ]
    assert result.provenance.source_identifiers == tuple(
        record.score_record_id for record in reversed_records
    )
    forward = assemble_briefing_from_parts(scores=scores, as_of=AS_OF)
    assert result.provenance.source_identifiers != forward.provenance.source_identifiers
    assert result.briefing_id != forward.briefing_id


def test_duplicate_instrument_key_preserves_upstream_public_sequence() -> None:
    # Premarket Scoring scan rejects duplicate instruments; briefing admits constructed
    # public ScoreCollection payloads and preserves upstream sequence without re-ranking.
    first = _manual_record(
        score_record_id=HEX_C,
        instrument_key="bergama:equity:us:aapl",
        score=Decimal("0.9"),
    )
    second = _manual_record(
        score_record_id=HEX_D,
        instrument_key="bergama:equity:us:aapl",
        score=Decimal("0.1"),
    )
    result = assemble_briefing_from_parts(
        scores=_manual_collection((first, second)),
        as_of=AS_OF,
    )
    assert [record.score_record_id for record in result.records] == [HEX_C, HEX_D]
    assert [record.instrument_key for record in result.records] == [
        "bergama:equity:us:aapl",
        "bergama:equity:us:aapl",
    ]


def test_null_local_symbol_and_optional_components_preserved() -> None:
    record = _manual_record(
        score_record_id=HEX_C,
        instrument_key="bergama:equity:us:aapl",
        score=Decimal("0.25"),
        local_symbol=None,
        components=ScoreComponents(
            watchlist_rank=Decimal("1"),
            gap_magnitude=None,
            catalyst_presence=None,
        ),
    )
    result = assemble_briefing_from_parts(
        scores=_manual_collection((record,)),
        as_of=AS_OF,
    )
    assert result.records[0].local_symbol is None
    assert result.records[0].components.gap_magnitude is None
    assert result.records[0].components.catalyst_presence is None


def test_upstream_provenance_references_unchanged() -> None:
    scores = _score_collection(("bergama:equity:us:aapl", "AAPL"))
    result = assemble_briefing_from_parts(scores=scores, as_of=AS_OF)
    assert result.provenance.upstream_scoring_config_fingerprint == (
        scores.provenance.config_fingerprint
    )
    assert result.provenance.upstream_scoring_input_fingerprint == (
        scores.provenance.input_fingerprint
    )
    assert result.provenance.upstream_scoring_policy_version_id == (
        scores.provenance.policy_version_id
    )
    assert result.provenance.upstream_scoring_weight_profile_id == (
        scores.provenance.weight_profile_id
    )
    assert result.provenance.upstream_scoring_ordering_policy_id == (
        scores.provenance.ordering_policy_id
    )


def test_identity_changes_when_score_set_changes() -> None:
    first = assemble_briefing_from_parts(
        scores=_score_collection(("bergama:equity:us:aapl", "AAPL")),
        as_of=AS_OF,
    )
    second = assemble_briefing_from_parts(
        scores=_score_collection(
            ("bergama:equity:us:aapl", "AAPL"),
            ("bergama:equity:us:msft", "MSFT"),
        ),
        as_of=AS_OF,
    )
    assert first.briefing_id != second.briefing_id


def test_default_configuration_constants() -> None:
    config = BriefingConfig()
    assert config.policy_version_id == POLICY_VERSION_V1
    assert config.ordering_preservation_policy_id == ORDERING_PRESERVATION_POLICY_V1
    assert config.identity_specification_id == IDENTITY_SPECIFICATION_V1
    assert config.provenance_specification_id == PROVENANCE_SPECIFICATION_V1
    assert config.digest_method_id == DIGEST_METHOD_V1


def test_no_float_or_wall_clock_in_briefing_sources() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[2] / "app" / "premarket" / "morning_briefing"
    forbidden = ("datetime.now(", "time.time(", "uuid4(", "random.")
    for path in root.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, f"{path.name} contains {token}"


def test_coerce_invalid_request_fail_closed() -> None:
    with pytest.raises(BriefingValidationError):
        assemble_briefing({"scores": "not-a-collection"})
