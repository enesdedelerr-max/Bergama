# Sprint 3 Release Package

This package is the self-contained Sprint 3 runtime validation and release evidence for `v0.3.0-sprint3`.

## Validate

Run from the repository root:

```bash
make validate-sprint3-release
```

## Reproduce

Run from a clean checkout at commit `045e9ad0f54411b5538d349928ab37d57adb0529` with required local Kafka, Iceberg REST catalog, and MinIO available:

```bash
make gate-sprint3
```

Post-merge tag policy is documented in `docs/sprints/sprint-3/README.md`. Do not create or push `v0.3.0-sprint3` unless the merged-main gate has passed and explicit approval is given.

## Artifacts

- `sprint3-quality-gate.json`: normalized required and optional gate results.
- `sprint3-runtime-validation.json`: normalized Kafka to Iceberg runtime proof.
- `sprint3-openapi.json`: current generated API schema.
- `sbom.spdx.json`: real Syft SPDX JSON SBOM with normalized volatile creation timestamp and document namespace.
- `MANIFEST.json`: release metadata, hashes, tool versions, and source evidence hashes.
- `checksums.txt`: SHA-256 hashes for tracked release files.
