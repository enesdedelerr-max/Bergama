# Sprint 1 Release Notes

Release: `v0.1.0-sprint1`  
Gate decision: **GO for Sprint 2**  
Validation: live Kind cluster `bergama-sprint1`

## Included

- Version lock foundation (`infra/locks/`) with resolved image digests
- Secrets foundation (`infra/secrets/`) with fail-closed validation
- Backup and restore-smoke scripts against live Kubernetes services
- Platform validation harness with real service smoke tests
- Kind bootstrap and local deploy targets (`infra/bootstrap/`, `infra/kind/`)
- Helm `platform-foundation` chart (namespaces, declarations, NetworkPolicy)
- ArgoCD GitOps app `platform-foundation` (Healthy + Synced)
- Release packaging with Syft SPDX SBOM (`releases/sprint-1/sbom.spdx.json`)
- Platform Operations Console read-only shell (`apps/platform-console`)
- Sprint 1 gate (`make gate-sprint1`) and unit tests (12 passed)

## Verified on Kind (runtime)

- PostgreSQL, Redis, Kafka, ClickHouse, MinIO, Iceberg REST catalog
- Prometheus, Grafana, Loki, Tempo
- Ingress health route, PVCs bound, cluster DNS
- Backup + restore smoke PASS

## Not included / not certified

- Full disaster recovery certification
- Sprint 2 FastAPI application runtime
- Production GitOps for all stateful workloads (foundation chart only via ArgoCD)
- PostgreSQL `vector` / `timescaledb` extensions on stock image

## Upgrade / deploy

```bash
make kind-bootstrap
make ingress-install
make argocd-bootstrap
make postgres-deploy redis-deploy kafka-deploy clickhouse-deploy minio-deploy iceberg-deploy observability-deploy
make gate-sprint1
```

## Evidence

- `artifacts/sprint1/gate-summary.json` (generated at gate run; not committed)
- `docs/sprints/sprint-1/retrospective.md`
- `CHANGELOG.md`
