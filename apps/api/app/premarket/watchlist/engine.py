"""Deterministic Premarket Watchlist Engine."""

from __future__ import annotations

from datetime import datetime

from app.premarket.errors import (
    PremarketDisabledError,
    WatchlistDuplicateInstrumentError,
    WatchlistValidationError,
)
from app.premarket.settings import PremarketSettings
from app.premarket.watchlist.models import (
    Watchlist,
    WatchlistCandidate,
    WatchlistConfig,
    WatchlistEntry,
    WatchlistGenerationRequest,
    WatchlistInclusionRule,
    WatchlistProvenance,
)
from app.premarket.watchlist.normalize import normalize_candidates
from app.premarket.watchlist.ordering import (
    ORDERING_POLICY_RULE_PRIORITY_ASC_INSTRUMENT_KEY_ASC,
    watchlist_sort_key,
)
from app.strategy.keys import strategy_sha256

_RANK_BASE = 1


def generate_watchlist(
    request: WatchlistGenerationRequest | object,
    *,
    settings: PremarketSettings | None = None,
) -> Watchlist:
    """Generate a deterministic watchlist from approved candidates and config.

    When ``settings`` is provided, enablement must be true (fail-closed).
    When ``settings`` is omitted, generation runs for direct unit use.
    """
    if settings is not None and not settings.enabled:
        raise PremarketDisabledError(detail="premarket_disabled")

    validated = _coerce_request(request)
    candidates = _reject_duplicate_keys(validated.candidates)
    included = _select_included(candidates=candidates, config=validated.config)
    ordered = sorted(
        included,
        key=lambda item: watchlist_sort_key(
            rule=item[1],
            instrument_key=item[0].instrument_key,
        ),
    )
    if validated.config.max_size is not None:
        ordered = ordered[: validated.config.max_size]

    evaluation_timestamp = validated.as_of
    entries = tuple(
        WatchlistEntry(
            instrument_key=candidate.instrument_key,
            local_symbol=candidate.local_symbol,
            evaluation_timestamp=evaluation_timestamp,
            rank=_RANK_BASE + index,
            inclusion_reason=rule.inclusion_reason,
            rule_id=rule.rule_id,
        )
        for index, (candidate, rule) in enumerate(ordered)
    )

    provenance = WatchlistProvenance(
        config_fingerprint=_config_fingerprint(validated.config),
        input_fingerprint=_input_fingerprint(validated),
        ordering_policy_id=validated.config.ordering_policy_id,
        source_identifiers=tuple(entry.instrument_key for entry in entries),
    )
    return Watchlist(
        evaluation_timestamp=evaluation_timestamp,
        entries=entries,
        provenance=provenance,
    )


def generate_watchlist_from_parts(
    *,
    candidates: object,
    as_of: datetime,
    config: WatchlistConfig | object,
    settings: PremarketSettings | None = None,
) -> Watchlist:
    """Convenience entrypoint that normalizes candidate sequences."""
    from datetime import datetime as datetime_type

    if not isinstance(as_of, datetime_type):
        raise WatchlistValidationError(detail="invalid_as_of")
    request = WatchlistGenerationRequest(
        candidates=normalize_candidates(candidates),
        as_of=as_of,
        config=(
            config
            if isinstance(config, WatchlistConfig)
            else WatchlistConfig.model_validate(config)
        ),
    )
    return generate_watchlist(request, settings=settings)


def _coerce_request(request: object) -> WatchlistGenerationRequest:
    if isinstance(request, WatchlistGenerationRequest):
        return request
    try:
        return WatchlistGenerationRequest.model_validate(request)
    except Exception as exc:
        raise WatchlistValidationError(detail=f"invalid_request:{exc}") from exc


def _reject_duplicate_keys(
    candidates: tuple[WatchlistCandidate, ...],
) -> tuple[WatchlistCandidate, ...]:
    seen: set[str] = set()
    for candidate in candidates:
        key = candidate.instrument_key
        if key in seen:
            raise WatchlistDuplicateInstrumentError(detail=f"duplicate_instrument:{key}")
        seen.add(key)
    return candidates


def _select_included(
    *,
    candidates: tuple[WatchlistCandidate, ...],
    config: WatchlistConfig,
) -> list[tuple[WatchlistCandidate, WatchlistInclusionRule]]:
    rules_by_priority = sorted(config.rules, key=lambda rule: (rule.rule_priority, rule.rule_id))
    included: list[tuple[WatchlistCandidate, WatchlistInclusionRule]] = []
    for candidate in candidates:
        matched = _match_rule(candidate.instrument_key, rules_by_priority)
        if matched is not None:
            included.append((candidate, matched))
    return included


def _match_rule(
    instrument_key: str,
    rules_by_priority: list[WatchlistInclusionRule],
) -> WatchlistInclusionRule | None:
    for rule in rules_by_priority:
        if instrument_key in rule.allowed_instrument_keys:
            return rule
    return None


def _config_fingerprint(config: WatchlistConfig) -> str:
    return strategy_sha256(config.model_dump(mode="python"))


def _input_fingerprint(request: WatchlistGenerationRequest) -> str:
    return strategy_sha256(
        {
            "as_of": request.as_of,
            "candidates": [c.model_dump(mode="python") for c in request.candidates],
            "config": request.config.model_dump(mode="python"),
            "ordering_policy_id": ORDERING_POLICY_RULE_PRIORITY_ASC_INSTRUMENT_KEY_ASC,
        }
    )
