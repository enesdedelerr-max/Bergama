# Dashboard Governance Decision #2 — Authorized Inputs

**Decision ID:** `dashboard.governance.02-authorized-inputs`
**Title:** Decision #2 — Authorized Inputs
**Status:** RESOLVED
**Document class:** Governance Decision only
**Bounded context:** Dashboard

**Subordinate to:**

- Sprint 10 Planning Gate (`sprint-10.planning-gate`)
- Dashboard Architecture v1 (`dashboard.architecture.v1`)
- Dashboard Governance Decision #1 — Semantic Boundary
- Premarket Scoring Governance Decisions #1–#12
- Premarket Scoring Engine Architecture v1
- Premarket Scoring Policy Version `premarket.scoring.policy.v1`
- Morning Briefing Governance Decisions #1–#8
- Morning Briefing Architecture v1
- Morning Briefing Policy Version `morning-briefing.policy.v1`

This Governance Decision freezes repository-wide input authority for Dashboard.
It does not define Architecture, Planning, Policy Version formulas, presentation behavior, filtering, sorting, pagination, replay behavior, output behavior, algorithms, formatting, sections, templates, ranking, weighting, APIs, storage, schemas, user interfaces, rendering, components, packages, classes, services, notification behavior, or implementation.

---

## Purpose

Freeze repository-wide governance for all authorized inputs that Dashboard may consume.

This decision defines input authority only.

---

## Repository Constraints

Dashboard is a downstream consumer of Morning Briefing.

Dashboard shall consume only repository-approved public contracts.
Dashboard shall never acquire authority over upstream bounded contexts.
Dashboard shall never expand repository input authority.

This decision shall not redesign any approved repository artifact.
Dashboard shall never redefine Premarket Score semantics under Premarket Scoring Governance Decision #1.
Dashboard shall never redefine Morning Briefing semantics under Morning Briefing Governance Decision #1.
Dashboard shall never redefine Dashboard semantic meaning under Dashboard Governance Decision #1.

Direct Premarket Scoring consumption remains unauthorized by this decision.

---

## Governance Definitions

### Authorized Input

An input explicitly approved by repository Governance and exposed through an approved public contract for Dashboard consumption.

### Unauthorized Input

Any information not explicitly approved for Dashboard consumption under this decision.

### Input Authority

The repository-approved authority defining which inputs may participate in Dashboard.

These definitions are governance concepts only.

---

## Decision

### Input Authority

This Governance Decision is the sole input authority for Dashboard consumption eligibility.

Only repository-authorized public inputs may be consumed.
Neither implementation, Policy Versions, downstream bounded contexts, documentation, nor operational procedures may invent additional input sources or redefine input authority frozen by this decision.

Input authority governs only eligibility for consumption.
It does not grant ownership, interpretation authority, transformation authority, lifecycle authority, or policy authority over authorized inputs.

Dashboard input authority shall never depend on runtime discovery, mutable UI state, wall-clock time, randomness, or implementation details.

### Public Contract Requirement

Authorized inputs shall be consumed only through approved repository public contracts.

Dashboard shall never consume implementation-private representations of otherwise authorized repository artifacts.
Dashboard shall never consume implementation-private representations of unauthorized repository artifacts.

### Public Contract Ownership

Approval to consume a public contract does not transfer ownership of that contract.

Ownership remains permanently with the originating bounded context.

### Authorized Inputs

The following input categories are authorized for Dashboard consumption:

- Morning Briefing public outputs
- Morning Briefing identity references
- Morning Briefing provenance references
- Explicit UTC `as_of`
- Repository-approved Dashboard configuration
- Repository-approved Dashboard Policy Version identity

Morning Briefing public outputs remain the required authorized upstream.

Authorized inputs remain owned by their originating bounded contexts.
Dashboard consumes them read-only.

### Unauthorized Inputs

Dashboard shall not consume:

