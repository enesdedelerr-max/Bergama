# AI Decision Engine Governance Decision #6 — Replay / PIT

**Decision ID:** `ai-decision-engine.governance.06-replay-pit`
**Title:** Decision #6 — Replay / PIT
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
- AI Decision Engine Governance Decision #5 — Provenance
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
Replay / Point-in-Time boundary of a canonical AI Decision Engine decision.

It does not define Architecture, Policy Freeze, implementation, replay
algorithms, reconstruction algorithms, snapshot-selection algorithms,
timestamp-comparison algorithms, temporal lookup algorithms, clock sources,
timestamp serialization, storage mechanisms, event sourcing, temporal
databases, schemas, APIs, identity mechanisms, provenance mechanisms, Policy
ID/version/hash/digest/schema, exact governing-context composition, output
taxonomy, abstention taxonomy, human-authority workflows, model participation,
or Broker Execution.

---

## Purpose

Freeze the semantic Replay / Point-in-Time requirements that make an
authoritative canonical ADE decision reconstructable, examinable, and
replayable against the same governed point-in-time context without future
knowledge, mutable-current-state leakage, silent evidence substitution, or
authority drift.

This Decision answers:

> What must remain semantically true so that an authoritative canonical ADE
> decision can later be reconstructed, examined, or replayed against the same
> governed point-in-time context without future knowledge,
> mutable-current-state leakage, silent evidence substitution, or authority
> drift?

Replay explains historical reproducibility of canonical ADE semantic meaning.
Replay does not answer which ADE decision is being identified, whether that
result possesses canonical ADE authority, or what output class is emitted when
replay cannot be established.

This Decision defines Replay / PIT semantics only.

---

## Immutable Concern

This Decision freezes only:

- historical-replay meaning for canonical ADE decisions;
- binding of historical canonical ADE evaluation and replay to one explicit
  governed UTC `as_of` context;
- prohibition of future knowledge in historical replay;
- restriction of historical replay to Decision #2-authorized recorded
  evidence;
- preservation of Human Review recorded public-artifact and attestation
  meaning under the governed PIT context;
- separation of historical replay from new-decision creation;
- replay compatibility with Decision #4 identity without redefining identity;
- consumption of Decision #5 provenance guarantees without redefining
  provenance;
- inspection or verification of historical Decision #3 authority conditions
  without creating authority;
- attribution of original governing semantic context without freezing exact
  Policy/config/code composition;
- deterministic semantic reproducibility under identical governed conditions;
- read-only / non-mutating replay;
- semantic replay equivalence without an equivalence algorithm;
- fail-closed treatment when historical replay/PIT guarantees cannot be
  established;
- semantic auditability of historical replay conditions.

This Decision does not freeze:

- a replay algorithm;
- a reconstruction algorithm;
- a snapshot-selection algorithm;
- a timestamp-comparison algorithm;
- a temporal lookup algorithm;
- a clock source;
- timestamp serialization;
- a storage or persistence model;
- event sourcing;
- a temporal database;
- a schema or API;
- an identity mechanism;
- a provenance mechanism;
- a Policy ID, version, hash, digest, or schema;
- exact governing-context composition;
- an output or abstention taxonomy;
- a human-approval workflow;
- model or provider participation;
- Broker Execution.

---

## Repository Constraints

AI Decision Engine is a distinct, deterministic, auditable,
point-in-time-bound, non-executing bounded context downstream of Human Review.

Decision #1 remains the authority for the AI Decision Engine semantic boundary.
Decision #2 remains the authority for authorized-input admission and imported
authority limits. Decision #3 remains the authority for the semantic authority
class of a canonical ADE decision. Decision #4 remains the authority for ADE
decision identity. Decision #5 remains the authority for ADE decision
provenance.

The sole authorized upstream input remains Human Review public outputs through
approved Human Review public contracts, consumed as recorded human-attestation
context only.

Historical replay, reconstruction, examination, or PIT evaluation shall not:

- transfer semantic ownership;
- expand authorized inputs;
- establish canonical ADE authority;
- redefine ADE identity;
- redefine ADE provenance;
- redefine Human Review replay;
- create Order Intent;
- create financial or execution authority.

