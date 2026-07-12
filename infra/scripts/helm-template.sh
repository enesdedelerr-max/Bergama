#!/usr/bin/env bash
# Issue #198 — Helm template render for platform-foundation chart.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CHART="${ROOT}/infra/helm/platform-foundation"
EVIDENCE_DIR="${ROOT}/infra/evidence/sprint1"
OUT="${EVIDENCE_DIR}/helm-template.yaml"
PATH="${HOME}/.local/bin:${PATH}"

mkdir -p "${EVIDENCE_DIR}"
command -v helm >/dev/null || { echo "helm-template FAIL: helm not found" >&2; exit 1; }

helm template platform-foundation "${CHART}" \
  --namespace platform \
  >"${OUT}"

# Basic assertions on rendered output
grep -q 'kind: Namespace' "${OUT}" || { echo "helm-template FAIL: Namespace missing" >&2; exit 1; }
grep -q 'platform-foundation-inventory' "${OUT}" || { echo "helm-template FAIL: inventory ConfigMap missing" >&2; exit 1; }
grep -q 'service-declaration-postgresql' "${OUT}" || { echo "helm-template FAIL: postgresql declaration missing" >&2; exit 1; }
grep -q 'tag: latest' "${OUT}" && { echo "helm-template FAIL: latest tag rendered" >&2; exit 1; } || true

echo "helm-template PASS"
echo "evidence: ${OUT}"
