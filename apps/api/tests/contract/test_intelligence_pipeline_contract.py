"""Contract / firewall tests for Intelligence Pipeline Core (Issue #126/#128/#130)."""

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
    PipelineReplayInequalityError,
    PipelineRequest,
    PipelineResult,
    assert_replay_equal,
    replay_intelligence_pipeline,
    run_intelligence_pipeline,
)
from app.intelligence_pipeline import (
    __all__ as pipeline_all,
)
from app.intelligence_pipeline.policy import FINGERPRINT_SCHEMA_ID

PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "app" / "intelligence_pipeline"
REPO_ROOT = Path(__file__).resolve().parents[4]

FORBIDDEN_IMPORT_PREFIXES = (
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

# Deterministic hashing utility only — not Strategy authority.
ALLOWED_STRATEGY_MODULES = frozenset({"app.strategy.keys"})

# Public Pipeline package surface must not re-export HR/ADE entrypoints.
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
    "strategy_sha256",
    "canonical_strategy_json",
)

ALLOWED_HR_MODULES = frozenset(
    {
        "app.human_review.engine",
        "app.human_review.models",
    }
)
ALLOWED_ADE_MODULES = frozenset(
    {
        "app.ai_decision_engine.engine",
        "app.ai_decision_engine.models",
    }
)

ALLOWED_THIRD_PARTY_MODULES = frozenset(
    {
        "pydantic",
    }
)

ALLOWED_STDLIB_MODULES = frozenset(
    {
        "__future__",
        "typing",
        "datetime",
        "enum",
        "ast",
        "pathlib",
    }
)

ALLOWED_APP_PREFIXES = (
    "app.intelligence_pipeline",
    "app.ai_decision_engine",
    "app.human_review",
    "app.dashboard",
    "app.premarket",
    "app.market_data",
    "app.core",
    "app.strategy.keys",
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
        "PipelineReplayInequalityError",
        "PipelineRequest",
        "PipelineResult",
        "PipelineStageExecutionError",
        "assert_replay_equal",
        "replay_intelligence_pipeline",
        "run_intelligence_pipeline",
    }
    assert set(pipeline_all) == expected
    for name in pipeline_all:
        assert hasattr(pipeline, name)
    assert POLICY_VERSION_V1 == "intelligence-pipeline.policy.v1"
    assert FINGERPRINT_SCHEMA_ID == "intelligence-pipeline.fingerprint.v1"
    assert MODEL_PARTICIPATION == "UNAUTHORIZED"
    assert BROKER_EXECUTION == "DENIED / DEFERRED"
    assert len(GLOBAL_OUTCOME_FAMILIES) == 6
    assert len(ISSUE_1_REACHABLE_OUTCOMES) == 3
    assert callable(run_intelligence_pipeline)
    assert callable(replay_intelligence_pipeline)
    assert callable(assert_replay_equal)
    assert issubclass(PipelineReplayInequalityError, Exception)


def test_c01_models_frozen_forbid_extra() -> None:
    for model in (PipelineBindings, PipelineRequest, PipelineResult, PipelineProvenance):
        assert model.model_config.get("frozen") is True
        assert model.model_config.get("extra") == "forbid"


def test_c01_outcome_enum_preserves_global_six() -> None:
    assert tuple(member.value for member in PipelineOutcome) == GLOBAL_OUTCOME_FAMILIES
    assert len(tuple(member.value for member in PipelineOutcome)) == 6


def _imported_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return modules


def _imported_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.name)
    return names


def test_c02_c09_no_forbidden_authority_imports() -> None:
    for path in PACKAGE_ROOT.rglob("*.py"):
        for module in _imported_modules(path):
            for prefix in FORBIDDEN_IMPORT_PREFIXES:
                assert not module.startswith(prefix), f"{path} imports {module}"
            if module.startswith("app.strategy"):
                assert module in ALLOWED_STRATEGY_MODULES, f"{path} imports {module}"


def test_c01_human_review_public_api_only() -> None:
    hr_modules: set[str] = set()
    for path in PACKAGE_ROOT.rglob("*.py"):
        for module in _imported_modules(path):
            if module.startswith("app.human_review"):
                hr_modules.add(module)
    assert hr_modules
    assert hr_modules <= ALLOWED_HR_MODULES
    for path in PACKAGE_ROOT.rglob("*.py"):
        names = _imported_names(path)
        text = path.read_text(encoding="utf-8")
        assert "assemble_human_review_from_parts" not in names
        assert "assemble_human_review_from_parts" not in text


