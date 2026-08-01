# Sprint 8 Governance Closeout

## Decision

Sprint 8 is complete.

The approved Sprint 8 theme is **Premarket Scoring Foundation**. Authorized
implementation scope is Issue **#78**, merged through PR **#79**. The final
implementation merge commit is:

```text
dedccab35d3238f6cc9840689ca61a99cc454ce6
```

Planning / governance baseline for this sprint is repository-backed as:

- Governance Decisions #1–#12 under `docs/governance/`
- Policy Version v1 under `docs/policy/premarket-scoring-policy-v1.md`
- Premarket Scoring Engine Architecture v1 under
  `docs/architecture/premarket-scoring-engine-architecture-v1.md`
- Gap conflict scope rationale under
  `docs/architecture/premarket-scoring-gap-conflict-scope.md`

Those documents were merged with PR #79. This closeout does not modify them.

This closeout does not authorize Morning Briefing, Human Review Workflow, UI
integration, HTTP APIs, persistence, workers, live providers, or AI Decision
Engine work.

## Completion evidence

- Implementation issue documentation exists under `docs/sprints/sprint-8/`.
- PR #79 merged Premarket Scoring Foundation to `main`
  (`dedccab35d3238f6cc9840689ca61a99cc454ce6`).
- Issue #78 is closed through PR #79 (`Closes #78`).
- Scoring package, tests, and authoritative governance/policy/architecture
  documents are present on `main`.
- This closeout changes only documentation and release-governance artifacts.
- `ROADMAP.md` records Sprint 8 as Premarket Scoring Foundation and complete.

Detailed mapping is maintained in [`README.md`](README.md).

## Delivered architecture summary

- Premarket Scoring Engine under `apps/api/app/premarket/scoring/`.
- Watchlist / Catalyst / Gap integration under Policy Version
  `premarket.scoring.policy.v1`.
- Decimal-only scoring; Weight Profile `default_v1`.
- Deterministic identity (`premarket.score.identity.v1`), provenance, and
  ordering with tie-break.
- PIT-safe replay helpers and fail-closed validation boundaries.
- Unit, contract, and integration tests; Makefile target
  `test-api-premarket-scoring` (included in `test-api-premarket`).
- Evaluation-scoped Gap duplicate/conflict abort under documented v1 behavior
  (`docs/architecture/premarket-scoring-gap-conflict-scope.md`).

## Compatibility and operational impact

- Breaking changes to Strategy SDK public API: none.
- Market Data contracts: unchanged by Sprint 8 scoring.
- Feature Platform: no redesign.
- Premarket settings fail closed when supplied and disabled.
- Live trading: not enabled.
- This closeout itself does not change runtime code.

## Validation evidence (authorized implementation)

Commands and outcomes recorded in PR #79 and re-verified during local merge
readiness / hygiene validation for that PR:

```bash
make lint                                    # PASS
make typecheck                               # PASS
make validate-secrets                        # PASS
make test-api-premarket-scoring              # 51 passed
make test-api-premarket                      # 117 passed
make test-api-feature-platform               # 29 passed
make test-api-strategy-sdk                   # 85 passed
make test-api-strategy-engine                # 54 passed
git diff --check                             # PASS
```

Evidence origin: PR #79 body and local validation records associated with that
merge. This closeout does not invent GitHub CI status checks. No dedicated
`gate-sprint8` target exists in the repository. This closeout does not invent
one.

## Known limitations

- No Premarket Scoring HTTP APIs, persistence, workers, or UI.
- No live providers or live trading enablement.
- No Morning Briefing, Human Review Workflow, or AI Decision Engine.
- Process-global binder registry overrides are single-threaded only
  (documented on `override_binder_registry`).
- Gap conflict remains evaluation-scoped under documented Policy Version v1
  runtime behavior.

## Scope classification

| Item | Status |
| --- | --- |
| Governance Decisions #1–#12 | COMPLETE |
| Policy Version v1 | COMPLETE |
| Premarket Scoring Engine Architecture v1 | COMPLETE |
| Premarket Scoring Foundation (Issue #78) | COMPLETE |
| Watchlist / Catalyst / Gap scoring integration | COMPLETE |
| Deterministic replay / PIT / identity / provenance / ordering | COMPLETE |
| Unit / contract / integration tests | COMPLETE |
| Morning Briefing | OUT OF SCOPE |
| Human Review Workflow | OUT OF SCOPE |
| AI Decision Engine | OUT OF SCOPE (deferred future work) |
| HTTP / persistence / workers / UI / live providers | OUT OF SCOPE |

## Risks

| Risk | Mitigation |
| --- | --- |
| Scope expands into briefing / review / Decision Engine | Explicit Issue #78 non-goals and this closeout |
| Accidental Premarket enablement | Settings fail-closed when supplied and disabled |
| SDK / Market Data / Feature Platform drift | Contract boundaries; no public SDK / MD / FP redesign |
| Premature Decision Engine or Sprint 9 start | Not authorized by this closeout |

## Rollback

This closeout contains governance documentation only. If correction is needed,
revert the closeout commit before relying on the Sprint 8 release tag.
Reverting these documents does not roll back Premarket Scoring application
code.

To roll back Premarket Scoring implementation code, revert or follow-up-fix
the implementation merge commit through normal repository change control —
outside this documentation-only closeout:

- Premarket Scoring Foundation: `dedccab35d3238f6cc9840689ca61a99cc454ce6`
  (PR #79)

No schema or migration rollback is required because Sprint 8 introduced no
persistence or migrations.

## Release

The prepared Sprint 8 release tag is:

```text
v0.8.0-sprint8
```

Tag and GitHub Release creation are **not** performed by this documentation
commit. Create them only after:

1. This closeout commit is on `main`.
2. Local `main` is clean and equals `origin/main`.
3. Explicit approval to tag has been given.

Release baseline SHA for tagging is the implementation merge commit above
(or the closeout merge commit on `main` once this package is merged, if
maintainers choose the post-closeout tip). The implementation baseline remains
`dedccab35d3238f6cc9840689ca61a99cc454ce6`.

## Explicit exclusions

- Morning Briefing generation and API
- Human-review workflow
- UI integration
- Live market-data providers / polling / streaming workers
- Premarket Scoring persistence and database migrations
- Premarket Scoring HTTP APIs
- AI Decision Engine
- Production deployment claims
- SBOM / checksum / release manifests (not present for Sprint 8)

## Repository state at closeout preparation

- Implementation baseline (final merge):
  `dedccab35d3238f6cc9840689ca61a99cc454ce6`
- Sprint 8 feature branch removed after merge
- Sprint 8 milestone remains open until maintainers close it after closeout
  merge (not closed by this documentation commit)
- No Sprint 9 implementation issue, branch, or PR is created by this closeout

## Next work

1. Merge this Sprint 8 governance closeout package to `main`.
2. Create release tag / GitHub Release `v0.8.0-sprint8` after approval.
3. Close the Sprint 8 milestone after closeout merge.
4. Next planning gate remains pending and is not authorized by this closeout.

See also: [`docs/sprints/sprint-7/CLOSEOUT.md`](../sprint-7/CLOSEOUT.md) and
[`ROADMAP.md`](../../../ROADMAP.md).
