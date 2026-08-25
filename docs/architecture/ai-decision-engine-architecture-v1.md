# AI Decision Engine Architecture v1

**Architecture ID:** `ai-decision-engine.architecture.v1`  
**Bounded context:** AI Decision Engine  
**Status:** APPROVED  
**Document class:** Architecture only  
**Prerequisite Planning Gate:** `sprint-12.planning-gate`  
**Upstream immutable foundations:** Premarket Scoring Engine Architecture v1; Premarket Scoring Policy Version `premarket.scoring.policy.v1`; Premarket Scoring Governance Decisions #1–#12; Morning Briefing Architecture v1; Morning Briefing Policy Version `morning-briefing.policy.v1`; Morning Briefing Governance Decisions #1–#8; Dashboard Architecture v1; Dashboard Policy Version `dashboard.policy.v1`; Dashboard Governance Decisions #1–#8; Human Review Architecture v1; Human Review Policy Version `human-review.policy.v1`; Human Review Governance Decisions #1–#8

This Architecture defines structure, responsibilities, ownership, dependency direction, public contract boundaries, ports, integration boundaries, replay compatibility, PIT compatibility, auditability, human-authority boundary, decision-authority boundary, model-participation boundary, downstream isolation, architectural invariants, and future compatibility for the AI Decision Engine bounded context.  
It does not approve Governance Decisions, Policy Freeze, or Implementation.  
It does not specify algorithms, models, prompts, providers, training, fine-tuning, inference topology, concrete decision taxonomies, action taxonomies, recommendation types, reason codes, confidence semantics, thresholds, strategy rules, trade rules, approval workflows, concrete HTTP APIs, concrete schemas, concrete persistence models, concrete storage technology, concrete user-interface frameworks, package names, services, modules, classes, persistence, transport, rendering mechanisms, or notification providers.  
It does not freeze the name DecisionProposal.

---

## Status

| Field | Value |
| --- | --- |
| Architecture status | APPROVED |
| Architecture approved | Yes |
| Approves Governance Decisions | No |
| Approves Policy Freeze | No |
| Approves Implementation Authorization | No |
| Approves Implementation | No |
| Redesigns Sprint 8 artifacts | Forbidden |
| Redesigns Sprint 9 artifacts | Forbidden |
| Redesigns Sprint 10 artifacts | Forbidden |
| Redesigns Sprint 11 artifacts | Forbidden |
| Next mandatory gate after Architecture approval | Governance Gate |

This Architecture is APPROVED. Architecture approval authorizes documentation-only Governance work. Governance Decisions are not RESOLVED. No Governance artifacts exist.  
Architecture approval does not authorize Policy Freeze, Implementation Authorization, Implementation, or Broker Execution.  
Until Implementation Authorization Gate approval, no AI Decision Engine implementation issue, branch, or pull request may claim implementation authority from this Architecture alone.

**Architecture status:** APPROVED  
**Architecture approval:** GRANTED  
**Governance authorization:** AUTHORIZED for documentation-only Governance work. Governance Decisions are not RESOLVED. No Governance artifacts exist.  
**Policy Freeze authorization:** DENIED until Governance completion  
**Implementation authorization:** DENIED until Policy approval  
**Implementation:** DENIED  
**Broker Execution:** DENIED / DEFERRED

---

## Purpose

Define the complete Clean Architecture for AI Decision Engine Foundation as the repository-authorized non-executing bounded context sequenced after Human Review Foundation.

This Architecture establishes:

- bounded context placement and mission
- layer responsibilities and ownership
- allowed and prohibited dependencies
- public contract boundaries and ports
- upstream and downstream relationships
- semantic isolation without binding semantic ownership
- identity, provenance, replay, and PIT responsibilities at architecture fidelity
- human-authority boundary at architecture fidelity
- decision-authority boundary at architecture fidelity
- model-participation boundary at architecture fidelity
- Broker Execution firewall
- authority, auditability, and failure boundaries

This Architecture does not freeze AI Decision Engine behavioral policy. Behavioral binding remains reserved for an approved AI Decision Engine Policy Version under the Policy Freeze Gate after Governance completion.  
This Architecture does not resolve Governance Decisions.  
This Architecture does not define decision, recommendation, action, or abstention taxonomy.  
This Architecture does not define human approval workflow over AI Decision Engine outputs.

---

## Architecture Authority

This Architecture defines only:

- structural responsibilities
- dependency direction
- ownership and isolation
- architectural boundaries
- public contract boundaries at architecture fidelity
- ports and integration boundaries at architecture fidelity
- replay compatibility at architecture fidelity
- PIT compatibility at architecture fidelity
- auditability at architecture fidelity
- human-authority boundary at architecture fidelity
- decision-authority boundary at architecture fidelity
- model-participation boundary at architecture fidelity
- downstream isolation
- architectural invariants
- future compatibility

This Architecture does not define:

- Governance
- Policy
- Algorithms
- Business Rules
- Implementation
- Concrete decision enumerations
- Concrete recommendation types
- Concrete action taxonomies
- Reason-code catalogs
- Confidence semantics
- Thresholds
- Rankings
- Strategy rules
- Trade rules
- Model, provider, prompt, training, fine-tuning, or inference selection
- Reviewer roles or approval-state catalogs
- Concrete HTTP APIs
- Concrete schemas
- Concrete persistence models
- Concrete storage technology
- Concrete user-interface frameworks or component hierarchies
- Packages, classes, or services
- Notifications
- Rendering
- Order Intent conversion
- Broker behavior

Architecture documentation itself is not Governance authority, Policy Freeze authority, Implementation Authorization, or Implementation authority.  
Behavioral rules remain reserved for Governance and Policy Freeze.  
Implementation derives authority only from the completed gate sequence for AI Decision Engine.

Architecture approval would not authorize definition of concrete HTTP APIs, concrete schemas, concrete persistence models, concrete storage technology, concrete user-interface frameworks, concrete decision enumerations, model catalogs, or approval-workflow catalogs merely because Architecture is approved.

This Architecture remains subordinate to:

- Sprint 12 Planning Gate (`sprint-12.planning-gate`)
- Human Review Architecture v1
- Dashboard Architecture v1
- Morning Briefing Architecture v1
- Premarket Scoring Engine Architecture v1

---

## Repository Context

Sprint 8 delivered and froze Premarket Scoring Foundation, including:

