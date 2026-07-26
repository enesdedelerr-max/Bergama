"""Unit tests for Premarket Watchlist Engine foundation (#72)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.core.config import AppSettings
from app.core.premarket_settings import PremarketSettings
from app.premarket.errors import (
    PremarketDisabledError,
    WatchlistDuplicateInstrumentError,
    WatchlistUnsupportedCandidateError,
    WatchlistValidationError,
)
from app.premarket.watchlist.engine import generate_watchlist, generate_watchlist_from_parts
from app.premarket.watchlist.models import (
    WatchlistCandidate,
    WatchlistConfig,
    WatchlistGenerationRequest,
    WatchlistInclusionRule,
)
from app.premarket.watchlist.ordering import ORDERING_POLICY_RULE_PRIORITY_ASC_INSTRUMENT_KEY_ASC
from pydantic import ValidationError

AS_OF = datetime(2026, 7, 17, 12, 0, 0, tzinfo=UTC)


def _rule(
    *,
    rule_id: str = "allowlist-core",
    rule_priority: int = 10,
    keys: tuple[str, ...] = ("bergama:equity:us:aapl",),
    reason: str = "core_allowlist",
) -> WatchlistInclusionRule:
    return WatchlistInclusionRule(
        rule_id=rule_id,
        rule_priority=rule_priority,
        inclusion_reason=reason,
        allowed_instrument_keys=keys,
    )


def _config(
    *,
    rules: tuple[WatchlistInclusionRule, ...] | None = None,
    max_size: int | None = None,
) -> WatchlistConfig:
    return WatchlistConfig(
        rules=rules or (_rule(),),
        max_size=max_size,
    )


def _request(
    candidates: tuple[WatchlistCandidate, ...],
    *,
    config: WatchlistConfig | None = None,
    as_of: datetime = AS_OF,
) -> WatchlistGenerationRequest:
    return WatchlistGenerationRequest(
        candidates=candidates,
        as_of=as_of,
        config=config or _config(),
    )


def test_premarket_settings_disabled_by_default() -> None:
    settings = PremarketSettings()
    assert settings.enabled is False
    app = AppSettings(environment="test", bootstrap_auth_enabled=False)
    assert app.premarket.enabled is False
    assert "premarket" in AppSettings.model_fields
    assert app.safe_summary()["premarket"] == {"enabled": False}


def test_generate_fails_closed_when_settings_disabled() -> None:
    request = _request((WatchlistCandidate(instrument_key="bergama:equity:us:aapl"),))
    with pytest.raises(PremarketDisabledError) as exc_info:
        generate_watchlist(request, settings=PremarketSettings(enabled=False))
    assert exc_info.value.detail == "premarket_disabled"
    assert exc_info.value.code == "premarket.disabled"


def test_generate_runs_when_enabled() -> None:
    request = _request((WatchlistCandidate(instrument_key="bergama:equity:us:aapl"),))
    result = generate_watchlist(request, settings=PremarketSettings(enabled=True))
    assert len(result.entries) == 1
    assert result.entries[0].instrument_key == "bergama:equity:us:aapl"


def test_single_valid_candidate() -> None:
    candidate = WatchlistCandidate(
        instrument_key="bergama:equity:us:aapl",
        local_symbol="AAPL",
    )
    result = generate_watchlist(_request((candidate,)))
    assert len(result.entries) == 1
    entry = result.entries[0]
    assert entry.instrument_key == "bergama:equity:us:aapl"
    assert entry.local_symbol == "AAPL"
    assert entry.evaluation_timestamp == AS_OF
    assert entry.rank == 1
    assert entry.rule_id == "allowlist-core"
    assert entry.inclusion_reason == "core_allowlist"
    assert result.evaluation_timestamp == AS_OF
    assert (
        result.provenance.ordering_policy_id == ORDERING_POLICY_RULE_PRIORITY_ASC_INSTRUMENT_KEY_ASC
    )


def test_multiple_candidates_and_deterministic_ordering() -> None:
    config = _config(
        rules=(
            _rule(rule_id="b", rule_priority=20, keys=("bergama:equity:us:msft",)),
            _rule(
                rule_id="a",
                rule_priority=10,
                keys=("bergama:equity:us:aapl", "bergama:equity:us:zzz"),
            ),
        )
    )
    candidates = (
        WatchlistCandidate(instrument_key="bergama:equity:us:zzz"),
        WatchlistCandidate(instrument_key="bergama:equity:us:msft"),
        WatchlistCandidate(instrument_key="bergama:equity:us:aapl"),
        WatchlistCandidate(instrument_key="bergama:equity:us:ignored"),
    )
    first = generate_watchlist(_request(candidates, config=config))
    second = generate_watchlist(_request(candidates, config=config))
    keys = tuple(entry.instrument_key for entry in first.entries)
    assert keys == (
        "bergama:equity:us:aapl",
        "bergama:equity:us:zzz",
        "bergama:equity:us:msft",
    )
    assert tuple(entry.rank for entry in first.entries) == (1, 2, 3)
    assert first.model_dump() == second.model_dump()
    assert first.provenance.config_fingerprint == second.provenance.config_fingerprint
    assert first.provenance.input_fingerprint == second.provenance.input_fingerprint


def test_rule_priority_and_instrument_key_tie_break() -> None:
    config = _config(
        rules=(
            _rule(rule_id="p1", rule_priority=1, keys=("bergama:equity:us:bbb",)),
            _rule(
                rule_id="p0",
                rule_priority=0,
                keys=("bergama:equity:us:aaa", "bergama:equity:us:ccc"),
            ),
        )
    )
    candidates = (
        WatchlistCandidate(instrument_key="bergama:equity:us:ccc"),
        WatchlistCandidate(instrument_key="bergama:equity:us:bbb"),
        WatchlistCandidate(instrument_key="bergama:equity:us:aaa"),
    )
    result = generate_watchlist(_request(candidates, config=config))
    assert [e.instrument_key for e in result.entries] == [
        "bergama:equity:us:aaa",
        "bergama:equity:us:ccc",
        "bergama:equity:us:bbb",
    ]
    assert [e.rule_id for e in result.entries] == ["p0", "p0", "p1"]


def test_duplicate_instrument_keys_are_rejected() -> None:
    candidates = (
        WatchlistCandidate(instrument_key="bergama:equity:us:aapl"),
        WatchlistCandidate(instrument_key="bergama:equity:us:aapl", local_symbol="AAPL"),
    )
    with pytest.raises(WatchlistDuplicateInstrumentError) as exc_info:
        generate_watchlist(_request(candidates))
    assert "duplicate_instrument" in (exc_info.value.detail or "")


def test_empty_candidates_produce_empty_watchlist() -> None:
    result = generate_watchlist(_request(()))
    assert result.entries == ()
    assert result.evaluation_timestamp == AS_OF
    assert result.provenance.config_fingerprint
    assert result.provenance.input_fingerprint
    assert result.provenance.source_identifiers == ()


def test_unsupported_candidate_type_fails_closed() -> None:
    with pytest.raises(WatchlistUnsupportedCandidateError):
        generate_watchlist_from_parts(
            candidates=["bergama:equity:us:aapl"],
            as_of=AS_OF,
            config=_config(),
        )


def test_invalid_identity_fails_closed() -> None:
    with pytest.raises(ValidationError):
        WatchlistCandidate(instrument_key="   ")


def test_naive_as_of_is_rejected() -> None:
    with pytest.raises(ValidationError):
        WatchlistGenerationRequest(
            candidates=(),
            as_of=datetime(2026, 7, 17, 12, 0, 0),
            config=_config(),
        )


def test_timezone_aware_as_of_is_normalized_to_utc() -> None:
    from datetime import timedelta, timezone

    offset = timezone(timedelta(hours=-4))
    as_of = datetime(2026, 7, 17, 8, 0, 0, tzinfo=offset)
    result = generate_watchlist(_request((), as_of=as_of))
    assert result.evaluation_timestamp.tzinfo == UTC
    assert result.evaluation_timestamp == as_of.astimezone(UTC)


def test_max_size_applied_after_ordering() -> None:
    config = _config(
        rules=(
            _rule(
                keys=(
                    "bergama:equity:us:aapl",
                    "bergama:equity:us:msft",
                    "bergama:equity:us:zzz",
                )
            ),
        ),
        max_size=2,
    )
    candidates = (
        WatchlistCandidate(instrument_key="bergama:equity:us:zzz"),
        WatchlistCandidate(instrument_key="bergama:equity:us:msft"),
        WatchlistCandidate(instrument_key="bergama:equity:us:aapl"),
    )
    result = generate_watchlist(_request(candidates, config=config))
    assert [e.instrument_key for e in result.entries] == [
        "bergama:equity:us:aapl",
        "bergama:equity:us:msft",
    ]
    assert [e.rank for e in result.entries] == [1, 2]


def test_invalid_max_size_rejected() -> None:
    with pytest.raises(ValidationError):
        WatchlistConfig(rules=(_rule(),), max_size=0)
    with pytest.raises(ValidationError):
        WatchlistConfig(rules=(_rule(),), max_size=-1)


def test_invalid_ordering_policy_rejected() -> None:
    with pytest.raises(ValidationError):
        WatchlistConfig(rules=(_rule(),), ordering_policy_id="random_order")


def test_local_symbol_optional_and_not_identity() -> None:
    with_symbol = WatchlistCandidate(instrument_key="bergama:equity:us:aapl", local_symbol="AAPL")
    without_symbol = WatchlistCandidate(instrument_key="bergama:equity:us:aapl")
    first = generate_watchlist(_request((with_symbol,)))
    second = generate_watchlist(_request((without_symbol,)))
    assert first.entries[0].instrument_key == second.entries[0].instrument_key
    assert first.entries[0].local_symbol == "AAPL"
    assert second.entries[0].local_symbol is None


def test_v1_inclusion_does_not_require_feature_platform() -> None:
    # GenerationRequest has no feature snapshot field; allowlist alone is sufficient.
    fields = set(WatchlistGenerationRequest.model_fields)
    assert "feature_snapshots" not in fields
    assert "features" not in fields
    result = generate_watchlist(
        _request((WatchlistCandidate(instrument_key="bergama:equity:us:aapl"),))
    )
    assert len(result.entries) == 1


def test_fingerprints_stable_across_replay() -> None:
    request = _request(
        (
            WatchlistCandidate(instrument_key="bergama:equity:us:msft"),
            WatchlistCandidate(instrument_key="bergama:equity:us:aapl"),
        ),
        config=_config(rules=(_rule(keys=("bergama:equity:us:aapl", "bergama:equity:us:msft")),)),
    )
    outputs = [generate_watchlist(request) for _ in range(3)]
    assert len({o.provenance.input_fingerprint for o in outputs}) == 1
    assert len({o.provenance.config_fingerprint for o in outputs}) == 1
    assert outputs[0].model_dump() == outputs[1].model_dump() == outputs[2].model_dump()


def test_invalid_request_object_fails_closed() -> None:
    with pytest.raises(WatchlistValidationError):
        generate_watchlist(object())
