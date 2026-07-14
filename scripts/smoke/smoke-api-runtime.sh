#!/usr/bin/env bash
# Sprint 2 API runtime smoke orchestration wrapper.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT}/apps/api"
exec uv run python "${ROOT}/scripts/smoke/smoke_api_runtime.py" "$@"
