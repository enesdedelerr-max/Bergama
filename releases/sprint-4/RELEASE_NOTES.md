# Sprint 4 Release Notes

## Completed

### Strategy Engine

- Added deterministic, infrastructure-neutral strategy contracts and lifecycle.
- Added explicit strategy identity, configuration fingerprinting, registry,
  decision output, and optional state boundaries.
- Preserved the distinction between strategy decisions and executable orders.

### Portfolio

- Added a deterministic Portfolio Aggregate and orchestration boundary.
- Added immutable snapshots, explicit version checks, ledger-entry output, and
  average-cost accounting policy.
- Kept order submission, broker access, and risk approval outside Portfolio.

### Risk Engine

- Added a pure, deterministic risk evaluator for already-sized trade intents.
- Added ordered fail-closed rules and explicit `APPROVE`, `REJECT`, and `HALT`
  outcomes.
- Preserved the rule that Risk never sizes or resizes trades.

### Order Management System

- Added deterministic admission and internal order lifecycle state.
- Added broker-neutral commands, immutable snapshots, and explicit fill/event
  boundaries.
- Required matching risk approval before order admission.

### Broker Abstraction

- Added typed broker outcomes, capability negotiation, and normalized lifecycle
  and fill facts.
- Added a deterministic in-process paper broker.
- Preserved reconciliation requirements for unknown outcomes.

### Strategy SDK Runtime

- Added the author-facing `bergama-strategy-sdk` package and opt-in host runtime.
- Added immutable feature snapshots, plugin manifests, permissions, feature
  schemas, explicit state I/O, execution budgets, and partial batch recovery.
- Kept the legacy #401 Strategy Engine as the default runtime path.

## Safety and defaults

- No live broker integration or live execution was enabled.
- Broker, order, risk, and Strategy SDK runtimes remain disabled by default.
- No risk, compliance, review, authorization, kill-switch, or idempotency
  boundary was bypassed.

## Breaking Changes

None.

## Backward Compatibility

Maintained.

## Known exclusions

- Live broker SDKs and live trading.
- Durable outbox, durable reconciliation, and cross-process exactly-once
  guarantees.
- Automatic portfolio booking from fills.
- Replace/amend, advanced order types, margin, settlement, derivatives, and FX.
- Strategy plugin CPU or memory sandboxing.
- Feature Platform, Premarket Intelligence, and any Issue #407 implementation.
