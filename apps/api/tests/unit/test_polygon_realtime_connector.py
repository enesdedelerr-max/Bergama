"""Offline unit/integration tests for Polygon realtime connector (#303)."""

from __future__ import annotations

import asyncio
import importlib.metadata
import json
import logging
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from app.core.clock import FixedClock
from app.core.config import AppSettings
from app.core.container import build_container
from app.core.environment import AppEnvironment
from app.core.polygon_settings import PolygonSettings
from app.core.secrets import SecretSettings
from app.infrastructure.polygon.errors import (
    PolygonMappingFailedError,
    PolygonWebsocketAuthFailedError,
    PolygonWebsocketOverflowError,
    PolygonWebsocketProtocolError,
    PolygonWebsocketReconnectExhaustedError,
)
from app.infrastructure.polygon.realtime import (
    ConnectionState,
    PolygonRealtimeConnector,
    RealtimeStartRequest,
    SymbolRealtimeContext,
)
from app.infrastructure.polygon.ws_mapper import (
    REALTIME_ADJUSTMENT_ASSUMPTION,
    map_ws_minute_bar,
    map_ws_quote,
    map_ws_trade,
)
from app.infrastructure.polygon.ws_schemas import (
    PolygonWsMinuteAggregateMessage,
    PolygonWsQuoteMessage,
    PolygonWsTradeMessage,
    parse_ws_message,
)
from app.infrastructure.polygon.ws_transport import (
    build_auth_frame,
    build_subscribe_frame,
    redact_control_frame,
)
from app.market_data.enums import AdjustmentState, AssetClass
from app.market_data.events.bar import BarEvent
from app.market_data.events.quote import QuoteEvent
from app.market_data.events.trade import TradeEvent
from app.market_data.identity import InstrumentId
from app.market_data.keys import build_deduplication_key, build_idempotency_key
from app.market_data.serialization import market_event_to_envelope, market_event_to_payload
from pydantic import SecretStr, ValidationError
from tests.conftest import VALID_PROD_JWT_SECRET
from tests.support.fake_polygon_websocket import FakePolygonWebSocketTransport

API_KEY = "test-polygon-ws-key-value"
T_MS = 1_704_196_800_000


def _instrument() -> InstrumentId:
    return InstrumentId(
        instrument_key="bergama:equity:us:aapl",
        asset_class=AssetClass.EQUITY,
        local_symbol="AAPL",
        symbol_effective_from=datetime(2020, 1, 1, tzinfo=UTC),
    )


def _settings(**overrides: object) -> PolygonSettings:
    base: dict[str, object] = {
        "enabled": True,
        "websocket_enabled": True,
        "api_key": SecretStr(API_KEY),
        "websocket_max_queue_size": 100,
        "websocket_max_reconnect_attempts": 3,
        "websocket_reconnect_initial_delay_seconds": 0.01,
        "websocket_reconnect_max_delay_seconds": 0.05,
        "websocket_auth_timeout_seconds": 2.0,
    }
    base.update(overrides)
    return PolygonSettings(**base)


def _request(*, channels: tuple[str, ...] = ("T", "Q", "AM")) -> RealtimeStartRequest:
    return RealtimeStartRequest(
        symbols=(
            SymbolRealtimeContext(
                symbol="AAPL",
                instrument=_instrument(),
                currency="USD",
                venue="XNAS",
                channels=channels,  # type: ignore[arg-type]
            ),
        )
    )


class _Sleeper:
    def __init__(self) -> None:
        self.delays: list[float] = []

    async def __call__(self, seconds: float) -> None:
        self.delays.append(seconds)


def test_settings_defaults_and_websocket_validation() -> None:
    defaults = PolygonSettings()
    assert defaults.enabled is False
    assert defaults.websocket_enabled is False
    assert defaults.websocket_url == "wss://socket.polygon.io/stocks"
    with pytest.raises(ValidationError):
        PolygonSettings(
            enabled=False,
            websocket_enabled=True,
            api_key=SecretStr(API_KEY),
        )
    with pytest.raises(ValidationError):
        PolygonSettings(
            enabled=True,
            websocket_enabled=True,
            api_key=SecretStr(API_KEY),
            websocket_url="ws://socket.polygon.io/stocks",
        )


