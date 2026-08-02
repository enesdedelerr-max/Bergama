# Sprint 9 Governance Closeout

## Decision

Sprint 9 is complete.

The approved Sprint 9 theme is **Morning Briefing Foundation**. Authorized
implementation scope is Issue **#82**, merged through PR **#83**. The final
implementation merge commit is:

```text
a713bea13b352f35a9390f68ce43081b68587eb9
```

Planning / governance baseline for this sprint is repository-backed as:

- Sprint 9 Planning Gate under `docs/sprints/sprint-9/planning-gate.md`
- Morning Briefing Architecture v1 under
  `docs/architecture/morning-briefing-architecture-v1.md`
- Governance Decisions #1–#8 under `docs/governance/morning-briefing/`
- Policy Version v1 under `docs/policy/morning-briefing-policy-v1.md`
- Implementation Authorization v1 under
  `docs/sprints/sprint-9/implementation-authorization-v1.md`
- Upstream Premarket Scoring Policy Version `premarket.scoring.policy.v1`
  (immutable)

Those documents were merged with PR #83. This closeout does not modify them.

This closeout does not authorize Dashboard, Human Review Workflow, UI
integration, HTTP APIs, persistence, workers, schedulers, notifications,
Broker Execution, or AI Decision Engine work.

## Completion evidence

- Implementation issue documentation exists under `docs/sprints/sprint-9/`.
- PR #83 merged Morning Briefing Foundation to `main`
  (`a713bea13b352f35a9390f68ce43081b68587eb9`).
- Issue #82 is closed through PR #83 (`Closes #82`).
- Morning Briefing package, tests, and authoritative
  planning/architecture/governance/policy/authorization documents are present
  on `main`.
- This closeout changes only documentation and release-governance artifacts.
- `ROADMAP.md` records Sprint 9 as Morning Briefing Foundation and complete.

Detailed mapping is maintained in [`README.md`](README.md).

## Delivered architecture summary

- Morning Briefing Engine under `apps/api/app/premarket/morning_briefing/`.
- Read-only Premarket Scoring consumption under Policy Version
  `morning-briefing.policy.v1`.
- Exact score-order preservation under
  `preserve_premarket_scoring_order.v1`.
- Deterministic identity (`morning-briefing.identity.v1`), provenance
  (`morning-briefing.provenance.v1`), and digest method
  `canonical_payload_sha256_v1`.
- PIT-safe replay helpers and fail-closed validation boundaries.
- Immutable contracts and Premarket `BRIEFING_*` public exports.
- Unit, contract, and integration tests; Makefile target
  `test-api-premarket-morning-briefing` (included in `test-api-premarket`).

## Compatibility and operational impact

- Breaking changes to Strategy SDK public API: none.
- Market Data contracts: unchanged by Sprint 9 Morning Briefing.
- Feature Platform: no redesign.
- Premarket Scoring Foundation: frozen; not redesigned.
- Premarket settings fail closed when supplied and disabled.
- Live trading: not enabled.
- This closeout itself does not change runtime code.

## Validation evidence (authorized implementation)

Commands and outcomes recorded in PR #83 and re-verified during local merge
readiness / hygiene validation for that PR:

```bash
make lint                                    # PASS
make typecheck                               # PASS
make validate-secrets                        # PASS
make test-api-premarket-morning-briefing     # 32 passed
make test-api-premarket-scoring              # 51 passed
make test-api-premarket                      # 149 passed
make test-api-feature-platform               # 29 passed
make test-api-strategy-sdk                   # 85 passed
make test-api-strategy-engine                # 54 passed
git diff --check                             # PASS
```

Evidence origin: PR #83 body and local validation records associated with that
merge. This closeout does not invent GitHub CI status checks. No dedicated
`gate-sprint9` target exists in the repository. This closeout does not invent
one.

## Known limitations

- No Morning Briefing HTTP APIs, persistence, workers, schedulers, or UI.
- No notifications or notification providers.
- No live providers or live trading enablement.
- No Dashboard, Human Review Workflow, Broker Execution, or AI Decision Engine.
- Morning Briefing preserves Premarket Scoring order exactly and does not
  independently re-rank or invent tie-breaks.

