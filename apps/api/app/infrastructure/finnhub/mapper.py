"""Map Finnhub REST responses to #301 ReferenceDataEvent / FundamentalEvent."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal

from app.core.logging import get_logger, structured_extra
from app.infrastructure.finnhub.errors import FinnhubMappingFailedError
from app.infrastructure.finnhub.schemas import FinnhubBasicFinancials, FinnhubCompanyProfile2
from app.market_data.enums import AdjustmentState
from app.market_data.events.fundamental import FundamentalEvent
from app.market_data.events.reference import ReferenceDataEvent
from app.market_data.identity import InstrumentId
from app.market_data.money import require_finite_decimal
from app.market_data.quality import DataQualityFlags
from app.market_data.serialization import CANONICAL_MARKET_SCHEMA_VERSION
from app.market_data.source import SourceReference

logger = get_logger(__name__)

PROVIDER_SCHEMA_VERSION = "v1"
PeriodKind = Literal["ttm", "annual", "snapshot"]
UnitKind = Literal["ratio", "percent", "per_share", "shares", "currency"]


@dataclass(frozen=True, slots=True)
class MetricDefinition:
    """Explicit Finnhub metric semantics for #304A whitelist."""

    period: PeriodKind
    unit: UnitKind


# Closed whitelist: Finnhub metric codes only — no global ontology.
METRIC_DEFINITIONS: dict[str, MetricDefinition] = {
    # Valuation ratios
    "peTTM": MetricDefinition(period="ttm", unit="ratio"),
    "peAnnual": MetricDefinition(period="annual", unit="ratio"),
    "pbAnnual": MetricDefinition(period="annual", unit="ratio"),
    "psTTM": MetricDefinition(period="ttm", unit="ratio"),
    "psAnnual": MetricDefinition(period="annual", unit="ratio"),
    # Profitability
    "roeTTM": MetricDefinition(period="ttm", unit="percent"),
    "roaTTM": MetricDefinition(period="ttm", unit="percent"),
    "netProfitMarginTTM": MetricDefinition(period="ttm", unit="percent"),
    "grossMarginTTM": MetricDefinition(period="ttm", unit="percent"),
    "operatingMarginTTM": MetricDefinition(period="ttm", unit="percent"),
    # Liquidity
    "currentRatioAnnual": MetricDefinition(period="annual", unit="ratio"),
    "quickRatioAnnual": MetricDefinition(period="annual", unit="ratio"),
    # Leverage
    "totalDebt/totalEquityAnnual": MetricDefinition(period="annual", unit="ratio"),
    "longTermDebt/equityAnnual": MetricDefinition(period="annual", unit="ratio"),
    # Growth percentages
    "revenueGrowthTTMYoy": MetricDefinition(period="ttm", unit="percent"),
    "epsGrowthTTMYoy": MetricDefinition(period="ttm", unit="percent"),
    # Per-share
    "epsTTM": MetricDefinition(period="ttm", unit="per_share"),
    "epsAnnual": MetricDefinition(period="annual", unit="per_share"),
    "bookValuePerShareAnnual": MetricDefinition(period="annual", unit="per_share"),
    # Snapshot
    "marketCapitalization": MetricDefinition(period="snapshot", unit="currency"),
    "shareOutstanding": MetricDefinition(period="snapshot", unit="shares"),
}

SUPPORTED_METRICS: frozenset[str] = frozenset(METRIC_DEFINITIONS)


def decimal_from_provider(value: object, *, field_name: str) -> Decimal:
    return require_finite_decimal(str(value), field_name=field_name)


