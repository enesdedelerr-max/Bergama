# Version locks (Issue #195)

This directory pins Sprint 1 tool, chart, image, Python and Node versions.

## Files

- `component-matrix.yaml` — required components and lock ownership
- `helm-versions.yaml` — Helm chart/tool pins
- `images.lock` — image tags + digests (`digest` must be resolved; never invented)
- `python.lock` — Python toolchain pin
- `node.lock` — Node application lock reference
- `scripts/verify-locks.sh` — fail-closed verification
- `sbom/` — workspace for SBOM intermediates (release SBOM is produced by `make build-release`)

## Rules

- Mutable tags (`latest`, `stable`, `master`, `main`) are forbidden.
- Components marked `require_digest: true` fail verification when digest is missing/unresolved.
- Digests must be obtained from a registry/tooling (`docker buildx imagetools`, `crane`, etc.).
- Do not fabricate digests or checksums.
