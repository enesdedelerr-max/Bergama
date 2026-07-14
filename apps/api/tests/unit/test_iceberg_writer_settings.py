"""Configuration tests for Iceberg writer settings (#307)."""

from __future__ import annotations

import pytest
from app.core.config import AppSettings
from app.core.environment import AppEnvironment
from app.core.iceberg_writer_settings import IcebergWriterSettings
from pydantic import SecretStr


def test_disabled_by_default() -> None:
    settings = IcebergWriterSettings()
    assert settings.enabled is False
    assert settings.auto_create_tables is False
    assert settings.batch_max_records == 100
    assert settings.batch_max_bytes == 1_048_576
    assert settings.flush_interval_seconds == 2.0


def test_enabled_requires_catalog_and_warehouse() -> None:
    with pytest.raises(ValueError, match="CATALOG_URI"):
        IcebergWriterSettings(enabled=True, warehouse="file:///tmp/wh")
    with pytest.raises(ValueError, match="WAREHOUSE"):
        IcebergWriterSettings(enabled=True, catalog_uri="sqlite:////tmp/c.db")


def test_placeholder_credentials_rejected() -> None:
    with pytest.raises(ValueError, match="placeholder"):
        IcebergWriterSettings(
            enabled=True,
            catalog_type="rest",
            catalog_uri="http://catalog:8181",
            warehouse="s3://bergama-warehouse/",
            s3_endpoint="http://minio:9000",
            access_key=SecretStr("changeme"),
            secret_key=SecretStr("not-a-placeholder-secret-key"),
        )


def test_safe_summary_redacts_secrets() -> None:
    settings = IcebergWriterSettings(
        enabled=True,
        catalog_type="sql",
        catalog_uri="sqlite:////tmp/c.db",
        warehouse="file:///tmp/wh",
        access_key=SecretStr("local-dev-access-key-0001"),
        secret_key=SecretStr("local-dev-secret-key-0001"),
    )
    summary = settings.safe_summary()
    assert summary["access_key_configured"] is True
    assert summary["secret_key_configured"] is True
    assert "access_key" not in summary
    assert "secret_key" not in summary
    blob = str(summary)
    assert "local-dev-access-key-0001" not in blob


def test_app_settings_requires_kafka_when_writer_enabled() -> None:
    with pytest.raises(ValueError, match="KAFKA__ENABLED"):
        AppSettings(
            environment=AppEnvironment.TEST,
            bootstrap_auth_enabled=False,
            iceberg_writer=IcebergWriterSettings(
                enabled=True,
                catalog_type="sql",
                catalog_uri="sqlite:////tmp/c.db",
                warehouse="file:///tmp/wh",
            ),
        )


def test_auto_create_forbidden_in_production() -> None:
    with pytest.raises(ValueError, match="AUTO_CREATE_TABLES"):
        AppSettings(
            environment=AppEnvironment.PRODUCTION,
            debug=False,
            bootstrap_auth_enabled=False,
            kafka={"enabled": True, "bootstrap_servers": ["localhost:9092"]},
            iceberg_writer=IcebergWriterSettings(
                enabled=True,
                catalog_type="sql",
                catalog_uri="sqlite:////tmp/c.db",
                warehouse="file:///tmp/wh",
                auto_create_tables=True,
            ),
        )


def test_embedded_credentials_in_uri_rejected() -> None:
    with pytest.raises(ValueError, match="embed credentials"):
        IcebergWriterSettings(
            enabled=True,
            catalog_type="rest",
            catalog_uri="http://user:pass@catalog:8181",
            warehouse="s3://bergama-warehouse/",
            access_key=SecretStr("local-dev-access-key-0001"),
            secret_key=SecretStr("local-dev-secret-key-0001"),
        )
