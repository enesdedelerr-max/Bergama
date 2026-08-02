# Sprint 9 Release Notes

## Theme

Morning Briefing Foundation

## Completed

- Sprint 9 Planning Gate (`docs/sprints/sprint-9/planning-gate.md`)
- Morning Briefing Architecture v1
  (`docs/architecture/morning-briefing-architecture-v1.md`)
- Governance Decisions #1–#8 (`docs/governance/morning-briefing/`)
- Policy Version v1 (`docs/policy/morning-briefing-policy-v1.md`)
- Implementation Authorization v1
  (`docs/sprints/sprint-9/implementation-authorization-v1.md`)
- Deterministic Morning Briefing package under
  `apps/api/app/premarket/morning_briefing/`
- Read-only Premarket Scoring consumption under Policy Version
  `morning-briefing.policy.v1`
- Exact score-order preservation
  (`preserve_premarket_scoring_order.v1`)
- Deterministic identity (`morning-briefing.identity.v1`)
- Deterministic provenance (`morning-briefing.provenance.v1`)
- Digest method `canonical_payload_sha256_v1`
- PIT-safe replay with explicit UTC `as_of`
- Immutable contracts and Premarket `BRIEFING_*` exports
- Unit / contract / integration coverage
- Issue #82 / PR #83 merge commit:
  `a713bea13b352f35a9390f68ce43081b68587eb9`

## Safety and Defaults

- Premarket settings fail closed when supplied and disabled
- no live execution enablement
- no Strategy SDK public API expansion
- no Market Data contract changes
- no Feature Platform redesign
- Premarket Scoring Foundation remains frozen

## Validation evidence

Evidence recorded in PR #83 and local validation records for that merge:

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

No GitHub CI status checks are claimed by this document.

## Breaking Changes

None to frozen Strategy SDK public API or Market Data contracts

## Backward Compatibility

Maintained for Strategy SDK and Market Data surfaces. Feature Platform
contracts were not redesigned. Premarket Scoring public contracts remain
immutable upstream inputs to Morning Briefing.

## Known Limitations

- no HTTP/API
- no persistence
- no workers / schedulers
- no UI
- no notifications
- no Dashboard
- no Human Review
- no AI Decision Engine
- no Broker Execution
- no independent re-ranking or new score tie-breaks

## Risks

| Risk | Mitigation |
| --- | --- |
| Scope expands into Dashboard / review / Decision Engine / Broker Execution | Explicit Issue #82 non-goals and Sprint 9 closeout |
| Default-on Premarket | Settings fail-closed when supplied and disabled |
| Premature Dashboard or next-theme start | Not authorized by Sprint 9 closeout |

## Rollback

Revert the Sprint 9 closeout and implementation merge commits according to
repository history; no schema or migration rollback is required because Sprint
9 introduced no persistence or migrations.

Implementation merge commit:

```text
a713bea13b352f35a9390f68ce43081b68587eb9
```

## Explicit exclusions

- Dashboard
- Human Review Workflow
- UI
- Notifications
- Workers / schedulers / Morning Briefing persistence
- Morning Briefing HTTP APIs
- Broker Execution
- AI Decision Engine
- Premarket Scoring redesign
- Feature Platform / Market Data / Strategy SDK expansion
- Production deployment
- SBOM / checksum / release manifests

## Release readiness

Prepared release tag:

```text
v0.9.0-sprint9
```

Status: **PREPARED**, **NOT CREATED**. Create only after closeout merge to
`main` and explicit maintainer approval. Sprint 9 milestone remains open until
maintainers close it after closeout merge.

## References

- Final implementation merge:
  `a713bea13b352f35a9390f68ce43081b68587eb9`
- Issue: #82
- PR: https://github.com/enesdedelerr-max/Bergama/pull/83
