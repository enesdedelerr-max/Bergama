# AI Decision Engine Policy Version v1 Specification

## Version Metadata

| Field | Value |
|-------|-------|
| Policy Version ID | `ai-decision-engine.policy.v1` |
| Policy Version Label | AI Decision Engine Policy Version v1 |
| Status | APPROVED |
| Document class | Policy Version / Policy Freeze only |
| Bounded context | AI Decision Engine |
| Governance Dependency | AI Decision Engine Governance Decisions #1–#8 (immutable) |
| Architecture Dependency | AI Decision Engine Architecture v1 (immutable) |
| Planning Dependency | Sprint 12 Planning Gate (`sprint-12.planning-gate`) (immutable) |
| Upstream Human Review Policy Dependency | `human-review.policy.v1` (immutable; via Human Review public outputs only) |
| Model Participation | UNAUTHORIZED under this Policy Version |
| Implementation Authorization | DENIED |
| Broker Execution | DENIED / DEFERRED |

This document freezes Policy Freeze semantics under Policy Version
`ai-decision-engine.policy.v1`. Workflow approval prerequisites — commit, PR,
CI, external approval, merge, and post-merge verification — are complete.
Policy workflow status is APPROVED. Sprint 12 remains not complete.
Implementation Authorization remains DENIED. Implementation remains DENIED.
Broker Execution remains DENIED / DEFERRED. Model participation remains
UNAUTHORIZED under this Policy Version.

---

## Purpose

This specification freezes the semantic behavioral Policy of the AI Decision
Engine under Policy Version `ai-decision-engine.policy.v1`.

Governance Decisions #1–#8 define what ADE is permitted to mean and own.
`ai-decision-engine.policy.v1` defines how authorized ADE governed evaluation
behavior shall operate within those boundaries.

This Policy Version is subordinate to:

- Sprint 12 Planning Gate (`sprint-12.planning-gate`)
- AI Decision Engine Architecture v1 (`ai-decision-engine.architecture.v1`)
- AI Decision Engine Governance Decisions #1–#8
- Human Review Governance Decisions #1–#8
- Human Review Policy Version `human-review.policy.v1`
- Dashboard, Morning Briefing, and Premarket Scoring frozen Governance and
  Policy artifacts as immutable upstream foundations (not ADE inputs)

This document does not modify, reinterpret, expand, or supersede any approved
repository artifact. Policy Freeze is subordinate to Governance.
`ai-decision-engine.policy.v1` shall never redesign Architecture, expand
authorized inputs, authorize implementation, authorize Broker Execution, or
modify upstream semantic meaning.

This Policy Version freezes semantics only. It does not define APIs, schemas,
DTOs, enums as implementation artifacts, storage, persistence, UI, workflow
engines, RBAC, SSO, packages, services, model adapters, prompts, providers,
deployment topology, or trading/execution mechanisms.

---

## Explicit Exclusions

This Policy Version does not authorize or define:

- Implementation Authorization or Implementation;
- APIs, endpoints, schemas, DTOs, JSON, protobuf, events, queues, or topics;
- database tables, migrations, storage, caches, or retention mechanisms;
- UI, dashboards, approval screens, notifications, or workflow engines;
- RBAC, SSO, user DTO, authentication providers, or permissions tables;
- identity UUID, hash, tuple, digest, or key formats;
- provenance WORM, event sourcing, signatures, or registry mechanisms;
- replay snapshots, temporal databases, or reconstruction algorithms;
- BUY / SELL / HOLD / NO_TRADE / NEUTRAL / WAIT / LONG / SHORT / ENTER / EXIT;
- position sizing, allocation, or execution instructions;
- Strategy, Risk, Portfolio, Order Intent, OMS, or Broker Execution authority;
- model, provider, prompt, temperature, seed, SDK, hosting, training, or
  fine-tuning;
- model participation of any kind under this Policy Version.

---

## Governance Dependencies

This Policy Version SHALL comply with all of the following immutable AI
Decision Engine Governance Decisions:

