"""Typed secret settings boundary (Issue #204).

Provider-agnostic: values come from environment or local `.secrets.env` only.
No Vault / cloud secret-manager clients here.
"""

from __future__ import annotations

from typing import Final, Self

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator, model_validator

# Cryptographic / signing material — explicit minimum length (not password-strength heuristics).
MIN_CRYPTO_SECRET_LENGTH: Final = 32

_PLACEHOLDER_VALUES: Final[frozenset[str]] = frozenset(
    {
        "changeme",
        "password",
        "secret",
        "default",
        "example",
        "test",
    }
)

_REQUIRED_PRODUCTION_FIELDS: Final[tuple[str, ...]] = (
    "app_secret_key",
    "bootstrap_jwt_signing_key",
)


class SecretSettings(BaseModel):
    """Nested secret settings loaded via ``BERGAMA_SECRETS__*`` (or local `.secrets.env`)."""

    model_config = ConfigDict(
        extra="forbid",
        validate_default=True,
        hide_input_in_errors=True,
    )

    app_secret_key: SecretStr | None = Field(
        default=None,
        description="Application secret key reserved for upcoming auth/session use (#205+).",
    )
    bootstrap_jwt_signing_key: SecretStr | None = Field(
        default=None,
        description="JWT signing key reserved for Issue #205 bootstrap; unused until auth lands.",
    )

    @field_validator("app_secret_key", "bootstrap_jwt_signing_key", mode="before")
    @classmethod
    def reject_blank_and_whitespace(cls, value: object) -> object:
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
        return raw

    @model_validator(mode="after")
    def reject_empty_secret_str(self) -> Self:
        for name in _REQUIRED_PRODUCTION_FIELDS:
            secret = getattr(self, name)
            if isinstance(secret, SecretStr) and secret.get_secret_value() == "":
                msg = f"{name} must not be empty"
                raise ValueError(msg)
        return self

    def configured_flags(self) -> dict[str, bool]:
        """Operational indicators — never values."""
        return {
            "app_secret_key_configured": self.app_secret_key is not None,
            "bootstrap_jwt_signing_key_configured": self.bootstrap_jwt_signing_key is not None,
        }

    def safe_summary(self) -> dict[str, bool]:
        """Redacted operational summary."""
        return self.configured_flags()

    def validate_for_environment(self, *, production_like: bool) -> None:
        """Fail fast for staging/production; local/test may omit secrets."""
        if not production_like:
            return
        for name in _REQUIRED_PRODUCTION_FIELDS:
            secret: SecretStr | None = getattr(self, name)
            if secret is None:
                msg = (
                    f"BERGAMA_SECRETS__{name.upper()} is required when "
                    "BERGAMA_ENVIRONMENT is staging or production"
                )
                raise ValueError(msg)
            raw = secret.get_secret_value()
            if raw.lower() in _PLACEHOLDER_VALUES:
                msg = f"BERGAMA_SECRETS__{name.upper()} must not use a placeholder value"
                raise ValueError(msg)
            if len(raw) < MIN_CRYPTO_SECRET_LENGTH:
                msg = (
                    f"BERGAMA_SECRETS__{name.upper()} must be at least "
                    f"{MIN_CRYPTO_SECRET_LENGTH} characters"
                )
                raise ValueError(msg)
