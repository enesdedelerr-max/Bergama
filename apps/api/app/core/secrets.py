"""Typed secret settings boundary (Issues #204 / #205).

Provider-agnostic: values come from environment or local `.secrets.env` only.
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

_SECRET_FIELD_NAMES: Final[tuple[str, ...]] = (
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
        description="Optional reserved application secret; not required by current runtime.",
    )
    bootstrap_jwt_signing_key: SecretStr | None = Field(
        default=None,
        description="HS256 signing key for local/test JWT bootstrap (#205).",
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
        for name in _SECRET_FIELD_NAMES:
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

    def validate_bootstrap_signing_key(self) -> None:
        """Require a strong bootstrap JWT signing key when bootstrap auth is enabled."""
        secret = self.bootstrap_jwt_signing_key
        if secret is None:
            msg = (
                "BERGAMA_SECRETS__BOOTSTRAP_JWT_SIGNING_KEY is required when "
                "bootstrap auth is enabled"
            )
            raise ValueError(msg)
        raw = secret.get_secret_value()
        if raw.lower() in _PLACEHOLDER_VALUES:
            msg = "BERGAMA_SECRETS__BOOTSTRAP_JWT_SIGNING_KEY must not use a placeholder value"
            raise ValueError(msg)
        if len(raw) < MIN_CRYPTO_SECRET_LENGTH:
            msg = (
                "BERGAMA_SECRETS__BOOTSTRAP_JWT_SIGNING_KEY must be at least "
                f"{MIN_CRYPTO_SECRET_LENGTH} characters"
            )
            raise ValueError(msg)
