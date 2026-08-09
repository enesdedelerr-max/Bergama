# Sprint 10 — Dashboard Foundation

**Issue type:** Implementation
**Bounded context:** Dashboard
**GitHub Issue:** [#85](https://github.com/enesdedelerr-max/Bergama/issues/85)

## Authorization

- Sprint 10 Planning Gate (`sprint-10.planning-gate`)
- Dashboard Architecture v1 (`dashboard.architecture.v1`)
- Dashboard Governance Decisions #1–#8
- Dashboard Policy Version `dashboard.policy.v1`
- Dashboard Implementation Authorization v1 (`dashboard.implementation-authorization.v1`)

## Goal

Implement the Dashboard Foundation exactly as authorized: a deterministic, read-only, presentation-oriented operational visibility bounded context under Policy Version `dashboard.policy.v1`, consuming approved Morning Briefing public outputs only.

## Authorized scope

Implementation SHALL include ONLY:

- Dashboard package
- immutable contracts
- deterministic presentation assembly
- presentation pipeline
- identity generation
- provenance generation
- ordering preservation
- replay support
- PIT validation
- deterministic output
- validation
- unit tests
- contract tests
- integration tests
- public exports

## Explicit non-goals

Do NOT implement:

- Dashboard UI
- HTTP APIs
- REST
- GraphQL
- persistence
- database
- workers
- schedulers
- notifications
- websocket
- authentication
- authorization
- Human Review
- AI Decision Engine
- Broker Execution
- Strategy SDK redesign
- Feature Platform redesign
- Market Data redesign
- Morning Briefing redesign
- Premarket Scoring redesign
- direct Premarket Scoring consumption (unauthorized under Governance Decision #2)

## Acceptance criteria

Implementation satisfies:

- `dashboard.policy.v1`
- Dashboard Governance Decisions #1–#8
- deterministic replay
- PIT safety
- identity preservation
- provenance preservation
- ordering preservation
- read-only upstream consumption
- fail-closed behavior
- immutable contracts
- Dashboard never becomes ordering, scoring, briefing, review, decision, or execution authority
- public exports expose only repository-approved Dashboard public contracts
- Dashboard consumes only repository-approved public contracts
- Implementation shall never consume implementation-private representations of upstream bounded contexts
- Same authorized inputs, UTC `as_of`, Dashboard Policy Version, and configuration shall always produce the same Dashboard output

## Deliverables

- Dashboard package
- immutable contracts
- deterministic presentation assembly
- presentation pipeline
- identity generation
- provenance generation
- ordering preservation
- replay support
- PIT validation
- deterministic output
- validation
- unit tests
- contract tests
- integration tests
- public exports
- repository-supported Dashboard test target
- documentation required for the authorized implementation slice

## Implementation Independence

Implementation shall remain independent of UI framework, rendering technology, deployment topology, transport mechanism, and client implementation.

## Validation

```bash
make lint
make typecheck
make validate-secrets
# Dashboard test suite via repository-supported Dashboard test target
make test-api-premarket
make test-api-feature-platform
make test-api-strategy-sdk
make test-api-strategy-engine
git diff --check
```

## Branch rule

Create a branch only after a real GitHub issue number exists for this specification and only linked to that issue number.

## Repository Boundary

Implementation shall remain entirely within the Dashboard bounded context.

No upstream bounded context may be redesigned, modified, or reauthorized by this implementation.

## Rollback boundary

Revert only authorized Dashboard implementation artifacts introduced by this issue. Upstream Morning Briefing and Premarket Scoring remain intact. Governance, Architecture, Policy Version, and Implementation Authorization remain unchanged.
