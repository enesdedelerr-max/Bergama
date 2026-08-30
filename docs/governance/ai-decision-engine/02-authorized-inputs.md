# AI Decision Engine Governance Decision #2 — Authorized Inputs

**Decision ID:** `ai-decision-engine.governance.02-authorized-inputs`  
**Title:** Decision #2 — Authorized Inputs  
**Status:** RESOLVED  
**Document class:** Governance Decision only  
**Bounded context:** AI Decision Engine

**Subordinate to:**

- Sprint 12 Planning Gate (`sprint-12.planning-gate`) — APPROVED
- AI Decision Engine Architecture v1 (`ai-decision-engine.architecture.v1`) — APPROVED
- AI Decision Engine Governance Decision #1 — Semantic Boundary
- Human Review Governance Decisions #1–#8
- Human Review Architecture v1
- Human Review Policy Version `human-review.policy.v1`
- Dashboard Governance Decisions #1–#8
- Dashboard Architecture v1
- Dashboard Policy Version `dashboard.policy.v1`
- Morning Briefing Governance Decisions #1–#8
- Morning Briefing Architecture v1
- Morning Briefing Policy Version `morning-briefing.policy.v1`
- Premarket Scoring Governance Decisions #1–#12
- Premarket Scoring Engine Architecture v1
- Premarket Scoring Policy Version `premarket.scoring.policy.v1`
- Sprint 4 Strategy Engine, Risk, Portfolio, OMS, and Broker ownership boundaries

This Governance Decision freezes repository-wide authorized-input admission and imported-authority limits for AI Decision Engine.  
It does not define Architecture, Planning, Policy Version formulas, AI Decision authority, abstention taxonomy, identity composition, provenance composition, replay mechanics, output behavior, human-authority workflows over AI Decision Engine outputs, model participation, algorithms, exception classes, HTTP status codes, APIs, storage, schemas, user interfaces, rendering, components, packages, classes, services, transport, notification behavior, runtime validation algorithms, or implementation.

---

## Purpose

Freeze repository-wide governance for all inputs that AI Decision Engine may consume under Architecture v1 and Governance v1.

This decision defines authorized-input admission and imported-authority limits only.  
It does not redefine AI Decision Engine semantic meaning under AI Decision Engine Governance Decision #1.

---

## Repository Constraints

AI Decision Engine is a downstream consumer of Human Review under Architecture v1.

AI Decision Engine shall consume only repository-approved public contracts.  
AI Decision Engine shall never acquire authority over upstream bounded contexts through consumption.  
AI Decision Engine shall never expand repository input authority beyond what this decision explicitly authorizes.

This decision shall not redesign any approved repository artifact.  
AI Decision Engine shall never redefine Human Review semantics under Human Review Governance Decision #1 or AI Decision Engine Governance Decision #1.  
AI Decision Engine shall never redefine Dashboard semantics under Dashboard Governance Decision #1.  
AI Decision Engine shall never redefine Morning Briefing semantics under Morning Briefing Governance Decision #1.  
AI Decision Engine shall never redefine Premarket Score semantics under Premarket Scoring Governance Decision #1.

Direct Dashboard consumption remains unauthorized by this decision.  
Direct Morning Briefing consumption remains unauthorized by this decision.  
Direct Premarket Scoring consumption remains unauthorized by this decision.  
Risk, Portfolio, and Strategy Engine consumption remain unauthorized by this decision.

Governance alone cannot reopen an Architecture-deferred input boundary.  
Where Architecture v1 requires an amendment, Architecture amendment, Architecture approval, and subsequent Governance must occur before that input may become authorized.

---

## Governance Definitions

### Authorized Input

An input explicitly approved by repository Governance and exposed through an approved Human Review public contract for AI Decision Engine read-only consumption as recorded human-attestation context only.

### Unauthorized Input

Any information not explicitly approved for AI Decision Engine consumption under this decision.

