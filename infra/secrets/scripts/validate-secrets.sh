#!/usr/bin/env bash
# Issue #196 — fail-closed secrets validation.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SECRETS="${ROOT}/infra/secrets"
REPORT="${ROOT}/artifacts/sprint1/evidence/validate-secrets.json"
export ROOT
mkdir -p "$(dirname "${REPORT}")"

fail() { echo "validate-secrets FAIL: $*" >&2; exit 1; }

[[ -f "${SECRETS}/templates/local-secret.yaml" ]] || fail "missing local-secret template"
[[ -f "${SECRETS}/templates/external-secret.yaml" ]] || fail "missing external-secret template"
[[ -f "${SECRETS}/policies/naming.md" ]] || fail "missing naming policy"
[[ -f "${SECRETS}/policies/rotation.md" ]] || fail "missing rotation policy"

python3 - <<'PY'
import json, os, pathlib, re, sys

root = pathlib.Path(os.environ["ROOT"])
errors = []
scanned_files = 0

required = [
    root / "infra/secrets/templates/local-secret.yaml",
    root / "infra/secrets/templates/external-secret.yaml",
    root / "infra/secrets/refs/postgresql-credentials.yaml",
    root / "infra/secrets/refs/redis-credentials.yaml",
    root / "infra/secrets/refs/minio-credentials.yaml",
    root / "infra/secrets/refs/argocd-admin.yaml",
]
for path in required:
    if not path.exists():
        errors.append(f"missing required secret reference: {path.relative_to(root)}")

forbidden_patterns = [
    re.compile(r"(?i)password\s*[:=]\s*[\"']?(admin|password|changeme|secret|root|123456|postgres)[\"']?\s*$"),
    re.compile(r"(?i)POSTGRES_PASSWORD\s*=\s*(postgres|admin|password|changeme)"),
    re.compile(r"(?i)BEGIN (RSA |OPENSSH )?PRIVATE KEY"),
    re.compile(r"(?i)api[_-]?key\s*[:=]\s*[\"']?[A-Za-z0-9_\-]{20,}"),
]

exclude_dirs = {".git", "node_modules", ".next", "evidence", "artifacts", "releases", "backup"}
exclude_names = {"validate-secrets.sh", "policy.yaml", "naming.md", "rotation.md", "README.md"}

for path in root.rglob("*"):
    if not path.is_file():
        continue
    if any(part in exclude_dirs for part in path.parts):
        continue
    if path.name in exclude_names:
        continue
    if path.suffix not in {".yaml", ".yml", ".env", ".tf", ".json", ".toml", ".ini", ".properties", ".txt"} and path.name != ".env.example":
        # still scan .env* 
        if not path.name.startswith(".env"):
            continue
    scanned_files += 1
    try:
        text = path.read_text(errors="ignore")
    except Exception:
        continue
    # committed env files with assignments
    if path.name.startswith(".env") and path.name != ".env.example":
        for line in text.splitlines():
            if re.match(r"^[A-Z0-9_]+=.+$", line) and not line.endswith("="):
                errors.append(f"committed env secret assignment in {path.relative_to(root)}")
                break
    for pat in forbidden_patterns:
        for i, line in enumerate(text.splitlines(), 1):
            if pat.search(line):
                errors.append(f"forbidden credential pattern in {path.relative_to(root)}:{i}")

# templates must not contain literal passwords
for tmpl in (root / "infra/secrets/templates").glob("*.yaml"):
    text = tmpl.read_text()
    if "SECRETREF" not in text and "remoteRef" not in text:
        errors.append(f"template missing secret reference mechanism: {tmpl.name}")
    if re.search(r"(?i)password:\s*[\"']?(admin|password|changeme)[\"']?", text):
        errors.append(f"default password in template {tmpl.name}")

status = "pass" if not errors else "fail"
# Never include secret values in the report.
report = {
    "check": "validate-secrets",
    "status": status,
    "scanned_files": scanned_files,
    "error_count": len(errors),
    "errors": errors,
}
out = root / "artifacts/sprint1/evidence/validate-secrets.json"
out.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"status": status, "error_count": len(errors), "errors": errors}, indent=2))
if status != "pass":
    sys.exit(1)
print("validate-secrets PASS")
PY
