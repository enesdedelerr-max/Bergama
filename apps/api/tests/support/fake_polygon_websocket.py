"""Deterministic fake Polygon WebSocket transport for offline tests."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Iterable, Sequence
from typing import Any

from app.infrastructure.polygon.errors import PolygonWebsocketError


class FakePolygonWebSocketTransport:
    """Scripted duplex transport with sent-frame capture and disconnect hooks."""

    def __init__(
        self,
        *,
        incoming: Sequence[str] | None = None,
        auto_auth_success: bool = True,
        auth_failure: bool = False,
        disconnect_after_frames: int | None = None,
    ) -> None:
        self._incoming: asyncio.Queue[str] = asyncio.Queue()
        self._sent: list[str] = []
        self._connected = False
        self._closed = False
        self._recv_count = 0
        self._disconnect_after_frames = disconnect_after_frames
        self._auto_auth_success = auto_auth_success
        self._auth_failure = auth_failure
        self._auth_responded = False
        self._connect_event = asyncio.Event()
        self._close_event = asyncio.Event()
        self._force_disconnect = False
        self._connect_count = 0
        if incoming:
            for frame in incoming:
                self._incoming.put_nowait(frame)

    @property
    def sent_frames(self) -> tuple[str, ...]:
        return tuple(self._sent)

    @property
    def connect_count(self) -> int:
        return self._connect_count

    @property
    def connected(self) -> bool:
        return self._connected and not self._closed

    def force_disconnect(self) -> None:
        """Make the next recv_text raise a transient disconnect error."""
        self._force_disconnect = True
        self.push_text("__disconnect__")

    async def connect(self, url: str, *, open_timeout: float) -> None:
        _ = open_timeout
        if not url.startswith("wss://"):
            raise PolygonWebsocketError("fake websocket url must use wss")
        self._closed = False
        self._connected = True
        self._auth_responded = False
        self._recv_count = 0
        self._force_disconnect = False
        self._connect_count += 1
        self._connect_event.set()
        if self._auto_auth_success is False and not self._auth_failure:
            return
        self.push_json(
            [{"ev": "status", "status": "connected", "message": "Connected Successfully"}]
        )

    async def send_text(self, text: str) -> None:
        if not self._connected or self._closed:
            raise PolygonWebsocketError("fake websocket not connected")
        self._sent.append(text)
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return
        if not isinstance(payload, dict):
            return
        action = payload.get("action")
        if action == "auth" and not self._auth_responded:
            self._auth_responded = True
            if self._auth_failure:
                self.push_json(
                    [{"ev": "status", "status": "auth_failed", "message": "not authorized"}]
                )
            elif self._auto_auth_success:
                self.push_json(
                    [{"ev": "status", "status": "auth_success", "message": "authenticated"}]
                )
        if action == "subscribe" and self._auto_auth_success and not self._auth_failure:
            params = str(payload.get("params", ""))
            self.push_json(
                [
                    {
                        "ev": "status",
                        "status": "success",
                        "message": f"subscribed to: {params}",
                    }
                ]
            )

    async def recv_text(self) -> str:
        if not self._connected or self._closed:
            raise PolygonWebsocketError("fake websocket disconnected")
        if (
            self._disconnect_after_frames is not None
            and self._recv_count >= self._disconnect_after_frames
        ):
            self._connected = False
            raise PolygonWebsocketError("fake websocket disconnected")
        frame = await self._incoming.get()
        self._recv_count += 1
        if self._force_disconnect or frame == "__disconnect__":
            self._force_disconnect = False
            self._connected = False
            raise PolygonWebsocketError("fake websocket disconnected")
        return frame

    async def close(self) -> None:
        self._closed = True
        self._connected = False
        self._close_event.set()
        while not self._incoming.empty():
            try:
                self._incoming.get_nowait()
            except asyncio.QueueEmpty:
                break

    def push_text(self, frame: str) -> None:
        self._incoming.put_nowait(frame)

    def push_json(self, payloads: Iterable[dict[str, Any]]) -> None:
        self.push_text(json.dumps(list(payloads)))

    def clear_sent(self) -> None:
        self._sent.clear()
