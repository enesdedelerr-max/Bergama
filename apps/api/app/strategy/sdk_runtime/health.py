"""Plugin health lifecycle states (#406)."""

from __future__ import annotations

from enum import StrEnum


class PluginHealth(StrEnum):
    CREATED = "CREATED"
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    FAILED = "FAILED"
    DISABLED = "DISABLED"
    DISPOSING = "DISPOSING"
    DISPOSED = "DISPOSED"
    INCOMPATIBLE = "INCOMPATIBLE"


_ALLOWED_TRANSITIONS: dict[PluginHealth, frozenset[PluginHealth]] = {
    PluginHealth.CREATED: frozenset(
        {PluginHealth.INITIALIZING, PluginHealth.INCOMPATIBLE, PluginHealth.DISABLED}
    ),
    PluginHealth.INITIALIZING: frozenset(
        {PluginHealth.READY, PluginHealth.FAILED, PluginHealth.INCOMPATIBLE}
    ),
    PluginHealth.READY: frozenset(
        {PluginHealth.FAILED, PluginHealth.DISPOSING, PluginHealth.DISABLED}
    ),
    PluginHealth.FAILED: frozenset({PluginHealth.DISABLED, PluginHealth.DISPOSING}),
    PluginHealth.DISABLED: frozenset({PluginHealth.DISPOSING, PluginHealth.CREATED}),
    PluginHealth.DISPOSING: frozenset({PluginHealth.DISPOSED}),
    PluginHealth.DISPOSED: frozenset({PluginHealth.CREATED}),
    PluginHealth.INCOMPATIBLE: frozenset({PluginHealth.DISPOSED, PluginHealth.CREATED}),
}


def transition_health(current: PluginHealth, target: PluginHealth) -> PluginHealth:
    allowed = _ALLOWED_TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        msg = f"illegal plugin health transition {current.value} -> {target.value}"
        raise ValueError(msg)
    return target
