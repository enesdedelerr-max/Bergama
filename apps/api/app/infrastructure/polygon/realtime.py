"""Polygon stocks realtime WebSocket connector (Issue #303) — transport only."""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import AsyncIterator
from enum import StrEnum
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.clock import Clock
from app.core.logging import get_logger, structured_extra
from app.core.polygon_settings import PolygonSettings
from app.infrastructure.polygon.errors import (
    PolygonInvalidRequestError,
    PolygonMappingFailedError,
    PolygonNotConfiguredError,
    PolygonWebsocketAuthFailedError,
    PolygonWebsocketError,
    PolygonWebsocketOverflowError,
    PolygonWebsocketProtocolError,
    PolygonWebsocketReconnectExhaustedError,
)
from app.infrastructure.polygon.ws_mapper import map_ws_minute_bar, map_ws_quote, map_ws_trade
from app.infrastructure.polygon.ws_reconnect import (
    AsyncSleeper,
    WebsocketReconnectPolicy,
    default_sleeper,
)
from app.infrastructure.polygon.ws_schemas import (
    PolygonWsMinuteAggregateMessage,
    PolygonWsQuoteMessage,
    PolygonWsStatusMessage,
    PolygonWsTradeMessage,
    parse_ws_message,
)
from app.infrastructure.polygon.ws_transport import (
    PolygonWebSocketTransport,
    WebsocketsPolygonTransport,
    build_auth_frame,
    build_subscribe_frame,
    parse_incoming_frames,
    redact_control_frame,
)
from app.market_data.envelope import CanonicalMarketEvent
from app.market_data.identity import InstrumentId

logger = get_logger(__name__)

ChannelKind = Literal["T", "Q", "AM"]
_ALLOWED_CHANNELS: frozenset[str] = frozenset({"T", "Q", "AM"})


class ConnectionState(StrEnum):
    STOPPED = "STOPPED"
    CONNECTING = "CONNECTING"
    AUTHENTICATING = "AUTHENTICATING"
    SUBSCRIBING = "SUBSCRIBING"
    STREAMING = "STREAMING"
    RECONNECTING = "RECONNECTING"
    STOPPING = "STOPPING"


