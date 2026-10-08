"""Firewall tests for Intelligence Run WS1/WS2/WS3 package boundaries."""

from __future__ import annotations

import ast
import tomllib
from pathlib import Path

from app.core.config import AppSettings
from app.core.environment import AppEnvironment
from app.core.secrets import SecretSettings
from app.factory import create_app
from tests.conftest import VALID_PROD_JWT_SECRET

REPO_ROOT = Path(__file__).resolve().parents[4]
API_ROOT = REPO_ROOT / "apps" / "api"
PACKAGE_ROOT = API_ROOT / "app" / "intelligence_runs"
PIPELINE_ROOT = API_ROOT / "app" / "intelligence_pipeline"
ROUTER_PATH = API_ROOT / "app" / "routers" / "intelligence_runs.py"

FORBIDDEN_DIRECT_DEPS = {
    "asyncpg",
    "psycopg2",
    "psycopg2-binary",
    "testcontainers",
    "uuid6",
    "uuid7",
    "ulid",
    "python-ulid",
    "peewee",
    "tortoise-orm",
    "django",
    "databases",
}

# WS2 may import PipelineResult into materializer/snapshot modules only.
_WS2_PIPELINE_IMPORT_ALLOWLIST = frozenset({"materializer.py", "snapshot.py"})

_EXPECTED_PRODUCT_GET_PATHS = {
    "/api/v1/intelligence/runs/id/{run_id}",
    "/api/v1/intelligence/runs/fingerprint/{fingerprint}",
    "/api/v1/intelligence/runs/latest-dashboard-capable",
    "/api/v1/intelligence/runs/id/{run_id}/dashboard",
    "/api/v1/intelligence/runs/id/{run_id}/human-review",
    "/api/v1/intelligence/runs/id/{run_id}/ade",
}


def _top_level_requirement(raw: str) -> str:
    text = raw.strip().lower()
    for sep in ("[", "==", ">=", "<=", "~=", "!=", ">", "<"):
        if sep in text:
            text = text.split(sep, 1)[0]
    return text.strip()


def test_dependency_firewall_no_unauthorized_direct_deps() -> None:
    pyproject = tomllib.loads((API_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    deps = [_top_level_requirement(item) for item in pyproject["project"]["dependencies"]]
    for forbidden in FORBIDDEN_DIRECT_DEPS:
        assert forbidden not in deps
    assert "sqlalchemy" in deps
    assert "alembic" in deps
    assert "psycopg" in deps


def test_pipeline_remains_db_free() -> None:
    forbidden_prefixes = (
        "sqlalchemy",
        "alembic",
        "psycopg",
        "app.intelligence_runs",
    )
    for path in PIPELINE_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith(forbidden_prefixes)
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith(forbidden_prefixes)


def test_ws3_package_has_query_without_write_or_pipeline_recompute() -> None:
    names = {path.name for path in PACKAGE_ROOT.glob("*.py")}
    assert "materializer.py" in names
    assert "snapshot.py" in names
    assert "query_service.py" in names
    assert "product_errors.py" in names
    assert "router.py" not in names  # HTTP router lives under app/routers/
    for path in PACKAGE_ROOT.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "APIRouter" not in text
        assert "evaluate_ade" not in text
        assert "run_intelligence_pipeline" not in text
        tree = ast.parse(text, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imports_pipeline_result = (
                    node.module.startswith("app.intelligence_pipeline")
                    and any(alias.name == "PipelineResult" for alias in node.names)
                ) or any(alias.name == "PipelineResult" for alias in node.names)
                if imports_pipeline_result:
                    assert path.name in _WS2_PIPELINE_IMPORT_ALLOWLIST


def test_exactly_six_product_get_routes_no_writes() -> None:
    settings = AppSettings(
        environment=AppEnvironment.LOCAL,
        debug=True,
        bootstrap_auth_enabled=True,
        secrets=SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
    )
    application = create_app(settings)
    openapi_paths = application.openapi()["paths"]
    product_paths = {path for path in openapi_paths if path.startswith("/api/v1/intelligence/runs")}
    assert product_paths == _EXPECTED_PRODUCT_GET_PATHS
    for path in product_paths:
        methods = {method.upper() for method in openapi_paths[path]}
        assert methods == {"GET"}
    joined = " ".join(sorted(product_paths))
    assert "search" not in joined
    assert "history" not in joined
    assert "/list" not in joined


def test_router_enforces_product_scope_dependency() -> None:
    text = ROUTER_PATH.read_text(encoding="utf-8")
    assert "require_intelligence_runs_read" in text
    assert text.count("require_intelligence_runs_read") >= 6
    assert "APIRouter" in text
    for forbidden in ("evaluate_ade", "run_intelligence_pipeline", "materialize("):
        assert forbidden not in text


def test_no_ws4_authorization_platform_leakage() -> None:
    # WS3 may add minimal scope wiring only; forbid broad authz platforms.
    forbidden_filenames = {
        "authorization_policy_engine.py",
        "rbac_engine.py",
        "policy_engine.py",
    }
    for path in (API_ROOT / "app").rglob("*.py"):
        assert path.name not in forbidden_filenames


def test_no_new_alembic_migration_for_ws3() -> None:
    versions = API_ROOT / "alembic" / "versions"
    # WS1 migration remains the sole intelligence_runs schema migration.
    names = sorted(p.name for p in versions.glob("*.py") if p.name != "__pycache__")
    assert any("intelligence_runs" in name for name in names)
    # Guard: no WS3-named migration artifact.
    assert not any("ws3" in name.lower() or "query" in name.lower() for name in names)
