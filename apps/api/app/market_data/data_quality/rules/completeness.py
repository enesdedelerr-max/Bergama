"""Completeness quality rules."""

from __future__ import annotations

from app.market_data.data_quality.models import (
    QualityRuleId,
    QualityRuleResult,
    QualitySeverity,
)
from app.market_data.data_quality.policy import QualityPolicy
from app.market_data.envelope import CanonicalMarketEvent
from app.market_data.events.bar import BarEvent
from app.market_data.events.filing import FilingEvent
from app.market_data.events.fundamental import FundamentalEvent
from app.market_data.events.news import NewsEvent
from app.market_data.events.quote import QuoteEvent


def evaluate(event: CanonicalMarketEvent, policy: QualityPolicy) -> tuple[QualityRuleResult, ...]:
    return (
        _missing_value(event, policy),
        _incomplete_flag(event, policy),
    )


def _missing_value(event: CanonicalMarketEvent, policy: QualityPolicy) -> QualityRuleResult:
    missing: list[str] = []
    match event:
        case QuoteEvent():
            for field_name in ("bid_price", "ask_price", "bid_size", "ask_size"):
                if getattr(event, field_name) is None:
                    missing.append(field_name)
        case BarEvent():
            for field_name in ("open", "high", "low", "close", "volume"):
                if getattr(event, field_name) is None:
                    missing.append(field_name)
        case FundamentalEvent():
            for field_name in ("metric_code", "period", "value"):
                if getattr(event, field_name) in {None, ""}:
                    missing.append(field_name)
        case FilingEvent():
            for field_name in ("accession_number", "form_type"):
                if getattr(event, field_name) in {None, ""}:
                    missing.append(field_name)
        case NewsEvent():
            if not event.headline:
                missing.append("headline")
    passed = not missing
    return QualityRuleResult(
        rule_id=QualityRuleId.COMPLETENESS_MISSING_VALUE,
        passed=passed,
        severity=policy.severity_for(
            QualityRuleId.COMPLETENESS_MISSING_VALUE,
            QualitySeverity.ERROR if not passed else QualitySeverity.INFO,
        ),
        reason_code="completeness_required_values_present"
        if passed
        else "completeness_required_value_missing",
        measured_value=",".join(missing) if missing else None,
    )


def _incomplete_flag(event: CanonicalMarketEvent, policy: QualityPolicy) -> QualityRuleResult:
    flagged = event.quality.is_incomplete
    return QualityRuleResult(
        rule_id=QualityRuleId.COMPLETENESS_INCOMPLETE_FLAG,
        passed=not flagged,
        severity=policy.severity_for(
            QualityRuleId.COMPLETENESS_INCOMPLETE_FLAG,
            QualitySeverity.WARNING if flagged else QualitySeverity.INFO,
        ),
        reason_code="completeness_not_flagged_incomplete"
        if not flagged
        else "completeness_flagged_incomplete",
        measured_value="true" if flagged else None,
    )
