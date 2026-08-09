# Sprint 10 — Dashboard Foundation

## Summary

Sprint 10 delivered Dashboard Foundation: a deterministic, read-only
presentation bounded context that consumes approved Morning Briefing public
outputs only.

Implementation issue [#85](https://github.com/enesdedelerr-max/Bergama/issues/85)
is CLOSED / COMPLETED. Implementation PR
[#86](https://github.com/enesdedelerr-max/Bergama/pull/86) is MERGED.
Implementation baseline / rollback reference:

```text
c87b1afdca60f0eb4c734c75ed1aeba71de69646
```

## Completed Work

- separate Dashboard bounded context under `apps/api/app/dashboard/`
- immutable Dashboard contracts
- deterministic 13-stage Presentation Pipeline
- read-only Morning Briefing public-output consumption
- exact upstream ordering preservation
- Dashboard identity (`dashboard.identity.v1`)
- Dashboard provenance (`dashboard.provenance.v1`)
- PIT validation and deterministic replay
- fail-closed typed errors
- unit / contract / integration coverage
- Makefile target `test-api-dashboard`
- Issue #85 / PR #86 merge commit:
  `c87b1afdca60f0eb4c734c75ed1aeba71de69646`

## Architecture / Governance / Policy

- Sprint 10 Planning Gate (`docs/sprints/sprint-10/planning-gate.md`) — APPROVED
- Dashboard Architecture v1
  (`docs/architecture/dashboard-architecture-v1.md`) — APPROVED
- Governance Decisions #1–#8 (`docs/governance/dashboard/`) — RESOLVED
- Policy Version `dashboard.policy.v1`
  (`docs/policy/dashboard-policy-v1.md`) — APPROVED
- Dashboard Implementation Authorization v1
  (`docs/sprints/sprint-10/implementation-authorization-v1.md`) — APPROVED

Upstream Morning Briefing Policy Version `morning-briefing.policy.v1` remains
immutable. Premarket Scoring Policy Version `premarket.scoring.policy.v1`
remains immutable and is not consumed directly.

## Dashboard Foundation Behavior

- Presentation-only; no scoring, briefing regeneration, review, decision, or
  execution authority
- Include all Morning Briefing records (`include_all_morning_briefing_records.v1`)
- Preserve exact upstream sequence (`preserve_morning_briefing_order.v1`)
- `sequence_index` equals upstream zero-based position
- No filter, sort, pagination, truncation, dedupe, aggregation, inference,
  independent ranking, or new tie-break

## Determinism / PIT / Replay

- Explicit timezone-aware UTC `as_of` under `utc_aware_instant_v1`
- Naive `as_of` fail-closed; fixed-offset equal instant accepted
- Cross-`as_of` fail-closed; no wall-clock fallback
- Replay equality is full structural equality
  (`replay_equality.structural_complete.v1`)
- Replay inequality fail-closed with typed error
- Decimal score references only; finite `[0,1]`; `-0` canonicalized to
  `Decimal("0")`; no clamp

## Identity / Provenance

- Deterministic SHA-256 identity (`dashboard.identity.v1`,
  `canonical_payload_sha256_v1`)
- 64 lowercase hex; no UUID, randomness, or wall-clock
- Provenance carries Policy IDs, `as_of`, config/input fingerprints, ordered
  source identifiers, and upstream Morning Briefing identity/provenance linkage
- No fabricated, omitted, or rewritten lineage

## Ordering Preservation

Equal-score inputs and reversed upstream inputs remain in exact Morning
Briefing order. Dashboard does not re-rank.

## Testing / Validation

Repository/local validation results on `main` at implementation baseline
`c87b1afdca60f0eb4c734c75ed1aeba71de69646`. No GitHub CI status checks are
claimed by this document.

```bash
make lint                                    # PASS
make typecheck                               # PASS (393 source files)
make validate-secrets                        # PASS (error_count: 0)
make test-api-dashboard                      # 40 passed
make test-api-premarket                      # 149 passed
make test-api-feature-platform               # 29 passed
make test-api-strategy-sdk                   # 85 passed
make test-api-strategy-engine                # 54 passed
git diff --check                             # PASS
ruff                                         # PASS
mypy apps/api/app/dashboard                  # PASS (13 source files)
```

## Breaking Changes

None. Frozen Strategy SDK public API, Market Data contracts, Feature Platform,
Morning Briefing, and Premarket Scoring surfaces were not redesigned.

## Known Limitations

- no concrete Dashboard UI / product surface
- no HTTP / API
- no persistence / database
- no workers / schedulers
- no notifications
- no authentication / authorization productization

## Explicit Exclusions

- Human Review
- AI Decision Engine
- Broker Execution
- Portfolio Management
- Risk Engine
- direct Premarket Scoring input
- Market Data redesign
- Feature Platform redesign
- Strategy SDK redesign
- Morning Briefing redesign
- production deployment

## Risks

| Risk | Mitigation |
| --- | --- |
| Scope expands into UI / review / Decision Engine / Broker Execution | Explicit Issue #85 non-goals and Sprint 10 closeout |
| Accidental score or order mutation | Policy Version v1 include-all + exact upstream order |
| Premature next-theme start | Not authorized; new Planning Gate required |

This package does not claim production deployment readiness.

## Rollback

Revert the Sprint 10 closeout and, if required, the implementation merge
commit according to repository history. No schema or migration rollback is
required because Sprint 10 introduced no persistence or migrations.

Implementation baseline / rollback reference:

```text
c87b1afdca60f0eb4c734c75ed1aeba71de69646
```

Do not rewrite frozen Governance, Policy, or Architecture when rolling back.

## Release Readiness

Prepared release tag:

```text
v0.10.0-sprint10
```

Status: **PREPARED** / **NOT RELEASED**.

Preferred tag target: the final Sprint 10 closeout merge tip on `main`, not
`c87b1afdca60f0eb4c734c75ed1aeba71de69646`.

Create only after closeout merge to `main` and explicit maintainer approval.
Sprint 10 milestone remains **OPEN** until closeout merge, tag creation, and
GitHub Release publication. GitHub Release is **NOT PUBLISHED**.

This document does not mention production deployment as completed.

## References

- Final implementation merge:
  `c87b1afdca60f0eb4c734c75ed1aeba71de69646`
- Issue: #85
- PR: https://github.com/enesdedelerr-max/Bergama/pull/86
