# Secret naming standard (Issue #196)

## Pattern

```text
{environment}/{system}/{component}/{purpose}
```

Examples:

- `paper/platform/postgresql/credentials`
- `sandbox/platform/redis/password`
- `live/platform/minio/root`

## Kubernetes object names

- Secret: `{component}-{purpose}` (example: `postgresql-credentials`)
- ExternalSecret: `{component}-{purpose}` matching Secret name
- Namespace: environment-specific platform namespace (`platform` for paper local)

## Rules

- Never embed credential literals in Git.
- Use `${SECRETREF:...}` or External Secrets remote refs.
- Separate paper, sandbox, and live credential stores.
- Rotation must create a new version; do not mutate historical secret versions in place.
