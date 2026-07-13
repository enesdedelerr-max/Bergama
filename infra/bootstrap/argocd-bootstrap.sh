#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
ensure_tools
require_cmd argocd
use_context

kubectl create namespace "${ARGOCD_NS}" --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace "${NS}" --dry-run=client -o yaml | kubectl apply -f -

if ! kubectl get deployment -n "${ARGOCD_NS}" argocd-server >/dev/null 2>&1; then
  log "Installing Argo CD v2.14.9"
  kubectl apply -n "${ARGOCD_NS}" -f https://raw.githubusercontent.com/argoproj/argo-cd/v2.14.9/manifests/install.yaml
fi

ARGOCD_IMAGE="$(image_ref argocd)"
for dep in argocd-server argocd-repo-server argocd-application-controller; do
  kubectl set image -n "${ARGOCD_NS}" "deployment/${dep}" "*=${ARGOCD_IMAGE}" >/dev/null 2>&1 || true
done

kubectl patch deployment argocd-repo-server -n "${ARGOCD_NS}" --type=json -p='[
  {"op":"add","path":"/spec/template/spec/volumes/-","value":{"name":"bergama-repo","hostPath":{"path":"/bergama-repo","type":"Directory"}}},
  {"op":"add","path":"/spec/template/spec/containers/0/volumeMounts/-","value":{"name":"bergama-repo","mountPath":"/bergama-repo","readOnly":true}}
]' 2>/dev/null || kubectl patch deployment argocd-repo-server -n "${ARGOCD_NS}" --type=strategic -p '
spec:
  template:
    spec:
      volumes:
        - name: bergama-repo
          hostPath:
            path: /bergama-repo
            type: Directory
      containers:
        - name: argocd-repo-server
          volumeMounts:
            - name: bergama-repo
              mountPath: /bergama-repo
              readOnly: true
'

kubectl rollout status -n "${ARGOCD_NS}" deployment/argocd-server --timeout=300s
kubectl rollout status -n "${ARGOCD_NS}" deployment/argocd-repo-server --timeout=300s
kubectl rollout status -n "${ARGOCD_NS}" statefulset/argocd-application-controller --timeout=300s

BRANCH="$(git -C "${ROOT}" rev-parse --abbrev-ref HEAD)"
kubectl apply -f - <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: bergama-local-repo
  namespace: ${ARGOCD_NS}
  labels:
    argocd.argoproj.io/secret-type: repository
stringData:
  type: git
  url: file:///bergama-repo
EOF

kubectl apply -f - <<EOF
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: platform-foundation
  namespace: ${ARGOCD_NS}
  labels:
    app.kubernetes.io/part-of: platform-foundation
    bergama.io/sprint: "1"
spec:
  project: default
  source:
    repoURL: file:///bergama-repo
    targetRevision: ${BRANCH}
    path: infra/helm/platform-foundation
    helm:
      valueFiles:
        - values.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: ${NS}
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
EOF

argocd login --core --insecure >/dev/null 2>&1 || true
for _ in $(seq 1 30); do
  health="$(kubectl get application -n "${ARGOCD_NS}" platform-foundation -o jsonpath='{.status.health.status}' 2>/dev/null || true)"
  sync="$(kubectl get application -n "${ARGOCD_NS}" platform-foundation -o jsonpath='{.status.sync.status}' 2>/dev/null || true)"
  if [[ "${health}" == "Healthy" && "${sync}" == "Synced" ]]; then
    break
  fi
  argocd app sync platform-foundation --force >/dev/null 2>&1 || true
  sleep 5
done
health="$(kubectl get application -n "${ARGOCD_NS}" platform-foundation -o jsonpath='{.status.health.status}' 2>/dev/null || true)"
sync="$(kubectl get application -n "${ARGOCD_NS}" platform-foundation -o jsonpath='{.status.sync.status}' 2>/dev/null || true)"
[[ "${health}" == "Healthy" && "${sync}" == "Synced" ]] || fail "platform-foundation not Healthy/Synced (health=${health} sync=${sync})"

log "argocd-bootstrap PASS"