Unauthorized inputs have no AI Decision Engine input authority.  
They shall never be interpreted as AI Decision Engine authority, Human Review authority, trade approval, Order Intent authority, or execution authority.

### Admissible Input Boundary

The closed set of Authorized Inputs that may participate in AI Decision Engine evaluation under Architecture v1 and Governance v1.

Any input outside that set is outside the admissible input boundary.

### Input Authority

The repository-approved authority defining which inputs may be admitted for AI Decision Engine consumption and what authority may be imported from those inputs.

### Imported Authority

The limited repository-approved authority that AI Decision Engine may derive from an Authorized Input without acquiring upstream ownership, without redefining upstream semantics, and without converting attestation context into AI Decision approval, trade approval, Order Intent authority, or execution authority.

### Upstream Ownership Preservation

Authorized upstream inputs remain owned by their originating bounded contexts.  
AI Decision Engine acquires read-only consumption authority only.  
Ownership is never transferred.

These definitions are governance concepts only.  
They do not define runtime validation algorithms, exception classes, HTTP status codes, or implementation mechanisms.

---

## Decision

### Input Authority

This Governance Decision is the sole authorized-input authority for AI Decision Engine input admission and imported-authority limits under Architecture v1 and Governance v1.

Only repository-authorized Human Review public outputs, consumed through approved Human Review public contracts under the conditions frozen by this decision, may participate in AI Decision Engine evaluation.  
Neither implementation, Policy Versions, downstream bounded contexts, documentation, nor operational procedures may invent additional input sources or redefine input authority frozen by this decision.

Input authority governs only eligibility for admission and the limits of imported authority.  
It does not grant ownership, interpretation authority beyond attestation-context preservation, transformation authority, lifecycle authority, policy authority, AI Decision approval authority, trade approval authority, Order Intent authority, or execution authority over authorized inputs.

AI Decision Engine input authority shall never depend on runtime discovery, mutable UI state, wall-clock substitution, randomness, model output, cached private representation, broker state, OMS state, portfolio state, or implementation convenience.

### Sole Authorized Upstream Input Surface

The sole Architecture v1 and Governance v1 authorized upstream input surface is:

**Human Review public outputs**

Only through approved Human Review public contracts under Human Review Policy Version `human-review.policy.v1` and Human Review Governance Decisions #1–#8.

Human Review public outputs remain the required authorized upstream.  
No secondary authorized input surface exists under this decision.

### Public Contract Requirement

Authorized Human Review inputs shall be consumed only through approved Human Review public contracts.

AI Decision Engine shall never consume implementation-private Human Review representations.  
AI Decision Engine shall never consume implementation-private representations of any other bounded context as a substitute for authorized Human Review public contracts.

### Public Contract Ownership

Approval to consume a Human Review public contract does not transfer ownership of that contract or of Human Review semantic meaning.

Human Review retains Human Review semantic ownership under Human Review Governance Decision #1 and AI Decision Engine Governance Decision #1.

### Authorized Input Characteristics

Authorized Human Review public outputs consumed by AI Decision Engine shall be:

- read-only
- recorded human-attestation context only
- PIT-bound to an explicit UTC `as_of`
- identity-reference preserving
- provenance-reference preserving
- non-mutating with respect to upstream artifacts
- non-reinterpretive with respect to Human Review semantics

AI Decision Engine shall consume Human Review public outputs as attestation context only.  
Human Review input does not import AI Decision approval, trade approval, Order Intent authority, execution authority, Dashboard ownership, Morning Briefing ownership, or Premarket Scoring ownership.

### Imported Authority

AI Decision Engine may import only the following authority from authorized Human Review public outputs:

- existence of an approved Human Review public artifact eligible for read-only consumption
- recorded human-attestation semantics as frozen by Human Review Governance Decision #1
- Human Review identity references as received
- Human Review provenance references as received
- PIT and explicit UTC `as_of` context associated with the authorized public artifact
- frozen upstream Human Review Policy Version identity and Human Review Governance meaning as referenced by the authorized public artifact

