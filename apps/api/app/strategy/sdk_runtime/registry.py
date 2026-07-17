"""Allowlisted plugin registry (#406)."""

from __future__ import annotations

from collections.abc import Callable

from bergama_strategy_sdk.errors import StrategyManifestError
from bergama_strategy_sdk.execution import Strategy
from bergama_strategy_sdk.manifest import StrategyPluginManifest

StrategyFactory = Callable[[StrategyPluginManifest], Strategy]


class StrategySdkPluginRegistry:
    """Explicit allowlisted registry — factories bound to approved manifest identity."""

    def __init__(self) -> None:
        self._entries: dict[str, tuple[StrategyPluginManifest, StrategyFactory]] = {}

    @staticmethod
    def _route_key(manifest: StrategyPluginManifest) -> str:
        return f"{manifest.strategy_id}:{manifest.strategy_version}"

    def register(self, manifest: StrategyPluginManifest, factory: StrategyFactory) -> None:
        key = self._route_key(manifest)
        existing = self._entries.get(key)
        if existing is not None:
            registered, _ = existing
            if registered.fingerprint() == manifest.fingerprint():
                raise StrategyManifestError(detail=f"duplicate_plugin:{key}")
            raise StrategyManifestError(detail=f"conflicting_plugin_identity:{key}")
        self._entries[key] = (manifest, factory)

    def create(self, manifest: StrategyPluginManifest) -> Strategy:
        key = self._route_key(manifest)
        try:
            registered, factory = self._entries[key]
        except KeyError as exc:
            raise StrategyManifestError(detail=f"unknown_plugin:{key}") from exc
        self._assert_manifest_identity(registered=registered, supplied=manifest)
        return factory(manifest)

    def get_manifest(self, strategy_id: str, strategy_version: str) -> StrategyPluginManifest:
        key = f"{strategy_id}:{strategy_version}"
        try:
            manifest, _ = self._entries[key]
        except KeyError as exc:
            raise StrategyManifestError(detail=f"unknown_plugin:{key}") from exc
        return manifest

    def list_plugin_keys(self) -> tuple[str, ...]:
        return tuple(sorted(self._entries))

    @staticmethod
    def _assert_manifest_identity(
        *,
        registered: StrategyPluginManifest,
        supplied: StrategyPluginManifest,
    ) -> None:
        checks = (
            ("strategy_id", registered.strategy_id, supplied.strategy_id),
            ("strategy_version", registered.strategy_version, supplied.strategy_version),
            ("package_identity", registered.package_identity, supplied.package_identity),
            ("sdk_schema_version", registered.sdk_schema_version, supplied.sdk_schema_version),
            (
                "runtime_protocol_version",
                registered.runtime_protocol_version,
                supplied.runtime_protocol_version,
            ),
            (
                "feature_schema_version",
                registered.feature_schema_version,
                supplied.feature_schema_version,
            ),
            (
                "config_schema_version",
                registered.config_schema_version,
                supplied.config_schema_version,
            ),
            ("manifest_fingerprint", registered.fingerprint(), supplied.fingerprint()),
        )
        for axis, expected, actual in checks:
            if expected != actual:
                raise StrategyManifestError(detail=f"manifest_identity_mismatch:{axis}")
