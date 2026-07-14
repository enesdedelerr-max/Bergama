# Sprint 2 Rollback Notes

## Software rollback

1. Revert the Sprint 2 gate/release commit(s) if only packaging changed.
2. To roll back runtime features, revert stacked PRs in reverse order (#210 → #209 → #208B → #208A …).
3. Redeploy previous known-good API image/tag if deployed.

## Data / ops

- No production trading state is written by Sprint 2 runtime foundation.
- Registry files are read-only; no registry writes to roll back.
- Kafka offsets for optional live smoke should be treated as ephemeral test groups.

## Tag

Do not delete `v0.2.0-sprint2` if already published without an explicit ops decision.
