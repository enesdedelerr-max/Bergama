# Sprint 7 Governance Closeout

## Decision

Sprint 7 is complete.

The approved Sprint 7 theme is **Premarket Intelligence**. Planning is Issue
**#71**. Authorized implementation scope is Issues **#72**, **#74**, and
**#76**, merged through PRs **#73**, **#75**, and **#77**. The final
implementation merge commit is:

```text
3b8358e728555bc17da87786b3a2f41792559433
```

This closeout does not authorize Premarket Scoring, Morning Briefing, Human
Review Workflow, UI integration, or Sprint 8 AI Decision Engine work.

## Completion evidence

- Planning and implementation issues are documented under
  `docs/sprints/sprint-7/`.
- PR #73 merged Watchlist Engine Foundation to `main`
  (`02bf9afe6e3a0a49c0e8758ac57d65e05a30e7d5`).
- PR #75 merged Catalyst Ingestion and Normalization Foundation to `main`
  (`05f38e841972793b4111fa1a165922dab81e925a`).
- PR #77 merged Gap Scanner Foundation to `main`
  (`3b8358e728555bc17da87786b3a2f41792559433`).
- Issues #71, #72, #74, and #76 are closed.
- This closeout changes only documentation and release-governance artifacts.
- `ROADMAP.md` records Sprint 7 as Premarket Intelligence and complete.

Detailed mapping is maintained in [`README.md`](README.md).

## Delivered architecture summary

- Premarket Watchlist Engine under `apps/api/app/premarket/watchlist/`.
- Premarket Catalyst normalization under `apps/api/app/premarket/catalyst/`.
- Premarket Gap Scanner under `apps/api/app/premarket/gap/`.
- Shared Premarket settings remain disabled by default (`enabled=False`).
- Inputs remain offline / injected Market Data contracts and explicit
  configuration; no live provider workers in these foundations.

## Compatibility and operational impact

- Breaking changes to Strategy SDK public API: none.
- Market Data contracts: unchanged by Sprint 7 foundations.
- Premarket disabled by default; fail-closed when settings are supplied and
  disabled.
- Live trading: not enabled.
- This closeout itself does not change runtime code.

## Validation evidence (authorized implementation slices)

Commands recorded as required by Sprint 7 issue documents and previously
executed for the Gap Scanner Foundation merge readiness review (PR #77):

```bash
make lint
make typecheck
make validate-secrets
make test-api-premarket-gap
make test-api-premarket
make test-api-feature-platform
make test-api-strategy-sdk
make test-api-strategy-engine
git diff --check
```

No dedicated `gate-sprint7` target exists in the repository. This closeout does
not invent one.

## Known limitations

- Two-bar Gap selection policy is not exchange-calendar or RTH-aware.
- Catalyst join into Gap scoring is not implemented.
- Premarket Scoring, Morning Briefing, and Human Review remain deferred per
  Issue #71.
- UI remains out of scope per Issue #71.
- No Premarket HTTP APIs, workers, persistence, or live providers were added
  for the authorized foundation slices.

## Deferred work (Issue #71)

Exactly as recorded in the Sprint 7 Gap Scanner planning amendment on Issue
#71:

| Slice | Status |
| --- | --- |
| Watchlist Engine Foundation | COMPLETE |
| Catalyst Foundation | COMPLETE |
| Gap Scanner | COMPLETE (authorized and merged) |
| Premarket Scoring | DEFERRED |
| Morning Briefing | DEFERRED |
| Human Review Workflow | DEFERRED |
| UI | OUT OF SCOPE |

## Risks

| Risk | Mitigation |
| --- | --- |
| Scope expands into scoring / briefing / UI | Explicit Issue #71 deferrals and this closeout |
| Accidental Premarket default enablement | Settings default `enabled=False`; fail-closed |
| SDK or Market Data contract drift | Contract tests; no `__all__` / MD contract changes |
| Premature Sprint 8 Decision Engine work | Not authorized by this closeout |

## Rollback

This closeout contains governance documentation only. If correction is needed,
revert the closeout commit before relying on the Sprint 7 release tag.
Reverting these documents does not roll back Premarket application code.

To roll back Premarket implementation code, revert or follow-up-fix the
relevant merge commits through normal repository change control — outside this
documentation-only closeout:

- Watchlist: `02bf9afe6e3a0a49c0e8758ac57d65e05a30e7d5` (PR #73)
- Catalyst: `05f38e841972793b4111fa1a165922dab81e925a` (PR #75)
- Gap Scanner: `3b8358e728555bc17da87786b3a2f41792559433` (PR #77)

## Release

The Sprint 7 release tag is:

```text
v0.7.0-sprint7
```

Tag and GitHub Release creation are part of this governance closeout after the
closeout commit is on `main` and local `main` equals `origin/main`.

## Explicit exclusions

- Premarket Scoring
- Morning Briefing generation and API
- Human-review workflow
- UI integration
- Live market-data providers / polling / streaming workers
- Premarket persistence and database migrations
- AI Decision Engine (Sprint 8)

## Repository state at closeout

- Implementation baseline (final merge):
  `3b8358e728555bc17da87786b3a2f41792559433`
- Sprint 7 feature branches removed after merge
- Milestone Sprint 7 closed as part of governance closeout
- No Sprint 8 implementation issue, branch, or PR is created by this closeout

## Next work

Next sprint planning remains pending. This closeout does not authorize Sprint 8
implementation.

See also: [`docs/sprints/sprint-6/CLOSEOUT.md`](../sprint-6/CLOSEOUT.md) and
[`ROADMAP.md`](../../../ROADMAP.md).
