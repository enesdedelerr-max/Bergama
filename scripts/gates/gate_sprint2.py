"""Sprint 2 fail-closed gate orchestrator."""

from __future__ import annotations

import argparse
import atexit
import signal
import sys
from collections.abc import Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "scripts" / "gates") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts" / "gates"))

from build_sprint2_release import verify_checksums, write_checksums  # noqa: E402
from sprint2_common import (  # noqa: E402
    OPTIONAL_STEP_SPECS,
    POST_STEP_SPECS,
    REQUIRED_STEP_SPECS,
    CheckResult,
    GateState,
    Runner,
    Status,
    clear_directory,
    command_string,
    default_runner,
    decision_for,
    git_meta,
    interpret_optional_kafka,
    sha256_file,
    summary_payload,
    utc_now,
    validation_report,
    write_json,
    write_text_summary,
)

_CHILD_PIDS: set[int] = set()


def register_child_pid(pid: int) -> None:
    """Track a child PID so signal/atexit cleanup can terminate orphans."""
    _CHILD_PIDS.add(pid)


def cleanup_children() -> None:
    """Best-effort terminate of tracked children (success, failure, signals)."""
    for pid in list(_CHILD_PIDS):
        try:
            Path(f"/proc/{pid}").exists()  # Linux hint; ignored on macOS
        except OSError:
            pass
        try:
            import os

            os.kill(pid, signal.SIGTERM)
        except (OSError, ProcessLookupError):
            pass
        _CHILD_PIDS.discard(pid)


def _install_signal_handlers() -> None:
    def _handler(signum: int, _frame: object) -> None:
        cleanup_children()
        raise SystemExit(128 + signum)

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, _handler)
        except ValueError:
            # Not in main thread.
            return
    atexit.register(cleanup_children)


def run_required_steps(
    state: GateState,
    *,
    runner: Runner = default_runner,
    steps: Sequence[tuple[str, tuple[str, ...]]] = REQUIRED_STEP_SPECS,
) -> None:
    for name, cmd in steps:
        print(f"[gate-sprint2] BEGIN {name}")
        log_path = state.logs / f"{name}.log"
        import time

        started = time.perf_counter()
        code, _body = runner(cmd, state.root, log_path)
        duration = round(time.perf_counter() - started, 3)
        if code != 0:
            result = CheckResult(
                name=name,
                status="FAIL",
                command=command_string(cmd),
                duration_seconds=duration,
                log_path=str(log_path.relative_to(state.root)),
                message=f"command exited {code}",
                corrective_action=(
                    f"Fix failures from `{command_string(cmd)}` and re-run make gate-sprint2"
                ),
            )
            state.checks.append(result)
            state.overall_status = "FAIL"
            state.first_failed_stage = name
            print(f"[gate-sprint2] FAIL {name} exit={code}")
            return
        state.checks.append(
            CheckResult(
                name=name,
                status="PASS",
                command=command_string(cmd),
                duration_seconds=duration,
                log_path=str(log_path.relative_to(state.root)),
                message="ok",
            )
        )
        print(f"[gate-sprint2] PASS {name}")


def run_optional_steps(
    state: GateState,
    *,
    runner: Runner = default_runner,
    steps: Sequence[tuple[str, tuple[str, ...]]] = OPTIONAL_STEP_SPECS,
) -> Status:
    live_status: Status = "SKIPPED"
    if state.overall_status == "FAIL":
        return live_status
    for name, cmd in steps:
        print(f"[gate-sprint2] BEGIN {name} (optional)")
        log_path = state.logs / f"{name}.log"
        import time

        started = time.perf_counter()
        code, body = runner(cmd, state.root, log_path)
        duration = round(time.perf_counter() - started, 3)
        status = (
            interpret_optional_kafka(body, code)
            if name == "smoke-api-kafka"
            else ("PASS" if code == 0 else "FAIL")
        )
        live_status = status
        result = CheckResult(
            name=name,
            status=status,
            command=command_string(cmd),
            duration_seconds=duration,
            log_path=str(log_path.relative_to(state.root)),
            message="ok" if status != "FAIL" else f"command exited {code}",
            corrective_action=(
                None
                if status != "FAIL"
                else "Enable a provisioned broker/topic or disable BERGAMA_KAFKA_SMOKE"
            ),
        )
        state.optional_checks.append(result)
        print(f"[gate-sprint2] {status} {name}")
        if status == "FAIL":
            state.overall_status = "FAIL"
            state.first_failed_stage = name
            return live_status
    return live_status


