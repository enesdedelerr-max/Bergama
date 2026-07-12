# ARCHITECTURE.md

## Architectural style

The platform uses:

- Clean Architecture
- Feature-first organization
- Ports and adapters
- Event-driven workflows
- Explicit bounded contexts
- Deterministic state machines
- Append-only audit and ledger records

## Core layers

### Presentation

Responsibilities:

- HTTP routing
- Request parsing
- Response serialization
- UI rendering
- Transport-specific concerns

Must not contain:

- business rules
- persistence logic
- broker logic
- risk decisions
- financial calculations

### Application

Responsibilities:

- use-case orchestration
- transaction boundaries
- policy invocation
- dependency coordination
- event publication
- workflow state transitions

### Domain

Responsibilities:

- business invariants
- entities
- value objects
- calculations
- state-machine rules
- policy-independent domain behavior

The domain should remain framework independent.

### Infrastructure

Responsibilities:

- PostgreSQL
- Redis
- Kafka
- ClickHouse
- object storage
- market-data providers
- broker adapters
- external APIs
- telemetry exporters

## Bounded contexts

Primary bounded contexts include:

- Market Data
- Feature Platform
- Premarket Intelligence
- Decision Engine
- Human Review
- Execution
- Portfolio and Ledger
- Risk
- MLOps
- Research
- Compliance
- Operations
- Control Plane

Each bounded context owns:

- its internal data model,
- its application interfaces,
- its events,
- its database schema or repository boundaries,
- its operational metrics.

## Cross-context communication

Preferred mechanisms:

1. Versioned application interfaces for synchronous in-process calls.
2. Versioned APIs for service boundaries.
3. Canonical events for asynchronous workflows.

Forbidden:

- importing internal modules across bounded contexts,
- reading another context’s database tables directly,
- mutating another context’s state directly.

## Deterministic workflow model

Replayable workflows must:

- receive an injected clock,
- consume pinned inputs,
- use canonical ordering,
- avoid uncontrolled concurrency,
- avoid unseeded randomness,
- emit stable structured outputs,
- persist checkpoints.

## Financial state model

Order and portfolio state must be derived from immutable events.

```text
Order Intent
→ Authorization
→ Broker Order
→ Broker Events
→ Fill
→ Ledger Entries
→ Position Projection
→ P&L
```

Source-of-truth hierarchy:

- Broker events for external execution facts
- Append-only ledger for accounting facts
- Projections for current state
- Snapshots for performance and query efficiency

## Failure model

Failures must be:

- explicit,
- classified,
- persisted where workflow relevant,
- observable,
- recoverable where possible.

Critical uncertain state should produce:

`SAFE_HOLD`

rather than optimistic continuation.

## Change policy

For an architectural change:

1. Explain the current architecture.
2. Identify the limitation.
3. Present alternatives.
4. Describe migration and compatibility.
5. Identify operational and security risks.
6. Create or update an ADR.
7. Obtain approval before implementation.
