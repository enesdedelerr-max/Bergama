# Morning Briefing Governance Decision #5 — Identity Policy

**Decision ID:** `morning-briefing.governance.05-identity-policy`  
**Title:** Decision #5 — Identity Policy  
**Status:** RESOLVED  
**Document class:** Governance Decision only  
**Bounded context:** Morning Briefing  

**Subordinate to:**

- Sprint 9 Planning Gate (`sprint-9.planning-gate`)  
- Morning Briefing Architecture v1 (`morning-briefing.architecture.v1`)  
- Morning Briefing Governance Decision #1 — Semantic Boundary  
- Morning Briefing Governance Decision #2 — Authorized Inputs  
- Morning Briefing Governance Decision #3 — Brief Assembly Policy  
- Morning Briefing Governance Decision #4 — Replay Policy  
- Premarket Scoring Governance Decisions #1–#12  
- Premarket Scoring Engine Architecture v1  
- Premarket Scoring Policy Version `premarket.scoring.policy.v1`  

This Governance Decision freezes repository-wide identity authority for Morning Briefing.  
It does not define Architecture, Planning, Policy Version formulas, hashing, identifiers, algorithms, schemas, serialization, APIs, storage, notification behavior, or implementation.

---

## Purpose

Freeze repository-wide identity governance for Morning Briefing.

This decision governs identity authority only.

---

## Repository Constraints

Morning Briefing is a downstream consumer of Premarket Scoring.

Morning Briefing identity governance shall remain subordinate to:

- semantic meaning under Governance Decision #1  
- authorized input boundaries under Governance Decision #2  
- assembly authority under Governance Decision #3  
- replay authority under Governance Decision #4  
- Premarket Scoring Governance Decisions #1–#12  
- Premarket Scoring Policy Version `premarket.scoring.policy.v1`  

This decision shall not redesign any approved repository artifact.  
Morning Briefing shall never redefine Premarket Score identity ownership or Premarket Score semantic meaning.

---

## Governance Definitions

### Morning Briefing Identity

The repository-governed identity belonging exclusively to a Morning Briefing output.

### Upstream Identity

An identity owned by an originating bounded context and consumed by Morning Briefing as a reference only.

### Identity Authority

The repository-approved authority defining ownership, stability, determinism, and compatibility obligations for Morning Briefing identity and for preservation of upstream identity references.

### Identity Independence

The requirement that Morning Briefing identity remain distinct from Premarket Score identity and from all other upstream identities.

These definitions are governance concepts only.

---

## Decision

### Identity Authority

This Governance Decision is the sole identity authority for Morning Briefing.

Neither implementation, Policy Versions, downstream bounded contexts, documentation, nor operational procedures may redefine the identity authority frozen by this decision.

Identity authority governs only Morning Briefing identity ownership, stability, determinism, and upstream identity preservation.  
It does not grant ownership of upstream artifacts, decisioning authority, approval authority, execution authority, hashing authority, serialization authority, or presentation authority.

### Identity Ownership

Morning Briefing owns Morning Briefing identity for briefing outputs only.

Premarket Scoring retains exclusive ownership of Premarket Score identity.  
Ownership of upstream identities is never transferred to Morning Briefing.  
Morning Briefing acquires reference authority over upstream identities only.

### Identity Stability

Morning Briefing identity, once produced under a frozen Policy Version for a given pinned evaluation, shall remain stable for that evaluation.

Identity authority shall not authorize silent replacement, mutation, or reassignment of Morning Briefing identity after emission under later frozen policy.  
Upstream identity references shall remain stable exactly as received.

### Identity Determinism

Morning Briefing identity shall be deterministic under later frozen policy.

Same authorized inputs, same explicit UTC `as_of`, same frozen Policy Version identity, and same frozen configuration shall produce the same Morning Briefing identity.  
Identity shall never depend on wall-clock time, randomness, mutable runtime state, implementation discovery, external side effects, or downstream consumers.

### Identity Compatibility

Morning Briefing identity shall remain compatible with:

- semantic meaning under Governance Decision #1  
- authorized input boundaries under Governance Decision #2  
- assembly authority under Governance Decision #3  
- replay authority under Governance Decision #4  

Morning Briefing outputs that reference Premarket Scores shall retain original Premarket Score identity references unchanged.

### Identity Replay

