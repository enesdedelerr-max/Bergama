#!/usr/bin/env bash
# Issue #197 — create deterministic backup of Sprint 1 foundation artifacts.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
EVIDENCE_DIR="${ROOT}/infra/evidence/sprint1"
BACKUP_DIR="${EVIDENCE_DIR}/backups"
STAMP="sprint1-foundation"
OUT_TAR="${BACKUP_DIR}/${STAMP}.tar.gz"
OUT_SHA="${BACKUP_DIR}/${STAMP}.tar.gz.sha256"
REPORT="${EVIDENCE_DIR}/backup.json"

mkdir -p "${BACKUP_DIR}"

fail() {
  echo "backup FAIL: $*" >&2
  exit 1
}

INCLUDE=(
  infra/locks
  infra/secrets
  infra/helm
  infra/gitops
  infra/scripts
  Makefile
)

for item in "${INCLUDE[@]}"; do
  [[ -e "${ROOT}/${item}" ]] || fail "missing backup source ${item}"
done

tar -C "${ROOT}" -czf "${OUT_TAR}" "${INCLUDE[@]}"
(
  cd "${BACKUP_DIR}"
  shasum -a 256 "$(basename "${OUT_TAR}")" >"$(basename "${OUT_SHA}")"
)

SIZE="$(wc -c <"${OUT_TAR}" | tr -d ' ')"
SHA="$(awk '{print $1}' "${OUT_SHA}")"

python3 - <<PY
import json, pathlib
report = {
  "check": "backup",
  "status": "pass",
  "archive": "infra/evidence/sprint1/backups/${STAMP}.tar.gz",
  "sha256": "${SHA}",
  "bytes": int("${SIZE}"),
  "includes": $(printf '%s\n' "${INCLUDE[@]}" | python3 -c 'import json,sys; print(json.dumps([l.strip() for l in sys.stdin if l.strip()]))'),
}
pathlib.Path("${REPORT}").write_text(json.dumps(report, indent=2) + "\n")
print("backup PASS")
print(f"archive: ${OUT_TAR}")
print(f"sha256: ${SHA}")
print(f"evidence: ${REPORT}")
PY
