"""Build Sprint 2 release package, checksums, and runtime validation scaffolding."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "scripts" / "gates") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts" / "gates"))

from sprint2_common import (  # noqa: E402
    RELEASE_VERSION,
    ensure_no_secrets,
    git_meta,
    sha256_file,
    utc_now,
    write_json,
)

OUT = ROOT / "releases" / "sprint-2"

CHECKSUM_TARGETS = (
    "reports/sprint2-runtime-validation.json",
    "releases/sprint-2/release-notes.md",
    "releases/sprint-2/known-issues.md",
    "releases/sprint-2/risk-summary.md",
    "releases/sprint-2/rollback-notes.md",
    "releases/sprint-2/artifact-manifest.yaml",
    "releases/sprint-2/versions.json",
    "artifacts/sprint2/evidence/openapi.json",
    "artifacts/sprint2/gate-summary.json",
    "artifacts/sprint2/gate-summary.txt",
)


def _write_docs(branch: str, commit: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "release-notes.md").write_text(
        f"""# Sprint 2 Release Notes

Release: `{RELEASE_VERSION}`
Branch: `{branch}`
Commit: `{commit}`
Generated: `{utc_now()}`

## Delivered runtime capabilities

- FastAPI runtime bootstrap and typed configuration
- Structured logging with request/correlation identifiers
- Typed secret boundary (`BERGAMA_SECRETS__*`)
- Local/test JWT bootstrap (HS256); production OIDC not included
- Explicit `AppContainer` dependency ownership
- Liveness / readiness / startup health probes
- Kafka core event runtime (aiokafka) with manual commits
- Broker-free Kafka test runtime (#208B)
- Local YAML/JSON registry loader (#209)
- Sprint 2 fail-closed gate and runtime smoke evidence

## Explicitly not certified

- Production trading readiness
- Market-data connectors / Iceberg
- Persistent Kafka DLQ or retry topics
- Production OIDC
- Application PostgreSQL/Redis clients
- Trading Engine Foundation (#211) — excluded from this gate
""",
        encoding="utf-8",
    )
    (OUT / "known-issues.md").write_text(
        """# Sprint 2 Known Issues

- Production OIDC is not implemented; JWT bootstrap is local/test only.
- Live Kafka broker smoke may be unverified (`make smoke-api-kafka` SKIPPED by default).
- No persistent retry topics or production DLQ adapter.
- No application PostgreSQL/Redis client runtime yet.
- Registry Loader is local-file and read-only.
- Stacked Sprint 2 PRs must merge in order (#208A → #208B → #209 → #210).
- Kafka in-memory test runtime does not emulate full consumer-group rebalance semantics.
- Trading Engine Foundation (#211) is out of scope for this gate.
""",
        encoding="utf-8",
    )
    (OUT / "risk-summary.md").write_text(
        """# Sprint 2 Risk Summary

| Risk | Mitigation |
|------|------------|
| Live Kafka unverified | Broker-free #208A/#208B tests required; live smoke optional |
| Local JWT bootstrap misuse | Disabled in staging/production via settings invariants |
| Registry misconfiguration | Fail-closed startup when required registries missing/invalid |
| Stacked PR divergence | Gate runs on #209 tip; #211 excluded |
| Evidence secret leakage | Pattern checks on logs and artifacts |
""",
        encoding="utf-8",
    )
    (OUT / "rollback-notes.md").write_text(
        f"""# Sprint 2 Rollback Notes

## Software rollback

1. Revert the Sprint 2 gate/release commit(s) if only packaging changed.
2. To roll back runtime features, revert stacked PRs in reverse order (#210 → #209 → #208B → #208A …).
3. Redeploy previous known-good API image/tag if deployed.

## Data / ops

- No production trading state is written by Sprint 2 runtime foundation.
- Registry files are read-only; no registry writes to roll back.
- Kafka offsets for optional live smoke should be treated as ephemeral test groups.

## Tag

Do not delete `{RELEASE_VERSION}` if already published without an explicit ops decision.
""",
        encoding="utf-8",
    )
    artifacts = [
        "release-notes.md",
        "known-issues.md",
        "risk-summary.md",
        "rollback-notes.md",
        "artifact-manifest.yaml",
        "versions.json",
        "checksums.txt",
    ]
    (OUT / "artifact-manifest.yaml").write_text(
        f"release: {RELEASE_VERSION}\nartifacts:\n"
        + "".join(f"  - {name}\n" for name in artifacts),
        encoding="utf-8",
    )
    write_json(
        OUT / "versions.json",
        {
            "release": RELEASE_VERSION,
            "generated_at": utc_now(),
            "git": {"branch": branch, "commit": commit},
            "python_requires": ">=3.13",
            "api_package": "bergama-api",
        },
    )


def _ensure_stub_reports_if_missing() -> None:
    """Allow release packaging during isolated make build before full gate."""
    report = ROOT / "reports" / "sprint2-runtime-validation.json"
    if not report.exists():
        write_json(
            report,
            {
                "gate_id": "sprint2-runtime-gate",
                "sprint": "2",
                "overall_status": "PENDING",
                "message": "placeholder until gate-sprint2 completes",
            },
        )
    summary_json = ROOT / "artifacts" / "sprint2" / "gate-summary.json"
    summary_txt = ROOT / "artifacts" / "sprint2" / "gate-summary.txt"
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    if not summary_json.exists():
        write_json(
            summary_json,
            {
                "gate_id": "sprint2-runtime-gate",
                "overall_status": "PENDING",
                "final_decision": "NO-GO FOR SPRINT 3",
            },
        )
    if not summary_txt.exists():
        summary_txt.write_text("overall_status=PENDING\n", encoding="utf-8")
    openapi = ROOT / "artifacts" / "sprint2" / "evidence" / "openapi.json"
    if not openapi.exists():
        # Require openapi evidence from validate-api-openapi in full gate.
        # For isolated build, generate quickly.
        subprocess.run(
            ["python3", str(ROOT / "scripts" / "gates" / "validate_api_openapi.py")],
            cwd=ROOT,
            check=True,
        )


def write_checksums(*, root: Path | None = None) -> Path:
    base = root or ROOT
    out_dir = base / "releases" / "sprint-2"
    out_dir.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    for rel in CHECKSUM_TARGETS:
        path = base / rel
        if not path.is_file() or path.stat().st_size == 0:
            msg = f"missing/empty checksum target: {rel}"
            raise FileNotFoundError(msg)
        text = path.read_text(encoding="utf-8", errors="replace")
        ensure_no_secrets(text, context=rel)
        digest = sha256_file(path)
        lines.append(f"{digest}  {rel}")
    out = out_dir / "checksums.txt"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def verify_checksums(*, root: Path | None = None) -> None:
    base = root or ROOT
    checksums = base / "releases" / "sprint-2" / "checksums.txt"
    for line in checksums.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, _, rel = line.partition("  ")
        path = base / rel.strip()
        actual = sha256_file(path)
        if actual != digest.strip():
            msg = f"checksum mismatch for {rel}"
            raise RuntimeError(msg)


def main() -> int:
    branch, commit = git_meta(ROOT)
    _ensure_stub_reports_if_missing()
    _write_docs(branch, commit)
    write_checksums(root=ROOT)
    verify_checksums(root=ROOT)
    print(f"build-sprint2-release PASS -> {OUT}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"build-sprint2-release FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
