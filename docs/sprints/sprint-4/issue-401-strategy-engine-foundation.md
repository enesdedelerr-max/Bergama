# Sprint 4 — Issue #401 Strategy Engine Foundation

## Scope

Issue #401 establishes an infrastructure-neutral Strategy Engine boundary:

```text
CanonicalMarketEvent + QualityAssessment
  -> StrategyInput
  -> Strategy.evaluate(input, context)
  -> StrategyDecision
  -> StrategyDecisionPort
```

The foundation consumes Sprint 3 canonical market data and emits deterministic,
auditable strategy decisions. A strategy decision is not a broker order, order
intent, portfolio mutation, fill, risk approval, P&L update, or execution event.

## Included

- Strict strategy identity and version models.
- Strict strategy configuration base with deterministic SHA-256 fingerprinting.
- `StrategyInput` wrapper around `CanonicalMarketEvent`, idempotency keys, PIT
  metadata, and explicit quality summary.
- Closed `StrategyAction` vocabulary: `NO_ACTION`, `ENTER_LONG`, `EXIT_LONG`,
  `ENTER_SHORT`, `EXIT_SHORT`, `FLATTEN`.
- Deterministic `StrategyDecision` with payload-free audit metadata.
- Infrastructure-neutral `Strategy` and `StrategyDecisionPort` protocols.
- Optional `StrategyState` snapshot/restore protocol, with no durable state
  implementation.
- Explicit in-code `StrategyRegistry`; no plugin discovery or dynamic imports.
- `StrategySession` and `StrategyEngine` lifecycle with no startup evaluation.
- Bounded process-local metrics and in-memory audit sink.
- Reference `NoOpStrategy` for contract validation only.
- Disabled-by-default `BERGAMA_STRATEGY__*` settings and container ownership.

## Excluded

- Broker calls, order submission, cancel/replace, execution adapters.
- Portfolio accounting, cash/P&L, positions, fills, or risk approvals.
- Feature computation, model training, optimization, backtest performance
  analytics, UI, scheduler, automatic live startup, or remote strategy loading.
- Kafka decision publishing adapter. #401 defines only the downstream protocol.

## Validation

```bash
make test-api-strategy-engine
make lint
make typecheck
make test-api
make gate-sprint3
```

Sprint 3 gates must remain green because #401 builds on the released canonical
market-data contracts without changing provider, Kafka, Iceberg, replay,
backfill, data-quality, or release-builder behavior.
