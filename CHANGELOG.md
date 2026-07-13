# Changelog

All notable changes to this project are documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [v0.1.0-sprint1] - 2026-07-12

Sprint 1 — Infrastructure foundation gate. Decision: **GO for Sprint 2**.

### Added

- Permanent repository context (`AGENTS.md`, `PROJECT.md`, `ARCHITECTURE.md`, `ROADMAP.md`, `.cursor/rules/`)
- Platform Operations Console read-only shell (`apps/platform-console`)
- Sprint 1 version locks with resolved image digests (`infra/locks/`)
- Secrets foundation templates, policies and fail-closed validation (`infra/secrets/`)
- Backup and restore-smoke orchestration against live Kubernetes (`scripts/backup.sh`, `scripts/restore-smoke.sh`)
- Live platform validation harness (`scripts/platform-validate.sh`)
- Release packaging with mandatory Syft SPDX SBOM (`scripts/build-release.sh`)
- Sprint 1 Go/No-Go gate (`scripts/gates/gate-sprint1.sh`, `make gate-sprint1`)
- Kind bootstrap and local platform deploy targets (`infra/bootstrap/`, `infra/kind/`)
- Unit tests for locks, secrets, backup, platform validation and release scripts (`tests/`)
- Release artifacts under `releases/sprint-1/`

### Changed

- `platform-foundation` NetworkPolicy allows in-namespace and ingress-nginx traffic for Sprint 1 local gate
- Makefile expanded with bootstrap and per-service deploy targets

### Verified (runtime)

- Kind cluster `bergama-sprint1` with PostgreSQL, Redis, Kafka, ClickHouse, MinIO, Iceberg catalog, observability stack
- ArgoCD application `platform-foundation`: Healthy + Synced
- `make gate-sprint1` PASS with live evidence
- Annotated tag `v0.1.0-sprint1`

### Known limitations

- ArgoCD manages foundation chart only; stateful workloads deployed via bootstrap Make targets for local gate
- Backup/restore is smoke-level, not DR certification
- Stock PostgreSQL image does not ship `vector` / `timescaledb` extensions
