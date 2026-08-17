# Human Review Governance Decision #2 — Authorized Inputs

**Decision ID:** `human-review.governance.02-authorized-inputs`  
**Title:** Decision #2 — Authorized Inputs  
**Status:** RESOLVED  
**Document class:** Governance Decision only  
**Bounded context:** Human Review

**Subordinate to:**

- Sprint 11 Planning Gate (`sprint-11.planning-gate`)
- Human Review Architecture v1 (`human-review.architecture.v1`)
- Human Review Governance Decision #1 — Semantic Boundary
- Dashboard Governance Decisions #1–#8
- Dashboard Architecture v1
- Dashboard Policy Version `dashboard.policy.v1`
- Morning Briefing Governance Decisions #1–#8
- Morning Briefing Architecture v1
- Morning Briefing Policy Version `morning-briefing.policy.v1`
- Premarket Scoring Governance Decisions #1–#12
- Premarket Scoring Engine Architecture v1
- Premarket Scoring Policy Version `premarket.scoring.policy.v1`

This Governance Decision freezes repository-wide input authority for Human Review.  
It does not define Architecture, Planning, Policy Version formulas, review workflow, outcome taxonomy, reviewer roles, identity mechanisms, replay behavior, output behavior, algorithms, APIs, storage, schemas, user interfaces, rendering, components, packages, classes, services, transport, notification behavior, runtime validation, or implementation.

---

## Purpose

Freeze repository-wide governance for all authorized inputs that Human Review may consume.

This decision defines input authority only.  
It freezes only what inputs Human Review is semantically authorized to consume.

---

## Repository Constraints

Human Review is a downstream consumer of Dashboard.

Human Review shall consume only repository-approved public contracts.  
Human Review shall never acquire authority over upstream bounded contexts.  
Human Review shall never expand repository input authority.

This decision shall not redesign any approved repository artifact.  
Human Review shall never redefine Dashboard semantics under Dashboard Governance Decision #1.  
Human Review shall never redefine Morning Briefing semantics under Morning Briefing Governance Decision #1.  
Human Review shall never redefine Premarket Score semantics under Premarket Scoring Governance Decision #1.  
Human Review shall never redefine Human Review semantic meaning under Human Review Governance Decision #1.

Direct Morning Briefing consumption remains unauthorized by this decision.  
Direct Premarket Scoring consumption remains unauthorized by this decision.

---

## Governance Definitions

### Authorized Input

An input explicitly approved by repository Governance and exposed through an approved public contract for Human Review consumption, or an explicit human-attestation recorded input as frozen by Human Review Governance Decision #1.

### Unauthorized Input

Any information not explicitly approved for Human Review consumption under this decision.

Unauthorized inputs have no Human Review input authority.  
They shall never be interpreted as Human Review authority.

### Admissible Semantic Boundary

The closed set of Authorized Inputs that may participate in Human Review semantic meaning.

Any input outside that set is outside the admissible semantic boundary.

### Input Authority

The repository-approved authority defining which inputs may participate in Human Review.

### Upstream Ownership Preservation

Authorized upstream inputs remain owned by their originating bounded contexts.  
Human Review acquires consumption authority only.  
Ownership is never transferred.

These definitions are governance concepts only.  
They do not define runtime validation.

---

## Decision

### Input Authority

This Governance Decision is the sole input authority for Human Review consumption eligibility.

Only repository-authorized public inputs, together with explicit human attestation as frozen by Human Review Governance Decision #1, may participate in Human Review.  
Neither implementation, Policy Versions, downstream bounded contexts, documentation, nor operational procedures may invent additional input sources or redefine input authority frozen by this decision.

Input authority governs only eligibility for consumption.  
It does not grant ownership, interpretation authority, transformation authority, lifecycle authority, or policy authority over authorized inputs.

Human Review input authority shall never depend on runtime discovery, mutable UI state, wall-clock time, randomness, or implementation details.

### Public Contract Requirement

Authorized upstream inputs shall be consumed only through approved repository public contracts.

Human Review shall never consume implementation-private representations of otherwise authorized repository artifacts.  
Human Review shall never consume implementation-private representations of unauthorized repository artifacts.

### Public Contract Ownership

Approval to consume a public contract does not transfer ownership of that contract.

Ownership remains permanently with the originating bounded context.

### Authorized Inputs

The following input categories are authorized for Human Review:

- Dashboard public outputs
- Dashboard identity references
- Dashboard provenance references
- Explicit UTC `as_of`
- Explicit human attestation as a recorded input under Human Review Governance Decision #1
- Repository-approved Human Review configuration
- Repository-approved Human Review Policy Version identity

Dashboard public outputs remain the required authorized upstream.

Authorized upstream inputs remain owned by their originating bounded contexts.  
Human Review consumes them read-only.

Explicit human attestation is not an upstream artifact.  
It is recorded human authority as frozen by Human Review Governance Decision #1.  
This Decision does not define reviewer roles, reviewer identity mechanisms, concrete review outcomes, or workflow state transitions.

### Conditionally Authorized Inputs