Imported authority is attestation-context authority only.  
It is not AI Decision approval authority.  
It is not trade approval authority.  
It is not Order Intent authority.  
It is not Broker Execution authority.

### Explicitly Non-Imported Authority

AI Decision Engine shall not import from Human Review or any other source:

- authority to reinterpret Human Review semantics
- authority to manufacture missing attestation
- authority to infer approval from absence, silence, or missing evidence
- authority to change Human Review history
- authority to mutate Human Review records
- trade approval authority
- Order Intent authority
- Broker Execution authority
- Dashboard semantic ownership
- Morning Briefing semantic ownership
- Premarket Scoring semantic ownership
- Strategy Engine ownership
- Risk ownership
- Portfolio ownership
- OMS ownership

```text
Human Review record
  ≠ AI Decision
  ≠ AI proposal approval
  ≠ Order Intent
  ≠ execution authority
```

Human Review input admission does not convert Human Review attestation into AI Decision approval.

### Deferred Inputs Remain Closed

Direct consumption remains unauthorized under this decision for:

- Dashboard public outputs
- Morning Briefing public outputs
- Premarket Scoring public outputs
- Risk evaluations or snapshots
- Portfolio snapshots
- Strategy Engine artifacts or relationships

This decision does not reopen Architecture-deferred input boundaries.  
This decision does not create conditional consumption ports.  
This decision does not authorize fallback reads, convenience reads, optional secondary sources, or indirect dependency paths that substitute for authorized Human Review public outputs.

Reopening a deferred input requires a later approved Architecture amendment where Architecture v1 requires one, followed by subsequent approved Governance, remaining inside Planning scope.

### Forbidden Input Sources

AI Decision Engine shall not consume or treat as decision authority:

- raw Market Data
- Feature Platform internals
- Feature Store internals
- Strategy SDK internals
- implementation-private upstream representations
- OMS state
- Broker abstraction state
- live execution state
- mutable UI state
- rendering state
- product-surface state
- notification state
- broker APIs or SDK payloads
- portfolio mutation authority
- model output as a substitute for authorized Human Review public input
- cached or private representations as a substitute for authorized Human Review public input
- any information not explicitly authorized as Human Review public outputs under this decision

Forbidden inputs shall never be interpreted as AI Decision Engine authority.

### No Fallback Authority

If Human Review public input is unavailable, missing, invalid, unauthorized, malformed, semantically incompatible, stale, or conflicting, AI Decision Engine must not fall back to:

- Dashboard
- Morning Briefing
- Premarket Scoring
- Risk
- Portfolio
- Strategy Engine
- Market Data
- model output
- cached or private representation
- broker or OMS state
- mutable live authority
- inferred or synthesized Human Review substitutes

No fallback source may silently become authorized input.  
Missing Human Review evidence must never silently imply authorization or an AI Decision.

This Decision does not pre-resolve authoritative-result versus abstention semantics for such conditions.  
That belongs to future AI Decision Engine Governance Decision #3 — AI Decision Authority and later Policy Freeze as authorized.

### Missing / Invalid Required Input

Governance-level rule:

Missing Human Review evidence must never silently imply authorization or an AI Decision.

Unauthorized, malformed, semantically incompatible, stale, or conflicting required Human Review public evidence must fail closed.

AI Decision Engine shall not silently substitute, infer, discover, fabricate, synthesize, repair, or normalize missing or invalid required Human Review input into authorized input.

This Decision does not define concrete exception classes, HTTP status codes, operator messaging, retry policy, or implementation algorithms.

### Read-Only Consumption

AI Decision Engine shall consume authorized Human Review public outputs as immutable repository artifacts.

AI Decision Engine shall not:

