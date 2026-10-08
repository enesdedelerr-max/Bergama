"""Firewall tests for Intelligence Run WS1–WS4 package boundaries."""

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
REPOSITORY_PATH = PACKAGE_ROOT / "repository.py"
AUTHZ_PATH = API_ROOT / "app" / "deps" / "authz.py"
INTELLIGENCE_RUNS_DEPS_PATH = API_ROOT / "app" / "deps" / "intelligence_runs.py"
SCHEMAS_PATH = API_ROOT / "app" / "schemas" / "intelligence_runs.py"

# Repo-derived authority domains only (WS4 AST firewall). Prefix match, not substring.
_FORBIDDEN_AUTHORITY_IMPORT_PREFIXES = (
    "app.broker",
    "app.orders",
    "app.features",
    "app.infrastructure.polygon",
)

_AUTHORITY_PROTECTED_PATHS: tuple[Path, ...] = (
    *sorted(PACKAGE_ROOT.rglob("*.py")),
    ROUTER_PATH,
    INTELLIGENCE_RUNS_DEPS_PATH,
    AUTHZ_PATH,
    SCHEMAS_PATH,
)

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


def _module_matches_forbidden_prefix(module: str, prefix: str) -> bool:
    return module == prefix or module.startswith(f"{prefix}.")


def _imported_module_targets(node: ast.AST) -> list[str]:
    """Resolve Import / ImportFrom targets including ``from app import broker`` → app.broker."""
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if isinstance(node, ast.ImportFrom) and node.module:
        targets = [node.module]
        for alias in node.names:
            if alias.name == "*":
                continue
            targets.append(f"{node.module}.{alias.name}")
        return targets
    return []


def test_authority_import_firewall_blocks_broker_oms_features_providers() -> None:
    """WS4-15: product read surfaces must not import broker/OMS/FP/live-provider packages."""
    for path in _AUTHORITY_PROTECTED_PATHS:
        assert path.is_file(), f"missing protected surface: {path}"
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            for module in _imported_module_targets(node):
                for prefix in _FORBIDDEN_AUTHORITY_IMPORT_PREFIXES:
                    assert not _module_matches_forbidden_prefix(module, prefix), (
                        f"forbidden authority import {module!r} in protected file {path} "
                        f"(prefix {prefix!r})"
                    )


def test_authority_import_target_resolution_covers_from_app_import_form() -> None:
    """R2: ``from app import broker`` must resolve to the forbidden ``app.broker`` target."""
    tree = ast.parse("from app import broker, orders\nfrom app.infrastructure import polygon\n")
    targets: list[str] = []
    for node in tree.body:
        targets.extend(_imported_module_targets(node))
    assert "app.broker" in targets
    assert "app.orders" in targets
    assert "app.infrastructure.polygon" in targets
    forbidden_hits = [
        module
        for module in targets
        for prefix in _FORBIDDEN_AUTHORITY_IMPORT_PREFIXES
        if _module_matches_forbidden_prefix(module, prefix)
    ]
    assert set(forbidden_hits) >= {"app.broker", "app.orders", "app.infrastructure.polygon"}


def test_latest_dashboard_candidate_has_no_jsonb_typeof_payload_health_prefilter() -> None:
    """WS4-09 structural guard: no jsonb_typeof payload-health filter before LIMIT 1."""
    source = REPOSITORY_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(REPOSITORY_PATH))
    method: ast.FunctionDef | ast.AsyncFunctionDef | None = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "SqlAlchemyIntelligenceRunRepository":
            for child in node.body:
                if (
                    isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and child.name == "get_latest_dashboard_storage_candidate"
                ):
                    method = child
                    break
    assert method is not None, "get_latest_dashboard_storage_candidate missing"
    method_source = ast.get_source_segment(source, method)
    assert method_source is not None
    # Ban payload-health prefiltering via jsonb_typeof before LIMIT 1 (WS3 defect).
    assert "jsonb_typeof" not in method_source


def test_no_new_alembic_migration_for_ws3() -> None:
    versions = API_ROOT / "alembic" / "versions"
    # WS1 migration remains the sole intelligence_runs schema migration.
    names = sorted(p.name for p in versions.glob("*.py") if p.name != "__pycache__")
    assert any("intelligence_runs" in name for name in names)
    # Guard: no WS3-named migration artifact.
    assert not any("ws3" in name.lower() or "query" in name.lower() for name in names)
