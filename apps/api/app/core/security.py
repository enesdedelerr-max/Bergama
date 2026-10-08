"""Auth/security constants for JWT bootstrap (Issue #205)."""

from __future__ import annotations

from typing import Final, Literal

JwtAlgorithm = Literal["HS256"]

JWT_ALGORITHM_HS256: Final[JwtAlgorithm] = "HS256"
TOKEN_TYPE_ACCESS: Final = "access"

BOOTSTRAP_SUBJECT: Final = "local-bootstrap-user"
BOOTSTRAP_ROLES: Final[tuple[str, ...]] = ("developer",)
# Bootstrap carries both general API read and the dedicated product read scope.
# ``api:read`` alone remains insufficient for Intelligence Run product routes.
INTELLIGENCE_RUNS_READ_SCOPE: Final = "intelligence:runs:read"
API_READ_SCOPE: Final = "api:read"
BOOTSTRAP_SCOPES: Final[tuple[str, ...]] = (API_READ_SCOPE, INTELLIGENCE_RUNS_READ_SCOPE)
BOOTSTRAP_GRANT_TYPE: Final = "bootstrap"
