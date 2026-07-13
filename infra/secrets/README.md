# Secrets foundation (Issue #196)

- `templates/` — local and ExternalSecret manifests (references only)
- `policies/` — naming and rotation standards
- `scripts/validate-secrets.sh` — fail-closed scanner
- Existing `refs/` remain as additional reference manifests

`make validate-secrets` must fail on plaintext defaults, committed env secrets, or missing required references.
Reports never print secret values.
