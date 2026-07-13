# Rollback Notes — Sprint 1

1. Do not promote `v0.1.0-sprint1` if `make gate-sprint1` failed.
2. To roll back GitOps sync: disable automated sync and `argocd app rollback platform-foundation` (or equivalent) to the previous known revision.
3. Restore stateful data only from verified backup artifacts under `backup/` after validating checksums.
4. Remove a mistaken local tag with `git tag -d v0.1.0-sprint1` if created erroneously.