- Governance Decisions #1–#12
- Premarket Scoring Engine Architecture v1
- Premarket Scoring Policy Version `premarket.scoring.policy.v1`
- Premarket Scoring implementation and release `v0.8.0-sprint8`

Sprint 9 delivered and froze Morning Briefing Foundation, including:

- Morning Briefing Architecture v1
- Morning Briefing Governance Decisions #1–#8
- Morning Briefing Policy Version `morning-briefing.policy.v1`
- Morning Briefing Implementation Authorization v1
- Morning Briefing implementation and release `v0.9.0-sprint9`

Sprint 10 delivered and froze Dashboard Foundation, including:

- Dashboard Architecture v1
- Dashboard Governance Decisions #1–#8
- Dashboard Policy Version `dashboard.policy.v1`
- Dashboard Implementation Authorization v1
- Dashboard implementation and release `v0.10.0-sprint10`

Sprint 11 delivered and froze Human Review Foundation, including:

- Human Review Architecture v1
- Human Review Governance Decisions #1–#8
- Human Review Policy Version `human-review.policy.v1`
- Human Review Implementation Authorization v1
- Human Review implementation and release `v0.11.0-sprint11`

Sprint 12 Planning Gate approved AI Decision Engine Foundation as the Sprint 12 theme and established repository sequencing:

```text
Premarket Scoring
      │
      ▼
Morning Briefing
      │
      ▼
Dashboard
      │
      ▼
Human Review
      │
      ▼
AI Decision Engine
      │
      ▼
Broker Execution
```

The final arrow is sequencing only. It is not authorization of Broker Execution.

AI Decision Engine is downstream of Human Review.  
AI Decision Engine is not a peer redesign of Human Review, Dashboard, Morning Briefing, or Premarket Scoring.  
AI Decision Engine is not a replacement or silent merge of the Sprint 4 Strategy Engine.  
Sprint 8, Sprint 9, Sprint 10, and Sprint 11 artifacts remain immutable under this Architecture.  
Sprint 4 Strategy Engine, Portfolio, Risk, OMS, and Broker abstraction foundations remain ownership boundaries.

---

## Architecture Principles

| Principle | Requirement |
| --- | --- |
| Non-execution | AI Decision Engine produces only non-executing artifacts or explicit abstention; it never creates Order Intent or execution authority |
| Semantic isolation | AI Decision Engine is a distinct bounded context; binding semantic ownership remains Governance / Policy |
| Semantic ownership | Consumption, recording, presentation, and preservation never transfer upstream semantic ownership |
| Human Review firewall | Human Review public outputs are recorded attestation context only; they are not AI Decision, proposal approval, Order Intent, or execution authority |
| Read-only consumption | Upstream outputs are consumed read-only; AI Decision Engine never mutates upstream domain artifacts |
| Determinism | Same authorized inputs, frozen configuration, later Policy Version, and code version produce the same authorized result as later frozen |
| Replay-safety | Deterministic AI Decision Engine paths forbid wall-clock dependence, unseeded randomness, live vendor or database authority on replay, and silent promotion of nondeterministic model output to canonical state |
| PIT-safety | All consumption and evaluation remain bound to a single explicit UTC `as_of`; future knowledge is forbidden |
| Fail-closed | Missing, stale, conflicting, unauthorized, or invariant-violating conditions abort; silent repair is forbidden |
| Clean Architecture | Presentation → Application → Domain; Infrastructure implements interfaces owned by Application or Domain |
| Contract Stability | Approved public contracts are immutable within an approved Architecture Version |
| Public-contract-only integration | Cross-bounded-context integration uses approved public contracts only |
| Non-expansion | Feature Platform, Market Data, Strategy SDK, Premarket Scoring, Morning Briefing, Dashboard, and Human Review frozen authorities are non-expansion boundaries |
| Authority subordination | Architecture remains subordinate to Planning Gate intent and to later Governance and Policy Freeze |
| Auditability | AI Decision Engine outputs must remain independently auditable through identity references, provenance references, and pinned authorized inputs |
| Technology independence | Architecture remains technology-neutral; transport, rendering, model hosting, and product-surface form are not Architecture authority |

---

## Architecture Goals

1. Place AI Decision Engine as a distinct, deterministic, auditable, non-executing bounded context downstream of Human Review.
2. Authorize consumption of approved Human Review public outputs only as recorded human-attestation context under explicit UTC `as_of`.
3. Keep Dashboard, Morning Briefing, Premarket Scoring, Risk, Portfolio, and Strategy Engine direct consumption deferred in Architecture v1.
4. Preserve upstream identity references, provenance references, and semantic references without modification and without acquiring upstream authority.
5. Define Clean Architecture layers and dependency direction for deterministic non-executing AI Decision artifact or abstention construction.
6. Establish isolation of a future AI Decision semantic boundary without freezing binding ownership, enumerations, or public-output schemas.
7. Preserve the unresolved relationship between existing Human Review attestation and any future human authority over AI Decision Engine outputs as a Governance question.
8. Establish that any later model participation remains subordinate to determinism, PIT, replay, and fail-closed invariants.
9. Keep Broker Execution, Order Intent, live trading, and capital deployment outside AI Decision Engine Architecture authority.
10. Preserve Sprint 8–11 as non-redesign boundaries and Sprint 4 ownership boundaries.
11. Keep Architecture free of concrete APIs, schemas, storage, UI frameworks, packages, classes, services, modules, taxonomies, thresholds, strategy rules, and implementation mechanisms.

---

## Bounded Context Definition

AI Decision Engine is a non-executing bounded context whose mission is to isolate future AI Decision semantic authority downstream of Human Review, consuming approved Human Review public outputs only as recorded human-attestation context known at an explicit UTC `as_of`, without acquiring scoring, briefing, Dashboard, Human Review, risk, portfolio, OMS, Strategy Engine, or Broker Execution authority.

AI Decision Engine is:

- deterministic with respect to authorized recorded inputs as later frozen
- auditable
- PIT-aware
- fail-closed
- provenance-preserving
- identity-preserving
- non-executing
- downstream of Human Review
- public-contract-only
- isolated from Broker Execution

AI Decision Engine is not:

