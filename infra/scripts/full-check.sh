#!/usr/bin/env bash
# Aggregate static checks for Sprint 1 foundation package.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
EVIDENCE_DIR="${ROOT}/infra/evidence/sprint1"
REPORT="${EVIDENCE_DIR}/full-check.json"
PATH="${HOME}/.local/bin:${PATH}"

mkdir -p "${EVIDENCE_DIR}"

fail() {
  echo "full-check FAIL: $*" >&2
  exit 1
}

command -v helm >/dev/null || fail "helm not found"
command -v python3 >/dev/null || fail "python3 not found"

# Shell syntax
while IFS= read -r script; do
  bash -n "${script}" || fail "bash -n failed for ${script}"
done < <(find "${ROOT}/infra/scripts" -type f -name '*.sh')

# Required tree
REQUIRED=(
  infra/locks/versions.lock.yaml
  infra/secrets/policy.yaml
  infra/secrets/refs/postgresql-credentials.yaml
  infra/helm/platform-foundation/Chart.yaml
  infra/helm/platform-foundation/values.yaml
  infra/gitops/applications/platform-foundation.yaml
  Makefile
)
for rel in "${REQUIRED[@]}"; do
  [[ -f "${ROOT}/${rel}" ]] || fail "missing ${rel}"
done

# No latest tags in values
grep -E 'tag:[[:space:]]*["'\'']?latest["'\'']?' "${ROOT}/infra/helm/platform-foundation/values.yaml" \
  && fail "latest tag in values" || true

python3 - <<PY
import json, pathlib
report = {"check": "full-check", "status": "pass"}
pathlib.Path(r"${REPORT}").write_text(json.dumps(report, indent=2) + "\n")
print("full-check PASS")
print(f"evidence: ${REPORT}")
PY
