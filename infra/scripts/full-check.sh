#!/usr/bin/env bash
# Aggregate static checks for Sprint 1 package layout.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REPORT="${ROOT}/artifacts/sprint1/evidence/full-check.json"
PATH="${HOME}/.local/bin:${PATH}"
mkdir -p "$(dirname "${REPORT}")"

fail() { echo "full-check FAIL: $*" >&2; exit 1; }

command -v helm >/dev/null || fail "helm not found"
command -v python3 >/dev/null || fail "python3 not found"

REQUIRED=(
  infra/locks/component-matrix.yaml
  infra/locks/helm-versions.yaml
  infra/locks/images.lock
  infra/locks/python.lock
  infra/locks/node.lock
  infra/locks/scripts/verify-locks.sh
  infra/secrets/templates/local-secret.yaml
  infra/secrets/templates/external-secret.yaml
  infra/secrets/policies/naming.md
  infra/secrets/policies/rotation.md
  infra/secrets/scripts/validate-secrets.sh
  scripts/backup.sh
  scripts/restore-smoke.sh
  scripts/platform-validate.sh
  scripts/build-release.sh
  scripts/gates/gate-sprint1.sh
  infra/helm/platform-foundation/Chart.yaml
  backup/README.md
)
for rel in "${REQUIRED[@]}"; do
  [[ -e "${ROOT}/${rel}" ]] || fail "missing ${rel}"
done

while IFS= read -r script; do
  bash -n "${script}" || fail "bash -n failed for ${script}"
done < <(find "${ROOT}/infra/locks/scripts" "${ROOT}/infra/secrets/scripts" "${ROOT}/scripts" -type f -name '*.sh')

python3 - <<PY
import json, pathlib
path = pathlib.Path("${REPORT}")
path.write_text(json.dumps({"check": "full-check", "status": "pass"}, indent=2) + "\n")
print("full-check PASS")
PY