This Decision shall not redesign or redefine Human Review, Dashboard, Morning
Briefing, Premarket Scoring, Strategy Engine, Risk, Portfolio, OMS, Broker
abstraction, or Broker Execution.

---

## Governance Definitions

### Historical Replay

The reproduction, reconstruction, or verification of the original canonical
ADE semantic meaning under the applicable original governed semantic context
and governed UTC `as_of`.

### Point-in-Time (PIT) Context

The explicit governed UTC `as_of` context that anchors historical ADE
evaluation and historical replay and excludes future knowledge.

### Future Knowledge

Evidence, state, governing meaning, or authority unavailable or not
attributable to the governed PIT context of the historical canonical ADE
decision.

### Historical Replay Equivalence

Preservation of the same canonical ADE semantic meaning under identical
governed semantic conditions, without requiring byte-identical representation
or an equivalence algorithm.

### Replay Inability

The condition in which historical replay/PIT guarantees cannot be established
and successful historical replay of the canonical ADE decision therefore
cannot be claimed.

These definitions are Governance concepts only. They do not define schemas,
fields, algorithms, storage, APIs, serialization, event sourcing, or runtime
mechanisms.

---

## Decision

### Replay / PIT Ownership

ADE owns the Governance semantics of historical replay and PIT binding for
canonical ADE decisions.

ADE does not acquire:

- Human Review replay ownership;
- Human Review semantic ownership;
- Dashboard, Morning Briefing, or Premarket Scoring ownership;
- Strategy, Risk, Portfolio, or OMS ownership;
- Policy Freeze authority;
- Implementation Authorization;
- Broker Execution authority.

### Historical Replay Boundary

Historical replay means reproduction, reconstruction, or verification of the
ORIGINAL canonical ADE semantic meaning under the applicable original governed
semantic context.

```text
historical replay
  ≠ creation of a new ADE decision
  ≠ re-evaluation under changed evidence
  ≠ re-evaluation under later governing Policy context
  ≠ recomputation from mutable current state
  ≠ calling a model/provider again
  ≠ creation of new authority
```

Re-evaluation under changed evidence or changed governing context is not
historical replay of the original canonical ADE decision.

This Decision does not define what output such re-evaluation produces.

### Single Governed PIT

Each historical canonical ADE evaluation and historical replay is bound to one
explicit governed UTC `as_of` context.

The governed `as_of`:

- anchors the historical semantic context;
- excludes future knowledge;
- cannot be silently replaced by wall-clock or current time;
- cannot be silently reconciled with a materially different temporal context.

This Decision does not freeze:

- a timestamp field schema;
- timestamp serialization;
- a clock source;
- a temporal database;
- a snapshot-selection algorithm;
- a lookup algorithm;
- a timestamp-comparison algorithm.

### Future-Knowledge Firewall

Evidence unavailable or not attributable to the governed PIT context must not
silently enter historical replay.

Historical replay shall not silently use:

- evidence created after the governed PIT context;
- mutable current-state substitutes;
- later Human Review mutations as replacement historical authority;
- later Policy state to redefine original meaning;
- later model or provider state;
- unauthorized historical data;
- future knowledge.

No temporal query mechanism is authorized by this Decision.

### Authorized Evidence Firewall

Decision #2 remains authoritative for inputs.

Historical replay may rely only on historically attributable, authorized
recorded evidence permitted by Decision #2.

The sole authorized upstream remains Human Review public outputs through
approved Human Review public contracts, as recorded human-attestation context.

Decision #6 creates no new input authorization.

Replay does not create a new authorization path. Caches, snapshots, logs,
archives, event streams, derived artifacts, or historical databases do not
become authorized merely because they are historical.

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

Nested historical lineage visible through an authorized Human Review public
contract does not authorize direct ADE access to underlying systems.

### Human Review PIT Firewall

Historical replay shall preserve, as applicable:

- the original authorized Human Review public artifact or context;
- the recorded Human Review attestation meaning;
- the Human Review identity reference;
- the Human Review provenance reference;
- the applicable governed UTC `as_of`;
- the applicable frozen Human Review Governance and Policy meaning.

Human Review owns Human Review semantics and Human Review replay. ADE shall
not:

- redefine Human Review replay;
- query mutable current Human Review state as replacement historical
  authority;