- Premarket Scoring public outputs under this decision
- Premarket Score identity references as direct Dashboard inputs under this decision
- Premarket Score provenance references as direct Dashboard inputs under this decision
- raw Market Data
- Feature Platform internals
- Feature Store internals
- Strategy SDK internals
- Broker state
- Portfolio state
- Live execution state
- Human Review decisions
- AI Decision Engine outputs
- mutable UI state
- rendering state
- product-surface state
- notification state
- operational metadata not exposed through approved contracts
- implementation-private data
- any other information not explicitly listed as an Authorized Input under this decision

Direct Premarket Scoring consumption remains UNAUTHORIZED by this decision.
Direct Premarket Scoring consumption may become authorized only through a subsequent approved Dashboard Governance Decision.

### Ownership

Ownership of authorized inputs remains with the originating bounded context.

Dashboard acquires consumption authority only.
Ownership is never transferred.

Morning Briefing retains ownership of Morning Briefing public outputs, Morning Briefing identity, and Morning Briefing provenance.
Premarket Scoring retains ownership of Premarket Scoring public outputs, score identity, and score provenance.
Dashboard retains ownership only of Dashboard configuration and Dashboard Policy Version identity as later frozen by Policy Freeze, without acquiring ownership of upstream artifacts.

### Read-only Consumption

Dashboard shall consume authorized inputs as immutable repository artifacts.

It shall never mutate, regenerate, reinterpret, repair, fabricate, infer, synthesize, reorder, or replace upstream artifacts.
It shall never mutate, replace, repair, reinterpret, or regenerate authorized inputs.

### Input Boundary

Authorized input boundaries are immutable under this decision.

Implementation shall never expand them.
Policy Versions shall not expand them without a subsequent approved Governance Decision.
Only a subsequent approved Dashboard Governance Decision may amend Dashboard input authority.

### Input Stability

Authorized input eligibility shall remain stable across repository executions.

Operational environment, deployment topology, transport mechanism, rendering technology, or presentation platform shall not alter Dashboard input authority.

### Consumer Independence

The set of authorized inputs shall remain invariant regardless of the number, type, or existence of downstream consumers.

The introduction, removal, or evolution of Human Review, AI Decision Engine, Broker Execution, or any later bounded context shall not modify the input authority frozen by this decision.

### Semantic Ownership Preservation

Dashboard owns only Dashboard semantic meaning under Dashboard Governance Decision #1.

Dashboard does not acquire semantic ownership of any consumed repository artifact.
Semantic ownership of consumed artifacts remains permanently with the originating bounded context.
Presentation shall never transfer semantic ownership.
Consumption never transfers semantic ownership.

Dashboard preserves semantic meaning only.
Dashboard does not preserve operational responsibility, ownership authority, or lifecycle authority for upstream artifacts.
Preservation of semantic meaning shall never be interpreted as ownership transfer.

### Identity Compatibility

Dashboard shall preserve identity references exactly as received.

Dashboard shall not replace, rewrite, or synthesize upstream identities.
Dashboard presentation identity remains distinct from Morning Briefing identity and Premarket Score identity under Dashboard Governance Decision #1.

### Provenance Compatibility

Dashboard shall preserve provenance references exactly as received.

Dashboard shall not invent, rewrite, or omit provenance relationships.
Dashboard presentation provenance remains distinct from Morning Briefing provenance and Premarket Score provenance under Dashboard Governance Decision #1.

### Replay Compatibility

Authorized inputs shall remain replay-compatible.

Input authority shall depend only on approved repository contracts.
Input authority shall never depend on wall-clock time, runtime discovery, randomness, mutable UI state, or implementation details.

### PIT Compatibility

Authorized inputs shall remain PIT-compatible.

Only repository-approved inputs valid for the explicit UTC `as_of` may participate.
Dashboard shall not repair PIT violations.

### Fail Closed

Unauthorized, missing, conflicting, or stale inputs shall never become authorized through implementation behavior.

Implementation shall not silently substitute, infer, discover, fabricate, synthesize, or repair additional inputs.
Direct Premarket Scoring inputs shall never become authorized through implementation behavior, Policy Version behavior, or operational procedure under this decision.

### Semantic Preservation

