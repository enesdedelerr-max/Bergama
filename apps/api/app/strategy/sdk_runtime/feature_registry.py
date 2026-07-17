"""Host-owned feature schema registry (#406)."""

from __future__ import annotations

from dataclasses import dataclass

from bergama_strategy_sdk.errors import StrategyFeatureSchemaError
from bergama_strategy_sdk.features import FeatureSnapshot
from bergama_strategy_sdk.manifest import StrategyPluginManifest
from bergama_strategy_sdk.serialization import sha256_hex


@dataclass(frozen=True, slots=True)
class FeatureSchemaDefinition:
    schema_id: str
    schema_version: str
    feature_id: str
    value_type: str = "decimal"

    def registry_key(self) -> str:
        return f"{self.schema_id}:{self.schema_version}:{self.feature_id}"


class FeatureSchemaRegistry:
    """Explicit host-owned feature schema registry."""

    def __init__(self, *, closed: bool = True) -> None:
        self._schemas: dict[str, FeatureSchemaDefinition] = {}
        self._closed = closed

    def register(self, schema: FeatureSchemaDefinition) -> None:
        key = schema.registry_key()
        if key in self._schemas:
            raise StrategyFeatureSchemaError(detail=f"duplicate_schema:{key}")
        self._schemas[key] = schema

    def get(
        self,
        *,
        schema_id: str,
        schema_version: str,
        feature_id: str,
    ) -> FeatureSchemaDefinition:
        key = f"{schema_id}:{schema_version}:{feature_id}"
        try:
            return self._schemas[key]
        except KeyError as exc:
            raise StrategyFeatureSchemaError(detail=f"unknown_schema:{key}") from exc

    def has_feature(self, feature_id: str) -> bool:
        return any(schema.feature_id == feature_id for schema in self._schemas.values())

    def find_by_feature_id(self, feature_id: str) -> FeatureSchemaDefinition:
        for schema in self._schemas.values():
            if schema.feature_id == feature_id:
                return schema
        raise StrategyFeatureSchemaError(detail=f"unknown_feature:{feature_id}")

    def validate_required_features(self, required: tuple[str, ...]) -> None:
        for feature_id in required:
            if not self.has_feature(feature_id):
                raise StrategyFeatureSchemaError(detail=f"missing_required_feature:{feature_id}")

    def validate_snapshot(
        self,
        snapshot: FeatureSnapshot,
        *,
        manifest: StrategyPluginManifest,
    ) -> None:
        """Fail-closed snapshot validation against registry and manifest requirements."""
        if snapshot.feature_schema_version != manifest.feature_schema_version:
            raise StrategyFeatureSchemaError(detail="feature_schema_version_mismatch")
        for required in manifest.required_features:
            if not any(feature.feature_id == required for feature in snapshot.features):
                raise StrategyFeatureSchemaError(detail=f"missing_required_feature:{required}")
        for feature in snapshot.features:
            if self._closed and not self.has_feature(feature.feature_id):
                raise StrategyFeatureSchemaError(detail=f"unknown_feature:{feature.feature_id}")
            registered = self.get(
                schema_id=feature.schema_id,
                schema_version=feature.schema_version,
                feature_id=feature.feature_id,
            )
            if registered.feature_id != feature.feature_id:
                raise StrategyFeatureSchemaError(detail=f"feature_id_mismatch:{feature.feature_id}")

    def fingerprint(self) -> str:
        payload = {
            schema.registry_key(): {
                "feature_id": schema.feature_id,
                "schema_id": schema.schema_id,
                "schema_version": schema.schema_version,
                "value_type": schema.value_type,
            }
            for key, schema in sorted(self._schemas.items())
        }
        return str(sha256_hex(payload))
