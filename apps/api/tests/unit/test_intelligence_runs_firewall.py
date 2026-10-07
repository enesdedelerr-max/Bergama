"""Firewall tests for Intelligence Run WS1/WS2 package boundaries."""

from __future__ import annotations

import ast
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
API_ROOT = REPO_ROOT / "apps" / "api"
PACKAGE_ROOT = API_ROOT / "app" / "intelligence_runs"
PIPELINE_ROOT = API_ROOT / "app" / "intelligence_pipeline"

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


def test_ws2_package_has_materializer_without_http_or_query_surface() -> None:
    names = {path.name for path in PACKAGE_ROOT.glob("*.py")}
    assert "materializer.py" in names
    assert "snapshot.py" in names
    assert "query_service.py" not in names
    assert "router.py" not in names
    for path in PACKAGE_ROOT.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "APIRouter" not in text
        tree = ast.parse(text, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imports_pipeline_result = (
                    node.module.startswith("app.intelligence_pipeline")
                    and any(alias.name == "PipelineResult" for alias in node.names)
                ) or any(alias.name == "PipelineResult" for alias in node.names)
                if imports_pipeline_result:
                    assert path.name in _WS2_PIPELINE_IMPORT_ALLOWLIST