- Human Review
- AI proposal approval
- Order Intent
- executable instruction
- Broker Execution authorization
- a scoring engine
- a ranking engine
- a Morning Briefing regeneration authority
- a Dashboard redesign or presentation authority
- a Human Review redesign or human-attestation authority
- a replacement of the Sprint 4 Strategy Engine
- a risk, compliance, portfolio, OMS, or trade-approval authority
- the source of truth for upstream domain artifacts
- Premarket Scoring authority
- Morning Briefing authority
- Dashboard authority
- Human Review authority
- portfolio authority
- risk authority
- OMS authority
- Broker Execution

---

## Responsibilities

AI Decision Engine Architecture owns the following responsibilities:

- admit only Architecture-legal AI Decision Engine evaluation requests
- consume approved Human Review public outputs as recorded human-attestation context only, without regeneration, inference, fabrication, or mutation
- refuse to infer Human Review from missing information
- refuse to reinterpret, overwrite, or mutate Human Review semantics or history
- refuse to treat Human Review consumption as trade approval, Order Intent, or execution authorization
- preserve referenced upstream identity, provenance, and semantic references
- bind evaluation to an explicit UTC `as_of`
- enforce PIT-safe consumption of authorized upstream outputs
- isolate a future non-executing AI Decision semantic artifact or explicit abstention without freezing its name, taxonomy, or schema
- attach AI Decision Engine identity and provenance as later frozen
- fail closed on missing, stale, conflicting, unauthorized, or invariant-violating conditions
- support deterministic replay of authorized AI Decision Engine results under pinned authorized recorded inputs
- keep canonical repository decision state deterministic even if later gates authorize model participation
- expose AI Decision Engine outputs only through Application-owned public contract boundaries as later authorized

---

## Explicit Non-Responsibilities

AI Decision Engine Architecture does not own:

- Premarket Score computation, normalization, weighting, aggregation, or ordering
- Premarket Score identity or score provenance generation
- Premarket Scoring Policy Version definition or amendment
- Morning Briefing assembly, regeneration, or mutation
- Morning Briefing identity or briefing provenance generation as upstream authority
- Morning Briefing Policy Version definition or amendment
- Dashboard presentation assembly, regeneration, or mutation
- Dashboard identity or presentation provenance generation as upstream authority
- Dashboard Policy Version definition or amendment
- Human Review outcome generation, history mutation, or semantic redefinition
- Human Review Policy Version definition or amendment
- independent ranking or replacement of upstream ordering authority
- Watchlist, Catalyst, or Gap foundation redesign
- Feature Platform expansion
- Feature Store internals
- Market Data contract expansion or raw Market Data as decision authority
- Strategy SDK public expansion
- Sprint 4 Strategy Engine replacement or silent merge
- Risk ownership or Risk Engine redesign
- Portfolio ownership, snapshot authority, or ledger mutation
- OMS ownership, mutation, or dependency
- Broker abstraction, broker connectivity, or live execution state
- Order Intent creation
- order submission, cancellation, or replacement
- fill processing
- live trading
- autonomous capital deployment
- Broker Execution implementation
- notification-provider selection or delivery-channel productization
- concrete production UI and product-surface implementation
- concrete HTTP API implementation
- concrete persistence or storage implementation
- live deployment productization
- concrete AI Decision output taxonomy
- concrete action, recommendation, reason-code, or confidence catalogs
- reviewer-role catalogs, approval-state catalogs, or approval workflow
- model, provider, prompt, training, fine-tuning, or inference selection

---

## Ownership

| Concern | Owner |
| --- | --- |
| Premarket Score values | Premarket Scoring |
| Premarket Score ordering | Premarket Scoring |
| Premarket Score identity | Premarket Scoring |
| Premarket Score provenance | Premarket Scoring |
| Premarket Scoring Policy Version `premarket.scoring.policy.v1` | Premarket Scoring / frozen Policy |
| Premarket Scoring Governance Decisions #1–#12 | Repository Governance |
| Morning Briefing assembled outputs | Morning Briefing |
| Morning Briefing identity | Morning Briefing |
| Morning Briefing provenance | Morning Briefing |
| Morning Briefing Policy Version `morning-briefing.policy.v1` | Morning Briefing / frozen Policy |
| Morning Briefing Governance Decisions #1–#8 | Repository Governance |
| Dashboard presentation outputs | Dashboard |
| Dashboard presentation identity | Dashboard |
| Dashboard presentation provenance | Dashboard |
| Dashboard Policy Version `dashboard.policy.v1` | Dashboard / frozen Policy |
| Dashboard Governance Decisions #1–#8 | Repository Governance |
| Human Review records | Human Review |
| Human Review identity | Human Review |
| Human Review provenance | Human Review |
| Human Review history authority | Human Review |
| Human Review Policy Version `human-review.policy.v1` | Human Review / frozen Policy |
| Human Review Governance Decisions #1–#8 | Repository Governance |
| Strategy Engine authority | Sprint 4 Strategy Engine |
| Portfolio authority | Portfolio |
| Risk authority | Risk |
| OMS authority | OMS |
| Broker abstraction | Sprint 4 Broker foundation |
| AI Decision Engine isolation and non-executing artifact boundary | AI Decision Engine |
| AI Decision Engine identity | AI Decision Engine |
| AI Decision Engine provenance | AI Decision Engine |
| Binding AI Decision semantic ownership | Later AI Decision Engine Governance / Policy Freeze |
| Broker Execution authority | Future Broker Execution Planning Gate |

AI Decision Engine may reference Human Review identity and provenance.  
AI Decision Engine may not claim ownership of Human Review artifacts, Dashboard artifacts, Morning Briefing artifacts, Premarket Scoring artifacts, Strategy Engine artifacts, Risk artifacts, Portfolio artifacts, OMS artifacts, or Broker artifacts, and may not rewrite them.

---

## Semantic Ownership

This Architecture isolates a future AI Decision semantic boundary.  
It does not freeze binding semantic ownership.

Human Review semantic ownership remains with Human Review.  
Dashboard semantic ownership remains with Dashboard.  
Morning Briefing semantic ownership remains with Morning Briefing.  
Premarket Scoring semantic ownership remains with Premarket Scoring.

Consumption never transfers semantic ownership.  
Recording never transfers semantic ownership.  
Presentation never transfers semantic ownership.  
Preservation never implies semantic ownership.