def test_websockets_is_direct_dependency() -> None:
    pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    assert '"websockets==16.1"' in text or "'websockets==16.1'" in text
    assert importlib.metadata.version("websockets") == "16.1"


def test_auth_message_shape_and_redaction() -> None:
    frame = build_auth_frame(API_KEY)
    payload = json.loads(frame)
    assert payload == {"action": "auth", "params": API_KEY}
    redacted = redact_control_frame(frame)
    assert API_KEY not in redacted
    assert "***REDACTED***" in redacted
    assert build_subscribe_frame(["T.AAPL", "Q.AAPL", "AM.AAPL"]) == (
        '{"action":"subscribe","params":"T.AAPL,Q.AAPL,AM.AAPL"}'
    )


def test_subscription_request_deterministic() -> None:
    req = RealtimeStartRequest(
        symbols=(
            SymbolRealtimeContext(
                symbol="msft",
                instrument=_instrument(),
                currency="usd",
                venue="xnas",
                channels=("AM", "T"),
            ),
            SymbolRealtimeContext(
                symbol="AAPL",
                instrument=_instrument(),
                currency="USD",
                venue="XNAS",
                channels=("Q",),
            ),
        )
    )
    assert req.channel_list() == ["AM.MSFT", "T.MSFT", "Q.AAPL"]
    with pytest.raises(ValidationError):
        SymbolRealtimeContext(
            symbol="AAPL",
            instrument=_instrument(),
            currency="USD",
            venue="XNAS",
            channels=("A",),  # type: ignore[arg-type]
        )


@pytest.mark.asyncio
async def test_auth_success_and_subscription_and_mapping(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG)
    clock = FixedClock(datetime(2024, 6, 15, 12, 0, tzinfo=UTC))
    transport = FakePolygonWebSocketTransport()
    sleeper = _Sleeper()
    connector = PolygonRealtimeConnector(
        _settings(),
        clock=clock,
        transport=transport,
        sleeper=sleeper,
    )
    await connector.start(_request())
    await asyncio.sleep(0)  # let handshake begin
    # Wait until streaming.
    for _ in range(50):
        if connector.state is ConnectionState.STREAMING:
            break
        await asyncio.sleep(0.01)
    assert connector.state is ConnectionState.STREAMING
    assert any('"action":"auth"' in f for f in transport.sent_frames)
    assert any(API_KEY in f for f in transport.sent_frames)
    assert API_KEY not in caplog.text
    assert any("T.AAPL,Q.AAPL,AM.AAPL" in f for f in transport.sent_frames)

    transport.push_json(
        [
            {
                "ev": "T",
                "sym": "AAPL",
                "i": "77",
                "x": 4,
                "p": "190.12",
                "s": "10",
                "t": T_MS,
            },
            {
                "ev": "Q",
                "sym": "AAPL",
                "bx": 4,
                "bp": "190.1",
                "bs": "100",
                "ax": 4,
                "ap": "190.2",
                "as": "50",
                "t": T_MS + 1,
            },
            {
                "ev": "AM",
                "sym": "AAPL",
                "o": "10",
                "h": "12",
                "l": "9",
                "c": "11",
                "v": "1000",
                "vw": "10.5",
                "s": T_MS,
                "e": T_MS + 60_000,
            },
        ]
    )
    trade = await connector.get_event(timeout=1.0)
    quote = await connector.get_event(timeout=1.0)
    bar = await connector.get_event(timeout=1.0)
    assert isinstance(trade, TradeEvent)
    assert isinstance(quote, QuoteEvent)
    assert isinstance(bar, BarEvent)
    assert trade.instrument.instrument_key == "bergama:equity:us:aapl"
    assert trade.currency == "USD"
    assert trade.venue == "XNAS"
    assert trade.source.source_symbol == "AAPL"
    assert trade.source.extras.get("exchange_id") == "4"
    assert quote.bid_price == Decimal("190.1")
    assert bar.window_start == datetime(2024, 1, 2, 12, 0, tzinfo=UTC)
    assert bar.source.extras.get("adjustment_assumption") == REALTIME_ADJUSTMENT_ASSUMPTION
    assert build_idempotency_key(trade)
    assert build_deduplication_key(quote)
    env = market_event_to_envelope(bar)
    assert env.occurred_at == bar.occurred_at
    payload = market_event_to_payload(trade)
    assert "polygon_ticker" not in payload
    await connector.stop()
    assert connector.state is ConnectionState.STOPPED
    await connector.stop()  # idempotent


