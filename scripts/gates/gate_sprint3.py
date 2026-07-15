"""Sprint 3 fail-closed runtime gate."""

from __future__ import annotations

import argparse
import subprocess
from collections.abc import Sequence
from pathlib import Path

from scripts.gates.sprint3_common import (
    APPROVED_SPRINT3_RELEASE_PATHS,
    GO_DECISION,
    CommandResult,
    CommandSpec,
    GateState,
    Runner,
    all_evidence_files,
    clear_directory,
    command_specs,
    decision_for,
    default_runner,
    git_is_dirty,
    git_meta,
    preflight_payload,
    result_payload,
    read_json,
    summarize_results,
    utc_now,
    write_environment,
    write_git_state,
    write_json,
    write_text_summary,
)

ROOT = Path(__file__).resolve().parents[2]
RELEASE_PACKAGE_READY = "RELEASE PACKAGE READY"


def _write_group_evidence(state: GateState, group: str) -> None:
    results = [result for result in state.results if _group_for(result.id) == group]
    if group == "runtime-smoke":
        path = state.evidence / "runtime-smoke.json"
        payload: dict[str, object]
        if path.is_file():
            try:
                payload = read_json(path)
            except Exception:  # noqa: BLE001 - malformed runtime evidence is caught later
                payload = {}
        else:
            payload = {}
        payload["command_results"] = result_payload(results)["results"]
        write_json(path, payload)
        return
    write_json(state.evidence / f"{group}.json", result_payload(results))


def _group_for(result_id: str) -> str:
    for spec in command_specs():
        if spec.id == result_id:
            return spec.group
    return "unknown"


def _record_result(state: GateState, result: CommandResult) -> None:
    state.results.append(result)
    _write_group_evidence(state, _group_for(result.id))
    if result.required and result.status != "PASS":
        state.overall_status = "FAIL"
        state.first_failed_stage = state.first_failed_stage or result.id
    if not result.required and result.status == "FAIL":
        state.overall_status = "FAIL"
        state.first_failed_stage = state.first_failed_stage or result.id
        state.optional_failures.append(result.id)


def _run_spec(state: GateState, spec: CommandSpec, *, runner: Runner) -> None:
    log_path = state.logs / f"{spec.id}.log"
    print(f"[gate-sprint3] run {spec.id}: {spec.command}")
    result = runner(spec, state.root, log_path, state.git_commit)
    _record_result(state, result)
    print(f"[gate-sprint3] {spec.id}={result.status}")


def _run_group(state: GateState, group: str, *, runner: Runner) -> None:
    for spec in command_specs():
        if spec.group != group:
            continue
        _run_spec(state, spec, runner=runner)
        if spec.required and state.overall_status == "FAIL":
            return


def _write_summaries(state: GateState) -> dict[str, object]:
    summary = summarize_results(state)
    if getattr(state, "gate_phase", "final") == "prepare" and state.overall_status == "PASS":
        summary["final_decision"] = RELEASE_PACKAGE_READY
    summary["evidence_paths"] = all_evidence_files(state.root)
    write_json(state.art / "gate-summary.json", summary)
    write_text_summary(state.art / "gate-summary.txt", summary)
    return summary


def _fail_preflight(state: GateState, preflight: dict[str, object]) -> None:
    state.overall_status = "FAIL"
    errors = preflight.get("errors", [])
    state.preflight_errors = [str(error) for error in errors if str(error)]
    state.first_failed_stage = "preflight"
    write_json(state.evidence / "preflight.json", preflight)


def _git_status_paths(root: Path) -> list[str]:
    proc = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if proc.returncode != 0:
        return ["<git-status-failed>"]
    paths: list[str] = []
    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:]
        if " -> " in path:
            path = path.rsplit(" -> ", 1)[1]
        paths.append(path)
    return sorted(paths)


def _unexpected_dirty_paths(root: Path) -> list[str]:
    return sorted(path for path in _git_status_paths(root) if path not in APPROVED_SPRINT3_RELEASE_PATHS)


def _read_release_manifest(root: Path) -> dict[str, object] | None:
    path = root / "releases" / "sprint-3" / "MANIFEST.json"
    if not path.is_file():
        return None
    try:
        payload = read_json(path)
    except Exception:  # noqa: BLE001
        return None
    return payload if isinstance(payload, dict) else None


def _is_full_sha(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 40
        and value == value.lower()
        and all(char in "0123456789abcdef" for char in value)
    )


def _git_success(root: Path, *args: str) -> bool:
    return (
        subprocess.run(
            ["git", *args],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        ).returncode
        == 0
    )


