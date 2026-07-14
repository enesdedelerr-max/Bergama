"""Unit tests for TradingEngineRegistry and TradingEngineFactory."""

from __future__ import annotations

import pytest
from app.trading.engines.factory import TradingEngineFactory
from app.trading.engines.registry import (
    EngineAlreadyRegisteredError,
    EngineNotFoundError,
    TradingEngineRegistry,
)
from app.trading.shared.contracts import TradingEngine
from app.trading.shared.enums import EngineType, SupportedAssetClass, SupportedTimeframe
from app.trading.shared.models import EngineCapabilities, EngineHealth, EngineMetadata


class _StubEngine(TradingEngine):
    """Test-only concrete engine — not a production implementation."""

    def __init__(self, *, engine_id: str, engine_type: EngineType) -> None:
        self._engine_id = engine_id
        self._engine_type = engine_type
        self._name = f"Stub {engine_id}"

    @property
    def engine_id(self) -> str:
        return self._engine_id

    @property
    def engine_name(self) -> str:
        return self._name

    @property
    def engine_type(self) -> EngineType:
        return self._engine_type

    @property
    def supported_assets(self) -> tuple[SupportedAssetClass, ...]:
        return (SupportedAssetClass.EQUITY,)

    @property
    def supported_timeframes(self) -> tuple[SupportedTimeframe, ...]:
        return (SupportedTimeframe.MINUTE_5,)

    async def initialize(self) -> None:
        return None

    async def shutdown(self) -> None:
        return None

    async def health(self) -> EngineHealth:
        return EngineHealth(engine_id=self._engine_id, healthy=True, message="ok")

    def metadata(self) -> EngineMetadata:
        return EngineMetadata(
            engine_id=self._engine_id,
            engine_name=self._name,
            engine_type=self._engine_type,
            capabilities=EngineCapabilities(
                asset_classes=self.supported_assets,
                timeframes=self.supported_timeframes,
            ),
        )


def _metadata(engine_id: str, engine_type: EngineType = EngineType.DAY_TRADING) -> EngineMetadata:
    return EngineMetadata(
        engine_id=engine_id,
        engine_name=f"Stub {engine_id}",
        engine_type=engine_type,
        capabilities=EngineCapabilities(
            asset_classes=(SupportedAssetClass.EQUITY,),
            timeframes=(SupportedTimeframe.MINUTE_5,),
        ),
    )


def test_register_and_exists() -> None:
    registry = TradingEngineRegistry()
    meta = _metadata("day-equity-v1")

    def factory() -> TradingEngine:
        return _StubEngine(engine_id="day-equity-v1", engine_type=EngineType.DAY_TRADING)

    registry.register(meta, factory)
    assert registry.exists("day-equity-v1") is True
    assert registry.exists("missing") is False


def test_duplicate_registration_fails() -> None:
    registry = TradingEngineRegistry()
    meta = _metadata("dup-id")

    def factory() -> TradingEngine:
        return _StubEngine(engine_id="dup-id", engine_type=EngineType.SWING)

    registry.register(meta, factory)
    with pytest.raises(EngineAlreadyRegisteredError):
        registry.register(meta, factory)


def test_lookup_get() -> None:
    registry = TradingEngineRegistry()
    meta = _metadata("swing-1", EngineType.SWING)
    registry.register(meta, lambda: _StubEngine(engine_id="swing-1", engine_type=EngineType.SWING))
    found_meta, factory = registry.get("swing-1")
    assert found_meta.engine_id == "swing-1"
    assert found_meta.engine_type is EngineType.SWING
    engine = factory()
    assert engine.engine_id == "swing-1"


def test_lookup_missing_fails() -> None:
    registry = TradingEngineRegistry()
    with pytest.raises(EngineNotFoundError):
        registry.get("unknown")


def test_list_sorted_by_engine_id() -> None:
    registry = TradingEngineRegistry()
    registry.register(
        _metadata("zebra"),
        lambda: _StubEngine(engine_id="zebra", engine_type=EngineType.CRYPTO),
    )
    registry.register(
        _metadata("alpha"),
        lambda: _StubEngine(engine_id="alpha", engine_type=EngineType.INVESTING),
    )
    ids = [item.engine_id for item in registry.list()]
    assert ids == ["alpha", "zebra"]


def test_unregister_removes_engine() -> None:
    registry = TradingEngineRegistry()
    registry.register(
        _metadata("to-remove"),
        lambda: _StubEngine(engine_id="to-remove", engine_type=EngineType.OPTIONS),
    )
    registry.unregister("to-remove")
    assert registry.exists("to-remove") is False
    with pytest.raises(EngineNotFoundError):
        registry.unregister("to-remove")


def test_no_shared_global_registry_state() -> None:
    a = TradingEngineRegistry()
    b = TradingEngineRegistry()
    a.register(
        _metadata("only-a"),
        lambda: _StubEngine(engine_id="only-a", engine_type=EngineType.FUTURES),
    )
    assert a.exists("only-a") is True
    assert b.exists("only-a") is False


def test_factory_create_and_list_available() -> None:
    registry = TradingEngineRegistry()
    registry.register(
        _metadata("day-1"),
        lambda: _StubEngine(engine_id="day-1", engine_type=EngineType.DAY_TRADING),
    )
    factory = TradingEngineFactory(registry)
    engine = factory.create_engine("day-1")
    assert isinstance(engine, TradingEngine)
    assert engine.engine_id == "day-1"
    assert [m.engine_id for m in factory.list_available()] == ["day-1"]


@pytest.mark.asyncio
async def test_stub_engine_lifecycle_for_contract_surface() -> None:
    engine = _StubEngine(engine_id="lifecycle", engine_type=EngineType.DAY_TRADING)
    await engine.initialize()
    health = await engine.health()
    assert health.healthy is True
    meta = engine.metadata()
    assert meta.engine_id == "lifecycle"
    await engine.shutdown()
