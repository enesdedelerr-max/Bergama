"""Deterministic Premarket Catalyst normalization engine."""

from __future__ import annotations

from datetime import datetime

from app.market_data.events.news import NewsEvent
from app.premarket.catalyst.classify import classify_news_event
from app.premarket.catalyst.identity import build_catalyst_record_id, declared_source_identity
from app.premarket.catalyst.models import (
    CatalystCollection,
    CatalystConfig,
    CatalystNormalizationRequest,
    CatalystProvenance,
    CatalystRecord,
)
from app.premarket.catalyst.normalize import coerce_news_events
from app.premarket.catalyst.ordering import (
    ORDERING_POLICY_KNOWN_AT_ASC_EVENT_TIME_ASC_TYPE_ASC_INSTRUMENT_KEY_ASC_ID_ASC,
    catalyst_sort_key,
)
from app.premarket.errors import (
    CatalystIdentityConflictError,
    CatalystStaleKnownAtError,
    CatalystUnsupportedEventError,
    CatalystValidationError,
    PremarketDisabledError,
)
from app.premarket.settings import PremarketSettings
from app.strategy.keys import strategy_sha256


def normalize_catalysts(
    request: CatalystNormalizationRequest | object,
    *,
    settings: PremarketSettings | None = None,
) -> CatalystCollection:
    """Normalize approved NewsEvent inputs into a deterministic catalyst collection.

    When ``settings`` is provided, enablement must be true (fail-closed).
    When ``settings`` is omitted, normalization runs for direct unit use.
    """
    if settings is not None and not settings.enabled:
        raise PremarketDisabledError(detail="premarket_disabled")

    validated = _coerce_request(request)
    records = _normalize_events(
        events=validated.events,
        as_of=validated.as_of,
        config=validated.config,
    )
    ordered = tuple(sorted(records, key=catalyst_sort_key))

    provenance = CatalystProvenance(
        config_fingerprint=_config_fingerprint(validated.config),
        input_fingerprint=_input_fingerprint(validated),
        ordering_policy_id=validated.config.ordering_policy_id,
        source_identifiers=tuple(record.catalyst_record_id for record in ordered),
    )
    return CatalystCollection(
        as_of=validated.as_of,
        records=ordered,
        provenance=provenance,
    )


def normalize_catalysts_from_parts(
    *,
    events: object,
    as_of: datetime,
    config: CatalystConfig | object,
    settings: PremarketSettings | None = None,
) -> CatalystCollection:
    """Convenience entrypoint that coerces event sequences."""
    if not isinstance(as_of, datetime):
        raise CatalystValidationError(detail="invalid_as_of")
    request = CatalystNormalizationRequest(
        events=coerce_news_events(events),
        as_of=as_of,
        config=(
            config if isinstance(config, CatalystConfig) else CatalystConfig.model_validate(config)
        ),
    )
    return normalize_catalysts(request, settings=settings)


def _coerce_request(request: object) -> CatalystNormalizationRequest:
    if isinstance(request, CatalystNormalizationRequest):
        return request
    try:
        return CatalystNormalizationRequest.model_validate(request)
    except Exception as exc:
        raise CatalystValidationError(detail=f"invalid_request:{exc}") from exc


def _normalize_events(
    *,
    events: tuple[NewsEvent, ...],
    as_of: datetime,
    config: CatalystConfig,
) -> list[CatalystRecord]:
    by_record_id: dict[str, CatalystRecord] = {}
    source_identity_to_record_id: dict[tuple[str, str], str] = {}

    for event in events:
        if not isinstance(event, NewsEvent):
            raise CatalystUnsupportedEventError(
                detail=f"unsupported_event_type:{type(event).__name__}"
            )
        if event.known_at > as_of:
            raise CatalystStaleKnownAtError(
                detail=(
                    f"known_at_after_as_of:{event.source.source_event_id or event.headline[:64]}"
                )
            )

        rule = classify_news_event(event, config)
        record_id = build_catalyst_record_id(event)
        source_identity = declared_source_identity(event)
        if source_identity is not None:
            prior_id = source_identity_to_record_id.get(source_identity)
            if prior_id is not None and prior_id != record_id:
                raise CatalystIdentityConflictError(
                    detail=(f"source_identity_conflict:{source_identity[0]}:{source_identity[1]}")
                )
            source_identity_to_record_id[source_identity] = record_id

        if record_id in by_record_id:
            # Exact semantic duplicate — collapse to the first occurrence.
            continue

        by_record_id[record_id] = CatalystRecord(
            catalyst_record_id=record_id,
            source_event_id=event.source.source_event_id,
            source_content_fingerprint=record_id,
            instrument_key=event.instrument.instrument_key,
            local_symbol=event.instrument.local_symbol,
            catalyst_type=rule.catalyst_type,
            event_time=event.occurred_at,
            known_at=event.known_at,
            as_of=as_of,
            source_provider=event.source.provider,
            rule_id=rule.rule_id,
        )

    # Preserve insertion order of unique record ids before sorting.
    return list(by_record_id.values())


def _config_fingerprint(config: CatalystConfig) -> str:
    return strategy_sha256(config.model_dump(mode="python"))


def _input_fingerprint(request: CatalystNormalizationRequest) -> str:
    return strategy_sha256(
        {
            "as_of": request.as_of,
            "config": request.config.model_dump(mode="python"),
            "events": [event.model_dump(mode="python") for event in request.events],
            "ordering_policy_id": (
                ORDERING_POLICY_KNOWN_AT_ASC_EVENT_TIME_ASC_TYPE_ASC_INSTRUMENT_KEY_ASC_ID_ASC
            ),
        }
    )
