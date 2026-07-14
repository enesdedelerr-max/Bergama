"""Validate Sprint 2 OpenAPI document and write evidence."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "scripts" / "gates") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts" / "gates"))

from sprint2_common import ensure_no_secrets, write_json  # noqa: E402


def _load_openapi() -> dict[object, object]:
    # Import app in-process; avoid long-lived server.
    sys.path.insert(0, str(ROOT / "apps" / "api"))
    from app.core.config import AppSettings
    from app.core.environment import AppEnvironment
    from app.core.secrets import SecretSettings
    from app.factory import create_app

    settings = AppSettings(
        environment=AppEnvironment.TEST,
        bootstrap_auth_enabled=True,
        secrets=SecretSettings(
            bootstrap_jwt_signing_key="sprint2-gate-bootstrap-jwt-signing-key-32b"
        ),
        docs_enabled=True,
        openapi_enabled=True,
    )
    app = create_app(settings)
    schema = app.openapi()
    if not isinstance(schema, dict):
        msg = "openapi schema must be an object"
        raise TypeError(msg)
    return schema


def validate(schema: dict[object, object]) -> None:
    info = schema.get("info")
    if not isinstance(info, dict):
        raise RuntimeError("OpenAPI info missing")
    if not info.get("title") or not info.get("version"):
        raise RuntimeError("OpenAPI title/version required")

    paths = schema.get("paths")
    if not isinstance(paths, dict):
        raise RuntimeError("OpenAPI paths missing")

    required_paths = (
        "/health/live",
        "/health/startup",
        "/health/ready",
        "/api/v1/auth/token",
        "/api/v1/auth/me",
    )
    for path in required_paths:
        if path not in paths:
            raise RuntimeError(f"missing OpenAPI path {path}")

    components = schema.get("components")
    if not isinstance(components, dict):
        raise RuntimeError("OpenAPI components missing")
    security_schemes = components.get("securitySchemes")
    if not isinstance(security_schemes, dict):
        raise RuntimeError("OpenAPI securitySchemes missing")
    scheme_names = {str(k).lower() for k in security_schemes}
    if not any("bearer" in name for name in scheme_names):
        raise RuntimeError("Bearer security scheme missing")

    me = paths["/api/v1/auth/me"]
    if not isinstance(me, dict) or "get" not in me:
        raise RuntimeError("/auth/me GET missing")
    get_op = me["get"]
    if not isinstance(get_op, dict):
        raise RuntimeError("/auth/me GET invalid")
    security = get_op.get("security")
    if not security:
        raise RuntimeError("/auth/me must declare bearer security")

    encoded = json.dumps(schema)
    ensure_no_secrets(encoded, context="openapi")
    banned = ("bootstrap_jwt_signing_key", "app_secret_key", "/internal/test")
    for token in banned:
        if token in encoded:
            raise RuntimeError(f"forbidden token in OpenAPI: {token}")


def main() -> int:
    schema = _load_openapi()
    validate(schema)
    out = ROOT / "artifacts" / "sprint2" / "evidence" / "openapi.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    # Convert to plain JSON-friendly dict[str, object] via dump/load.
    write_json(out, json.loads(json.dumps(schema)))
    print(f"validate-api-openapi PASS -> {out}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"validate-api-openapi FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
