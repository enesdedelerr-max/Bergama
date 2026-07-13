#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
ensure_tools

CONFIG_TEMPLATE="${ROOT}/infra/kind/bergama-sprint1.yaml"
CONFIG_RENDERED="${ROOT}/artifacts/sprint1/kind-config.yaml"
mkdir -p "$(dirname "${CONFIG_RENDERED}")"
sed "s|__REPO_ROOT__|${ROOT}|g" "${CONFIG_TEMPLATE}" >"${CONFIG_RENDERED}"

if kind get clusters 2>/dev/null | grep -qx "${CLUSTER_NAME}"; then
  log "Kind cluster ${CLUSTER_NAME} already exists"
else
  log "Creating Kind cluster ${CLUSTER_NAME}"
  kind create cluster --name "${CLUSTER_NAME}" --config "${CONFIG_RENDERED}" --wait 120s
fi

use_context
kubectl get nodes -o wide
log "kind-bootstrap PASS"
