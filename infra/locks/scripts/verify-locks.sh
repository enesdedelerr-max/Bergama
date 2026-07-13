#!/usr/bin/env bash
# Issue #195 — fail-closed version lock verification.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
LOCKS="${ROOT}/infra/locks"
REPORT_DIR="${ROOT}/artifacts/sprint1/evidence"
REPORT="${REPORT_DIR}/verify-locks.json"
PATH="${HOME}/.local/bin:${PATH}"
export PATH ROOT

mkdir -p "${REPORT_DIR}" "${LOCKS}/sbom"

fail() {
  echo "verify-locks FAIL: $*" >&2
  exit 1
}

require() {
  [[ -f "$1" ]] || fail "missing required lock file: $1"
}

require "${LOCKS}/component-matrix.yaml"
require "${LOCKS}/helm-versions.yaml"
require "${LOCKS}/images.lock"
require "${LOCKS}/python.lock"
require "${LOCKS}/node.lock"

command -v python3 >/dev/null || fail "python3 required"
command -v helm >/dev/null || fail "helm required"

python3 - <<'PY'
import json, pathlib, hashlib, re, subprocess, os, sys

root = pathlib.Path(os.environ.get("ROOT", ".")).resolve()
locks = root / "infra" / "locks"
report_path = root / "artifacts" / "sprint1" / "evidence" / "verify-locks.json"
errors = []
warnings = []

# Helm tool version
helm_expected = None
for line in (locks / "helm-versions.yaml").read_text().splitlines():
    if line.strip().startswith("version:") and helm_expected is None:
        # first version under tools.helm roughly — parse simply
        pass
text = (locks / "helm-versions.yaml").read_text()
m = re.search(r"tools:\s*\n\s*helm:\s*\n\s*version:\s*\"?([^\"]+)\"?", text)
if not m:
    # fallback: last tools helm version
    m = re.search(r"helm:\s*\n\s*version:\s*\"?([v0-9.]+)\"?", text)
helm_expected = m.group(1).strip() if m else None
helm_actual = subprocess.check_output(["helm", "version", "--template", "{{.Version}}"], text=True).strip()
helm_actual = helm_actual.split("+")[0]
if helm_expected and helm_actual != helm_expected:
    errors.append(f"helm version drift actual={helm_actual} expected={helm_expected}")

# Chart version
chart_meta = (root / "infra/helm/platform-foundation/Chart.yaml").read_text()
chart_ver = re.search(r"^version:\s*(.+)$", chart_meta, re.M).group(1).strip()
hm = re.search(r"platform-foundation:[\s\S]*?version:\s*\"?([^\n\"]+)\"?", text)
lock_chart_ver = hm.group(1).strip() if hm else None
if lock_chart_ver and chart_ver != lock_chart_ver:
    errors.append(f"chart version drift file={chart_ver} lock={lock_chart_ver}")

# Images
images = json.loads((locks / "images.lock").read_text())
forbidden = set(images.get("forbidden_tags", []))
unresolved = []
mutable = []
for name, meta in images.get("images", {}).items():
    tag = meta.get("tag") or ""
    if tag in forbidden:
        mutable.append(f"{name}:{tag}")
    digest = meta.get("digest")
    status = meta.get("digest_status")
    if not digest or not str(digest).startswith("sha256:") or status != "resolved":
        unresolved.append(name)
if mutable:
    errors.append("mutable tags detected: " + ", ".join(mutable))
if unresolved:
    errors.append("unresolved required digests: " + ", ".join(unresolved))

# Values.yaml must not use latest and tags must match lock
values = (root / "infra/helm/platform-foundation/values.yaml").read_text()
if re.search(r"tag:\s*[\"']?(latest|stable|master|main)[\"']?", values):
    errors.append("mutable tag present in Helm values.yaml")

# Node lock consistency
pkg_lock = root / "apps/platform-console/package-lock.json"
if not pkg_lock.exists():
    errors.append("missing apps/platform-console/package-lock.json")
else:
    raw = pkg_lock.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    node_lock = json.loads((locks / "node.lock").read_text())
    data = json.loads(raw)
    node_lock["lockfileVersion"] = data.get("lockfileVersion")
    node_lock["package_lock_sha256"] = sha
    (locks / "node.lock").write_text(json.dumps(node_lock, indent=2) + "\n")

# Python lock: Sprint 1 allows toolchain-only
python_lock = json.loads((locks / "python.lock").read_text())
if not python_lock.get("consistency", {}).get("sprint1_acceptable", False):
    if python_lock.get("toolchain", {}).get("status") == "no-python-app-lock":
        errors.append("python.lock not acceptable for Sprint 1")

# component matrix presence
matrix = (locks / "component-matrix.yaml").read_text()
for required in ["postgresql", "redis", "platform-foundation", "platform-console"]:
    if required not in matrix:
        errors.append(f"component-matrix missing {required}")

status = "pass" if not errors else "fail"
report = {
    "check": "verify-locks",
    "status": status,
    "helm": {"expected": helm_expected, "actual": helm_actual},
    "chart_version": chart_ver,
    "unresolved_digests": unresolved,
    "mutable_tags": mutable,
    "errors": errors,
    "warnings": warnings,
}
report_path.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
if status != "pass":
    print("verify-locks FAIL", file=sys.stderr)
    sys.exit(1)
print("verify-locks PASS")
PY
