# Sprint 9 — Morning Briefing Foundation


GitHub Issue: [#82](https://github.com/enesdedelerr-max/Bergama/issues/82)
## Authorization

- Sprint 9 Planning Gate
- Morning Briefing Architecture v1
- Morning Briefing Governance Decisions #1–#8
- Morning Briefing Policy Version `morning-briefing.policy.v1`
- Morning Briefing Implementation Authorization v1
- Premarket Scoring Policy Version `premarket.scoring.policy.v1` (immutable upstream)

## Goal

Implement the Morning Briefing Engine as a deterministic, presentation-oriented
Premarket consumer of frozen Premarket Scoring outputs under Policy Version
`morning-briefing.policy.v1`.

## Implemented scope

- Package `apps/api/app/premarket/morning_briefing/`
- Immutable contracts: `BriefingRequest`, `BriefingConfig`, `BriefingRecord`,
  `BriefingCollection`, `BriefingProvenance`
- Assembly Pipeline stages under Policy Version v1
- Identity Spec `morning-briefing.identity.v1`
- Provenance Spec `morning-briefing.provenance.v1`
- Ordering Preservation Policy `preserve_premarket_scoring_order.v1`
- Unit, contract, and integration tests
- Makefile target `test-api-premarket-morning-briefing` (included in
  `test-api-premarket`)

## Explicit non-goals

- Dashboard / UI / HTTP APIs / persistence / notifications
- Human Review / AI Decision Engine / Broker Execution
- Premarket Scoring redesign
- Feature Platform / Market Data / Strategy SDK expansion

## Validation

```bash
make lint
make typecheck
make validate-secrets
make test-api-premarket-morning-briefing
make test-api-premarket
make test-api-premarket-scoring
git diff --check
```

## Rollback boundary

Revert the Morning Briefing package, Premarket export/error additions,
Makefile briefing targets, briefing tests, and Sprint 9 briefing docs.
Upstream Premarket Scoring remains intact.