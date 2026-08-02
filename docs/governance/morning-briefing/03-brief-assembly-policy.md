# Morning Briefing Governance Decision #3 — Brief Assembly Policy

**Decision ID:** `morning-briefing.governance.03-brief-assembly-policy`  
**Title:** Decision #3 — Brief Assembly Policy  
**Status:** RESOLVED  
**Document class:** Governance Decision only  
**Bounded context:** Morning Briefing  

**Subordinate to:**

- Sprint 9 Planning Gate (`sprint-9.planning-gate`)  
- Morning Briefing Architecture v1 (`morning-briefing.architecture.v1`)  
- Morning Briefing Governance Decision #1 — Semantic Boundary  
- Morning Briefing Governance Decision #2 — Authorized Inputs  
- Premarket Scoring Governance Decisions #1–#12  
- Premarket Scoring Engine Architecture v1  
- Premarket Scoring Policy Version `premarket.scoring.policy.v1`  

This Governance Decision freezes repository-wide assembly authority for Morning Briefing.  
It does not define Architecture, Planning, Policy Version formulas, formatting, sections, templates, rendering, presentation, APIs, storage, schemas, algorithms, notification behavior, or implementation.

---

## Purpose

Freeze repository-wide governance for how authorized inputs may participate in Morning Briefing assembly.

This decision governs assembly authority only.

---

## Repository Constraints

Morning Briefing is a downstream consumer of Premarket Scoring.

Morning Briefing shall assemble operator attention context only from inputs authorized under Governance Decision #2.  
Morning Briefing shall never acquire ownership, interpretation authority, transformation authority, or policy authority over upstream artifacts through assembly.  
Morning Briefing shall never redefine Premarket Score semantics under Premarket Scoring Governance Decision #1 or Morning Briefing semantic meaning under Morning Briefing Governance Decision #1.

This decision shall not redesign any approved repository artifact.  
Assembly remains subordinate to Governance Decisions #1 and #2.

---

## Governance Definitions

### Assembly

The deterministic participation of authorized inputs in the formation of a Morning Briefing under a repository-approved Morning Briefing Policy Version.

### Assembly Authority

The repository-approved authority defining how authorized inputs may participate in Morning Briefing assembly.

### Fabrication

The creation of briefing content, evidence, relationships, or conclusions not present in authorized inputs.

### Inference

The derivation of briefing content, evidence, relationships, or conclusions not explicitly present in authorized inputs.

### Synthesis

The construction of briefing content by combining, inventing, or completing material beyond the authorized inputs actually consumed.

These definitions are governance concepts only.

---

## Decision

### Assembly Authority

This Governance Decision is the sole assembly authority for Morning Briefing.

Neither implementation, Policy Versions, downstream bounded contexts, documentation, nor operational procedures may redefine the assembly authority frozen by this decision.

Assembly authority governs only how authorized inputs may participate in Morning Briefing assembly.  
It does not grant ownership of upstream artifacts, decisioning authority, approval authority, execution authority, formatting authority, or presentation authority.

### Assembly Scope

Morning Briefing assembly may:

- admit only inputs authorized under Governance Decision #2  
- bind assembly to an explicit UTC `as_of`  
- form a deterministic Morning Briefing under a repository-approved Morning Briefing Policy Version  
- preserve upstream identity and provenance references exactly as received  
- attach Morning Briefing identity and provenance as later frozen by subsequent Governance Decisions and Policy Freeze  

Morning Briefing assembly shall never:

- regenerate Premarket Scores  
- mutate, replace, repair, reinterpret, or regenerate authorized inputs  
- invent briefing content  
- fabricate, infer, or synthesize evidence  
- reorder Premarket Scores  
- expand authorized inputs  
- confer trading, review, AI decisioning, or execution authority  

### Read-only Assembly

Assembly shall consume authorized inputs as immutable repository artifacts.

Assembly shall never mutate upstream artifacts.  
Assembly shall never regenerate Premarket Scores.  
Assembly shall never invent briefing content.

### No Fabrication

Assembly shall not fabricate briefing content, evidence, relationships, or conclusions.

Absent authorized evidence shall remain absent.  
Fabrication is forbidden under all conditions.

### No Inference

Assembly shall not infer briefing content, evidence, relationships, or conclusions not explicitly present in authorized inputs.

Inference is forbidden under all conditions.

### No Synthesis

Assembly shall not synthesize briefing content by inventing, completing, or inventing relationships beyond authorized inputs actually consumed.

Synthesis is forbidden under all conditions.

### Presentation Neutrality

Assembly shall remain presentation-neutral.

Assembly authority does not define formatting, sections, templates, rendering, or presentation surfaces.  
Presentation concerns remain outside this Governance Decision.

