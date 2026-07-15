"""Explicit in-code strategy registry."""

from __future__ import annotations

from collections.abc import Callable

from app.strategy.config import StrategyConfig
from app.strategy.errors import StrategyAlreadyRegisteredError, StrategyNotFoundError
from app.strategy.identity import StrategyIdentity
from app.strategy.protocol import Strategy

StrategyFactory = Callable[[StrategyIdentity, StrategyConfig], Strategy]


class StrategyRegistry:
    """Instance-scoped registry. No globals, auto-discovery, or arbitrary imports."""

    def __init__(self) -> None:
        self._entries: dict[str, StrategyFactory] = {}

    def register(self, strategy_id: str, factory: StrategyFactory) -> None:
        key = strategy_id.strip()
        StrategyIdentity(
            strategy_id=key,
            strategy_version="0",
            strategy_instance_id=f"{key}:registry",
        )
        if key in self._entries:
            raise StrategyAlreadyRegisteredError(detail=key)
        self._entries[key] = factory

    def unregister(self, strategy_id: str) -> None:
        key = strategy_id.strip()
        if key not in self._entries:
            raise StrategyNotFoundError(detail=key)
        del self._entries[key]

    def create(self, identity: StrategyIdentity, config: StrategyConfig) -> Strategy:
        try:
            factory = self._entries[identity.strategy_id]
        except KeyError as exc:
            raise StrategyNotFoundError(detail=identity.strategy_id) from exc
        return factory(identity, config)

    def list_strategy_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._entries))

    def exists(self, strategy_id: str) -> bool:
        return strategy_id.strip() in self._entries
