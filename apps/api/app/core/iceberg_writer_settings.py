"""Iceberg market-data writer settings (#307).

Append-only Kafka → Iceberg sink. Disabled by default.
Kafka bootstrap/auth come from KafkaSettings — not duplicated here.
"""

from __future__ import annotations

from typing import Self
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator, model_validator

_ALLOWED_CATALOG_SCHEMES = frozenset({"http", "https", "sqlite", "file"})
_ALLOWED_WAREHOUSE_SCHEMES = frozenset({"s3", "s3a", "file"})


class IcebergWriterSettings(BaseModel):
    """Typed Iceberg writer configuration. No production credential defaults."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    enabled: bool = False
    required: bool = False
    catalog_uri: str | None = None
    warehouse: str | None = None
    namespace: str = Field(default="bergama", min_length=1, max_length=128)
    table_prefix: str = Field(default="", max_length=64)
    s3_endpoint: str | None = None
    s3_region: str = Field(default="us-east-1", min_length=1, max_length=64)
    path_style_access: bool = True
    access_key: SecretStr | None = None
    secret_key: SecretStr | None = None
    batch_max_records: int = Field(default=100, gt=0, le=10_000)
    batch_max_bytes: int = Field(default=1_048_576, gt=0, le=64_000_000)
    flush_interval_seconds: float = Field(default=2.0, gt=0, le=300.0)
    consumer_group_id: str = Field(default="bergama-iceberg-writer", min_length=1, max_length=200)
    auto_create_tables: bool = False
    committed_key_ttl_seconds: float = Field(default=3600.0, gt=0, le=86_400.0)
    committed_key_max_entries: int = Field(default=100_000, gt=0, le=2_000_000)
    # catalog_type: rest for live; sql for offline fixture injection path
    catalog_type: str = Field(default="rest", min_length=1, max_length=32)

    @field_validator("namespace", "consumer_group_id", "s3_region", "catalog_type")
    @classmethod
    def strip_required(cls, value: str) -> str:
        text = value.strip()
        if not text:
            msg = "value must be non-empty"
            raise ValueError(msg)
        return text

    @field_validator("table_prefix")
    @classmethod
    def strip_prefix(cls, value: str) -> str:
        return value.strip()

    @field_validator("catalog_uri", "warehouse", "s3_endpoint", mode="before")
    @classmethod
    def blank_to_none(cls, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, str):
            text = value.strip()
            return text or None
        return value

    @field_validator("access_key", "secret_key", mode="before")
    @classmethod
    def normalize_secret(cls, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, SecretStr):
            raw = value.get_secret_value()
        elif isinstance(value, str):
            raw = value
        else:
            return value
        if raw == "":
            return None
        if raw != raw.strip():
            msg = "secret value must not include leading or trailing whitespace"
            raise ValueError(msg)
        lowered = raw.lower()
        if lowered in {"changeme", "password", "secret", "default", "example"}:
            msg = "default or placeholder object-store credentials are not allowed"
            raise ValueError(msg)
        return raw

    @model_validator(mode="after")
    def validate_when_enabled(self) -> Self:
        if self.catalog_type not in {"rest", "sql"}:
            msg = "catalog_type must be rest or sql"
            raise ValueError(msg)
        if not self.enabled:
            return self
        if not self.catalog_uri:
            msg = "BERGAMA_ICEBERG_WRITER__CATALOG_URI is required when enabled"
            raise ValueError(msg)
        if not self.warehouse:
            msg = "BERGAMA_ICEBERG_WRITER__WAREHOUSE is required when enabled"
            raise ValueError(msg)
        self._validate_uri(self.catalog_uri, allowed=_ALLOWED_CATALOG_SCHEMES, field="catalog_uri")
        self._validate_uri(self.warehouse, allowed=_ALLOWED_WAREHOUSE_SCHEMES, field="warehouse")
        if self.s3_endpoint is not None:
            self._validate_uri(
                self.s3_endpoint,
                allowed=frozenset({"http", "https"}),
                field="s3_endpoint",
            )
        if (
            self.catalog_type == "rest"
            and self.warehouse.startswith("s3")
            and (self.access_key is None or self.secret_key is None)
        ):
            msg = "S3 access_key and secret_key are required for s3 warehouse when enabled"
            raise ValueError(msg)
        return self

    @staticmethod
    def _validate_uri(value: str, *, allowed: frozenset[str], field: str) -> None:
        parsed = urlparse(value)
        scheme = (parsed.scheme or "").lower()
        if scheme not in allowed:
            msg = f"{field} scheme must be one of {sorted(allowed)}"
            raise ValueError(msg)
        # Reject credential embedding in URIs.
        if parsed.username or parsed.password:
            msg = f"{field} must not embed credentials"
            raise ValueError(msg)

    def safe_summary(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "required": self.required,
            "catalog_uri_configured": self.catalog_uri is not None,
            "warehouse_configured": self.warehouse is not None,
            "namespace": self.namespace,
            "table_prefix": self.table_prefix,
            "s3_endpoint_configured": self.s3_endpoint is not None,
            "s3_region": self.s3_region,
            "path_style_access": self.path_style_access,
            "access_key_configured": self.access_key is not None,
            "secret_key_configured": self.secret_key is not None,
            "batch_max_records": self.batch_max_records,
            "batch_max_bytes": self.batch_max_bytes,
            "flush_interval_seconds": self.flush_interval_seconds,
            "consumer_group_id": self.consumer_group_id,
            "auto_create_tables": self.auto_create_tables,
            "committed_key_ttl_seconds": self.committed_key_ttl_seconds,
            "committed_key_max_entries": self.committed_key_max_entries,
            "catalog_type": self.catalog_type,
        }
