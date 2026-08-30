# AI Decision Engine Governance Decision #4 — Identity

**Decision ID:** `ai-decision-engine.governance.04-identity`
**Title:** Decision #4 — Identity
**Status:** RESOLVED
**Document class:** Governance Decision only
**Bounded context:** AI Decision Engine

**Subordinate to:**

- Sprint 12 Planning Gate (`sprint-12.planning-gate`) — APPROVED
- AI Decision Engine Architecture v1 (`ai-decision-engine.architecture.v1`) — APPROVED
- AI Decision Engine Governance Decision #1 — Semantic Boundary
- AI Decision Engine Governance Decision #2 — Authorized Inputs
- AI Decision Engine Governance Decision #3 — AI Decision Authority
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

This Governance Decision is the sole Governance authority for the semantic
identity boundary of a canonical AI Decision Engine decision.

It does not define authority, provenance, replay mechanics, PIT algorithms,
output or abstention taxonomy, human approval, model participation, concrete
identity composition, identity algorithms, schemas, APIs, storage, persistence,
serialization, or implementation.

---

## Purpose

Freeze the semantic identity requirements that make a canonical AI Decision
Engine decision stably identifiable, distinguishable, and referenceable within
the AI Decision Engine bounded context.

Identity answers:

> Which ADE decision is this?

Identity does not answer:

> Is this decision authoritative?

Authority remains governed by Decision #3. Identity is not authority and does
not independently create authority.

---

## Immutable Concern

This Decision freezes only:

- ADE ownership of canonical ADE decision identity;
- stable semantic identifiability within ADE scope;
- semantic uniqueness and distinctness;
- identity immutability once a canonical ADE decision is established;
- deterministic identifiability under equivalent governed semantic conditions;
- repeatable, audit-safe, replay-compatible referenceability;
- separation from upstream and downstream identities;
- prohibition of identity mutation, reassignment, reuse, aliasing, and drift;
- fail-closed behavior when valid ADE identity cannot be established.

This Decision does not freeze:

- a concrete identity name or field set;
- an identity tuple;
- an identity algorithm;
- a UUID or hash choice;
- a digest algorithm;
- a namespace format;
- canonical serialization;
- a database key;
- a storage or API representation;
- identity semantics for non-canonical outputs or evaluation attempts.

---

## Repository Constraints

AI Decision Engine is a distinct, deterministic, auditable, point-in-time-bound,
non-executing bounded context downstream of Human Review.

Decision #1 remains the authority for the AI Decision Engine semantic boundary.
Decision #2 remains the authority for authorized-input admission and imported
authority limits. Decision #3 remains the authority for the semantic authority
class of a canonical ADE decision.

The sole authorized upstream input remains Human Review public outputs through
approved Human Review public contracts, consumed as recorded human-attestation
context only.

Identity assignment, preservation, or reference shall not:

- transfer semantic ownership;
- expand authorized inputs;
- establish canonical authority;
- redefine Human Review semantics;
- reopen Architecture-deferred boundaries;
- create downstream consumption authority;
- create financial or execution authority.

This Decision shall not redesign or redefine Human Review, Dashboard, Morning
Briefing, Premarket Scoring, Strategy Engine, Risk, Portfolio, OMS, Broker
abstraction, or Broker Execution.

---

## Governance Definitions

### ADE Decision Identity

Repository-governed semantic identity belonging to a canonical ADE decision
within the AI Decision Engine bounded context.

This definition does not establish a concrete identifier, representation,
algorithm, or identity-bearing output schema.

### Semantic Identifiability

The Governance property that a canonical ADE decision can be distinguished
from other canonical ADE decisions and referred to without ambiguity within
ADE semantic scope.

### Identity Reference

A reference that identifies an ADE decision without transferring its ownership,
semantic authority, approval authority, or execution authority to the
referencing context.

### Identity Ownership

The limited ownership of ADE decision identity for canonical ADE decisions only.
It does not include ownership of upstream identities, downstream identities,
or the lifecycle of another bounded context.

### Equivalent Governed Conditions

The same governed semantic conditions as later defined by authorized Governance
and Policy, without this Decision selecting their exact composition,
serialization, or comparison mechanism.

### Materially Distinct Governed Context

A governed semantic context whose difference could make two ADE decisions
semantically different, including a materially different point-in-time context
or governing Policy semantics, without this Decision defining an exact identity
composition.

These definitions are Governance concepts only. They do not define schemas,
algorithms, storage, APIs, serialization, or runtime validation.

---

## Decision

### Identity Authority

This Governance Decision is the sole Governance authority for the semantic
identity boundary of a canonical ADE decision.