Identity shall remain replay-compatible.

Pinned replay conditions shall reproduce the same Morning Briefing identity under later frozen policy.  
Replay shall not replace, rewrite, or synthesize Morning Briefing identity or upstream identity references.

### Identity PIT

Identity shall remain PIT-compatible.

Morning Briefing identity shall bind to the explicit UTC `as_of` of the evaluation under later frozen policy.  
Identity shall not incorporate future knowledge.  
Identity shall not repair PIT violations.

### Identity Independence

Morning Briefing identity shall remain distinct from Premarket Scoring identity.

Morning Briefing identity shall never reuse Premarket Score identity as a substitute for briefing identity.  
Morning Briefing identity shall never absorb, replace, or merge upstream identities.

### Identity shall never

- reuse Premarket Score identity  
- rewrite upstream identities  
- invent identities  
- synthesize identities  
- change identity ownership  
- mutate upstream identity references  
- depend on wall-clock time, randomness, or mutable runtime state  
- confer recommendation, approval, or execution authority  

### Upstream Identity Preservation

Morning Briefing shall preserve upstream identity references exactly as received through approved repository public contracts.

Morning Briefing shall not replace, rewrite, invent, or synthesize upstream identities.  
Implementation-private identity representations shall not be consumed in place of approved public identity references.

### Fail Closed

Missing, conflicting, rewritten, invented, or non-deterministic identity conditions shall never become identity-valid through implementation behavior.

Implementation shall not silently substitute, infer, discover, fabricate, or synthesize identities to complete briefing emission.  
Prohibited identity conditions shall abort; silent partial success is forbidden.

### Contract Stability

Identity references shall be consumed and preserved only through approved repository public contracts.

Implementation shall not derive identity authority from implementation-private representations of otherwise authorized repository artifacts.

### Consumer Independence

Identity authority shall remain invariant regardless of the number, type, or existence of downstream consumers.

The introduction, removal, or evolution of downstream bounded contexts shall not modify the identity authority frozen by this decision.

### Semantic Preservation

Identity governance shall preserve Premarket Score semantic meaning under Premarket Scoring Governance Decision #1 and Morning Briefing semantic meaning under Morning Briefing Governance Decision #1.

Assignment or preservation of identity shall not alter score semantic meaning or confer decisioning, approval, or execution authority.

---

## Prohibited Assumptions

The following assumptions are prohibited:

- that Morning Briefing may reuse Premarket Score identity as Morning Briefing identity  
- that Morning Briefing may rewrite, invent, or synthesize upstream identities  
- that identity ownership of upstream artifacts transfers to Morning Briefing  
- that wall-clock time, randomness, mutable runtime state, implementation discovery, or external side effects may participate in identity authority  
- that identity may repair PIT, provenance, or input-boundary violations  
- that Policy Versions may redefine identity authority without a subsequent approved Governance Decision  
- that downstream consumers may redefine identity authority  
- that identity confers recommendation, approval, or execution authority  
- that the existence or evolution of any downstream consumer may alter identity authority  

---

## Implementation Impact

Implementation may produce and preserve identities only under the identity authority frozen by this decision.

Implementation shall never redefine, expand, or reinterpret identity authority.  
Documentation and contracts must preserve this identity boundary.  
Implementation must treat Morning Briefing identity as distinct, deterministic, and non-substitutable for Premarket Score identity under the frozen Morning Briefing Policy Version identity once that Policy Version is approved.

This decision does not authorize implementation.

---

## Future Compatibility

The identity authority frozen by this decision is immutable across Morning Briefing Policy Versions unless superseded by a subsequent approved Governance Decision.

Future Policy Versions may define deterministic identity behavior within this authority.  
They may not redefine identity authority, authorize reuse of Premarket Score identity, rewrite upstream identities, invent or synthesize identities, change identity ownership, or alter semantic meaning without a subsequent approved Governance Decision.

Morning Briefing remains subordinate to Sprint 8 Governance Decisions, Premarket Scoring semantic authority, and Morning Briefing Governance Decisions #1–#4.

---

## Resolution

**Status:** RESOLVED  

**Governance effect:** Identity authority for Morning Briefing is frozen. All subsequent Morning Briefing Governance Decisions, Morning Briefing Policy Version v1, and any later authorized Morning Briefing implementation remain subordinate to this decision.
