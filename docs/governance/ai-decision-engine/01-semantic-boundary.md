# AI Decision Engine Governance Decision #1 — Semantic Boundary

**Decision ID:** `ai-decision-engine.governance.01-semantic-boundary`  
**Title:** Decision #1 — AI Decision Engine Semantic Boundary  
**Status:** RESOLVED  
**Document class:** Governance Decision only  
**Bounded context:** AI Decision Engine

**Subordinate to:**

- Sprint 12 Planning Gate (`sprint-12.planning-gate`) — APPROVED
- AI Decision Engine Architecture v1 (`ai-decision-engine.architecture.v1`) — APPROVED
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

This Governance Decision freezes repository-wide semantic authority for the AI Decision Engine semantic boundary.  
It does not define Architecture, Planning, Policy Version formulas, algorithms, concrete decision enumerations, action taxonomies, recommendation types, reason codes, confidence semantics, thresholds, rankings, strategy rules, trade rules, identity mechanisms, provenance composition, replay mechanics, output schemas, abstention taxonomies, human-authority workflows over AI Decision Engine outputs, model catalogs, providers, prompts, APIs, storage, user interfaces, rendering, components, packages, classes, services, transport, notification behavior, or implementation.

---

## Purpose

Freeze the repository-wide semantic meaning and authority boundary of AI Decision Engine.

This decision answers:

- What is AI Decision Engine as a semantic bounded context?
- What semantic authority does AI Decision Engine own?
- What authority does AI Decision Engine explicitly not own?
- How is AI Decision Engine semantically isolated from Human Review, Dashboard, Morning Briefing, Premarket Scoring, Strategy Engine, Risk, Portfolio, OMS, and Broker Execution?
- What must never be inferred from consumption, reference, preservation, display, recording, or lineage?

This Decision defines semantic authority only.

---

## Repository Constraints

No AI Decision Engine semantic authority exists prior to this decision.

Sprint 8 froze Premarket Scoring as a Premarket attention and ordering-priority signal under Premarket Scoring Governance Decision #1 and Policy Version `premarket.scoring.policy.v1`.

Sprint 9 froze Morning Briefing as a deterministic, presentation-oriented Premarket bounded-context assembly under Morning Briefing Governance Decision #1 and Policy Version `morning-briefing.policy.v1`.

Sprint 10 froze Dashboard as a deterministic, read-only, presentation-oriented operational visibility context under Dashboard Governance Decision #1 and Policy Version `dashboard.policy.v1`.

Sprint 11 froze Human Review as a deterministic, auditable, explicit human-attestation record under Human Review Governance Decision #1 and Policy Version `human-review.policy.v1`.

Sprint 12 Planning Gate and AI Decision Engine Architecture v1 authorize AI Decision Engine as the repository-authorized non-executing bounded context sequenced after Human Review Foundation.

This decision shall not redesign any approved repository artifact.  
AI Decision Engine shall never redefine Human Review semantics.  
AI Decision Engine shall never redefine Dashboard semantics.  
AI Decision Engine shall never redefine Morning Briefing semantics.  
AI Decision Engine shall never redefine Premarket Score semantics.  
AI Decision Engine shall never replace, merge with, or silently inherit Sprint 4 Strategy Engine, Risk, Portfolio, OMS, or Broker ownership.

This Decision does not authorize direct Dashboard consumption.  
This Decision does not authorize direct Morning Briefing consumption.  
This Decision does not authorize direct Premarket Scoring consumption.  
This Decision does not authorize Risk, Portfolio, or Strategy Engine consumption.  
This Decision does not reopen Architecture-deferred input boundaries.

Governance alone cannot reopen an Architecture-deferred input boundary.  
Reopening requires a later approved Architecture amendment and subsequent approved Governance, remaining inside Planning scope.

---

## Governance Definitions

**AI Decision Engine**  
A distinct, deterministic, auditable, point-in-time-bound, non-executing bounded context whose mission is to isolate future AI Decision semantic authority downstream of Human Review, without acquiring Human Review, Dashboard, Morning Briefing, Premarket Scoring, Strategy Engine, Risk, Portfolio, OMS, or Broker Execution authority.

