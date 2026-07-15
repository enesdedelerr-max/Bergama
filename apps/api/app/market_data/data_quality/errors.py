"""Typed data-quality errors (#310)."""

from __future__ import annotations


class DataQualityError(Exception):
    """Base typed data-quality failure. Messages must be safe."""

    code: str = "data_quality.error"

    def __init__(self, code: str | None = None, *, detail: str | None = None) -> None:
        self.code = code or self.code
        self.detail = detail
        message = self.code if detail is None else f"{self.code}: {detail}"
        super().__init__(message)


class DataQualityPolicyError(DataQualityError):
    code = "data_quality.policy_invalid"


class DataQualityPolicyNotFoundError(DataQualityPolicyError):
    code = "data_quality.policy_not_found"


class DataQualityPolicyFileTooLargeError(DataQualityPolicyError):
    code = "data_quality.policy_file_too_large"


class DataQualityPolicySymlinkRejectedError(DataQualityPolicyError):
    code = "data_quality.policy_symlink_rejected"


class DataQualityPolicyPathError(DataQualityPolicyError):
    code = "data_quality.policy_path_invalid"


class DataQualityPolicyParseError(DataQualityPolicyError):
    code = "data_quality.policy_parse_failed"


class DataQualityQuarantineUnavailableError(DataQualityError):
    code = "data_quality.quarantine_unavailable"


class DataQualityHaltError(DataQualityError):
    code = "data_quality.halt"
