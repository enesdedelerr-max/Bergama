# AI Decision Engine Governance Decision #5 — Provenance

**Decision ID:** `ai-decision-engine.governance.05-provenance`
**Title:** Decision #5 — Provenance
**Status:** RESOLVED
**Document class:** Governance Decision only
**Bounded context:** AI Decision Engine

**Subordinate to:**

- Sprint 12 Planning Gate (`sprint-12.planning-gate`) — APPROVED
- AI Decision Engine Architecture v1 (`ai-decision-engine.architecture.v1`) — APPROVED
- AI Decision Engine Governance Decision #1 — Semantic Boundary
- AI Decision Engine Governance Decision #2 — Authorized Inputs
- AI Decision Engine Governance Decision #3 — AI Decision Authority
- AI Decision Engine Governance Decision #4 — Identity
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
- Sprint 4 Strategy Engine, Risk, Portfolio, OMS, and Broker ownership
  boundaries

This Governance Decision is the sole Governance authority for the semantic
provenance boundary of a canonical AI Decision Engine decision.

It does not define Architecture, Policy Freeze, implementation, provenance
fields, provenance IDs, schemas, graph structures, serialization, canonical
bytes, hashing, storage, persistence, database tables, indexes, events, APIs,
retention, cryptographic mechanisms, validation mechanisms, error mapping,
replay algorithms, PIT reconstruction, output taxonomy, abstention taxonomy,
human-authority workflows, model participation, or Broker Execution.

---

## Purpose

Freeze the semantic provenance requirements that make the lineage, authorized
evidence, source authority, governing context, and derivation history of a
canonical ADE decision attributable and auditable without transferring
semantic ownership or authority.

This Decision answers:

> What authoritative evidence and governed context is this ADE decision
> derived from, and can that lineage be proven?

Provenance explains lineage, evidence, and governed evaluation context.
Provenance does not answer which ADE decision is being identified or whether
that result possesses canonical ADE authority.

This Decision defines provenance semantics and ownership only.

---

## Immutable Concern

This Decision freezes only:

- ADE ownership of provenance for canonical ADE decisions;
- attributable lineage from authorized evidence to a canonical ADE result;
- preservation of the authorized upstream artifact and provenance context
  actually used;
- attribution of the governing semantic context;
- attribution of the explicit governed UTC `as_of` context;
- semantic completeness sufficient for independent audit;
- provenance immutability after canonical establishment;
- provenance continuity across representations and references;
- deterministic and replay-compatible provenance meaning;
- preservation of upstream provenance ownership;
- separation of provenance from identity, canonical authority, approval, and
  execution;
- fail-closed treatment when valid provenance cannot be established.

This Decision does not freeze:

- a provenance field list;
- a provenance tuple;
- a provenance identifier or primary key;
- a lineage graph;
- an event model;
- a storage or persistence model;
- a serialization format;
- canonical bytes;
- a hash or digest;
- a cryptographic proof;
- a Policy Version;
- an acceptance algorithm;
- provenance treatment for non-canonical outputs.

---

## Repository Constraints

AI Decision Engine is a distinct, deterministic, auditable,
point-in-time-bound, non-executing bounded context downstream of Human Review.

Decision #1 remains the authority for the AI Decision Engine semantic boundary.
Decision #2 remains the authority for authorized-input admission and imported
authority limits. Decision #3 remains the authority for the semantic authority
class of a canonical ADE decision. Decision #4 remains the authority for ADE
decision identity.

The sole authorized upstream input remains Human Review public outputs through
approved Human Review public contracts, consumed as recorded human-attestation
context only.

Provenance preservation, reference, recording, audit, or lineage shall not:

- transfer semantic ownership;
- expand authorized inputs;
- establish canonical ADE authority;
- create or replace ADE identity;
- redefine Human Review semantics;
- reopen Architecture-deferred boundaries;
- create downstream consumption authority;
- create financial or execution authority.

This Decision shall not redesign or redefine Human Review, Dashboard, Morning
Briefing, Premarket Scoring, Strategy Engine, Risk, Portfolio, OMS, Broker
abstraction, or Broker Execution.

---

## Governance Definitions

