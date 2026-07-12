#!/usr/bin/env bash
# Issue #196 — validate secret references and forbid default credentials.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
POLICY="${ROOT}/infra/secrets/policy.yaml"
REFS="${ROOT}/infra/secrets/refs"
EVIDENCE_DIR="${ROOT}/infra/evidence/sprint1"
REPORT="${EVIDENCE_DIR}/validate-secrets.json"

mkdir -p "${EVIDENCE_DIR}"

fail() {
  echo "validate-secrets FAIL: $*" >&2
  exit 1
}

[[ -f "${POLICY}" ]] || fail "missing policy"
[[ -d "${REFS}" ]] || fail "missing refs directory"

REQUIRED=(
  "postgresql-credentials.yaml"
  "redis-credentials.yaml"
  "minio-credentials.yaml"
  "argocd-admin.yaml"
  ".env.example"
)

for f in "${REQUIRED[@]}"; do
  [[ -f "${REFS}/${f}" ]] || fail "missing required secret ref: ${f}"
done

# Every secret manifest must be a reference placeholder, not a literal credential.
while IFS= read -r file; do
  if grep -E 'password:[[:space:]]*["'\'']?(admin|password|changeme|secret|root|123456|postgres)["'\'']?[[:space:]]*$' "${file}" >/dev/null; then
    fail "default credential literal in ${file}"
  fi
  if ! grep -q 'SECRETREF:' "${file}"; then
    fail "missing SECRETREF placeholder in ${file}"
  fi
  if ! grep -q 'bergama.io/secret-ref: "true"' "${file}"; then
    fail "missing secret-ref label in ${file}"
  fi
done < <(find "${REFS}" -type f -name '*.yaml')

# Repo-wide scan for common default credential assignments (exclude docs that mention the words in prose carefully).
SCAN_PATHS=(
  "${ROOT}/infra"
  "${ROOT}/apps"
  "${ROOT}/Makefile"
)
HITS=0
TMP_HITS="$(mktemp)"
for path in "${SCAN_PATHS[@]}"; do
  [[ -e "${path}" ]] || continue
  # shellcheck disable=SC2162
  grep -RInE \
    --exclude-dir=node_modules \
    --exclude-dir=.git \
    --exclude-dir=evidence \
    --exclude='*.md' \
    --exclude='policy.yaml' \
    --exclude='validate-secrets.sh' \
    --exclude='.env.example' \
    -e 'password[[:space:]]*=[[:space:]]*(admin|password|changeme|secret|root|123456)' \
    -e 'POSTGRES_PASSWORD[[:space:]]*=[[:space:]]*(postgres|admin|password|changeme)' \
    -e 'BEGIN (RSA |OPENSSH )?PRIVATE KEY' \
    "${path}" 2>/dev/null >>"${TMP_HITS}" || true
done

if [[ -s "${TMP_HITS}" ]]; then
  echo "validate-secrets FAIL: forbidden credential patterns found:" >&2
  cat "${TMP_HITS}" >&2
  rm -f "${TMP_HITS}"
  exit 1
fi
rm -f "${TMP_HITS}"

# .env.example must not contain assigned secret values
if grep -E '^(POSTGRES_PASSWORD|REDIS_PASSWORD|MINIO_SECRET_KEY|ARGOCD_ADMIN_PASSWORD)=.+' "${REFS}/.env.example" | grep -vq '=$'; then
  fail ".env.example contains assigned secret values"
fi

python3 - <<PY
import json, pathlib
report = {
  "check": "validate-secrets",
  "status": "pass",
  "required_refs": ${#REQUIRED[@]},
  "default_credentials": "none",
  "policy": "infra/secrets/policy.yaml",
}
pathlib.Path("${REPORT}").write_text(json.dumps(report, indent=2) + "\n")
print("validate-secrets PASS")
print(f"evidence: ${REPORT}")
PY
