#!/usr/bin/env bash
# Sprint 1 Go/No-Go gate — fail closed, no fabricated evidence.
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ART="${ROOT}/artifacts/sprint1"
LOG="${ART}/logs"
EVD="${ART}/evidence"
PATH="${HOME}/.local/bin:${PATH}"
export PATH ROOT ARGOCD_NAMESPACE="${ARGOCD_NAMESPACE:-argocd}"
mkdir -p "${LOG}" "${EVD}"

SUMMARY_TXT="${ART}/gate-summary.txt"
SUMMARY_JSON="${ART}/gate-summary.json"
TAG="v0.1.0-sprint1"

ts() { date -u +%Y-%m-%dT%H:%M:%SZ; }
log() { echo "[$(ts)] $*" | tee -a "${LOG}/gate-sprint1.log"; }

run_step() {
  local name="$1"
  shift
  log "BEGIN ${name}"
  if "$@" >"${LOG}/${name}.out" 2>"${LOG}/${name}.err"; then
    log "PASS ${name}"
    echo "${name}=PASS" >>"${SUMMARY_TXT}"
  else
    local rc=$?
    log "FAIL ${name} (exit ${rc})"
    echo "${name}=FAIL" >>"${SUMMARY_TXT}"
    {
      echo "----- ${name} stdout -----"
      cat "${LOG}/${name}.out" || true
      echo "----- ${name} stderr -----"
      cat "${LOG}/${name}.err" || true
    } | tee -a "${LOG}/gate-sprint1.log"
    finalize "fail" "${name}"
    exit "${rc}"
  fi
}

collect_k8s_evidence() {
  mkdir -p "${EVD}/kubectl" "${EVD}/argocd"
  kubectl get pods -A >"${EVD}/kubectl-pods-all.txt" 2>"${EVD}/kubectl-pods-all.err" || true
  kubectl get pvc -A >"${EVD}/kubectl-pvc-all.txt" 2>"${EVD}/kubectl-pvc-all.err" || true
  kubectl get ingress -A >"${EVD}/kubectl-ingress-all.txt" 2>"${EVD}/kubectl-ingress-all.err" || true
  kubectl get storageclass >"${EVD}/kubectl-storageclass.txt" 2>"${EVD}/kubectl-storageclass.err" || true
  # Legacy paths retained for prior consumers.
  cp -f "${EVD}/kubectl-pods-all.txt" "${EVD}/kubectl/pods.txt" 2>/dev/null || true
  cp -f "${EVD}/kubectl-pvc-all.txt" "${EVD}/kubectl/pvc.txt" 2>/dev/null || true
  cp -f "${EVD}/kubectl-ingress-all.txt" "${EVD}/kubectl/ingress.txt" 2>/dev/null || true
  cp -f "${EVD}/kubectl-storageclass.txt" "${EVD}/kubectl/storageclass.txt" 2>/dev/null || true
  if command -v argocd >/dev/null 2>&1; then
    ARGOCD_NAMESPACE="${ARGOCD_NAMESPACE:-argocd}" argocd app list >"${EVD}/argocd-app-list.txt" 2>"${EVD}/argocd-app-list.err" || true
    ARGOCD_NAMESPACE="${ARGOCD_NAMESPACE:-argocd}" argocd app get platform-foundation >"${EVD}/argocd-app-platform.txt" 2>"${EVD}/argocd-app-platform.err" || true
  fi
  if [[ ! -s "${EVD}/argocd-app-list.txt" ]]; then
    kubectl get applications.argoproj.io -n "${ARGOCD_NAMESPACE:-argocd}" -o wide >"${EVD}/argocd-app-list.txt" 2>"${EVD}/argocd-app-list.err" || true
    kubectl get application -n "${ARGOCD_NAMESPACE:-argocd}" platform-foundation -o yaml >"${EVD}/argocd-app-platform.txt" 2>"${EVD}/argocd-app-platform.err" || true
  fi
}

require_artifact() {
  local path="$1"
  [[ -s "${ROOT}/${path}" ]] || { log "missing/empty artifact: ${path}"; return 1; }
}

finalize() {
  local status="$1"
  local failed_step="${2:-}"
  collect_k8s_evidence
  python3 - <<PY
import json, pathlib, os, subprocess
root = pathlib.Path(os.environ["ROOT"])
art = root / "artifacts/sprint1"
status = "${status}"
failed_step = "${failed_step}"
tag = "${TAG}"
tag_exists = subprocess.call(["git", "rev-parse", tag], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0
decision = "GO" if status == "pass" and tag_exists else "NO-GO"
report = {
  "gate": "sprint1",
  "status": status,
  "failed_step": failed_step or None,
  "tag": tag if tag_exists else None,
  "tag_created": tag_exists,
  "sprint2_decision": decision,
}
(art / "gate-summary.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
PY
  log "FINAL status=${status} decision=$(python3 -c 'import json,pathlib; print(json.loads(pathlib.Path("'${SUMMARY_JSON}'").read_text())["sprint2_decision"])')"
}

: >"${SUMMARY_TXT}"
log "Sprint 1 gate starting"

cd "${ROOT}"
run_step helm-lint make helm-lint
run_step helm-template make helm-template
run_step full-check make full-check
run_step verify-locks make verify-locks
run_step validate-secrets make validate-secrets
run_step backup make backup
run_step restore-smoke make restore-smoke
run_step platform-validate make platform-validate
run_step build-release make build-release

# Artifact requirements
require_artifact "reports/platform-validation.json" || { finalize fail artifacts; exit 1; }
require_artifact "releases/sprint-1/checksums.txt" || { finalize fail artifacts; exit 1; }
require_artifact "releases/sprint-1/sbom.spdx.json" || { finalize fail artifacts; exit 1; }

# Create tag only after all checks pass and worktree has no staged-required dirty secrets;
# allow generated artifact dirtiness but require scripts/locks committed ideally.
if git -C "${ROOT}" rev-parse "${TAG}" >/dev/null 2>&1; then
  log "tag ${TAG} already exists"
else
  git -C "${ROOT}" tag -a "${TAG}" -m "Sprint 1 foundation gate ${TAG}"
  log "created local annotated tag ${TAG}"
fi

git -C "${ROOT}" rev-parse "${TAG}" >/dev/null 2>&1 || { log "tag missing after creation attempt"; finalize fail tag; exit 1; }

finalize pass
log "gate-sprint1 PASS"
exit 0