### ADE Provenance

Repository-governed semantic lineage belonging to a canonical ADE decision,
describing the authorized evidence, governed context, and derivation history
that contributed to that decision.

This definition does not establish a concrete representation.

### Upstream Provenance

Provenance owned by an originating bounded context and made available to ADE
only through an authorized Human Review public contract.

### Provenance Ownership

The limited ownership of ADE provenance for canonical ADE decisions only,
without acquisition of ownership of upstream artifacts, upstream provenance,
or another bounded context's lifecycle.

### Provenance Attribution

The Governance property that provenance can be associated with the correct ADE
decision and can identify the authorized evidence and governed context that
contributed to its meaning.

### Authorized Lineage

The governed relationship between a canonical ADE decision and the authorized
Human Review public artifact, evidence, and context actually consumed for that
decision.

### Governing Context

The semantic Governance and, when separately authorized, Policy context under
which the ADE decision was evaluated and accepted.

This definition does not establish a Policy identifier, version, field, or
representation.

### Provenance Continuity

The requirement that provenance retain the same semantic attribution when the
canonical ADE decision is persisted, retrieved, presented, referenced,
audited, or later replayed.

### Provenance Completeness

The Governance property that provenance is sufficient to establish authorized
lineage, governing context, temporal context, and the relationship to the
correct ADE identity without fabricated or substituted history.

These definitions are Governance concepts only. They do not define schemas,
fields, algorithms, storage, APIs, serialization, event sourcing, or runtime
validation.

---

## Decision

### Provenance Authority

This Governance Decision is the sole Governance authority for the semantic
provenance boundary of a canonical ADE decision.

Neither Policy, implementation, downstream bounded contexts, documentation, nor
operational procedures may redefine the provenance requirements frozen here.

ADE owns provenance for canonical ADE decisions only. Upstream provenance remains
owned by its originating bounded context.

Provenance authority governs lineage, attribution, traceability, stability,
continuity, and preservation obligations. It does not grant identity authority,
canonical-authority authority, schema authority, storage authority, approval
authority, or execution authority.

### Provenance Semantics

Provenance for a canonical ADE decision shall be:

- attributable to the correct ADE decision;
- derived only from authorized evidence and governed context;
- sufficient to establish the lineage actually used;
- linked to the applicable upstream Human Review public artifact;
- compatible with ADE identity without becoming ADE identity;
- compatible with deterministic governed acceptance without performing it;
- compatible with the explicit governed UTC `as_of` context;
- semantically immutable after canonical establishment;
- continuous across authorized representations and references;
- independently auditable;
- compatible with future replay and PIT semantics.

Provenance shall never fabricate, infer, synthesize, substitute, omit, or
silently reinterpret lineage.

### Ownership Preservation

Consumption, preservation, recording, reference, display, audit, lineage, or
downstream propagation never transfers semantic ownership.

ADE provenance shall not appropriate:

- Human Review provenance ownership;
- Dashboard provenance ownership;
- Morning Briefing provenance ownership;
- Premarket Scoring provenance ownership;
- Strategy provenance ownership;
- Risk authority;
- Portfolio authority;
- OMS lifecycle authority;
- Broker, execution, or fill provenance ownership.

Referencing upstream provenance gives ADE reference authority only. It does not
give ADE authority to mutate, reconstruct, replace, or govern the upstream
artifact.

---

## Human Review Provenance Firewall

Human Review public outputs through approved Human Review public contracts remain
the sole authorized upstream input surface under Decision #2.

ADE provenance may semantically preserve or reference, as applicable:

- the consumed Human Review public artifact;
- the Human Review identity reference;
- the Human Review provenance reference;
- the recorded Human Review attestation meaning;
- the explicit UTC `as_of` context;
- applicable frozen Human Review Governance and Policy meaning.

These are semantic provenance concepts. They are not an exact provenance tuple,
field list, schema, or representation.

Human Review provenance remains Human Review-owned. ADE shall not:

- overwrite Human Review provenance;
- reinterpret Human Review provenance;
- fabricate Human Review provenance;
- infer missing Human Review provenance;
- synthesize Human Review lineage;
- substitute ADE-generated lineage for Human Review provenance;
- mutate Human Review provenance;
- claim ownership of Human Review provenance.