AI Decision Engine shall never become the semantic owner of any consumed bounded context.  
Concrete AI Decision semantic authority, enumerations, and public-output schemas remain reserved for later Governance and Policy Freeze.

---

## Semantic Preservation Scope

AI Decision Engine preserves only:

- intended AI Decision Engine semantic isolation
- approved upstream semantic references
- identity references
- provenance references

Preservation does not preserve or transfer:

- operational authority
- ownership authority
- execution authority
- scoring authority
- briefing authority
- Dashboard authority
- Human Review authority
- decision-as-execution authority
- portfolio authority
- risk authority
- OMS authority
- Strategy Engine authority

Semantic preservation does not imply semantic ownership.

---

## Repository Semantic Independence

AI Decision Engine semantic evolution shall never redefine:

- Premarket Scoring semantics
- Morning Briefing semantics
- Dashboard semantics
- Human Review semantics
- Sprint 4 Strategy Engine, Portfolio, Risk, OMS, or Broker abstraction authority

Future AI Decision Engine Governance Decisions shall not redefine upstream semantic meaning.  
Future AI Decision Engine Policy Versions shall not redefine upstream semantic meaning.  
AI Decision Engine implementation shall not redefine upstream semantic meaning.

Only the originating bounded context may evolve its own semantic authority through its own approved Governance process.

---

## Architecture Layers

AI Decision Engine follows Clean Architecture with four layers.

### Presentation

**Owns:** transport adaptation and operator-facing mapping after Application contracts exist, when later authorized.  
**May:** invoke Application use cases; display freshness, environment distinction, and explicit UTC `as_of` context when later authorized.  
**Must not:** contain scoring rules, briefing regeneration rules, Dashboard regeneration rules, Human Review mutation, independent ranking authority, authorization of financial action, Order Intent creation, execution semantics, fabricated or inferred Human Review outcomes, or direct Infrastructure access that bypasses Application.  
**Must not:** treat mutable presentation state as repository authority.  
**Must not:** auto-approve AI Decision Engine outputs.

### Application

**Owns:** use-case orchestration for AI Decision Engine request admission, authorized Human Review consumption coordination, non-executing artifact or abstention construction orchestration, identity and provenance attachment orchestration, post-condition validation orchestration, and replay orchestration.  
**May:** depend on Domain contracts and Application-owned ports.  
**Must not:** embed Premarket Scoring formulas, regenerate Morning Briefing outputs, regenerate Dashboard outputs, mutate Human Review records, invent Human Review evidence, fabricate or infer human outcomes, mutate upstream artifacts, create Order Intent, or own persistence technology decisions.  
**Must not:** define concrete HTTP APIs, concrete schemas, concrete storage mechanisms, concrete taxonomies, model catalogs, or approval-workflow catalogs.  
**Must not:** promote nondeterministic model output to canonical repository decision state.

### Domain

**Owns:** AI Decision Engine isolation invariants, non-execution invariants, semantic-isolation boundaries, fail-closed domain conditions, identity and provenance obligations at domain fidelity, prohibition of Human Review mutation, and prohibition of scoring, briefing, Dashboard redesign, Order Intent, or execution semantics.  
**May:** define pure domain types and invariant checks independent of frameworks.  
**Must not:** import presentation frameworks, persistence frameworks, broker SDKs, model-hosting SDKs as Domain authority, Premarket Scoring internal engines, Morning Briefing internal assembly engines, Dashboard internal presentation engines, or Human Review internal engines.  
**Must not:** freeze binding semantic enumerations.

### Infrastructure

**Owns:** adapters that implement Application or Domain ports for authorized upstream public-contract consumption and any later-authorized external integration.  
**May:** adapt approved Human Review public contracts.  
**Must not:** adapt Dashboard, Morning Briefing, Premarket Scoring, Risk, Portfolio, Strategy Engine, OMS, Broker, raw Market Data, Feature Platform internals, Feature Store internals, or Strategy SDK internals as Architecture v1 consumption surfaces.  
**Must not:** redefine Domain invariants, regenerate upstream outputs, expand Feature Platform, Market Data, or Strategy SDK public contracts, or introduce storage technology or model-hosting technology as Architecture authority.

---

## Dependency Direction

```text
Presentation
      │
      ▼
Application
      │
      ▼
Domain

Infrastructure implements interfaces owned by Application or Domain.
```

Additional dependency rules:

- AI Decision Engine Application may depend on approved Human Review public contracts only through the required authorized port.
- AI Decision Engine Application must not depend on Dashboard, Morning Briefing, Premarket Scoring, Risk, Portfolio, or Strategy Engine public contracts in Architecture v1.
- AI Decision Engine Domain must not depend on Human Review internal engines or private stages.
- AI Decision Engine Domain must not depend on Dashboard, Morning Briefing, or Premarket Scoring internal engines or private stages.
- AI Decision Engine must not reverse dependency direction toward Human Review, Dashboard, Morning Briefing, or Premarket Scoring ownership.
- AI Decision Engine must not reverse dependency direction toward Strategy Engine, Risk, Portfolio, OMS, or Broker ownership.
- Cross-context communication remains public-contract-based; no direct database access across bounded contexts.
- Mutable presentation state must never authorize financial action and must never reverse repository authority.

This Architecture does not design a concrete integration topology beyond these dependency rules.

---

## Upstream Dependencies

### Required upstream

| Upstream | Dependency class | Allowed use |
| --- | --- | --- |
| Human Review public outputs under Policy Version `human-review.policy.v1` | Required consumer dependency | Read-only consumption as recorded human-attestation context only |
| Human Review public identity and provenance | Required reference dependency | Preserve and reference without mutation |
| Explicit UTC `as_of` and Human Review PIT conventions | Mandatory evaluation dependency | Bind all consumption and evaluation |
| Human Review Governance Decisions #1–#8 | Immutable semantic dependency | Preserve Human Review meaning and Human Review invariants |
| Human Review Architecture v1 | Immutable structural dependency | Preserve Human Review architecture boundary |
| Dashboard Architecture v1 | Immutable structural dependency | Preserve Dashboard architecture boundary |
| Morning Briefing Architecture v1 | Immutable structural dependency | Preserve briefing architecture boundary |
| Premarket Scoring Engine Architecture v1 | Immutable structural dependency | Preserve scoring architecture boundary |
| Dashboard Governance Decisions #1–#8 | Immutable semantic dependency | Preserve Dashboard meaning; not a consumption authorization |
| Morning Briefing Governance Decisions #1–#8 | Immutable semantic dependency | Preserve briefing meaning; not a consumption authorization |
| Premarket Scoring Governance Decisions #1–#12 | Immutable semantic dependency | Preserve score meaning; not a consumption authorization |

