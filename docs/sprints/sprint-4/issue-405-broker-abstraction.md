# Sprint 4 — Issue #405 — Broker Abstraction

## Scope

Issue #405 adds a pure broker abstraction between OMS and concrete adapters.

Broker owns:

- provider communication (PaperBroker only in this issue)
- capability negotiation
- typed command outcomes
- normalized broker lifecycle/fill facts

Broker never owns OMS order state, transitions, versions, Portfolio, Risk, or Strategy.

## Typed outcomes

Mutually exclusive:

- `ACKNOWLEDGED` — command accepted by broker (not a fill)
- `REJECTED` — explicit broker rejection
- `FAILED_BEFORE_SEND` — broker definitely never received the command
- `OUTCOME_UNKNOWN` — may have been received; never implies accept/reject; requires reconciliation
- `RECONCILIATION_REQUIRED` — explicit reconciliation path (not retry)

## PaperBroker

Deterministic in-process adapter. Same ExecutableOrder + policy + fixed clock + seed
produces the same submission identity, broker order id, events, and outcomes.

No live SDK. No Kafka. No durable outbox. No exactly-once claim.

## Lifecycle

`BERGAMA_BROKER__ENABLED=false` by default. Container creates PaperBroker only when
enabled/injected. No startup submit/cancel. Close is idempotent.

## Out of scope

Live broker SDK, Kafka execution adapter, EventEnvelope publisher, portfolio booking,
risk/strategy mutation, replace/amend, reconciliation daemon, UI, Issue #406+.
