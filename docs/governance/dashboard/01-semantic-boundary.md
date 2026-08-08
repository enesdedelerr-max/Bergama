# Dashboard Governance Decision #1 — Semantic Boundary

**Decision ID:** `dashboard.governance.01-semantic-boundary`
**Title:** Decision #1 — Dashboard Semantic Boundary
**Status:** RESOLVED
**Document class:** Governance Decision only
**Bounded context:** Dashboard

**Subordinate to:**

- Sprint 10 Planning Gate (`sprint-10.planning-gate`)
- Dashboard Architecture v1 (`dashboard.architecture.v1`)
- Premarket Scoring Governance Decisions #1–#12
- Premarket Scoring Engine Architecture v1
- Premarket Scoring Policy Version `premarket.scoring.policy.v1`
- Morning Briefing Governance Decisions #1–#8
- Morning Briefing Architecture v1
- Morning Briefing Policy Version `morning-briefing.policy.v1`

This Governance Decision freezes repository-wide semantic authority for Dashboard.
It does not define Architecture, Planning, Policy Version formulas, algorithms, formatting, sections, templates, ranking, weighting, output schemas, APIs, storage, user interfaces, rendering, components, packages, classes, services, transport, notification behavior, or implementation.

---

## Purpose

Freeze the semantic meaning of Dashboard.

This decision establishes what Dashboard is and what Dashboard is not.
It defines semantic authority only.

---

## Repository Constraints

No Dashboard semantic authority exists prior to this decision.

Sprint 8 froze Premarket Scoring as a Premarket attention and ordering-priority signal under Premarket Scoring Governance Decision #1 and Policy Version `premarket.scoring.policy.v1`.

Sprint 9 froze Morning Briefing as a deterministic, presentation-oriented Premarket bounded-context assembly under Morning Briefing Governance Decision #1 and Policy Version `morning-briefing.policy.v1`.

Sprint 10 Planning Gate and Dashboard Architecture v1 authorize Dashboard as the first repository-authorized operational presentation bounded context sequenced after Morning Briefing, and as a deterministic, read-only, presentation-oriented downstream consumer of approved repository public outputs.

This decision shall not redesign any approved repository artifact.
Dashboard shall never redefine Premarket Score semantics.
Dashboard shall never redefine Morning Briefing semantics.

---

## Decision

### Semantic Authority

This Governance Decision is the sole semantic authority for the meaning of Dashboard.

Neither implementation, Policy Versions, downstream bounded contexts, documentation, nor operational procedures may redefine the semantic meaning frozen by this decision.

Dashboard semantic meaning is immutable across Dashboard Policy Versions unless explicitly superseded by a subsequent approved Dashboard Governance Decision.

### Semantic Ownership

Dashboard owns only Dashboard semantic meaning.

Dashboard does not acquire semantic ownership of any consumed repository artifact.

Semantic ownership of consumed artifacts remains permanently with the originating bounded context.

Presentation shall never transfer semantic ownership.

### Semantic meaning

Dashboard is a deterministic, replayable, point-in-time-safe, read-only, presentation-oriented operational visibility context and downstream consumer of approved repository public outputs known at an explicit UTC `as_of`.

Dashboard expresses approved repository information for operator visibility.
Dashboard does not become repository authority.

Dashboard does not express a trading decision, recommendation, approval, review outcome, or execution authority.

Dashboard remains subordinate to Premarket Scoring semantic authority under Premarket Scoring Governance Decision #1.
Dashboard remains subordinate to Morning Briefing semantic authority under Morning Briefing Governance Decision #1.

A Premarket Score referenced by Dashboard remains an attention and ordering-priority signal only.
A Morning Briefing referenced by Dashboard remains presentation-oriented Premarket attention context only.

### Presentation-only responsibility

Dashboard has presentation-oriented visibility responsibility only.

It may present approved repository public outputs as operator-facing operational visibility.
It may not convert presented material into decisioning, approval, review, or execution semantics.
It may not become the source of truth for upstream domain artifacts.

### Read-only consumer responsibility

Dashboard is a read-only downstream consumer.

