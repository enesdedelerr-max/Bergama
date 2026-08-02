# Morning Briefing Governance Decision #4 — Replay Policy

**Decision ID:** `morning-briefing.governance.04-replay-policy`
**Title:** Decision #4 — Replay Policy
**Status:** RESOLVED
**Document class:** Governance Decision only
**Bounded context:** Morning Briefing

**Subordinate to:**

- Sprint 9 Planning Gate (`sprint-9.planning-gate`)
- Morning Briefing Architecture v1 (`morning-briefing.architecture.v1`)
- Morning Briefing Governance Decision #1 — Semantic Boundary
- Morning Briefing Governance Decision #2 — Authorized Inputs
- Morning Briefing Governance Decision #3 — Brief Assembly Policy
- Premarket Scoring Governance Decisions #1–#12
- Premarket Scoring Engine Architecture v1
- Premarket Scoring Policy Version `premarket.scoring.policy.v1`

This Governance Decision freezes repository-wide replay authority for Morning Briefing.
It does not define Architecture, Planning, Policy Version formulas, algorithms, APIs, storage, schemas, notification behavior, or implementation.

---

## Purpose

Freeze repository-wide replay governance for Morning Briefing.

This decision governs replay authority only.

---

## Repository Constraints

Morning Briefing is a downstream consumer of Premarket Scoring.

Morning Briefing replay shall remain subordinate to:

- semantic meaning under Governance Decision #1
- authorized input boundaries under Governance Decision #2
- assembly authority under Governance Decision #3
- Premarket Scoring Governance Decisions #1–#12
- Premarket Scoring Policy Version `premarket.scoring.policy.v1`

This decision shall not redesign any approved repository artifact.
Replay shall never redefine Premarket Score semantics or Morning Briefing semantic meaning.

---

## Governance Definitions

### Replay

The deterministic re-execution of Morning Briefing assembly under pinned authorized inputs, pinned configuration, pinned Policy Version identity, and an explicit UTC `as_of`.

### Replay Authority

The repository-approved authority defining the conditions under which Morning Briefing results are replay-valid.

### Replay Determinism

The requirement that identical pinned replay inputs produce identical Morning Briefing results under the frozen Policy Version.

### Replay Inequality

Any divergence between Morning Briefing results produced from identical pinned replay inputs under the same frozen Policy Version and configuration.

These definitions are governance concepts only.

---

## Decision

### Replay Authority

This Governance Decision is the sole replay authority for Morning Briefing.

Neither implementation, Policy Versions, downstream bounded contexts, documentation, nor operational procedures may redefine the replay authority frozen by this decision.

Replay authority governs only replay eligibility and replay validity.
It does not grant ownership of upstream artifacts, decisioning authority, approval authority, execution authority, formatting authority, or presentation authority.

### Replay Scope

Morning Briefing replay may:

- re-execute Morning Briefing assembly under pinned authorized inputs
- bind replay to an explicit UTC `as_of`
- bind replay to a frozen Morning Briefing Policy Version identity
- bind replay to frozen Morning Briefing configuration
- compare replay results for equality under later frozen policy

Morning Briefing replay shall never:

- regenerate Premarket Scores
- mutate, replace, repair, reinterpret, or regenerate authorized inputs
- invent, fabricate, infer, or synthesize briefing content
- expand authorized inputs
- depend on non-replayable state
- redefine semantic meaning, identity, provenance, or ordering

### Replay Determinism

Same authorized inputs, same explicit UTC `as_of`, same frozen Policy Version identity, and same frozen configuration shall produce the same Morning Briefing result.

Replay inequality under identical pinned conditions is a hard failure.
Silent acceptance of replay inequality is forbidden.

### Replay shall depend ONLY on

- authorized inputs under Governance Decision #2
- explicit UTC `as_of`
- frozen Morning Briefing Policy Version identity
- frozen Morning Briefing configuration

### Replay shall NEVER depend on

- wall-clock time
- randomness
- mutable runtime state
- implementation discovery
- external side effects
- downstream consumers
- Dashboard state
- UI state
- notification state
- Human Review decisions
- AI Decision Engine outputs
- Broker Execution state

### Replay Identity

Replay shall preserve upstream identity references exactly as received.

