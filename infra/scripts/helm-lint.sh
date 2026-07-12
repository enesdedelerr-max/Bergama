#!/usr/bin/env bash
# Issue #198 — Helm lint for platform-foundation chart.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CHART="${ROOT}/infra/helm/platform-foundation"
EVIDENCE_DIR="${ROOT}/infra/evidence/sprint1"
REPORT="${EVIDENCE_DIR}/helm-lint.txt"
PATH="${HOME}/.local/bin:${PATH}"

mkdir -p "${EVIDENCE_DIR}"
command -v helm >/dev/null || { echo "helm-lint FAIL: helm not found" >&2; exit 1; }

helm lint "${CHART}" | tee "${REPORT}"
echo "helm-lint PASS"
echo "evidence: ${REPORT}"