- fabricate historical attestation;
- reinterpret historical attestation;
- mutate Human Review history;
- infer approval;
- appropriate Human Review ownership.

### Replay / Identity Separation

Decision #4 remains the sole Governance authority for ADE identity.

```text
historical replay
  ≠ ADE decision identity composition
```

Replay compatibility requirements:

- replay does not silently create a different identity for the same
  historical canonical ADE decision;
- materially distinct PIT or governing semantic contexts must not silently
  alias;
- replay or reference does not define identity composition.

This Decision does not define:

- an identity tuple;
- a UUID;
- a hash or digest;
- a namespace;
- canonical bytes;
- serialization.

### Replay / Provenance Separation

Decision #5 remains the sole Governance authority for provenance.

```text
historical replay semantics
  ≠ provenance semantics
```

Decision #6 consumes the guarantees of attributable authorized evidence,
provenance meaning, governing-context attribution, and UTC `as_of`
attribution. It does not redefine provenance ownership.

Replay may require sufficient attributable provenance to establish historical
context. This Decision does not define:

- an evidence-bundle schema;
- a provenance graph;
- an event log;
- a lineage database;
- a retention mechanism;
- provenance serialization.

### Replay / Authority Separation

Decision #3 remains the sole Governance authority for canonical ADE authority.

```text
successful historical replay
  ≠ creation of canonical ADE authority
```

Replay may inspect, reconstruct, or verify historical authority conditions.

Replay shall not:

- create canonical authority;
- promote non-authoritative material;
- upgrade advisory or model material;
- inherit Human Review approval;
- create human or trade approval;
- create Strategy authority;
- create Risk authority;
- create Portfolio authority;
- create OMS authority;
- create Order Intent;
- create execution authority.

### Governing Semantic Context

A historical canonical ADE decision must remain attributable to the original
governing semantic context under which its authority was established.

Historical replay under that original context must remain distinguishable from
hypothetical re-evaluation under a later governing context.

Policy Freeze remains DENIED. This Decision does not freeze or imply an exact
replay tuple containing:

- a Policy Version;
- a config version;
- a code version;
- a Policy ID;
- a Policy hash or digest;
- a Policy field;
- a configuration field;
- a code identifier.

Exact composition of governing context remains reserved for later separately
authorized Policy and Implementation. This Decision does not select a Policy
versioning mechanism and does not create or assume an ADE Policy Version.

### Deterministic Semantic Reproducibility

Identical authorized recorded evidence, identical governed semantic context,
and identical governed PIT conditions must preserve the same canonical ADE
semantic meaning.

Historical replay must not depend on:

- mutable wall-clock or current state;
- runtime randomness;
- unauthorized mutable external authority.

This is a semantic invariant only. This Decision does not define:

- a canonicalization algorithm;
- a deterministic seed;
- a random-seed policy;
- a comparison formula;
- a tolerance;
- a threshold;
- a scoring rule;
- an exact replay tuple.

### Model / Provider Firewall

No model or provider participation is authorized by this Decision.

Calling a model or provider again must not be defined as historical replay of
canonical ADE state.

Decision #6 does not authorize or select:

- an LLM;
- a model;
- a provider;
- a prompt;
- inference;
- model replay;
- provider replay;
- training;
- fine-tuning;
- hosting;
- model-metadata storage;
- model versioning;
- a deterministic seed;
- model-output canonicalization.

Any future model participation, if separately authorized, remains subordinate
to these Replay / PIT invariants and cannot redefine historical replay as a
fresh model call.

### Read-Only / Non-Mutating Replay

Historical replay is semantically read-only and non-mutating.

Historical replay shall not mutate:

- a canonical ADE decision;
- ADE identity;
- ADE provenance;
- a Human Review artifact or history;
- upstream semantic state;
- Strategy Engine;
- Risk;
- Portfolio;
- OMS;
- Order Intent;
- Broker state.

Replay does not rewrite history.

### Replay Equivalence

Historical replay under identical governed semantic conditions must preserve
the same canonical ADE semantic meaning.

Relevant semantic conditions may include, without defining an exact tuple:

- same historical decision association;
- same authorized evidence meaning;
- same governing semantic context;
- same governed UTC `as_of`;
- same attributable provenance meaning.

This Decision does not require:

