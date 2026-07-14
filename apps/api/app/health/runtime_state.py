"""Application lifecycle startup state owned by the container."""

from __future__ import annotations

from enum import StrEnum
from threading import Lock


class RuntimeLifecycleState(StrEnum):
    """Lifecycle phases for startup/readiness probes."""

    INITIALIZING = "initializing"
    STARTED = "started"
    FAILED = "failed"
    STOPPING = "stopping"
    STOPPED = "stopped"


class RuntimeState:
    """Thread-safe lifecycle flag. No persistence. No request-scoped data."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._state = RuntimeLifecycleState.INITIALIZING

    @property
    def state(self) -> RuntimeLifecycleState:
        with self._lock:
            return self._state

    def mark_started(self) -> None:
        with self._lock:
            self._state = RuntimeLifecycleState.STARTED

    def mark_failed(self) -> None:
        with self._lock:
            self._state = RuntimeLifecycleState.FAILED

    def mark_stopping(self) -> None:
        with self._lock:
            self._state = RuntimeLifecycleState.STOPPING

    def mark_stopped(self) -> None:
        with self._lock:
            self._state = RuntimeLifecycleState.STOPPED

    def startup_probe_status(self) -> str:
        """Map lifecycle state to startup probe status string."""
        current = self.state
        if current is RuntimeLifecycleState.STARTED:
            return "started"
        if current is RuntimeLifecycleState.FAILED:
            return "failed"
        return "starting"