**AI Decision**  
The future non-executing AI Decision Engine semantic artifact whose binding existence and isolation are established by Planning and Architecture, and whose detailed authority, taxonomy, and output contract remain reserved for later AI Decision Engine Governance Decisions and Policy Freeze. An AI Decision is not Human Review, not Human Review approval, not Order Intent, not an executable instruction, and not Broker Execution authorization.

**Semantic boundary**  
The immutable limit separating AI Decision Engine semantic ownership from upstream and downstream bounded-context ownership, and separating AI Decision meaning from trade, Order Intent, and execution authority.

These definitions freeze semantic meaning and isolation only.  
They do not freeze concrete decision types, abstention taxonomies, artifact names, schemas, model participation, identity composition, provenance composition, or human-authority workflows over AI Decision Engine outputs.

---

## Decision

### Semantic Authority

This Governance Decision is the sole semantic authority for the meaning of the AI Decision Engine semantic boundary.

Neither implementation, Policy Versions, downstream bounded contexts, documentation, nor operational procedures may redefine the semantic meaning frozen by this decision.

AI Decision Engine semantic meaning is immutable across AI Decision Engine Policy Versions unless explicitly superseded by a subsequent approved AI Decision Engine Governance Decision.

### Semantic meaning

AI Decision Engine is a distinct, deterministic, auditable, point-in-time-bound, non-executing bounded context downstream of Human Review.

AI Decision Engine isolates future AI Decision semantic authority.  
AI Decision Engine does not become Human Review.  
AI Decision Engine does not become Order Intent.  
AI Decision Engine does not become Broker Execution.  
AI Decision Engine does not silently inherit upstream or downstream authority.

An AI Decision, if later authorized under later Governance and Policy Freeze, represents only a non-executing AI Decision Engine semantic artifact.  
It does not express Human Review attestation, Human Review approval, trade approval, Order Intent, executable instruction, execution authorization, risk approval, compliance approval, portfolio authorization, or Strategy Engine authority.

AI Decision Engine remains subordinate to Human Review semantic authority under Human Review Governance Decision #1.  
AI Decision Engine remains subordinate to Dashboard semantic authority under Dashboard Governance Decision #1.  
AI Decision Engine remains subordinate to Morning Briefing semantic authority under Morning Briefing Governance Decision #1.  
AI Decision Engine remains subordinate to Premarket Scoring semantic authority under Premarket Scoring Governance Decision #1.

A Human Review record referenced by AI Decision Engine remains recorded human-attestation context only.  
A Dashboard output, if later authorized and used, remains operational visibility context only.  
A Morning Briefing, if later authorized and used, remains presentation-oriented Premarket attention context only.  
A Premarket Score, if later authorized and used, remains an attention and ordering-priority signal only.

---

## Semantic Ownership

AI Decision Engine owns only AI Decision Engine semantic meaning.

Human Review retains Human Review semantic ownership.  
Dashboard retains Dashboard semantic ownership.  
Morning Briefing retains Morning Briefing semantic ownership.  
Premarket Scoring retains Premarket Scoring semantic ownership.  
Strategy Engine retains Strategy Engine ownership.  
Risk retains Risk ownership.  
Portfolio retains Portfolio ownership.  
OMS retains OMS ownership.  
Broker Execution and Broker abstraction retain their ownership boundaries.

Consumption never transfers semantic ownership.  
Reference never transfers semantic ownership.  
Preservation never transfers semantic ownership.  
Display never transfers semantic ownership.  
Recording never transfers semantic ownership.  
Lineage never transfers semantic ownership.

AI Decision Engine shall never become the semantic owner of any consumed, referenced, preserved, displayed, recorded, or lineage-linked bounded context.

---

## Semantic Preservation Scope

AI Decision Engine preserves:

- AI Decision Engine semantic meaning
- authorized upstream semantic references when consumption is authorized
- upstream identity references when consumption is authorized
- upstream provenance references when consumption is authorized

Semantic preservation shall not transfer or imply:

- Human Review authority
- Dashboard authority
- Morning Briefing authority
- Premarket Scoring authority
- Strategy Engine authority
- Risk authority
- Portfolio authority
- OMS authority
- Broker Execution authority
- Order Intent authority
- trade-approval authority
- lifecycle authority over upstream artifacts

Semantic preservation does not imply semantic ownership.

---

