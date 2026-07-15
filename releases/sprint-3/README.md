# Sprint 3 Release Package

Sprint 3 validates the market-data plane through executable gate evidence and a self-contained release package.

## Validate

```bash
make validate-sprint3-release
```

## Reproduce

From a clean checkout with required local Kafka, Iceberg REST catalog, and MinIO configured:

```bash
make gate-sprint3
```

`make build-sprint3-release` generates the machine artifacts in this directory from validated per-run evidence. It must not be replaced with hand-written JSON or placeholder SBOM output.

## Artifacts

- `sprint3-quality-gate.json`: normalized required and optional gate results.
- `sprint3-runtime-validation.json`: normalized Kafka to Iceberg runtime proof.
- `sprint3-openapi.json`: generated OpenAPI schema.
- `sbom.spdx.json`: real Syft SPDX JSON SBOM.
- `MANIFEST.json`: release metadata, evidence hashes, file hashes, and tool versions.
- `checksums.txt`: SHA-256 hashes for tracked release files.
