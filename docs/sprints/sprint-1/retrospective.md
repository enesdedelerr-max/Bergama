# Sprint 1 Retrospective

**Sprint:** 1 — Infrastructure Finalization  
**Release:** `v0.1.0-sprint1`  
**Date:** 2026-07-12  
**Duration:** ~1 day (docs → console shell → gate harness → live runtime)  
**Decision:** GO for Sprint 2

## Goal

Establish a fail-closed Sprint 1 infrastructure gate with real runtime evidence: version locks, secrets validation, live backups, platform validation, Syft SBOM release packaging, and `make gate-sprint1`.

## What went well

- Fail-closed harness design prevented fabricated PASS states (offline-only runs correctly returned NO-GO).
- Image digests were resolved from registries, not invented.
- Kind bootstrap layer was added incrementally; each service failure (Kafka listeners, Tempo config, NetworkPolicy) was diagnosed from pod logs.
- `platform-validate.sh` was hardened with in-pod exec and port-forward probes — reliable under deny-by-default NetworkPolicy.
- Gate produced auditable evidence under `artifacts/sprint1/` and `releases/sprint-1/`.
- Platform Console shell landed early on a separate branch without blocking infra gate work.

## What was hard

- Repository initially had validation scripts but no runtime deployment layer — bootstrap had to be built under time pressure.
- Default-deny NetworkPolicy blocked cross-pod HTTP probes until policy and probe strategy were fixed.
- ArgoCD CLI required namespace context; kubectl Application status was the reliable source of truth.
- Kafka KRaft single-broker setup needed `127.0.0.1` advertised listeners for in-pod roundtrip.
- Local repo had no GitHub remote at sprint close — release process depends on `gh` + remote setup.

## What we would do differently

- Ship minimal Kind bootstrap manifests earlier in the sprint (same sprint, earlier day).
- Document GitOps scope explicitly: foundation chart vs stateful workloads.
- Add unreachable-kubeconfig fixture from the start for platform-validate unit tests.
- Pin bootstrap-only images (e.g. Iceberg REST) in `images.lock` or component matrix.

## Metrics

| Metric | Result |
|--------|--------|
| Gate stages passed | 11/11 |
| Unit tests | 12/12 |
| Platform validation checks | 0 failures at gate |
| Stateful PVCs bound | 5/5 |
| ArgoCD sync | Healthy + Synced |

## Carry forward to Sprint 2

- Do not start application runtime until Sprint 1 tag is on `main`.
- Keep fail-closed gates for any new bounded context.
- Prefer GitOps expansion over ad-hoc kubectl for production paths.
- Treat backup/restore as smoke until a dedicated DR issue is scheduled.

## Participants

- Engineering (local gate execution)
- Cursor agent (implementation partner)
