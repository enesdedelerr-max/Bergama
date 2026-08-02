# Morning Briefing Governance Decision #2 — Authorized Inputs

**Decision ID:** `morning-briefing.governance.02-authorized-inputs`  
**Title:** Decision #2 — Authorized Inputs  
**Status:** RESOLVED  
**Document class:** Governance Decision only  
**Bounded context:** Morning Briefing  

**Subordinate to:**

- Sprint 9 Planning Gate (`sprint-9.planning-gate`)  
- Morning Briefing Architecture v1 (`morning-briefing.architecture.v1`)  
- Morning Briefing Governance Decision #1 — Semantic Boundary  
- Premarket Scoring Governance Decisions #1–#12  
- Premarket Scoring Engine Architecture v1  
- Premarket Scoring Policy Version `premarket.scoring.policy.v1`  

This Governance Decision freezes repository-wide input authority for Morning Briefing.  
It does not define Architecture, Planning, Policy Version formulas, briefing assembly, formatting, sections, templates, presentation, ordering, weighting, replay algorithms, APIs, storage, schemas, notification behavior, or implementation.

---

## Purpose

Freeze repository-wide governance for all authorized inputs that Morning Briefing may consume.

This decision defines input authority only.

---

## Repository Constraints

Morning Briefing is a downstream consumer of Premarket Scoring.

Morning Briefing shall consume only repository-approved public contracts.  
Morning Briefing shall never acquire authority over upstream bounded contexts.  
Morning Briefing shall never expand repository input authority.

This decision shall not redesign any approved repository artifact.  
Morning Briefing shall never redefine Premarket Score semantics under Governance Decision #1.

---

## Governance Definitions

### Authorized Input

An input explicitly approved by repository Governance and exposed through an approved public contract.

### Unauthorized Input

Any information not explicitly approved for Morning Briefing consumption.

### Input Authority

The repository-approved authority defining which inputs may participate in Morning Briefing.

These definitions are governance concepts only.

---

## Decision

### Input Authority

This Governance Decision is the sole input authority for Morning Briefing consumption eligibility.

Only repository-authorized public inputs may be consumed.  
Neither implementation, Policy Versions, downstream bounded contexts, documentation, nor operational procedures may invent additional input sources or redefine input authority frozen by this decision.

Input authority governs only eligibility for consumption.  
It does not grant ownership, interpretation authority, transformation authority, or policy authority over authorized inputs.

### Contract Stability

Authorized inputs shall be consumed only through approved repository public contracts.

Implementation shall not consume implementation-private representations of otherwise authorized repository artifacts.

### Authorized Inputs

The following input categories are authorized for Morning Briefing consumption:

- Premarket Scoring public outputs  
- Premarket Score identity references  
- Premarket Score provenance references  
- Explicit UTC `as_of`  
- Repository-approved Morning Briefing configuration  
- Repository-approved Policy Version identity  

Authorized inputs remain owned by their originating bounded contexts.  
Morning Briefing consumes them read-only.

### Unauthorized Inputs

Morning Briefing shall not consume:

- raw Market Data  
- Feature Platform internals  
- Feature Store internals  
- Strategy SDK internals  
- Broker state  
- Portfolio state  
- Live execution state  
- Human Review decisions  
- AI Decision Engine outputs  
- Dashboard state  
- UI state  
- notification state  
- operational metadata not exposed through approved contracts  
- implementation-private data  
- any other information not explicitly listed as an Authorized Input under this decision  

### Ownership

Ownership of authorized inputs remains with the originating bounded context.

Morning Briefing acquires consumption authority only.  
Ownership is never transferred.

Premarket Scoring retains ownership of Premarket Scoring public outputs, score identity, and score provenance.  
Morning Briefing retains ownership only of Morning Briefing configuration and Morning Briefing Policy Version identity as later frozen by Policy Freeze, without acquiring ownership of upstream Premarket Scoring artifacts.

### Read-only Consumption

Morning Briefing shall consume authorized inputs as immutable repository artifacts.

It shall never mutate, replace, repair, reinterpret, or regenerate authorized inputs.

### Input Boundary

Authorized input boundaries are immutable under this decision.

