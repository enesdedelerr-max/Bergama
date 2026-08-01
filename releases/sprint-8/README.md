# Sprint 8 Release Package

This documentation package is the governance record prepared for
`v0.8.0-sprint8`.

The implementation baseline before governance closeout is:

```text
dedccab35d3238f6cc9840689ca61a99cc454ce6
```

## Contents

- `RELEASE_NOTES.md`: completed capabilities, compatibility, safety boundaries,
  limitations, risks, rollback guidance, and exclusions.

## Related

- Sprint README: [`docs/sprints/sprint-8/README.md`](../../docs/sprints/sprint-8/README.md)
- Sprint CLOSEOUT: [`docs/sprints/sprint-8/CLOSEOUT.md`](../../docs/sprints/sprint-8/CLOSEOUT.md)
- Issue #78
- PR #79
- Roadmap: [`ROADMAP.md`](../../ROADMAP.md)
- Governance: [`docs/governance/`](../../docs/governance/)
- Policy Version v1: [`docs/policy/premarket-scoring-policy-v1.md`](../../docs/policy/premarket-scoring-policy-v1.md)
- Architecture v1: [`docs/architecture/premarket-scoring-engine-architecture-v1.md`](../../docs/architecture/premarket-scoring-engine-architecture-v1.md)

## Tag policy

Create `v0.8.0-sprint8` after:

1. The governance closeout commit is on `main`.
2. Local `main` is clean and equals `origin/main`.
3. The closeout diff is confirmed to contain only documentation and release
   governance artifacts.
4. Applicable repository quality and security checks have been executed and
   their real results reviewed.
5. Explicit approval to tag has been given.

This package does not contain or claim a Sprint 8 runtime validation artifact,
SBOM, OpenAPI snapshot, checksum manifest, dedicated `gate-sprint8` result, or
GitHub CI status inventory.