- byte-identical representation;
- raw model-output equality;
- exact serialization equality.

This Decision does not define an equivalence algorithm or tuple.

### Fail-Closed Boundary

If historical replay/PIT guarantees cannot be established, the system must not
treat the attempt as a successful historical replay of the canonical ADE
decision and must not invent canonical authority.

This rule applies to:

- required historical evidence unavailable;
- provenance insufficient;
- PIT ambiguous;
- temporal conflict;
- governing semantic context unknown;
- future-knowledge contamination;
- mutable-current-state substitution;
- unauthorized evidence;
- identity association that cannot be established.

No silent:

- repair;
- inference;
- fabrication;
- substitution;
- reconciliation;
- fallback authority;
- promotion.

This Decision does not classify the resulting condition as abstention,
rejection, error, failure, no-decision, recommendation, or any other output
class. Decision #7 and later authorized Policy own that representation.

### Temporal Conflicts

Unresolved temporal conflict prevents successful historical replay.

This includes, conceptually:

- mismatched `as_of`;
- conflicting PIT context;
- evidence unavailable at the original PIT;
- later evidence correction substituted into the original context;
- later governing-context changes;
- mutable upstream history.

No precedence, merge, repair, or reconciliation algorithm is authorized.

### Auditability

Historical replay must be independently auditable as to:

- which canonical ADE decision is being replayed;
- which authorized historical evidence governed it;
- which governing semantic context applied;
- which governed UTC `as_of` applied;
- the absence of future knowledge;
- the absence of unauthorized substitution;
- whether original canonical semantic meaning was preserved.

This is a semantic auditability invariant. It does not define audit tables,
audit events, logs, tracing, correlation IDs, evidence bundles, or telemetry.

### Sprint 4 Ownership Firewall

The following distinctions are binding:

```text
ADE replay
  ≠ Strategy Engine replay ownership
  ≠ Risk replay ownership
  ≠ Portfolio replay ownership
  ≠ OMS replay ownership
```

Historical references do not create authorization. ADE replay shall not depend
on Strategy Engine internals, Risk internals, Portfolio internals, OMS
lifecycle, broker lifecycle, fills, or execution state as ADE replay inputs.

This Decision does not reopen or redesign Sprint 4.

### Broker Execution Firewall

```text
ADE historical replay
  ≠ execution authorization
```

Execution or fill history is not an authorized ADE replay input under Decision
#2.

Decision #6 authorizes none of the following:

- Broker APIs;
- Broker SDKs;
- broker replay;
- order submission;
- cancellation;
- replacement;
- fill processing;
- live trading;
- capital deployment;
- Order Intent creation;
- execution authorization.

Broker Execution remains DENIED / DEFERRED and requires a future independent
Planning Gate. Repository sequencing is not authorization.

### Storage / Technical Mechanism Firewall

This Decision does not select:

- event sourcing;
- snapshotting;
- temporal tables;
- WORM storage;
- append-only storage;
- audit-log design;
- a provenance graph;
- a replay cache;
- checkpointing;
- a historical database;
- a storage engine;
- a retention mechanism.

Governance freezes semantic requirements only. Technical mechanisms remain
reserved for separately authorized Implementation.

---

## Output / Abstention Firewall

Decision #7 owns Output / Abstention.

Decision #7 remains NOT STARTED.

Decision #6 does not define:

- a replay-result taxonomy;
- a divergence taxonomy;
- an abstention taxonomy;
- a rejection taxonomy;
- a failure taxonomy;
- an error taxonomy;
- reason codes;
- a recommendation or action taxonomy;
- confidence;
- thresholds;
- ranking;
- trade rules.

Fail-closed Replay / PIT semantics do not select an output class.

---

## Human Authority Firewall

Decision #8 owns Human Authority over ADE Outputs.

Decision #8 remains NOT STARTED.

Decision #6 does not define:

- replay approval;
- reviewer identity;
- sign-off;
- override;
- an approval or rejection workflow;
- reviewer provenance;
- escalation.

Historical Human Review attestation remains upstream context only.

---

## Reserved Later Governance Decisions

The following remain NOT STARTED and are not resolved by this Decision:

