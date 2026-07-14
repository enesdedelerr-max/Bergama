"""Iceberg catalog factory and table bootstrap helpers (#307)."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from pyiceberg.catalog import Catalog, load_catalog
from pyiceberg.exceptions import NoSuchTableError, TableAlreadyExistsError

from app.core.environment import AppEnvironment
from app.core.iceberg_writer_settings import IcebergWriterSettings
from app.infrastructure.iceberg.errors import (
    IcebergCatalogError,
    IcebergConfigurationError,
    IcebergTableMissingError,
)
from app.infrastructure.iceberg.routing import all_table_bases
from app.infrastructure.iceberg.schemas import day_partition_spec, schema_for_table


def build_catalog(settings: IcebergWriterSettings) -> Catalog:
    """Build REST or SQL catalog from settings. Credentials never logged."""
    if not settings.catalog_uri or not settings.warehouse:
        msg = "catalog_uri and warehouse are required"
        raise IcebergConfigurationError(msg)
    try:
        if settings.catalog_type == "sql":
            return _build_sql_catalog(settings)
        return _build_rest_catalog(settings)
    except IcebergConfigurationError:
        raise
    except Exception as exc:
        msg = "Iceberg catalog initialization failed"
        raise IcebergCatalogError(msg) from exc


def _build_sql_catalog(settings: IcebergWriterSettings) -> Catalog:
    uri = settings.catalog_uri or ""
    warehouse = settings.warehouse or ""
    _ensure_sql_paths(uri, warehouse)
    return load_catalog(
        "bergama-iceberg-sql",
        **{
            "type": "sql",
            "uri": uri,
            "warehouse": warehouse,
        },
    )


def _build_rest_catalog(settings: IcebergWriterSettings) -> Catalog:
    props: dict[str, Any] = {
        "type": "rest",
        "uri": settings.catalog_uri,
        "warehouse": settings.warehouse,
        "s3.region": settings.s3_region,
        "s3.force-virtual-addressing": str(not settings.path_style_access).lower(),
    }
    if settings.s3_endpoint:
        props["s3.endpoint"] = settings.s3_endpoint
    if settings.access_key is not None:
        props["s3.access-key-id"] = settings.access_key.get_secret_value()
    if settings.secret_key is not None:
        props["s3.secret-access-key"] = settings.secret_key.get_secret_value()
    return load_catalog("bergama-iceberg-rest", **props)


def _ensure_sql_paths(catalog_uri: str, warehouse: str) -> None:
    if catalog_uri.startswith("sqlite:///"):
        path_part = catalog_uri.removeprefix("sqlite:///")
        if path_part not in {":memory:", "/:memory:"} and not path_part.endswith(":memory:"):
            Path(path_part).parent.mkdir(parents=True, exist_ok=True)
    wh = urlparse(warehouse)
    if wh.scheme == "file":
        Path(wh.path).mkdir(parents=True, exist_ok=True)


def ensure_namespace(catalog: Catalog, namespace: str) -> None:
    try:
        existing = catalog.list_namespaces()
        normalized = {(ns if isinstance(ns, str) else ns[0]) for ns in existing}
        if namespace in normalized:
            return
        catalog.create_namespace(namespace)
    except Exception as exc:
        try:
            catalog.create_namespace(namespace)
            return
        except Exception:
            msg = "failed to ensure Iceberg namespace"
            raise IcebergCatalogError(msg) from exc


def table_identifier(namespace: str, table_name: str) -> str:
    return f"{namespace}.{table_name}"


def load_required_table(catalog: Catalog, *, namespace: str, table_name: str) -> Any:
    ident = table_identifier(namespace, table_name)
    try:
        return catalog.load_table(ident)
    except NoSuchTableError as exc:
        msg = f"required Iceberg table missing: {ident}"
        raise IcebergTableMissingError(msg) from exc
    except Exception as exc:
        msg = f"failed to load Iceberg table {ident}"
        raise IcebergCatalogError(msg) from exc


def ensure_market_tables(
    catalog: Catalog,
    settings: IcebergWriterSettings,
    *,
    environment: AppEnvironment,
) -> None:
    """Create namespace + tables when auto_create_tables is explicitly enabled."""
    if not settings.auto_create_tables:
        msg = "ensure_market_tables requires auto_create_tables=true"
        raise IcebergConfigurationError(msg)
    if environment not in {AppEnvironment.LOCAL, AppEnvironment.TEST}:
        msg = "auto_create_tables is only allowed in local/test environments"
        raise IcebergConfigurationError(msg)
    ensure_namespace(catalog, settings.namespace)
    for base in all_table_bases():
        name = f"{settings.table_prefix}{base}" if settings.table_prefix else base
        ident = table_identifier(settings.namespace, name)
        try:
            catalog.create_table(
                ident,
                schema=schema_for_table(base),
                partition_spec=day_partition_spec(),
            )
        except TableAlreadyExistsError:
            continue
        except Exception as exc:
            try:
                catalog.load_table(ident)
            except Exception:
                msg = f"failed to create Iceberg table {ident}"
                raise IcebergCatalogError(msg) from exc


def require_tables_present(catalog: Catalog, settings: IcebergWriterSettings) -> None:
    for base in all_table_bases():
        name = f"{settings.table_prefix}{base}" if settings.table_prefix else base
        load_required_table(catalog, namespace=settings.namespace, table_name=name)


def build_offline_sql_settings(warehouse_dir: Path) -> IcebergWriterSettings:
    """Test helper settings: SqlCatalog + file warehouse, auto-create enabled."""
    warehouse_dir.mkdir(parents=True, exist_ok=True)
    db_path = warehouse_dir / "catalog.db"
    return IcebergWriterSettings(
        enabled=True,
        catalog_type="sql",
        catalog_uri=f"sqlite:///{db_path}",
        warehouse=f"file://{warehouse_dir}",
        namespace="bergama",
        auto_create_tables=True,
        batch_max_records=100,
        batch_max_bytes=1_048_576,
        flush_interval_seconds=2.0,
    )
