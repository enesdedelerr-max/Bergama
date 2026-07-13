#!/usr/bin/env bash
# Issue #197 — backup orchestration against local Kubernetes services.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT_ROOT="${ROOT}/backup"
SUMMARY="${ROOT}/artifacts/sprint1/evidence/backup-summary.json"
LOG_DIR="${ROOT}/artifacts/sprint1/logs"
export ROOT STAMP OUT_ROOT
mkdir -p "${LOG_DIR}" "${OUT_ROOT}"/{postgres,redis,clickhouse,minio}

log() { echo "[backup] $*" | tee -a "${LOG_DIR}/backup-${STAMP}.log"; }
fail() { log "FAIL: $*"; exit 1; }

command -v kubectl >/dev/null || fail "kubectl not available"
command -v jq >/dev/null || fail "jq not available"

if ! kubectl get nodes >/dev/null 2>&1; then
  fail "Kubernetes API unavailable (no Kind/cluster context). Cannot perform live service backups."
fi

NS="${BACKUP_NAMESPACE:-platform}"
mkdir -p "${OUT_ROOT}/postgres/${STAMP}" "${OUT_ROOT}/redis/${STAMP}" \
  "${OUT_ROOT}/clickhouse/${STAMP}" "${OUT_ROOT}/minio/${STAMP}"

RESULTS=()

backup_postgres() {
  local pod
  pod="$(kubectl get pods -n "${NS}" -l app.kubernetes.io/name=postgresql -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)"
  [[ -n "${pod}" ]] || { RESULTS+=("postgres:FAIL:no-pod"); return 1; }
  kubectl exec -n "${NS}" "${pod}" -- pg_dump -U postgres -d postgres >"${OUT_ROOT}/postgres/${STAMP}/dump.sql" 2>"${LOG_DIR}/postgres-${STAMP}.err" || {
    RESULTS+=("postgres:FAIL:pg_dump"); return 1;
  }
  [[ -s "${OUT_ROOT}/postgres/${STAMP}/dump.sql" ]] || { RESULTS+=("postgres:FAIL:empty-dump"); return 1; }
  RESULTS+=("postgres:PASS")
}

backup_redis() {
  local pod
  pod="$(kubectl get pods -n "${NS}" -l app.kubernetes.io/name=redis -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)"
  [[ -n "${pod}" ]] || { RESULTS+=("redis:FAIL:no-pod"); return 1; }
  kubectl exec -n "${NS}" "${pod}" -- redis-cli BGSAVE >/dev/null 2>"${LOG_DIR}/redis-${STAMP}.err" || true
  kubectl exec -n "${NS}" "${pod}" -- sh -c 'cat /data/dump.rdb 2>/dev/null || cat /data/appendonly.aof 2>/dev/null' \
    >"${OUT_ROOT}/redis/${STAMP}/redis-data.bin" 2>>"${LOG_DIR}/redis-${STAMP}.err" || {
    RESULTS+=("redis:FAIL:artifact"); return 1;
  }
  [[ -s "${OUT_ROOT}/redis/${STAMP}/redis-data.bin" ]] || { RESULTS+=("redis:FAIL:empty-artifact"); return 1; }
  RESULTS+=("redis:PASS")
}

backup_clickhouse() {
  local pod
  pod="$(kubectl get pods -n "${NS}" -l app.kubernetes.io/name=clickhouse -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)"
  [[ -n "${pod}" ]] || { RESULTS+=("clickhouse:FAIL:no-pod"); return 1; }
  kubectl exec -n "${NS}" "${pod}" -- clickhouse-client -q 'SHOW DATABASES' \
    >"${OUT_ROOT}/clickhouse/${STAMP}/databases.txt" 2>"${LOG_DIR}/clickhouse-${STAMP}.err" || {
    RESULTS+=("clickhouse:FAIL:query"); return 1;
  }
  [[ -s "${OUT_ROOT}/clickhouse/${STAMP}/databases.txt" ]] || { RESULTS+=("clickhouse:FAIL:empty"); return 1; }
  RESULTS+=("clickhouse:PASS")
}

backup_minio() {
  local pod
  pod="$(kubectl get pods -n "${NS}" -l app.kubernetes.io/name=minio -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)"
  [[ -n "${pod}" ]] || { RESULTS+=("minio:FAIL:no-pod"); return 1; }
  kubectl exec -n "${NS}" "${pod}" -- sh -c 'mc ls local 2>/dev/null || ls -la /data 2>/dev/null' \
    >"${OUT_ROOT}/minio/${STAMP}/listing.txt" 2>"${LOG_DIR}/minio-${STAMP}.err" || {
    RESULTS+=("minio:FAIL:listing"); return 1;
  }
  [[ -s "${OUT_ROOT}/minio/${STAMP}/listing.txt" ]] || { RESULTS+=("minio:FAIL:empty"); return 1; }
  RESULTS+=("minio:PASS")
}

rc=0
backup_postgres || rc=1
backup_redis || rc=1
backup_clickhouse || rc=1
backup_minio || rc=1

python3 - <<PY
import json, os, pathlib
results = """${RESULTS[*]}""".split()
parsed = []
status = "pass"
for item in results:
    parts = item.split(":", 2)
    entry = {"service": parts[0], "status": parts[1], "message": parts[2] if len(parts) > 2 else ""}
    if entry["status"] != "PASS":
        status = "fail"
    parsed.append(entry)
report = {
  "check": "backup",
  "status": status,
  "timestamp": os.environ["STAMP"],
  "namespace": "${NS}",
  "results": parsed,
  "note": "Sprint 1 smoke backup only; not DR certification.",
}
path = pathlib.Path(os.environ["ROOT"]) / "artifacts/sprint1/evidence/backup-summary.json"
path.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
PY

[[ "${rc}" -eq 0 ]] || fail "one or more service backups failed"
log "PASS"
exit 0