| # | Planned Decision | Status |
| --- | --- | --- |
| 7 | Output / Abstention | NOT STARTED |
| 8 | Human Authority over AI Decision Engine Outputs | NOT STARTED |

Decision #6 does not pre-resolve these Decisions.

Decision #7 retains output, abstention, rejection, error, failure,
divergence, and result-representation taxonomies.

Decision #8 retains reviewer identity, approval, rejection, sign-off, override,
and human-authority lifecycle.

---

## Policy Boundary

Policy Freeze remains DENIED.

After separate Policy authorization, Policy may define concrete behavior within
this frozen semantic boundary, including:

- concrete historical-replay completeness requirements;
- concrete PIT attribution obligations;
- concrete failure categories for replay inability;
- concrete governing-context association requirements once Policy exists.

This Decision does not authorize Policy to define a schema, field list,
identifier, serialization, storage representation, temporal algorithm, or
technical mechanism. Those details remain reserved for later approved stages.

Policy shall not:

- redefine Replay / PIT ownership;
- expand authorized inputs;
- redefine historical replay as new-decision creation;
- establish canonical authority through replay alone;
- supersede this Decision;
- authorize implementation or Broker Execution.

This Decision does not create or authorize a Policy Version.

---

## Implementation Boundary

Implementation Authorization remains DENIED.

The following technical mechanisms remain reserved for later authorized
Implementation:

- replay algorithms;
- reconstruction algorithms;
- snapshot-selection algorithms;
- timestamp-comparison algorithms;
- temporal lookup algorithms;
- clock sources;
- timestamp serialization;
- storage;
- event sourcing;
- temporal databases;
- schemas;
- APIs;
- validators;
- error mapping;
- packages, modules, or services.

Implementation must remain subordinate to the approved Planning Gate,
Architecture, and Governance Decisions. Implementation shall not reinterpret,
expand, or silently repair this Replay / PIT boundary.

This Decision does not authorize implementation.

---

## Explicit Non-Authorizations

Decision #6 does not authorize or freeze:

- Decision #7 or #8;
- Policy Freeze;
- Implementation Authorization;
- ADE implementation;
- a replay algorithm;
- a reconstruction algorithm;
- a snapshot-selection algorithm;
- a timestamp-comparison algorithm;
- a temporal lookup algorithm;
- a clock source;
- timestamp serialization;
- a storage mechanism;
- event sourcing;
- a temporal database;
- a schema or API;
- an identity mechanism;
- a provenance mechanism;
- a Policy ID, version, hash, digest, or schema;
- exact governing-context composition;
- model or provider integration;
- model replay;
- an output taxonomy;
- an abstention taxonomy;
- a human approval workflow;
- Order Intent creation;
- Broker Execution;
- order submission, cancellation, or replacement;
- fill processing;
- live trading;
- capital deployment;
- execution authorization.

---

## Resolution

**Status:** RESOLVED

**Governance effect:** The semantic Replay / Point-in-Time boundary for a
canonical ADE decision is frozen as historical reproduction,
reconstruction, or verification of the original canonical ADE semantic meaning
under one explicit governed UTC `as_of` and the original governing semantic
context, using only Decision #2-authorized historically attributable recorded
evidence, preserving Human Review recorded meaning without acquiring Human
Review ownership, remaining distinct from identity and canonical authority,
remaining read-only and non-mutating, remaining free of future knowledge and
mutable-current-state substitution, and supporting independent audit without
creating new authority.

Re-evaluation under changed evidence or later governing context is not
historical replay. Calling a model or provider again is not historical replay.
Unresolved temporal conflict, insufficient provenance, ambiguous PIT,
unavailable historical evidence, unauthorized evidence, future-knowledge
contamination, mutable-current-state substitution, or unestablished identity
association cannot support successful historical replay and cannot invent
canonical authority. No output or abstention taxonomy is defined by this rule.

Concrete replay mechanics, storage, schemas, Policy composition, and
implementation remain reserved for later authorized stages. Decisions #7–#8
remain NOT STARTED. Policy Freeze, Implementation Authorization,
Implementation, and Broker Execution remain DENIED / DEFERRED.

Governance remains IN PROGRESS — documentation-only. Decisions #1–#6 are
RESOLVED. Decisions #7–#8 remain NOT STARTED. Governance is not COMPLETE.
