"""Optional Strategy Engine state protocol."""

from __future__ import annotations

from typing import Any, Protocol

from app.market_data.identity import InstrumentId


class StrategyState(Protocol):
    """Optional bounded state partitioned by strategy instance and instrument."""

    strategy_instance_id: str
    instrument_id: InstrumentId

    def snapshot(self) -> dict[str, Any]: ...

    def restore(self, snapshot: dict[str, Any]) -> None: ...