Replay shall not replace, rewrite, or synthesize upstream identities.
Morning Briefing identity produced under replay shall remain distinct from Premarket Score identity and shall remain deterministic under later frozen identity governance.

### Replay Provenance

Replay shall preserve upstream provenance references exactly as received.

Replay shall not invent, rewrite, or omit provenance relationships.
Morning Briefing provenance produced under replay shall remain distinct from Premarket Score provenance and shall remain deterministic under later frozen provenance governance.

### Replay PIT

Replay shall remain PIT-compatible.

Only repository-approved authorized inputs valid for the explicit UTC `as_of` may participate in replay.
Replay shall not repair PIT violations.
Future knowledge shall not enter replay.

### Replay Configuration

Replay shall consume only repository-approved Morning Briefing configuration.

Configuration used in replay shall be pinned.
Runtime-discovered, mutable, or environment-derived configuration that is not repository-approved and pinned is forbidden in deterministic replay paths.

### Replay Policy Version

Replay shall bind to exactly one frozen Morning Briefing Policy Version identity for a given replay execution.

Silent Policy Version substitution during replay is forbidden.
Unsupported or mismatched Policy Version identity shall fail closed.

### Preservation Obligations

Replay shall preserve:

- semantic meaning under Governance Decision #1
- authorized input boundaries under Governance Decision #2
- assembly authority under Governance Decision #3
- Premarket Score identity references
- Premarket Score provenance references
- Premarket Score ordering as received from Premarket Scoring
- score domain expectations visible to the consumer

### Fail Closed

Unauthorized, missing, conflicting, stale, or non-replayable conditions shall never become replay-valid through implementation behavior.

Implementation shall not silently substitute, infer, discover, fabricate, synthesize, or repair inputs to complete replay.
Replay inequality under identical pinned conditions shall abort as failure.

### Contract Stability

Replay shall consume authorized inputs only through approved repository public contracts.

Implementation shall not replay from implementation-private representations of otherwise authorized repository artifacts.

### Consumer Independence

Replay authority shall remain invariant regardless of the number, type, or existence of downstream consumers.

The introduction, removal, or evolution of downstream bounded contexts shall not modify the replay authority frozen by this decision.

### Semantic Preservation

Replay shall preserve Premarket Score semantic meaning under Premarket Scoring Governance Decision #1 and Morning Briefing semantic meaning under Morning Briefing Governance Decision #1.

Successful replay shall not confer recommendation, approval, or execution authority.

---

## Prohibited Assumptions

The following assumptions are prohibited:

- that replay may depend on wall-clock time, randomness, mutable runtime state, implementation discovery, or external side effects
- that replay may regenerate, mutate, reorder, or reinterpret Premarket Scores
- that replay may fabricate, infer, or synthesize briefing content
- that replay may expand authorized inputs
- that replay may repair PIT, identity, provenance, or conflict violations
- that replay inequality under identical pinned conditions may be silently accepted
- that Policy Version identity may be silently substituted during replay
- that downstream consumers may redefine replay authority
- that Policy Versions may redefine replay authority without a subsequent approved Governance Decision
- that the existence or evolution of any downstream consumer may alter replay authority

---

## Implementation Impact

Implementation may replay Morning Briefings only under the replay authority frozen by this decision.

Implementation shall never redefine, expand, or reinterpret replay authority.
Documentation and contracts must preserve this replay boundary.
Implementation must treat replay as deterministic re-execution under pinned authorized inputs, pinned configuration, pinned Policy Version identity, and explicit UTC `as_of` once the Morning Briefing Policy Version is approved.

This decision does not authorize implementation.

---

## Future Compatibility

The replay authority frozen by this decision is immutable across Morning Briefing Policy Versions unless superseded by a subsequent approved Governance Decision.

Future Policy Versions may define deterministic replay behavior within this authority.
They may not redefine replay authority, authorize non-replayable dependencies, expand authorized inputs, or alter semantic meaning without a subsequent approved Governance Decision.

Morning Briefing remains subordinate to Sprint 8 Governance Decisions, Premarket Scoring semantic authority, and Morning Briefing Governance Decisions #1–#3.

---

## Resolution

**Status:** RESOLVED

**Governance effect:** Replay authority for Morning Briefing is frozen. All subsequent Morning Briefing Governance Decisions, Morning Briefing Policy Version v1, and any later authorized Morning Briefing implementation remain subordinate to this decision.
