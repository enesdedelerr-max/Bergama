"""Shared helpers for Sprint 3 fail-closed gate and release tooling."""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import re
import shutil
import subprocess
import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

Status = Literal["PASS", "FAIL", "SKIPPED"]

EVIDENCE_VERSION = "sprint3.gate.v1"
GATE_ID = "sprint3-runtime-gate"
SPRINT = "3"
RELEASE_VERSION = "v0.3.0-sprint3"
GO_DECISION = "GO FOR SPRINT 4"
NO_GO_DECISION = "NO-GO FOR SPRINT 4"

SECRET_PATTERNS = (
    re.compile(r"(?i)authorization\s*[:=]\s*bearer\s+[A-Za-z0-9\-._~+/]+=*"),
    re.compile(r"(?i)\"access_token\"\s*:\s*\"[^\"]+\""),
    re.compile(r"(?i)\b(api[_-]?key|secret|token|password)\b\s*[:=]\s*[^\s,;]+"),
    re.compile(r"(?i)AWS_SECRET_ACCESS_KEY\s*[:=]\s*\S+"),
    re.compile(r"(?i)BERGAMA_[A-Z0-9_]*(SECRET|TOKEN|API_KEY|PASSWORD)[A-Z0-9_]*=\S+"),
)

SAFE_ENV_KEYS = (
    "BERGAMA_ENVIRONMENT",
    "BERGAMA_KAFKA__ENABLED",
    "BERGAMA_KAFKA__BOOTSTRAP_SERVERS",
    "BERGAMA_KAFKA__TOPIC_PREFIX",
    "BERGAMA_ICEBERG_WRITER__ENABLED",
    "BERGAMA_ICEBERG_WRITER__CATALOG_TYPE",
    "BERGAMA_ICEBERG_WRITER__CATALOG_URI",
    "BERGAMA_ICEBERG_WRITER__WAREHOUSE",
    "BERGAMA_ICEBERG_WRITER__NAMESPACE",
    "BERGAMA_ICEBERG_WRITER__TABLE_PREFIX",
    "BERGAMA_ICEBERG_WRITER__S3_ENDPOINT",
    "BERGAMA_ICEBERG_WRITER__AUTO_CREATE_TABLES",
    "BERGAMA_SPRINT3_RUNTIME_BOOTSTRAP",
)

RUNTIME_ENV_PREFIXES = (
    "BERGAMA_KAFKA__",
    "BERGAMA_ICEBERG_WRITER__",
)

RUNTIME_ENV_EXACT_KEYS = frozenset(
    {
        "BERGAMA_ENVIRONMENT",
        "BERGAMA_SPRINT3_RUNTIME_SMOKE",
        "BERGAMA_SPRINT3_GATE_BOOTSTRAP_LOCAL_RUNTIME",
        "BERGAMA_SPRINT3_RUNTIME_BOOTSTRAP",
    }
)

GATE_SECRET_ENV_EXACT_KEYS = frozenset(
    {
        "BERGAMA_SECRETS__BOOTSTRAP_JWT_SIGNING_KEY",
    }
)

REQUIRED_SOURCE_PATHS = (
    "apps/api/app/market_data/envelope.py",
    "apps/api/app/market_data/events/base.py",
    "apps/api/app/market_data/quality.py",
    "apps/api/app/infrastructure/polygon/historical.py",
    "apps/api/app/infrastructure/polygon/realtime.py",
    "apps/api/app/infrastructure/finnhub/fundamentals.py",
    "apps/api/app/infrastructure/fred/observations.py",
    "apps/api/app/infrastructure/sec/submissions.py",
    "apps/api/app/infrastructure/benzinga/news.py",
    "apps/api/app/market_data/orchestrator/pipeline.py",
    "apps/api/app/infrastructure/kafka/market_data_publish.py",
    "apps/api/app/infrastructure/iceberg/consumer.py",
    "apps/api/app/market_data/replay/__init__.py",
    "apps/api/app/market_data/backfill/__init__.py",
    "apps/api/app/market_data/data_quality/__init__.py",
)

