"""Trading-engine factory — creates engines from an explicit registry.

No AppContainer wiring in Issue #211. Callers supply the registry.
"""

from __future__ import annotations

from app.trading.engines.registry import EngineNotFoundError, TradingEngineRegistry
from app.trading.shared.contracts import TradingEngine
from app.trading.shared.models import EngineMetadata


class TradingEngineFactory:
    """Instantiate registered engines by ``engine_id``."""

    def __init__(self, registry: TradingEngineRegistry) -> None:
        self._registry = registry

    def create_engine(self, engine_id: str) -> TradingEngine:
        """Create a new engine instance for the given id."""
        try:
            _metadata, factory = self._registry.get(engine_id)
        except EngineNotFoundError:
            raise
        return factory()

    def list_available(self) -> tuple[EngineMetadata, ...]:
        """Return metadata for all registered engines (deterministic order)."""
        return self._registry.list()
