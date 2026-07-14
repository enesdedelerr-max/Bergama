"""Map Benzinga news items to #301 NewsEvent (Issue #304D)."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

from app.infrastructure.benzinga.errors import BenzingaMappingFailedError
from app.infrastructure.benzinga.schemas import BenzingaNewsItem
from app.market_data.enums import AdjustmentState
from app.market_data.events.news import NewsEvent
from app.market_data.identity import InstrumentId
from app.market_data.quality import DataQualityFlags
from app.market_data.serialization import CANONICAL_MARKET_SCHEMA_VERSION
from app.market_data.source import SourceReference

PROVIDER = "benzinga"
PROVIDER_SCHEMA_VERSION = "v1"
TIME_POLICY = "benzinga_created_as_occurred_effective_updated_in_revision_id"
MAX_SUMMARY = 4096
MAX_TOPICS = 32
ALLOWED_URL_HOSTS = frozenset(
    {
        "benzinga.com",
        "www.benzinga.com",
        "m.benzinga.com",
    }
)


def normalize_ticker_for_lookup(ticker: str) -> str:
    """Narrow provider-specific lookup normalization: trim + uppercase."""
    return ticker.strip().upper()


def unique_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def parse_benzinga_timestamp(value: str, *, field_name: str) -> datetime:
    text = value.strip()
    if not text:
        raise BenzingaMappingFailedError(f"missing {field_name}")
    try:
        parsed = parsedate_to_datetime(text)
    except (TypeError, ValueError, IndexError) as exc:
        raise BenzingaMappingFailedError(f"invalid {field_name}: {value!r}") from exc
    if parsed.tzinfo is None:
        raise BenzingaMappingFailedError(f"{field_name} must be timezone-aware: {value!r}")
    return parsed.astimezone(UTC)


def format_updated_iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def validate_article_url(url: str | None) -> str | None:
    if url is None:
        return None
    text = url.strip()
    if not text:
        return None
    parsed = urlparse(text)
    if parsed.scheme not in {"http", "https"}:
        raise BenzingaMappingFailedError(f"unsupported article URL scheme: {text!r}")
    if parsed.username or parsed.password:
        raise BenzingaMappingFailedError("article URL must not include credentials")
    host = (parsed.hostname or "").lower()
    if host not in ALLOWED_URL_HOSTS:
        raise BenzingaMappingFailedError(f"article URL host not allowed: {host!r}")
    # Rebuild without fragment to avoid secret-bearing fragments.
    cleaned = f"{parsed.scheme}://{host}{parsed.path or ''}"
    if parsed.query:
        cleaned = f"{cleaned}?{parsed.query}"
    if any(token in cleaned.lower() for token in ("token=", "api_key=", "apikey=")):
        raise BenzingaMappingFailedError("article URL must not contain credentials")
    if len(cleaned) > 1024:
        raise BenzingaMappingFailedError("article URL exceeds canonical bound")
    return cleaned


def extract_provider_tickers(item: BenzingaNewsItem) -> list[str]:
    originals: list[str] = []
    for stock in item.stocks:
        if stock.name is None:
            continue
        name = stock.name.strip()
        if name:
            originals.append(name)
    return unique_preserve_order(originals)


def build_topics(item: BenzingaNewsItem) -> tuple[str, ...]:
    names: list[str] = []
    for channel in item.channels:
        if channel.name and channel.name.strip():
            names.append(channel.name.strip())
    for tag in item.tags:
        if tag.name and tag.name.strip():
            names.append(tag.name.strip())
    return tuple(unique_preserve_order(names)[:MAX_TOPICS])


def resolve_instruments(
    *,
    provider_tickers: list[str],
    ticker_to_instrument: Mapping[str, InstrumentId],
    anchor_instrument: InstrumentId | None,
) -> list[tuple[InstrumentId, str | None]]:
    """Return (instrument, source_symbol) emission units."""
    lookup = {
        normalize_ticker_for_lookup(k): v for k, v in ticker_to_instrument.items() if k.strip()
    }
    mapped: list[tuple[InstrumentId, str | None]] = []
    seen_keys: set[str] = set()
    for original in provider_tickers:
        key = normalize_ticker_for_lookup(original)
        instrument = lookup.get(key)
        if instrument is None:
            continue
        if instrument.instrument_key in seen_keys:
            continue
        seen_keys.add(instrument.instrument_key)
        mapped.append((instrument, original))

    if mapped:
        return mapped
    if anchor_instrument is not None:
        return [(anchor_instrument, provider_tickers[0] if provider_tickers else None)]
    if provider_tickers:
        raise BenzingaMappingFailedError(
            "provider tickers present but none mapped and anchor_instrument missing"
        )
    raise BenzingaMappingFailedError("story has no tickers and anchor_instrument is required")


def map_news_item(
    item: BenzingaNewsItem,
    *,
    ticker_to_instrument: Mapping[str, InstrumentId],
    anchor_instrument: InstrumentId | None,
    observed_at: datetime,
    endpoint_ref: str,
) -> tuple[NewsEvent, ...]:
    """Map one provider story into one or more NewsEvent instances."""
    try:
        created = parse_benzinga_timestamp(item.created, field_name="created")
        updated = parse_benzinga_timestamp(item.updated, field_name="updated")
    except BenzingaMappingFailedError:
        raise
    except Exception as exc:
        raise BenzingaMappingFailedError("failed to parse story timestamps") from exc

    title = item.title.strip()
    if not title:
        raise BenzingaMappingFailedError("story title is required")
    if len(title) > 1024:
        title = title[:1024]

    summary: str | None = None
    if item.teaser is not None:
        teaser = item.teaser.strip()
        if teaser:
            summary = teaser[:MAX_SUMMARY]

    url_ref = validate_article_url(item.url)
    topics = build_topics(item)
    provider_tickers = extract_provider_tickers(item)
    instruments = resolve_instruments(
        provider_tickers=provider_tickers,
        ticker_to_instrument=ticker_to_instrument,
        anchor_instrument=anchor_instrument,
    )

    source_event_id = f"{item.id}:{format_updated_iso(updated)}"
    ticker_csv = ",".join(provider_tickers)
    if len(ticker_csv) > 512:
        ticker_csv = ticker_csv[:512]

    metadata: dict[str, str] = {
        "provider_schema_version": PROVIDER_SCHEMA_VERSION,
        "time_policy": TIME_POLICY,
        "updated_at": format_updated_iso(updated),
        "story_id": str(item.id),
        "display_content_policy": "no_body",
    }
    if item.author and item.author.strip():
        metadata["author"] = item.author.strip()[:512]
    if item.original_id is not None:
        metadata["original_id"] = str(item.original_id)
    if item.importance_rank is not None:
        metadata["importance_rank"] = str(item.importance_rank)
    if ticker_csv:
        metadata["provider_tickers"] = ticker_csv
    # Explicitly record that body was ignored if present.
    if item.body is not None and item.body.strip():
        metadata["body_omitted"] = "true"

    events: list[NewsEvent] = []
    for instrument, source_symbol in instruments:
        source = SourceReference(
            provider=PROVIDER,
            source_symbol=source_symbol,
            source_instrument_id=None,
            source_event_id=source_event_id,
            source_payload_ref=endpoint_ref[:512],
            extras={
                "story_id": str(item.id),
                "updated_at": format_updated_iso(updated),
            },
        )
        try:
            event = NewsEvent(
                schema_version=CANONICAL_MARKET_SCHEMA_VERSION,
                instrument=instrument,
                source=source,
                quality=DataQualityFlags(),
                adjustment_state=AdjustmentState.UNADJUSTED,
                occurred_at=created,
                effective_at=created,
                known_at=observed_at,
                ingested_at=observed_at,
                currency=None,
                venue=None,
                metadata=metadata,
                headline=title,
                summary=summary,
                url_ref=url_ref,
                language=None,
                topics=topics,
            )
        except ValueError as exc:
            raise BenzingaMappingFailedError(
                f"canonical NewsEvent validation failed: {exc}"
            ) from exc
        events.append(event)
    return tuple(events)
