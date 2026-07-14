"""Typed FastAPI access to the application container."""

from __future__ import annotations

from fastapi import Request

from app.core.container import AppContainer

_CONTAINER_STATE_KEY = "container"


def get_app_container(request: Request) -> AppContainer:
    """Return the application container attached to the FastAPI app.

    Fails fast if missing or invalid. Never builds a fallback container.
    """
    container = getattr(request.app.state, _CONTAINER_STATE_KEY, None)
    if not isinstance(container, AppContainer):
        msg = "application container is not configured on app.state.container"
        raise RuntimeError(msg)
    return container


def attach_container(app_state: object, container: AppContainer) -> None:
    """Attach the canonical container reference to FastAPI app.state."""
    setattr(app_state, _CONTAINER_STATE_KEY, container)
