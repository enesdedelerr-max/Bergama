# Morning Briefing Governance Decision #1 — Semantic Boundary

**Decision ID:** `morning-briefing.governance.01-semantic-boundary`
**Title:** Decision #1 — Morning Briefing Semantic Boundary
**Status:** RESOLVED
**Document class:** Governance Decision only
**Bounded context:** Morning Briefing

**Subordinate to:**

- Sprint 9 Planning Gate (`sprint-9.planning-gate`)
- Morning Briefing Architecture v1 (`morning-briefing.architecture.v1`)
- Premarket Scoring Governance Decisions #1–#12
- Premarket Scoring Engine Architecture v1
- Premarket Scoring Policy Version `premarket.scoring.policy.v1`

This Governance Decision freezes repository-wide semantic authority for Morning Briefing.
It does not define Architecture, Planning, Policy Version formulas, algorithms, formatting, sections, templates, ranking, weighting, output schemas, APIs, storage, notification behavior, or implementation.

---

## Purpose

Freeze the semantic meaning of a Morning Briefing.

This decision establishes what a Morning Briefing is and what it is not.
It defines semantic authority only.

---

## Repository Constraints

No Morning Briefing semantic authority exists prior to this decision.

Sprint 8 froze Premarket Scoring as a Premarket attention and ordering-priority signal under Governance Decision #1 and Policy Version `premarket.scoring.policy.v1`.

Sprint 9 Planning Gate and Morning Briefing Architecture v1 authorize Morning Briefing as the first downstream consumer of frozen Premarket Scoring outputs and as a deterministic, presentation-oriented Premarket bounded context.

This decision shall not redesign any approved repository artifact.
Morning Briefing shall never redefine Premarket Score semantics.

---

## Decision

### Semantic Authority

This Governance Decision is the sole semantic authority for the meaning of a Morning Briefing.

Neither implementation, Policy Versions, downstream bounded contexts, documentation, nor operational procedures may redefine the semantic meaning frozen by this decision.

### Semantic meaning

A Morning Briefing is a deterministic, policy-versioned, presentation-oriented assembly of operator attention context for Premarket evidence known at an explicit UTC `as_of`.

It expresses assembled Premarket attention context for human operators.
It does not express a trading decision, recommendation, approval, or execution authority.

A Morning Briefing remains subordinate to Premarket Scoring semantic authority under Premarket Scoring Governance Decision #1.
A Premarket Score consumed by Morning Briefing remains an attention and ordering-priority signal only.

### Presentation-only responsibility

Morning Briefing has presentation-oriented assembly responsibility only.

It may assemble operator-facing briefing material from authorized Premarket evidence.
It may not convert assembled material into decisioning, approval, or execution semantics.

### Consumer-only responsibility

Morning Briefing is a consumer of frozen Premarket Scoring outputs.

It may read Premarket Scoring public outputs.
It may not regenerate, recompute, repair, or replace Premarket Scores.

### Consumer Independence

The semantic meaning of a Morning Briefing shall remain invariant regardless of the number, type, or existence of downstream consumers.

The introduction, removal, or evolution of downstream bounded contexts shall not modify the semantic meaning frozen by this decision.

### Relationship to Premarket Scoring

Premarket Scoring owns score values, score ordering, score identity, score provenance, and Premarket Scoring Policy Version `premarket.scoring.policy.v1`.

Morning Briefing:

- consumes frozen Premarket Scoring outputs read-only
- preserves score semantic meaning
- preserves score domain, ordering, identity, and provenance references
- never claims ownership of Premarket Scoring artifacts

### Relationship to Dashboard

Dashboard is a deferred downstream consumer of Morning Briefing.

Morning Briefing does not become Dashboard.
Dashboard may later consume Morning Briefing outputs only through later approved Planning Gates and architectures.
Dashboard may not redefine Morning Briefing semantic meaning.

### Relationship to Human Review

Human Review is deferred and downstream of Morning Briefing.

Morning Briefing does not perform Human Review.
Morning Briefing does not approve, reject, escalate, or authorize review outcomes.
Human Review may later consume Morning Briefing outputs only as attention context, not as review authority.

### Relationship to AI Decision Engine

AI Decision Engine is deferred and downstream of Human Review.

Morning Briefing does not perform AI decisioning.
Morning Briefing does not generate model decisions, trade hypotheses as decisions, or autonomous actions.
AI Decision Engine may not redefine Morning Briefing as decision authority.

### Relationship to Broker Execution

Broker Execution is deferred and outside Morning Briefing authority.