It may read approved Morning Briefing public outputs.
It may read Premarket Scoring public outputs only if a later approved Dashboard Governance Decision and later approved Dashboard Policy Version explicitly authorize that conditional consumption path.
It may not regenerate, recompute, repair, reorder, mutate, or replace Premarket Scores.
It may not regenerate, mutate, or replace Morning Briefing outputs.

### Consumer Independence

The semantic meaning of Dashboard shall remain invariant regardless of the number, type, or existence of downstream consumers.

The introduction, removal, or evolution of Human Review, AI Decision Engine, Broker Execution, or any later bounded context shall not modify the semantic meaning frozen by this decision.

### Relationship to Premarket Scoring

Premarket Scoring owns score values, score ordering, score identity, score provenance, and Premarket Scoring Policy Version `premarket.scoring.policy.v1`.

Dashboard:

- consumes Premarket Scoring public outputs only through a conditional path that remains unauthorized by this decision alone
- preserves Premarket Score semantic meaning when Premarket Scoring outputs are referenced
- preserves score domain, ordering, identity, and provenance references without modification
- never claims ownership of Premarket Scoring artifacts
- never redefines Premarket Score semantics

Direct Premarket Scoring consumption remains conditional upon later approved Dashboard Governance.
This decision does not authorize direct Premarket Scoring consumption.

### Relationship to Morning Briefing

Morning Briefing remains the required upstream of Dashboard.

Morning Briefing owns Morning Briefing assembled outputs, Morning Briefing identity, Morning Briefing provenance, and Morning Briefing Policy Version `morning-briefing.policy.v1`.

Dashboard:

- consumes approved Morning Briefing public outputs read-only
- preserves Morning Briefing semantic meaning
- preserves Morning Briefing identity and provenance references without modification
- never claims ownership of Morning Briefing artifacts
- never regenerates or redefines Morning Briefing semantics

Dashboard consumes approved public outputs only.
Dashboard does not become Morning Briefing.

### Relationship to Human Review

Human Review is deferred and downstream of Dashboard in repository sequencing.

Dashboard does not perform Human Review.
Dashboard does not approve, reject, escalate, or authorize review outcomes.
Dashboard never authorizes Human Review.
Human Review may later consume Dashboard outputs only through later approved Planning Gates and architectures, and only as operational visibility context, not as review authority.

### Relationship to AI Decision Engine

AI Decision Engine is deferred and downstream of Human Review.

Dashboard does not perform AI decisioning.
Dashboard does not generate model decisions, trade hypotheses as decisions, or autonomous actions.
Dashboard never authorizes AI Decision Engine.
AI Decision Engine may not redefine Dashboard as decision authority.

### Relationship to Broker Execution

Broker Execution is deferred and outside Dashboard authority.

Dashboard does not create order intents.
Dashboard does not submit, cancel, replace, or authorize orders.
Dashboard does not interact with broker execution boundaries.
Dashboard never authorizes Broker Execution.

### Relationship to Portfolio, Risk, and Compliance

Dashboard is not Portfolio Management.
Dashboard is not a Risk Engine.
Dashboard is not a Compliance Engine.

Dashboard does not construct portfolios, size positions, mutate ledgers, approve risk, or approve compliance outcomes.
Dashboard does not bypass risk, compliance, review, kill-switch, or execution controls.

### Dashboard IS

- deterministic
- replayable
- point-in-time safe
- read-only
- presentation-oriented
- a downstream consumer
- an operational visibility context
- a consumer of approved Morning Briefing public outputs
- a potential conditional consumer of Premarket Scoring public outputs only under later approved Governance and Policy
- bound to an explicit UTC `as_of`
- subject to later frozen Dashboard Policy Version behavior
- subordinate to Sprint 8 Premarket Scoring semantic authority
- subordinate to Sprint 9 Morning Briefing semantic authority

### Dashboard IS NOT