| Decision | Title | Binding effect on v1 |
|----------|-------|----------------------|
| #1 | Semantic Boundary | ADE is a distinct, deterministic, auditable, non-executing bounded context; no ownership of upstream or Sprint 4 / Broker domains |
| #2 | Authorized Inputs | Sole authorized upstream is Human Review public outputs through approved public contracts as recorded attestation context only |
| #3 | AI Decision Authority | Canonical ADE authority requires deterministic governed acceptance; model/confidence/HR/disposition alone cannot create authority |
| #4 | Identity | Canonical ADE decision identity semantics remain Decision #4-owned; Policy does not redefine identity mechanisms |
| #5 | Provenance | Canonical ADE provenance and Policy-context attribution requirements remain Decision #5-owned |
| #6 | Replay / PIT | Historical replay is bound to original PIT and Policy semantic context; replay ≠ new decision |
| #7 | Output / Abstention | Minimum ADE outcome classes are authoritative decision outcome and explicit abstention only |
| #8 | Human Authority | Human disposition is distinct from ADE output and Human Review; disposition does not create #3 authority or trading/execution authority |

This Policy Version SHALL also preserve:

- Human Review semantic meaning under Human Review Governance Decision #1 and
  Policy Version `human-review.policy.v1`
- Sprint 4 Strategy Engine, Risk, Portfolio, and OMS ownership
- Broker Execution DENIED / DEFERRED posture

Policy SHALL NOT reopen, redefine, or supersede Decisions #1–#8.

---

## Authorized Input Admission Policy

### Sole authorized upstream

v1 SHALL admit only:

**Human Review public outputs** through approved Human Review public contracts
under Human Review Policy Version `human-review.policy.v1`, consumed as
recorded human-attestation context only, with attributable Human Review
identity and provenance references as received, under an explicit UTC `as_of`
evaluation context.

No secondary authorized ADE upstream input surface exists under this Policy
Version.

### Forbidden inputs

v1 SHALL NOT consume or treat as ADE authority:

- Dashboard public outputs as ADE inputs;
- Morning Briefing public outputs as ADE inputs;
- Premarket Scoring public outputs as ADE inputs;
- Risk, Portfolio, or Strategy Engine outputs as ADE inputs;
- raw Market Data;
- Feature Platform, Feature Store, or Strategy SDK internals;
- implementation-private Human Review or other upstream representations;
- OMS state;
- Broker or live execution state;
- fills or execution history as ADE authority;
- model output as authorized upstream evidence;
- mutable UI, rendering, product-surface, or notification state;
- caches, logs, archives, or enrichment paths as substitute authorized input;
- any information not admitted under Decision #2 and this section.

### Admissibility and fail-closed admission

Authorized Human Review evidence is admissible for ADE evaluation only when it
is:

- present through an approved Human Review public contract;
- valid and semantically compatible with frozen Human Review meaning;
- attributable;
- temporally admissible under the evaluation's explicit UTC `as_of`;
- non-conflicting and non-ambiguous for the required evaluation context;
- not stale relative to the governed PIT requirements.

If required authorized evidence is missing, invalid, stale, conflicting,
ambiguous, temporally mismatched, insufficiently attributable, or otherwise
inadmissible:

- ADE SHALL NOT invent, repair, infer, synthesize, substitute, or discover
  replacement evidence;
- ADE SHALL NOT fall back to any forbidden input;
- ADE SHALL NOT establish Decision #3 canonical authority;
- the governed ADE outcome SHALL be explicit abstention under Outcome /
  Abstention Policy below.

No repair. No inference. No substitution. No fallback source. No hidden input
path.

---

## Deterministic Governed Acceptance Policy

Decision #3 remains the sole Governance owner of canonical ADE authority
semantics.

Under this Policy Version, ADE may recognize a result as Decision #3
canonical ADE authority only when all of the following semantic conditions
hold:

1. Required authorized Human Review evidence is admissible under Authorized
   Input Admission Policy.
2. The evaluation is bound to one explicit UTC `as_of` / PIT context.
3. The evaluation is attributable to exactly one applicable frozen Policy
   semantic context equal to `ai-decision-engine.policy.v1` (or a later
   separately authorized successor Policy Version under its own rules).
4. Acceptance conditions are deterministic: identical authorized evidence,
   identical Policy semantic context, and identical PIT/`as_of` context yield
   the same acceptance result.