REQUIRED_IMPORTS = (
    "app.market_data.envelope",
    "app.market_data.events.base",
    "app.market_data.quality",
    "app.infrastructure.polygon.historical",
    "app.infrastructure.polygon.realtime",
    "app.infrastructure.finnhub.fundamentals",
    "app.infrastructure.fred.observations",
    "app.infrastructure.sec.submissions",
    "app.infrastructure.benzinga.news",
    "app.market_data.orchestrator.pipeline",
    "app.infrastructure.kafka.market_data_publish",
    "app.infrastructure.iceberg.consumer",
    "app.market_data.replay",
    "app.market_data.backfill",
    "app.market_data.data_quality",
)

REQUIRED_MAKE_TARGETS = (
    "lint",
    "typecheck",
    "validate-secrets",
    "test-api-market-contracts",
    "test-api-provider-contracts",
    "test-api-market-orchestrator",
    "test-api-kafka-publish-adapter",
    "test-api-iceberg-writer",
    "test-api-replay-engine",
    "test-api-backfill",
    "test-api-data-quality",
    "test-api",
    "smoke-api-data-quality",
    "smoke-api-replay-engine",
    "smoke-sprint3-runtime",
    "prepare-sprint3-release",
    "build-sprint3-release",
    "validate-sprint3-evidence",
    "validate-sprint3-release",
    "test-sprint3-gate",
    "gate-sprint3",
)

APPROVED_SPRINT3_RELEASE_PATHS = frozenset(
    {
        "releases/sprint-3/README.md",
        "releases/sprint-3/RELEASE_NOTES.md",
        "releases/sprint-3/MANIFEST.json",
        "releases/sprint-3/checksums.txt",
        "releases/sprint-3/sbom.spdx.json",
        "releases/sprint-3/sprint3-openapi.json",
        "releases/sprint-3/sprint3-quality-gate.json",
        "releases/sprint-3/sprint3-runtime-validation.json",
        "releases/sprint-3/sprint3-known-limitations.md",
    }
)

APPROVED_SPRINT3_FINALIZATION_PATHS = frozenset(
    {
        *APPROVED_SPRINT3_RELEASE_PATHS,
        "scripts/gates/build_sprint3_release.py",
        "scripts/gates/gate_sprint3.py",
        "scripts/gates/sprint3_common.py",
        "scripts/gates/validate_sprint3_evidence.py",
        "tests/gates/test_sprint3_gate.py",
    }
)

STATIC_STEP_SPECS = (
    ("lint", ("make", "lint")),
    ("typecheck", ("make", "typecheck")),
    ("validate-secrets", ("make", "validate-secrets")),
)

FOCUSED_STEP_SPECS = (
    ("test-api-market-contracts", ("make", "test-api-market-contracts")),
    ("test-api-provider-contracts", ("make", "test-api-provider-contracts")),
    ("test-api-market-orchestrator", ("make", "test-api-market-orchestrator")),
    ("test-api-kafka-publish-adapter", ("make", "test-api-kafka-publish-adapter")),
    ("test-api-iceberg-writer", ("make", "test-api-iceberg-writer")),
    ("test-api-replay-engine", ("make", "test-api-replay-engine")),
    ("test-api-backfill", ("make", "test-api-backfill")),
    ("test-api-data-quality", ("make", "test-api-data-quality")),
)

REGRESSION_STEP_SPECS = (("test-api", ("make", "test-api")),)

OFFLINE_SMOKE_STEP_SPECS = (
    ("smoke-api-data-quality", ("make", "smoke-api-data-quality"), {}),
    (
        "smoke-api-replay-engine",
        ("make", "smoke-api-replay-engine"),
        {"BERGAMA_REPLAY_ENGINE_SMOKE": "1"},
    ),
)

RUNTIME_SMOKE_STEP_SPECS = (("smoke-sprint3-runtime", ("make", "smoke-sprint3-runtime")),)

