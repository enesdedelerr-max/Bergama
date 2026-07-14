"""Trading domain package — multi-horizon engine foundations (Issue #211).

Architecture only. No strategy, market-data, execution, or portfolio logic.
"""

from __future__ import annotations

from app.trading.engines.base import TradingEngine
from app.trading.engines.factory import TradingEngineFactory
from app.trading.engines.registry import TradingEngineRegistry
from app.trading.shared.enums import EngineType, SupportedAssetClass, SupportedTimeframe
from app.trading.shared.models import EngineCapabilities, EngineHealth, EngineMetadata

__all__ = [
    "EngineCapabilities",
    "EngineHealth",
    "EngineMetadata",
    "EngineType",
    "SupportedAssetClass",
    "SupportedTimeframe",
    "TradingEngine",
    "TradingEngineFactory",
    "TradingEngineRegistry",
]
