"""Shared trading-engine contracts.

Concrete horizon packages implement ``TradingEngine``. This module owns the
abstract boundary only — no strategy, market-data, or execution behavior.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.trading.shared.enums import EngineType, SupportedAssetClass, SupportedTimeframe
from app.trading.shared.models import EngineHealth, EngineMetadata


class TradingEngine(ABC):
    """Stable multi-horizon trading engine contract.

    Engines are registered explicitly. There is no auto-discovery and no
    runtime wiring in Issue #211.
    """

    @property
    @abstractmethod
    def engine_id(self) -> str:
        """Stable unique identifier for this engine instance/type."""

    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Human-readable engine name."""

    @property
    @abstractmethod
    def engine_type(self) -> EngineType:
        """Horizon/category this engine belongs to."""

    @property
    @abstractmethod
    def supported_assets(self) -> tuple[SupportedAssetClass, ...]:
        """Asset classes this engine supports."""

    @property
    @abstractmethod
    def supported_timeframes(self) -> tuple[SupportedTimeframe, ...]:
        """Timeframes this engine supports."""

    @abstractmethod
    async def initialize(self) -> None:
        """Perform one-time engine initialization."""

    @abstractmethod
    async def shutdown(self) -> None:
        """Release engine resources. Must be idempotent in implementations."""

    @abstractmethod
    async def health(self) -> EngineHealth:
        """Return a lightweight health snapshot for this engine."""

    @abstractmethod
    def metadata(self) -> EngineMetadata:
        """Return static engine identity and capability metadata."""