ADE shall preserve the meaning of upstream provenance as received through the
authorized Human Review public contract. If the upstream reference is missing,
broken, conflicting, stale, incompatible, or semantically unavailable, ADE
shall not silently repair or replace it.

Preserving or referencing Human Review provenance does not transfer Human Review
semantic ownership, provenance ownership, or authority to ADE.

---

## Identity / Provenance Separation

The following distinction is binding:

```text
ADE decision identity
  ≠ ADE decision provenance
```

Identity answers:

> Which ADE decision is this?

Provenance answers:

> What authorized evidence and governed context produced or supported this
> decision?

Provenance shall:

- remain associated with the correct ADE identity;
- preserve ADE identity by reference;
- never create ADE identity;
- never replace ADE identity;
- never mutate ADE identity;
- never use provenance similarity to establish identity;
- never cause provenance to determine identity composition.

Decision #4 remains the sole Governance authority for ADE identity.

---

## Provenance / Authority Separation

The following distinction is binding:

```text
valid provenance
  ≠ canonical ADE authority
```

Valid provenance may demonstrate that authorized evidence and governed context
are attributable. It does not independently establish that a result is a
canonical ADE decision.

Provenance shall not independently confer:

- ADE canonical authority;
- Human Review approval;
- human approval;
- trade approval;
- Strategy Engine authority;
- Risk authority;
- Portfolio authority;
- OMS authority;
- Order Intent;
- executable instruction;
- Broker Execution authorization.

Canonical ADE authority remains subject to the deterministic, governed
acceptance requirement frozen by Decision #3. Provenance supports audit of that
boundary but does not perform or replace acceptance.

---

## ADE-Owned Provenance Boundary

ADE may semantically own provenance describing the governed derivation of a
canonical ADE decision.

At Governance level, ADE provenance may establish:

- attributable lineage from authorized evidence to the canonical ADE result;
- which authorized upstream artifact supplied the evidence;
- the governing semantic context that applied;
- the explicit governed UTC `as_of` context;
- the future governing Policy semantic context when separately authorized;
- the relationship to deterministic governed acceptance under Decision #3;
- continuity of lineage across representations;
- immutable provenance meaning after canonical establishment.

ADE-owned provenance shall describe the ADE derivation context only. It shall
not become ownership of the upstream evidence, Human Review artifact, or
another bounded context's provenance.

This section does not select exact fields, graph structure, event model,
identifier, serialization, storage, or validation mechanism.

---

## Authorized Input Firewall

Decision #5 creates no new input authorization.

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
- implementation-private upstream representations;
- OMS;
- Broker abstraction;
- live execution state.

Provenance may describe only evidence and context already authorized for ADE
consumption. A source does not become authorized because it would improve
provenance, lineage, auditability, reconstruction, validation, or explanation.

Nested lineage visible through an authorized Human Review public contract does
not authorize direct ADE access to the underlying systems.

No fallback source, hidden authority path, convenience read, or model-context
workaround is created by this Decision.

---

## Provenance Completeness

Provenance for a canonical ADE decision shall be semantically sufficient to
establish:

- the authorized evidence actually used;
- the authorized upstream artifact supplying that evidence;
- the applicable governing semantic context;
- the explicit governed UTC `as_of` context;
- the absence of silent unauthorized contribution;
- attributable lineage for audit and future replay;
- association with the correct ADE identity;
- the absence of fabricated, inferred, substituted, omitted, or silently
  repaired lineage.

Completeness does not require every repository artifact to participate. It
requires that every provenance claim made for the canonical ADE decision be
supported by authorized evidence actually used.

Completeness does not confer reconstruction authority over upstream bounded
contexts and does not define a required field list.

---

## Provenance Immutability

Once a canonical ADE decision is established, the semantic meaning of its
provenance is immutable.

The following are prohibited:

- silent history rewriting;
- evidence substitution;
- source reassignment;
- governing-context replacement;
- provenance mutation;
- lineage replacement;
- semantic drift under unchanged provenance meaning;
- repair after canonical establishment;
- deletion that destroys auditability;
- silent change to the meaning of a referenced artifact.

