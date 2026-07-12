#!/usr/bin/env bash
# Issue #197 — restore smoke test against the Sprint 1 foundation backup.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
EVIDENCE_DIR="${ROOT}/infra/evidence/sprint1"
BACKUP_DIR="${EVIDENCE_DIR}/backups"
STAMP="sprint1-foundation"
IN_TAR="${BACKUP_DIR}/${STAMP}.tar.gz"
IN_SHA="${BACKUP_DIR}/${STAMP}.sha256"
# Prefer .tar.gz.sha256 naming from backup.sh
[[ -f "${BACKUP_DIR}/${STAMP}.tar.gz.sha256" ]] && IN_SHA="${BACKUP_DIR}/${STAMP}.tar.gz.sha256"
REPORT="${EVIDENCE_DIR}/restore-smoke.json"
RESTORE_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/sprint1-restore.XXXXXX")"

cleanup() {
  rm -rf "${RESTORE_ROOT}"
}
trap cleanup EXIT

fail() {
  echo "restore-smoke FAIL: $*" >&2
  exit 1
}

[[ -f "${IN_TAR}" ]] || fail "missing backup archive; run make backup first"
[[ -f "${IN_SHA}" ]] || fail "missing backup checksum"

EXPECTED_SHA="$(awk '{print $1}' "${IN_SHA}")"
ACTUAL_SHA="$(shasum -a 256 "${IN_TAR}" | awk '{print $1}')"
[[ "${ACTUAL_SHA}" == "${EXPECTED_SHA}" ]] || fail "checksum mismatch"

tar -C "${RESTORE_ROOT}" -xzf "${IN_TAR}"

REQUIRED_RESTORED=(
  "infra/locks/versions.lock.yaml"
  "infra/secrets/policy.yaml"
  "infra/helm/platform-foundation/Chart.yaml"
  "infra/gitops/applications/platform-foundation.yaml"
  "Makefile"
)

for rel in "${REQUIRED_RESTORED[@]}"; do
  [[ -f "${RESTORE_ROOT}/${rel}" ]] || fail "restored tree missing ${rel}"
done

# Content equality smoke for lock file
cmp -s "${ROOT}/infra/locks/versions.lock.yaml" "${RESTORE_ROOT}/infra/locks/versions.lock.yaml" \
  || fail "restored versions.lock.yaml differs from source"

python3 - <<PY
import json, pathlib
report = {
  "check": "restore-smoke",
  "status": "pass",
  "archive": "infra/evidence/sprint1/backups/${STAMP}.tar.gz",
  "sha256_verified": True,
  "restored_required_paths": ${#REQUIRED_RESTORED[@]},
}
pathlib.Path("${REPORT}").write_text(json.dumps(report, indent=2) + "\n")
print("restore-smoke PASS")
print(f"evidence: ${REPORT}")
PY
