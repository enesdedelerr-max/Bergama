# Morning Briefing Governance Decision #8 — Ordering & Presentation Policy

**Decision ID:** `morning-briefing.governance.08-ordering-and-presentation-policy`
**Title:** Decision #8 — Ordering & Presentation Policy
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
- Morning Briefing Governance Decision #6 — Provenance Policy
- Morning Briefing Governance Decision #7 — Output Policy
- Premarket Scoring Governance Decisions #1–#12
- Premarket Scoring Engine Architecture v1
- Premarket Scoring Policy Version `premarket.scoring.policy.v1`

This Governance Decision freezes repository-wide ordering and presentation authority for Morning Briefing.
It does not define Architecture, Planning, Policy Version formulas, rendering, UI, templates, layouts, algorithms, APIs, storage, schemas, notification behavior, or implementation.

---

## Purpose

Freeze repository-wide governance for ordering and presentation within Morning Briefing.

This decision governs ordering authority and presentation authority only.

---

## Repository Constraints

Morning Briefing is a downstream consumer of Premarket Scoring.

Morning Briefing ordering and presentation governance shall remain subordinate to:

- semantic meaning under Governance Decision #1
- authorized input boundaries under Governance Decision #2
- assembly authority under Governance Decision #3
- replay authority under Governance Decision #4
- identity authority under Governance Decision #5
- provenance authority under Governance Decision #6
- output authority under Governance Decision #7
- Premarket Scoring Governance Decisions #1–#12
- Premarket Scoring Policy Version `premarket.scoring.policy.v1`

This decision shall not redesign any approved repository artifact.
Ordering remains subordinate to Premarket Scoring ordering authority.
Presentation remains presentation-only.

---

## Governance Definitions

### Ordering Authority

The repository-approved authority defining whether and how instrument or score order may appear within Morning Briefing without acquiring Premarket Scoring ordering ownership.

### Presentation Authority

The repository-approved authority defining presentation-only obligations for Morning Briefing outputs without acquiring Dashboard, UI, rendering, or product-surface authority.

### Ordering Stability

The requirement that Premarket Scoring ordering referenced by Morning Briefing remain preserved exactly as received from Premarket Scoring public outputs.

### Presentation Stability

The requirement that presentation authority remain presentation-only and invariant under later frozen policy with respect to semantic meaning, identity, provenance, and authorized input boundaries.

These definitions are governance concepts only.

---

## Decision

### Ordering Authority

This Governance Decision, together with Premarket Scoring ordering authority, is the sole ordering authority relevant to Morning Briefing.

Neither implementation, Policy Versions, downstream bounded contexts, documentation, nor operational procedures may redefine Premarket Scoring ordering authority through Morning Briefing.

Morning Briefing does not own Premarket Score ordering.
Morning Briefing acquires preservation authority only over ordering as received through approved Premarket Scoring public contracts.

### Presentation Authority

This Governance Decision is the sole presentation authority for Morning Briefing at Governance fidelity.

Neither implementation, Policy Versions, downstream bounded contexts, documentation, nor operational procedures may redefine the presentation authority frozen by this decision.

Presentation authority governs only presentation-only obligations for Morning Briefing outputs.
It does not grant rendering authority, UI authority, template authority, layout authority, Dashboard authority, decisioning authority, approval authority, or execution authority.

### Ordering Stability

Morning Briefing shall preserve Premarket Scoring ordering exactly as received.

Morning Briefing shall not reorder Premarket Scores.
Morning Briefing shall not mutate Premarket Scoring ordering authority.
Morning Briefing shall not invent an independent instrument ranking that replaces Premarket Scoring order.

### Presentation Stability

Presentation shall remain presentation-only.

Presentation shall not alter semantic meaning, authorized inputs, assembly authority, replay authority, identity, provenance, or output authority.
Presentation mechanisms remain outside this Governance Decision and shall not redefine Morning Briefing meaning.

### Presentation Independence

Presentation authority shall remain invariant regardless of rendering technology, delivery channel, transport mechanism, or downstream product surface.

Changes to presentation technology shall not redefine presentation authority.

### Ordering and Presentation shall never

- change semantic meaning
- reinterpret scores
- mutate ordering authority
- change identity
- change provenance
- become Dashboard behavior
- become UI behavior
- become implementation behavior
- regenerate, mutate, or reorder Premarket Scores
- invent, fabricate, infer, or synthesize evidence
- authorize trading or bypass risk, compliance, review, kill-switch, or execution controls

### Replay Compatibility

Ordering and presentation authority shall remain replay-compatible under Governance Decision #4.

Pinned authorized inputs, pinned configuration, pinned Policy Version identity, and explicit UTC `as_of` shall preserve the same Premarket Scoring order references and the same presentation-only obligations under later frozen policy.
Ordering and presentation authority shall never depend on wall-clock time, randomness, mutable runtime state, implementation discovery, external side effects, or downstream consumers.

### PIT Compatibility

Ordering and presentation authority shall remain PIT-compatible.

Only Premarket Scoring ordering valid for the explicit UTC `as_of` may participate.
Ordering and presentation shall not repair PIT violations.
Future knowledge shall not enter ordering or presentation authority.

