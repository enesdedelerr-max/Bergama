"""Shared constants and helpers for Sprint 2 gate / smoke tooling."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import time
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

Status = Literal["PASS", "FAIL", "SKIPPED"]

GATE_ID = "sprint2-runtime-gate"
SPRINT = "2"
RELEASE_VERSION = "v0.2.0-sprint2"

SECRET_PATTERNS = (
    re.compile(r"(?i)authorization\s*[:=]\s*bearer\s+[A-Za-z0-9\-._~+/]+=*"),
    re.compile(r"(?i)bootstrap[_-]?jwt[_-]?signing[_-]?key\s*[:=]\s*\S+"),
    re.compile(r"(?i)\"access_token\"\s*:\s*\"[^\"]+\""),
    re.compile(r"(?i)BERGAMA_SECRETS__BOOTSTRAP_JWT_SIGNING_KEY=\S+"),
)

# Exact required order for make gate-sprint2 orchestration.
REQUIRED_STEP_SPECS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("lint", ("make", "lint")),
    ("typecheck", ("make", "typecheck")),
    ("validate-secrets", ("make", "validate-secrets")),
    ("test-api", ("make", "test-api")),
    ("test-api-auth", ("make", "test-api-auth")),
    ("test-api-container", ("make", "test-api-container")),
    ("test-api-health", ("make", "test-api-health")),
    ("test-api-kafka-core", ("make", "test-api-kafka-core")),
    ("test-api-kafka-test-runtime", ("make", "test-api-kafka-test-runtime")),
    ("test-api-registry", ("make", "test-api-registry")),
    ("validate-api-openapi", ("make", "validate-api-openapi")),
    ("smoke-api-runtime", ("make", "smoke-api-runtime")),
)

OPTIONAL_STEP_SPECS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("smoke-api-kafka", ("make", "smoke-api-kafka")),
)

POST_STEP_SPECS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("build-sprint2-release", ("make", "build-sprint2-release")),
)


@dataclass(slots=True)
class CheckResult:
    name: str
    status: Status
    command: str
    duration_seconds: float
    log_path: str | None
    message: str
    corrective_action: str | None = None


@dataclass
class GateState:
    root: Path
    checks: list[CheckResult] = field(default_factory=list)
    optional_checks: list[CheckResult] = field(default_factory=list)
    started_at: str = ""
    completed_at: str = ""
    first_failed_stage: str | None = None
    overall_status: Literal["PASS", "FAIL"] = "PASS"

    @property
    def art(self) -> Path:
        return self.root / "artifacts" / "sprint2"

    @property
    def logs(self) -> Path:
        return self.art / "logs"

    @property
    def evidence(self) -> Path:
        return self.art / "evidence"


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git_meta(root: Path) -> tuple[str, str]:
    branch = subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=root, text=True
    ).strip()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    return branch, commit


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clear_directory(path: Path) -> None:
    if path.exists():
        for child in sorted(path.rglob("*"), reverse=True):
            if child.is_file() or child.is_symlink():
                child.unlink(missing_ok=True)
            elif child.is_dir():
                child.rmdir()
    path.mkdir(parents=True, exist_ok=True)


def ensure_no_secrets(text: str, *, context: str) -> None:
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            msg = f"secret-like material detected in {context}"
            raise RuntimeError(msg)


def command_string(cmd: Sequence[str]) -> str:
    return " ".join(cmd)


Runner = Callable[[Sequence[str], Path, Path], tuple[int, str]]


def default_runner(cmd: Sequence[str], cwd: Path, log_path: Path) -> tuple[int, str]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    proc = subprocess.run(
        list(cmd),
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    duration = round(time.perf_counter() - started, 3)
    body = (
        f"$ {command_string(cmd)}\n"
        f"exit_code={proc.returncode}\n"
        f"duration_seconds={duration}\n"
        f"----- stdout -----\n{proc.stdout}"
        f"----- stderr -----\n{proc.stderr}"
    )
    log_path.write_text(body, encoding="utf-8")
    ensure_no_secrets(body, context=str(log_path))
    return proc.returncode, body


def interpret_optional_kafka(body: str, exit_code: int) -> Status:
    upper = body.upper()
    if exit_code == 0 and ("SKIPPED" in upper or "BERGAMA_KAFKA_SMOKE" in body):
        if "SKIPPED" in upper:
            return "SKIPPED"
        return "PASS"
    if exit_code == 0:
        return "PASS"
    return "FAIL"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def decision_for(overall: Literal["PASS", "FAIL"]) -> str:
    if overall == "PASS":
        return "GO FOR SPRINT 3"
    return "NO-GO FOR SPRINT 3"


def summary_payload(
    state: GateState,
    *,
    branch: str,
    commit: str,
    live_kafka_status: Status,
) -> dict[str, Any]:
    required = state.checks
    optional = state.optional_checks
    passed = sum(1 for c in required if c.status == "PASS")
    failed = sum(1 for c in required if c.status == "FAIL")
    skipped_optional = sum(1 for c in optional if c.status == "SKIPPED")
    return {
        "gate_id": GATE_ID,
        "sprint": SPRINT,
        "release_version": RELEASE_VERSION,
        "branch": branch,
        "commit": commit,
        "started_at": state.started_at,
        "completed_at": state.completed_at or utc_now(),
        "overall_status": state.overall_status,
        "required_checks_count": len(required),
        "passed_count": passed,
        "failed_count": failed,
        "skipped_optional_count": skipped_optional,
        "first_failed_stage": state.first_failed_stage,
        "live_kafka_status": live_kafka_status,
        "release_path": "releases/sprint-2",
        "report_path": "reports/sprint2-runtime-validation.json",
        "final_decision": decision_for(state.overall_status),
        "checks": [asdict(c) for c in required],
        "optional_checks": [asdict(c) for c in optional],
    }


def validation_report(
    state: GateState,
    *,
    branch: str,
    commit: str,
    evidence_paths: list[str],
    live_kafka_status: Status,
) -> dict[str, Any]:
    return {
        "gate_id": GATE_ID,
        "sprint": SPRINT,
        "commit": commit,
        "branch": branch,
        "started_at": state.started_at,
        "completed_at": state.completed_at or utc_now(),
        "overall_status": state.overall_status,
        "checks": [asdict(c) for c in state.checks],
        "optional_checks": [asdict(c) for c in state.optional_checks],
        "evidence_paths": evidence_paths,
        "known_limitations": [
            "production OIDC not implemented",
            "live Kafka broker smoke may be unverified",
            "no persistent retry/DLQ",
            "no application PostgreSQL/Redis client runtime",
            "Registry Loader is local-file/read-only",
            "Kafka test runtime does not emulate full consumer-group rebalance",
            "Trading Engine Foundation (#211) excluded from this gate",
        ],
        "live_kafka_status": live_kafka_status,
        "final_decision": decision_for(state.overall_status),
    }


def write_text_summary(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        f"gate_id={summary['gate_id']}",
        f"sprint={summary['sprint']}",
        f"branch={summary['branch']}",
        f"commit={summary['commit']}",
        f"overall_status={summary['overall_status']}",
        f"required_checks_count={summary['required_checks_count']}",
        f"passed_count={summary['passed_count']}",
        f"failed_count={summary['failed_count']}",
        f"skipped_optional_count={summary['skipped_optional_count']}",
        f"first_failed_stage={summary['first_failed_stage']}",
        f"live_kafka_status={summary['live_kafka_status']}",
        f"release_path={summary['release_path']}",
        f"report_path={summary['report_path']}",
        f"final_decision={summary['final_decision']}",
        "",
    ]
    for check in summary["checks"]:
        lines.append(f"REQUIRED {check['name']}={check['status']}")
    for check in summary["optional_checks"]:
        lines.append(f"OPTIONAL {check['name']}={check['status']}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def env_bool(name: str) -> bool:
    return os.environ.get(name, "").strip() in {"1", "true", "TRUE", "yes", "YES"}
