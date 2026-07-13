#!/usr/bin/env bash
# Shared helpers for Sprint 1 local platform bootstrap.
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CLUSTER_NAME="${KIND_CLUSTER_NAME:-bergama-sprint1}"
ARGOCD_NS="${ARGOCD_NAMESPACE:-argocd}"
NS="${PLATFORM_NAMESPACE:-platform}"
PATH="${HOME}/.local/bin:${PATH}"
export PATH ROOT CLUSTER_NAME NS ARGOCD_NS ARGOCD_NAMESPACE="${ARGOCD_NS}"

log() { echo "[bootstrap] $*"; }
fail() { log "FAIL: $*"; exit 1; }

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "$1 is required"
}

ensure_tools() {
  require_cmd kind
  require_cmd kubectl
  require_cmd helm
}

context_name() {
  echo "kind-${CLUSTER_NAME}"
}

use_context() {
  kubectl config use-context "$(context_name)" >/dev/null 2>&1 || fail "kubectl context kind-${CLUSTER_NAME} not found; run make kind-bootstrap"
}

wait_rollout() {
  local ns="$1"
  local selector="$2"
  local timeout="${3:-300s}"
  kubectl rollout status -n "${ns}" "${selector}" --timeout="${timeout}" || fail "rollout failed: ${ns}/${selector}"
}

wait_pods_ready() {
  local ns="$1"
  local label="$2"
  local timeout="${3:-300}"
  local end=$((SECONDS + timeout))
  while (( SECONDS < end )); do
    local ready total
    ready="$(kubectl get pods -n "${ns}" -l "${label}" -o jsonpath='{range .items[*]}{.status.conditions[?(@.type=="Ready")].status}{"\n"}{end}' 2>/dev/null | grep -c True || true)"
    total="$(kubectl get pods -n "${ns}" -l "${label}" --no-headers 2>/dev/null | wc -l | tr -d ' ')"
    if [[ "${total}" -gt 0 && "${ready}" -eq "${total}" ]]; then
      return 0
    fi
    sleep 5
  done
  kubectl get pods -n "${ns}" -l "${label}" -o wide || true
  fail "pods not ready for ${label} in ${ns}"
}

image_ref() {
  local key="$1"
  python3 - <<PY
import json, pathlib, os
root = pathlib.Path(os.environ["ROOT"])
data = json.loads((root / "infra/locks/images.lock").read_text())
img = data["images"]["${key}"]
print(f"{img['repository']}@{img['digest']}")
PY
}

apply_manifest() {
  local file="$1"
  [[ -f "${file}" ]] || fail "missing manifest ${file}"
  kubectl apply -f "${file}"
}
