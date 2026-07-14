"""Typed Iceberg writer errors (#307). Messages must not include secrets or raw payloads."""

from __future__ import annotations


class IcebergWriterError(Exception):
    """Base fail-closed Iceberg writer error."""

    code: str = "iceberg_writer.error"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        if code is not None:
            self.code = code


class IcebergEnvelopeError(IcebergWriterError):
    code = "iceberg_writer.envelope"


class IcebergSchemaVersionError(IcebergWriterError):
    code = "iceberg_writer.unsupported_schema_version"


class IcebergCanonicalError(IcebergWriterError):
    code = "iceberg_writer.canonical"


class IcebergUnknownRouteError(IcebergWriterError):
    code = "iceberg_writer.unknown_route"


class IcebergMappingError(IcebergWriterError):
    code = "iceberg_writer.mapping"


class IcebergDecimalError(IcebergWriterError):
    code = "iceberg_writer.decimal"


class IcebergBatchError(IcebergWriterError):
    code = "iceberg_writer.batch"


class IcebergDuplicateBatchKeyError(IcebergWriterError):
    code = "iceberg_writer.duplicate_batch_key"


class IcebergCatalogError(IcebergWriterError):
    code = "iceberg_writer.catalog"


class IcebergObjectStoreError(IcebergWriterError):
    code = "iceberg_writer.object_store"


class IcebergParquetError(IcebergWriterError):
    code = "iceberg_writer.parquet"


class IcebergAppendError(IcebergWriterError):
    code = "iceberg_writer.append"


class IcebergSnapshotError(IcebergWriterError):
    code = "iceberg_writer.snapshot"


class IcebergTableMissingError(IcebergWriterError):
    code = "iceberg_writer.table_missing"


class IcebergOffsetCommitError(IcebergWriterError):
    code = "iceberg_writer.offset_commit"


class IcebergShutdownFlushError(IcebergWriterError):
    code = "iceberg_writer.shutdown_flush"


class IcebergConfigurationError(IcebergWriterError):
    code = "iceberg_writer.configuration"