- Premarket Scoring
- Morning Briefing
- Human Review
- AI Decision Engine
- Broker Execution
- Portfolio Management
- a Risk Engine
- a Compliance Engine
- a Source of Truth for upstream domain artifacts
- a Business Rule Engine
- a Decision Engine
- a Premarket Score
- a forecast of return, volatility, or direction
- investment advice or a trading recommendation
- an order intent, order, fill, or execution authorization
- a risk approval, compliance approval, or Human Review decision
- an AI Decision Engine decision
- a portfolio construction or position-sizing decision
- a Market Data price, quote, or bar substitute
- a Feature Platform feature value or FeatureSnapshot
- a Strategy SDK public-API contract
- a concrete production UI authority by semantic meaning alone

### Dashboard never

- fabricates repository artifacts
- infers missing repository artifacts to complete meaning
- synthesizes repository artifacts
- repairs repository artifacts
- reinterprets upstream artifacts
- mutates upstream artifacts
- regenerates Premarket Scores
- regenerates Morning Briefing outputs
- reorders Premarket Scores as independent Dashboard authority
- interprets Premarket Scores as investment advice
- interprets Morning Briefing outputs as decisions or approvals
- performs Human Review
- performs AI decisions
- authorizes trading
- creates execution intent
- transfers upstream ownership into Dashboard
- invents upstream Premarket evidence
- treats mutable presentation state as repository authority
- bypasses Governance, Policy Freeze, PIT, Replay, or fail-closed obligations

### Semantic preservation

Dashboard shall preserve Premarket Score semantic meaning exactly as frozen by Premarket Scoring Governance Decision #1.
Dashboard shall preserve Morning Briefing semantic meaning exactly as frozen by Morning Briefing Governance Decision #1.

Dashboard shall not reinterpret a higher or lower Premarket Score as expected PnL, edge, probability of profit, recommendation strength, or execution authority.
Dashboard shall not reinterpret Morning Briefing outputs as forecasts, recommendations, approvals, or execution authority.

Dashboard represents repository presentation only.
Dashboard never changes semantic meaning, ownership, ordering authority, identity, or provenance of upstream artifacts.

### Semantic Preservation Scope

Dashboard preserves semantic meaning only.

Dashboard does not preserve operational responsibility, ownership authority, or lifecycle authority for upstream artifacts.

Preservation of semantic meaning shall never be interpreted as ownership transfer.

### Ordering preservation

Ordering authority remains with Premarket Scoring.
Morning Briefing ordering-preservation obligations remain with Morning Briefing under Morning Briefing Governance.

Dashboard shall preserve ordering references without modification.
Dashboard shall not become independent ranking or ordering authority.

### Identity preservation

Dashboard presentation identity is distinct from Premarket Score identity and Morning Briefing identity.

Dashboard shall not reuse Premarket Score identity or Morning Briefing identity as a substitute for Dashboard presentation identity.
Dashboard shall not mutate or replace upstream identity references.
Dashboard shall preserve upstream identity references without modification.

Exact Dashboard identity composition remains reserved for later Governance and Policy Freeze.

### Provenance preservation

Dashboard presentation provenance is distinct from Premarket Score provenance and Morning Briefing provenance.

Dashboard shall preserve linkage to consumed Morning Briefing identity and provenance references.
When conditional Premarket Scoring consumption is later authorized and used, Dashboard shall preserve linkage to consumed Premarket Scoring identity and provenance references.
Dashboard shall not rewrite, omit, or synthesize upstream provenance.
Dashboard shall preserve upstream provenance references without modification.

Exact Dashboard provenance composition remains reserved for later Governance and Policy Freeze.

### Replay compatibility

Dashboard semantic meaning must remain compatible with deterministic replay.

Wall-clock time, unseeded randomness, and non-replayable state shall not affect what Dashboard means.
Dashboard shall preserve replay compatibility without modification of upstream semantic meaning.

### PIT compatibility

Dashboard semantic meaning is bound to explicit UTC `as_of`.

Dashboard represents operational visibility over approved repository information known at that `as_of` only.
Future knowledge shall not alter semantic meaning.
Dashboard shall preserve UTC `as_of` and PIT compatibility without modification.

### Fail Closed compatibility

Dashboard semantic meaning forbids silent repair.

Absent, stale, conflicting, or unauthorized evidence shall not be fabricated, inferred, synthesized, repaired, reinterpreted, mutated, regenerated, or reordered to complete semantic meaning.