def test_c02_ade_public_api_only() -> None:
    ade_modules: set[str] = set()
    for path in PACKAGE_ROOT.rglob("*.py"):
        for module in _imported_modules(path):
            if module.startswith("app.ai_decision_engine"):
                ade_modules.add(module)
    assert ade_modules
    assert ade_modules <= ALLOWED_ADE_MODULES
    for path in PACKAGE_ROOT.rglob("*.py"):
        names = _imported_names(path)
        text = path.read_text(encoding="utf-8")
        assert "evaluate_ade_from_parts" not in names
        assert "evaluate_ade_from_parts" not in text
        assert "classify_admission" not in names
        assert "from_parts" not in text


def test_c03_public_entrypoints_used() -> None:
    orch = (PACKAGE_ROOT / "orchestrator.py").read_text(encoding="utf-8")
    assert "assemble_human_review(" in orch
    assert "evaluate_ade(" in orch
    assert "HumanReviewRequest(" in orch
    assert "AdeEvaluationRequest(" in orch


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
    assert "openai" not in pyproject
    assert "anthropic" not in pyproject
    assert "langchain" not in pyproject
    # AST: package imports stay within stdlib / pydantic / authorized app modules.
    for path in PACKAGE_ROOT.rglob("*.py"):
        for module in _imported_modules(path):
            root = module.split(".", 1)[0]
            if root in ALLOWED_STDLIB_MODULES or module in ALLOWED_STDLIB_MODULES:
                continue
            if module in ALLOWED_THIRD_PARTY_MODULES or root in ALLOWED_THIRD_PARTY_MODULES:
                continue
            if module.startswith("app."):
                assert any(
                    module == prefix or module.startswith(prefix + ".")
                    for prefix in ALLOWED_APP_PREFIXES
                ), f"{path} imports unauthorized app module {module}"
                continue
            raise AssertionError(f"{path} imports unauthorized module {module}")


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
    for relative in frozen:
        assert (REPO_ROOT / relative).is_dir()


def test_c12_replay_present_in_process_only() -> None:
    """Issue #130: replay authorized; remain thin/in-process (replaces pre-#130 C-12)."""
    assert (PACKAGE_ROOT / "replay.py").exists()
    replay_text = (PACKAGE_ROOT / "replay.py").read_text(encoding="utf-8")
    assert "def replay_intelligence_pipeline" in replay_text
    assert "def assert_replay_equal" in replay_text
    assert "run_intelligence_pipeline" in replay_text
    assert "pipeline_fingerprint" in (PACKAGE_ROOT / "models.py").read_text(encoding="utf-8")
    for path in PACKAGE_ROOT.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "uuid4" not in text
        assert "durable_replay" not in text
        assert "redis" not in text.lower() or path.name.endswith(".pyc")
        assert "APIRouter" not in text
        assert "sqlalchemy" not in text
        assert "aiokafka" not in text
    assert "replay_intelligence_pipeline" in pipeline_all
    assert "assert_replay_equal" in pipeline_all
    assert "PipelineReplayInequalityError" in pipeline_all
    assert "run_id" not in replay_text


def test_c13_c14_bag_denylist_preserves_human_review_and_ade() -> None:
    admit = (PACKAGE_ROOT / "admit.py").read_text(encoding="utf-8")
    assert '"human_review"' in admit
    assert '"ade"' in admit


def test_c15_c16_frozen_six_outcome_taxonomy_unchanged() -> None:
    assert GLOBAL_OUTCOME_FAMILIES == (
        "admission_rejected",
        "required_stage_failed",
        "completed_dashboard",
        "completed_human_review",
        "completed_ade_accept",
        "completed_ade_abstain",
    )
    assert len(GLOBAL_OUTCOME_FAMILIES) == 6


def test_c17_same_public_pipeline_entrypoint_retained() -> None:
    assert callable(run_intelligence_pipeline)
    assert "run_intelligence_pipeline" in pipeline_all


def test_public_surface_excludes_forbidden_tokens() -> None:
    public_names = " ".join(pipeline_all).lower()
    for token in FORBIDDEN_TOKENS_IN_PUBLIC:
        assert token not in public_names
