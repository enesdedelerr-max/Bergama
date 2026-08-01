# Sprint 8 — Issue #78 — Premarket Scoring Foundation

GitHub Issue: [#78](https://github.com/enesdedelerr-max/Bergama/issues/78)

## Authorization

- Repository Governance Decisions #1–#12 (immutable): `docs/governance/`
- Policy Version v1 (immutable): `docs/policy/premarket-scoring-policy-v1.md`
- Architecture v1 (immutable): `docs/architecture/premarket-scoring-engine-architecture-v1.md`
- Gap conflict scope rationale:
  `docs/architecture/premarket-scoring-gap-conflict-scope.md`

## Goal

Implement the Premarket Scoring Engine skeleton under Policy Version
`premarket.scoring.policy.v1` as a Premarket-internal deterministic attention /
ordering-priority signal over an approved Watchlist universe.

## Implemented scope

- Package `apps/api/app/premarket/scoring/` including ports, pipeline stages,
  engine entrypoints, replay helpers, and `policy_v1/` binder + Feature Specs
- Immutable contracts: `ScoreRequest`, `ScoreConfig`, `ScoreRecord`,
  `ScoreCollection`, `ScoreProvenance`, `ScoreComponents`
- Weight Profile `default_v1` (`0.50` / `0.30` / `0.20`)
- Feature Specs: `watchlist_rank.v1`, `gap_magnitude.v1`, `catalyst_presence.v1`
- Identity Spec `premarket.score.identity.v1`
- Canonical Catalyst source-identifier ordering (unique ascending) for identity
  and provenance
- Evaluation-scoped Gap duplicate/conflict abort (see gap-conflict scope doc)
- Unit, contract, and integration tests
- Makefile target `test-api-premarket-scoring` (included in `test-api-premarket`)

## Explicit non-goals

- Morning Briefing / Human Review / AI Decision Engine
- HTTP APIs, persistence, workers, UI
- Strategy SDK public API expansion
- Market Data or Feature Platform contract changes
- Live broker / execution integration
- Alternate Policy Versions beyond the v1 binder registry hook

## Validation evidence

```bash
make lint
make typecheck
make validate-secrets
make test-api-premarket-scoring
make test-api-premarket
make test-api-feature-platform
make test-api-strategy-sdk
make test-api-strategy-engine
git diff --check
```

## Known limitations

- Process-global binder registry overrides are single-threaded only
  (documented on `override_binder_registry`; not redesigned here)
- No HTTP/persistence/observability surfaces (Architecture non-goals)

## Rollback boundary

Revert the Premarket Scoring package, Premarket export/error additions,
Makefile scoring targets, scoring tests, and Sprint 8/docs scoring artifacts.
Upstream Watchlist / Catalyst / Gap foundations remain intact.
