#!/usr/bin/env bash
# Validate OpenAPI contract for Sprint 2 API.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT}/apps/api"
exec uv run python "${ROOT}/scripts/gates/validate_api_openapi.py" "$@"
