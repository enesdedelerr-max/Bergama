"""Unit tests for RuntimeState transitions."""

from __future__ import annotations

from app.health.runtime_state import RuntimeLifecycleState, RuntimeState
from app.health.service import log_startup_state_change


def test_initial_state_is_initializing() -> None:
    state = RuntimeState()
    assert state.state is RuntimeLifecycleState.INITIALIZING
    assert state.startup_probe_status() == "starting"


def test_mark_started() -> None:
    state = RuntimeState()
    state.mark_started()
    assert state.state is RuntimeLifecycleState.STARTED
    assert state.startup_probe_status() == "started"


def test_mark_failed() -> None:
    state = RuntimeState()
    state.mark_failed()
    assert state.startup_probe_status() == "failed"


def test_shutdown_updates_runtime_state() -> None:
    state = RuntimeState()
    state.mark_started()
    state.mark_stopping()
    assert state.state is RuntimeLifecycleState.STOPPING
    state.mark_stopped()
    assert state.state is RuntimeLifecycleState.STOPPED
    assert state.startup_probe_status() == "starting"


def test_log_startup_state_change_does_not_raise() -> None:
    state = RuntimeState()
    log_startup_state_change(state, previous=None)
    state.mark_started()
    log_startup_state_change(state, previous=RuntimeLifecycleState.INITIALIZING)
