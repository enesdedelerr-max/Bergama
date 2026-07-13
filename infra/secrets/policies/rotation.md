# Secret rotation policy (Issue #196)

## Cadence

- Application/database credentials: rotate at least every 90 days, or immediately on suspected compromise.
- Bootstrap/admin credentials: rotate after initial provisioning and whenever operators change.

## Process

1. Generate a new secret version in the external store / local sealed source.
2. Update ExternalSecret remote ref / local injection source.
3. Roll dependent workloads.
4. Verify application health.
5. Revoke the previous secret version.
6. Record rotation event (who/when/why) outside Git if the value is sensitive.

## Sprint 1 limitation

Vault is not required. Local development may use untracked `.env` files derived from `.env.example`.
Production-like environments must use external injection.