- mutate upstream artifacts
- repair upstream artifacts
- rewrite upstream artifacts
- deduplicate upstream artifacts in a way that changes meaning
- fabricate upstream authority
- infer missing upstream authority
- normalize upstream semantics in a way that changes Human Review meaning
- regenerate Human Review outputs
- reinterpret Human Review semantics

Consumption does not transfer semantic ownership.  
AI Decision Engine Governance Decision #1 remains the semantic-boundary authority.

### Ownership

Human Review retains ownership of Human Review public outputs, Human Review identity, Human Review provenance, and Human Review semantic meaning.

Dashboard retains Dashboard ownership.  
Morning Briefing retains Morning Briefing ownership.  
Premarket Scoring retains Premarket Scoring ownership.  
Strategy Engine, Risk, Portfolio, OMS, and Broker abstraction retain their ownership boundaries.

AI Decision Engine acquires read-only consumption authority only for authorized Human Review public outputs.  
AI Decision Engine does not acquire ownership of any consumed bounded context.

### Input Boundary Stability

Authorized input boundaries are immutable under this decision unless superseded by a subsequent approved AI Decision Engine Governance Decision following any required Architecture amendment.

Implementation shall never expand them.  
Policy Versions shall not expand them without a subsequent approved Governance Decision.  
Only a subsequent approved AI Decision Engine Governance Decision, following any required Architecture amendment, may amend AI Decision Engine authorized-input authority.

Operational environment, deployment topology, transport mechanism, rendering technology, presentation platform, or model participation shall not alter authorized-input authority frozen by this decision.

### PIT Binding

Authorized Human Review public inputs shall belong to the AI Decision Engine evaluation's explicit UTC `as_of` context.

Governance-level PIT expectations:

- no future knowledge
- cross-`as_of` semantic mismatch fails closed
- no wall-clock substitution for explicit UTC `as_of`
- recorded public Human Review artifacts are used; mutable live authority is not substituted

AI Decision Engine shall not repair PIT violations to admit otherwise unauthorized input.

This Decision does not define exact comparison algorithms, serializers, or replay storage.  
Detailed replay semantics remain AI Decision Engine Governance Decision #6 — Replay / PIT.

### Identity / Provenance Boundary

AI Decision Engine shall preserve Human Review identity references and Human Review provenance references exactly as received from authorized Human Review public contracts.

AI Decision Engine shall not replace, rewrite, synthesize, omit, or substitute upstream identity or provenance references.

This Decision requires preservation obligations only.  
It does not define AI Decision Engine identity format, hash strategy, digest payload, provenance schema, or canonical payload fields.

Exact identity composition belongs to AI Decision Engine Governance Decision #4 — Identity.  
Exact provenance composition belongs to AI Decision Engine Governance Decision #5 — Provenance and later Policy Freeze as authorized.

### Broker Execution Firewall

Authorized Human Review input must never become execution authority.

```text
Human Review input
  ≠ Order Intent
  ≠ broker authorization
  ≠ executable instruction
  ≠ Broker Execution authorization
```

This Decision does not authorize:

- Order Intent creation
- broker APIs or SDKs
- submit order
- cancel order
- replace order
- fill processing
- OMS mutation
- Portfolio mutation
- live trading
- capital deployment
- execution authorization

An authorized Human Review public artifact alone shall never constitute Broker Execution authorization.

Broker Execution remains DENIED / DEFERRED and requires a future independent Planning Gate.

---

## Reserved Later Governance Decisions

This Decision freezes authorized-input admission and imported-authority limits only.

The following remain NOT STARTED and are not resolved by this Decision:

| # | Planned Decision | Status |
| --- | --- | --- |
| 3 | AI Decision Authority | NOT STARTED |
| 4 | Identity | NOT STARTED |
| 5 | Provenance | NOT STARTED |
| 6 | Replay / PIT | NOT STARTED |
| 7 | Output / Abstention | NOT STARTED |
| 8 | Human Authority over AI Decision Engine Outputs | NOT STARTED |

