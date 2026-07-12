#!/usr/bin/env bash
# Issue #199 — build Sprint 1 release artifact, checksums, and SBOM.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RELEASE_VERSION="$(awk '/^release_version:/{gsub(/"/,"",$2); print $2; exit}' "${ROOT}/infra/locks/versions.lock.yaml")"
OUT_DIR="${ROOT}/releases/${RELEASE_VERSION}"
EVIDENCE_DIR="${ROOT}/infra/evidence/sprint1"
REPORT="${EVIDENCE_DIR}/build-release.json"
STAGING="$(mktemp -d "${TMPDIR:-/tmp}/sprint1-release.XXXXXX")"

cleanup() {
  rm -rf "${STAGING}"
}
trap cleanup EXIT

mkdir -p "${OUT_DIR}" "${EVIDENCE_DIR}"

INCLUDE=(
  infra/locks
  infra/secrets
  infra/helm
  infra/gitops
  infra/scripts
  Makefile
  PROJECT.md
  ROADMAP.md
  AGENTS.md
  ARCHITECTURE.md
  docs/sprints/sprint-1
)

for item in "${INCLUDE[@]}"; do
  [[ -e "${ROOT}/${item}" ]] || { echo "build-release FAIL: missing ${item}" >&2; exit 1; }
done

# Stage release contents
mkdir -p "${STAGING}/bergama-${RELEASE_VERSION}"
for item in "${INCLUDE[@]}"; do
  mkdir -p "${STAGING}/bergama-${RELEASE_VERSION}/$(dirname "${item}")"
  cp -R "${ROOT}/${item}" "${STAGING}/bergama-${RELEASE_VERSION}/${item}"
done

# Copy platform validation evidence if present
if [[ -d "${EVIDENCE_DIR}" ]]; then
  mkdir -p "${STAGING}/bergama-${RELEASE_VERSION}/infra/evidence/sprint1"
  # Avoid copying large nested backups recursively into themselves; copy reports only
  find "${EVIDENCE_DIR}" -maxdepth 1 -type f -exec cp {} "${STAGING}/bergama-${RELEASE_VERSION}/infra/evidence/sprint1/" \;
fi

ARCHIVE="${OUT_DIR}/bergama-${RELEASE_VERSION}.tar.gz"
tar -C "${STAGING}" -czf "${ARCHIVE}" "bergama-${RELEASE_VERSION}"

(
  cd "${OUT_DIR}"
  shasum -a 256 "$(basename "${ARCHIVE}")" >"$(basename "${ARCHIVE}").sha256"
)

# Deterministic CycloneDX-like SBOM from version lock + chart metadata (no network).
SBOM="${OUT_DIR}/bergama-${RELEASE_VERSION}.sbom.json"
python3 - <<PY
import json, pathlib, datetime, hashlib, os

root = pathlib.Path(r"${ROOT}")
lock_text = (root / "infra/locks/versions.lock.yaml").read_text()
chart = (root / "infra/helm/platform-foundation/Chart.yaml").read_text()
values = (root / "infra/helm/platform-foundation/values.yaml").read_text()

components = []
# Parse images from values.yaml simply
repo = tag = name = None
for line in values.splitlines():
    if line.startswith("  ") and line.strip().endswith(":") and not line.strip().startswith("repository") and not line.strip().startswith("tag"):
        # service key under images
        pass

images = {}
current = None
in_images = False
for raw in values.splitlines():
    line = raw.rstrip()
    if line.startswith("images:"):
        in_images = True
        continue
    if in_images and line and not line.startswith(" "):
        in_images = False
    if not in_images:
        continue
    if line.startswith("  ") and not line.startswith("    ") and line.strip().endswith(":"):
        current = line.strip()[:-1]
        images[current] = {}
    elif current and "repository:" in line:
        images[current]["repository"] = line.split(":",1)[1].strip().strip('"')
    elif current and "tag:" in line:
        images[current]["tag"] = line.split(":",1)[1].strip().strip('"')

for name, meta in images.items():
    purl = f"pkg:docker/{meta['repository']}@{meta['tag']}"
    components.append({
        "type": "container",
        "name": name,
        "version": meta["tag"],
        "purl": purl,
    })

components.append({
    "type": "application",
    "name": "platform-foundation",
    "version": "0.1.0",
    "purl": "pkg:helm/platform-foundation@0.1.0",
})

sbom = {
    "bomFormat": "CycloneDX",
    "specVersion": "1.5",
    "version": 1,
    "metadata": {
        "timestamp": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "component": {
            "type": "application",
            "name": "bergama-sprint1",
            "version": "${RELEASE_VERSION}",
        },
        "tools": [{"name": "bergama-build-release", "version": "0.1.0"}],
    },
    "components": components,
}

digest = hashlib.sha256(json.dumps(sbom, sort_keys=True).encode()).hexdigest()
sbom["metadata"]["properties"] = [{"name": "bergama:content-hash", "value": digest}]
pathlib.Path(r"${SBOM}").write_text(json.dumps(sbom, indent=2) + "\n")
print(f"sbom written: ${SBOM}")
PY

(
  cd "${OUT_DIR}"
  shasum -a 256 "$(basename "${SBOM}")" >"$(basename "${SBOM}").sha256"
)

ARCHIVE_SHA="$(awk '{print $1}' "${ARCHIVE}.sha256")"
SBOM_SHA="$(awk '{print $1}' "${SBOM}.sha256")"

python3 - <<PY
import json, pathlib
report = {
  "check": "build-release",
  "status": "pass",
  "release_version": "${RELEASE_VERSION}",
  "archive": "releases/${RELEASE_VERSION}/bergama-${RELEASE_VERSION}.tar.gz",
  "archive_sha256": "${ARCHIVE_SHA}",
  "sbom": "releases/${RELEASE_VERSION}/bergama-${RELEASE_VERSION}.sbom.json",
  "sbom_sha256": "${SBOM_SHA}",
}
pathlib.Path(r"${REPORT}").write_text(json.dumps(report, indent=2) + "\n")
print("build-release PASS")
print(f"archive: ${ARCHIVE}")
print(f"sbom: ${SBOM}")
print(f"evidence: ${REPORT}")
PY
