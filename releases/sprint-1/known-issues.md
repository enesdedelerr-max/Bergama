# Known Issues — Sprint 1 (`v0.1.0-sprint1`)

- ArgoCD application `platform-foundation` syncs the foundation Helm chart only. Stateful and observability workloads are deployed via `infra/bootstrap/` Make targets for the local Kind gate.
- `argocd` CLI may fail without `ARGOCD_NAMESPACE=argocd`; use `kubectl get application -n argocd platform-foundation` for authoritative status.
- Stock `postgres:16.8` does not provide `vector` or `timescaledb` extensions; only core SQL smoke is certified.
- Iceberg REST catalog uses `tabulario/iceberg-rest:1.6.0` (not yet in `images.lock`).
- Backup/restore is smoke-level validation only — not DR certification.
- Gate evidence and backup timestamps under `artifacts/` and `backup/` are local runtime outputs and are gitignored.