### Determinism

Same authorized inputs, same explicit UTC `as_of`, same frozen Policy Version identity, and same frozen configuration shall preserve the same Premarket Scoring order references under later frozen policy.

Presentation-only obligations shall remain deterministic with respect to semantic meaning, identity, provenance, and authorized input boundaries.

### Consumer Independence

Ordering and presentation authority shall remain invariant regardless of the number, type, or existence of downstream consumers.

The introduction, removal, or evolution of downstream bounded contexts shall not modify the ordering or presentation authority frozen by this decision.

### Identity Compatibility

Ordering and presentation shall preserve Morning Briefing identity and upstream Premarket Score identity references under Governance Decision #5.

Ordering and presentation shall not replace, rewrite, invent, or synthesize identities.

### Provenance Compatibility

Ordering and presentation shall preserve Morning Briefing provenance and upstream Premarket Score provenance references under Governance Decision #6.

Ordering and presentation shall not rewrite, invent, omit, or synthesize provenance.

### Semantic Preservation

Ordering and presentation shall preserve Premarket Score semantic meaning under Premarket Scoring Governance Decision #1 and Morning Briefing semantic meaning under Morning Briefing Governance Decision #1.

Preservation or presentation of order shall not reinterpret scores as investment advice, recommendations, approvals, or execution authority.

### Fail Closed

Conditions that would reorder Premarket Scores, mutate ordering authority, alter identity or provenance, or convert presentation into Dashboard, UI, decisioning, or execution behavior shall never become valid through implementation behavior.

Implementation shall not silently substitute, infer, discover, fabricate, or synthesize ordering or presentation outcomes to complete emission.
Prohibited ordering or presentation conditions shall abort; silent partial success is forbidden.

### Contract Stability

Ordering references shall be consumed only through approved Premarket Scoring public contracts.

Presentation authority shall not be derived from implementation-private representations, Dashboard state, UI state, or notification state.

### Relationship to Premarket Scoring

Premarket Scoring retains exclusive ownership of Premarket Score ordering under Premarket Scoring Governance Decision #12 and Policy Version `premarket.scoring.policy.v1`.

Morning Briefing remains a read-only consumer of that ordering.
Morning Briefing shall never claim ranking authority.

### Relationship to Dashboard and UI

Dashboard and UI are deferred downstream concerns.

Morning Briefing ordering and presentation authority does not become Dashboard behavior or UI behavior.
Future Dashboard or UI surfaces may consume Morning Briefing outputs only through later approved Planning Gates and architectures and shall not redefine ordering or presentation authority.

---

## Prohibited Assumptions

The following assumptions are prohibited:

- that Morning Briefing may reorder Premarket Scores or replace Premarket Scoring ordering authority
- that presentation may change semantic meaning or reinterpret scores
- that ordering or presentation may mutate identity or provenance
- that ordering or presentation may become Dashboard, UI, or implementation behavior
- that rendering, templates, layouts, or algorithms may redefine ordering or presentation authority
- that rendering technology, delivery channel, transport mechanism, or downstream product surface may redefine presentation authority
- that wall-clock time, randomness, mutable runtime state, implementation discovery, or external side effects may participate in ordering or presentation authority
- that Policy Versions may redefine ordering or presentation authority without a subsequent approved Governance Decision
- that downstream consumers may redefine ordering or presentation authority
- that the existence or evolution of any downstream consumer may alter ordering or presentation authority

---

## Implementation Impact

Implementation may preserve ordering and apply presentation-only obligations only under the authority frozen by this decision.

Implementation shall never redefine, expand, or reinterpret ordering or presentation authority.
Documentation and contracts must preserve this boundary.
Implementation must treat Premarket Scoring order as read-only and presentation as presentation-only under the frozen Morning Briefing Policy Version identity once that Policy Version is approved.

This decision does not authorize implementation.

---

## Future Compatibility

The ordering and presentation authority frozen by this decision is immutable across Morning Briefing Policy Versions unless superseded by a subsequent approved Governance Decision.

Future Policy Versions may define deterministic ordering-preservation and presentation-only behavior within this authority.
They may not redefine ordering or presentation authority, authorize reordering of Premarket Scores, mutate identity or provenance, alter semantic meaning, or convert Morning Briefing into Dashboard or UI authority without a subsequent approved Governance Decision.

Future Dashboard, Human Review, AI Decision Engine, and Broker Execution consumers may consume Morning Briefing outputs only as operator attention context.
They must not redefine Morning Briefing ordering or presentation as ranking authority, investment advice, approval, or execution authority.

Morning Briefing remains subordinate to Sprint 8 Governance Decisions, Premarket Scoring ordering authority, and Morning Briefing Governance Decisions #1–#7.

---

## Resolution

**Status:** RESOLVED

**Governance effect:** Ordering and presentation authority for Morning Briefing is frozen. All subsequent Morning Briefing Policy Version v1 work and any later authorized Morning Briefing implementation remain subordinate to this decision and to Morning Briefing Governance Decisions #1–#7.
