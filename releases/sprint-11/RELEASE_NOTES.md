# Sprint 11 — Human Review Foundation

## Summary

Sprint 11 delivered Human Review Foundation: a deterministic, auditable,
human-authority bounded context that consumes approved Dashboard public outputs
only and requires explicit recorded human attestation.

Implementation issue [#89](https://github.com/enesdedelerr-max/Bergama/issues/89)
is CLOSED / COMPLETED. Implementation PR
[#90](https://github.com/enesdedelerr-max/Bergama/pull/90) is MERGED.
Implementation baseline / rollback reference:

```text
baf1ae03312418cfe6a17d8615ccfec62d14f8c0
```

## Completed Work

- separate Human Review bounded context under `apps/api/app/human_review/`
- immutable Human Review contracts
- deterministic 15-stage Human Review Pipeline
- read-only Dashboard public-output consumption
- explicit recorded human attestation admission
- exact upstream ordering preservation
- Human Review identity (`human-review.identity.v1`)
- Human Review provenance (`human-review.provenance.v1`)
- review history binding (`human-review.history.v1`)
- PIT validation and deterministic replay
- fail-closed typed errors
- unit / contract / integration coverage
- Makefile target `test-api-human-review`
- Issue #89 / PR #90 merge commit:
  `baf1ae03312418cfe6a17d8615ccfec62d14f8c0`

## Architecture / Governance / Policy

- Sprint 11 Planning Gate (`docs/sprints/sprint-11/planning-gate.md`) — APPROVED
- Human Review Architecture v1
  (`docs/architecture/human-review-architecture-v1.md`) — APPROVED
- Governance Decisions #1–#8 (`docs/governance/human-review/`) — RESOLVED
- Policy Version `human-review.policy.v1`
  (`docs/policy/human-review-policy-v1.md`) — APPROVED
- Human Review Implementation Authorization v1
  (`docs/sprints/sprint-11/implementation-authorization-v1.md`) — APPROVED

Upstream Dashboard Policy Version `dashboard.policy.v1` remains immutable.
Morning Briefing Policy Version `morning-briefing.policy.v1` and Premarket
Scoring Policy Version `premarket.scoring.policy.v1` remain immutable and are
not consumed directly.

## Human Review Foundation Behavior

- Human-authority bounded context; no scoring, Dashboard regeneration,
  decision, or execution authority
- Explicit recorded attestation required
  (`explicit_human_attestation.recorded_input.v1`)
- Include all Dashboard presentation records
  (`include_all_dashboard_presentation_records.v1`)
- Preserve exact upstream sequence (`preserve_dashboard_order.v1`)
- `sequence_index` equals Dashboard zero-based position
- No filter, sort, pagination, truncation, dedupe, aggregation, inference,
  independent ranking, new tie-break, auto-approve, or auto-reject

## Determinism / PIT / Replay

- Explicit timezone-aware UTC `as_of` under `utc_aware_instant_v1`
- Naive `as_of` fail-closed; fixed-offset equal instant accepted
- Cross-`as_of` fail-closed; no wall-clock fallback
- Replay equality is full structural equality
  (`replay_equality.structural_complete.v1`)
- Replay inequality fail-closed with typed error
- Decimal score references only; finite `[0,1]`; `-0` canonicalized to
  `Decimal("0")`; no clamp

## Identity / Provenance / History

- Deterministic SHA-256 identity (`human-review.identity.v1`,
  `canonical_payload_sha256_v1`)
- 64 lowercase hex; no UUID, randomness, or wall-clock
- Provenance carries Policy IDs, `as_of`, config/input fingerprints, ordered
  source identifiers, Dashboard identity/provenance linkage, and attestation
  fingerprint
- History binding is reconstructable and immutable for the evaluation; no
  persistence or event-sourcing infrastructure
- No fabricated, omitted, or rewritten lineage

## Ordering Preservation

Equal-score inputs and reversed Dashboard inputs remain in exact Dashboard
order. Human Review does not re-rank. Ordering never implies recommendation or
review outcome.

## Testing / Validation

Repository/local validation results on `main` at implementation baseline
`baf1ae03312418cfe6a17d8615ccfec62d14f8c0`. No GitHub CI status checks are
claimed by this document.

```bash
make lint                                    # PASS
make typecheck                               # PASS (407 source files)
make validate-secrets                        # PASS (error_count: 0)
make test-api-human-review                   # 45 passed
make test-api-dashboard                      # 40 passed
make test-api-premarket                      # 149 passed
make test-api-feature-platform               # 29 passed
make test-api-strategy-sdk                   # 85 passed
make test-api-strategy-engine                # 54 passed
git diff --check                             # PASS
ruff                                         # PASS
mypy apps/api/app/human_review               # PASS (14 source files)
```

## Breaking Changes

None. Frozen Strategy SDK public API, Market Data contracts, Feature Platform,
Dashboard, Morning Briefing, and Premarket Scoring surfaces were not redesigned.

## Known Limitations

- no concrete Human Review UI / product surface
- no HTTP / API
- no persistence / database
- no workers / schedulers
- no notifications
- no authentication / authorization productization
- no reviewer-role management
- no workflow engine

## Explicit Exclusions

- AI Decision Engine
- Broker Execution
- Portfolio Management
- Risk Engine
- direct Morning Briefing input
- direct Premarket Scoring input
- Market Data redesign
- Feature Platform redesign
- Strategy SDK redesign
- Dashboard redesign
- Morning Briefing redesign
- Premarket Scoring redesign
- production deployment

## Risks

| Risk | Mitigation |
| --- | --- |
| Scope expands into UI / Decision Engine / Broker Execution | Explicit Issue #89 non-goals and Sprint 11 closeout |
| Fabricated or inferred human authority | Explicit attestation admission; fail-closed human-authority tests |
| Accidental Dashboard order or score mutation | Policy Version v1 include-all + exact upstream order |
| Premature next-theme start | Not authorized; new Planning Gate required |

This package does not claim production deployment readiness.

## Rollback

Revert the Sprint 11 closeout and, if required, the implementation merge
commit according to repository history. No schema or migration rollback is
required because Sprint 11 introduced no persistence or migrations.

Implementation baseline / rollback reference:

```text
baf1ae03312418cfe6a17d8615ccfec62d14f8c0
```

Do not rewrite frozen Governance, Policy, or Architecture when rolling back.

## Release Readiness

Prepared release tag:

```text
v0.11.0-sprint11
```

Status: **PREPARED** / **NOT RELEASED**.

Preferred tag target: the final Sprint 11 closeout merge tip on `main`, not
`baf1ae03312418cfe6a17d8615ccfec62d14f8c0`.

Create only after closeout merge to `main` and explicit maintainer approval.
Sprint 11 milestone remains **OPEN** until closeout merge, tag creation, and
GitHub Release publication. GitHub Release is **NOT PUBLISHED**.

This document does not mention production deployment as completed.

## References

- Final implementation merge:
  `baf1ae03312418cfe6a17d8615ccfec62d14f8c0`
- Issue: #89
- PR: https://github.com/enesdedelerr-max/Bergama/pull/90
