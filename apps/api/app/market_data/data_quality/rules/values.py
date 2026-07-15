"""Value-integrity quality rules."""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal

from app.market_data.data_quality.models import (
    QualityRuleId,
    QualityRuleResult,
    QualitySeverity,
)
from app.market_data.data_quality.policy import QualityPolicy
from app.market_data.envelope import CanonicalMarketEvent
from app.market_data.events.bar import BarEvent
from app.market_data.events.fundamental import FundamentalEvent
from app.market_data.events.macro import MacroEvent
from app.market_data.events.quote import QuoteEvent
from app.market_data.events.trade import TradeEvent


def evaluate(event: CanonicalMarketEvent, policy: QualityPolicy) -> tuple[QualityRuleResult, ...]:
    return (
        _invalid_ohlc(event, policy),
        _crossed_quote(event, policy),
        _negative_quantity(event, policy),
        _invalid_price(event, policy),
    )


def _invalid_ohlc(event: CanonicalMarketEvent, policy: QualityPolicy) -> QualityRuleResult:
    failed = False
    if isinstance(event, BarEvent):
        failed = (
            event.high < event.low
            or event.high < max(event.open, event.close)
            or event.low > min(event.open, event.close)
        )
    return QualityRuleResult(
        rule_id=QualityRuleId.VALUE_INVALID_OHLC,
        passed=not failed,
        severity=policy.severity_for(
            QualityRuleId.VALUE_INVALID_OHLC,
            QualitySeverity.ERROR if failed else QualitySeverity.INFO,
        ),
        reason_code="value_ohlc_valid" if not failed else "value_ohlc_invalid",
    )


def _crossed_quote(event: CanonicalMarketEvent, policy: QualityPolicy) -> QualityRuleResult:
    failed = isinstance(event, QuoteEvent) and event.bid_price > event.ask_price
    return QualityRuleResult(
        rule_id=QualityRuleId.VALUE_CROSSED_QUOTE,
        passed=not failed,
        severity=policy.severity_for(
            QualityRuleId.VALUE_CROSSED_QUOTE,
            QualitySeverity.ERROR if failed else QualitySeverity.INFO,
        ),
        reason_code="value_quote_not_crossed" if not failed else "value_quote_crossed",
    )


def _negative_quantity(event: CanonicalMarketEvent, policy: QualityPolicy) -> QualityRuleResult:
    quantities: list[Decimal] = []
    match event:
        case TradeEvent():
            quantities.append(event.size)
        case QuoteEvent():
            quantities.extend([event.bid_size, event.ask_size])
        case BarEvent():
            quantities.append(event.volume)
    failed = any(value < 0 for value in quantities)
    return QualityRuleResult(
        rule_id=QualityRuleId.VALUE_NEGATIVE_QUANTITY,
        passed=not failed,
        severity=policy.severity_for(
            QualityRuleId.VALUE_NEGATIVE_QUANTITY,
            QualitySeverity.ERROR if failed else QualitySeverity.INFO,
        ),
        reason_code="value_quantities_non_negative" if not failed else "value_quantity_negative",
    )


def _invalid_price(event: CanonicalMarketEvent, policy: QualityPolicy) -> QualityRuleResult:
    prices: Iterable[Decimal] = ()
    match event:
        case TradeEvent():
            prices = (event.price,)
        case QuoteEvent():
            prices = (event.bid_price, event.ask_price)
        case BarEvent():
            prices = (event.open, event.high, event.low, event.close)
        case FundamentalEvent():
            prices = (event.value,)
        case MacroEvent():
            prices = (event.value,)
    failed = any((not value.is_finite()) or value <= 0 for value in prices)
    if isinstance(event, (FundamentalEvent, MacroEvent)):
        failed = any(not value.is_finite() for value in prices)
    return QualityRuleResult(
        rule_id=QualityRuleId.VALUE_INVALID_PRICE,
        passed=not failed,
        severity=policy.severity_for(
            QualityRuleId.VALUE_INVALID_PRICE,
            QualitySeverity.ERROR if failed else QualitySeverity.INFO,
        ),
        reason_code="value_prices_valid" if not failed else "value_price_invalid",
    )