def _attr(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _source(
    *,
    symbol: str,
    endpoint: str,
    observed_at: datetime,
    request_id: str | None,
) -> SourceReference:
    extras: dict[str, str] = {
        "endpoint": endpoint,
        "provider_schema_version": PROVIDER_SCHEMA_VERSION,
        "timestamp_policy": "connector_observation_clock",
        "observed_at": observed_at.isoformat().replace("+00:00", "Z"),
    }
    if request_id:
        # Conservative provenance key (see TD-MARKET-DATA-002). Do not store secrets.
        extras["http_request_id"] = request_id[:256]
    return SourceReference(
        provider="finnhub",
        source_symbol=symbol,
        source_event_id=f"{endpoint}:{symbol}:{extras['observed_at']}",
        extras=extras,
    )


def map_reference_event(
    profile: FinnhubCompanyProfile2,
    *,
    instrument: InstrumentId,
    symbol: str,
    observed_at: datetime,
    request_id: str | None,
    caller_currency: str | None = None,
) -> ReferenceDataEvent:
    if profile.is_empty():
        raise FinnhubMappingFailedError("finnhub company profile is empty")

    attributes: dict[str, str] = {}
    for key, raw in (
        ("country", profile.country),
        ("provider_currency", profile.currency),
        ("listed_exchange_text", profile.exchange),
        ("ipo_date", profile.ipo),
        ("finnhub_industry", profile.finnhub_industry),
        ("phone", profile.phone),
        ("web_url", profile.weburl),
    ):
        text = _attr(raw)
        if text is not None:
            attributes[key] = text[:512]

    if profile.market_capitalization is not None:
        try:
            mcap = decimal_from_provider(
                profile.market_capitalization,
                field_name="marketCapitalization",
            )
            attributes["market_capitalization"] = str(mcap)
        except ValueError as exc:
            raise FinnhubMappingFailedError("invalid marketCapitalization") from exc
    if profile.share_outstanding is not None:
        try:
            shares = decimal_from_provider(
                profile.share_outstanding,
                field_name="shareOutstanding",
            )
            attributes["share_outstanding"] = str(shares)
        except ValueError as exc:
            raise FinnhubMappingFailedError("invalid shareOutstanding") from exc

    # logo omitted: not fetched; no safe fetch in-scope; avoid unbounded remote assets.

    source_symbol = _attr(profile.ticker) or symbol
    currency = caller_currency.strip().upper() if caller_currency else None

    return ReferenceDataEvent(
        schema_version=CANONICAL_MARKET_SCHEMA_VERSION,
        instrument=instrument,
        source=_source(
            symbol=source_symbol,
            endpoint="stock/profile2",
            observed_at=observed_at,
            request_id=request_id,
        ),
        quality=DataQualityFlags(),
        adjustment_state=AdjustmentState.UNADJUSTED,
        occurred_at=observed_at,
        effective_at=observed_at,
        known_at=observed_at,
        ingested_at=observed_at,
        currency=currency,
        venue=None,
        name=_attr(profile.name),
        exchange_mic=None,
        isin=None,
        cusip=None,
        status=None,
        attributes=attributes,
        metadata={},
    )


def map_fundamental_events(
    payload: FinnhubBasicFinancials,
    *,
    instrument: InstrumentId,
    symbol: str,
    observed_at: datetime,
    request_id: str | None,
    caller_currency: str | None = None,
) -> tuple[FundamentalEvent, ...]:
    source_symbol = _attr(payload.symbol) or symbol
    currency = caller_currency.strip().upper() if caller_currency else None
    events: list[FundamentalEvent] = []

    for key in sorted(payload.metric.keys()):
        if key not in SUPPORTED_METRICS:
            logger.debug(
                "finnhub unsupported metric ignored",
                extra=structured_extra(
                    event="finnhub.metric.ignored",
                    source="finnhub_mapper",
                    metric_key=str(key)[:64],
                ),
            )
            continue

        raw_value = payload.metric[key]
        if raw_value is None:
            continue

        definition = METRIC_DEFINITIONS[key]
        if definition.unit == "currency" and currency is None:
            logger.debug(
                "finnhub currency metric skipped without caller currency",
                extra=structured_extra(
                    event="finnhub.metric.skipped_no_currency",
                    source="finnhub_mapper",
                    metric_key=key,
                ),
            )
            continue

        try:
            value = decimal_from_provider(raw_value, field_name=key)
        except ValueError as exc:
            raise FinnhubMappingFailedError(f"invalid value for supported metric {key}") from exc

        unit = definition.unit
        event_currency = currency if unit == "currency" else None

        events.append(
            FundamentalEvent(
                schema_version=CANONICAL_MARKET_SCHEMA_VERSION,
                instrument=instrument,
                source=_source(
                    symbol=source_symbol,
                    endpoint="stock/metric",
                    observed_at=observed_at,
                    request_id=request_id,
                ),
                quality=DataQualityFlags(),
                adjustment_state=AdjustmentState.UNADJUSTED,
                occurred_at=observed_at,
                effective_at=observed_at,
                known_at=observed_at,
                ingested_at=observed_at,
                currency=event_currency,
                venue=None,
                metric_code=key[:64],
                period=definition.period,
                value=value,
                unit=unit,
                metadata={},
            )
        )

    return tuple(events)