The following input categories remain unauthorized under this Decision and may become authorized only through a subsequent approved Human Review Governance Decision:

- Morning Briefing public outputs
- Morning Briefing identity references as direct Human Review inputs
- Morning Briefing provenance references as direct Human Review inputs
- Premarket Scoring public outputs
- Premarket Score identity references as direct Human Review inputs
- Premarket Score provenance references as direct Human Review inputs

Direct Morning Briefing consumption remains UNAUTHORIZED by this decision.  
Direct Premarket Scoring consumption remains UNAUTHORIZED by this decision.

### Unauthorized Inputs

Human Review shall not consume:

- Morning Briefing public outputs under this decision
- Premarket Scoring public outputs under this decision
- raw Market Data
- Feature Platform internals
- Feature Store internals
- Strategy SDK internals
- implementation-private representations
- mutable UI state
- rendering state
- product-surface state
- notification state
- broker state
- portfolio state
- live execution state
- AI Decision Engine outputs
- operational metadata not exposed through approved contracts
- any other information not explicitly listed as an Authorized Input under this decision

Unauthorized inputs shall never be interpreted as Human Review authority.

### Ownership

Ownership of authorized upstream inputs remains with the originating bounded context.

Human Review acquires consumption authority only.  
Ownership is never transferred.

Dashboard retains ownership of Dashboard public outputs, Dashboard identity, and Dashboard provenance.  
Morning Briefing retains ownership of Morning Briefing public outputs, Morning Briefing identity, and Morning Briefing provenance.  
Premarket Scoring retains ownership of Premarket Scoring public outputs, score identity, and score provenance.  
Human Review retains ownership only of Human Review configuration, Human Review Policy Version identity as later frozen by Policy Freeze, and Human Review semantic artifacts under Human Review Governance Decision #1, without acquiring ownership of upstream artifacts.

### Read-only Consumption

Human Review shall consume authorized upstream inputs as immutable repository artifacts.

It shall never mutate, regenerate, reinterpret, repair, fabricate, infer, synthesize, reorder, or replace upstream artifacts.  
It shall never mutate, replace, repair, reinterpret, or regenerate authorized upstream inputs.

### Input Boundary

Authorized input boundaries are immutable under this decision.

Implementation shall never expand them.  
Policy Versions shall not expand them without a subsequent approved Governance Decision.  
Only a subsequent approved Human Review Governance Decision may amend Human Review input authority.

### Input Stability

Authorized input eligibility shall remain stable across repository executions.

Operational environment, deployment topology, transport mechanism, rendering technology, or presentation platform shall not alter Human Review input authority.

### Consumer Independence

The set of authorized inputs shall remain invariant regardless of the number, type, or existence of downstream consumers.

The introduction, removal, or evolution of AI Decision Engine, Broker Execution, or any later bounded context shall not modify the input authority frozen by this decision.

### Semantic Ownership Preservation

Human Review owns only Human Review semantic meaning under Human Review Governance Decision #1.

Human Review does not acquire semantic ownership of any consumed repository artifact.  
Semantic ownership of consumed artifacts remains permanently with the originating bounded context.  
Consumption never transfers semantic ownership.  
Recording human attestation never transfers semantic ownership of upstream artifacts.  
Presentation never transfers semantic ownership.

Human Review preserves semantic meaning only.  
Human Review does not preserve operational responsibility, ownership authority, or lifecycle authority for upstream artifacts.  
Preservation of semantic meaning shall never be interpreted as ownership transfer.

### Identity Compatibility

Human Review shall preserve identity references exactly as received.

Human Review shall not replace, rewrite, or synthesize upstream identities.  
Human Review identity remains distinct from Dashboard identity, Morning Briefing identity, and Premarket Score identity under Human Review Governance Decision #1.

### Provenance Compatibility

Human Review shall preserve provenance references exactly as received.

Human Review shall not invent, rewrite, or omit provenance relationships.  
Human Review provenance remains distinct from Dashboard provenance, Morning Briefing provenance, and Premarket Score provenance under Human Review Governance Decision #1.

### Replay Compatibility

Authorized inputs shall remain replay-compatible.

Input authority shall depend only on approved repository contracts and explicit recorded human attestation as frozen by Human Review Governance Decision #1.  
Input authority shall never depend on wall-clock time, runtime discovery, randomness, mutable UI state, or implementation details.

### PIT Compatibility

Authorized inputs shall remain PIT-compatible.

Only repository-approved inputs valid for the explicit UTC `as_of` may participate.  
Human Review shall not repair PIT violations.

### Fail Closed

Unauthorized, missing, conflicting, or stale inputs shall never become authorized through implementation behavior.

Implementation shall not silently substitute, infer, discover, fabricate, synthesize, or repair additional inputs.  
Direct Morning Briefing inputs shall never become authorized through implementation behavior, Policy Version behavior, or operational procedure under this decision.  
Direct Premarket Scoring inputs shall never become authorized through implementation behavior, Policy Version behavior, or operational procedure under this decision.

Missing Dashboard context shall never be inferred.  
Missing Morning Briefing shall never be synthesized.  
Missing Premarket Scoring shall never be fabricated.

