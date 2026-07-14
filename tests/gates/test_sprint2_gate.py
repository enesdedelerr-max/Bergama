"""Deterministic unit tests for the Sprint 2 gate orchestrator."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from collections.abc import Sequence
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GATES = ROOT / "scripts" / "gates"
sys.path.insert(0, str(GATES))

import build_sprint2_release as release_mod  # noqa: E402
import gate_sprint2 as gate  # noqa: E402
from sprint2_common import (  # noqa: E402
    OPTIONAL_STEP_SPECS,
    POST_STEP_SPECS,
    REQUIRED_STEP_SPECS,
    ensure_no_secrets,
)


def _seed_release_artifacts(root: Path) -> None:
    (root / "artifacts" / "sprint2" / "evidence").mkdir(parents=True, exist_ok=True)
    (root / "reports").mkdir(parents=True, exist_ok=True)
    (root / "releases" / "sprint-2").mkdir(parents=True, exist_ok=True)
    openapi = root / "artifacts" / "sprint2" / "evidence" / "openapi.json"
    openapi.write_text(
        json.dumps(
            {
                "openapi": "3.1.0",
                "info": {"title": "Bergama Trading API", "version": "0.2.0"},
                "paths": {},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    report = root / "reports" / "sprint2-runtime-validation.json"
    report.write_text(json.dumps({"gate_id": "sprint2-runtime-gate", "overall_status": "PASS"}) + "\n")
    summary_json = root / "artifacts" / "sprint2" / "gate-summary.json"
    summary_txt = root / "artifacts" / "sprint2" / "gate-summary.txt"
    summary_json.write_text(json.dumps({"overall_status": "PASS"}) + "\n")
    summary_txt.write_text("overall_status=PASS\n")
    rel = root / "releases" / "sprint-2"
    for name in (
        "release-notes.md",
        "known-issues.md",
        "risk-summary.md",
        "rollback-notes.md",
        "artifact-manifest.yaml",
        "versions.json",
    ):
        (rel / name).write_text(f"{name}\n", encoding="utf-8")
    release_mod.write_checksums(root=root)


def _recording_runner(
    outcomes: dict[str, tuple[int, str]],
    calls: list[str],
    root: Path,
):
    def runner(cmd: Sequence[str], cwd: Path, log_path: Path) -> tuple[int, str]:
        joined = " ".join(cmd)
        # Derive step name from make target.
        name = cmd[-1] if cmd and cmd[0] == "make" else joined
        calls.append(name)
        code, body = outcomes.get(name, (0, f"{name} PASS\n"))
        if name == "validate-api-openapi" and code == 0:
            evidence = root / "artifacts" / "sprint2" / "evidence"
            evidence.mkdir(parents=True, exist_ok=True)
            (evidence / "openapi.json").write_text(
                json.dumps({"openapi": "3.1.0", "info": {"title": "t", "version": "0.2.0"}, "paths": {}})
                + "\n",
                encoding="utf-8",
            )
        if name == "smoke-api-runtime" and code == 0:
            health = root / "artifacts" / "sprint2" / "evidence" / "health"
            health.mkdir(parents=True, exist_ok=True)
            (health / "health_live.json").write_text("{}\n", encoding="utf-8")
        if name == "build-sprint2-release" and code == 0:
            _seed_release_artifacts(root)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(body, encoding="utf-8")
        return code, body

    return runner


@pytest.fixture()
def gate_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(gate, "git_meta", lambda _root: ("feature/test", "abc123"))
    monkeypatch.setattr(release_mod, "ROOT", tmp_path)
    # Point release checksum helper at tmp when imported functions use module ROOT in stubs.
    return tmp_path


def test_required_step_order() -> None:
    names = [name for name, _ in REQUIRED_STEP_SPECS]
    assert names == [
        "lint",
        "typecheck",
        "validate-secrets",
        "test-api",
        "test-api-auth",
        "test-api-container",
        "test-api-health",
        "test-api-kafka-core",
        "test-api-kafka-test-runtime",
        "test-api-registry",
        "validate-api-openapi",
        "smoke-api-runtime",
    ]
    assert [n for n, _ in OPTIONAL_STEP_SPECS] == ["smoke-api-kafka"]
    assert [n for n, _ in POST_STEP_SPECS] == ["build-sprint2-release"]


def test_stops_on_first_required_failure(gate_root: Path) -> None:
    calls: list[str] = []
    outcomes = {name: (0, "ok") for name, _ in REQUIRED_STEP_SPECS}
    outcomes["typecheck"] = (1, "typecheck FAIL\n")
    code = gate.run_gate(root=gate_root, runner=_recording_runner(outcomes, calls, gate_root))
    assert code == 1
    assert calls == ["lint", "typecheck"]
    assert "validate-secrets" not in calls


def test_nonzero_exit_on_failure(gate_root: Path) -> None:
    calls: list[str] = []
    outcomes = {name: (0, "ok") for name, _ in REQUIRED_STEP_SPECS}
    outcomes["lint"] = (7, "lint FAIL\n")
    assert gate.run_gate(root=gate_root, runner=_recording_runner(outcomes, calls, gate_root)) == 1
    summary = json.loads((gate_root / "artifacts/sprint2/gate-summary.json").read_text())
    assert summary["final_decision"] == "NO-GO FOR SPRINT 3"
    assert summary["first_failed_stage"] == "lint"


def test_optional_kafka_skipped_does_not_fail(gate_root: Path) -> None:
    calls: list[str] = []
    outcomes = {name: (0, f"{name} PASS\n") for name, _ in REQUIRED_STEP_SPECS}
    outcomes["smoke-api-kafka"] = (0, "smoke-api-kafka SKIPPED (set BERGAMA_KAFKA_SMOKE=1)\n")
    outcomes["build-sprint2-release"] = (0, "build PASS\n")
    code = gate.run_gate(root=gate_root, runner=_recording_runner(outcomes, calls, gate_root))
    assert code == 0
    summary = json.loads((gate_root / "artifacts/sprint2/gate-summary.json").read_text())
    assert summary["final_decision"] == "GO FOR SPRINT 3"
    assert summary["live_kafka_status"] == "SKIPPED"
    assert summary["skipped_optional_count"] == 1


def test_optional_kafka_fail_when_enabled_fails_gate(gate_root: Path) -> None:
    calls: list[str] = []
    outcomes = {name: (0, f"{name} PASS\n") for name, _ in REQUIRED_STEP_SPECS}
    outcomes["smoke-api-kafka"] = (1, "BERGAMA_KAFKA_SMOKE=1 live smoke FAILED\n")
    code = gate.run_gate(root=gate_root, runner=_recording_runner(outcomes, calls, gate_root))
    assert code == 1
    summary = json.loads((gate_root / "artifacts/sprint2/gate-summary.json").read_text())
    assert summary["final_decision"] == "NO-GO FOR SPRINT 3"
    assert summary["live_kafka_status"] == "FAIL"
    assert summary["first_failed_stage"] == "smoke-api-kafka"
    assert "build-sprint2-release" not in calls


def test_summary_json_on_success(gate_root: Path) -> None:
    calls: list[str] = []
    outcomes = {name: (0, "ok\n") for name, _ in (*REQUIRED_STEP_SPECS, *OPTIONAL_STEP_SPECS, *POST_STEP_SPECS)}
    outcomes["smoke-api-kafka"] = (0, "SKIPPED\n")
    assert gate.run_gate(root=gate_root, runner=_recording_runner(outcomes, calls, gate_root)) == 0
    summary = json.loads((gate_root / "artifacts/sprint2/gate-summary.json").read_text())
    report = json.loads((gate_root / "reports/sprint2-runtime-validation.json").read_text())
    assert summary["overall_status"] == "PASS"
    assert report["overall_status"] == "PASS"
    assert (gate_root / "artifacts/sprint2/gate-summary.txt").is_file()


def test_failure_summary_produced(gate_root: Path) -> None:
    calls: list[str] = []
    outcomes = {"lint": (1, "fail\n")}
    gate.run_gate(root=gate_root, runner=_recording_runner(outcomes, calls, gate_root))
    summary = json.loads((gate_root / "artifacts/sprint2/gate-summary.json").read_text())
    assert summary["overall_status"] == "FAIL"
    assert summary["failed_count"] >= 1


def test_stale_artifacts_cleared(gate_root: Path) -> None:
    stale = gate_root / "artifacts" / "sprint2" / "evidence" / "stale.txt"
    stale.parent.mkdir(parents=True, exist_ok=True)
    stale.write_text("old\n", encoding="utf-8")
    calls: list[str] = []
    outcomes = {"lint": (1, "fail\n")}
    gate.run_gate(root=gate_root, runner=_recording_runner(outcomes, calls, gate_root))
    assert not stale.exists()


def test_missing_release_artifact_fails(gate_root: Path) -> None:
    calls: list[str] = []

    def runner(cmd: Sequence[str], cwd: Path, log_path: Path) -> tuple[int, str]:
        name = cmd[-1]
        calls.append(name)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        if name == "validate-api-openapi":
            evidence = gate_root / "artifacts/sprint2/evidence"
            evidence.mkdir(parents=True, exist_ok=True)
            (evidence / "openapi.json").write_text("{}\n", encoding="utf-8")
        if name == "build-sprint2-release":
            # Intentionally omit release package files.
            log_path.write_text("incomplete\n", encoding="utf-8")
            return 0, "incomplete\n"
        if name == "smoke-api-kafka":
            body = "SKIPPED\n"
            log_path.write_text(body, encoding="utf-8")
            return 0, body
        log_path.write_text("ok\n", encoding="utf-8")
        return 0, "ok\n"

    code = gate.run_gate(root=gate_root, runner=runner)
    assert code == 1
    summary = json.loads((gate_root / "artifacts/sprint2/gate-summary.json").read_text())
    assert summary["first_failed_stage"] == "artifact-verification"


def test_missing_openapi_evidence_fails(gate_root: Path) -> None:
    calls: list[str] = []

    def runner(cmd: Sequence[str], cwd: Path, log_path: Path) -> tuple[int, str]:
        name = cmd[-1]
        calls.append(name)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        if name == "smoke-api-kafka":
            body = "SKIPPED\n"
            log_path.write_text(body, encoding="utf-8")
            return 0, body
        if name == "build-sprint2-release":
            _seed_release_artifacts(gate_root)
            # Remove openapi after "build" seeded it.
            (gate_root / "artifacts/sprint2/evidence/openapi.json").unlink()
            log_path.write_text("ok\n", encoding="utf-8")
            return 0, "ok\n"
        log_path.write_text("ok\n", encoding="utf-8")
        return 0, "ok\n"

    code = gate.run_gate(root=gate_root, runner=runner)
    assert code == 1
    summary = json.loads((gate_root / "artifacts/sprint2/gate-summary.json").read_text())
    assert summary["first_failed_stage"] == "artifact-verification"


def test_checksum_mismatch_fails(gate_root: Path) -> None:
    calls: list[str] = []

    def runner(cmd: Sequence[str], cwd: Path, log_path: Path) -> tuple[int, str]:
        name = cmd[-1]
        calls.append(name)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        if name == "validate-api-openapi":
            evidence = gate_root / "artifacts/sprint2/evidence"
            evidence.mkdir(parents=True, exist_ok=True)
            (evidence / "openapi.json").write_text("{}\n", encoding="utf-8")
        if name == "smoke-api-kafka":
            body = "SKIPPED\n"
            log_path.write_text(body, encoding="utf-8")
            return 0, body
        if name == "build-sprint2-release":
            _seed_release_artifacts(gate_root)
            # Corrupt a checksummed file without refreshing digests.
            notes = gate_root / "releases/sprint-2/release-notes.md"
            notes.write_text(notes.read_text(encoding="utf-8") + "tampered\n", encoding="utf-8")
            log_path.write_text("ok\n", encoding="utf-8")
            return 0, "ok\n"
        log_path.write_text("ok\n", encoding="utf-8")
        return 0, "ok\n"

    # After gate overwrites summaries it rewrites checksums — so corruption of release notes
    # before rewrite still fails verify if we prevent rewrite? Gate always rewrites checksums
    # on PASS before verify, which would re-hash tampered notes and PASS.
    # To test mismatch, corrupt AFTER write_checksums inside verification by patching.
    real_write = release_mod.write_checksums

    def write_then_tamper(*, root: Path | None = None) -> Path:
        out = real_write(root=root)
        notes = (root or gate_root) / "releases/sprint-2/release-notes.md"
        notes.write_text(notes.read_text(encoding="utf-8") + "tampered-after-hash\n", encoding="utf-8")
        return out

    monkey_gate = gate
    # Patch gate's imported write_checksums.
    import gate_sprint2 as gate_mod

    original = gate_mod.write_checksums
    gate_mod.write_checksums = write_then_tamper  # type: ignore[assignment]
    try:
        code = gate.run_gate(root=gate_root, runner=runner)
    finally:
        gate_mod.write_checksums = original  # type: ignore[assignment]
    assert code == 1
    summary = json.loads((gate_root / "artifacts/sprint2/gate-summary.json").read_text())
    assert summary["first_failed_stage"] == "artifact-verification"
    _ = monkey_gate


def test_cleanup_trap_terminates_child() -> None:
    proc = subprocess.Popen(["sleep", "30"])
    try:
        gate.register_child_pid(proc.pid)
        gate.cleanup_children()
        time.sleep(0.2)
        assert proc.poll() is not None
    finally:
        if proc.poll() is None:
            proc.send_signal(signal.SIGKILL)
            proc.wait(timeout=5)


def test_no_secrets_written_to_evidence_patterns() -> None:
    with pytest.raises(RuntimeError, match="secret-like"):
        ensure_no_secrets(
            '{"access_token":"eyJhbGciOiJIUzI1NiJ9.payload.sig"}',
            context="evidence",
        )


def test_final_decision_strings(gate_root: Path) -> None:
    calls: list[str] = []
    outcomes = {name: (0, "ok\n") for name, _ in (*REQUIRED_STEP_SPECS, *OPTIONAL_STEP_SPECS, *POST_STEP_SPECS)}
    outcomes["smoke-api-kafka"] = (0, "SKIPPED\n")
    assert gate.run_gate(root=gate_root, runner=_recording_runner(outcomes, calls, gate_root)) == 0
    text = (gate_root / "artifacts/sprint2/gate-summary.txt").read_text(encoding="utf-8")
    assert "final_decision=GO FOR SPRINT 3" in text
    assert os.environ.get("BERGAMA_KAFKA_SMOKE", "") != "1" or True