## Repository Semantic Independence

AI Decision Engine semantic evolution shall never redefine Human Review semantics.  
AI Decision Engine semantic evolution shall never redefine Dashboard semantics.  
AI Decision Engine semantic evolution shall never redefine Morning Briefing semantics.  
AI Decision Engine semantic evolution shall never redefine Premarket Scoring semantics.  
AI Decision Engine semantic evolution shall never redefine Strategy Engine, Risk, Portfolio, OMS, or Broker ownership.

Future AI Decision Engine Governance Decisions shall not redefine upstream semantic meaning.  
Future AI Decision Engine Policy Versions shall not redefine upstream semantic meaning.  
AI Decision Engine implementation shall not redefine upstream semantic meaning.

Only the originating bounded context may evolve its own semantic authority through its own approved Governance process.

---

## Human Review Firewall

Human Review remains its own frozen Sprint 11 bounded context.

```text
Human Review record
  ≠ AI Decision
  ≠ AI proposal approval
  ≠ Order Intent
  ≠ execution authority
```

Human Review records explicit human attestation.  
Human Review does not invent human decisions.  
Human Review never authorizes AI Decision Engine.  
AI Decision Engine may not redefine Human Review semantics.

AI Decision Engine shall not:

- fabricate Human Review
- infer Human Review from absence or missing information
- reinterpret Human Review semantics
- overwrite Human Review history
- mutate Human Review records
- treat Human Review attestation as approval of an AI Decision
- convert Human Review into trade authority
- convert Human Review into Order Intent
- convert Human Review into execution authority

Architecture acknowledges Human Review public outputs as the required Architecture v1 upstream attestation context.  
Consuming Human Review does not transfer Human Review semantic authority to AI Decision Engine.

This Decision does not define the detailed authorized-input contract.  
That belongs to future AI Decision Engine Governance Decision #2 — Authorized Inputs.

---

## AI Decision Boundary

```text
AI Decision
  ≠ Human Review
  ≠ Human Review approval
  ≠ Order Intent
  ≠ executable instruction
  ≠ Broker Execution authorization
```

AI Decision Engine is non-executing.

AI Decision Engine does not own:

- Order Intent
- OMS
- Portfolio mutation
- Risk ownership
- Strategy Engine ownership
- broker connectivity
- order submission
- cancellation
- replacement
- fills
- capital deployment
- live execution

This Decision does not freeze concrete AI Decision types.  
This Decision does not freeze action taxonomy, recommendation taxonomy, reason codes, confidence semantics, rankings, thresholds, strategy rules, trade rules, output fields, or DecisionProposal schema.

Detailed AI Decision authority, including authoritative-result versus abstention semantics beyond this boundary firewall, belongs to future AI Decision Engine Governance Decision #3 — AI Decision Authority and later Policy Freeze as authorized.

---

## Relationship to Human Review

Human Review is the Architecture-approved required upstream bounded context for Architecture v1.

AI Decision Engine may acknowledge Human Review public outputs as recorded human-attestation context only.  
AI Decision Engine shall preserve Human Review semantic meaning.  
AI Decision Engine shall never regenerate, mutate, or redefine Human Review outputs.  
AI Decision Engine shall never treat Human Review consumption as AI Decision approval.

Human Review does not equal AI Decision.  
AI Decision Engine does not become Human Review.

---

## Relationship to Dashboard

Direct Dashboard public-output consumption remains Architecture-deferred and closed under Architecture v1.

AI Decision Engine shall not inherit Dashboard authority.  
Dashboard remains owner of Dashboard semantics.  
This Decision does not authorize Dashboard consumption.  
This Decision does not reopen the deferred Dashboard input boundary.

---

## Relationship to Morning Briefing

Direct Morning Briefing public-output consumption remains Architecture-deferred and closed under Architecture v1.

AI Decision Engine shall not inherit Morning Briefing authority.  
Morning Briefing remains owner of briefing semantics.  
This Decision does not authorize Morning Briefing consumption.  
This Decision does not reopen the deferred Morning Briefing input boundary.

---

## Relationship to Premarket Scoring

Direct Premarket Scoring public-output consumption remains Architecture-deferred and closed under Architecture v1.

Premarket Scoring remains:

