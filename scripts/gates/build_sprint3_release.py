"""Build the tracked Sprint 3 release package from validated evidence."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from collections.abc import Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any

from scripts.gates.sprint3_common import (
    EVIDENCE_VERSION,
    GO_DECISION,
    RELEASE_VERSION,
    ensure_no_secrets,
    git_meta,
    read_json,
    release_file_hashes,
    sha256_file,
    utc_now,
    write_checksums,
    write_json,
    write_text,
)
from scripts.gates.validate_sprint3_evidence import validate_evidence

ROOT = Path(__file__).resolve().parents[2]
RELEASE_DIR = ROOT / "releases" / "sprint-3"


def _run_syft(root: Path) -> dict[str, Any]:
    syft = shutil.which("syft")
    if syft is None:
        raise RuntimeError("syft is required for Sprint 3 release SBOM")
    proc = subprocess.run(
        [syft, "dir:apps/api", "-o", "spdx-json"],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"syft failed with exit code {proc.returncode}: {proc.stderr[:500]}")
    ensure_no_secrets(proc.stdout, context="syft output")
    payload = json.loads(proc.stdout)
    if not isinstance(payload, dict) or "packages" not in payload:
        raise RuntimeError("syft did not produce valid-looking SPDX JSON")
    return payload


def _sort_list(value: list[Any]) -> list[Any]:
    if all(isinstance(item, dict) for item in value):
        return sorted(
            (_normalize_json(item) for item in value),
            key=lambda item: json.dumps(item, sort_keys=True, separators=(",", ":")),
        )
    return [_normalize_json(item) for item in value]


def _normalize_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _normalize_json(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return _sort_list(value)
    return value


def _normalize_sbom(sbom: dict[str, Any], *, normalized_created: str) -> dict[str, Any]:
    payload = deepcopy(sbom)
    creation = payload.setdefault("creationInfo", {})
    if isinstance(creation, dict):
        creation["created"] = normalized_created
    return _normalize_json(payload)


def _generate_openapi(root: Path) -> dict[str, Any]:
    api_path = str(root / "apps" / "api")
    if api_path not in sys.path:
        sys.path.insert(0, api_path)
    from app.factory import create_app  # noqa: PLC0415

    schema = create_app().openapi()
    return _normalize_json(schema)


def _collect_command_results(root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    evidence = root / "artifacts" / "sprint3" / "evidence"
    required: list[dict[str, Any]] = []
    optional: list[dict[str, Any]] = []
    for name in (
        "static-checks.json",
        "focused-tests.json",
        "regression.json",
        "offline-smokes.json",
        "runtime-smoke.json",
        "provider-smokes.json",
    ):
        payload = read_json(evidence / name)
        rows = payload.get("results", payload.get("command_results", []))
        if not isinstance(rows, list):
            raise RuntimeError(f"{name} command rows must be a list")
        for row in rows:
            if not isinstance(row, dict):
                continue
            target = required if row.get("required") is True else optional
            target.append(
                {
                    "id": row.get("id"),
                    "status": row.get("status"),
                    "required": row.get("required"),
                    "duration_seconds": row.get("duration_seconds"),
                    "exit_code": row.get("exit_code"),
                    "log_path": row.get("log_path"),
                    "skip_reason": row.get("skip_reason"),
                    "timeout_seconds": row.get("timeout_seconds"),
                }
            )
    return required, optional


def _runtime_summary(root: Path) -> dict[str, Any]:
    runtime = read_json(root / "artifacts" / "sprint3" / "evidence" / "runtime-smoke.json")
    return {
        "evidence_version": runtime.get("evidence_version"),
        "git_commit": runtime.get("git_commit"),
        "environment": runtime.get("environment"),
        "topic": runtime.get("topic"),
        "consumer_group": runtime.get("consumer_group"),
        "table": runtime.get("table"),
        "event_type": runtime.get("event_type"),
        "idempotency_key": runtime.get("idempotency_key"),
        "kafka_ack_metadata": runtime.get("kafka_ack_metadata"),
        "snapshot_id": runtime.get("snapshot_id"),
        "row_verification_summary": runtime.get("row_verification_summary"),
        "decimal_verification": runtime.get("decimal_verification"),
        "offset_before": runtime.get("offset_before"),
        "offset_after": runtime.get("offset_after"),
        "operation_timestamps": runtime.get("operation_timestamps"),
        "quality_assessment_summary": runtime.get("quality_assessment_summary"),
        "kafka_ack_verified": runtime.get("kafka_ack_verified"),
        "snapshot_verified": runtime.get("snapshot_verified"),
        "row_verified": runtime.get("row_verified"),
        "decimal_verified": runtime.get("decimal_verified"),
        "offset_after_durability_verified": runtime.get("offset_after_durability_verified"),
        "final_status": runtime.get("final_status"),
        "safe_limitations": runtime.get("safe_limitations"),
    }


def _quality_gate_summary(root: Path, *, commit: str) -> dict[str, Any]:
    required, optional = _collect_command_results(root)
    return _normalize_json(
        {
            "evidence_version": EVIDENCE_VERSION,
            "release_version": RELEASE_VERSION,
            "git_commit": commit,
            "final_decision": GO_DECISION,
            "required_results": required,
            "optional_provider_results": optional,
        }
    )


def _write_docs(root: Path, release_dir: Path, *, commit: str) -> None:
    readme = f"""# Sprint 3 Release Package

This package is the self-contained Sprint 3 runtime validation and release evidence for `{RELEASE_VERSION}`.

## Validate

Run from the repository root:

```bash
make validate-sprint3-release
```

## Reproduce

