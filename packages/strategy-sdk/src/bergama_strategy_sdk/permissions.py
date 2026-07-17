"""Plugin permission declarations."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, model_validator


class PluginPermissions(BaseModel):
    """Declared plugin permissions — MVP accepts empty/restricted set only."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    network: bool = False
    filesystem: bool = False
    environment: bool = False
    secrets: bool = False
    subprocess: bool = False
    imports: bool = False
    external_libraries: bool = False

    @classmethod
    def empty(cls) -> PluginPermissions:
        return cls()

    @model_validator(mode="after")
    def reject_unsafe_permissions(self) -> PluginPermissions:
        unsafe = [
            name
            for name, value in self.model_dump(mode="python").items()
            if isinstance(value, bool) and value
        ]
        if unsafe:
            msg = f"unsupported plugin permissions requested: {', '.join(unsafe)}"
            raise ValueError(msg)
        return self

    def requested_permissions(self) -> tuple[str, ...]:
        return tuple(
            name
            for name, value in self.model_dump(mode="python").items()
            if isinstance(value, bool) and value
        )