@pytest.mark.asyncio
async def test_auth_failure_is_terminal() -> None:
    transport = FakePolygonWebSocketTransport(auth_failure=True, auto_auth_success=False)
    # Seed only the auth_failed response after auth (no automatic connected frames).
    connector = PolygonRealtimeConnector(
        _settings(websocket_max_reconnect_attempts=5),
        clock=FixedClock(datetime(2024, 6, 15, 12, 0, tzinfo=UTC)),
        transport=transport,
        sleeper=_Sleeper(),
    )

    async def _on_auth_send() -> None:
        for _ in range(100):
            if any('"action":"auth"' in f for f in transport.sent_frames):
                transport.push_json(
                    [{"ev": "status", "status": "auth_failed", "message": "not authorized"}]
                )
                return
            await asyncio.sleep(0.01)

    await connector.start(_request())
    await _on_auth_send()
    for _ in range(100):
        if connector._fatal is not None or connector.state is ConnectionState.STOPPED:
            break
        await asyncio.sleep(0.01)
    assert isinstance(connector._fatal, PolygonWebsocketAuthFailedError)
    assert transport.connect_count == 1
    await connector.stop()


@pytest.mark.asyncio
async def test_reconnect_resubscribes_full_set() -> None:
    transport = FakePolygonWebSocketTransport()
    sleeper = _Sleeper()
    connector = PolygonRealtimeConnector(
        _settings(websocket_max_reconnect_attempts=3),
        clock=FixedClock(datetime(2024, 6, 15, 12, 0, tzinfo=UTC)),
        transport=transport,
        sleeper=sleeper,
    )
    await connector.start(_request(channels=("T",)))
    for _ in range(100):
        if connector.state is ConnectionState.STREAMING:
            break
        await asyncio.sleep(0.01)
    assert connector.state is ConnectionState.STREAMING
    transport.force_disconnect()
    for _ in range(100):
        if transport.connect_count >= 2 and connector.state is ConnectionState.STREAMING:
            break
        await asyncio.sleep(0.01)
    assert transport.connect_count >= 2
    assert sleeper.delays
    subscribe_frames = [f for f in transport.sent_frames if '"action":"subscribe"' in f]
    assert len(subscribe_frames) >= 2
    assert all('"params":"T.AAPL"' in f for f in subscribe_frames)
    await connector.stop()
    connects = transport.connect_count
    await asyncio.sleep(0.05)
    assert transport.connect_count == connects


@pytest.mark.asyncio
async def test_reconnect_exhaustion() -> None:
    transport = FakePolygonWebSocketTransport(disconnect_after_frames=0)
    connector = PolygonRealtimeConnector(
        _settings(websocket_max_reconnect_attempts=2),
        clock=FixedClock(datetime(2024, 6, 15, 12, 0, tzinfo=UTC)),
        transport=transport,
        sleeper=_Sleeper(),
    )
    await connector.start(_request(channels=("T",)))
    for _ in range(100):
        if isinstance(connector._fatal, PolygonWebsocketReconnectExhaustedError):
            break
        await asyncio.sleep(0.01)
    assert isinstance(connector._fatal, PolygonWebsocketReconnectExhaustedError)
    await connector.stop()


