# Sprint 8 Release Notes

## Theme

Premarket Scoring Foundation

## Completed

- Governance Decisions #1–#12 (`docs/governance/`)
- Policy Version v1 (`docs/policy/premarket-scoring-policy-v1.md`)
- Premarket Scoring Engine Architecture v1
  (`docs/architecture/premarket-scoring-engine-architecture-v1.md`)
- Deterministic scoring pipeline under `apps/api/app/premarket/scoring/`
- Watchlist / Catalyst / Gap integration under Policy Version
  `premarket.scoring.policy.v1`
- Decimal-only scoring with Weight Profile `default_v1` and quantize policy
  `decimal_8dp_half_even`
- Deterministic identity (`premarket.score.identity.v1`)
- Provenance fingerprints and source identifiers
- Deterministic ordering and tie-breaks
  (`score_desc_instrument_key_asc_score_record_id_asc`)
- PIT-safe replay with explicit UTC `as_of`
- Unit / contract / integration coverage
- Issue #78 / PR #79 merge commit:
  `dedccab35d3238f6cc9840689ca61a99cc454ce6`

## Safety and Defaults

- Premarket settings fail closed when supplied and disabled
- no live execution enablement
- no Strategy SDK public API expansion
- no Market Data contract changes
- no Feature Platform redesign

## Validation evidence

Evidence recorded in PR #79 and local validation records for that merge:

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

No GitHub CI status checks are claimed by this document.

## Breaking Changes

None to frozen Strategy SDK public API or Market Data contracts

## Backward Compatibility

Maintained for Strategy SDK and Market Data surfaces consumed by Premarket
Scoring. Feature Platform contracts were not redesigned.

## Known Limitations

- no HTTP/API
- no persistence
- no workers
- no UI
- no live providers
- no Morning Briefing
- no Human Review
- no AI Decision Engine
- binder registry override not concurrency-safe for multi-threaded use
- Gap conflict remains evaluation-scoped under documented v1 behavior

## Risks

| Risk | Mitigation |
| --- | --- |
| Scope expands into briefing / review / Decision Engine | Explicit Issue #78 non-goals and Sprint 8 closeout |
| Default-on Premarket | Settings fail-closed when supplied and disabled |
| Premature Decision Engine start | Not authorized by Sprint 8 closeout |

## Rollback

Revert the Sprint 8 closeout and implementation merge commits according to
repository history; no schema or migration rollback is required because Sprint
8 introduced no persistence or migrations.

Implementation merge commit:

```text
dedccab35d3238f6cc9840689ca61a99cc454ce6
```

## Explicit exclusions

- Morning Briefing
- Human Review Workflow
- UI
- Live providers / workers / Premarket Scoring persistence
- Premarket Scoring HTTP APIs
- AI Decision Engine
- Production deployment
- SBOM / checksum / release manifests

## References

- Final implementation merge:
  `dedccab35d3238f6cc9840689ca61a99cc454ce6`
- Issue: #78
- PR: https://github.com/enesdedelerr-max/Bergama/pull/79
