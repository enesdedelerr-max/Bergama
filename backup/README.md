# Sprint 1 backup foundation (Issue #197)

Timestamped backups for local Kubernetes services land in:

- `backup/postgres/`
- `backup/redis/`
- `backup/clickhouse/`
- `backup/minio/`

Orchestration:

- `scripts/backup.sh`
- `scripts/restore-smoke.sh`

This is a Sprint 1 smoke validation only — not disaster-recovery certification.

Backups fail closed if the Kind cluster or required pods are unavailable.