Implementation shall never expand them.  
Policy Versions shall not expand them without a new approved Governance Decision.

### Consumer Independence

The set of authorized inputs shall remain invariant regardless of the number, type, or existence of downstream consumers.

The introduction, removal, or evolution of downstream bounded contexts shall not modify the input authority frozen by this decision.

### Identity Compatibility

Morning Briefing shall preserve identity references exactly as received.

Morning Briefing shall not replace, rewrite, or synthesize upstream identities.  
Morning Briefing identity remains distinct from Premarket Score identity under Governance Decision #1.

### Provenance Compatibility

Morning Briefing shall preserve provenance references exactly as received.

Morning Briefing shall not invent, rewrite, or omit provenance relationships.  
Morning Briefing provenance remains distinct from Premarket Score provenance under Governance Decision #1.

### Replay Compatibility

Authorized inputs shall remain replay-compatible.

Input authority shall depend only on approved repository contracts.  
Input authority shall never depend on wall-clock time, runtime discovery, randomness, or mutable runtime state.

### PIT Compatibility

Authorized inputs shall remain PIT-compatible.

Only repository-approved inputs valid for the explicit UTC `as_of` may participate.  
Morning Briefing shall not repair PIT violations.

### Fail Closed

Unauthorized, missing, conflicting, or stale inputs shall never become authorized through implementation behavior.

Implementation shall not silently substitute, infer, discover, or synthesize additional inputs.

### Semantic Preservation

Authorized input consumption shall preserve Premarket Score semantic meaning under Premarket Scoring Governance Decision #1 and Morning Briefing semantic meaning under Morning Briefing Governance Decision #1.

Inclusion of Premarket Scoring outputs in Morning Briefing shall not alter score semantic meaning or confer decisioning, approval, or execution authority.

---

## Prohibited Assumptions

The following assumptions are prohibited:

- that Morning Briefing may consume any repository data not explicitly authorized by this decision  
- that implementation may discover, invent, or substitute additional input sources  
- that Policy Versions may expand authorized inputs without a subsequent approved Governance Decision  
- that ownership of authorized inputs transfers to Morning Briefing upon consumption  
- that authorized input eligibility grants ownership, interpretation authority, transformation authority, or policy authority over those inputs  
- that authorized inputs may be mutated, repaired, reinterpreted, or regenerated by Morning Briefing  
- that implementation-private representations of otherwise authorized artifacts may be consumed in place of approved public contracts  
- that upstream identity or provenance references may be rewritten or synthesized  
- that wall-clock time, runtime discovery, randomness, or mutable runtime state may expand input authority  
- that PIT violations may be repaired to admit otherwise unauthorized or invalid inputs  
- that Dashboard, Human Review, AI Decision Engine, Broker Execution, UI state, or notification state may serve as Morning Briefing inputs  
- that the existence or evolution of any downstream consumer may alter Morning Briefing input authority  

---

## Implementation Impact

Implementation may consume only repository-authorized inputs.

Implementation shall never redefine, expand, or reinterpret input authority.  
Documentation and contracts must preserve this input boundary.  
Implementation must treat every authorized input as a read-only repository artifact under the frozen Morning Briefing Policy Version identity once that Policy Version is approved.

This decision does not authorize implementation.

---

## Future Compatibility

The input authority frozen by this decision is immutable across Morning Briefing Policy Versions unless superseded by a subsequent approved Governance Decision.

Future Policy Versions may define how authorized inputs are consumed.  
They may not redefine which inputs are authorized without a subsequent approved Governance Decision.

Future bounded contexts may expose additional public contracts.  
Such contracts shall not become authorized Morning Briefing inputs unless explicitly approved by a later Governance Decision.

Morning Briefing remains subordinate to Sprint 8 Governance Decisions, Premarket Scoring semantic authority, and Morning Briefing Governance Decision #1.

---

## Resolution

**Status:** RESOLVED  

**Governance effect:** Authorized input authority for Morning Briefing is frozen. All subsequent Morning Briefing Governance Decisions, Morning Briefing Policy Version v1, and any later authorized Morning Briefing implementation remain subordinate to this decision.