def _changed_paths_between(root: Path, base: str, head: str) -> list[str]:
    proc = subprocess.run(
        ["git", "diff", "--name-only", f"{base}..{head}"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if proc.returncode != 0:
        return ["<git-diff-failed>"]
    return sorted(path for path in proc.stdout.splitlines() if path)


def _prepare_preflight(root: Path, *, git_commit: str) -> dict[str, object]:
    payload = preflight_payload(root, git_commit=git_commit)
    unexpected = _unexpected_dirty_paths(root)
    if unexpected:
        return payload
    errors = [error for error in payload.get("errors", []) if error != "working tree is dirty"]
    checks = dict(payload.get("checks", {}))
    checks["working_tree_clean"] = True
    checks["release_dirty_paths_allowed"] = _git_status_paths(root)
    payload["checks"] = checks
    payload["errors"] = errors
    payload["status"] = "PASS" if not errors else "FAIL"
    return payload


def _final_context(root: Path, *, head_commit: str) -> tuple[str, list[str], list[str]]:
    manifest = _read_release_manifest(root)
    if manifest is None:
        return head_commit, ["missing release package; run make prepare-sprint3-release"], []
    validated_source_commit = manifest.get("validated_source_commit")
    if not _is_full_sha(validated_source_commit):
        return head_commit, ["release manifest missing validated_source_commit"], []
    source = str(validated_source_commit)
    errors: list[str] = []
    if not _git_success(root, "merge-base", "--is-ancestor", source, head_commit):
        errors.append("validated_source_commit is not an ancestor of HEAD")
    changed_paths = _changed_paths_between(root, source, head_commit)
    unexpected = sorted(path for path in changed_paths if path not in APPROVED_SPRINT3_RELEASE_PATHS)
    if unexpected:
        errors.append(f"non-release changes after validated source commit: {unexpected}")
    return source, errors, changed_paths


def _write_release_attestation(
    root: Path,
    *,
    validated_source_commit: str,
    release_commit: str,
    release_paths: list[str],
) -> None:
    parent = subprocess.check_output(["git", "rev-parse", f"{release_commit}^"], cwd=root, text=True).strip()
    write_json(
        root / "artifacts" / "sprint3" / "evidence" / "release-attestation.json",
        {
            "validated_source_commit": validated_source_commit,
            "release_commit": release_commit,
            "release_commit_parent": parent,
            "release_only_diff_verified": True,
            "release_paths": release_paths,
            "gate_phase": "final",
            "validated_at": utc_now(),
            "final_status": "PASS",
        },
    )


def _decision(state: GateState) -> str:
    if getattr(state, "gate_phase", "final") == "prepare" and state.overall_status == "PASS":
        return RELEASE_PACKAGE_READY
    return decision_for(state.overall_status)


def _run_full_gate(state: GateState, *, runner: Runner) -> None:
    for group in (
        "static-checks",
        "focused-tests",
        "regression",
        "offline-smokes",
        "runtime-smoke",
        "provider-smokes",
        "release",
    ):
        _run_group(state, group, runner=runner)
        if state.overall_status == "FAIL" and group != "provider-smokes":
            break


def _run_final_release_validation(state: GateState, *, runner: Runner) -> None:
    for spec in command_specs():
        if spec.id in {
            "build-sprint3-release",
            "validate-sprint3-evidence",
            "validate-sprint3-release",
        }:
            _run_spec(state, spec, runner=runner)
            if state.overall_status == "FAIL":
                break


def run_gate(*, root: Path = ROOT, runner: Runner = default_runner, phase: str = "final") -> int:
    if phase not in {"prepare", "final"}:
        raise ValueError("phase must be prepare or final")
    branch, head_commit = git_meta(root)
    commit = head_commit
    final_context_errors: list[str] = []
    release_paths: list[str] = []
    if phase == "final":
        commit, final_context_errors, release_paths = _final_context(root, head_commit=head_commit)
    state = GateState(root=root, started_at=utc_now(), git_branch=branch, git_commit=commit)
    state.gate_phase = phase  # type: ignore[attr-defined]
    state.release_commit = head_commit if phase == "final" and commit != head_commit else None  # type: ignore[attr-defined]
    if phase == "prepare":
        clear_directory(state.art)
    state.logs.mkdir(parents=True, exist_ok=True)
    state.evidence.mkdir(parents=True, exist_ok=True)

    print(f"[gate-sprint3] start branch={branch} commit={commit}")
    if phase == "prepare":
        write_environment(root, state.evidence, commit=commit)
        write_git_state(root, state.evidence, branch=branch, commit=commit)
    preflight = (
        _prepare_preflight(root, git_commit=commit)
        if phase == "prepare"
        else preflight_payload(root, git_commit=commit)
    )
    if final_context_errors:
        preflight["status"] = "FAIL"
        preflight["errors"] = [*list(preflight.get("errors", [])), *final_context_errors]
    if preflight["status"] != "PASS":
        _fail_preflight(state, preflight)
        summary = _write_summaries(state)
        decision = _decision(state)
        print(f"[gate-sprint3] final_decision={decision}")
        print(decision)
        _ = summary
        return 1
    if phase == "prepare":
        write_json(state.evidence / "preflight.json", preflight)

    if phase == "prepare":
        _run_full_gate(state, runner=runner)
    else:
        _run_final_release_validation(state, runner=runner)

    if state.overall_status == "PASS":
        if phase == "prepare":
            unexpected = _unexpected_dirty_paths(root)
            if unexpected:
                state.overall_status = "FAIL"
                state.first_failed_stage = "prepare-working-tree"
                state.preflight_errors.append(f"unexpected dirty paths after prepare: {unexpected}")
        elif git_is_dirty(root):
            state.overall_status = "FAIL"
            state.first_failed_stage = "final-working-tree"
            state.preflight_errors.append("release regeneration drifted or left uncommitted files")
        else:
            _write_release_attestation(
                root,
                validated_source_commit=commit,
                release_commit=head_commit,
                release_paths=release_paths,
            )

    summary = _write_summaries(state)
    decision = _decision(state)
    print(f"[gate-sprint3] final_decision={decision}")
    print(decision)
    _ = summary
    return 0 if state.overall_status == "PASS" else 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sprint 3 runtime gate")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--phase", choices=("prepare", "final"), default="final")
    args = parser.parse_args(list(argv) if argv is not None else None)
    return run_gate(root=args.root.resolve(), phase=args.phase)


if __name__ == "__main__":
    raise SystemExit(main())