Neither Policy, implementation, downstream consumers, documentation, nor
operational procedures may redefine the identity requirements frozen here.

ADE owns identity for canonical ADE decisions only. Identity remains internal
to ADE and does not become authority in another bounded context.

### Semantic Identity Requirements

A canonical ADE decision identity shall be:

- ADE-owned;
- stable within ADE semantic scope;
- semantically unique;
- immutable once the canonical ADE decision is established;
- deterministically identifiable under equivalent governed semantic conditions;
- repeatably referenceable;
- compatible with audit and future replay/PIT semantics;
- distinct from upstream and downstream identities;
- independent of presentation, transport, and downstream consumers.

Semantically distinct canonical ADE decisions must not silently share the same
ADE decision identity.

The same governed semantic decision must not silently acquire unrelated
identities across equivalent governed evaluations.

Identity must not be silently mutated, reassigned, reused, or made to represent
different semantic meaning after canonical establishment.

### Identity Is Not Authority

The following distinction is binding:

```text
ADE decision identity
  ≠ ADE canonical authority
```

Identity answers which ADE decision is being identified. Authority answers
whether an ADE result is an authoritative canonical ADE decision.

A valid identity does not independently establish:

- canonical ADE authority;
- Human Review approval;
- human approval;
- trade approval;
- Strategy Engine authority;
- risk approval;
- portfolio authority;
- Order Intent;
- executable instruction;
- Broker Execution authorization.

Canonical authority remains subject to the deterministic, governed acceptance
requirement frozen by Decision #3. This Decision does not redefine that
requirement.

### Canonical Identity Scope

This Decision governs the semantic identity of a canonical ADE decision only.

It does not determine whether advisory material, a candidate result, an
abstention, rejection, failure, error, evaluation attempt, or other
non-authoritative material has an identity. That determination remains reserved
for Decision #7 and later Policy.

Identity cannot promote non-canonical material into canonical ADE authority.

---

## Human Review Identity Firewall

Human Review remains its own frozen Sprint 11 bounded context.

```text
Human Review identity
  ≠ ADE decision identity

Human Review record
  ≠ AI Decision

Human Review attestation
  ≠ ADE canonical authority
```

Human Review public outputs through approved Human Review public contracts remain
the sole authorized upstream input under Decision #2.

Human Review identity remains owned by Human Review. ADE may preserve or
reference an authorized upstream Human Review identity only as an upstream
reference.

ADE shall not:

- reuse Human Review identity as ADE decision identity;
- overwrite Human Review identity;
- mutate Human Review identity or records;
- reinterpret Human Review identity or semantics;
- fabricate or infer Human Review identity;
- claim ownership of Human Review identity;
- treat Human Review identity as ADE approval or canonical authority.

Preserving an upstream identity reference does not transfer semantic ownership,
identity ownership, or authority.

This Decision does not redesign Sprint 11 Human Review.

---

## Provenance Separation

Identity and provenance are separate Governance concerns.

```text
Identity
  = identifies the ADE decision

Provenance
  = explains lineage, evidence, and evaluation context
```

Identity is not a provenance record. Provenance is not identity.

Decision #4 does not freeze:

- provenance schema;
- evidence graph;
- source-chain representation;
- lineage format;
- provenance payload;
- provenance serialization;
- provenance persistence;
- audit-event schema.

Decision #5 — Provenance remains NOT STARTED and retains authority for those
concerns.

---

## Replay and PIT Separation

Decision #6 — Replay / PIT remains NOT STARTED.

Decision #4 freezes only the following compatibility requirements:

- materially distinct PIT contexts must not silently alias under one ADE
  decision identity;
- identical governed semantic conditions must not silently create conflicting
  identities;
- identity must not rely on mutable wall-clock state or runtime randomness for
  semantic sameness;
- identity must remain compatible with future replay and PIT semantics.

This Decision does not define:

- replay algorithm;
- replay lookup algorithm;
- PIT reconstruction;
- clock behavior;
- snapshot behavior;
- event sourcing;
- temporal storage;
- replay persistence;
- comparison implementation.

---

## Explicit UTC `as_of` Boundary

Decision #2 requires explicit UTC `as_of` and point-in-time-safe authorized
input handling.

A materially different point-in-time context must remain distinguishable for
ADE identity purposes when it produces materially distinct semantic meaning.

This Decision does not establish:

- `as_of` as a literal identity field;
- an identity tuple;
- timestamp normalization;
- timestamp serialization;
- timestamp comparison mechanics;
- temporal storage behavior.

Those details remain reserved for later Governance, Decision #6, and Policy as
authorized.

---

## Policy-Semantics Boundary

ADE decisions produced under materially different governing semantic Policy
contexts must not silently alias as the same semantic decision.