### Architecture v1 evaluation of Planning-deferred inputs

Planning classified the following as DEFERRED. Architecture v1 evaluates each explicitly and does not silently authorize it.

| Candidate | Architecture v1 decision | Meaning |
| --- | --- | --- |
| Direct Dashboard public-output consumption | Continue to defer (A) | No Architecture v1 consumption port; not authorized by this Architecture |
| Direct Morning Briefing public-output consumption | Continue to defer (A) | No Architecture v1 consumption port; not authorized by this Architecture |
| Direct Premarket Scoring public-output consumption | Continue to defer (A) | No Architecture v1 consumption port; not authorized by this Architecture |
| Risk read or evaluation relationship | Continue to defer (A) | No Architecture v1 consumption or evaluation port; Risk ownership remains with Risk |
| Portfolio snapshot reads | Continue to defer (A) | No Architecture v1 consumption port; Portfolio ownership remains with Portfolio |
| Strategy Engine relationship or reuse | Continue to defer (A) | No Architecture v1 reuse or merge path; Strategy Engine ownership remains with Sprint 4 |

Deferred classification does not authorize later work.  
Architecture v1 does not open conditional consumption ports for these inputs.  
Later Governance cannot silently reopen a deferred input boundary. Reopening requires a later approved Architecture amendment and subsequent approved Governance, remaining inside Planning scope.

Human Review remains the sole required upstream consumption surface in Architecture v1.

### Forbidden direct dependencies

AI Decision Engine shall not treat the following as upstream dependencies or decision authority:

- raw Market Data as decision authority
- Feature Platform internals
- Feature Store internals
- Strategy SDK internals
- implementation-private upstream representations
- OMS
- Broker abstraction
- live execution state
- Feature Platform redesign
- Market Data redesign
- Strategy SDK expansion
- Broker Execution
- Portfolio mutation
- Risk-engine redesign

---

## Downstream Consumers

The following consumers are recorded for repository sequencing and are outside AI Decision Engine Architecture authority:

| Consumer | Relationship | Authorization under this Architecture |
| --- | --- | --- |
| Broker Execution | Downstream of AI Decision Engine in repository sequencing | Deferred; not authorized |

AI Decision Engine Architecture does not define Broker Execution architecture.  
AI Decision Engine Architecture does not authorize Broker Execution.  
AI Decision Engine Architecture does not invent a later sprint number for Broker Execution.  
The sequencing arrow from AI Decision Engine to Broker Execution is not authorization.

No other downstream consumer is authorized by this Architecture.

---

## Data Ownership

| Data class | Ownership | AI Decision Engine duty |
| --- | --- | --- |
| Premarket Score values and component snapshots | Premarket Scoring | Do not consume in Architecture v1; never recompute or alter |
| Premarket Score collection ordering | Premarket Scoring | Do not independently re-rank as AI Decision Engine authority |
| Premarket Score identity | Premarket Scoring | Do not mutate |
| Premarket Score provenance | Premarket Scoring | Do not mutate |
| Morning Briefing assembled outputs | Morning Briefing | Do not consume in Architecture v1; never regenerate or alter |
| Dashboard presentation output | Dashboard | Do not consume in Architecture v1; never regenerate or alter |
| Human Review output | Human Review | Consume read-only as attestation context only; never regenerate or alter |
| Human Review identity | Human Review | Reference unchanged |
| Human Review provenance | Human Review | Reference unchanged |
| Human Review history | Human Review | Never overwrite or mutate |
| Portfolio snapshots | Portfolio | Do not consume in Architecture v1; never mutate |
| Risk evaluations | Risk | Do not consume in Architecture v1; never acquire |
| Strategy Engine artifacts | Strategy Engine | Do not reuse or merge in Architecture v1 |
| AI Decision Engine output | AI Decision Engine | Produce deterministically as later frozen; non-executing |
| AI Decision Engine identity | AI Decision Engine | Generate deterministically as later frozen |
| AI Decision Engine provenance | AI Decision Engine | Attach deterministically as later frozen |

AI Decision Engine data ownership never transfers Human Review ownership, Dashboard ownership, Morning Briefing ownership, Premarket Scoring ownership, Risk ownership, Portfolio ownership, OMS ownership, or Strategy Engine ownership into AI Decision Engine.

---

## Identity Ownership

Human Review retains exclusive ownership of Human Review identity.  
Dashboard retains exclusive ownership of Dashboard presentation identity.  
Morning Briefing retains exclusive ownership of Morning Briefing identity.  
Premarket Scoring retains exclusive ownership of Premarket Score identity.

AI Decision Engine owns AI Decision Engine identity for AI Decision Engine outputs only.

Identity architecture rules:

- AI Decision Engine identity must be distinct from upstream identities.
- AI Decision Engine identity must be deterministic with respect to authorized recorded inputs as later frozen.
- AI Decision Engine identity must not reuse Human Review identity, Dashboard identity, Morning Briefing identity, or Premarket Score identity as a substitute for AI Decision Engine identity.
- AI Decision Engine identity must not mutate or replace upstream identities.
- AI Decision Engine outputs that reference upstream artifacts must retain original upstream identity references.
- Wall-clock identifiers, unseeded random identifiers, and mutable runtime identifiers are forbidden in deterministic AI Decision Engine identity paths.
- Exact identity composition remains reserved for Governance and Policy Freeze.

---

## Provenance Ownership

Human Review retains exclusive ownership of Human Review provenance.  
Dashboard retains exclusive ownership of Dashboard presentation provenance.  
Morning Briefing retains exclusive ownership of Morning Briefing provenance.  
Premarket Scoring retains exclusive ownership of Premarket Score provenance.

AI Decision Engine owns AI Decision Engine provenance for AI Decision Engine outputs only.

Provenance architecture rules:

- AI Decision Engine provenance must record authorized inputs actually consumed and explicit UTC `as_of`.
- AI Decision Engine provenance must preserve linkage to consumed Human Review identity and provenance references.
- AI Decision Engine must not rewrite, omit, or synthesize upstream provenance.
- Synthetic provenance is forbidden.
- Provenance must support auditability and replay comparison.
- Exact provenance composition remains reserved for Governance and Policy Freeze.