5. Acceptance is compatible with Decision #4 identity semantics for a
   canonical ADE decision.
6. Acceptance is compatible with Decision #5 provenance semantics, including
   Policy-context attribution.
7. Acceptance is compatible with Decision #6 Replay / PIT semantics.
8. No forbidden authority source is used to establish acceptance.

If any required condition cannot be established:

```text
NO authoritative ADE decision exists.
```

Use fail-closed treatment. The governed ADE outcome SHALL be explicit
abstention.

This Policy Version does not define acceptance algorithms, formulas, scores,
confidence thresholds, numeric thresholds, ranking, or canonicalization
implementation.

---

## Authority Firewall

Under this Policy Version:

```text
model output alone
  ≠ Decision #3 canonical ADE authority

model confidence
  ≠ Decision #3 canonical ADE authority

model explanation / reasoning
  ≠ Decision #3 canonical ADE authority

Human Review attestation
  ≠ Decision #3 canonical ADE authority

human disposition
  ≠ Decision #3 canonical ADE authority

presentation / serialization / storage / packaging
  ≠ Decision #3 canonical ADE authority

absence of failure
  ≠ Decision #3 canonical ADE authority
```

Human Review attestation remains Decision #2 recorded attestation context only.
Human disposition remains Decision #8 distinct downstream semantics.

---

## Outcome / Abstention Policy

Decision #7 remains the sole Governance owner of ADE outcome-class semantics.

This Policy Version preserves exactly two ADE-owned governed outcome classes:

1. Authoritative ADE decision outcome
2. Explicit ADE abstention

### Completeness rule

If Decision #3 canonical ADE authority cannot be established under Deterministic
Governed Acceptance Policy, the governed ADE outcome MUST be **explicit ADE
abstention**.

Silent absence of every ADE outcome, invented authority, or silent promotion of
non-authoritative material is forbidden.

Authoritative ADE decision outcome exists only when Decision #3 canonical
authority has been established under this Policy Version.

Richer outcome taxonomies are not required and remain deferred.

---

## Abstention Firewall

```text
explicit ADE abstention
  ≠ NO_TRADE
  ≠ HOLD
  ≠ NEUTRAL
  ≠ WAIT
  ≠ human rejection
  ≠ provider refusal
  ≠ Broker cancellation
  ≠ execution instruction
  ≠ Strategy signal
  ≠ Risk approval
  ≠ Portfolio instruction
  ≠ Order Intent
  ≠ OMS instruction
```

---

## Fail-Closed Outcome Policy

Already-governed inability conditions under Decisions #2–#6 and this Policy
Version — including missing, invalid, stale, conflicting, ambiguous,
temporally invalid, or insufficiently attributable evidence, identity
insufficiency, provenance insufficiency, Policy-context insufficiency, or
inability to establish deterministic governed acceptance — MUST NOT create
Decision #3 authority.

Under this Policy Version, those conditions resolve to:

```text
explicit ADE abstention / non-acceptance
```

consistent with Governance Decision #7.

No fallback authority. No evidence repair. No inferred trade action.

---

## Reason Semantics

This Policy Version freezes semantic reason **categories** sufficient to make
authoritative ADE outcomes, explicit abstention, and fail-closed treatment
auditable and attributable.

Material semantic category families include:

- accepted governed evidence;
- missing authorized evidence;
- invalid authorized evidence;
- stale evidence;
- conflicting or ambiguous evidence;
- temporal / PIT mismatch;
- identity insufficiency;
- provenance insufficiency;
- deterministic acceptance not established;
- Policy-context insufficiency.

These are semantic categories only. This Policy Version does not define DTO
fields, numeric codes, database values, API enums, or machine code catalogs.

Exact machine reason codes remain reserved for later Implementation
Authorization.

---

## Identity Boundary

Decision #4 remains the sole Governance authority for canonical ADE decision
identity semantics.

This Policy Version requires compliance with Decision #4. It does not own or
redefine identity mechanics.

This Policy Version does not define UUID, hash, key, tuple, database
identifier, or serialization identity.

Explicit abstention remains outside the Decision #4 canonical decision identity
domain. Technical identity representation for abstention remains deferred.

