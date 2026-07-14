"""Narrow WebSocket transport boundary for Polygon realtime (Issue #303)."""

from __future__ import annotations

import json
from typing import Any, Protocol

import websockets
from websockets.asyncio.client import ClientConnection

from app.infrastructure.polygon.errors import PolygonWebsocketError


class PolygonWebSocketTransport(Protocol):
    """Minimal duplex transport used by the realtime connector."""

    async def connect(self, url: str, *, open_timeout: float) -> None:
        """Open the connection."""

    async def send_text(self, text: str) -> None:
        """Send a UTF-8 text frame."""

    async def recv_text(self) -> str:
        """Receive the next UTF-8 text frame."""

    async def close(self) -> None:
        """Close the transport. Idempotent."""


def redact_control_frame(text: str) -> str:
    """Redact auth params from diagnostic control-frame strings."""
    try:
        payload = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return "<unparseable-frame>"
    if isinstance(payload, dict) and payload.get("action") == "auth":
        safe = dict(payload)
        safe["params"] = "***REDACTED***"
        return json.dumps(safe, separators=(",", ":"), sort_keys=True)
    return text


class WebsocketsPolygonTransport:
    """Production adapter over the pinned ``websockets`` client."""

    def __init__(self) -> None:
        self._connection: ClientConnection | None = None

    async def connect(self, url: str, *, open_timeout: float) -> None:
        try:
            self._connection = await websockets.connect(
                url,
                open_timeout=open_timeout,
                max_size=2_097_152,
            )
        except Exception as exc:
            raise PolygonWebsocketError("polygon websocket connect failed") from exc

    async def send_text(self, text: str) -> None:
        if self._connection is None:
            raise PolygonWebsocketError("polygon websocket is not connected")
        try:
            await self._connection.send(text)
        except Exception as exc:
            raise PolygonWebsocketError("polygon websocket send failed") from exc

    async def recv_text(self) -> str:
        if self._connection is None:
            raise PolygonWebsocketError("polygon websocket is not connected")
        try:
            message = await self._connection.recv()
        except Exception as exc:
            raise PolygonWebsocketError("polygon websocket receive failed") from exc
        if isinstance(message, bytes):
            return message.decode("utf-8")
        if isinstance(message, str):
            return message
        msg = f"unexpected websocket frame type {type(message)!r}"
        raise PolygonWebsocketError(msg)

    async def close(self) -> None:
        if self._connection is None:
            return
        connection = self._connection
        self._connection = None
        try:
            await connection.close()
        except Exception:
            # Best-effort close; connector treats cleanup as idempotent.
            return


def build_auth_frame(api_key: str) -> str:
    """Official Polygon WS auth payload. Caller must not log the result."""
    return json.dumps({"action": "auth", "params": api_key}, separators=(",", ":"))


def build_subscribe_frame(channels: list[str]) -> str:
    params = ",".join(channels)
    return json.dumps({"action": "subscribe", "params": params}, separators=(",", ":"))


def parse_incoming_frames(raw: str) -> list[dict[str, Any]]:
    """Polygon emits JSON arrays of objects (occasionally a single object)."""
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PolygonWebsocketError("invalid polygon websocket JSON") from exc
    if isinstance(payload, dict):
        return [payload]
    if isinstance(payload, list):
        objects: list[dict[str, Any]] = []
        for item in payload:
            if not isinstance(item, dict):
                raise PolygonWebsocketError("polygon websocket array item must be an object")
            objects.append(item)
        return objects
    raise PolygonWebsocketError("polygon websocket payload must be object or array")
