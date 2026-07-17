"""Independent version axes for SDK compatibility."""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

_SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-(?:0|[1-9]\d*|[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|[a-zA-Z-][0-9a-zA-Z-]*))*)?"
    r"(?:\+[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*)?$"
)


def parse_semver(value: str) -> tuple[int, int, int]:
    text = value.strip()
    if not _SEMVER_RE.fullmatch(text):
        msg = f"invalid semantic version {value!r}"
        raise ValueError(msg)
    major_text, _, rest = text.partition(".")
    minor_text, _, patch_text = rest.partition(".")
    patch_text = patch_text.split("-", 1)[0].split("+", 1)[0]
    return int(major_text), int(minor_text), int(patch_text)


class VersionAxes(BaseModel):
    """Five independent version axes — none may be overloaded."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    sdk_schema_version: str = Field(min_length=1, max_length=32)
    runtime_protocol_version: str = Field(min_length=1, max_length=32)
    strategy_version: str = Field(min_length=1, max_length=64)
    feature_schema_version: str = Field(min_length=1, max_length=32)
    config_schema_version: str = Field(min_length=1, max_length=32)

    @field_validator(
        "sdk_schema_version",
        "runtime_protocol_version",
        "strategy_version",
        "feature_schema_version",
        "config_schema_version",
    )
    @classmethod
    def validate_semver(cls, value: str) -> str:
        parse_semver(value)
        return value.strip()


def is_sdk_backward_compatible(
    *,
    required: VersionAxes,
    supported_sdk_schema_version: str,
    supported_runtime_protocol_version: str,
    supported_feature_schema_version: str,
    supported_config_schema_version: str,
) -> bool:
    """Fail-closed compatibility: same major required; supported minor >= required."""
    req_sdk = parse_semver(required.sdk_schema_version)
    sup_sdk = parse_semver(supported_sdk_schema_version)
    if req_sdk[0] != sup_sdk[0] or sup_sdk < req_sdk:
        return False
    req_rt = parse_semver(required.runtime_protocol_version)
    sup_rt = parse_semver(supported_runtime_protocol_version)
    if req_rt[0] != sup_rt[0] or sup_rt < req_rt:
        return False
    req_feat = parse_semver(required.feature_schema_version)
    sup_feat = parse_semver(supported_feature_schema_version)
    if req_feat[0] != sup_feat[0] or sup_feat < req_feat:
        return False
    req_cfg = parse_semver(required.config_schema_version)
    sup_cfg = parse_semver(supported_config_schema_version)
    if req_cfg[0] != sup_cfg[0] or sup_cfg < req_cfg:
        return False
    return True