- score authority
- score semantic owner
- ordering authority
- score identity owner
- score provenance owner

AI Decision Engine shall not recompute, reinterpret, or independently re-rank Premarket Scores.  
This Decision does not authorize Premarket Scoring consumption.  
This Decision does not reopen the deferred Premarket Scoring input boundary.

---

## Relationship to Strategy Engine, Risk, Portfolio, and OMS

Sprint 4 ownership boundaries remain preserved.

AI Decision Engine shall not replace, merge with, or silently inherit:

- Strategy Engine ownership
- Risk ownership
- Portfolio ownership
- OMS ownership

Risk and Portfolio relationships remain Architecture-deferred and closed under Architecture v1.  
OMS remains a forbidden AI Decision Engine dependency.  
This Decision does not authorize Risk, Portfolio, Strategy Engine, or OMS consumption or mutation.  
This Decision does not redesign Sprint 4.

---

## Relationship to Broker Execution

Broker Execution remains DENIED / DEFERRED.

```text
AI Decision
  ≠ Order Intent
  ≠ executable instruction
  ≠ Broker Execution authorization
```

AI Decision Engine:

- does not create Order Intent
- does not submit orders
- does not cancel orders
- does not replace orders
- does not call broker APIs or SDKs
- does not process fills
- does not deploy capital
- does not mutate OMS
- does not mutate Portfolio
- does not authorize execution

An AI Decision alone shall never constitute Broker Execution authorization.  
AI Decision Engine never authorizes Broker Execution.

Broker Execution requires a future independent Planning Gate.  
The repository sequencing arrow from AI Decision Engine to Broker Execution is sequencing only. It is not authorization.

---

## Model / AI Boundary

This Decision does not choose or authorize:

- LLM
- model
- provider
- prompt
- training
- fine-tuning
- inference architecture
- hosting

This Decision does not resolve model participation.

It preserves only the already-approved architectural invariant that nondeterministic model output cannot silently become canonical AI Decision Engine state.

Detailed model and canonical-authority posture belongs to later AI Decision Engine Governance Decision #3 — AI Decision Authority and/or Policy Freeze as authorized.

---

## Deferred Input Closure

Architecture v1 continues to defer, with no Architecture v1 consumption ports:

- Dashboard
- Morning Briefing
- Premarket Scoring
- Risk
- Portfolio
- Strategy Engine

Those deferred input boundaries remain CLOSED under this Decision.

Governance alone cannot reopen them.  
A required Architecture amendment must occur first where Architecture v1 requires one, followed by subsequent approved Governance inside Planning scope.

---

## Reserved Later Governance Decisions

This Decision freezes only the semantic boundary.

The following remain NOT STARTED and are not resolved by this Decision beyond the minimum firewalls stated above:

| # | Planned Decision | Status |
| --- | --- | --- |
| 2 | Authorized Inputs | NOT STARTED |
| 3 | AI Decision Authority | NOT STARTED |
| 4 | Identity | NOT STARTED |
| 5 | Provenance | NOT STARTED |
| 6 | Replay / PIT | NOT STARTED |
| 7 | Output / Abstention | NOT STARTED |
| 8 | Human Authority over AI Decision Engine Outputs | NOT STARTED |

Exact identity composition, provenance composition, replay mechanics, output schemas, abstention taxonomy, and concrete human authority over AI Decision Engine outputs remain reserved for those later Decisions and Policy Freeze as authorized.

This Decision does not create files for Decisions #2–#8.

---

## AI Decision Engine IS

- a distinct bounded context
- the repository-authorized non-executing AI Decision semantic boundary downstream of Human Review
- deterministic with respect to authorized recorded inputs as later frozen
- auditable
- PIT-aware
- fail-closed at architecture fidelity
- public-contract-only with respect to cross-context integration
- subordinate to frozen Sprint 8–11 authorities
- subordinate to Sprint 4 ownership boundaries
- isolated from Broker Execution authority

---

## AI Decision Engine IS NOT

- Human Review
- Human Review approval
- AI proposal approval by virtue of Human Review consumption
- Dashboard
- Morning Briefing
- Premarket Scoring
- Strategy Engine
- Risk ownership
- Portfolio ownership
- OMS ownership
- Broker Execution
- Order Intent
- an executable instruction
- trade approval
- execution authorization
- capital deployment authority
- a ranking engine that acquires Premarket Scoring ordering authority
- a redesign of Sprint 8–11
- a silent merge of Sprint 4 foundations

