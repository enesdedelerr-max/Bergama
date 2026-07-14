#!/usr/bin/env bash
# Build Sprint 2 release package + checksums.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
# Release packaging is stdlib-only; prefer 3.13 for UTC typing parity.
PYTHON="${BERGAMA_PYTHON:-}"
if [[ -z "${PYTHON}" ]]; then
  if command -v python3.13 >/dev/null 2>&1; then
    PYTHON="$(command -v python3.13)"
  else
    PYTHON="$(command -v python3)"
  fi
fi
exec "${PYTHON}" "${ROOT}/scripts/gates/build_sprint2_release.py" "$@"