Authorized input consumption shall preserve:

- Premarket Score semantic meaning under Premarket Scoring Governance Decision #1
- Morning Briefing semantic meaning under Morning Briefing Governance Decision #1
- Dashboard semantic meaning under Dashboard Governance Decision #1

Inclusion of Morning Briefing outputs in Dashboard shall not alter Morning Briefing semantic meaning or confer decisioning, approval, review, or execution authority.
Unauthorized Premarket Scoring outputs shall not acquire Dashboard input eligibility through presentation intent, implementation convenience, or downstream demand.

---

## Prohibited Assumptions

The following assumptions are prohibited:

- that Dashboard may consume any repository data not explicitly authorized by this decision
- that Premarket Scoring public outputs are authorized Dashboard inputs under this decision
- that implementation may discover, invent, or substitute additional input sources
- that Policy Versions may expand authorized inputs without a subsequent approved Governance Decision
- that ownership of authorized inputs transfers to Dashboard upon consumption
- that approval to consume a public contract transfers ownership of that contract to Dashboard
- that operational environment, deployment topology, transport mechanism, rendering technology, or presentation platform may alter Dashboard input authority
- that consumption transfers semantic ownership of upstream artifacts to Dashboard
- that preservation of semantic meaning transfers operational responsibility, ownership authority, or lifecycle authority for upstream artifacts to Dashboard
- that authorized input eligibility grants ownership, interpretation authority, transformation authority, lifecycle authority, or policy authority over those inputs
- that authorized inputs may be mutated, regenerated, reinterpreted, repaired, fabricated, inferred, synthesized, reordered, or replaced by Dashboard
- that implementation-private representations of otherwise authorized artifacts may be consumed in place of approved public contracts
- that upstream identity or provenance references may be rewritten or synthesized
- that wall-clock time, runtime discovery, randomness, mutable UI state, or implementation details may expand input authority
- that PIT violations may be repaired to admit otherwise unauthorized or invalid inputs
- that Human Review, AI Decision Engine, Broker Execution, UI state, rendering state, product-surface state, or notification state may serve as Dashboard inputs
- that the existence or evolution of any downstream consumer may alter Dashboard input authority
- that Architecture, Policy Versions, or implementation may supersede this Governance Decision
- that this Governance Decision authorizes Policy Freeze or Implementation

---

## Implementation Impact

Implementation may consume only repository-authorized inputs.

Implementation shall never redefine, expand, or reinterpret input authority.
Documentation and contracts must preserve this input boundary.
Implementation must treat every authorized input as a read-only repository artifact under the frozen Dashboard Policy Version identity once that Policy Version is approved.

Implementation shall remain subordinate to this Governance Decision.
This decision does not authorize implementation.

---

## Future Compatibility

The input authority frozen by this decision is immutable across Dashboard Policy Versions unless superseded by a subsequent approved Dashboard Governance Decision.

Future Policy Versions may define how authorized inputs are consumed.
They may not redefine which inputs are authorized without a subsequent approved Dashboard Governance Decision.

Only a subsequent approved Dashboard Governance Decision may amend Dashboard input authority.

Future bounded contexts may expose additional public contracts.
Such contracts shall not become authorized Dashboard inputs unless explicitly approved by a later Dashboard Governance Decision.

Direct Premarket Scoring consumption, if ever permitted, shall require a subsequent approved Dashboard Governance Decision and shall not redefine Premarket Score semantics, Morning Briefing semantics, or Dashboard semantic meaning.

Dashboard remains subordinate to Sprint 8 Governance Decisions, Sprint 9 Governance Decisions, Premarket Scoring semantic authority, Morning Briefing semantic authority, and Dashboard Governance Decision #1.

---

## Resolution

**Status:** RESOLVED

**Governance effect:** Authorized input authority for Dashboard is frozen. Morning Briefing public outputs remain the required authorized upstream. Direct Premarket Scoring consumption remains unauthorized. All subsequent Dashboard Governance Decisions, Dashboard Policy Version binding, and any later authorized Dashboard implementation remain subordinate to this decision.