---

## Human Authority Boundary

Human Review remains the immediate repository-sequenced upstream.

Human Review public outputs are consumed as recorded human-attestation context only.

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
- infer Human Review from missing information
- reinterpret Human Review semantics
- overwrite Human Review history
- mutate Human Review records
- treat Human Review consumption as trade approval
- treat Human Review consumption as Order Intent
- treat Human Review consumption as execution authorization

This Architecture does not define reviewer roles, approval states, approval or rejection taxonomy, workflow engines, automatic approval, proposal-approval semantics, or human-to-Order-Intent conversion.

The exact relationship between existing Human Review attestation records and any future human authority over AI Decision Engine outputs remains unresolved by this Architecture.  
That question is preserved as an authority boundary for later approved Governance without redefining Sprint 11.

Architectural requirements for later Governance:

- later Governance must not redefine Human Review semantics
- later Governance must not treat Human Review consumption as approval of AI Decision Engine outputs merely because consumption occurred
- later Governance must not invent auto-approval
- later Governance must not convert Human Review or AI Decision Engine outputs into Order Intent or execution authority
- later Governance may resolve whether a distinct future human-authority surface over AI Decision Engine outputs exists, without collapsing that surface into Sprint 11 Human Review

The human remains final decision authority.  
Mutable user-interface state, rendering state, or product-surface state shall never become repository authority for review action or financial action.

---

## Decision Authority Boundary

This Architecture establishes the existence and isolation of a future non-executing AI Decision semantic artifact or explicit abstention.

If later authorized, an AI Decision Engine public semantic artifact:

- is non-executing
- is not Human Review
- is not Order Intent
- is not executable instruction
- is not Broker Execution authority
- cannot silently acquire upstream authority

```text
AI Decision Engine output
  ≠ Human Review
  ≠ Order Intent
  ≠ executable instruction
  ≠ Broker Execution authorization
```

This Architecture does not freeze:

- the name DecisionProposal
- concrete artifact names
- decision types
- recommendation types
- action taxonomy
- reason-code taxonomy
- confidence semantics
- scoring meaning
- thresholds
- ranking rules
- strategy rules
- trade rules
- output schema
- proposal-to-intent conversion

Binding semantic ownership and concrete taxonomy remain Governance / Policy responsibilities.  
Architecture establishes isolation and responsibility, not Policy vocabulary.

---

## Model Participation Boundary

Whether and how AI, LLM, or other model components participate remains deferred to later approved Governance.

This Architecture does not select a model, provider, prompt, training, fine-tuning, inference topology, model hosting, or canonicalization mechanism.

Architectural boundary:

- any later model participation remains subordinate to determinism, PIT, replay, fail-closed, identity, provenance, Decimal, and public-contract invariants
- nondeterministic model output must not silently become canonical repository decision state
- canonical AI Decision Engine results, if later authorized, must remain deterministic for the same authorized inputs, frozen configuration, later Policy Version, and code version
- Architecture does not choose the later mechanism that preserves that invariant

---

## Public Contract Boundaries

AI Decision Engine Architecture defines public contract boundaries at architecture fidelity only.

Public contract boundary rules:

- Cross-bounded-context integration shall use approved public contracts only.
- Human Review public outputs are the required upstream public-contract boundary for AI Decision Engine.
- Dashboard, Morning Briefing, Premarket Scoring, Risk, Portfolio, and Strategy Engine public outputs are not Architecture v1 consumption boundaries.
- AI Decision Engine Application owns AI Decision Engine public contract boundaries for later-authorized AI Decision Engine outputs.
- Infrastructure may adapt approved Human Review public contracts but may not invent private cross-context contracts.
- Implementation-private upstream representations are forbidden as AI Decision Engine integration surfaces.
- Transport or technology choice shall not redefine the contract boundary.
- Concrete HTTP APIs, concrete schemas, concrete persistence models, and concrete storage technology are outside Architecture definition and remain reserved for later authorized gates without being implied by Architecture approval.

Public contract boundaries define ownership and integration legality.  
They do not define concrete contract payloads, transport mechanisms, or serialization formats.

---

## Ports

AI Decision Engine Architecture defines the following ports at architecture fidelity only.

| Port | Direction | Architectural role |
| --- | --- | --- |
| Human Review public-output consumption port | Inbound dependency port | Required read-only access to approved Human Review public outputs as recorded human-attestation context only |
| Evaluation-context admission port | Application admission port | Admit AI Decision Engine evaluation under explicit UTC `as_of` |
| Non-executing artifact or abstention emission port | Application output port | Emit deterministic non-executing AI Decision Engine outputs as later frozen, without freezing name or taxonomy |
| Replay comparison port | Application replay port | Support deterministic replay comparison under pinned authorized recorded inputs |

Port rules:

- Ports are Application- or Domain-owned interfaces at architecture fidelity.
- Ports do not prescribe frameworks, transport, packages, classes, or runtime libraries.
- Architecture v1 does not define Dashboard, Morning Briefing, Premarket Scoring, Risk, Portfolio, or Strategy Engine consumption ports.
- Unauthorized ports for raw Market Data, Feature Platform internals, Feature Store internals, Strategy SDK internals, OMS, broker state, live execution state, and implementation-private Human Review representations are forbidden.
- Opening a deferred consumption port requires a later approved Architecture amendment; Architecture v1 and later Governance alone do not open that port.

---

## Replay Compatibility

AI Decision Engine Architecture requires deterministic replay capability for AI Decision Engine paths that consume recorded inputs.

Replay architecture rules:

- Deterministic paths forbid wall-clock dependence.
- Deterministic paths forbid unseeded randomness.
- Deterministic paths forbid live vendor or live database authority on replay.
- Replay must use pinned authorized recorded inputs, pinned configuration, and later frozen Policy Version and code version.
- Replay must reproduce the same authorized canonical result as later frozen.
- Nondeterministic model output must not become an unreproducible source of canonical state.

This Architecture does not define replay storage, clocks, serializers, or infrastructure.

---

## PIT Compatibility

All AI Decision Engine consumption and evaluation remain bound to a single explicit UTC `as_of`.

PIT architecture rules:

- Future knowledge is forbidden.
- Inputs not known at the evaluation `as_of` must fail closed.
- Human Review consumption must use Human Review public outputs known at that `as_of`.
- Late, stale, or conflicting evidence must not be silently repaired into an authorized result.

Exact stale-data and known-at rules remain reserved for Governance and Policy Freeze.

---

## Read-Only Responsibilities

AI Decision Engine consumes authorized upstream outputs read-only.

Read-only architecture rules:

- Human Review records shall not be mutated.
- Human Review history shall not be overwritten.
- Upstream identity and provenance references shall not be rewritten.
- Presentation, recording, and preservation shall not become write authority over upstream contexts.
- UI state shall not mutate repository authority.

---

## Integration Boundaries

Allowed Architecture v1 integration:

- read-only consumption of approved Human Review public contracts
- later-authorized emission of AI Decision Engine public contracts owned by AI Decision Engine Application

Forbidden integration:

- private Human Review representations
- Dashboard, Morning Briefing, or Premarket Scoring consumption in Architecture v1
- Risk, Portfolio, or Strategy Engine consumption or reuse in Architecture v1
- raw Market Data as decision authority
- Feature Platform internals
- Feature Store internals
- Strategy SDK internals
- OMS
- Broker abstraction
- live execution state
- direct database access across bounded contexts
- agent-to-agent mutation
- strategy-to-broker access

This Architecture does not design adapter topology, message buses, or service graphs.

---

## Cross-Bounded Context Rule

Cross-bounded-context integration shall use approved public contracts only.

No bounded context may:

- read another context’s private representations
- mutate another context’s records
- acquire another context’s semantic ownership by consumption
- reverse dependency direction toward an upstream owner

AI Decision Engine may consume Human Review public outputs.  
AI Decision Engine may not become Human Review.  
Human Review may not become AI Decision Engine.

---

## Failure Boundaries

AI Decision Engine must fail closed when:

- required Human Review public outputs are missing
- Human Review evidence is stale, conflicting, or unauthorized as later frozen
- explicit UTC `as_of` is missing
- PIT safety would be violated
- identity or provenance references are missing or would be rewritten
- an attempt is made to fabricate or infer Human Review
- an attempt is made to create Order Intent or execution authority
- an unauthorized upstream dependency is requested
- a deferred input boundary is requested without a later Architecture amendment
- canonicalization of later-authorized model participation cannot preserve determinism as later frozen

Silent repair, silent omission, and silent continuation are forbidden.

---

## Fail Closed Behavior

Fail-closed is an architectural invariant.

Missing, stale, conflicting, unauthorized, or invariant-violating conditions abort.  
Architecture does not define retry policy, error codes, or operator messaging.  
Those remain reserved for later Governance, Policy Freeze, and implementation authorization.

---

## Auditability

AI Decision Engine outputs must remain independently auditable against approved gates.

Auditability requires, at architecture fidelity:

- identity references
- provenance references
- explicit UTC `as_of`
- pinned authorized Human Review input references
- reconstructability on replay

Auditability does not require a specific storage technology.  
Audit logs must not include secrets, tokens, or credentials.

---

## Bounded Context Boundaries

AI Decision Engine remains isolated from:

- Premarket Scoring authority
- Morning Briefing authority
- Dashboard authority
- Human Review authority
- Strategy Engine authority
- Risk authority
- Portfolio authority
- OMS authority
- Broker Execution authority

Sprint 8–11 redesign is forbidden.  
Sprint 4 ownership boundaries remain preserved.

---

## Broker Execution Firewall

Broker Execution remains DENIED / DEFERRED.

AI Decision Engine Architecture must not authorize:

- Order Intent
- broker connectivity
- broker APIs or SDKs
- submit order
- cancel order
- replace order
- fill processing
- live trading
- capital deployment
- portfolio mutation
- OMS mutation
- execution authorization

```text
AI Decision Engine output
  ≠ Order Intent
  ≠ executable instruction
  ≠ Broker Execution authorization
```

Broker Execution requires a future independent Planning Gate.  
This Architecture does not authorize that later gate.

```text
AI Decision Engine
      │
      ▼
Broker Execution
```

The arrow is sequencing only. It is not authorization.

---

## Architectural Invariants

1. AI Decision Engine is a distinct non-executing bounded context downstream of Human Review.
2. Human Review public outputs are the sole required Architecture v1 upstream consumption surface and are attestation context only.
3. Human Review ≠ AI Decision ≠ AI proposal approval ≠ Order Intent ≠ execution authority.
4. Consumption, recording, presentation, and preservation never transfer ownership.
5. Binding semantic ownership, enumerations, and public-output schemas are not frozen by Architecture.
6. Dashboard, Morning Briefing, Premarket Scoring, Risk, Portfolio, and Strategy Engine direct consumption remain deferred in Architecture v1.
7. Raw Market Data, Feature Platform internals, Feature Store internals, Strategy SDK internals, private representations, OMS, Broker abstraction, and live execution state are forbidden dependencies.
8. Sprint 4 Strategy Engine is not replaced or silently merged.
9. Deterministic canonical behavior, explicit UTC `as_of`, PIT safety, replay compatibility, fail-closed behavior, immutable identity and provenance references, Decimal preservation, public-contract-only integration, and read-only upstream consumption remain mandatory.
10. Nondeterministic model output must not silently become canonical repository decision state.
11. AI Decision Engine output ≠ Order Intent ≠ executable instruction ≠ Broker Execution authorization.
12. The exact future human authority over AI Decision Engine outputs remains unresolved and is reserved for later Governance without redefining Sprint 11.

---

## Architecture Quality Requirements

- Architecture is documentation-only. Architecture approval does not authorize implementation.
- Architecture remains technology-neutral.
- Architecture remains independently reviewable against `sprint-12.planning-gate`.
- Architecture remains compatible with frozen Sprint 8–11 authorities.
- Architecture remains small enough to review without implementation inference.

---

## Repository Constraints

- Sprint 8–11 Planning Gates, Architecture bodies, Governance Decisions, Policy bodies, Implementation Authorization bodies, and release artifacts remain frozen.
- Sprint 4 Strategy Engine, Portfolio, Risk, OMS, and Broker abstraction ownership remains frozen.
- No implementation issue, branch, or pull request may claim implementation authority from this Architecture alone.
- Broker Execution remains unauthorized.