Run from a clean checkout at commit `{commit}` with required local Kafka, Iceberg REST catalog, and MinIO available:

```bash
make gate-sprint3
```

Post-merge tag policy is documented in `docs/sprints/sprint-3/README.md`. Do not create or push `v0.3.0-sprint3` unless the merged-main gate has passed and explicit approval is given.

## Artifacts

- `sprint3-quality-gate.json`: normalized required and optional gate results.
- `sprint3-runtime-validation.json`: normalized Kafka to Iceberg runtime proof.
- `sprint3-openapi.json`: current generated API schema.
- `sbom.spdx.json`: real Syft SPDX JSON SBOM with normalized volatile creation timestamp.
- `MANIFEST.json`: release metadata, hashes, tool versions, and source evidence hashes.
- `checksums.txt`: SHA-256 hashes for tracked release files.
"""
    notes = """# Sprint 3 Release Notes

## Completed

- Canonical market-data contracts.
- Historical and realtime provider connectors.
- Cross-provider contract tests.
- Market Data Orchestrator.
- Kafka publish adapter.
- Iceberg writer.
- Replay engine.
- Historical backfill pipeline.
- Data quality and monitoring.
- Fail-closed Sprint 3 runtime gate and reproducible release package.
"""
    limitations = """# Sprint 3 Known Limitations

- At-least-once delivery only; exactly-once delivery is not claimed.
- Iceberg writes are append-only.
- Deduplication is process-local and not durable across restarts.
- Quality metrics are process-local.
- Replay ordering differs from original Kafka order.
- Multi-table Iceberg snapshots are not atomic.
- Finnhub and SEC connectors are bounded refresh sources.
- Optional provider live smokes may be SKIPPED when credentials or entitlements are unavailable.
- No external alert delivery.
- No Prometheus exporter.
- Production OIDC remains out of Sprint 3 scope if not already configured.
"""
    write_text(release_dir / "README.md", readme)
    write_text(release_dir / "RELEASE_NOTES.md", notes)
    write_text(release_dir / "sprint3-known-limitations.md", limitations)


def _manifest_file_hashes(root: Path, release_dir: Path) -> dict[str, str]:
    return {
        rel: digest
        for rel, digest in release_file_hashes(root, release_dir).items()
        if not rel.endswith("/MANIFEST.json")
    }


def build_release(root: Path) -> None:
    validation = validate_evidence(root, validate_release=False, require_release_evidence=False)
    if validation.status != "PASS":
        reasons = "; ".join(validation.reasons)
        raise RuntimeError(f"cannot build Sprint 3 release from invalid evidence: {reasons}")

    branch, commit = git_meta(root)
    release_dir = root / "releases" / "sprint-3"
    release_dir.mkdir(parents=True, exist_ok=True)
    for child in sorted(release_dir.iterdir()):
        if child.is_file():
            child.unlink()

    evidence = root / "artifacts" / "sprint3" / "evidence"
    evidence_hashes = {
        str(path.relative_to(root)): sha256_file(path)
        for path in sorted(evidence.glob("*.json"))
        if path.name != "checksums.json"
    }
    quality_gate = _quality_gate_summary(root, commit=commit)
    runtime_summary = _normalize_json(_runtime_summary(root))
    openapi = _generate_openapi(root)
    normalized_created = read_json(evidence / "git-state.json").get("generated_at", utc_now())
    sbom_first = _normalize_sbom(_run_syft(root), normalized_created=str(normalized_created))
    sbom_second = _normalize_sbom(_run_syft(root), normalized_created=str(normalized_created))
    if sbom_first != sbom_second:
        raise RuntimeError("normalized Syft SBOM generation drifted across two runs")

    _write_docs(root, release_dir, commit=commit)
    write_json(release_dir / "sprint3-quality-gate.json", quality_gate)
    write_json(release_dir / "sprint3-runtime-validation.json", runtime_summary)
    write_json(release_dir / "sprint3-openapi.json", openapi)
    write_json(release_dir / "sbom.spdx.json", sbom_first)

    syft_version = subprocess.check_output(["syft", "--version"], cwd=root, text=True).strip()
    manifest = {
        "release_version": RELEASE_VERSION,
        "validated_commit": commit,
        "source_branch": branch,
        "generated_at": normalized_created,
        "evidence_version": EVIDENCE_VERSION,
        "source_evidence_hashes": evidence_hashes,
        "gate_decision": GO_DECISION,
        "runtime_smoke_result": runtime_summary.get("final_status"),
        "optional_smoke_statuses": {
            item["id"]: item["status"] for item in quality_gate["optional_provider_results"]
        },
        "tool_versions": {"syft": syft_version},
        "sbom": {
            "format": "spdx-json",
            "generator": "syft",
            "scan_target": "apps/api",
            "normalized_fields": ["creationInfo.created"],
        },
        "manifest_included_in_checksums": True,
        "files": {},
    }
    write_json(release_dir / "MANIFEST.json", manifest)
    write_checksums(root, release_dir)
    manifest["files"] = _manifest_file_hashes(root, release_dir)
    write_json(release_dir / "MANIFEST.json", manifest)
    write_checksums(root, release_dir)
    first_hashes = release_file_hashes(root, release_dir)
    write_json(release_dir / "MANIFEST.json", manifest)
    write_checksums(root, release_dir)
    second_hashes = release_file_hashes(root, release_dir)
    if first_hashes != second_hashes:
        raise RuntimeError("release regeneration drifted")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Sprint 3 release package")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        build_release(args.root.resolve())
    except Exception as exc:  # noqa: BLE001 - command boundary
        print(f"FAIL: {exc}")
        return 1
    print("PASS: Sprint 3 release package built")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
