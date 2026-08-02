# Morning Briefing Governance Decision #6 — Provenance Policy

**Decision ID:** `morning-briefing.governance.06-provenance-policy`
**Title:** Decision #6 — Provenance Policy
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
- Morning Briefing Governance Decision #5 — Identity Policy
- Premarket Scoring Governance Decisions #1–#12
- Premarket Scoring Engine Architecture v1
- Premarket Scoring Policy Version `premarket.scoring.policy.v1`

This Governance Decision freezes repository-wide provenance authority for Morning Briefing.
It does not define Architecture, Planning, Policy Version formulas, schemas, APIs, storage, algorithms, notification behavior, or implementation.

---

## Purpose

Freeze repository-wide provenance governance for Morning Briefing.

This decision governs provenance authority only.

---

## Repository Constraints

Morning Briefing is a downstream consumer of Premarket Scoring.

Morning Briefing provenance governance shall remain subordinate to:

- semantic meaning under Governance Decision #1
- authorized input boundaries under Governance Decision #2
- assembly authority under Governance Decision #3
- replay authority under Governance Decision #4
- identity authority under Governance Decision #5
- Premarket Scoring Governance Decisions #1–#12
- Premarket Scoring Policy Version `premarket.scoring.policy.v1`

This decision shall not redesign any approved repository artifact.
Morning Briefing shall never redefine Premarket Score provenance ownership or Premarket Score semantic meaning.

---

## Governance Definitions

### Morning Briefing Provenance

The repository-governed provenance belonging exclusively to a Morning Briefing output.

### Upstream Provenance

Provenance owned by an originating bounded context and consumed by Morning Briefing as a reference only.

### Provenance Authority

The repository-approved authority defining ownership, lineage, traceability, and preservation obligations for Morning Briefing provenance and for preservation of upstream provenance references.

### Lineage

The governed relationship between a Morning Briefing output and the authorized inputs, configuration, Policy Version identity, and explicit UTC `as_of` that participated in its assembly.

### Traceability

The governed ability to audit a Morning Briefing output back to preserved upstream provenance and identity references and to Morning Briefing provenance under later frozen policy.

These definitions are governance concepts only.

---

## Decision

### Provenance Authority

This Governance Decision is the sole provenance authority for Morning Briefing.

Neither implementation, Policy Versions, downstream bounded contexts, documentation, nor operational procedures may redefine the provenance authority frozen by this decision.

Provenance authority governs only Morning Briefing provenance ownership, lineage, traceability, and upstream provenance preservation.
It does not grant ownership of upstream artifacts, decisioning authority, approval authority, execution authority, schema authority, storage authority, or presentation authority.

### Ownership

Morning Briefing owns Morning Briefing provenance for briefing outputs only.

Premarket Scoring retains exclusive ownership of Premarket Score provenance.
Ownership of upstream provenance is never transferred to Morning Briefing.
Morning Briefing acquires reference authority over upstream provenance only.

### Lineage

Morning Briefing provenance shall establish lineage to:

- authorized inputs actually consumed under Governance Decision #2
- explicit UTC `as_of`
- frozen Morning Briefing Policy Version identity
- frozen Morning Briefing configuration
- Morning Briefing identity under Governance Decision #5
- preserved upstream identity and provenance references

Lineage shall not invent relationships absent from authorized inputs actually consumed.

### Traceability

Morning Briefing provenance shall support repository auditability and replay comparison under later frozen policy.

Traceability shall preserve linkage from Morning Briefing outputs to upstream Premarket Scoring identity and provenance references.
Traceability shall not authorize reconstruction of upstream artifacts by mutation, repair, or regeneration.

### Identity Linkage

Morning Briefing provenance shall remain linked to Morning Briefing identity under Governance Decision #5.

Morning Briefing provenance shall preserve linkage to upstream Premarket Score identity references exactly as received.
Provenance shall not replace, rewrite, or synthesize identity references.
Morning Briefing provenance shall remain distinct from Premarket Score provenance and shall not substitute for upstream provenance.

### Provenance Preservation

