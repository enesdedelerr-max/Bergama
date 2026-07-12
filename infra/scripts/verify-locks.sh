#!/usr/bin/env bash
# Issue #195 — verify pinned tool/chart/image versions.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOCK="${ROOT}/infra/locks/versions.lock.yaml"
EVIDENCE_DIR="${ROOT}/infra/evidence/sprint1"
REPORT="${EVIDENCE_DIR}/verify-locks.json"
PATH="${HOME}/.local/bin:${PATH}"

mkdir -p "${EVIDENCE_DIR}"

fail() {
  echo "verify-locks FAIL: $*" >&2
  exit 1
}

[[ -f "${LOCK}" ]] || fail "missing ${LOCK}"

extract() {
  local key="$1"
  # shellcheck disable=SC2002
  grep -E "^[[:space:]]*${key}:" "${LOCK}" | head -1 | sed -E 's/^[^:]+:[[:space:]]*"?([^"#]+)"?.*/\1/' | tr -d '[:space:]'
}

HELM_EXPECTED="$(extract version | head -1)"
# More precise extractions values from structured sections
HELM_EXPECTED="$(awk '/^tools:/{p=1} p&&/helm:/{getline; if($1=="version:"){gsub(/"/,"",$2); print $2; exit}}' "${LOCK}")"
CHART_VERSION="$(awk '/platform-foundation:/{p=1} p&&/version:/{gsub(/"/,"",$2); print $2; exit}' "${LOCK}")"
RELEASE_VERSION="$(awk '/^release_version:/{gsub(/"/,"",$2); print $2; exit}' "${LOCK}")"

command -v helm >/dev/null || fail "helm not on PATH"
HELM_ACTUAL="$(helm version --template '{{.Version}}' 2>/dev/null || helm version --short | awk '{print $1}')"
HELM_ACTUAL="${HELM_ACTUAL%%+*}"

[[ "${HELM_ACTUAL}" == "${HELM_EXPECTED}" ]] || fail "helm version mismatch actual=${HELM_ACTUAL} expected=${HELM_EXPECTED}"

CHART_FILE="${ROOT}/infra/helm/platform-foundation/Chart.yaml"
[[ -f "${CHART_FILE}" ]] || fail "missing chart"
CHART_FILE_VERSION="$(awk '/^version:/{print $2; exit}' "${CHART_FILE}")"
[[ "${CHART_FILE_VERSION}" == "${CHART_VERSION}" ]] || fail "chart version mismatch file=${CHART_FILE_VERSION} lock=${CHART_VERSION}"

VALUES="${ROOT}/infra/helm/platform-foundation/values.yaml"
if grep -E '(^|[[:space:]])tag:[[:space:]]*["'\'']?(latest|stable|master|main)["'\'']?' "${VALUES}" >/dev/null; then
  fail "mutable image tag found in values.yaml"
fi

# Ensure every images.*.tag in values is present and non-empty
MISSING_TAGS="$(awk '
  /^images:/{in_images=1; next}
  in_images && /^[^[:space:]]/{in_images=0}
  in_images && /^[[:space:]]+[a-z0-9-]+:/{svc=$1; gsub(":","",svc); name=svc}
  in_images && /tag:/{tag=$2; gsub(/"/,"",tag); if(tag=="" || tag=="null"){print name}}
' "${VALUES}")"
[[ -z "${MISSING_TAGS}" ]] || fail "empty image tags: ${MISSING_TAGS}"

python3 - <<PY
import json, pathlib
report = {
  "check": "verify-locks",
  "status": "pass",
  "release_version": "${RELEASE_VERSION}",
  "helm": {"expected": "${HELM_EXPECTED}", "actual": "${HELM_ACTUAL}"},
  "chart": {"expected": "${CHART_VERSION}", "actual": "${CHART_FILE_VERSION}"},
  "mutable_tags": "none",
}
pathlib.Path("${REPORT}").write_text(json.dumps(report, indent=2) + "\n")
print("verify-locks PASS")
print(f"evidence: ${REPORT}")
PY
