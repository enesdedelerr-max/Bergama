# AI Decision Engine Governance Decision #3 — AI Decision Authority

**Decision ID:** `ai-decision-engine.governance.03-ai-decision-authority`  
**Title:** Decision #3 — AI Decision Authority  
**Status:** RESOLVED  
**Document class:** Governance Decision only  
**Bounded context:** AI Decision Engine

**Subordinate to:**

- Sprint 12 Planning Gate (`sprint-12.planning-gate`) — APPROVED
- AI Decision Engine Architecture v1 (`ai-decision-engine.architecture.v1`) — APPROVED
- AI Decision Engine Governance Decision #1 — Semantic Boundary
- AI Decision Engine Governance Decision #2 — Authorized Inputs
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
authority class of an AI Decision Engine canonical decision.

It does not define Architecture, Planning, Policy Version formulas, concrete
output taxonomy, abstention taxonomy, recommendation or action taxonomy,
reason codes, confidence semantics, thresholds, rankings, identity
composition, provenance composition, replay mechanics, PIT comparison
mechanics, schemas, APIs, storage, workflows, models, providers, prompts,
approval processes, or implementation.

---

## Purpose

Freeze the semantic authority that an AI Decision Engine canonical decision may
possess, where that authority applies, and what authority it must never possess.

This decision establishes that ADE canonical authority is internal semantic
authority within the AI Decision Engine bounded context. It does not grant
human, financial, operational, strategy, risk, portfolio, order, or execution
authority.

This Decision defines AI Decision authority only.

---

## Immutable Concern

This Decision freezes only:

- the semantic authority class of an ADE canonical decision;
- the limit of that authority to the AI Decision Engine bounded context;
- the requirement that canonical authority be deterministic and governed;
- the prohibition on raw, advisory, or nondeterministic material independently
  becoming canonical authority;
- the fail-closed authority rule when canonical authority cannot be established;
- the distinction between ADE canonical authority and Human Review, approval,
  Order Intent, and execution authority.

This Decision does not freeze concrete output names, result types, or schemas.

---

## Repository Constraints

AI Decision Engine is a distinct, deterministic, auditable, point-in-time-bound,
non-executing bounded context downstream of Human Review.

AI Decision Engine owns only AI Decision Engine semantic meaning. Consumption,
reference, preservation, display, presentation, recording, and lineage never
transfer semantic ownership between bounded contexts.

Decision #2 remains the sole authority for AI Decision Engine input admission and
imported-authority limits. The sole authorized upstream input remains Human
Review public outputs through approved Human Review public contracts, consumed
as recorded human-attestation context only.

This Decision shall not redesign or redefine:

- Human Review semantics;
- Dashboard semantics;
- Morning Briefing semantics;
- Premarket Scoring semantics;
- Sprint 4 Strategy Engine ownership;
- Risk ownership;
- Portfolio ownership;
- OMS ownership;
- Broker abstraction ownership;
- Broker Execution authority.

This Decision does not authorize direct Dashboard, Morning Briefing,
Premarket Scoring, Risk, Portfolio, or Strategy Engine consumption. Governance
alone cannot reopen an Architecture-deferred input boundary. Where required,
reopening requires an approved Architecture amendment followed by subsequent
approved Governance within Planning scope.

---

## Governance Definitions

### ADE Canonical Decision

An AI Decision Engine semantic result whose authority, if established under
later-authorized deterministic and governed acceptance, is limited to the AI
Decision Engine bounded context.

This definition does not establish a concrete artifact name, output type,
payload, schema, or acceptance mechanism.

### Canonical Authority

Repository-governed semantic authority belonging to an ADE canonical decision
within the AI Decision Engine bounded context only.

Canonical authority does not mean Human Review authority, approval authority,
trade authority, Order Intent authority, or execution authority.

### Governed Acceptance

The later-approved Governance and Policy requirements by which an ADE result
may be recognized as canonical authority.

This Decision requires deterministic, governed acceptance but does not define
its rules, algorithm, thresholds, formula, or implementation.

### Advisory Material

Raw, candidate, explanatory, confidence-bearing, or otherwise non-canonical
material that does not possess canonical ADE authority merely because it was
produced, referenced, preserved, or observed.

These definitions are Governance concepts only. They do not define output
taxonomy, abstention taxonomy, model participation, or implementation
behavior.

---

## Decision

### Semantic Authority

This Governance Decision is the sole Governance authority for the semantic
authority class of an ADE canonical decision.

An ADE canonical decision may possess authority only as an ADE-owned,
non-executing semantic result within the AI Decision Engine bounded context.

AI Decision Engine owns the semantic meaning of its canonical decision. That
authority is internal to ADE and does not imply authority in another bounded
context.

Consumption or reference by another context does not silently transfer ADE
canonical authority to that context, and consumption or reference of another
context does not transfer that context's authority to ADE.

