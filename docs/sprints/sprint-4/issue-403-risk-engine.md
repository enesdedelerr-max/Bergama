# Sprint 4 — Issue #403 — Risk Engine Implementation

## Scope

Issue #403 adds a pure, deterministic, side-effect-free Risk Engine.

Inputs:

- sized `ProposedTradeIntent`
- immutable `PortfolioSnapshot`
- immutable `RiskPolicy`
- injected evaluation time

Output:

- immutable `RiskAssessment`

The engine evaluates only. It does not size or resize trades, generate orders,
mutate Portfolio or Strategy state, call brokers, fetch market data, or perform
Kafka, database, filesystem, or network I/O.

## Safety Boundary

`StrategyDecision` may appear only as provenance on the intent. Executable
quantity comes exclusively from `ProposedTradeIntent`. Risk never changes,
proposes, or returns a reduced quantity.

Final actions are only:

- `APPROVE`
- `REJECT`
- `HALT`

There is no `REDUCE` / resize path.

`expected_portfolio_version` is validation-only. A mismatch yields
`risk.portfolio_version_mismatch` and `REJECT`. It never mutates Portfolio,
reserves state, retries newer snapshots, or increments versions.

`HALT` is reserved for kill switch (and reserved corrupted/untrusted-snapshot /
mandatory-stop cases). Version mismatch defaults to `REJECT`.

## Rule Order

Order is locked by tests and must never change:

1. Intent validation
2. Policy / currency compatibility
3. Portfolio version
4. Kill switch
5. Snapshot freshness
6. Mark freshness
7. Shorting policy
8. Order notional
9. Resulting position notional
10. Gross exposure
11. Net exposure
12. Concentration

Short-circuit behavior:

- invalid intent → remaining rules `SKIPPED`
- kill switch → `HALT`, remaining rules `SKIPPED`
- missing/stale mark → price-dependent exposure rules `SKIPPED`

Rule results use `PASS` / `FAIL` / `SKIPPED` (never bool-only).

## Determinism

- Policy fingerprint: canonical JSON of business fields only (SHA-256).
- Assessment ID: SHA-256 over intent, portfolio version, policy fingerprint,
  normalized quantity/price/currency, and rule-set version. No UUIDs.
- Assessment hash: ordered rule results, final action, identity, policy
  fingerprint, and normalized business facts. Excludes `evaluated_at`,
  safe metadata, wall clock, and random IDs.

Same intent + snapshot + policy + rule-set version → same `assessment_id`.
Same assessment business facts → same `assessment_hash`.

## Lifecycle

Disabled by default via `BERGAMA_RISK__*`. Container constructs the engine only
when enabled or injected. No startup evaluation. `close()` is idempotent.
Evaluate-after-close raises `RiskClosedError`.

Downstream boundary is protocol-only (`RiskAssessmentSink` /
`RiskDecisionPort`). No Kafka or persistence adapter in this issue.

## Out of Scope

OMS, Execution, Orders, Broker, Portfolio mutation, Strategy mutation, Kafka,
database, filesystem, Iceberg, market-data fetching, sizing optimizer, margin,
VaR, Greeks, options, FX conversion, historical drawdown, alerting, UI, and
Issue #404+.
