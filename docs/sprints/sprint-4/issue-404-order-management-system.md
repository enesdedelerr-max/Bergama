# Sprint 4 — Issue #404 — Order Management System

## Scope

Issue #404 adds the Order Management System foundation.

OMS admits an already-sized, risk-approved trading intent and owns deterministic
internal order lifecycle state.

Inputs:

- sized `ProposedTradeIntent`
- matching `RiskAssessment` with `final_action == APPROVE`
- `SubmitOrder` facts (`client_order_id`, `order_type`, `time_in_force`, optional `limit_price`)

Output:

- immutable `OrderSnapshot`
- `OrderMutationResult` with deterministic `broker_commands`, `domain_events`, and `fill_events`

## Safety Boundary

OMS does not calculate or resize quantity, reevaluate risk, mutate portfolio or
strategy state, call concrete brokers, fetch market data, or perform Kafka,
database, filesystem, or Iceberg I/O.

Replace/amend is out of MVP. `REPLACE_PENDING` / `REPLACED` are not present.

## Admission

Requires:

- `assessment.final_action == APPROVE`
- matching `intent_id` and `portfolio_id`
- matching approved portfolio version context

`REJECT` / `HALT` create no order and emit no broker command.

## Lifecycle

MVP statuses:

`CREATED`, `PENDING_SUBMIT`, `SUBMITTED`, `ACCEPTED`, `PARTIALLY_FILLED`,
`FILLED`, `CANCEL_PENDING`, `CANCELLED`, `REJECTED`, `EXPIRED`, `FAILED`,
`RECONCILIATION_REQUIRED`

Terminal: `FILLED`, `CANCELLED`, `REJECTED`, `EXPIRED`, `FAILED`.

Broker lifecycle events and fill events are separate. Only fills may later become
Portfolio `FillApplied` facts. `#404` emits fills via `FillEventPort` only and
does not call `PortfolioService`.

## Determinism

- Deterministic SHA-256 `order_id`
- Deterministic `transition_id` (`oms-transition:v1`)
- Deterministic broker-event and fill identities
- Duplicate broker/fill events mutate nothing
- Monotonic `order_version`

## Broker boundary

`ExecutableOrder` is immutable and broker-neutral.

`BrokerOrderPort` is protocol-only. No concrete adapter in `#404`.

OMS never claims successful submission before broker acknowledgement.
Port failure yields typed `OrderBrokerPortError`; durable outbox is deferred.

## Lifecycle wiring

Disabled by default via `BERGAMA_ORDER__*`. No startup order creation or broker
submission. Container owns service lifecycle only.

## Out of Scope

Concrete brokers (`#405`), portfolio mutation, risk evaluation, strategy sizing,
Kafka/DB/Iceberg adapters, replace/amend, advanced order types, settlement,
margin, UI.
