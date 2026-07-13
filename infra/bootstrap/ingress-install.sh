#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
ensure_tools
use_context

kubectl create namespace "${NS}" --dry-run=client -o yaml | kubectl apply -f -

if kubectl get ns ingress-nginx >/dev/null 2>&1; then
  log "ingress-nginx namespace exists"
else
  log "Installing ingress-nginx for Kind"
  kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.12.0/deploy/static/provider/kind/deploy.yaml
fi

kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=300s

kubectl apply -f "${ROOT}/infra/bootstrap/manifests/ingress-health.yaml"
kubectl wait --namespace "${NS}" \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/name=health-check \
  --timeout=180s || true

log "ingress-install PASS"