If an upstream reference later becomes broken or semantically different, the
historical provenance shall not be silently rewritten to accommodate that
change.

This Decision does not select an append-only database, WORM storage, event
sourcing, cryptographic signature, hash, digest, or retention mechanism.

---

## Provenance Continuity

The same semantic provenance meaning shall remain attributable across:

- persistence;
- retrieval;
- presentation;
- downstream reference;
- audit;
- future replay.

Representation changes shall not change:

- the ADE decision to which provenance belongs;
- the authorized evidence lineage;
- the upstream ownership boundary;
- the governing semantic context;
- the explicit UTC `as_of` meaning;
- the distinction between provenance and authority.

Presentation, transport, and downstream reference are not sources of truth and
do not acquire provenance ownership.

This section does not define storage, DTOs, transport, APIs, database joins,
lineage graphs, or event envelopes.

---

## PIT / `as_of` Boundary

Decision #6 owns Replay / PIT semantics and mechanics.

Decision #5 freezes only the temporal provenance requirements necessary for
auditability:

- the explicit governed UTC `as_of` context must remain attributable;
- relevant authorized upstream evidence must be attributable to that context;
- future knowledge must not silently enter lineage;
- temporal mismatch must not be silently reconciled;
- provenance must remain compatible with future replay;
- provenance must not repair a PIT violation.

This Decision does not define:

- replay algorithms;
- PIT reconstruction;
- temporal lookup;
- snapshot selection;
- timestamp comparison mechanics;
- clock sources;
- event sourcing;
- temporal databases;
- replay storage.

Decision #6 remains NOT STARTED.

---

## Governing Policy Context

A canonical ADE decision must be attributable to the governing semantic Policy
context under which it was accepted, once such Policy is separately
authorized.

This is a semantic attribution requirement only. It does not freeze:

- Policy ID;
- Policy Version format;
- a Policy field;
- a Policy hash;
- Policy serialization;
- a Policy equivalence algorithm;
- concrete Policy rules.

Policy Freeze remains DENIED. This Decision does not create, authorize, or
assume an ADE Policy Version.

---

## Determinism / Canonical Authority Relationship

Provenance must support auditability of deterministic governed acceptance under
Decision #3.

Under equivalent authorized evidence and governed context, provenance meaning
must be stable and repeatable. Provenance must not depend on:

- wall-clock generation;
- unseeded randomness;
- mutable runtime state;
- presentation;
- transport;
- downstream consumers;
- operational-environment discovery.

Provenance itself does not perform acceptance and does not establish canonical
authority.

This Decision does not define acceptance algorithms, canonicalization, scoring,
thresholds, confidence, rankings, formulas, or model behavior.

---

## Model / Provider Firewall

No model participation is authorized by this Decision.

Decision #5 does not authorize:

- an LLM;
- a model;
- a provider;
- a prompt;
- training;
- fine-tuning;
- inference;
- hosting;
- model integration;
- collection or storage of model metadata.

If model participation is separately authorized in the future, relevant
operational or model metadata may contribute to provenance only under
separately approved Governance and Policy boundaries.

Such metadata cannot independently establish:

- ADE identity;
- ADE canonical authority;
- Human Review approval;
- human approval;
- Order Intent;
- execution authorization.

This Decision does not assume that model or provider metadata exists.

---

## Output / Abstention Firewall

Decision #7 owns Output / Abstention.

Decision #5 governs provenance semantics of canonical ADE decisions only. It
does not define provenance treatment for:

- abstention;
- rejection;
- error;
- failure;
- evaluation attempt;
- `DecisionProposal`;
- recommendation;
- action;
- other non-authoritative material.

Whether non-canonical or non-authoritative outcomes receive provenance, and how
they are represented, remains reserved for Decision #7 and later authorized
Policy.

Decision #7 remains NOT STARTED.

---

## Human Authority Firewall

Decision #8 owns Human Authority over ADE Outputs.

Human Review attestation remains upstream context only. Provenance shall not
transform it into:

