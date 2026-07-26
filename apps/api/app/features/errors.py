"""Typed Feature Platform failures."""

from __future__ import annotations


class FeaturePlatformError(Exception):
    code = "feature_platform.error"

    def __init__(self, message: str | None = None, *, detail: str | None = None) -> None:
        super().__init__(message or self.code)
        self.detail = detail


class FeaturePlatformDisabledError(FeaturePlatformError):
    code = "feature_platform.disabled"


class FeaturePlatformUnsupportedEventError(FeaturePlatformError):
    code = "feature_platform.unsupported_event"


class FeaturePlatformValidationError(FeaturePlatformError):
    code = "feature_platform.validation_failed"
