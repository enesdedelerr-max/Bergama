"""Explicit trading-engine type registry.

No auto-discovery. Registration is always explicit and instance-scoped —
there is no process-global registry singleton.
"""

from __future__ import annotations

from collections.abc import Callable

from app.trading.shared.contracts import TradingEngine
from app.trading.shared.models import EngineMetadata

EngineFactoryFn = Callable[[], TradingEngine]


class EngineAlreadyRegisteredError(ValueError):
    """Raised when registering an engine_id that already exists."""

    def __init__(self, engine_id: str) -> None:
        super().__init__(f"engine already registered: {engine_id!r}")
        self.engine_id = engine_id


class EngineNotFoundError(KeyError):
    """Raised when looking up an unknown engine_id."""

    def __init__(self, engine_id: str) -> None:
        super().__init__(engine_id)
        self.engine_id = engine_id


class TradingEngineRegistry:
    """In-memory map of engine_id → (metadata, factory callable)."""

    def __init__(self) -> None:
        self._entries: dict[str, tuple[EngineMetadata, EngineFactoryFn]] = {}

    def register(
        self,
        metadata: EngineMetadata,
        factory: EngineFactoryFn,
    ) -> None:
        """Register an engine factory under ``metadata.engine_id``."""
        engine_id = metadata.engine_id
        if engine_id in self._entries:
            raise EngineAlreadyRegisteredError(engine_id)
        self._entries[engine_id] = (metadata, factory)

    def unregister(self, engine_id: str) -> None:
        """Remove a registered engine. Raises if unknown."""
        if engine_id not in self._entries:
            raise EngineNotFoundError(engine_id)
        del self._entries[engine_id]

    def get(self, engine_id: str) -> tuple[EngineMetadata, EngineFactoryFn]:
        """Return metadata and factory for ``engine_id``."""
        try:
            return self._entries[engine_id]
        except KeyError as exc:
            raise EngineNotFoundError(engine_id) from exc

    def exists(self, engine_id: str) -> bool:
        """Return True when ``engine_id`` is registered."""
        return engine_id in self._entries

    def list(self) -> tuple[EngineMetadata, ...]:
        """Return registered engine metadata sorted by engine_id."""
        return tuple(self._entries[engine_id][0] for engine_id in sorted(self._entries))
