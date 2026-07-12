#!/usr/bin/env bash
# Issue #199 — Sprint 1 gate orchestration and evidence package.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
EVIDENCE_DIR="${ROOT}/infra/evidence/sprint1"
GATE_JSON="${EVIDENCE_DIR}/GATE_RESULT.json"
GATE_MD="${EVIDENCE_DIR}/GATE_RESULT.md"
RELEASE_VERSION="$(awk '/^release_version:/{gsub(/"/,"",$2); print $2; exit}' "${ROOT}/infra/locks/versions.lock.yaml")"
PATH="${HOME}/.local/bin:${PATH}"
export PATH ROOT RELEASE_VERSION

cd "${ROOT}"

run() {
  local target="$1"
  echo "==> make ${target}"
  make "${target}"
}

run helm-lint
run helm-template
run full-check
run verify-locks
run validate-secrets
run backup
run restore-smoke
run platform-validate
run build-release

# Require release artifacts
ARCHIVE="${ROOT}/releases/${RELEASE_VERSION}/bergama-${RELEASE_VERSION}.tar.gz"
SBOM="${ROOT}/releases/${RELEASE_VERSION}/bergama-${RELEASE_VERSION}.sbom.json"
[[ -f "${ARCHIVE}" ]] || { echo "gate-sprint1 FAIL: missing release archive" >&2; exit 1; }
[[ -f "${ARCHIVE}.sha256" ]] || { echo "gate-sprint1 FAIL: missing archive checksum" >&2; exit 1; }
[[ -f "${SBOM}" ]] || { echo "gate-sprint1 FAIL: missing SBOM" >&2; exit 1; }
[[ -f "${SBOM}.sha256" ]] || { echo "gate-sprint1 FAIL: missing SBOM checksum" >&2; exit 1; }
[[ -f "${EVIDENCE_DIR}/PLATFORM_VALIDATION.json" ]] || { echo "gate-sprint1 FAIL: missing platform validation" >&2; exit 1; }

# Create annotated tag if missing (local only; push is out of scope)
if git rev-parse "${RELEASE_VERSION}" >/dev/null 2>&1; then
  echo "tag ${RELEASE_VERSION} already exists"
else
  # Require a clean-enough tree for tag; allow evidence/release untracked by adding them first if needed
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git tag -a "${RELEASE_VERSION}" -m "Sprint 1 foundation gate ${RELEASE_VERSION}" || {
      echo "gate-sprint1 FAIL: unable to create tag ${RELEASE_VERSION} (commit Sprint 1 work first)" >&2
      exit 1
    }
  fi
fi

python3 - <<'PY'
import json, pathlib, datetime, subprocess, os

root = pathlib.Path(os.environ["ROOT"])
evidence = root / "infra" / "evidence" / "sprint1"
release = os.environ["RELEASE_VERSION"]

def read_json(name):
    return json.loads((evidence / name).read_text())

steps = [
    "helm-lint",
    "helm-template",
    "full-check",
    "verify-locks",
    "validate-secrets",
    "backup",
    "restore-smoke",
    "platform-validate",
    "build-release",
]
platform = read_json("PLATFORM_VALIDATION.json")
tag_exists = (
    subprocess.call(
        ["git", "rev-parse", release],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    == 0
)

report = {
    "gate": "sprint1",
    "status": "pass",
    "release_version": release,
    "generated_at": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
    "steps": steps,
    "platform_validation": platform["status"],
    "tag": release if tag_exists else None,
    "artifacts": {
        "archive": f"releases/{release}/bergama-{release}.tar.gz",
        "sbom": f"releases/{release}/bergama-{release}.sbom.json",
        "platform_validation": "infra/evidence/sprint1/PLATFORM_VALIDATION.json",
    },
    "sprint2_decision": "GO",
    "risks": [
        "Live Kind/ArgoCD runtime sync was not executed as part of this gate sequence.",
        "GitOps 'Healthy and Synced' is declared via Application manifest policy, not live controller status.",
    ],
}
(evidence / "GATE_RESULT.json").write_text(json.dumps(report, indent=2) + "\n")
md = [
    "# Sprint 1 Gate Result",
    "",
    "Status: **PASS**",
    "",
    f"Release: `{release}`",
    "",
    "Sprint 2 decision: **GO**",
    "",
    "## Risks",
    "",
]
md.extend(f"- {r}" for r in report["risks"])
md.append("")
(evidence / "GATE_RESULT.md").write_text("\n".join(md))
print("gate-sprint1 PASS")
print(f"evidence: {evidence / 'GATE_RESULT.json'}")
print("Sprint 2 decision: GO")
PY
