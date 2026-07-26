# Sprint 6 Release Package

This documentation package prepares the governance record for
`v0.6.0-sprint6`.

The tag has not been created. The implementation baseline before governance
closeout is:

```text
a04b9e5d5b5673a3f4f2022159915b520995bf06
```

## Contents

- `RELEASE_NOTES.md`: completed capabilities, compatibility, safety boundaries,
  limitations, risks, rollback guidance, and exclusions.

## Related

- Sprint README: [`docs/sprints/sprint-6/README.md`](../../docs/sprints/sprint-6/README.md)
- Sprint CLOSEOUT: [`docs/sprints/sprint-6/CLOSEOUT.md`](../../docs/sprints/sprint-6/CLOSEOUT.md)
- Issues #65, #66, #67, #68
- PR #69
- Roadmap: [`ROADMAP.md`](../../ROADMAP.md)

## Tag policy

Create `v0.6.0-sprint6` only after:

1. The governance closeout commit is merged to `main`.
2. Local `main` is clean and equals `origin/main`.
3. The merged diff is confirmed to contain only documentation and release
   governance artifacts.
4. Applicable repository quality and security checks have been executed and
   their real results reviewed.
5. Explicit approval to tag has been given.

This package does not contain or claim a Sprint 6 runtime validation artifact,
SBOM, OpenAPI snapshot, checksum manifest, or dedicated `gate-sprint6` result.