@pytest.mark.asyncio
async def test_queue_overflow_fail_closed_no_silent_drop() -> None:
    transport = FakePolygonWebSocketTransport()
    connector = PolygonRealtimeConnector(
        _settings(websocket_max_queue_size=1),
        clock=FixedClock(datetime(2024, 6, 15, 12, 0, tzinfo=UTC)),
        transport=transport,
        sleeper=_Sleeper(),
    )
    await connector.start(_request(channels=("T",)))
    for _ in range(50):
        if connector.state is ConnectionState.STREAMING:
            break
        await asyncio.sleep(0.01)
    transport.push_json(
        [
            {"ev": "T", "sym": "AAPL", "i": "1", "p": "1", "s": "1", "t": T_MS},
            {"ev": "T", "sym": "AAPL", "i": "2", "p": "1", "s": "1", "t": T_MS + 1},
        ]
    )
    for _ in range(50):
        if connector.overflowed:
            break
        await asyncio.sleep(0.01)
    assert connector.overflowed is True
    assert isinstance(connector._fatal, PolygonWebsocketOverflowError)
    # Already-mapped event remains available (not silently dropped).
    first = await connector.get_event(timeout=1.0)
    assert isinstance(first, TradeEvent)
    assert first.trade_id == "1"
    with pytest.raises(PolygonWebsocketOverflowError):
        await connector.get_event(timeout=0.2)
    await connector.stop()


@pytest.mark.asyncio
async def test_duplicates_and_order_preserved() -> None:
    transport = FakePolygonWebSocketTransport()
    connector = PolygonRealtimeConnector(
        _settings(),
        clock=FixedClock(datetime(2024, 6, 15, 12, 0, tzinfo=UTC)),
        transport=transport,
        sleeper=_Sleeper(),
    )
    await connector.start(_request(channels=("T",)))
    for _ in range(50):
        if connector.state is ConnectionState.STREAMING:
            break
        await asyncio.sleep(0.01)
    transport.push_json(
        [
            {"ev": "T", "sym": "AAPL", "i": "dup", "p": "1", "s": "1", "t": T_MS + 5},
            {"ev": "T", "sym": "AAPL", "i": "dup", "p": "1", "s": "1", "t": T_MS + 5},
            {"ev": "T", "sym": "AAPL", "i": "early", "p": "2", "s": "1", "t": T_MS},
        ]
    )
    a = await connector.get_event(timeout=1.0)
    b = await connector.get_event(timeout=1.0)
    c = await connector.get_event(timeout=1.0)
    assert isinstance(a, TradeEvent) and isinstance(b, TradeEvent) and isinstance(c, TradeEvent)
    assert a.trade_id == b.trade_id == "dup"
    assert c.trade_id == "early"
    assert a.occurred_at > c.occurred_at  # receive order, not time order
    await connector.stop()


@pytest.mark.asyncio
async def test_status_not_emitted_unknown_and_a_rejected() -> None:
    with pytest.raises(PolygonWebsocketProtocolError):
        parse_ws_message(
            {"ev": "A", "sym": "AAPL", "o": 1, "h": 1, "l": 1, "c": 1, "v": 1, "s": 1, "e": 2}
        )
    with pytest.raises(PolygonWebsocketProtocolError):
        parse_ws_message({"ev": "XYZ", "sym": "AAPL"})

    transport = FakePolygonWebSocketTransport()
    connector = PolygonRealtimeConnector(
        _settings(),
        clock=FixedClock(datetime(2024, 6, 15, 12, 0, tzinfo=UTC)),
        transport=transport,
        sleeper=_Sleeper(),
    )
    await connector.start(_request(channels=("T",)))
    for _ in range(50):
        if connector.state is ConnectionState.STREAMING:
            break
        await asyncio.sleep(0.01)
    transport.push_json([{"ev": "status", "status": "success", "message": "subscribed to: T.AAPL"}])
    transport.push_json([{"ev": "T", "sym": "AAPL", "i": "1", "p": "1", "s": "1", "t": T_MS}])
    event = await connector.get_event(timeout=1.0)
    assert isinstance(event, TradeEvent)
    await connector.stop()