Morning Briefing does not create order intents.
Morning Briefing does not submit, cancel, replace, or authorize orders.
Morning Briefing does not interact with broker execution boundaries.

### Morning Briefing IS

- a deterministic Premarket bounded-context output
- a presentation-oriented assembly of operator attention context
- a consumer of frozen Premarket Scoring outputs
- bound to an explicit UTC `as_of`
- subject to later frozen Morning Briefing Policy Version behavior
- subordinate to Sprint 8 Premarket Scoring semantic authority

### Morning Briefing IS NOT

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
- a Dashboard product surface
- a Broker Execution system

### Morning Briefing never

- regenerates scores
- mutates scores
- reorders scores
- interprets scores as investment advice
- performs Human Review
- performs AI decisions
- authorizes trading
- creates execution intent
- invents upstream Premarket evidence
- bypasses Governance, Policy Freeze, PIT, Replay, or fail-closed obligations

### Semantic preservation

Morning Briefing shall preserve Premarket Score semantic meaning exactly as frozen by Premarket Scoring Governance Decision #1.

Morning Briefing shall not reinterpret a higher or lower Premarket Score as expected PnL, edge, probability of profit, recommendation strength, or execution authority.

### Replay compatibility

Morning Briefing semantic meaning must remain compatible with deterministic replay.

Wall-clock time, unseeded randomness, and non-replayable state shall not affect what a Morning Briefing means.

### PIT compatibility

Morning Briefing semantic meaning is bound to explicit UTC `as_of`.

A Morning Briefing represents assembled attention context known at that `as_of` only.
Future knowledge shall not alter semantic meaning.

### Fail Closed compatibility

Morning Briefing semantic meaning forbids silent repair.

Absent, stale, conflicting, or unauthorized evidence shall not be invented, inferred, or synthesized to complete semantic meaning.

### Determinism compatibility

Same authorized inputs, configuration, Morning Briefing Policy Version, and UTC `as_of` shall produce the same semantic briefing result under later frozen policy.

Semantic meaning does not authorize nondeterministic interpretation by operators or downstream systems.

### Identity compatibility

Morning Briefing identity is distinct from Premarket Score identity.

Morning Briefing shall not reuse Premarket Score identity as a substitute for briefing identity.
Morning Briefing shall not mutate or replace Premarket Score identity references.

### Provenance compatibility

Morning Briefing provenance is distinct from Premarket Score provenance.

Morning Briefing shall preserve linkage to consumed Premarket Scoring identity and provenance references.
Morning Briefing shall not rewrite, omit, or synthesize Premarket Scoring provenance.

---

## Prohibited Assumptions

The following assumptions are prohibited:

- that a Morning Briefing authorizes trading or bypasses risk, compliance, review, kill-switch, or execution controls
- that a Morning Briefing equals expected PnL, edge, or probability of profit
- that Premarket Scores consumed by Morning Briefing change semantic meaning by virtue of inclusion in a briefing
- that absent upstream evidence may be silently invented to produce a briefing
- that wall-clock time, randomness, or non-replayable state may affect briefing semantic meaning
- that Dashboard, Human Review, AI Decision Engine, or Broker Execution may redefine Morning Briefing semantic meaning
- that Morning Briefing may redefine Premarket Score semantic meaning
- that the existence or evolution of any downstream consumer may alter Morning Briefing semantic meaning

---

## Implementation Impact

Implementation may only assemble Morning Briefings consistent with this semantic boundary.

Implementation must never reinterpret this governance.
Documentation and contracts must preserve this semantic boundary.
Implementation must treat every Morning Briefing solely as presentation-oriented Premarket attention context under the frozen Morning Briefing Policy Version identity once that Policy Version is approved.

This decision does not authorize implementation.

---

## Future Compatibility

The semantic meaning frozen by this decision is immutable across Morning Briefing Policy Versions.

Future Policy Versions may change briefing assembly behavior.
They may not change the semantic meaning frozen by this decision without a new approved Governance Decision.

Morning Briefing remains subordinate to Sprint 8 Governance Decisions and Premarket Scoring semantic authority.

Future Dashboard, Human Review, AI Decision Engine, and Broker Execution consumers may read Morning Briefing outputs only as operator attention context.
They must not redefine a Morning Briefing as a trading decision, approval, or execution authorization.

---

## Resolution

**Status:** RESOLVED

**Governance effect:** Morning Briefing semantic boundary is frozen for all subsequent Morning Briefing Governance Decisions, Morning Briefing Policy Version v1, and any later authorized Morning Briefing implementation.
