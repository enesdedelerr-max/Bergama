# Sprint 6 Governance Closeout

## Decision

Sprint 6 is complete.

The approved Sprint 6 theme is **Feature Platform**. Planning is Issue **#65**.
Implementation scope is Issues **#66**, **#67**, and **#68**, merged through
PR **#69**. The final implementation merge commit is:

```text
a04b9e5d5b5673a3f4f2022159915b520995bf06
```

This closeout does not authorize Premarket Intelligence, AI Decision Engine,
Feature Store, persistence, online serving, or additional indicator work.

## Completion evidence

- Planning and implementation issues are documented under
  `docs/sprints/sprint-6/`.
- PR #69 merged Feature Platform foundation, host integration, and offline
  replay materialization to `main`.
- Closed bar catalog and default-disabled host settings are present on `main`.
- This closeout changes only documentation and release-governance artifacts.
- `ROADMAP.md` records Sprint 6 as Feature Platform and complete.

Detailed mapping is maintained in [`README.md`](README.md).

## Delivered architecture summary

- `BarEvent` → `FeatureSnapshot` materialization
  (`materialize_bar_feature_snapshot`).
- Initial closed catalog: `bar.open`, `bar.high`, `bar.low`, `bar.close`,
  `bar.volume`, optional `bar.vwap`.
- Strategy Host integration disabled by default
  (`BERGAMA_FEATURE_PLATFORM__*`).
- Offline replay ordered materialization
  (`materialize_bar_feature_snapshot_sequence`) without persistence.

## Compatibility and operational impact

- Breaking changes to Strategy SDK public API: none.
- Package version remains `0.1.0`.
- Feature Platform disabled by default; legacy assembler path remains when
  disabled.
- Live trading: not enabled.
- This closeout itself does not change runtime code.

## Validation evidence (implementation PR #69)

Commands recorded as required by Sprint 6 issues and previously executed for
the Feature Platform delivery:

```bash
make lint
make typecheck
make validate-secrets
make test-api-feature-platform
make test-api-strategy-sdk
make test-api-strategy-engine
git diff --check
```

No dedicated `gate-sprint6` target exists in the repository. This closeout does
not invent one.

## Known limitations

- Feature Platform is not a Feature Store.
- Offline materialization does not persist or serve features.
- Host integration is optional and disabled by default.
- Catalog is limited to existing bar fields; no derived indicators.
- Market Data replay is not a mandatory Feature Platform path.

## Risks

| Risk | Mitigation |
| --- | --- |
| Scope expands into Feature Store / Iceberg feature tables | Explicit exclusions in issue docs and this closeout |
| Premature Premarket / Decision Engine work | Deferred to Sprint 7 / Sprint 8 |
| Accidental default enablement | Settings default `enabled=False`; fail-closed when disabled |
| SDK contract drift | Sprint 5 freeze preserved; no `__all__` / version changes |

## Rollback

This closeout contains governance documentation only. If correction is needed,
revert the closeout commit before creating the Sprint 6 release tag. Reverting
these documents does not roll back Feature Platform application code.

To roll back Feature Platform implementation code, revert or follow-up-fix
PR #69 / merge `a04b9e5d5b5673a3f4f2022159915b520995bf06` through normal
repository change control — outside this documentation-only closeout.

## Release preparation

The intended release tag is:

```text
v0.6.0-sprint6
```

The tag is deliberately not created by this task. After this closeout is merged,
the next maintainer must:

1. Confirm the working tree is clean and local `main` equals `origin/main`.
2. Confirm the merged closeout commit contains only governance artifacts.
3. Review [`releases/sprint-6/RELEASE_NOTES.md`](../../../releases/sprint-6/RELEASE_NOTES.md).
4. Run the repository quality and security gates appropriate to a documentation
   release and record their actual outcomes.
5. Obtain explicit approval to create the release tag.
6. Create `v0.6.0-sprint6` at the verified merged `main` commit.

## Explicit exclusions

- Feature Store
- Feature persistence
- Online serving
- Additional / derived indicators
- Premarket Intelligence
- AI Decision Engine

## Next work

1. Merge this governance closeout.
2. Create Sprint 5 / Sprint 6 release tags when explicitly approved.
3. Begin Sprint 7 planning (Premarket Intelligence).

See also: [`docs/sprints/sprint-5/CLOSEOUT.md`](../sprint-5/CLOSEOUT.md) and
[`ROADMAP.md`](../../../ROADMAP.md).
