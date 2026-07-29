"""Explicit config-only catalyst classification."""

from __future__ import annotations

from app.market_data.events.news import NewsEvent
from app.premarket.catalyst.models import CatalystClassificationRule, CatalystConfig
from app.premarket.errors import CatalystClassificationError


def classify_news_event(
    event: NewsEvent,
    config: CatalystConfig,
) -> CatalystClassificationRule:
    """Match the lowest-priority classification rule by topic.

    Matching is case-insensitive against ``NewsEvent.topics``. Events that match
    no configured rule fail closed.
    """
    event_topics = {topic.strip().lower() for topic in event.topics if topic.strip()}
    rules = sorted(
        config.classification_rules,
        key=lambda rule: (rule.rule_priority, rule.rule_id),
    )
    for rule in rules:
        if any(topic in event_topics for topic in rule.match_topics):
            return rule
    raise CatalystClassificationError(
        detail=f"unclassified_event:{event.source.source_event_id or event.headline[:64]}"
    )