### Authority Granted

Subject to later-approved deterministic and governed acceptance, ADE may
recognize a result as canonical authority for ADE semantic purposes only.

This authority:

- belongs only to AI Decision Engine semantic meaning;
- applies only within the AI Decision Engine bounded context;
- remains non-executing;
- remains subordinate to authorized upstream meaning and repository-wide
  authority boundaries;
- does not authorize any downstream consumer;
- does not authorize any financial action or state transition outside ADE.

An ADE canonical decision does not become more authoritative because it is
displayed, recorded, preserved, referenced, or consumed by another context.

### Authority Explicitly Denied

An ADE canonical decision is not:

- Human Review authority;
- Human Review approval;
- human approval;
- trade approval;
- Strategy Engine authority;
- strategy-selection authority;
- Risk authority;
- risk approval;
- risk-limit authority;
- compliance approval;
- Portfolio authority;
- portfolio-construction authority;
- Portfolio mutation authority;
- OMS authority;
- order-admission authority;
- Order Intent;
- executable instruction;
- broker authorization;
- Broker Execution authorization.

ADE canonical authority must not inherit, replace, merge with, or redefine any
of these authorities.

---

## Canonical Authority Boundary

Raw material is not inherently canonical ADE authority.

Advisory material is not inherently canonical ADE authority.

Nondeterministic material is not inherently canonical ADE authority.

The following cannot independently establish canonical ADE authority:

- raw model output;
- model reasoning or explanation;
- model confidence;
- candidate material;
- upstream Human Review attestation;
- absence of evidence;
- implementation behavior;
- presentation or recording.

A canonical ADE result may become authoritative only through deterministic,
governed acceptance.

This is a Governance requirement. It does not define:

- an acceptance algorithm;
- a formula;
- a threshold;
- ranking;
- scoring;
- a canonicalization mechanism;
- validation implementation;
- model or provider behavior;
- storage;
- a schema.

Nondeterministic model output must never silently become canonical AI Decision
Engine state. A model output that has not satisfied deterministic, governed
acceptance has no canonical ADE authority.

Canonical ADE authority is limited to the ADE bounded context. It does not
become authority for Human Review, Dashboard, Morning Briefing, Premarket
Scoring, Strategy Engine, Risk, Portfolio, OMS, Broker Execution, or any other
bounded context.

---

## Human Review Authority Firewall

Human Review remains its own frozen Sprint 11 bounded context.

```text
Human Review record
  ≠ AI Decision
  ≠ AI proposal approval
  ≠ Order Intent
  ≠ execution authority
```

Human Review public outputs remain the sole authorized upstream input under
Decision #2 and provide recorded human-attestation context only.

Human Review attestation does not equal ADE canonical authority. The existence
of a Human Review artifact does not delegate authority to create or approve an
ADE canonical decision.

AI Decision Engine shall not:

- fabricate Human Review;
- infer Human Review from absence or missing information;
- reinterpret Human Review semantics;
- overwrite Human Review history;
- mutate Human Review records;
- treat Human Review attestation as approval of an ADE canonical decision;
- convert Human Review into trade authority;
- convert Human Review into Order Intent;
- convert Human Review into execution authority.

This Decision does not redesign Sprint 11 and does not define the future human
authority relationship over ADE outputs. That remains reserved for Governance
Decision #8.

---

## Model Authority Firewall

This Decision does not select or authorize:

- an LLM;
- a model;
- a model provider;
- a prompt;
- training;
- fine-tuning;
- inference topology;
- hosting;
- a canonicalization algorithm.

This Decision does not authorize model integration.

No model output may independently confer canonical ADE authority. No confidence
value may independently confer authority. No explanation or reasoning may
independently confer authority. Model or provider identity, if later relevant,
does not itself confer semantic authority.

Any later model participation remains subordinate to determinism, governed
acceptance, PIT, replay, fail-closed, identity, provenance, Decimal, and
public-contract invariants.

---

## Strategy, Risk, Portfolio, and OMS Firewall

Sprint 4 ownership boundaries remain preserved.

AI Decision Engine shall not:

- replace, merge with, or inherit Strategy Engine authority;
- become strategy-selection authority;
- own Risk semantics;
- approve risk;
- change risk limits;
- inherit Risk authority;
- own Portfolio semantics;
- construct Portfolio state;
- mutate Portfolio state;
- inherit Portfolio authority;
- own OMS lifecycle semantics;
- create OMS authority;
- mutate OMS;
- become order-admission authority.

This Decision does not authorize Strategy Engine, Risk, Portfolio, or OMS
consumption or mutation. It does not redesign Sprint 4.

---

## Deferred and Forbidden Inputs Remain Closed

Decision #3 does not amend Decision #2.

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