This is a non-aliasing Governance requirement. It does not define whether a
particular Policy Version is materially different, nor does it define Policy
equivalence.

This Decision does not create or authorize a Policy Version and does not define:

- Policy ID format;
- Policy Version format;
- an identity specification version;
- an exact Policy identity component;
- an equivalence algorithm;
- identity composition.

Policy Freeze remains DENIED.

---

## Output and Abstention Separation

Decision #7 — Output / Abstention remains NOT STARTED.

Decision #4 does not determine identity semantics for:

- abstention;
- rejection;
- failure;
- error;
- evaluation attempt;
- non-authoritative material;
- `DecisionProposal`;
- recommendation;
- action.

This Decision does not freeze:

- output taxonomy;
- abstention taxonomy;
- failure taxonomy;
- recommendation taxonomy;
- action taxonomy;
- reason codes;
- confidence semantics;
- output schema;
- `DecisionProposal` schema.

---

## Human Authority Separation

Decision #8 — Human Authority over ADE Outputs remains NOT STARTED.

Decision #4 does not define:

- reviewer identity semantics;
- approval workflow;
- approval state;
- sign-off;
- acceptance or rejection workflow;
- override behavior;
- proposal approval;
- human decision lifecycle.

An ADE identity reference identifies an ADE decision only. It does not imply
human approval or human authority over that decision.

---

## Determinism Boundary

Canonical ADE semantic identity must be deterministic under equivalent governed
semantic conditions.

Identity must not depend on:

- runtime randomness;
- mutable wall-clock generation;
- mutable runtime state;
- presentation;
- transport;
- downstream consumer behavior;
- operational environment discovery.

Nondeterministic material must not become a backdoor to canonical ADE identity
or authority.

This requirement does not define the deterministic identity algorithm.

---

## Model and Provider Firewall

This Decision does not authorize:

- an LLM;
- a model;
- a provider;
- a prompt;
- training;
- fine-tuning;
- inference;
- hosting;
- model integration.

The following must not independently define canonical ADE semantic identity:

- provider request ID;
- model run ID;
- model version ID;
- prompt ID;
- inference timestamp;
- stochastic seed.

Such values are not authorized ADE identity dependencies by this Decision.
Any future operational or provenance use requires separate authorization under
the applicable Governance and Policy boundaries.

---

## Sprint 4 Ownership Firewall

ADE decision identity remains distinct from:

- Strategy Engine identity;
- Risk decision identity;
- Portfolio instruction identity;
- OMS or order identity;
- Order Intent identity;
- broker order identity;
- execution identity;
- fill identity.

```text
ADE decision identity
  ≠ Strategy Engine identity
  ≠ Risk decision identity
  ≠ Portfolio instruction identity
  ≠ OMS/order identity
  ≠ Order Intent identity
  ≠ broker order identity
  ≠ execution identity
  ≠ fill identity
```

No ownership or lifecycle authority transfers through identity assignment or
reference. This Decision does not redesign Sprint 4.

---

## Authorized Input Firewall

Decision #4 creates no new input port.

The following remain closed:

- Dashboard;
- Morning Briefing;
- Premarket Scoring;
- Risk;
- Portfolio;
- Strategy Engine.

The following remain forbidden:

- raw Market Data as decision authority;
- Feature Platform internals;
- Feature Store internals;
- Strategy SDK internals;
- private upstream representations;
- OMS;
- Broker abstraction;
- live execution state.

Identity requirements must not introduce a source merely because it could help
construct identity. If identity would require an unauthorized source, the
identity condition fails closed. The source is not thereby authorized.

No fallback authority, hidden authority path, or model-context workaround is
created by this Decision.

---

## Fail-Closed Identity

If a purported canonical ADE decision cannot be established as having a valid,
stable, unambiguous identity under governed ADE semantics, it must not be
treated as a canonical authoritative ADE decision.

Identity shall not be established through:

- fallback identity;
- random identity;
- inferred identity;
- fabricated identity;
- repaired identity;
- substituted identity;
- silent identity promotion;
- silent identity mutation.

This Decision does not determine whether the resulting condition is represented
as abstention, rejection, error, failure, or no-decision. That remains reserved
for Decision #7 and Policy.

---

## Mutation, Collision, and Aliasing Boundary

The following semantic rules are binding:

- canonical identity is immutable;
- semantically distinct canonical ADE decisions cannot share identity;
- semantic drift cannot occur under an unchanged identity;
- identity cannot be silently reassigned;
- identity cannot be silently reused across materially distinct governed
  contexts;
- identity cannot silently alias an upstream or downstream identity;
- one semantic decision cannot silently acquire unrelated identities under
  equivalent governed conditions.

