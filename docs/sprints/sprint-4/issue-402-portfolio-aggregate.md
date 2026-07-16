# Sprint 4 — Issue #402 — Portfolio Aggregate Foundation

## Scope

Issue #402 adds the Portfolio Aggregate foundation for deterministic portfolio state transitions.

The service accepts typed commands that pair expected-version CAS metadata with
domain mutations:

- `FillAppliedCommand`
- `CashAdjustmentCommand`
- `MarkPriceUpdateCommand`

The aggregate receives only domain mutations:

- `FillApplied`
- `CashAdjustment`
- `MarkPriceUpdate`

It produces immutable `PortfolioMutationResult`, `LedgerEntry`, and
`PortfolioSnapshot` models through a pure `PortfolioAggregate` and an
orchestration-only `PortfolioService`. `expected_version` belongs only to
service/repository compare-and-commit orchestration and never reaches aggregate
accounting logic.

## Safety Boundary

The portfolio foundation does not create orders, approve risk, call brokers, fetch market data, publish Kafka events, persist to a database, or mutate strategy state.

`strategy_allocation_id`, `strategy_decision_id`, and `order_reference` are provenance only. They do not create accounting buckets and do not affect position identity.

## Accounting Policy

The initial accounting policy is average cost only:

- positive position quantity is long,
- negative position quantity is short,
- buy fills add positive signed quantity,
- sell fills add negative signed quantity,
- every successful mutation increments `portfolio_version` exactly once,
- one summary ledger entry is emitted per successful mutation.

Default policy:

- short positions disabled,
- non-negative cash not enforced,
- single base currency,
- FX conversion, margin, settlement, tax lots, and derivatives out of scope.

Fee policy:

- opening or increasing a long includes buy fees in average cost,
- covering a short deducts buy fees from close economics,
- closing a long deducts sell fees from realized P&L,
- opening or increasing a short leaves average cost at fill price while fees affect cash and `fees_total`.

## Determinism

The aggregate is domain-only and has no repository, clock, logger, network, filesystem, provider, broker, Kafka, database, strategy, or risk dependencies.

Snapshot hashes are computed from approved business state only: base currency,
cash, ordered positions, realized and unrealized P&L, fees, exposure fields,
portfolio version, and policy fingerprint. They exclude snapshot time,
account/portfolio identity, safe metadata, provenance, idempotency keys, runtime
state, random IDs, unordered containers, and object identity.

Ledger IDs use deterministic UTF-8 input:

```text
portfolio-ledger-entry:v1
{portfolio_id}
{portfolio_version}
{event_id}
{entry_index}
```

`entry_index` starts at `0` and entries are emitted in ascending order.

The in-memory repository provides process-local idempotency and atomic compare-and-commit semantics for tests and local runtime composition. It does not claim cross-process exactly-once guarantees.

## Validation

Focused target:

```bash
make test-api-portfolio-service
```

Regression targets for final validation include:

```bash
make lint
make typecheck
make validate-secrets
make test-api-portfolio-service
make test-api-strategy-engine
make test-api
make test-sprint3-gate
git diff --check
```

Do not run the full Sprint 3 release gate while the #402 feature tree is uncommitted.