- ADE-output approval;
- human approval;
- sign-off;
- trade approval;
- reviewer authority;
- override;
- approval workflow state;
- human acceptance lifecycle.

This Decision does not define reviewer provenance schema, reviewer identity,
approval events, rejection events, or human authority workflow.

Decision #8 remains NOT STARTED.

---

## Sprint 4 Ownership Firewall

The following distinctions are binding:

```text
ADE provenance
  ≠ Strategy provenance ownership
  ≠ Risk authority
  ≠ Portfolio authority
  ≠ OMS lifecycle authority
```

The following are also distinct:

```text
ADE provenance
  ≠ Order Intent provenance
  ≠ broker order provenance
  ≠ execution provenance
  ≠ fill provenance
```

ADE provenance shall not depend on Strategy Engine internals, Risk internals,
Portfolio internals, OMS lifecycle, broker lifecycle, fills, or execution
state.

Any future reference to those contexts requires prior applicable Architecture
and Governance authorization. This Decision does not reopen or redesign Sprint
4.

---

## Fail-Closed Provenance

If sufficient, valid, attributable, non-conflicting provenance cannot be
established for a purported canonical ADE decision, that result must not be
treated as a canonical authoritative ADE decision.

This rule applies to:

- missing provenance;
- ambiguous provenance;
- conflicting provenance;
- unauthorized provenance source;
- stale or incompatible provenance;
- broken upstream reference;
- fabricated lineage;
- substituted lineage;
- provenance whose semantic meaning cannot be established;
- provenance not attributable to the correct ADE decision;
- provenance that would require reinterpretation to become valid.

Provenance shall not be established through:

- silent repair;
- inference;
- fabrication;
- substitution;
- fallback authority;
- lineage synthesis;
- provenance promotion;
- silent omission.

This Decision does not classify the resulting condition as abstention,
rejection, error, failure, or no-decision. Decision #7 and later authorized
Policy own that representation.

---

## Provenance Conflict Rule

Unreconciled provenance conflict is a fail-closed condition.

This includes, conceptually:

- conflicting upstream artifact references;
- Human Review identity and provenance mismatch;
- mismatched PIT or `as_of` context;
- incompatible governing context;
- lineage that cannot be reconciled without reinterpretation;
- contradictory claims about the evidence actually used.

This Decision does not define:

- precedence rules;
- conflict-resolution algorithms;
- merge algorithms;
- repair algorithms;
- database reconciliation;
- exception classes.

No conflict may be silently converted into valid provenance or canonical
authority.

---

## Provenance Loss / Drift

The following are prohibited:

- silent provenance loss;
- source reassignment;
- replacement of broken lineage with inferred lineage;
- upstream-reference semantic drift;
- history rewriting;
- replacement of original lineage;
- mutable-reference drift without attributable governance;
- silent deletion that destroys auditability.

Loss or drift does not authorize fallback lineage, synthesized history, source
substitution, or restoration of canonical authority by inference.

This Decision does not select retention periods, archival systems, signatures,
hashes, WORM storage, immutable databases, or event sourcing.

---

## Auditability

A canonical ADE decision must be independently auditable as to:

- its ADE identity;
- its authorized upstream lineage;
- the upstream Human Review provenance meaning preserved;
- its governing semantic context;
- its explicit UTC `as_of` context;
- the canonical-authority establishment boundary;
- the absence of silent unauthorized contribution;
- the absence of fabricated, inferred, substituted, or silently repaired
  lineage.

This is a semantic auditability invariant. It does not define audit tables,
audit events, logs, tracing, correlation IDs, telemetry, or evidence-bundle
schemas.

---

## Downstream Reference Firewall

A downstream reference to ADE provenance identifies lineage associated with an
ADE decision only.

It does not confer:

- provenance ownership;
- semantic ownership;
- approval;
- canonical authority;
- Order Intent;
- execution authority;
- lifecycle authority.

Decision #5 creates no downstream consumer and no downstream port.

---

## Broker Execution Firewall

The following distinction is binding:

```text
ADE provenance
  ≠ execution authorization
```

Decision #5 authorizes none of the following:

- OMS;
- broker APIs or SDKs;
- order submission;
- cancellation;
- replacement;
- fills;
- execution lifecycle;
- live trading;
- capital deployment;
- Order Intent creation;
- execution authorization.