def run_post_steps(
    state: GateState,
    *,
    runner: Runner = default_runner,
    steps: Sequence[tuple[str, tuple[str, ...]]] = POST_STEP_SPECS,
) -> None:
    if state.overall_status == "FAIL":
        return
    for name, cmd in steps:
        print(f"[gate-sprint2] BEGIN {name}")
        log_path = state.logs / f"{name}.log"
        import time

        started = time.perf_counter()
        code, _body = runner(cmd, state.root, log_path)
        duration = round(time.perf_counter() - started, 3)
        if code != 0:
            state.checks.append(
                CheckResult(
                    name=name,
                    status="FAIL",
                    command=command_string(cmd),
                    duration_seconds=duration,
                    log_path=str(log_path.relative_to(state.root)),
                    message=f"command exited {code}",
                    corrective_action=f"Fix `{command_string(cmd)}`",
                )
            )
            state.overall_status = "FAIL"
            state.first_failed_stage = name
            print(f"[gate-sprint2] FAIL {name} exit={code}")
            return
        state.checks.append(
            CheckResult(
                name=name,
                status="PASS",
                command=command_string(cmd),
                duration_seconds=duration,
                log_path=str(log_path.relative_to(state.root)),
                message="ok",
            )
        )
        print(f"[gate-sprint2] PASS {name}")


def collect_evidence_paths(root: Path) -> list[str]:
    evidence = root / "artifacts" / "sprint2" / "evidence"
    if not evidence.exists():
        return []
    return sorted(str(path.relative_to(root)) for path in evidence.rglob("*") if path.is_file())


def verify_required_artifacts(root: Path) -> None:
    required = (
        "artifacts/sprint2/evidence/openapi.json",
        "reports/sprint2-runtime-validation.json",
        "artifacts/sprint2/gate-summary.json",
        "artifacts/sprint2/gate-summary.txt",
        "releases/sprint-2/release-notes.md",
        "releases/sprint-2/known-issues.md",
        "releases/sprint-2/risk-summary.md",
        "releases/sprint-2/rollback-notes.md",
        "releases/sprint-2/artifact-manifest.yaml",
        "releases/sprint-2/versions.json",
        "releases/sprint-2/checksums.txt",
    )
    for rel in required:
        path = root / rel
        if not path.is_file() or path.stat().st_size == 0:
            msg = f"missing/empty required artifact: {rel}"
            raise FileNotFoundError(msg)
    for line in (root / "releases/sprint-2/checksums.txt").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, _, rel = line.partition("  ")
        path = root / rel.strip()
        if sha256_file(path) != digest.strip():
            msg = f"checksum mismatch: {rel}"
            raise RuntimeError(msg)


def write_summaries(
    state: GateState,
    *,
    branch: str,
    commit: str,
    live_kafka_status: Status,
) -> dict[str, object]:
    state.completed_at = utc_now()
    evidence_paths = collect_evidence_paths(state.root)
    report = validation_report(
        state,
        branch=branch,
        commit=commit,
        evidence_paths=evidence_paths,
        live_kafka_status=live_kafka_status,
    )
    write_json(state.root / "reports" / "sprint2-runtime-validation.json", report)
    summary = summary_payload(
        state,
        branch=branch,
        commit=commit,
        live_kafka_status=live_kafka_status,
    )
    write_json(state.art / "gate-summary.json", summary)
    write_text_summary(state.art / "gate-summary.txt", summary)
    return summary


def run_gate(*, root: Path = ROOT, runner: Runner = default_runner) -> int:
    _install_signal_handlers()
    state = GateState(root=root, started_at=utc_now())
    clear_directory(state.art)
    state.logs.mkdir(parents=True, exist_ok=True)
    state.evidence.mkdir(parents=True, exist_ok=True)
    (root / "reports").mkdir(parents=True, exist_ok=True)

    branch, commit = git_meta(root)
    print(f"[gate-sprint2] start branch={branch} commit={commit}")

    run_required_steps(state, runner=runner)
    live_kafka_status = run_optional_steps(state, runner=runner)
    run_post_steps(state, runner=runner)

    summary = write_summaries(
        state,
        branch=branch,
        commit=commit,
        live_kafka_status=live_kafka_status,
    )

    if state.overall_status == "PASS":
        try:
            # Refresh checksums after real summaries/report replace any stubs.
            write_checksums(root=root)
            verify_checksums(root=root)
            verify_required_artifacts(root)
        except Exception as exc:  # noqa: BLE001
            state.overall_status = "FAIL"
            state.first_failed_stage = "artifact-verification"
            state.checks.append(
                CheckResult(
                    name="artifact-verification",
                    status="FAIL",
                    command="verify_required_artifacts",
                    duration_seconds=0.0,
                    log_path=None,
                    message=str(exc),
                    corrective_action="Ensure smoke/openapi/release stages produced evidence",
                )
            )
            summary = write_summaries(
                state,
                branch=branch,
                commit=commit,
                live_kafka_status=live_kafka_status,
            )

    decision = decision_for(state.overall_status)
    print(f"[gate-sprint2] final_decision={decision}")
    print(decision)
    _ = summary
    cleanup_children()
    return 0 if state.overall_status == "PASS" else 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sprint 2 runtime gate")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(list(argv) if argv is not None else None)
    return run_gate(root=args.root.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