OPTIONAL_PROVIDER_STEP_SPECS = (
    ("smoke-api-polygon", ("make", "smoke-api-polygon")),
    ("smoke-api-polygon-realtime", ("make", "smoke-api-polygon-realtime")),
    ("smoke-api-finnhub", ("make", "smoke-api-finnhub")),
    ("smoke-api-fred", ("make", "smoke-api-fred")),
    ("smoke-api-sec", ("make", "smoke-api-sec")),
    ("smoke-api-benzinga", ("make", "smoke-api-benzinga")),
    ("smoke-api-backfill", ("make", "smoke-api-backfill")),
)

POST_STEP_SPECS = (
    ("build-sprint3-release", ("make", "build-sprint3-release")),
    ("validate-sprint3-evidence", ("make", "validate-sprint3-evidence")),
    ("validate-sprint3-release", ("make", "validate-sprint3-release")),
)

DEFAULT_TIMEOUT_SECONDS = 900


@dataclass(frozen=True, slots=True)
class CommandSpec:
    id: str
    command: tuple[str, ...]
    group: str
    required: bool = True
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    env: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CommandResult:
    id: str
    command: str
    started_at: str
    completed_at: str
    duration_seconds: float
    exit_code: int
    status: Status
    required: bool
    log_path: str
    skip_reason: str | None
    timeout_seconds: int
    evidence_version: str
    git_commit: str
    sanitized_environment_summary: dict[str, object]


@dataclass
class GateState:
    root: Path
    started_at: str
    git_branch: str
    git_commit: str
    results: list[CommandResult] = field(default_factory=list)
    preflight_errors: list[str] = field(default_factory=list)
    optional_failures: list[str] = field(default_factory=list)
    first_failed_stage: str | None = None
    overall_status: Literal["PASS", "FAIL"] = "PASS"

    @property
    def art(self) -> Path:
        return self.root / "artifacts" / "sprint3"

    @property
    def logs(self) -> Path:
        return self.art / "logs"

    @property
    def evidence(self) -> Path:
        return self.art / "evidence"


Runner = Callable[[CommandSpec, Path, Path, str], CommandResult]


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def command_string(cmd: Sequence[str]) -> str:
    return " ".join(cmd)


def git_meta(root: Path) -> tuple[str, str]:
    branch = subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=root, text=True
    ).strip()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    return branch, commit


def git_is_dirty(root: Path) -> bool:
    status = subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True)
    return bool(status.strip())


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


def is_runtime_env_key(key: str) -> bool:
    return key in RUNTIME_ENV_EXACT_KEYS or any(
        key.startswith(prefix) for prefix in RUNTIME_ENV_PREFIXES
    )


def sanitized_gate_environment(env: Mapping[str, str] | None = None) -> dict[str, str]:
    """Return a child-process environment with local runtime overrides removed."""
    source = env or os.environ
    return {
        key: value
        for key, value in source.items()
        if not is_runtime_env_key(key) and key not in GATE_SECRET_ENV_EXACT_KEYS
    }


def runtime_smoke_environment(env: Mapping[str, str] | None = None) -> dict[str, str]:
    """Return the isolated runtime smoke environment.

    Runtime variables are copied from the parent process only for the required
    smoke command; all other gate commands use sanitized_gate_environment().
    """
    source = env or os.environ
    child = sanitized_gate_environment(source)
    child.update({key: value for key, value in source.items() if is_runtime_env_key(key)})
    return child


def environment_for_spec(spec: CommandSpec, env: Mapping[str, str] | None = None) -> dict[str, str]:
    child = (
        runtime_smoke_environment(env)
        if spec.group == "runtime-smoke"
        else sanitized_gate_environment(env)
    )
    child.update(spec.env)
    return child


def sanitized_environment_summary(env: Mapping[str, str] | None = None) -> dict[str, object]:
    source = env or os.environ
    summary: dict[str, object] = {}
    for key in SAFE_ENV_KEYS:
        if key not in source:
            continue
        value = source[key]
        lowered = key.lower()
        if any(token in lowered for token in ("secret", "token", "api_key", "password")):
            summary[key] = "<redacted>"
        elif "bootstrap_servers" in lowered:
            summary[key] = bool(value.strip())
        else:
            summary[key] = value
    return dict(sorted(summary.items()))