Broker Execution remains DENIED / DEFERRED and requires a future independent
Planning Gate. Repository sequencing is not authorization.

---

## Reserved Later Governance Decisions

The following remain NOT STARTED and are not resolved by this Decision:

| # | Planned Decision | Status |
| --- | --- | --- |
| 6 | Replay / PIT | NOT STARTED |
| 7 | Output / Abstention | NOT STARTED |
| 8 | Human Authority over AI Decision Engine Outputs | NOT STARTED |

Decision #5 does not pre-resolve these Decisions.

Decision #6 retains replay behavior, PIT reconstruction, temporal mechanics,
and replay comparison mechanisms.

Decision #7 retains abstention, rejection, error, failure, non-canonical
output provenance, and result representation.

Decision #8 retains reviewer identity, approval, rejection, sign-off, override,
and human-authority lifecycle.

---

## Policy Boundary

Policy Freeze remains DENIED.

After separate Policy authorization, Policy may define concrete behavior within
this frozen semantic boundary, including:

- concrete provenance completeness requirements;
- exact required provenance semantics;
- concrete validation obligations;
- concrete failure categories;
- concrete governing-policy association requirements.

This Decision does not authorize Policy to define a schema, field list,
identifier, serialization, storage representation, or technical mechanism.
Those details are not authorized by this Decision and remain reserved for later
approved stages.

Policy shall not:

- redefine provenance ownership;
- expand authorized inputs;
- transfer upstream ownership;
- establish canonical authority through provenance alone;
- supersede this Decision;
- authorize implementation or Broker Execution.

This Decision does not create or authorize a Policy Version.

---

## Implementation Boundary

Implementation Authorization remains DENIED.

The following technical mechanisms remain reserved for later authorized
Implementation:

- exact provenance fields;
- provenance schema;
- provenance ID;
- graph or data structure;
- canonical bytes;
- serialization;
- hashes or digests;
- storage;
- database tables;
- indexes;
- event model;
- APIs;
- retention mechanisms;
- cryptographic mechanisms;
- validators;
- error mapping;
- packages, modules, or services.

Implementation must remain subordinate to the approved Planning Gate,
Architecture, and Governance Decisions. Implementation shall not reinterpret,
expand, or silently repair this provenance boundary.

This Decision does not authorize implementation.

---

## Explicit Non-Authorizations

Decision #5 does not authorize:

- Decision #6, #7, or #8;
- Policy Freeze;
- Implementation Authorization;
- ADE implementation;
- model or provider integration;
- collection or storage of model metadata;
- any new input source;
- direct Dashboard, Morning Briefing, or Premarket Scoring consumption;
- Risk, Portfolio, or Strategy Engine consumption;
- OMS or broker access;
- downstream consumers or ports;
- human approval workflow;
- Order Intent creation;
- order submission, cancellation, or replacement;
- fill processing;
- live trading;
- capital deployment;
- execution authorization.

---

## Resolution

**Status:** RESOLVED

**Governance effect:** The semantic provenance boundary for a canonical ADE
decision is frozen as ADE-owned provenance describing attributable lineage from
authorized evidence through the governed derivation context to the correct ADE
decision. Provenance must preserve upstream Human Review provenance meaning,
remain distinct from identity and canonical authority, remain attributable to
the governed UTC `as_of` context, remain semantically immutable and continuous,
and support independent audit without transferring semantic ownership or
authority.

Insufficient, invalid, conflicting, unauthorized, stale, broken, fabricated,
substituted, or semantically unresolvable provenance cannot support treatment
as a canonical authoritative ADE decision. No output or abstention taxonomy is
defined by this rule.

Concrete provenance representation remains reserved for later authorized Policy
and Implementation. Decisions #6–#8 remain NOT STARTED. Policy Freeze,
Implementation Authorization, Implementation, and Broker Execution remain
DENIED / DEFERRED.

Governance remains IN PROGRESS — documentation-only. Decisions #1–#5 are
RESOLVED. Decisions #6–#8 remain NOT STARTED. Governance is not COMPLETE.