---

## Provenance / Policy Context

Decision #5 remains the sole Governance authority for canonical ADE provenance
semantics.

Under this Policy Version:

- Every accepted canonical ADE decision MUST be attributable to exactly one
  applicable frozen Policy semantic context.
- For evaluations under this Version, that context is
  `ai-decision-engine.policy.v1`.
- Policy-context attribution must be sufficient to distinguish the governing
  semantics under which the outcome was established.
- Historical meaning cannot be rewritten by later Policy.

This Policy Version does not select Policy hash, version-field representation,
registry, database key, signature, WORM, event sourcing, or storage layout.

---

## Replay / PIT Policy

Decision #6 remains the sole Governance authority for Replay / PIT semantics.

Under this Policy Version:

- Historical replay uses the original applicable Policy semantic context.
- Later Policy does not rewrite prior outcomes.
- Reevaluation under a later Policy context is a **new** evaluation context,
  not historical replay.
- Same authorized evidence + same frozen Policy semantic context + same
  PIT/`as_of` context MUST yield the same governed acceptance result and the
  same outcome class.

This Policy Version does not define replay infrastructure, algorithms,
snapshots, temporal databases, or clocks.

---

## Reevaluation Policy

Under this Policy Version:

- reevaluation ≠ historical replay;
- prior ADE outcomes remain immutable;
- later-Policy reevaluation is a distinct evaluation;
- newly available evidence remains constrained by Decision #2 and Authorized
  Input Admission Policy;
- human disposition MUST NOT itself become ADE upstream evidence;
- disposition-as-input remains unauthorized without future approved
  Architecture and Governance amendment.

This Policy Version does not define a reevaluation workflow, API, queue, or
request protocol. Whether a human disposition may semantically *request*
reevaluation without becoming ADE input remains deferred and confers no
authority by silence.

---

## Human Disposition Policy

Decision #8 remains the sole Governance authority for human-disposition
semantic separation and firewalls.

Under this Policy Version:

- Human disposition is distinct from Human Review upstream attestation.
- Human disposition is distinct from the ADE-owned outcome.
- Human disposition is **not required** for ADE to produce a governed outcome
  (authoritative decision outcome or explicit abstention).
- Human disposition does not create Decision #3 canonical ADE authority.
- Human disposition does not reclassify Decision #7 outcome class.
- Human disposition cannot mutate, delete, erase, replace, or rewrite
  historical ADE outcome, identity, provenance, or PIT context.
- If a disposition is authoritative within its own semantic scope, it must be
  attributable to a human authority context; technical attribution mechanism
  remains unselected.
- No disposition may be inferred from absence, ambiguity, conflict, invalid
  attribution, UI access, or system access.
- No default approval.
- No default rejection.

### Minimal disposition semantic categories

If human disposition is recorded under this Policy Version, only the following
minimal semantic distinction is frozen:

1. **Disposition recorded** — an attributable human disposition concerning an
   ADE-owned output exists.
2. **No disposition recorded** — no attributable human disposition exists.

Exact action labels such as APPROVED, REJECTED, ACKNOWLEDGED, OVERRIDDEN,
ACCEPTED, DECLINED, or ESCALATED are **not** frozen as binding Policy enums
under v1. If later used under a subsequent authorized Policy Version, any such
label remains:

```text
≠ Decision #3 ADE authority
≠ trade authority
≠ Strategy signal
≠ Risk approval
≠ Portfolio instruction
≠ Order Intent
≠ OMS instruction
≠ Broker authorization
```

### Deferred human-authority concerns

The following remain deferred under v1 and confer no implicit authority:

- quorum;
- separation of duties;
- timeout;
- escalation hierarchy;
- detailed override catalog;
- detailed rejection catalog;
- concrete reviewer-role taxonomy;
- RBAC / SSO.

---

## Model Participation

Under Policy Version `ai-decision-engine.policy.v1`:

```text
MODEL PARTICIPATION = UNAUTHORIZED
```

No model-generated material participates in establishing Decision #3 canonical
ADE authority under this Policy Version.

No advisory-model path is authorized under v1.

Future model participation requires the prerequisite Architecture / Governance
path identified by authoritative documents before any later Policy Version may
permit it.

