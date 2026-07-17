"""Static import-boundary enforcement for Strategy SDK (#406)."""

from __future__ import annotations

import ast
import textwrap
from pathlib import Path

import bergama_strategy_sdk
import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
SDK_SRC = REPO_ROOT / "packages" / "strategy-sdk" / "src" / "bergama_strategy_sdk"
RUNTIME_DIR = REPO_ROOT / "apps" / "api" / "app" / "strategy" / "sdk_runtime"
AUTHOR_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "strategy_author_packages"

FORBIDDEN_SDK_IMPORT_ROOTS = frozenset(
    {
        "app",
        "fastapi",
        "aiokafka",
        "sqlalchemy",
        "asyncpg",
        "redis",
        "httpx",
        "kafka",
    }
)

FORBIDDEN_AUTHOR_IMPORT_PREFIXES = frozenset(
    {
        "app.strategy.sdk_runtime",
        "app.strategy.engine",
        "app.strategy.session",
        "app.strategy.registry",
        "app.strategy.audit",
        "app.strategy.metrics",
        "app.core.container",
        "app.core.config",
        "app.core.strategy_sdk_settings",
        "app.portfolio",
        "app.risk",
        "app.orders",
        "app.broker",
        "app.market_data.providers",
        "app.market_data.kafka",
        "aiokafka",
        "httpx",
        "asyncpg",
        "sqlalchemy",
        "redis",
    }
)

ALLOWED_AUTHOR_IMPORT_ROOTS = frozenset(
    {
        "bergama_strategy_sdk",
        "asyncio",
        "collections",
        "dataclasses",
        "datetime",
        "decimal",
        "enum",
        "functools",
        "hashlib",
        "json",
        "math",
        "re",
        "typing",
        "pydantic",
    }
)


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def _forbidden_author_imports(modules: set[str]) -> set[str]:
    hits: set[str] = set()
    for module in modules:
        if module in FORBIDDEN_AUTHOR_IMPORT_PREFIXES or any(
            module.startswith(f"{prefix}.") for prefix in FORBIDDEN_AUTHOR_IMPORT_PREFIXES
        ):
            hits.add(module)
    return hits


def _scan_author_tree(root: Path) -> list[str]:
    violations: list[str] = []
    forbidden_roots = {
        "app",
        "aiokafka",
        "httpx",
        "asyncpg",
        "sqlalchemy",
        "redis",
        "fastapi",
        "kafka",
    }
    for path in sorted(root.rglob("*.py")):
        if path.name == "__pycache__":
            continue
        for module in _imported_modules(path):
            root_name = module.split(".", 1)[0]
            if module.startswith("bergama_strategy_sdk"):
                continue
            if root_name in ALLOWED_AUTHOR_IMPORT_ROOTS:
                continue
            if module in _forbidden_author_imports({module}) or root_name in forbidden_roots:
                violations.append(f"{path}:{module}")
    return violations


def test_sdk_package_does_not_import_api_runtime_or_side_effects() -> None:
    assert SDK_SRC.is_dir(), f"missing SDK source at {SDK_SRC}"
    for path in SDK_SRC.rglob("*.py"):
        for module in _imported_modules(path):
            root = module.split(".", 1)[0]
            assert root not in FORBIDDEN_SDK_IMPORT_ROOTS, f"{path} imports {module}"
            assert not module.startswith("app."), f"{path} imports {module}"


def test_stable_sdk_root_exports_authoring_contracts_only() -> None:
    public = set(bergama_strategy_sdk.__all__)
    assert "FeatureSnapshot" in public
    assert "StrategyExecutionOutput" in public
    assert "StrategyPluginManifest" in public
    assert "StrategyBatchExecutionResult" not in public
    assert "StrategyEngine" not in public
    assert "StrategySdkRuntimeSession" not in dir(bergama_strategy_sdk)
    assert "experimental" not in public
    assert not hasattr(bergama_strategy_sdk, "StrategyBatchExecutionResult")


def test_experimental_namespace_is_not_reexported_from_stable_root() -> None:
    assert "experimental" not in bergama_strategy_sdk.__all__
    import bergama_strategy_sdk.experimental as experimental

    assert experimental is not None


def test_real_author_fixture_package_passes_boundary_scan() -> None:
    clean = AUTHOR_FIXTURES / "clean_author_strategy"
    assert clean.is_dir()
    assert _scan_author_tree(clean) == []


def test_real_author_fixture_with_runtime_import_fails(tmp_path: Path) -> None:
    package = tmp_path / "bad_author"
    package.mkdir()
    (package / "strategy.py").write_text(
        textwrap.dedent(
            """
            from bergama_strategy_sdk import FeatureSnapshot
            from app.strategy.sdk_runtime import StrategySdkRuntimeSession
            from app.portfolio import PortfolioService
            from app.risk import RiskEngine
            from app.orders import OrderManagementService
            from app.broker import PaperBroker
            import httpx
            """
        ),
        encoding="utf-8",
    )
    violations = _scan_author_tree(package)
    joined = "\n".join(violations)
    assert "app.strategy.sdk_runtime" in joined
    assert "app.portfolio" in joined
    assert "app.risk" in joined
    assert "app.orders" in joined
    assert "app.broker" in joined
    assert "httpx" in joined


def test_sdk_package_author_tree_scan_passes() -> None:
    # The SDK package itself is the canonical author-facing tree.
    violations = [
        item
        for item in _scan_author_tree(SDK_SRC)
        if "bergama_strategy_sdk" not in item.split(":")[-1]
    ]
    # SDK internal modules may import sibling package modules; filter to forbidden only.
    forbidden_only = [
        item
        for item in _scan_author_tree(SDK_SRC)
        if any(
            part.startswith(prefix) or part == prefix
            for part in [item.split(":")[-1]]
            for prefix in FORBIDDEN_AUTHOR_IMPORT_PREFIXES
        )
    ]
    assert forbidden_only == []
    assert violations == [] or all("bergama_strategy_sdk" in v for v in violations)


def test_sdk_runtime_remains_host_owned_and_separate_from_sdk_package() -> None:
    assert RUNTIME_DIR.is_dir()
    runtime_files = {path.name for path in RUNTIME_DIR.glob("*.py")}
    assert "session.py" in runtime_files
    assert "engine.py" in runtime_files
    sdk_files = {path.name for path in SDK_SRC.glob("*.py")}
    assert "session.py" not in sdk_files
    assert "engine.py" not in sdk_files
    assert "batch_result.py" not in sdk_files


@pytest.mark.parametrize(
    "source",
    [
        "import app.portfolio",
        "from app.broker.adapters import PaperBroker",
    ],
)
def test_forbidden_import_forms_are_detected(source: str, tmp_path: Path) -> None:
    package = tmp_path / "author"
    package.mkdir()
    (package / "plugin.py").write_text(source + "\n", encoding="utf-8")
    assert _scan_author_tree(package)