Morning Briefing shall preserve provenance exactly as received through approved repository public contracts.

Morning Briefing shall never:

- rewrite provenance
- invent provenance
- omit provenance
- synthesize provenance
- mutate upstream provenance references
- change provenance ownership

### Replay Compatibility

Provenance shall remain replay-compatible.

Pinned replay conditions shall reproduce the same Morning Briefing provenance under later frozen policy.
Replay shall not rewrite, invent, omit, or synthesize provenance.
Provenance shall never depend on wall-clock time, randomness, mutable runtime state, implementation discovery, external side effects, or downstream consumers.

### PIT Compatibility

Provenance shall remain PIT-compatible.

Morning Briefing provenance shall bind to the explicit UTC `as_of` of the evaluation under later frozen policy.
Provenance shall not incorporate future knowledge.
Provenance shall not repair PIT violations.

### Fail Closed

Missing, conflicting, rewritten, invented, omitted, or non-deterministic provenance conditions shall never become provenance-valid through implementation behavior.

Implementation shall not silently substitute, infer, discover, fabricate, omit, or synthesize provenance to complete briefing emission.
Prohibited provenance conditions shall abort; silent partial success is forbidden.

### Contract Stability

Provenance references shall be consumed and preserved only through approved repository public contracts.

Implementation shall not derive provenance authority from implementation-private representations of otherwise authorized repository artifacts.

### Consumer Independence

Provenance authority shall remain invariant regardless of the number, type, or existence of downstream consumers.

The introduction, removal, or evolution of downstream bounded contexts shall not modify the provenance authority frozen by this decision.

### Semantic Preservation

Provenance governance shall preserve Premarket Score semantic meaning under Premarket Scoring Governance Decision #1 and Morning Briefing semantic meaning under Morning Briefing Governance Decision #1.

Assignment or preservation of provenance shall not alter score semantic meaning or confer recommendation, approval, or execution authority.

### Determinism Compatibility

Same authorized inputs, same explicit UTC `as_of`, same frozen Policy Version identity, and same frozen configuration shall produce the same Morning Briefing provenance under later frozen policy.

---

## Prohibited Assumptions

The following assumptions are prohibited:

- that Morning Briefing may rewrite, invent, omit, or synthesize provenance
- that provenance ownership of upstream artifacts transfers to Morning Briefing
- that Morning Briefing provenance may substitute for Premarket Score provenance
- that wall-clock time, randomness, mutable runtime state, implementation discovery, or external side effects may participate in provenance authority
- that provenance may repair PIT, identity, or input-boundary violations
- that Policy Versions may redefine provenance authority without a subsequent approved Governance Decision
- that downstream consumers may redefine provenance authority
- that provenance confers recommendation, approval, or execution authority
- that the existence or evolution of any downstream consumer may alter provenance authority

---

## Implementation Impact

Implementation may produce and preserve provenance only under the provenance authority frozen by this decision.

Implementation shall never redefine, expand, or reinterpret provenance authority.
Documentation and contracts must preserve this provenance boundary.
Implementation must treat Morning Briefing provenance as distinct, deterministic, and non-substitutable for Premarket Score provenance under the frozen Morning Briefing Policy Version identity once that Policy Version is approved.

This decision does not authorize implementation.

---

## Future Compatibility

The provenance authority frozen by this decision is immutable across Morning Briefing Policy Versions unless superseded by a subsequent approved Governance Decision.

Future Policy Versions may define deterministic provenance behavior within this authority.
They may not redefine provenance authority, authorize rewriting, invention, omission, or synthesis of provenance, change provenance ownership, or alter semantic meaning without a subsequent approved Governance Decision.

Morning Briefing remains subordinate to Sprint 8 Governance Decisions, Premarket Scoring semantic authority, and Morning Briefing Governance Decisions #1–#5.

---

## Resolution

**Status:** RESOLVED

**Governance effect:** Provenance authority for Morning Briefing is frozen. All subsequent Morning Briefing Governance Decisions, Morning Briefing Policy Version v1, and any later authorized Morning Briefing implementation remain subordinate to this decision.
