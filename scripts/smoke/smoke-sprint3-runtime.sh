#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

PYTHONPATH="${ROOT_DIR}:${ROOT_DIR}/apps/api" uv run --project "${ROOT_DIR}/apps/api" python -m scripts.smoke.smoke_sprint3_runtime "$@"
