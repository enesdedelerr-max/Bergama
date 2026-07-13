"""Typed registry errors with stable machine-readable codes."""

from __future__ import annotations


class RegistryError(Exception):
    """Base registry loader error."""

    code: str = "registry.error"

    def __init__(self, message: str, *, path: str | None = None) -> None:
        self.path = path
        super().__init__(message)


class RegistryPathNotFoundError(RegistryError):
    code = "registry.path_not_found"


class RegistryPathOutsideRootError(RegistryError):
    code = "registry.path_outside_root"


class RegistryFileTooLargeError(RegistryError):
    code = "registry.file_too_large"


class RegistryUnsupportedExtensionError(RegistryError):
    code = "registry.unsupported_extension"


class RegistryParseFailedError(RegistryError):
    code = "registry.parse_failed"


class RegistryInvalidRootError(RegistryError):
    code = "registry.invalid_root"


class RegistrySchemaInvalidError(RegistryError):
    code = "registry.schema_invalid"


class RegistryUnsupportedSchemaVersionError(RegistryError):
    code = "registry.unsupported_schema_version"


class RegistryDuplicateIdError(RegistryError):
    code = "registry.duplicate_id"


class RegistryDuplicateKeyError(RegistryError):
    code = "registry.duplicate_key"


class RegistryMissingRequiredError(RegistryError):
    code = "registry.missing_required"


class RegistryDependencyMissingError(RegistryError):
    code = "registry.dependency_missing"


class RegistryDependencyCycleError(RegistryError):
    code = "registry.dependency_cycle"


class RegistrySelfDependencyError(RegistryError):
    code = "registry.self_dependency"


class RegistryFingerprintFailedError(RegistryError):
    code = "registry.fingerprint_failed"


class RegistryNotLoadedError(RegistryError):
    code = "registry.not_loaded"


class RegistryNotFoundError(RegistryError):
    code = "registry.not_found"


class RegistrySymlinkRejectedError(RegistryError):
    code = "registry.path_outside_root"
