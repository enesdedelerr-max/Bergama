#!/usr/bin/env bash
# Render and apply Sprint 1 stateful/observability workloads with locked image digests.
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
ensure_tools
use_context

TARGET="${1:-all}"

render_and_apply() {
  local name="$1"
  local file="${ROOT}/infra/bootstrap/manifests/${name}.yaml"
  [[ -f "${file}" ]] || fail "missing manifest ${name}.yaml"
  apply_manifest "${file}"
}

deploy_postgresql() {
  kubectl create secret generic postgresql-credentials -n "${NS}" \
    --from-literal=username=postgres \
    --from-literal=password=bergama-sprint1-local-k9m2 \
    --dry-run=client -o yaml | kubectl apply -f -
  render_and_apply postgresql
  wait_rollout "${NS}" statefulset/postgresql
}

deploy_redis() {
  render_and_apply redis
  wait_rollout "${NS}" statefulset/redis
}

deploy_kafka() {
  render_and_apply kafka
  wait_rollout "${NS}" statefulset/kafka
}

deploy_clickhouse() {
  render_and_apply clickhouse
  wait_rollout "${NS}" statefulset/clickhouse
}

deploy_minio() {
  kubectl create secret generic minio-credentials -n "${NS}" \
    --from-literal=rootUser=bergama-minio-local \
    --from-literal=rootPassword=bergama-sprint1-minio-k7p4 \
    --dry-run=client -o yaml | kubectl apply -f -
  render_and_apply minio
  wait_rollout "${NS}" statefulset/minio
  local pod
  pod="$(kubectl get pods -n "${NS}" -l app.kubernetes.io/name=minio -o jsonpath='{.items[0].metadata.name}')"
  kubectl exec -n "${NS}" "${pod}" -- mkdir -p /data/bergama-warehouse
}

deploy_iceberg() {
  render_and_apply iceberg
  wait_rollout "${NS}" deployment/iceberg-catalog
}

deploy_observability() {
  render_and_apply observability
  for dep in prometheus grafana loki tempo; do
    wait_rollout "${NS}" "deployment/${dep}"
  done
}

case "${TARGET}" in
  postgresql) deploy_postgresql ;;
  redis) deploy_redis ;;
  kafka) deploy_kafka ;;
  clickhouse) deploy_clickhouse ;;
  minio) deploy_minio ;;
  iceberg) deploy_iceberg ;;
  observability) deploy_observability ;;
  all)
    deploy_postgresql
    deploy_redis
    deploy_kafka
    deploy_clickhouse
    deploy_minio
    deploy_iceberg
    deploy_observability
    ;;
  *) fail "unknown deploy target: ${TARGET}" ;;
esac

log "${TARGET} deploy PASS"