class SymbolRealtimeContext(BaseModel):
    """Caller-supplied symbol context for subscription and mapping."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    symbol: str = Field(min_length=1, max_length=32)
    instrument: InstrumentId
    currency: str = Field(min_length=3, max_length=3)
    venue: str = Field(min_length=1, max_length=32)
    channels: tuple[ChannelKind, ...] = ("T", "Q", "AM")

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        text = value.strip().upper()
        if not text or not all(ch.isalnum() or ch in {".", "-", "/"} for ch in text):
            msg = "symbol must be a non-empty ticker token"
            raise ValueError(msg)
        return text

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        text = value.strip().upper()
        if len(text) != 3 or not text.isalpha():
            msg = "currency must be a 3-letter ISO code"
            raise ValueError(msg)
        return text

    @field_validator("venue")
    @classmethod
    def normalize_venue(cls, value: str) -> str:
        text = value.strip().upper()
        if not text:
            msg = "venue is required"
            raise ValueError(msg)
        return text

    @field_validator("channels")
    @classmethod
    def validate_channels(cls, value: tuple[ChannelKind, ...]) -> tuple[ChannelKind, ...]:
        if not value:
            msg = "at least one channel is required"
            raise ValueError(msg)
        seen: set[str] = set()
        ordered: list[ChannelKind] = []
        for channel in value:
            if channel not in _ALLOWED_CHANNELS:
                msg = f"unsupported channel {channel!r}; only T, Q, AM are allowed"
                raise ValueError(msg)
            if channel not in seen:
                seen.add(channel)
                ordered.append(channel)
        return tuple(ordered)


class RealtimeStartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    symbols: tuple[SymbolRealtimeContext, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_symbols(self) -> Self:
        keys = [item.symbol for item in self.symbols]
        if len(keys) != len(set(keys)):
            msg = "duplicate symbols in realtime start request"
            raise ValueError(msg)
        return self

    def channel_list(self) -> list[str]:
        channels: list[str] = []
        for item in self.symbols:
            for kind in item.channels:
                channels.append(f"{kind}.{item.symbol}")
        # Deterministic order: by symbol then channel kind order as requested.
        return channels

    def context_by_symbol(self) -> dict[str, SymbolRealtimeContext]:
        return {item.symbol: item for item in self.symbols}


class PolygonRealtimeConnector:
    """Stocks WebSocket ingest: connect → auth → subscribe → map → enqueue."""

    def __init__(
        self,
        settings: PolygonSettings,
        *,
        clock: Clock,
        transport: PolygonWebSocketTransport | None = None,
        sleeper: AsyncSleeper = default_sleeper,
    ) -> None:
        if not settings.enabled:
            raise PolygonNotConfiguredError("polygon is disabled")
        if not settings.websocket_enabled:
            raise PolygonNotConfiguredError("polygon websocket is disabled")
        if settings.api_key is None:
            raise PolygonNotConfiguredError("polygon api key is not configured")
        self._settings = settings
        self._clock = clock
        self._transport = transport if transport is not None else WebsocketsPolygonTransport()
        self._sleeper = sleeper
        self._policy = WebsocketReconnectPolicy(
            max_attempts=settings.websocket_max_reconnect_attempts,
            initial_delay_seconds=settings.websocket_reconnect_initial_delay_seconds,
            max_delay_seconds=settings.websocket_reconnect_max_delay_seconds,
        )
        self._state = ConnectionState.STOPPED
        self._queue: asyncio.Queue[CanonicalMarketEvent] = asyncio.Queue(
            maxsize=settings.websocket_max_queue_size
        )
        self._task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()
        self._request: RealtimeStartRequest | None = None
        self._contexts: dict[str, SymbolRealtimeContext] = {}
        self._channels: list[str] = []
        self._overflow = False
        self._fatal: BaseException | None = None
        self._auth_succeeded_once = False

    @property
    def state(self) -> ConnectionState:
        return self._state

    @property
    def overflowed(self) -> bool:
        return self._overflow

    def subscription_channels(self) -> tuple[str, ...]:
        return tuple(self._channels)

    async def start(self, request: RealtimeStartRequest) -> None:
        if self._task is not None and not self._task.done():
            raise PolygonInvalidRequestError("polygon realtime connector already started")
        self._request = request
        self._contexts = request.context_by_symbol()
        self._channels = request.channel_list()
        if not self._channels:
            raise PolygonInvalidRequestError("subscription channel list is empty")
        self._stop_event = asyncio.Event()
        self._overflow = False
        self._fatal = None
        self._auth_succeeded_once = False
        self._drain_queue()
        self._task = asyncio.create_task(self._run_session(), name="polygon-realtime")

    async def stop(self) -> None:
        """Idempotent graceful stop. Does not reconnect after stop."""
        if self._state is ConnectionState.STOPPED and self._task is None:
            return
        self._state = ConnectionState.STOPPING
        self._stop_event.set()
        task = self._task
        if task is not None and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception:
                logger.exception(
                    "polygon realtime stop observed task error",
                    extra=structured_extra(
                        event="polygon.realtime.stop.task_error",
                        source="polygon_realtime",
                    ),
                )
        self._task = None
        try:
            await self._transport.close()
        finally:
            self._state = ConnectionState.STOPPED

    async def aclose(self) -> None:
        await self.stop()

    async def get_event(self, *, timeout: float | None = None) -> CanonicalMarketEvent:
        # Drain already-mapped events before surfacing a terminal fatal error.
        if self._fatal is not None and self._queue.empty():
            raise self._fatal
        if timeout is None:
            event = await self._queue.get()
        else:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=timeout)
            except TimeoutError as timeout_exc:
                if self._fatal is not None and self._queue.empty():
                    raise self._fatal from timeout_exc
                raise
        return event

    async def events(self) -> AsyncIterator[CanonicalMarketEvent]:
        while True:
            if self._fatal is not None and self._queue.empty():
                raise self._fatal
            if (
                self._state is ConnectionState.STOPPED
                and self._queue.empty()
                and (self._task is None or self._task.done())
            ):
                return
            try:
                yield await self.get_event(timeout=0.05)
            except TimeoutError as timeout_exc:
                if self._fatal is not None and self._queue.empty():
                    raise self._fatal from timeout_exc
                if self._stop_event.is_set() and self._queue.empty():
                    return
                continue

    def _drain_queue(self) -> None:
        while True:
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break

    async def _run_session(self) -> None:
        attempts = 0
        try:
            while not self._stop_event.is_set():
                try:
                    await self._connect_auth_subscribe_stream()
                    # Clean stream exit (server close) without stop → reconnect.
                    if self._stop_event.is_set() or self._overflow:
                        break
                    attempts += 1
                    if attempts > self._policy.max_attempts:
                        raise PolygonWebsocketReconnectExhaustedError(
                            "polygon websocket reconnect attempts exhausted"
                        )
                    self._state = ConnectionState.RECONNECTING
                    await self._sleeper(self._policy.delay_for_attempt(attempts))
                except asyncio.CancelledError:
                    raise
                except PolygonWebsocketAuthFailedError:
                    self._fatal = PolygonWebsocketAuthFailedError("polygon websocket auth failed")
                    break
                except PolygonWebsocketOverflowError as exc:
                    self._fatal = exc
                    break
                except (
                    PolygonWebsocketError,
                    PolygonMappingFailedError,
                    PolygonWebsocketProtocolError,
                    PolygonWebsocketReconnectExhaustedError,
                ) as exc:
                    if self._stop_event.is_set():
                        break
                    # Terminal if reconnect budget exhausted.
                    if isinstance(exc, PolygonWebsocketReconnectExhaustedError):
                        self._fatal = exc
                        break
                    attempts += 1
                    if attempts > self._policy.max_attempts:
                        self._fatal = PolygonWebsocketReconnectExhaustedError(
                            "polygon websocket reconnect attempts exhausted"
                        )
                        break
                    self._state = ConnectionState.RECONNECTING
                    logger.info(
                        "polygon realtime reconnecting",
                        extra=structured_extra(
                            event="polygon.realtime.reconnecting",
                            source="polygon_realtime",
                            attempt=attempts,
                            error_code=getattr(exc, "code", "polygon.websocket_error"),
                        ),
                    )
                    await self._sleeper(self._policy.delay_for_attempt(attempts))
                    continue
        except asyncio.CancelledError:
            raise
        finally:
            with contextlib.suppress(Exception):
                await self._transport.close()
            if self._state is not ConnectionState.STOPPING:
                self._state = ConnectionState.STOPPED

    async def _connect_auth_subscribe_stream(self) -> None:
        assert self._settings.api_key is not None
        self._state = ConnectionState.CONNECTING
        await self._transport.close()
        await self._transport.connect(
            self._settings.websocket_url,
            open_timeout=self._settings.websocket_connect_timeout_seconds,
        )

        self._state = ConnectionState.AUTHENTICATING
        auth_frame = build_auth_frame(self._settings.api_key.get_secret_value())
        logger.debug(
            "polygon realtime auth send",
            extra=structured_extra(
                event="polygon.realtime.auth.send",
                source="polygon_realtime",
                frame=redact_control_frame(auth_frame),
            ),
        )
        await self._transport.send_text(auth_frame)
        await self._wait_for_auth_success()

        self._state = ConnectionState.SUBSCRIBING
        subscribe_frame = build_subscribe_frame(self._channels)
        await self._transport.send_text(subscribe_frame)
        logger.info(
            "polygon realtime subscribed",
            extra=structured_extra(
                event="polygon.realtime.subscribed",
                source="polygon_realtime",
                channels=len(self._channels),
            ),
        )

        self._state = ConnectionState.STREAMING
        self._auth_succeeded_once = True
        await self._read_loop()

    async def _wait_for_auth_success(self) -> None:
        deadline = asyncio.get_running_loop().time() + self._settings.websocket_auth_timeout_seconds
        while True:
            if self._stop_event.is_set():
                return
            remaining = deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                raise PolygonWebsocketAuthFailedError("polygon websocket auth timed out")
            raw = await asyncio.wait_for(self._transport.recv_text(), timeout=remaining)
            for obj in parse_incoming_frames(raw):
                parsed = parse_ws_message(obj)
                if not isinstance(parsed, PolygonWsStatusMessage):
                    continue
                status = parsed.status.strip().lower()
                if status == "auth_success":
                    return
                if status == "auth_failed":
                    raise PolygonWebsocketAuthFailedError("polygon websocket auth failed")
                # Ignore connected / other pre-auth statuses.

    async def _read_loop(self) -> None:
        while not self._stop_event.is_set():
            raw = await self._transport.recv_text()
            for obj in parse_incoming_frames(raw):
                await self._handle_object(obj)

    async def _handle_object(self, obj: dict[str, object]) -> None:
        parsed = parse_ws_message(obj)
        if isinstance(parsed, PolygonWsStatusMessage):
            await self._handle_status(parsed)
            return
        known_at = self._clock.now()
        context = self._contexts.get(parsed.sym)
        if context is None:
            raise PolygonWebsocketProtocolError(
                f"received event for unsubscribed symbol {parsed.sym!r}"
            )
        event: CanonicalMarketEvent
        if isinstance(parsed, PolygonWsTradeMessage):
            event = map_ws_trade(
                parsed,
                instrument=context.instrument,
                currency=context.currency,
                venue=context.venue,
                known_at=known_at,
                clock=self._clock,
            )
        elif isinstance(parsed, PolygonWsQuoteMessage):
            event = map_ws_quote(
                parsed,
                instrument=context.instrument,
                currency=context.currency,
                venue=context.venue,
                known_at=known_at,
                clock=self._clock,
            )
        elif isinstance(parsed, PolygonWsMinuteAggregateMessage):
            event = map_ws_minute_bar(
                parsed,
                instrument=context.instrument,
                currency=context.currency,
                venue=context.venue,
                known_at=known_at,
                clock=self._clock,
            )
        else:
            raise PolygonWebsocketProtocolError("unsupported mapped message type")
        await self._enqueue(event)

    async def _handle_status(self, message: PolygonWsStatusMessage) -> None:
        status = message.status.lower()
        if status == "auth_failed":
            raise PolygonWebsocketAuthFailedError("polygon websocket auth failed")
        # Subscription acknowledgements and connected statuses are control-plane only.
        logger.debug(
            "polygon realtime status",
            extra=structured_extra(
                event="polygon.realtime.status",
                source="polygon_realtime",
                status=message.status,
                message=(message.message or "")[:128],
            ),
        )

    async def _enqueue(self, event: CanonicalMarketEvent) -> None:
        try:
            self._queue.put_nowait(event)
        except asyncio.QueueFull as exc:
            self._overflow = True
            logger.error(
                "polygon realtime queue overflow",
                extra=structured_extra(
                    event="polygon.realtime.queue.overflow",
                    source="polygon_realtime",
                    max_queue_size=self._settings.websocket_max_queue_size,
                ),
            )
            overflow = PolygonWebsocketOverflowError(
                "polygon realtime event queue overflow; session stopping"
            )
            self._fatal = overflow
            self._stop_event.set()
            raise overflow from exc
