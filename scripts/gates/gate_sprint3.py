"""Sprint 3 fail-closed runtime gate."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from scripts.gates.sprint3_common import (
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


def run_gate(*, root: Path = ROOT, runner: Runner = default_runner) -> int:
    branch, commit = git_meta(root)
    state = GateState(root=root, started_at=utc_now(), git_branch=branch, git_commit=commit)
    clear_directory(state.art)
    state.logs.mkdir(parents=True, exist_ok=True)
    state.evidence.mkdir(parents=True, exist_ok=True)

    print(f"[gate-sprint3] start branch={branch} commit={commit}")
    write_environment(root, state.evidence, commit=commit)
    write_git_state(root, state.evidence, branch=branch, commit=commit)
    preflight = preflight_payload(root, git_commit=commit)
    if preflight["status"] != "PASS":
        _fail_preflight(state, preflight)
        summary = _write_summaries(state)
        decision = decision_for(state.overall_status)
        print(f"[gate-sprint3] final_decision={decision}")
        print(decision)
        _ = summary
        return 1
    write_json(state.evidence / "preflight.json", preflight)

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

    if state.overall_status == "PASS" and git_is_dirty(root):
        state.overall_status = "FAIL"
        state.first_failed_stage = "final-working-tree"
        state.preflight_errors.append(
            "working tree changed during gate; commit expected release files before final gate"
        )

    summary = _write_summaries(state)
    decision = decision_for(state.overall_status)
    print(f"[gate-sprint3] final_decision={decision}")
    print(decision)
    _ = summary
    return 0 if state.overall_status == "PASS" else 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sprint 3 runtime gate")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(list(argv) if argv is not None else None)
    return run_gate(root=args.root.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