---

## Non Goals

This Architecture shall not:

- Approve itself
- Resolve Governance Decisions
- Freeze Policy
- Authorize implementation
- Become Human Review
- Become Broker Execution
- Create Order Intent
- Authorize live execution
- Redesign Sprint 8–11
- Replace or silently merge the Sprint 4 Strategy Engine
- Acquire Risk, Portfolio, or OMS ownership
- Open deferred Dashboard, Morning Briefing, Premarket Scoring, Risk, Portfolio, or Strategy Engine consumption ports
- Freeze DecisionProposal or any other concrete artifact name
- Define decision, recommendation, action, reason-code, or confidence taxonomy
- Select models, providers, prompts, training, fine-tuning, or inference topology
- Define human approval workflow, reviewer roles, or auto-approval
- Convert Human Review into trade approval, Order Intent, or execution authorization
- Define concrete APIs, schemas, storage, UI, packages, classes, or services

---

## Architecture Risks

| Risk | Effect | Architecture mitigation |
| --- | --- | --- |
| Architecture treated as Policy | Governance bypass | Binding ownership and taxonomies remain unfrozen |
| Human Review consumption treated as trade or execution approval | False authority | Human Authority Boundary forbids conversion |
| Deferred inputs silently opened | Unauthorized coupling | Architecture v1 continues to defer; no conditional ports |
| Nondeterministic model output becomes canonical state | Replay and audit failure | Model Participation Boundary forbids silent promotion |
| Silent merge with Strategy Engine | Authority collision | Replacement and reuse remain deferred / out of ownership |
| AI Decision Engine becomes execution authority | Unauthorized trading | Broker Execution Firewall; Order Intent forbidden |
| Premature implementation | Process failure | Architecture is APPROVED; Implementation DENIED |
| UI state treated as authority | Unaudiable action | Mutable UI state is not repository authority |

---

## Architecture Review Requirements

Architecture review shall confirm:

- theme and bounded context match Sprint 12 Planning
- Architecture fidelity is preserved
- Human Review remains the required attestation-only upstream
- deferred inputs remain deferred in Architecture v1
- forbidden dependencies remain forbidden
- binding semantic ownership is not frozen
- Human Review firewall is preserved
- Broker Execution remains DENIED / DEFERRED
- no implementation detail is introduced
- Architecture status is APPROVED only after explicit Architecture approval

A review that converts this document into Policy, implementation, or Broker Execution authorization is invalid.

---

## Architecture Exit Criteria

These exit criteria are satisfied. This Architecture is APPROVED. It was eligible to be marked APPROVED only when all of the following were satisfied:

- Bounded context accepted
- Required Human Review upstream accepted as attestation context only
- Deferred input evaluations accepted
- Forbidden dependencies accepted
- Semantic isolation accepted without binding ownership
- Human authority question preserved for Governance
- Determinism, PIT, replay, and fail-closed invariants accepted
- Broker Execution remains unauthorized
- Sprint 8–11 frozen authority preserved
- Sprint 4 ownership boundaries preserved
- No implementation issue exists
- No implementation branch exists
- No implementation exists

Unresolved Governance questions, including the exact future relationship between Human Review attestation records and any future human authority over AI Decision Engine outputs, did not block Architecture approval.  
They do not become solved merely because Architecture is APPROVED.

Architecture approval does not resolve Governance, freeze Policy, or authorize implementation.

---

## Future Compatibility

AI Decision Engine technology, rendering form, transport, delivery, model participation, or product-surface changes, if later authorized, shall not redefine AI Decision Engine authority and shall not redefine upstream authority.

Future consumers may use approved AI Decision Engine public contracts only after their own Planning Gates and subsequent approved gates.

No future consumer may redefine Human Review, Dashboard, Morning Briefing, or Premarket Score semantics, fabricate Human Review outcomes, or bypass approved Sprint 8–11 governance and policy.

Broker Execution remains a future independent theme.

Previously approved artifacts remain compatible unless explicitly superseded through approved amendments.

---

## Architecture Evolution

This Architecture is APPROVED and remains immutable in place.  
Evolution requires a later Architecture version or explicit approved amendment.  
Deferred input boundaries may be reopened only by a later approved Architecture amendment that remains inside Planning scope, followed by later approved Governance.

---

## Conclusion

AI Decision Engine Architecture v1 defines the Clean Architecture for a distinct, deterministic, replayable, point-in-time-safe, non-executing bounded context that consumes approved Human Review public outputs as recorded human-attestation context only, isolates a future AI Decision semantic artifact or explicit abstention without freezing taxonomy, and remains forbidden from Order Intent, execution, Sprint 8–11 redesign, and Sprint 4 ownership acquisition.

This Architecture defines:

- responsibilities and non-responsibilities,
- ownership and layer boundaries,
- dependency direction and integration limits,
- public contract boundaries and ports,
- identity, provenance, replay, and PIT obligations,
- human-authority, decision-authority, and model-participation boundaries,
- fail-closed and Broker Execution firewalls,

while intentionally deferring all behavioral policy, binding semantic ownership, and implementation mechanism detail to later repository gates.

This Architecture remains subordinate to the Sprint 12 Planning Gate, Human Review Architecture v1, Dashboard Architecture v1, Morning Briefing Architecture v1, and Premarket Scoring Engine Architecture v1.

This Architecture is APPROVED. It does not approve Governance Decisions, Policy Freeze, Implementation Authorization, or Implementation.

---

## Gate State

| Gate | State |
| --- | --- |
| Planning Gate | APPROVED |
| Architecture | APPROVED |
| Architecture approved | Yes |
| Governance | AUTHORIZED — documentation-only |
| Governance status | NOT STARTED |
| Governance Decisions resolved | No |
| Policy Freeze | DENIED |
| Implementation Authorization | DENIED |
| Implementation | DENIED |
| Broker Execution | DENIED / DEFERRED |

**Architecture status:** APPROVED  
**Architecture approval:** GRANTED  
**Governance authorization:** AUTHORIZED for documentation-only Governance work. Governance Decisions are not RESOLVED. No Governance artifacts exist.  
**Policy Freeze authorization:** DENIED until Governance completion  
**Implementation authorization:** DENIED until Policy approval  
**Implementation:** DENIED  
**Broker Execution:** DENIED / DEFERRED
