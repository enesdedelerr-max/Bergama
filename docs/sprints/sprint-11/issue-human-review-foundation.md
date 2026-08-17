# Sprint 11 — Human Review Foundation

**Issue type:** Implementation  
**Bounded context:** Human Review  
**GitHub Issue:** [#89](https://github.com/enesdedelerr-max/Bergama/issues/89)  
**GitHub Issue URL:** https://github.com/enesdedelerr-max/Bergama/issues/89

## Authorization

- Sprint 11 Planning Gate (`sprint-11.planning-gate`)
- Human Review Architecture v1 (`human-review.architecture.v1`)
- Human Review Governance Decisions #1–#8
- Human Review Policy Version `human-review.policy.v1`
- Human Review Implementation Authorization v1 (`human-review.implementation-authorization.v1`)

This specification remains subordinate to every artifact above.
It does not redefine Planning, Architecture, Governance, Policy, or Implementation Authorization.

## Goal

Implement the Human Review Foundation exactly as authorized: a deterministic, auditable, human-authority bounded context under Policy Version `human-review.policy.v1`, consuming approved Dashboard public outputs only and recording explicit human attestation.

Implementation SHALL create only the Human Review bounded context.

## Authorized scope

Implementation SHALL include ONLY:

- Human Review package
- immutable contracts
- deterministic review pipeline
- identity generation
- provenance generation
- review history binding
- ordering preservation
- replay support
- PIT validation
- deterministic outputs
- validation layer
- public exports
- unit tests
- contract tests
- integration tests
- implementation documentation

## Explicit non-goals

Do NOT implement:

- Dashboard redesign
- Morning Briefing redesign
- Premarket Scoring redesign
- AI Decision Engine
- Broker Execution
- UI
- HTTP APIs
- REST
- GraphQL
- persistence
- databases
- workers
- schedulers
- notifications
- authentication
- authorization
- reviewer role management
- workflow expansion
- Strategy SDK redesign
- Feature Platform redesign
- Market Data redesign
- direct Morning Briefing consumption (unauthorized under Governance Decision #2)
- direct Premarket Scoring consumption (unauthorized under Governance Decision #2)

## Acceptance criteria

Implementation satisfies:

- `human-review.policy.v1`
- Human Review Governance Decisions #1–#8
- Human Review Implementation Authorization v1
- deterministic replay
- PIT safety
- identity preservation
- provenance preservation
- ordering preservation
- read-only upstream consumption
- fail-closed behavior
- immutable contracts
- public-contract-only integration
- public exports expose only repository-approved Human Review public contracts
- Implementation SHALL never consume implementation-private representations of upstream bounded contexts
- Same authorized recorded inputs, explicit recorded human attestation, UTC `as_of`, Human Review Policy Version, and configuration SHALL always produce the same Human Review output

Human Review never becomes:

- Dashboard authority
- Morning Briefing authority
- Premarket Scoring authority
- AI Decision Engine
- Broker Execution
- execution authority

## Deliverables

- Human Review package
- immutable contracts
- deterministic review pipeline
- identity generation
- provenance generation
- review history binding
- ordering preservation
- replay support
- PIT validation
- deterministic outputs
- validation layer
- public exports
- unit tests
- contract tests
- integration tests
- implementation documentation

## Implementation Independence

Implementation shall remain independent of UI framework, rendering technology, deployment topology, transport mechanism, and client implementation.

## Validation

```bash
make lint
make typecheck
make validate-secrets
# Human Review test suite via repository-supported Human Review test target
make test-api-dashboard
make test-api-premarket
make test-api-feature-platform
make test-api-strategy-sdk
make test-api-strategy-engine
git diff --check
```

## Branch rule

A feature branch may be created only after a real numbered GitHub Issue exists for this specification and only linked to that issue number.

Feature branch: `feature/sprint11-89-human-review-foundation`

## Repository Boundary

Implementation shall remain entirely within the Human Review bounded context.

No upstream bounded context may be redesigned, modified, or reauthorized by this implementation.

## Rollback boundary

Rollback affects only Human Review implementation artifacts introduced by this issue.

Planning, Architecture, Governance, Policy, and Implementation Authorization remain immutable.
Upstream Dashboard, Morning Briefing, and Premarket Scoring remain intact.