### Determinism compatibility

Same authorized inputs, configuration, Dashboard Policy Version, and UTC `as_of` shall produce the same semantic Dashboard presentation result under later frozen policy.

Semantic meaning does not authorize nondeterministic interpretation by operators or downstream systems.

### Public-contract-only consumption

Dashboard consumes approved public outputs only.

Dashboard shall not consume implementation-private upstream representations.
Dashboard shall not redefine upstream public-contract meaning through presentation.

---

## Prohibited Assumptions

The following assumptions are prohibited:

- that Dashboard authorizes trading or bypasses risk, compliance, review, kill-switch, or execution controls
- that Dashboard equals expected PnL, edge, probability of profit, or recommendation strength
- that Premarket Scores change semantic meaning by virtue of inclusion in Dashboard presentation
- that Morning Briefing outputs change semantic meaning by virtue of inclusion in Dashboard presentation
- that Dashboard may redefine Premarket Score semantics
- that Dashboard may redefine Morning Briefing semantics
- that Dashboard may compute, regenerate, mutate, or reorder Premarket Scores
- that Dashboard may regenerate or mutate Morning Briefing outputs
- that Dashboard may reinterpret upstream artifacts as decisions, approvals, or execution authority
- that Dashboard may become repository source of truth for upstream domain artifacts
- that ownership of Premarket Scoring or Morning Briefing artifacts transfers to Dashboard through presentation
- that presentation of a repository artifact transfers semantic ownership of that artifact to Dashboard
- that preservation of semantic meaning transfers operational responsibility, ownership authority, or lifecycle authority for upstream artifacts to Dashboard
- that absent upstream evidence may be silently fabricated, inferred, synthesized, or repaired to produce Dashboard meaning
- that wall-clock time, randomness, or non-replayable state may affect Dashboard semantic meaning
- that mutable user-interface state, rendering state, or product-surface state may become repository authority
- that concrete production UI, rendering, components, transport, or notifications redefine Dashboard semantic meaning
- that Dashboard authorizes Human Review, AI Decision Engine, or Broker Execution
- that Human Review, AI Decision Engine, or Broker Execution may redefine Dashboard semantic meaning
- that the existence or evolution of any downstream consumer may alter Dashboard semantic meaning
- that Architecture, Policy Versions, or implementation may supersede this Governance Decision
- that this Governance Decision authorizes direct Premarket Scoring consumption without a later approved Governance Decision
- that this Governance Decision authorizes Policy Freeze or Implementation

---

## Implementation Impact

Implementation may only present Dashboard outputs consistent with this semantic boundary.

Implementation must never reinterpret this governance.
Documentation and contracts must preserve this semantic boundary.
Implementation must treat every Dashboard presentation solely as read-only operational visibility over approved repository public outputs under the frozen Dashboard Policy Version identity once that Policy Version is approved.

Implementation shall remain subordinate to this Governance Decision.
This Governance Decision shall not authorize implementation.

---

## Future Compatibility

The semantic meaning frozen by this decision is immutable across Dashboard Policy Versions.

Future Policy Versions may change Dashboard presentation behavior.
They may not change the semantic meaning frozen by this decision without a subsequent approved Dashboard Governance Decision.

Only a subsequent approved Dashboard Governance Decision may amend Dashboard semantic authority.

Dashboard remains subordinate to Sprint 8 Premarket Scoring Governance Decisions and Premarket Scoring semantic authority.
Dashboard remains subordinate to Sprint 9 Morning Briefing Governance Decisions and Morning Briefing semantic authority.

Future Human Review, AI Decision Engine, and Broker Execution consumers may read Dashboard outputs only as operational visibility context.
They must not redefine Dashboard as a trading decision, approval, review authority, or execution authorization.

Direct Premarket Scoring consumption, if ever permitted, shall require a later approved Dashboard Governance Decision and shall not redefine Premarket Score semantics.

---

## Resolution

**Status:** RESOLVED

**Governance effect:** Dashboard semantic boundary is frozen for all subsequent Dashboard Governance Decisions, Dashboard Policy Version binding, and any later authorized Dashboard implementation.