## Scope classification

| Item | Status |
| --- | --- |
| Sprint 9 Planning Gate | COMPLETE |
| Morning Briefing Architecture v1 | COMPLETE |
| Governance Decisions #1–#8 | COMPLETE |
| Policy Version `morning-briefing.policy.v1` | COMPLETE |
| Implementation Authorization v1 | COMPLETE |
| Morning Briefing Foundation (Issue #82) | COMPLETE |
| Deterministic replay / PIT / identity / provenance / ordering | COMPLETE |
| Unit / contract / integration tests | COMPLETE |
| Dashboard | OUT OF SCOPE (deferred future work) |
| Human Review Workflow | OUT OF SCOPE |
| AI Decision Engine | OUT OF SCOPE (deferred future work) |
| Broker Execution | OUT OF SCOPE |
| HTTP / persistence / workers / schedulers / UI / notifications | OUT OF SCOPE |

## Risks

| Risk | Mitigation |
| --- | --- |
| Scope expands into Dashboard / review / Decision Engine / Broker Execution | Explicit Issue #82 non-goals and this closeout |
| Accidental Premarket enablement | Settings fail-closed when supplied and disabled |
| SDK / Market Data / Feature Platform / Scoring drift | Contract boundaries; no public SDK / MD / FP / Scoring redesign |
| Premature Dashboard or next-theme start | Not authorized by this closeout |

## Rollback

This closeout contains governance documentation only. If correction is needed,
revert the closeout commit before relying on the Sprint 9 release tag.
Reverting these documents does not roll back Morning Briefing application
code.

To roll back Morning Briefing implementation code, revert or follow-up-fix
the implementation merge commit through normal repository change control —
outside this documentation-only closeout:

- Morning Briefing Foundation: `a713bea13b352f35a9390f68ce43081b68587eb9`
  (PR #83)

No schema or migration rollback is required because Sprint 9 introduced no
persistence or migrations.

## Release

The prepared Sprint 9 release tag is:

```text
v0.9.0-sprint9
```

Tag and GitHub Release creation are **not** performed by this documentation
commit. The tag is **PREPARED** and **NOT CREATED**. Create them only after:

1. This closeout commit is on `main`.
2. Local `main` is clean and equals `origin/main`.
3. Explicit approval to tag has been given.

Release baseline SHA for tagging is the implementation merge commit above
(or the closeout merge commit on `main` once this package is merged, if
maintainers choose the post-closeout tip). The implementation baseline remains
`a713bea13b352f35a9390f68ce43081b68587eb9`.

## Explicit exclusions

- Dashboard productization
- Human-review workflow
- UI integration
- Notifications / notification providers
- Live market-data providers / polling / streaming workers / schedulers
- Morning Briefing persistence and database migrations
- Morning Briefing HTTP APIs
- Broker Execution
- AI Decision Engine
- Premarket Scoring redesign
- Feature Platform / Market Data / Strategy SDK expansion
- Production deployment claims
- SBOM / checksum / release manifests (not present for Sprint 9)

## Repository state at closeout preparation

- Implementation baseline (final merge):
  `a713bea13b352f35a9390f68ce43081b68587eb9`
- Sprint 9 feature branch removed after merge
- Sprint 9 milestone remains open until maintainers close it after closeout
  merge (not closed by this documentation commit)
- No Dashboard, Human Review, AI Decision Engine, or Broker Execution
  implementation issue, branch, or PR is created by this closeout

## Next work

1. Merge this Sprint 9 governance closeout package to `main`.
2. Create release tag / GitHub Release `v0.9.0-sprint9` after approval.
3. Close the Sprint 9 milestone after closeout merge.
4. Next planning gate remains pending and is not authorized by this closeout.

Downstream sequencing recorded by Sprint 9 Planning Gate (not authorized here):

```text
Premarket Scoring → Morning Briefing → Dashboard → Human Review → AI Decision Engine
```

See also: [`docs/sprints/sprint-8/CLOSEOUT.md`](../sprint-8/CLOSEOUT.md) and
[`ROADMAP.md`](../../../ROADMAP.md).