This Decision does not define:

- collision-detection algorithms;
- duplicate-detection algorithms;
- database uniqueness constraints;
- migration behavior;
- indexes;
- repair mechanisms.

---

## Downstream Reference Firewall

A downstream reference to ADE decision identity identifies an ADE decision only.

It does not confer:

- ADE semantic ownership;
- canonical authority;
- approval;
- trade authority;
- Strategy Engine authority;
- risk approval;
- portfolio authority;
- Order Intent;
- execution authority.

Downstream reference does not transfer ADE identity ownership, semantic
ownership, or lifecycle authority.

---

## Broker Execution Firewall

```text
AI Decision
  ≠ Order Intent
  ≠ executable instruction
  ≠ Broker Execution authorization
```

```text
ADE decision identity
  ≠ Order Intent identity
  ≠ broker order identity
  ≠ execution identity
  ≠ fill identity
  ≠ OMS lifecycle identity
```

Decision #4 authorizes none of the following:

- broker IDs as ADE authority;
- order IDs as ADE authority;
- execution IDs as ADE authority;
- fill IDs as ADE authority;
- OMS lifecycle IDs as ADE authority;
- broker APIs or SDKs;
- order submission;
- cancellation;
- replacement;
- fill processing;
- live trading;
- capital deployment;
- execution authorization.

Broker Execution remains DENIED / DEFERRED and requires a future independent
Planning Gate. Repository sequencing is not authorization.

---

## Reserved Later Governance Decisions

The following remain NOT STARTED and are not resolved by this Decision:

| # | Planned Decision | Status |
| --- | --- | --- |
| 5 | Provenance | NOT STARTED |
| 6 | Replay / PIT | NOT STARTED |
| 7 | Output / Abstention | NOT STARTED |
| 8 | Human Authority over AI Decision Engine Outputs | NOT STARTED |

Decision #4 does not pre-resolve any of these Decisions.

---

## Policy Boundary

Policy may later define, subject to completed Governance:

- exact identity dimensions;
- exact identity composition;
- exact identity fields;
- Policy ID and Policy Version treatment;
- exact `as_of` treatment;
- identity algorithm;
- UUID or hash choice;
- digest algorithm;
- namespace format;
- canonical serialization;
- identity specification versions;
- exact collision semantics;
- exact validation behavior;
- concrete failure behavior.

Policy must not redefine ADE identity ownership, expand authorized inputs,
transfer authority, or supersede this Decision.

This Decision does not create or authorize a Policy Version. Policy Freeze
remains DENIED.

---

## Implementation Boundary

Implementation remains DENIED.

This Decision does not define or authorize:

- packages, modules, or services;
- APIs, DTOs, or schemas;
- database tables or primary keys;
- persistence or indexes;
- queues or topics;
- serializers;
- UUID or hashing libraries;
- collision or duplicate detection;
- error mapping;
- deployment;
- model or provider integration.

Implementation must remain subordinate to the approved Planning Gate,
Architecture, and Governance Decisions.

---

## Explicit Non-Authorizations

Decision #4 does not authorize:

- Decision #5, #6, #7, or #8;
- Policy Freeze;
- Implementation Authorization;
- ADE implementation;
- model or provider integration;
- direct consumption of closed inputs;
- downstream consumption;
- human approval workflow;
- Order Intent creation;
- OMS mutation;
- broker integration;
- order submission, cancellation, or replacement;
- fill processing;
- live trading;
- capital deployment;
- execution authorization.

---

## Resolution

**Status:** RESOLVED

**Governance effect:** The semantic identity boundary for a canonical ADE
decision is frozen as ADE-owned, stable, semantically unique, immutable once
canonical, deterministically identifiable under equivalent governed semantic
conditions, repeatably referenceable, audit-safe, and compatible with future
replay/PIT semantics. Semantically distinct canonical ADE decisions cannot
silently share identity, and the same governed semantic decision cannot silently
acquire unrelated identities.

ADE identity remains distinct from Human Review identity, upstream and
downstream identities, canonical authority, approval, Order Intent, executable
instruction, and Broker Execution authorization. Identity does not transfer
ownership or authority.

Concrete identity composition and technical mechanisms remain reserved for
later Policy and implementation. Provenance, Replay / PIT, Output / Abstention,
and Human Authority over ADE Outputs remain reserved for Decisions #5–#8.

Governance remains IN PROGRESS — documentation-only. Decisions #1–#4 are
RESOLVED. Decisions #5–#8 remain NOT STARTED. Governance is not COMPLETE.
Policy Freeze, Implementation Authorization, Implementation, and Broker
Execution remain DENIED / DEFERRED.
