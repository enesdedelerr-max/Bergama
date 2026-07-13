"""Auth/security constants for JWT bootstrap (Issue #205)."""

from __future__ import annotations

from typing import Final, Literal

JwtAlgorithm = Literal["HS256"]

JWT_ALGORITHM_HS256: Final[JwtAlgorithm] = "HS256"
TOKEN_TYPE_ACCESS: Final = "access"

BOOTSTRAP_SUBJECT: Final = "local-bootstrap-user"
BOOTSTRAP_ROLES: Final[tuple[str, ...]] = ("developer",)
BOOTSTRAP_SCOPES: Final[tuple[str, ...]] = ("api:read",)
BOOTSTRAP_GRANT_TYPE: Final = "bootstrap"
