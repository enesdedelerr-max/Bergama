#!/usr/bin/env bash
# Sprint 2 gate entrypoint — fail-closed runtime foundation verification.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
# Orchestrator is stdlib-only; use 3.13 when available.
PYTHON="${BERGAMA_PYTHON:-}"
if [[ -z "${PYTHON}" ]]; then
  if command -v python3.13 >/dev/null 2>&1; then
    PYTHON="$(command -v python3.13)"
  else
    PYTHON="$(command -v python3)"
  fi
fi
exec "${PYTHON}" "${ROOT}/scripts/gates/gate_sprint2.py" "$@"