This Decision creates no conditional reads, convenience reads, fallback reads,
hidden authority paths, or downstream consumption authorization.

No fallback source may become canonical ADE authority merely because authorized
Human Review input or governed evidence is unavailable.

---

## Fail-Closed Authority

If canonical ADE authority cannot be established from authorized, valid,
unambiguous, deterministic, and governed evidence, no authoritative ADE
decision exists.

This rule applies to:

- missing required authority;
- invalid evidence;
- stale evidence;
- ambiguous evidence;
- conflicting evidence;
- unauthorized evidence;
- nondeterministic material that has not satisfied governed acceptance;
- inability to establish deterministic governed acceptance.

AI Decision Engine shall not establish authority through:

- inference;
- fabrication;
- repair that creates authority;
- substitution;
- fallback;
- silent promotion;
- authority by absence;
- authority by presentation, recording, or downstream consumption.

This Decision does not define whether the concrete representation of such a
condition is an abstention, rejection, error, failure, no-decision result, or
another output type. Output and abstention semantics belong to Governance
Decision #7 and later Policy as authorized.

---

## Decision and Approval Separation

The following distinctions are binding:

```text
ADE canonical decision
  ≠ Human Review approval
  ≠ human approval
  ≠ trade approval
  ≠ risk approval
  ≠ portfolio authority
  ≠ Order Intent
  ≠ executable instruction
  ≠ Broker Execution authorization
```

An ADE canonical decision does not authorize a human approval workflow. Human
authority over ADE outputs remains reserved for Governance Decision #8.

---

## Broker Execution Firewall

```text
AI Decision
  ≠ Order Intent
  ≠ executable instruction
  ≠ Broker Execution authorization
```

Decision #3 authorizes none of the following:

- Order Intent creation;
- broker APIs or SDKs;
- order submission;
- order cancellation;
- order replacement;
- fill processing;
- live trading;
- capital deployment;
- OMS mutation;
- Portfolio mutation;
- execution authorization.

An ADE canonical decision alone shall never constitute Broker Execution
authorization.

Broker Execution remains DENIED / DEFERRED and requires a future independent
Planning Gate. Repository sequencing is not authorization.

---

## Reserved Later Governance Decisions

This Decision freezes AI Decision authority only. The following remain
NOT STARTED and are not resolved by this Decision:

| # | Planned Decision | Status |
| --- | --- | --- |
| 4 | Identity | NOT STARTED |
| 5 | Provenance | NOT STARTED |
| 6 | Replay / PIT | NOT STARTED |
| 7 | Output / Abstention | NOT STARTED |
| 8 | Human Authority over AI Decision Engine Outputs | NOT STARTED |

This Decision does not define:

- ADE identity format;
- hash strategy;
- digest construction;
- provenance schema;
- provenance serialization;
- replay algorithm;
- PIT comparison algorithm;
- output taxonomy;
- abstention taxonomy;
- recommendation or action taxonomy;
- reason-code taxonomy;
- confidence semantics;
- output payload or schema;
- DecisionProposal schema;
- human approval workflow.

---

## Policy Boundary

Policy Freeze remains DENIED.

Subject to later authorization, Policy may define:

- concrete deterministic acceptance rules;
- model participation rules if later Governance permits participation;
- confidence interpretation if applicable;
- thresholds if ever authorized;
- reason-code taxonomy;
- concrete failure behavior;
- exact validation rules;
- Policy identifiers and versions.

Policy must not expand authorized inputs or redefine Governance authority.

This Decision does not create or authorize a Policy Version.

---

## Implementation Boundary

Implementation remains DENIED.

This Decision does not create or define:

- algorithms;
- APIs;
- schemas;
- persistence;
- storage;
- packages;
- modules;
- services;
- database tables;
- queues or topics;
- model integration;
- provider integration;
- inference infrastructure;
- approval workflow implementation;
- execution integration.

Implementation must remain subordinate to the approved Planning Gate,
Architecture, and Governance Decisions.

---

## Resolution

**Status:** RESOLVED

**Governance effect:** The semantic authority class of an ADE canonical
decision is frozen as ADE-owned, non-executing semantic authority within the
AI Decision Engine bounded context only. Canonical authority requires
deterministic, governed acceptance. Raw, advisory, nondeterministic, model,
Human Review, absent, invalid, ambiguous, conflicting, or unaccepted material
cannot independently establish canonical ADE authority. Failure to establish
canonical authority fails closed without defining an output or abstention
taxonomy.

Decision #3 does not authorize downstream consumption, model integration,
human approval workflow, Policy Freeze, Implementation Authorization,
Implementation, Order Intent, or Broker Execution.

Governance remains IN PROGRESS — documentation-only. Decisions #1–#3 are
RESOLVED. Decisions #4–#8 remain NOT STARTED. Governance is not COMPLETE.