---

## AI Decision Engine never

- fabricates Human Review
- infers Human Review from absence
- reinterprets Human Review semantics
- overwrites or mutates Human Review records or history
- treats Human Review attestation as AI Decision approval
- converts Human Review into trade authority, Order Intent, or execution authority
- creates Order Intent
- submits, cancels, replaces, or authorizes orders
- calls broker APIs or SDKs
- processes fills
- deploys capital
- mutates OMS or Portfolio
- reopens Architecture-deferred input boundaries by Governance alone
- redefines upstream semantic meaning
- treats mutable presentation state as repository authority
- silently promotes nondeterministic model output to canonical AI Decision Engine state
- authorizes Policy Freeze or Implementation by virtue of this Decision alone

---

## Policy Boundary

This Decision MUST NOT and does not freeze:

- Policy ID
- Policy Version
- canonical payload schema
- exact hash or digest method
- validation stages
- concrete error taxonomy
- API contracts
- persistence representation
- serialization format
- implementation classes or modules

Policy Freeze remains DENIED until AI Decision Engine Governance completion.

---

## Prohibited Assumptions

The following assumptions are prohibited:

- that AI Decision equals Human Review
- that AI Decision equals Human Review approval
- that Human Review consumption equals AI Decision approval
- that AI Decision equals Order Intent
- that AI Decision equals executable instruction
- that AI Decision equals Broker Execution authorization
- that consumption transfers semantic ownership
- that reference, preservation, display, recording, or lineage transfers semantic ownership
- that AI Decision Engine may redefine Human Review, Dashboard, Morning Briefing, or Premarket Scoring semantics
- that AI Decision Engine may replace or silently merge Strategy Engine, Risk, Portfolio, OMS, or Broker ownership
- that this Decision authorizes Dashboard, Morning Briefing, Premarket Scoring, Risk, Portfolio, or Strategy Engine consumption
- that Governance alone may reopen Architecture-deferred inputs
- that this Decision freezes concrete AI Decision types, taxonomies, thresholds, schemas, or DecisionProposal fields
- that this Decision resolves Authorized Inputs, AI Decision Authority, Identity, Provenance, Replay / PIT, Output / Abstention, or Human Authority over AI Decision Engine Outputs beyond the minimum firewalls stated here
- that this Decision chooses a model, provider, prompt, or inference architecture
- that this Decision authorizes Policy Freeze, Implementation Authorization, Implementation, or Broker Execution
- that the sequencing arrow to Broker Execution is authorization

---

## Implementation Impact

Future implementation must remain subordinate to this Decision.

Implementation may only produce AI Decision Engine artifacts consistent with this semantic boundary once later gates authorize implementation.  
Implementation must never reinterpret this governance.  
Documentation and contracts must preserve this semantic boundary.

Implementation shall never reinterpret this Decision.  
This Decision does not authorize implementation.

---

## Future Compatibility

The semantic meaning frozen by this Decision is immutable across AI Decision Engine Policy Versions.

Future Policy Versions may change later-authorized deterministic behavior.  
They may not change the semantic meaning frozen here.

Any change to AI Decision Engine semantic authority requires a subsequent approved AI Decision Engine Governance Decision.

AI Decision Engine remains subordinate to Sprint 8–11 frozen authorities and to Sprint 4 ownership boundaries.

Future Broker Execution, if ever authorized under its own Planning Gate and subsequent approved gates, may not redefine AI Decision Engine semantic meaning by consumption alone.

Deferred input consumption, if ever permitted, shall require a later approved Architecture amendment where Architecture v1 requires one, followed by subsequent approved Governance, and shall not redefine upstream semantics.

---

## Resolution

**Status:** RESOLVED

**Governance effect:** AI Decision Engine semantic boundary is frozen for all subsequent AI Decision Engine Governance Decisions, AI Decision Engine Policy Versions, and any later authorized AI Decision Engine implementation.

**Governance set status:** IN PROGRESS — documentation-only. Decision #1 RESOLVED. Decisions #2–#8 NOT STARTED. Governance is not COMPLETE.