This Policy Version does not select a model, provider, prompt, temperature,
seed, SDK, API, hosting, training, or fine-tuning method, and does not define
model fallback behavior.

---

## Determinism

Under this Policy Version:

```text
same authorized evidence
+ same frozen Policy semantic context
+ same PIT / as_of context
→ same governed acceptance result
  and same outcome class
```

This is semantic determinism. This Policy Version does not require byte
equality and does not define hashing or canonicalization algorithms.

---

## Trading / Action Taxonomy Firewall

This Policy Version does not create or authorize:

- BUY;
- SELL;
- HOLD;
- NO_TRADE;
- WAIT;
- NEUTRAL;
- LONG;
- SHORT;
- ENTER;
- EXIT;
- position sizing;
- allocation;
- execution instruction.

An ADE decision is not silently a trading action.
Human disposition is not silently a trading action.

---

## Strategy / Risk / Portfolio Firewall

Sprint 4 ownership remains intact.

This Policy Version does not create:

- Strategy signal;
- Strategy approval;
- Risk approval;
- Risk override;
- Portfolio instruction;
- position instruction;
- allocation authority.

Human disposition does not create these either.

---

## Order Intent / OMS Firewall

```text
ADE outcome
  ≠ Order Intent
  ≠ OMS instruction

human disposition
  ≠ Order Intent
  ≠ OMS instruction
```

No order create, approve, mutate, or cancel semantics are authorized.
Proposal-to-Order-Intent conversion remains unauthorized.

---

## Broker Execution Firewall

Broker Execution remains DENIED / DEFERRED.

This Policy Version does not create routing, submit, replace, cancel, fill, or
execution authorization.

```text
human approval / disposition
  ≠ Broker Execution authorization
```

---

## Implementation Reservation

The following remain reserved for later Implementation Authorization and are
not selected by this Policy Version:

- Python classes, packages, modules, or services;
- interfaces, DTOs, schemas, JSON, protobuf;
- REST/GraphQL endpoints, queues, events, topics;
- database tables, migrations, indexes, storage, caches;
- UI, workflow engines, RBAC, SSO;
- exact enum implementation or machine reason codes;
- hash, signature, digest, or registry mechanisms;
- replay infrastructure;
- model adapters, provider SDKs, or prompts;
- deployment topology.

Implementation Authorization remains DENIED.
Implementation remains DENIED.

---

## Policy Freeze Completeness (v1 semantic set)

This Policy Version freezes the minimum Sprint 12 ADE Policy semantic set:

1. Sole HR authorized-input admission and fail-closed treatment.
2. Deterministic governed acceptance for Decision #3 authority.
3. Authority firewalls (model / confidence / HR / disposition / packaging).
4. Two outcome classes with abstention completeness.
5. Fail-closed outcome mapping to explicit abstention.
6. Semantic reason categories.
7. Policy-context attribution for canonical decisions.
8. Replay vs later-Policy reevaluation distinction.
9. Minimum human-disposition semantics and firewalls.
10. Model participation UNAUTHORIZED.
11. Trading / Strategy / Risk / Portfolio / Order Intent / OMS / Broker
    firewalls.
12. Implementation mechanisms reserved.

Quorum, SoD, timeouts, rich disposition catalogs, and model participation
remain deferred as stated and confer no authority.

---

## Resolution

**Status:** APPROVED

**Policy effect:** AI Decision Engine Policy Version `ai-decision-engine.policy.v1`
freezes semantics-only governed evaluation behavior subordinate to Planning,
Architecture, and Governance Decisions #1–#8. Sole authorized upstream remains
Human Review public outputs. Canonical ADE authority requires deterministic
governed acceptance and fails closed to explicit abstention. Model
participation is UNAUTHORIZED. Human disposition is optional for ADE outcome
production and never creates Decision #3, trading, Order Intent, OMS, or Broker
authority. Trading-action taxonomies remain unauthorized. Implementation
Authorization, Implementation, and Broker Execution remain DENIED / DEFERRED.

Policy Freeze workflow is APPROVED / complete. This does not complete Sprint 12
and does not authorize Implementation Authorization or Implementation.
