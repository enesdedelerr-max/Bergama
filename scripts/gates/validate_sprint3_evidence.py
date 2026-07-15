"""Validate Sprint 3 gate evidence and release package."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from scripts.gates.sprint3_common import (
    APPROVED_SPRINT3_RELEASE_PATHS,
    EVIDENCE_VERSION,
    GO_DECISION,
    NO_GO_DECISION,
    RELEASE_VERSION,
    all_evidence_files,
    ensure_no_secrets,
    git_meta,
    read_json,
    release_file_hashes,
    require_file,
    verify_checksums,
    write_json,
)

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_EVIDENCE = (
    "environment.json",
    "git-state.json",
    "preflight.json",
    "static-checks.json",
    "focused-tests.json",
    "regression.json",
    "offline-smokes.json",
    "runtime-smoke.json",
    "provider-smokes.json",
    "release.json",
)

RELEASE_FILES = (
    "README.md",
    "RELEASE_NOTES.md",
    "MANIFEST.json",
    "checksums.txt",
    "sprint3-runtime-validation.json",
    "sprint3-openapi.json",
    "sprint3-quality-gate.json",
    "sprint3-known-limitations.md",
    "sbom.spdx.json",
)


@dataclass
class ValidationResult:
    status: str = "PASS"
    reasons: list[str] = field(default_factory=list)

    def fail(self, reason: str) -> None:
        self.status = "FAIL"
        self.reasons.append(reason)


def _safe_log_path(root: Path, rel: str) -> Path:
    path = Path(rel)
    if path.is_absolute() or ".." in path.parts:
        raise RuntimeError(f"unsafe log path: {rel}")
    resolved = (root / path).resolve()
    if root.resolve() not in resolved.parents and resolved != root.resolve():
        raise RuntimeError(f"log path escapes repository: {rel}")
    return resolved


def _validate_timestamp(result: ValidationResult, value: str, *, field: str) -> None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        result.fail(f"invalid timestamp {field}: {value!r}")
        return
    if parsed > datetime.now(UTC) + timedelta(seconds=60):
        result.fail(f"future timestamp {field}: {value}")


def _command_results(payload: dict[str, Any]) -> list[dict[str, Any]]:
    raw = payload.get("results", payload.get("command_results", []))
    if not isinstance(raw, list):
        raise RuntimeError("command results must be a list")
    return [item for item in raw if isinstance(item, dict)]


def _validate_result_rows(
    result: ValidationResult,
    *,
    root: Path,
    commit: str,
    payload: dict[str, Any],
) -> None:
    for row in _command_results(payload):
        row_id = str(row.get("id", "<missing-id>"))
        if row.get("evidence_version") != EVIDENCE_VERSION:
            result.fail(f"{row_id}: unsupported evidence version")
        if row.get("git_commit") != commit:
            result.fail(f"{row_id}: evidence commit mismatch")
        status = row.get("status")
        required = bool(row.get("required"))
        if status not in {"PASS", "FAIL", "SKIPPED"}:
            result.fail(f"{row_id}: invalid status {status!r}")
        if required and status != "PASS":
            result.fail(f"{row_id}: required command did not PASS")
        if status == "SKIPPED" and required:
            result.fail(f"{row_id}: required command was SKIPPED")
        if status == "SKIPPED" and not row.get("skip_reason"):
            result.fail(f"{row_id}: optional SKIPPED missing skip_reason")
        for field in ("started_at", "completed_at"):
            value = row.get(field)
            if not isinstance(value, str):
                result.fail(f"{row_id}: missing {field}")
            else:
                _validate_timestamp(result, value, field=f"{row_id}.{field}")
        log_path = row.get("log_path")
        if not isinstance(log_path, str) or not log_path:
            result.fail(f"{row_id}: missing log_path")
            continue
        try:
            path = _safe_log_path(root, log_path)
            require_file(path)
            ensure_no_secrets(path.read_text(encoding="utf-8"), context=str(path))
        except Exception as exc:  # noqa: BLE001 - validator reports all as reasons
            result.fail(f"{row_id}: {exc}")


def _validate_runtime(result: ValidationResult, runtime: dict[str, Any], *, commit: str) -> None:
    if runtime.get("evidence_version") != EVIDENCE_VERSION:
        result.fail("runtime smoke evidence has unsupported evidence_version")
    if runtime.get("git_commit") != commit:
        result.fail("runtime smoke evidence commit mismatch")
    if runtime.get("final_status") != "PASS":
        result.fail("runtime smoke did not PASS")
    required_truths = {
        "kafka_ack_verified": "missing Kafka acknowledgement",
        "snapshot_verified": "missing Iceberg snapshot verification",
        "row_verified": "missing row verification",
        "decimal_verified": "missing Decimal verification",
        "offset_after_durability_verified": "offset-after-durability invariant missing",
    }
    for key, reason in required_truths.items():
        if runtime.get(key) is not True:
            result.fail(reason)
    timestamps = runtime.get("operation_timestamps", {})
    if not isinstance(timestamps, dict):
        result.fail("runtime operation_timestamps missing")
        return
    for key in (
        "kafka_publish_acknowledged_at",
        "iceberg_append_started_at",
        "iceberg_snapshot_committed_at",
        "row_verified_at",
        "kafka_offset_committed_at",
    ):
        value = timestamps.get(key)
        if not isinstance(value, str):
            result.fail(f"runtime timestamp missing: {key}")
        else:
            _validate_timestamp(result, value, field=f"runtime.{key}")
    snapshot_at = timestamps.get("iceberg_snapshot_committed_at")
    offset_at = timestamps.get("kafka_offset_committed_at")
    if isinstance(snapshot_at, str) and isinstance(offset_at, str):
        try:
            snapshot_dt = datetime.fromisoformat(snapshot_at.replace("Z", "+00:00"))
            offset_dt = datetime.fromisoformat(offset_at.replace("Z", "+00:00"))
        except ValueError:
            return
        if snapshot_dt > offset_dt:
            result.fail("Kafka offset commit occurred before Iceberg snapshot durability")


def validate_evidence(
    root: Path,
    *,
    validate_release: bool = False,
    require_release_evidence: bool = True,
    expected_commit: str | None = None,
) -> ValidationResult:
    result = ValidationResult()
    _, head_commit = git_meta(root)
    commit = expected_commit or _expected_validation_commit(root, head_commit=head_commit)
    evidence = root / "artifacts" / "sprint3" / "evidence"
    if not evidence.is_dir():
        result.fail("missing artifacts/sprint3/evidence")
        return result

    required_names = list(REQUIRED_EVIDENCE)
    if not require_release_evidence:
        required_names.remove("release.json")
    for name in required_names:
        path = evidence / name
        try:
            require_file(path)
            text = path.read_text(encoding="utf-8")
            ensure_no_secrets(text, context=str(path))
            payload = json.loads(text)
            if not isinstance(payload, dict):
                result.fail(f"{name}: JSON root is not object")
                continue
            if name != "runtime-smoke.json":
                if payload.get("evidence_version") != EVIDENCE_VERSION:
                    result.fail(f"{name}: unsupported evidence_version")
                _validate_result_rows(result, root=root, commit=commit, payload=payload)
            else:
                _validate_runtime(result, payload, commit=commit)
                _validate_result_rows(result, root=root, commit=commit, payload=payload)
        except json.JSONDecodeError:
            result.fail(f"{name}: invalid JSON")
        except Exception as exc:  # noqa: BLE001
            result.fail(f"{name}: {exc}")

    if validate_release:
        _validate_release(root, result, commit=commit)
    return result


def _expected_validation_commit(root: Path, *, head_commit: str) -> str:
    manifest_path = root / "releases" / "sprint-3" / "MANIFEST.json"
    if not manifest_path.is_file():
        return head_commit
    try:
        manifest = read_json(manifest_path)
    except Exception:  # noqa: BLE001
        return head_commit
    validated_source_commit = manifest.get("validated_source_commit")
    if isinstance(validated_source_commit, str):
        return validated_source_commit
    return head_commit


def _validate_release(root: Path, result: ValidationResult, *, commit: str) -> None:
    release_dir = root / "releases" / "sprint-3"
    if not release_dir.is_dir():
        result.fail("missing releases/sprint-3")
        return
    for name in RELEASE_FILES:
        try:
            require_file(release_dir / name)
            ensure_no_secrets((release_dir / name).read_text(encoding="utf-8"), context=name)
        except Exception as exc:  # noqa: BLE001
            result.fail(f"release {name}: {exc}")
    try:
        verify_checksums(root, release_dir)
    except Exception as exc:  # noqa: BLE001
        result.fail(f"release checksum validation failed: {exc}")
    try:
        manifest = read_json(release_dir / "MANIFEST.json")
    except Exception as exc:  # noqa: BLE001
        result.fail(f"release manifest invalid: {exc}")
        return
    if manifest.get("release_version") != RELEASE_VERSION:
        result.fail("release manifest version mismatch")
    if "source_branch" in manifest:
        result.fail("release manifest must not contain source_branch")
    if "release_commit" in manifest and manifest.get("release_commit") is not None:
        result.fail("release manifest must not contain release_commit")
    if manifest.get("validated_source_commit") != commit:
        result.fail("release manifest validated_source_commit mismatch")
    if manifest.get("gate_decision") != GO_DECISION:
        result.fail("release manifest does not record GO decision")
    approved_paths = manifest.get("approved_release_paths")
    if set(approved_paths or []) != set(APPROVED_SPRINT3_RELEASE_PATHS):
        result.fail("release manifest approved release paths mismatch")
    if manifest.get("sbom", {}).get("format") != "spdx-json":
        result.fail("release manifest missing SPDX SBOM metadata")
    try:
        sbom = read_json(release_dir / "sbom.spdx.json")
        if "SPDXID" not in sbom or "packages" not in sbom:
            result.fail("SBOM is not valid-looking SPDX JSON")
    except Exception as exc:  # noqa: BLE001
        result.fail(f"SBOM invalid: {exc}")
    hashes = release_file_hashes(root, release_dir)
    manifest_hashes = manifest.get("files", {})
    if not isinstance(manifest_hashes, dict):
        result.fail("release manifest files field invalid")
    else:
        for rel, digest in hashes.items():
            if rel.endswith("/MANIFEST.json"):
                continue
            if manifest_hashes.get(rel) != digest:
                result.fail(f"manifest checksum mismatch for {rel}")


def write_validation_output(root: Path, validation: ValidationResult, *, release: bool) -> Path:
    out = root / "artifacts" / "sprint3" / "evidence" / "checksums.json"
    write_json(
        out,
        {
            "evidence_version": EVIDENCE_VERSION,
            "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "status": validation.status,
            "reasons": validation.reasons,
            "validated_release": release,
            "evidence_paths": all_evidence_files(root),
        },
    )
    return out


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Sprint 3 gate evidence")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--release", action="store_true", help="also validate releases/sprint-3")
    args = parser.parse_args(list(argv) if argv is not None else None)
    root = args.root.resolve()
    validation = validate_evidence(root, validate_release=args.release)
    write_validation_output(root, validation, release=args.release)
    print(validation.status)
    if validation.status != "PASS":
        for reason in validation.reasons:
            print(f"- {reason}")
        print(NO_GO_DECISION)
        return 1
    print(GO_DECISION)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
