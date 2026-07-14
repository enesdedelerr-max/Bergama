"""Immutable shared models for trading-engine metadata and health."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.trading.shared.enums import EngineType, SupportedAssetClass, SupportedTimeframe


class EngineCapabilities(BaseModel):
    """Declared engine capabilities — no strategy semantics."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    asset_classes: tuple[SupportedAssetClass, ...] = ()
    timeframes: tuple[SupportedTimeframe, ...] = ()
    supports_paper: bool = True
    supports_live: bool = False


class EngineMetadata(BaseModel):
    """Static identity and capability metadata for a trading engine."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    engine_id: str = Field(min_length=1)
    engine_name: str = Field(min_length=1)
    engine_type: EngineType
    version: str = Field(default="0.0.0", min_length=1)
    description: str = ""
    capabilities: EngineCapabilities = Field(default_factory=EngineCapabilities)


class EngineHealth(BaseModel):
    """Lightweight engine health snapshot returned by ``TradingEngine.health``."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    engine_id: str = Field(min_length=1)
    healthy: bool
    message: str = ""