def normalize_status(*, exit_code: int, body: str) -> tuple[Status, str | None]:
    if exit_code == 0 and (reason := _explicit_skip_reason(body)) is not None:
        return "SKIPPED", reason
    if exit_code == 0:
        return "PASS", None
    return "FAIL", None


def _explicit_skip_reason(body: str) -> str | None:
    for line in body.splitlines():
        if line.strip() == "BERGAMA_SMOKE_STATUS=SKIPPED":
            return line.strip()[:500]
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and payload.get("status") == "SKIPPED":
            reason = payload.get("reason")
            return str(reason or "machine-readable smoke skip")[:500]
    return None


def default_runner(spec: CommandSpec, cwd: Path, log_path: Path, git_commit: str) -> CommandResult:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    env = environment_for_spec(spec)
    started_wall = utc_now()
    started = time.perf_counter()
    timed_out = False
    try:
        proc = subprocess.run(
            list(spec.command),
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=spec.timeout_seconds,
            check=False,
        )
        exit_code = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        exit_code = 124
        stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
        stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
        stderr += f"\nTIMEOUT after {spec.timeout_seconds}s\n"
    duration = round(time.perf_counter() - started, 3)
    completed_wall = utc_now()
    body = (
        f"$ {command_string(spec.command)}\n"
        f"started_at={started_wall}\n"
        f"completed_at={completed_wall}\n"
        f"exit_code={exit_code}\n"
        f"timeout_seconds={spec.timeout_seconds}\n"
        f"duration_seconds={duration}\n"
        f"timed_out={str(timed_out).lower()}\n"
        f"----- stdout -----\n{stdout}"
        f"----- stderr -----\n{stderr}"
    )
    ensure_no_secrets(body, context=str(log_path))
    log_path.write_text(body, encoding="utf-8")
    status, skip_reason = normalize_status(exit_code=exit_code, body=body)
    return CommandResult(
        id=spec.id,
        command=command_string(spec.command),
        started_at=started_wall,
        completed_at=completed_wall,
        duration_seconds=duration,
        exit_code=exit_code,
        status=status,
        required=spec.required,
        log_path=str(log_path.relative_to(cwd)),
        skip_reason=skip_reason,
        timeout_seconds=spec.timeout_seconds,
        evidence_version=EVIDENCE_VERSION,
        git_commit=git_commit,
        sanitized_environment_summary=sanitized_environment_summary(env),
    )


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    ensure_no_secrets(text, context=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    ensure_no_secrets(text, context=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def result_payload(results: Iterable[CommandResult]) -> dict[str, Any]:
    return {
        "evidence_version": EVIDENCE_VERSION,
        "generated_at": utc_now(),
        "results": [asdict(result) for result in results],
    }


def decision_for(overall: Literal["PASS", "FAIL"]) -> str:
    return GO_DECISION if overall == "PASS" else NO_GO_DECISION


def command_specs() -> list[CommandSpec]:
    specs: list[CommandSpec] = []
    for name, cmd in STATIC_STEP_SPECS:
        specs.append(CommandSpec(id=name, command=cmd, group="static-checks"))
    for name, cmd in FOCUSED_STEP_SPECS:
        specs.append(CommandSpec(id=name, command=cmd, group="focused-tests"))
    for name, cmd in REGRESSION_STEP_SPECS:
        specs.append(CommandSpec(id=name, command=cmd, group="regression"))
    for name, cmd, env in OFFLINE_SMOKE_STEP_SPECS:
        specs.append(CommandSpec(id=name, command=cmd, group="offline-smokes", env=env))
    for name, cmd in RUNTIME_SMOKE_STEP_SPECS:
        specs.append(CommandSpec(id=name, command=cmd, group="runtime-smoke", timeout_seconds=1200))
    for name, cmd in OPTIONAL_PROVIDER_STEP_SPECS:
        specs.append(CommandSpec(id=name, command=cmd, group="provider-smokes", required=False))
    for name, cmd in POST_STEP_SPECS:
        specs.append(CommandSpec(id=name, command=cmd, group="release", timeout_seconds=1200))
    return specs


def preflight_payload(root: Path, *, git_commit: str) -> dict[str, Any]:
    errors: list[str] = []
    checks: dict[str, Any] = {}
    checks["working_tree_clean"] = not git_is_dirty(root)
    if not checks["working_tree_clean"]:
        errors.append("working tree is dirty")

    missing_paths = [path for path in REQUIRED_SOURCE_PATHS if not (root / path).is_file()]
    checks["required_source_files"] = {
        "status": "PASS" if not missing_paths else "FAIL",
        "missing": missing_paths,
    }
    errors.extend(f"missing required source file: {path}" for path in missing_paths)

    makefile = root / "Makefile"
    make_text = makefile.read_text(encoding="utf-8") if makefile.is_file() else ""
    missing_targets = [
        target for target in REQUIRED_MAKE_TARGETS if not re.search(rf"^{target}:", make_text, re.M)
    ]
    checks["make_targets"] = {
        "status": "PASS" if not missing_targets else "FAIL",
        "missing": missing_targets,
    }
    errors.extend(f"missing Make target: {target}" for target in missing_targets)

    import_errors: dict[str, str] = {}
    python_path = str(root / "apps" / "api")
    import sys

    if python_path not in sys.path:
        sys.path.insert(0, python_path)
    for module in REQUIRED_IMPORTS:
        try:
            importlib.import_module(module)
        except Exception as exc:  # noqa: BLE001 - preflight boundary
            import_errors[module] = type(exc).__name__
    checks["required_imports"] = {
        "status": "PASS" if not import_errors else "FAIL",
        "errors": import_errors,
    }
    errors.extend(f"required import failed: {module} ({err})" for module, err in import_errors.items())

    tool_status: dict[str, str | None] = {
        tool: shutil.which(tool) for tool in ("python3", "syft", "docker", "kubectl", "kind")
    }
    missing_tools = [tool for tool, path in tool_status.items() if path is None]
    checks["tools"] = {"status": "PASS" if not missing_tools else "FAIL", "paths": tool_status}
    errors.extend(f"required tool missing: {tool}" for tool in missing_tools)

    checks["git_commit"] = git_commit
    return {
        "evidence_version": EVIDENCE_VERSION,
        "generated_at": utc_now(),
        "git_commit": git_commit,
        "status": "PASS" if not errors else "FAIL",
        "checks": checks,
        "errors": errors,
        "sanitized_environment_summary": sanitized_environment_summary(sanitized_gate_environment()),
    }


def write_git_state(root: Path, evidence: Path, *, branch: str, commit: str) -> None:
    origin_head = _git_output(root, "rev-parse", "--verify", "origin/main", default="")
    payload = {
        "evidence_version": EVIDENCE_VERSION,
        "generated_at": utc_now(),
        "branch": branch,
        "commit": commit,
        "origin_main": origin_head,
        "working_tree_clean": not git_is_dirty(root),
    }
    write_json(evidence / "git-state.json", payload)


def write_environment(root: Path, evidence: Path, *, commit: str) -> None:
    tools: dict[str, str | None] = {
        tool: shutil.which(tool) for tool in ("python3", "syft", "docker", "kubectl", "kind")
    }
    versions: dict[str, str] = {}
    for tool, path in tools.items():
        if path is None:
            continue
        versions[tool] = _tool_version(root, path)
    write_json(
        evidence / "environment.json",
        {
            "evidence_version": EVIDENCE_VERSION,
            "generated_at": utc_now(),
            "git_commit": commit,
            "tools": tools,
            "tool_versions": versions,
            "sanitized_environment_summary": sanitized_environment_summary(sanitized_gate_environment()),
        },
    )


def _tool_version(root: Path, executable: str) -> str:
    candidates = ([executable, "--version"], [executable, "version"])
    for cmd in candidates:
        try:
            proc = subprocess.run(
                cmd,
                cwd=root,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except Exception:
            continue
        output = (proc.stdout or proc.stderr).strip().splitlines()
        if output:
            return output[0][:300]
    return "unknown"


def _git_output(root: Path, *args: str, default: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=root, text=True).strip()
    except subprocess.CalledProcessError:
        return default


def summarize_results(state: GateState) -> dict[str, Any]:
    required = [result for result in state.results if result.required]
    optional = [result for result in state.results if not result.required]
    failed = [result for result in state.results if result.status == "FAIL"]
    required_skipped = [result for result in required if result.status == "SKIPPED"]
    passed = [result for result in required if result.status == "PASS"]
    skipped_optional = [result for result in optional if result.status == "SKIPPED"]
    return {
        "gate_id": GATE_ID,
        "sprint": SPRINT,
        "release_version": RELEASE_VERSION,
        "branch": state.git_branch,
        "commit": state.git_commit,
        "validated_source_commit": state.git_commit,
        "release_commit": getattr(state, "release_commit", None),
        "gate_phase": getattr(state, "gate_phase", "final"),
        "started_at": state.started_at,
        "completed_at": utc_now(),
        "overall_status": state.overall_status,
        "required_checks_count": len(required),
        "required_passed_count": len(passed),
        "required_failed_count": len([r for r in required if r.status == "FAIL"]),
        "required_skipped_count": len(required_skipped),
        "optional_failed_count": len([r for r in optional if r.status == "FAIL"]),
        "optional_skipped_count": len(skipped_optional),
        "first_failed_stage": state.first_failed_stage,
        "final_decision": decision_for(state.overall_status),
        "preflight_errors": state.preflight_errors,
        "checks": [asdict(result) for result in required],
        "optional_checks": [asdict(result) for result in optional],
        "failed_check_ids": [result.id for result in failed],
    }


def write_text_summary(path: Path, summary: Mapping[str, Any]) -> None:
    lines = [
        f"gate_id={summary['gate_id']}",
        f"sprint={summary['sprint']}",
        f"release_version={summary['release_version']}",
        f"branch={summary['branch']}",
        f"commit={summary['commit']}",
        f"overall_status={summary['overall_status']}",
        f"final_decision={summary['final_decision']}",
        f"first_failed_stage={summary['first_failed_stage']}",
        f"required_checks_count={summary['required_checks_count']}",
        f"required_passed_count={summary['required_passed_count']}",
        f"required_failed_count={summary['required_failed_count']}",
        f"required_skipped_count={summary['required_skipped_count']}",
        f"optional_failed_count={summary['optional_failed_count']}",
        f"optional_skipped_count={summary['optional_skipped_count']}",
        "",
    ]
    for check in summary["checks"]:
        lines.append(f"REQUIRED {check['id']}={check['status']}")
    for check in summary["optional_checks"]:
        lines.append(f"OPTIONAL {check['id']}={check['status']}")
    write_text(path, "\n".join(lines) + "\n")


def release_file_hashes(root: Path, release_dir: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(release_dir.rglob("*")):
        if not path.is_file() or path.name == "checksums.txt":
            continue
        rel = str(path.relative_to(root))
        hashes[rel] = sha256_file(path)
    return hashes


def write_checksums(root: Path, release_dir: Path) -> Path:
    lines = [f"{digest}  {rel}" for rel, digest in sorted(release_file_hashes(root, release_dir).items())]
    out = release_dir / "checksums.txt"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def verify_checksums(root: Path, release_dir: Path) -> None:
    checksums = release_dir / "checksums.txt"
    if not checksums.is_file() or checksums.stat().st_size == 0:
        raise FileNotFoundError("missing/empty checksums.txt")
    for line in checksums.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, sep, rel = line.partition("  ")
        if not sep:
            raise RuntimeError(f"invalid checksum line: {line!r}")
        path = root / rel.strip()
        if not path.is_file():
            raise FileNotFoundError(f"checksummed file missing: {rel.strip()}")
        actual = sha256_file(path)
        if actual != digest.strip():
            raise RuntimeError(f"checksum mismatch for {rel.strip()}")


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"JSON root must be an object: {path}")
    return payload


def require_file(path: Path) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise FileNotFoundError(f"missing/empty required file: {path}")


def all_evidence_files(root: Path) -> list[str]:
    evidence = root / "artifacts" / "sprint3" / "evidence"
    if not evidence.exists():
        return []
    return sorted(str(path.relative_to(root)) for path in evidence.rglob("*") if path.is_file())