def test_mapper_rejects_invalid_values() -> None:
    clock = FixedClock(datetime(2024, 6, 15, 12, 0, tzinfo=UTC))
    known = clock.now()
    with pytest.raises((PolygonMappingFailedError, ValueError)):
        map_ws_trade(
            PolygonWsTradeMessage.model_validate(
                {"ev": "T", "sym": "AAPL", "p": "NaN", "s": "1", "t": T_MS}
            ),
            instrument=_instrument(),
            currency="USD",
            venue="XNAS",
            known_at=known,
            clock=clock,
        )
    with pytest.raises((PolygonMappingFailedError, ValueError)):
        map_ws_quote(
            PolygonWsQuoteMessage.model_validate(
                {
                    "ev": "Q",
                    "sym": "AAPL",
                    "bp": "2",
                    "bs": "1",
                    "ap": "1",
                    "as": "1",
                    "t": T_MS,
                }
            ),
            instrument=_instrument(),
            currency="USD",
            venue="XNAS",
            known_at=known,
            clock=clock,
        )
    with pytest.raises((PolygonMappingFailedError, ValueError)):
        map_ws_minute_bar(
            PolygonWsMinuteAggregateMessage.model_validate(
                {
                    "ev": "AM",
                    "sym": "AAPL",
                    "o": "1",
                    "h": "1",
                    "l": "2",
                    "c": "1",
                    "v": "-1",
                    "s": T_MS,
                    "e": T_MS + 1,
                }
            ),
            instrument=_instrument(),
            currency="USD",
            venue="XNAS",
            known_at=known,
            clock=clock,
        )


def test_late_flag_and_adjustment_metadata() -> None:
    clock = FixedClock(datetime(2024, 6, 15, 12, 0, tzinfo=UTC))
    known = datetime(2024, 6, 15, 12, 0, 5, tzinfo=UTC)
    event = map_ws_trade(
        PolygonWsTradeMessage.model_validate(
            {"ev": "T", "sym": "AAPL", "i": "9", "p": "1", "s": "1", "t": T_MS}
        ),
        instrument=_instrument(),
        currency="USD",
        venue="XNAS",
        known_at=known,
        clock=clock,
    )
    assert event.quality.is_late is True
    bar = map_ws_minute_bar(
        PolygonWsMinuteAggregateMessage.model_validate(
            {
                "ev": "AM",
                "sym": "AAPL",
                "o": "1",
                "h": "1",
                "l": "1",
                "c": "1",
                "v": "0",
                "s": T_MS,
                "e": T_MS + 60_000,
            }
        ),
        instrument=_instrument(),
        currency="USD",
        venue="XNAS",
        known_at=clock.now(),
        clock=clock,
    )
    assert bar.adjustment_state is AdjustmentState.UNADJUSTED
    assert bar.source.extras["adjustment_assumption"] == REALTIME_ADJUSTMENT_ASSUMPTION


@pytest.mark.asyncio
async def test_cancellation_propagates() -> None:
    transport = FakePolygonWebSocketTransport()
    connector = PolygonRealtimeConnector(
        _settings(),
        clock=FixedClock(datetime(2024, 6, 15, 12, 0, tzinfo=UTC)),
        transport=transport,
        sleeper=_Sleeper(),
    )
    await connector.start(_request(channels=("T",)))
    task = connector._task
    assert task is not None
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    await connector.stop()
    assert connector.state is ConnectionState.STOPPED


@pytest.mark.asyncio
async def test_container_wiring_disabled_and_isolated() -> None:
    disabled = AppSettings(
        environment=AppEnvironment.TEST,
        bootstrap_auth_enabled=True,
        secrets=SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
        polygon=PolygonSettings(enabled=False),
    )
    c0 = build_container(disabled)
    assert c0.polygon_realtime is None

    settings = AppSettings(
        environment=AppEnvironment.TEST,
        bootstrap_auth_enabled=True,
        secrets=SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
        polygon=_settings(),
    )
    t1 = FakePolygonWebSocketTransport()
    t2 = FakePolygonWebSocketTransport()
    r1 = PolygonRealtimeConnector(
        settings.polygon, clock=FixedClock(datetime(2024, 1, 1, tzinfo=UTC)), transport=t1
    )
    r2 = PolygonRealtimeConnector(
        settings.polygon, clock=FixedClock(datetime(2024, 1, 1, tzinfo=UTC)), transport=t2
    )
    c1 = build_container(settings, polygon_realtime=r1)
    c2 = build_container(settings, polygon_realtime=r2)
    assert c1.polygon_realtime is r1
    assert c2.polygon_realtime is r2
    assert c1.polygon_realtime is not c2.polygon_realtime
    await c1.aclose()
    await c2.aclose()
