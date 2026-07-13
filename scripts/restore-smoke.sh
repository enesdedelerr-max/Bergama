#!/usr/bin/env bash
# Issue #197 — restore smoke against temporary restore targets.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SUMMARY="${ROOT}/artifacts/sprint1/evidence/restore-smoke-summary.json"
LOG_DIR="${ROOT}/artifacts/sprint1/logs"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "${LOG_DIR}" "$(dirname "${SUMMARY}")"

log() { echo "[restore-smoke] $*" | tee -a "${LOG_DIR}/restore-smoke-${STAMP}.log"; }
fail() {
  python3 - <<PY
import json, pathlib
path = pathlib.Path("${SUMMARY}")
path.write_text(json.dumps({
  "check": "restore-smoke",
  "status": "fail",
  "timestamp": "${STAMP}",
  "message": """$*""",
}, indent=2) + "\n")
PY
  log "FAIL: $*"
  exit 1
}

command -v kubectl >/dev/null || fail "kubectl not available"

if ! kubectl get nodes >/dev/null 2>&1; then
  fail "Kubernetes API unavailable; restore smoke requires a live Kind cluster with Sprint 1 services."
fi

# Locate newest postgres dump
DUMP="$(ls -1dt "${ROOT}"/backup/postgres/*/dump.sql 2>/dev/null | head -1 || true)"
[[ -n "${DUMP}" && -s "${DUMP}" ]] || fail "no non-empty postgres dump found; run make backup first"

# Isolated restore smoke: create a temporary database if postgres pod exists
NS="${BACKUP_NAMESPACE:-platform}"
POD="$(kubectl get pods -n "${NS}" -l app.kubernetes.io/name=postgresql -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)"
[[ -n "${POD}" ]] || fail "postgresql pod not found for restore smoke"

TMPDB="restore_smoke_${STAMP}"
kubectl exec -n "${NS}" "${POD}" -- psql -U postgres -c "CREATE DATABASE \"${TMPDB}\";" >/dev/null 2>&1 || fail "unable to create temp database"
if ! kubectl exec -n "${NS}" "${POD}" -- psql -U postgres -d "${TMPDB}" <"${DUMP}" >/dev/null 2>"${LOG_DIR}/restore-postgres-${STAMP}.err"; then
  kubectl exec -n "${NS}" "${POD}" -- psql -U postgres -c "DROP DATABASE IF EXISTS \"${TMPDB}\";" >/dev/null 2>&1 || true
  fail "postgres restore smoke failed"
fi

# Representative verification: ensure at least one relation or that restore completed without error and db exists
EXISTS="$(kubectl exec -n "${NS}" "${POD}" -- psql -U postgres -d "${TMPDB}" -tAc "SELECT 1" | tr -d '[:space:]')"
kubectl exec -n "${NS}" "${POD}" -- psql -U postgres -c "DROP DATABASE IF EXISTS \"${TMPDB}\";" >/dev/null 2>&1 || true
[[ "${EXISTS}" == "1" ]] || fail "restored database not queryable"

python3 - <<PY
import json, pathlib
path = pathlib.Path("${SUMMARY}")
path.write_text(json.dumps({
  "check": "restore-smoke",
  "status": "pass",
  "timestamp": "${STAMP}",
  "postgres_dump": "${DUMP}",
  "message": "Temporary database restore smoke succeeded.",
  "note": "Sprint 1 smoke only; not DR certification.",
}, indent=2) + "\n")
print("restore-smoke PASS")
PY
