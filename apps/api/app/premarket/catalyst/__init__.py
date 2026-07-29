"""Catalyst Foundation public exports."""

from __future__ import annotations

from app.premarket.catalyst.engine import normalize_catalysts, normalize_catalysts_from_parts
from app.premarket.catalyst.identity import build_catalyst_record_id, declared_source_identity
from app.premarket.catalyst.models import (
    CatalystClassificationRule,
    CatalystCollection,
    CatalystConfig,
    CatalystNormalizationRequest,
    CatalystProvenance,
    CatalystRecord,
)
from app.premarket.catalyst.normalize import coerce_news_events
from app.premarket.catalyst.ordering import (
    ORDERING_POLICY_KNOWN_AT_ASC_EVENT_TIME_ASC_TYPE_ASC_INSTRUMENT_KEY_ASC_ID_ASC,
    UNLINKED_INSTRUMENT_KEY_SENTINEL,
    catalyst_sort_key,
)

__all__ = [
    "ORDERING_POLICY_KNOWN_AT_ASC_EVENT_TIME_ASC_TYPE_ASC_INSTRUMENT_KEY_ASC_ID_ASC",
    "UNLINKED_INSTRUMENT_KEY_SENTINEL",
    "CatalystClassificationRule",
    "CatalystCollection",
    "CatalystConfig",
    "CatalystNormalizationRequest",
    "CatalystProvenance",
    "CatalystRecord",
    "build_catalyst_record_id",
    "catalyst_sort_key",
    "coerce_news_events",
    "declared_source_identity",
    "normalize_catalysts",
    "normalize_catalysts_from_parts",
]