### Deterministic Assembly

Same authorized inputs, same repository-approved Morning Briefing configuration, same Morning Briefing Policy Version identity, and same explicit UTC `as_of` shall produce the same assembly result under later frozen policy.

Assembly shall not depend on wall-clock time, unseeded randomness, runtime discovery, or mutable runtime state.

### Replay Compatibility

Assembly shall remain replay-compatible.

Pinned authorized inputs and pinned configuration shall re-execute to the same assembly result under later frozen policy.  
Assembly authority shall never depend on non-replayable state.

### PIT Compatibility

Assembly shall remain PIT-compatible.

Only repository-approved authorized inputs valid for the explicit UTC `as_of` may participate in assembly.  
Assembly shall not repair PIT violations.

### Identity Compatibility

Assembly shall preserve upstream identity references exactly as received.

Assembly shall not replace, rewrite, or synthesize upstream identities.  
Morning Briefing identity remains distinct from Premarket Score identity under Governance Decision #1 and shall not substitute for upstream identity.

### Provenance Compatibility

Assembly shall preserve upstream provenance references exactly as received.

Assembly shall not invent, rewrite, or omit provenance relationships.  
Morning Briefing provenance remains distinct from Premarket Score provenance under Governance Decision #1 and shall not replace upstream provenance.

### Fail Closed

Unauthorized, missing, conflicting, or stale inputs shall never become valid assembly participants through implementation behavior.

Implementation shall not silently substitute, infer, discover, fabricate, synthesize, or repair inputs to complete assembly.  
Prohibited assembly conditions shall abort; silent partial success is forbidden.

### Semantic Preservation

Assembly shall preserve:

- Premarket Score semantic meaning under Premarket Scoring Governance Decision #1  
- Morning Briefing semantic meaning under Morning Briefing Governance Decision #1  
- Authorized input boundaries under Morning Briefing Governance Decision #2  

Inclusion of Premarket Scoring outputs in assembly shall not alter score semantic meaning or confer recommendation, approval, or execution authority.

### Contract Stability

Assembly shall consume authorized inputs only through approved repository public contracts.

Implementation shall not assemble from implementation-private representations of otherwise authorized repository artifacts.

### Consumer Independence

Assembly authority shall remain invariant regardless of the number, type, or existence of downstream consumers.

The introduction, removal, or evolution of downstream bounded contexts shall not modify the assembly authority frozen by this decision.

---

## Prohibited Assumptions

The following assumptions are prohibited:

- that assembly eligibility over authorized inputs grants ownership, interpretation authority, transformation authority, or policy authority over those inputs  
- that assembly may fabricate, infer, or synthesize briefing content  
- that assembly may regenerate, mutate, reorder, or reinterpret Premarket Scores  
- that assembly may expand authorized inputs  
- that assembly may repair PIT, identity, provenance, or conflict violations  
- that wall-clock time, randomness, runtime discovery, or mutable runtime state may affect assembly authority  
- that formatting, sections, templates, rendering, or presentation surfaces may redefine assembly authority  
- that Policy Versions may redefine assembly authority without a subsequent approved Governance Decision  
- that Dashboard, Human Review, AI Decision Engine, or Broker Execution may redefine assembly authority  
- that the existence or evolution of any downstream consumer may alter assembly authority  

---

## Implementation Impact

Implementation may assemble Morning Briefings only from repository-authorized inputs and only under the assembly authority frozen by this decision.

Implementation shall never redefine, expand, or reinterpret assembly authority.  
Documentation and contracts must preserve this assembly boundary.  
Implementation must treat assembly as read-only, deterministic, presentation-neutral participation of authorized inputs under the frozen Morning Briefing Policy Version identity once that Policy Version is approved.

This decision does not authorize implementation.

---

## Future Compatibility

The assembly authority frozen by this decision is immutable across Morning Briefing Policy Versions unless superseded by a subsequent approved Governance Decision.

Future Policy Versions may define deterministic assembly behavior within this authority.  
They may not redefine assembly authority, authorize fabrication, inference, or synthesis, expand authorized inputs, or alter semantic meaning without a subsequent approved Governance Decision.

Morning Briefing remains subordinate to Sprint 8 Governance Decisions, Premarket Scoring semantic authority, Morning Briefing Governance Decision #1, and Morning Briefing Governance Decision #2.

---

## Resolution

**Status:** RESOLVED  

**Governance effect:** Brief assembly authority for Morning Briefing is frozen. All subsequent Morning Briefing Governance Decisions, Morning Briefing Policy Version v1, and any later authorized Morning Briefing implementation remain subordinate to this decision.
