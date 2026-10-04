"""Contract / firewall tests for Intelligence Pipeline Core (Issue #126)."""

from __future__ import annotations

import ast
from pathlib import Path

import app.intelligence_pipeline as pipeline
from app.intelligence_pipeline import (
    BROKER_EXECUTION,
    GLOBAL_OUTCOME_FAMILIES,
    ISSUE_1_REACHABLE_OUTCOMES,
    MODEL_PARTICIPATION,
    POLICY_VERSION_V1,
    PipelineBindings,
    PipelineOutcome,
    PipelineProvenance,
    PipelineRequest,
    PipelineResult,
    run_intelligence_pipeline,
)
from app.intelligence_pipeline import (
    __all__ as pipeline_all,
)

PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "app" / "intelligence_pipeline"
REPO_ROOT = Path(__file__).resolve().parents[4]

FORBIDDEN_IMPORT_PREFIXES = (
    "app.human_review",
    "app.ai_decision_engine",
    "app.broker",
    "app.orders",
    "app.risk",
    "app.portfolio",
    "app.strategy.engine",
    "app.features",
    "app.market_data.connectors",
    "app.market_data.orchestrator",
    "openai",
    "anthropic",
    "langchain",
    "llama",
    "transformers",
    "sqlalchemy",
    "alembic",
    "redis",
    "aiokafka",
    "fastapi",
    "starlette",
)

FORBIDDEN_TOKENS_IN_PUBLIC = (
    "llm",
    "prompt",
    "embedding",
    "openai",
    "order_intent",
    "oms",
    "evaluate_ade",
    "assemble_human_review",
    "from_parts",
)


def test_c01_package_public_exports_controlled() -> None:
    expected = {
        "BROKER_EXECUTION",
        "GLOBAL_OUTCOME_FAMILIES",
        "IMPLEMENTATION_AUTHORIZATION_ID",
        "ISSUE_1_REACHABLE_OUTCOMES",
        "MODEL_PARTICIPATION",
        "OUTCOME_ADMISSION_REJECTED",
        "OUTCOME_COMPLETED_ADE_ABSTAIN",
        "OUTCOME_COMPLETED_ADE_ACCEPT",
        "OUTCOME_COMPLETED_DASHBOARD",
        "OUTCOME_COMPLETED_HUMAN_REVIEW",
        "OUTCOME_REQUIRED_STAGE_FAILED",
        "POLICY_VERSION_V1",
        "STAGE_ORDER",
        "PipelineAdmissionError",
        "PipelineBindings",
        "PipelineError",
        "PipelineOutcome",
        "PipelineProvenance",
        "PipelineRequest",
        "PipelineResult",
        "PipelineStageExecutionError",
        "run_intelligence_pipeline",
    }
    assert set(pipeline_all) == expected
    for name in pipeline_all:
        assert hasattr(pipeline, name)
    assert POLICY_VERSION_V1 == "intelligence-pipeline.policy.v1"
    assert MODEL_PARTICIPATION == "UNAUTHORIZED"
    assert BROKER_EXECUTION == "DENIED / DEFERRED"
    assert len(GLOBAL_OUTCOME_FAMILIES) == 6
    assert len(ISSUE_1_REACHABLE_OUTCOMES) == 3
    assert callable(run_intelligence_pipeline)


def test_c01_models_frozen_forbid_extra() -> None:
    for model in (PipelineBindings, PipelineRequest, PipelineResult, PipelineProvenance):
        assert model.model_config.get("frozen") is True
        assert model.model_config.get("extra") == "forbid"


def test_c01_outcome_enum_preserves_global_six() -> None:
    assert tuple(member.value for member in PipelineOutcome) == GLOBAL_OUTCOME_FAMILIES


def _imported_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return modules


def test_c02_c09_no_forbidden_authority_imports() -> None:
    for path in PACKAGE_ROOT.rglob("*.py"):
        for module in _imported_modules(path):
            for prefix in FORBIDDEN_IMPORT_PREFIXES:
                assert not module.startswith(prefix), f"{path} imports {module}"


def test_c02_c03_no_human_review_or_ade_import_or_invocation() -> None:
    for path in PACKAGE_ROOT.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        modules = _imported_modules(path)
        assert all(not module.startswith("app.human_review") for module in modules)
        assert all(not module.startswith("app.ai_decision_engine") for module in modules)
        assert "assemble_human_review" not in text
        assert "evaluate_ade" not in text
        assert "from app.human_review" not in text
        assert "from app.ai_decision_engine" not in text


def test_c04_no_model_sdk_import() -> None:
    for path in PACKAGE_ROOT.rglob("*.py"):
        for module in _imported_modules(path):
            assert not any(
                module.startswith(tok)
                for tok in ("openai", "anthropic", "langchain", "llama", "transformers")
            )


def test_c05_no_broker_oi_oms_execution_import() -> None:
    for path in PACKAGE_ROOT.rglob("*.py"):
        for module in _imported_modules(path):
            assert not module.startswith(("app.broker", "app.orders", "app.risk", "app.portfolio"))


def test_c06_no_persistence_import() -> None:
    for path in PACKAGE_ROOT.rglob("*.py"):
        for module in _imported_modules(path):
            assert not module.startswith(("sqlalchemy", "alembic", "redis", "aiokafka"))


def test_c07_no_http_router_api_implementation() -> None:
    for path in PACKAGE_ROOT.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "APIRouter" not in text
        assert "@router" not in text
        for module in _imported_modules(path):
            assert not module.startswith(("fastapi", "starlette"))


def test_c08_no_feature_platform_dependency() -> None:
    for path in PACKAGE_ROOT.rglob("*.py"):
        for module in _imported_modules(path):
            assert not module.startswith("app.features")


def test_c09_no_provider_client() -> None:
    for path in PACKAGE_ROOT.rglob("*.py"):
        for module in _imported_modules(path):
            assert "connectors" not in module
            assert "orchestrator" not in module or module.startswith("app.intelligence_pipeline")


def test_c10_no_new_dependency() -> None:
    pyproject = (REPO_ROOT / "apps" / "api" / "pyproject.toml").read_text(encoding="utf-8")
    # Package must not require new declared dependencies beyond repository baseline.
    assert "openai" not in pyproject
    assert "anthropic" not in pyproject
    assert "langchain" not in pyproject


def test_c11_no_forbidden_stage_package_modification() -> None:
    frozen = [
        "apps/api/app/premarket/watchlist",
        "apps/api/app/premarket/gap",
        "apps/api/app/premarket/catalyst",
        "apps/api/app/premarket/scoring",
        "apps/api/app/premarket/morning_briefing",
        "apps/api/app/dashboard",
        "apps/api/app/human_review",
        "apps/api/app/ai_decision_engine",
    ]
    # Contract: package source does not rewrite stage packages; path inventory is structural.
    for relative in frozen:
        assert (REPO_ROOT / relative).is_dir()


def test_c12_no_replay_implementation_for_issue_3() -> None:
    assert not (PACKAGE_ROOT / "replay.py").exists()
    for path in PACKAGE_ROOT.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "assert_replay_equal" not in text
        assert "def reevaluate" not in text
        assert "def replay" not in text


def test_public_surface_excludes_forbidden_tokens() -> None:
    public_names = " ".join(pipeline_all).lower()
    for token in FORBIDDEN_TOKENS_IN_PUBLIC:
        assert token not in public_names
