"""Prohibition / firewall tests for Premarket Analyst WS1 package."""

from __future__ import annotations

from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[2] / "app" / "premarket_analyst"


def _package_source() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in sorted(PACKAGE.glob("*.py")))


def test_no_fastapi_sqlalchemy_broker_router_imports() -> None:
    text = _package_source()
    assert "from fastapi" not in text
    assert "import fastapi" not in text
    assert "from sqlalchemy" not in text
    assert "import sqlalchemy" not in text
    assert "from app.broker" not in text
    assert "from app.routers" not in text
    assert "from app.ai_decision_engine" not in text
    assert "from app.human_review" not in text


def test_no_model_llm_clients() -> None:
    text = _package_source().lower()
    for banned in ("openai", "anthropic", "langchain", "llm_client", "chatcompletion"):
        assert banned not in text


def test_no_persistence_or_alembic() -> None:
    text = _package_source()
    assert "alembic" not in text.lower()
    assert "create_engine" not in text
    assert "sessionmaker" not in text
    assert "from app.intelligence_runs" not in text


def test_no_ui_platform_console() -> None:
    text = _package_source()
    assert "platform-console" not in text
    assert "platform_console" not in text
    assert "from apps." not in text


def test_ws1_path_boundary_files_only() -> None:
    allowed = {
        "__init__.py",
        "models.py",
        "policy.py",
        "errors.py",
        "identity.py",
        "provenance.py",
        "ordering.py",
        "validate_input.py",
        "validate_output.py",
        "engine.py",
        "pipeline.py",
        "output.py",
        "replay.py",
    }
    present = {path.name for path in PACKAGE.glob("*.py")}
    assert present == allowed
