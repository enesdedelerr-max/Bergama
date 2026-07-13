#!/usr/bin/env bash
# Issue #199 — Sprint 1 release package (fail-closed; no fabricated SBOM).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${ROOT}/releases/sprint-1"
EVIDENCE="${ROOT}/artifacts/sprint1/evidence"
PATH="${HOME}/.local/bin:${PATH}"
export PATH ROOT
mkdir -p "${OUT}" "${EVIDENCE}"

fail() { echo "build-release FAIL: $*" >&2; exit 1; }

command -v shasum >/dev/null || command -v sha256sum >/dev/null || fail "sha256 tool missing"
command -v python3 >/dev/null || fail "python3 missing"
command -v helm >/dev/null || fail "helm missing"

# SBOM tool is mandatory — do not fabricate SPDX.
if ! command -v syft >/dev/null 2>&1; then
  fail "syft is not installed. Install syft to generate SPDX SBOM. Refusing to fabricate sbom.spdx.json."
fi

BRANCH="$(git -C "${ROOT}" rev-parse --abbrev-ref HEAD)"
COMMIT="$(git -C "${ROOT}" rev-parse HEAD)"
HELM_VER="$(helm version --template '{{.Version}}')"

# versions.json from locks
python3 - <<'PY'
import json, pathlib, os, subprocess, hashlib, datetime

root = pathlib.Path(os.environ["ROOT"])
out = root / "releases/sprint-1"
images = json.loads((root / "infra/locks/images.lock").read_text())
helm = (root / "infra/locks/helm-versions.yaml").read_text()
node = json.loads((root / "infra/locks/node.lock").read_text())
python_lock = json.loads((root / "infra/locks/python.lock").read_text())

versions = {
  "release": "v0.1.0-sprint1",
  "git": {
    "branch": subprocess.check_output(["git","rev-parse","--abbrev-ref","HEAD"], cwd=root, text=True).strip(),
    "commit": subprocess.check_output(["git","rev-parse","HEAD"], cwd=root, text=True).strip(),
  },
  "helm": helm,
  "images": images.get("images", {}),
  "node": node,
  "python": python_lock,
  "generated_at": datetime.datetime.utcnow().replace(microsecond=0).isoformat()+"Z",
}
(out / "versions.json").write_text(json.dumps(versions, indent=2, sort_keys=True) + "\n")

manifest = {
  "release": "v0.1.0-sprint1",
  "artifacts": [
    "release-notes.md",
    "known-issues.md",
    "risk-summary.md",
    "rollback-notes.md",
    "artifact-manifest.yaml",
    "versions.json",
    "checksums.txt",
    "sbom.spdx.json",
  ],
}
(out / "artifact-manifest.yaml").write_text(
    "release: v0.1.0-sprint1\nartifacts:\n" +
    "".join(f"  - {a}\n" for a in manifest["artifacts"])
)
PY

# Generate SPDX SBOM with syft over repo locks + console package-lock
syft "dir:${ROOT}" -o spdx-json="${OUT}/sbom.spdx.json" >/dev/null

[[ -s "${OUT}/sbom.spdx.json" ]] || fail "SBOM file missing or empty after syft"

# Documentation from actual state
python3 - <<'PY'
import pathlib, os, json, subprocess
root = pathlib.Path(os.environ["ROOT"])
out = root / "releases/sprint-1"
images = json.loads((root / "infra/locks/images.lock").read_text())["images"]
commit = subprocess.check_output(["git","rev-parse","--short","HEAD"], cwd=root, text=True).strip()
branch = subprocess.check_output(["git","rev-parse","--abbrev-ref","HEAD"], cwd=root, text=True).strip()

(out / "release-notes.md").write_text(f"""# Sprint 1 Release Notes

Release: `v0.1.0-sprint1`
Branch: `{branch}`
Commit: `{commit}`

## Included

- Version lock foundation (component matrix, helm, images with digests, python/node locks)
- Secrets foundation (templates, policies, validation)
- Backup/restore smoke orchestration scripts
- Platform validation harness
- Helm `platform-foundation` chart package validation
- Release artifact packaging

## Not included / not certified

- Live Kind cluster bootstrap automation in this change set
- Full disaster recovery certification
- Sprint 2 FastAPI runtime
""")

unresolved = [k for k,v in images.items() if v.get("digest_status") != "resolved"]
(out / "known-issues.md").write_text(f"""# Known Issues — Sprint 1

- Platform validation and live backups require a running Kind cluster and deployed services.
- ArgoCD CLI/runtime Healthy+Synced evidence is required for gate PASS.
- Unresolved image digests at packaging time: {unresolved or "none"}.
- Previous offline-only gate evidence must not be treated as live runtime proof.
""")

(out / "risk-summary.md").write_text("""# Risk Summary — Sprint 1

- **High**: Without Kind/ArgoCD runtime evidence, production-like readiness is unproven.
- **Medium**: Backup/restore is smoke-level only.
- **Medium**: Secrets validation detects patterns; it cannot prove external secret stores are correctly populated.
- **Low**: Helm chart currently declares inventory/config; full stateful workload rollout is environment-controlled.
""")

(out / "rollback-notes.md").write_text("""# Rollback Notes — Sprint 1

1. Do not promote `v0.1.0-sprint1` if `make gate-sprint1` failed.
2. To roll back GitOps sync: disable automated sync and `argocd app rollback platform-foundation` (or equivalent) to the previous known revision.
3. Restore stateful data only from verified backup artifacts under `backup/` after validating checksums.
4. Remove a mistaken local tag with `git tag -d v0.1.0-sprint1` if created erroneously.
""")
print("release docs written")
PY

# checksums
(
  cd "${OUT}"
  if command -v sha256sum >/dev/null; then
    sha256sum release-notes.md known-issues.md risk-summary.md rollback-notes.md artifact-manifest.yaml versions.json sbom.spdx.json >checksums.txt
  else
    shasum -a 256 release-notes.md known-issues.md risk-summary.md rollback-notes.md artifact-manifest.yaml versions.json sbom.spdx.json >checksums.txt
  fi
)

python3 - <<'PY'
import json, pathlib, os
root = pathlib.Path(os.environ["ROOT"])
report = {
  "check": "build-release",
  "status": "pass",
  "out": "releases/sprint-1",
}
(root / "artifacts/sprint1/evidence/build-release.json").write_text(json.dumps(report, indent=2)+"\n")
print("build-release PASS")
PY
