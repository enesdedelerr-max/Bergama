"""UTC / point-in-time timestamp validation."""

from __future__ import annotations

from datetime import UTC, datetime

from app.market_data.quality import DataQualityFlags


def require_utc_aware(value: datetime, *, field_name: str) -> datetime:
    """Require timezone-aware datetime and normalize to UTC."""
    if value.tzinfo is None:
        msg = f"{field_name} must be timezone-aware UTC"
        raise ValueError(msg)
    return value.astimezone(UTC)


def validate_point_in_time_order(
    *,
    occurred_at: datetime,
    effective_at: datetime,
    known_at: datetime,
    ingested_at: datetime,
    quality: DataQualityFlags,
) -> None:
    """Enforce PIT ordering and explicit late-arrival / revision rules.

    Rules:
    - ``occurred_at <= known_at`` (knowledge cannot precede the event).
    - ``effective_at`` must be timezone-aware UTC (ordering vs occurred is free).
    - ``known_at <= ingested_at`` unless ``quality.is_late`` is true
      (late-arrival / clock-skew semantics must be declared).
    - Revisions require ``quality.is_revision`` and ``revision_of_event_id``.
    """
    if occurred_at > known_at:
        msg = "occurred_at must be <= known_at"
        raise ValueError(msg)
    if known_at > ingested_at and not quality.is_late:
        msg = (
            "known_at must be <= ingested_at unless DataQualityFlags.is_late "
            "declares late-arrival semantics"
        )
        raise ValueError(msg)
    if quality.is_revision and not quality.revision_of_event_id:
        msg = "revisions require quality.revision_of_event_id"
        raise ValueError(msg)
    if quality.revision_of_event_id and not quality.is_revision:
        msg = "revision_of_event_id requires quality.is_revision=true"
        raise ValueError(msg)
    _ = effective_at  # validated as UTC by caller; free vs occurred_at