This Decision does not freeze concrete AI Decision types, abstention taxonomy, recommendation types, confidence semantics, thresholds, rankings, output schema, human approval workflow, or model/provider behavior.

---

## Prohibited Assumptions

The following assumptions are prohibited:

- that any input other than authorized Human Review public outputs may participate under this decision
- that Human Review consumption equals AI Decision approval
- that Human Review attestation equals trade approval
- that Human Review attestation equals Order Intent authority
- that Human Review attestation equals execution authority
- that missing Human Review evidence may be inferred, fabricated, or synthesized
- that missing Human Review evidence may silently imply authorization or an AI Decision
- that Dashboard, Morning Briefing, Premarket Scoring, Risk, Portfolio, or Strategy Engine may serve as fallback inputs
- that model output may substitute for missing authorized Human Review input
- that cached or private representations may substitute for authorized Human Review public contracts
- that broker, OMS, portfolio, or live execution state may serve as input authority
- that Governance alone may reopen Architecture-deferred inputs
- that conditional ports, convenience reads, or optional secondary sources are authorized by this decision
- that consumption transfers semantic ownership
- that imported attestation context transfers Human Review semantic ownership to AI Decision Engine
- that AI Decision Engine may mutate, repair, rewrite, or reinterpret authorized upstream inputs
- that wall-clock time, runtime discovery, randomness, or mutable UI state may expand input authority
- that PIT violations may be repaired to admit otherwise unauthorized input
- that this Decision pre-resolves authoritative-result versus abstention semantics beyond fail-closed input admission
- that this Decision defines AI Decision authority, identity composition, provenance composition, replay mechanics, output semantics, or human authority over AI Decision Engine outputs
- that Architecture, Policy Versions, or implementation may supersede this Governance Decision
- that this Decision authorizes Policy Freeze, Implementation Authorization, Implementation, or Broker Execution

---

## Implementation Impact

Implementation must admit only frozen authorized Human Review public inputs under the imported-authority limits frozen by this decision.

Implementation shall never redefine, expand, reinterpret, or substitute input authority.  
Documentation and contracts must preserve this input boundary.

Implementation shall remain subordinate to AI Decision Engine Governance Decision #1 and this Decision.  
This Decision does not authorize implementation.

---

## Future Compatibility

The authorized-input authority frozen by this decision is immutable across AI Decision Engine Policy Versions unless superseded by a subsequent approved AI Decision Engine Governance Decision following any required Architecture amendment.

Future Policy Versions may define how authorized Human Review public inputs are consumed.  
They may not redefine which inputs are authorized or what authority may be imported without a subsequent approved AI Decision Engine Governance Decision.

Only a subsequent approved AI Decision Engine Governance Decision, following any required Architecture amendment where Architecture v1 requires one, may amend AI Decision Engine authorized-input authority.

Deferred input consumption, if ever permitted, shall require Architecture amendment where required, subsequent approved Governance, and shall not redefine Human Review, Dashboard, Morning Briefing, or Premarket Scoring semantics.

AI Decision Engine remains subordinate to Sprint 8–11 frozen authorities, Sprint 4 ownership boundaries, AI Decision Engine Governance Decision #1, and Human Review Governance Decisions #1–#8.

---

## Resolution

**Status:** RESOLVED

**Governance effect:** Authorized-input admission and imported-authority limits for AI Decision Engine are frozen. Human Review public outputs remain the sole authorized upstream input surface under Architecture v1 and Governance v1. Direct Dashboard, Morning Briefing, Premarket Scoring, Risk, Portfolio, and Strategy Engine consumption remain unauthorized. Fallback authority is forbidden. All subsequent AI Decision Engine Governance Decisions, AI Decision Engine Policy Version binding, and any later authorized AI Decision Engine implementation remain subordinate to this decision.

**Governance set status:** IN PROGRESS — documentation-only. Decisions #1–#2 RESOLVED. Decisions #3–#8 NOT STARTED. Governance is not COMPLETE.