### Semantic Preservation

Authorized input consumption shall preserve:

- Dashboard semantic meaning under Dashboard Governance Decision #1
- Morning Briefing semantic meaning under Morning Briefing Governance Decision #1
- Premarket Score semantic meaning under Premarket Scoring Governance Decision #1
- Human Review semantic meaning under Human Review Governance Decision #1

Inclusion of Dashboard outputs in Human Review shall not alter Dashboard semantic meaning or confer decisioning, approval, recommendation, or execution authority.  
Unauthorized Morning Briefing or Premarket Scoring outputs shall not acquire Human Review input eligibility through review intent, implementation convenience, or downstream demand.

---

## Prohibited Assumptions

The following assumptions are prohibited:

- that Dashboard visibility equals authorization
- that Dashboard ordering equals recommendation
- that missing Dashboard context may be inferred
- that missing Morning Briefing may be synthesized
- that missing Premarket Scoring may be fabricated
- that implementation-private objects are valid authority
- that UI state is valid authority
- that broker state is valid authority
- that portfolio state is valid authority
- that Human Review may consume any repository data not explicitly authorized by this decision
- that Morning Briefing public outputs are authorized Human Review inputs under this decision
- that Premarket Scoring public outputs are authorized Human Review inputs under this decision
- that implementation may discover, invent, or substitute additional input sources
- that Policy Versions may expand authorized inputs without a subsequent approved Governance Decision
- that ownership of authorized inputs transfers to Human Review upon consumption
- that approval to consume a public contract transfers ownership of that contract to Human Review
- that operational environment, deployment topology, transport mechanism, rendering technology, or presentation platform may alter Human Review input authority
- that consumption transfers semantic ownership of upstream artifacts to Human Review
- that recording human attestation transfers semantic ownership of upstream artifacts to Human Review
- that preservation of semantic meaning transfers operational responsibility, ownership authority, or lifecycle authority for upstream artifacts to Human Review
- that authorized input eligibility grants ownership, interpretation authority, transformation authority, lifecycle authority, or policy authority over those inputs
- that authorized inputs may be mutated, regenerated, reinterpreted, repaired, fabricated, inferred, synthesized, reordered, or replaced by Human Review
- that implementation-private representations of otherwise authorized artifacts may be consumed in place of approved public contracts
- that upstream identity or provenance references may be rewritten or synthesized
- that wall-clock time, runtime discovery, randomness, mutable UI state, or implementation details may expand input authority
- that PIT violations may be repaired to admit otherwise unauthorized or invalid inputs
- that execution state, AI Decision Engine outputs, rendering state, product-surface state, or notification state may serve as Human Review inputs
- that unauthorized inputs may be interpreted as Human Review authority
- that the existence or evolution of any downstream consumer may alter Human Review input authority
- that Architecture, Policy Versions, or implementation may supersede this Governance Decision
- that this Governance Decision authorizes Policy Freeze or Implementation
- that this Governance Decision defines reviewer roles, review workflow, or outcome taxonomy

---

## Implementation Impact

Implementation must consume only frozen authorized inputs.

Implementation shall never redefine, expand, or reinterpret input authority.  
Documentation and contracts must preserve this input boundary.  
Implementation must treat every authorized upstream input as a read-only repository artifact under the frozen Human Review Policy Version identity once that Policy Version is approved.

Implementation shall remain subordinate to this Governance Decision.  
This decision does not authorize implementation.

---

## Future Compatibility

The input authority frozen by this decision is immutable across Human Review Policy Versions unless superseded by a subsequent approved Human Review Governance Decision.

Future Policy Versions may define how authorized inputs are consumed.  
They may not redefine which inputs are authorized without a subsequent approved Human Review Governance Decision.

Only a subsequent approved Human Review Governance Decision may amend Human Review input authority.

Future bounded contexts may expose additional public contracts.  
Such contracts shall not become authorized Human Review inputs unless explicitly approved by a later Human Review Governance Decision.

Direct Morning Briefing consumption, if ever permitted, shall require a subsequent approved Human Review Governance Decision and shall not redefine Morning Briefing semantics, Dashboard semantics, or Human Review semantic meaning.  
Direct Premarket Scoring consumption, if ever permitted, shall require a subsequent approved Human Review Governance Decision and shall not redefine Premarket Score semantics, Dashboard semantics, or Human Review semantic meaning.

Human Review remains subordinate to Sprint 8 Governance Decisions, Sprint 9 Governance Decisions, Sprint 10 Governance Decisions, Premarket Scoring semantic authority, Morning Briefing semantic authority, Dashboard semantic authority, and Human Review Governance Decision #1.

---

## Resolution

**Status:** RESOLVED

**Governance effect:** Authorized input authority for Human Review is frozen. Dashboard public outputs remain the required authorized upstream. Direct Morning Briefing consumption remains unauthorized. Direct Premarket Scoring consumption remains unauthorized. All subsequent Human Review Governance Decisions, Human Review Policy Version binding, and any later authorized Human Review implementation remain subordinate to this decision.
