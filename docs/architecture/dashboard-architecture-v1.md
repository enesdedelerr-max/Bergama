# Dashboard Architecture v1

**Architecture ID:** `dashboard.architecture.v1`
**Bounded context:** Dashboard
**Status:** APPROVED
**Document class:** Architecture only
**Prerequisite Planning Gate:** `sprint-10.planning-gate`
**Upstream immutable foundations:** Premarket Scoring Engine Architecture v1; Premarket Scoring Policy Version `premarket.scoring.policy.v1`; Premarket Scoring Governance Decisions #1–#12; Morning Briefing Architecture v1; Morning Briefing Policy Version `morning-briefing.policy.v1`; Morning Briefing Governance Decisions #1–#8

This Architecture defines structure, responsibilities, ownership, dependency direction, public contract boundaries, ports, integration boundaries, and deterministic presentation boundaries for the Dashboard bounded context.
It does not approve Governance Decisions, Policy Freeze, or Implementation.
It does not specify algorithms, formulas, policies, concrete HTTP APIs, concrete schemas, concrete persistence models, concrete storage technology, concrete user-interface frameworks, component hierarchies, package names, services, modules, classes, persistence, transport, rendering mechanisms, or notification providers.

---

## Status

| Field | Value |
| --- | --- |
| Architecture status | APPROVED |
| Approves Governance Decisions | No |
| Approves Policy Freeze | No |
| Approves Implementation | No |
| Redesigns Sprint 8 artifacts | Forbidden |
| Redesigns Sprint 9 artifacts | Forbidden |
| Next mandatory gate after Architecture approval | Governance Gate |

This Architecture is APPROVED. Architecture approval does not by itself authorize Governance, Policy Freeze, or Implementation.
No Dashboard implementation issue, branch, or pull request may claim implementation authority from this Architecture alone.

---

## Purpose

Define the complete Clean Architecture for Dashboard Foundation as the first repository-authorized operational presentation bounded context for approved Premarket outputs, sequenced after Morning Briefing.

This Architecture establishes:

- bounded context placement and mission
- layer responsibilities and ownership
- allowed and prohibited dependencies
- public contract boundaries and ports
- upstream and downstream relationships
- identity, provenance, replay, and PIT responsibilities at architecture fidelity
- deterministic, read-only, presentation-oriented behavior obligations
- authority, auditability, and failure boundaries

This Architecture does not freeze Dashboard behavioral policy. Behavioral binding remains reserved for an approved Dashboard Policy Version under the Policy Freeze Gate after Governance completion.

---

## Architecture Authority

This Architecture defines only:

- structural responsibilities
- dependency direction
- ownership
- architectural boundaries
- public contract boundaries at architecture fidelity
- ports and integration boundaries at architecture fidelity

This Architecture does not define:

- Governance
- Policy
- Algorithms
- Business Rules
- Implementation
- Concrete HTTP APIs
- Concrete schemas
- Concrete persistence models
- Concrete storage technology
- Concrete user-interface frameworks or component hierarchies

Architecture documentation itself is not Governance authority, Policy Freeze authority, or Implementation authority.
Behavioral rules remain reserved for Governance and Policy Freeze.
Implementation derives authority only from the completed gate sequence for Dashboard.

Architecture approval does not authorize definition of concrete HTTP APIs, concrete schemas, concrete persistence models, concrete storage technology, or concrete user-interface frameworks merely because Architecture is approved.

This Architecture remains subordinate to:

- Sprint 10 Planning Gate (`sprint-10.planning-gate`)
- Premarket Scoring Engine Architecture v1
- Morning Briefing Architecture v1

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

Sprint 10 Planning Gate approved Dashboard Foundation as the Sprint 10 theme and established repository sequencing:

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

Dashboard is downstream of Morning Briefing.
Dashboard is not a peer redesign of Morning Briefing or Premarket Scoring.
Sprint 8 and Sprint 9 artifacts remain immutable under this Architecture.

---

## Architecture Principles

| Principle | Requirement |
| --- | --- |
| Presentation purity | Dashboard presents approved repository public outputs; it never regenerates, mutates, or reinterprets upstream artifacts as decisions, reviews, or execution authority |
| Read-only consumption | Upstream outputs are consumed read-only; Dashboard never mutates upstream domain artifacts |
| Determinism | Same authorized inputs, configuration, Policy Version binding, and explicit UTC `as_of` produce the same Dashboard presentation result |
| Replay-safety | Deterministic Dashboard presentation paths forbid wall-clock dependence, unseeded randomness, and mutable runtime authority |
| PIT-safety | All consumption and presentation remain bound to a single explicit UTC `as_of`; future knowledge is forbidden |
| Fail-closed | Missing, stale, conflicting, unauthorized, or invariant-violating conditions abort; silent repair is forbidden |
| Clean Architecture | Presentation → Application → Domain; Infrastructure implements interfaces owned by Application or Domain |
| Contract Stability | Approved public contracts are immutable within an approved Architecture Version |
| Semantic preservation | Premarket Score meaning and Morning Briefing meaning remain owned by their upstream contexts and are not redefined by Dashboard |
| Non-expansion | Feature Platform, Market Data, Strategy SDK, Premarket Scoring Policy Version v1, and Morning Briefing Policy Version v1 are non-expansion boundaries |
| Authority subordination | Architecture remains subordinate to Planning Gate intent and to later Governance and Policy Freeze |
| Auditability | Dashboard presentation outputs must remain independently auditable through identity references, provenance references, and pinned authorized inputs |
| Presentation neutrality | Architecture remains presentation-technology neutral; rendering form is not Architecture authority |

---

## Architecture Goals

1. Place Dashboard as a deterministic, read-only, presentation-oriented operational presentation bounded context.
2. Authorize consumption of approved Morning Briefing public outputs under explicit UTC `as_of`.
3. Define a conditional architectural path for direct Premarket Scoring public-output consumption only when later Governance and Policy Freeze explicitly authorize it; otherwise forbid such direct consumption.
4. Preserve upstream identity references, provenance references, ordering authority, score domain, briefing meaning, and semantic meaning without modification.
5. Define Clean Architecture layers and dependency direction for deterministic Dashboard presentation.
6. Define ownership of Dashboard presentation identity and presentation provenance without transferring ownership of Premarket Scores or Morning Briefing outputs.
7. Establish replay, PIT, fail-closed, public-contract, and failure-boundary obligations suitable for later Governance and Policy Freeze.
8. Keep Human Review, AI Decision Engine, and Broker Execution outside Dashboard Architecture authority.
9. Preserve Sprint 8 and Sprint 9 as non-redesign boundaries.
10. Keep Architecture free of concrete APIs, schemas, storage, UI frameworks, packages, classes, services, modules, and implementation mechanisms.

---

## Bounded Context Definition

Dashboard is an operational presentation bounded context whose mission is to provide deterministic, read-only operator visibility over approved repository public outputs known at an explicit UTC `as_of`, without acquiring domain, review, decision, or execution authority.

Dashboard is:

- a consumer of Morning Briefing public outputs
- a potential conditional consumer of Premarket Scoring public outputs only when later Governance and Policy Freeze explicitly authorize such consumption
- a presentation-oriented producer of Dashboard presentation outputs under a later frozen Dashboard Policy Version
- a read-only operational visibility context

Dashboard is not:

- a scoring engine
- a ranking engine
- a Morning Briefing regeneration authority
- a Human Review system
- an AI Decision Engine
- a Broker Execution system
- a risk, compliance, portfolio, or trade-approval authority
- the source of truth for upstream domain artifacts

---

## Responsibilities

Dashboard Architecture owns the following responsibilities:

- admit only Architecture-legal Dashboard evaluation requests under later frozen policy
- consume approved Morning Briefing public outputs without regeneration or mutation
- consume Premarket Scoring public outputs only through the conditional architectural path and only when later Governance and Policy Freeze explicitly authorize that path
- preserve referenced upstream identity, provenance, ordering authority, and semantic meaning
- assemble deterministic read-only presentation outputs from authorized repository public outputs
- bind Dashboard presentation to an explicit UTC `as_of`
- enforce PIT-safe consumption of authorized upstream outputs
- attach Dashboard presentation identity and provenance as later frozen by Governance and Policy
- fail closed on missing, stale, conflicting, unauthorized, or invariant-violating conditions
- support deterministic replay of Dashboard presentation under pinned authorized inputs
- expose Dashboard presentation outputs only through Application-owned public contract boundaries as later authorized
- preserve presentation and domain separation so presentation concerns cannot become domain authority

---

## Explicit Non-Responsibilities

Dashboard Architecture does not own:

- Premarket Score computation, normalization, weighting, aggregation, or ordering
- Premarket Score identity or score provenance generation
- Premarket Scoring Policy Version definition or amendment
- Morning Briefing assembly, regeneration, or mutation
- Morning Briefing identity or briefing provenance generation as upstream authority
- Morning Briefing Policy Version definition or amendment
- independent ranking or replacement of upstream ordering authority
- Watchlist, Catalyst, or Gap foundation redesign
- Feature Platform expansion
- Market Data contract expansion
- Strategy SDK public expansion
- Human Review workflow semantics
- AI Decision Engine decisioning
- order intent creation, order submission, cancel, replace, or execution authorization
- portfolio construction, position sizing, or ledger mutation
- risk-engine redesign
- compliance restricted-list redesign
- notification-provider selection or delivery-channel productization
- concrete production UI and product-surface implementation
- concrete HTTP API implementation
- concrete persistence or storage implementation
- live deployment productization

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
| Dashboard presentation assembly semantics | Dashboard under later frozen Dashboard Policy Version |
| Dashboard presentation identity | Dashboard |
| Dashboard presentation provenance | Dashboard |
| Dashboard Policy Version | Dashboard Policy Freeze Gate |
| Human Review authority | Future Human Review Planning Gate |
| AI Decision Engine authority | Future AI Decision Engine Planning Gate |
| Broker Execution authority | Future Broker Execution Planning Gate |

Dashboard may reference Premarket Scoring identity and provenance and Morning Briefing identity and provenance.
Dashboard may not claim ownership of Premarket Scoring artifacts or Morning Briefing artifacts, and may not rewrite them.

---

## Architecture Layers

Dashboard follows Clean Architecture with four layers.

### Presentation

**Owns:** transport adaptation and operator-facing presentation mapping after Application contracts exist, when later authorized.
**May:** invoke Application use cases; display freshness, environment distinction, and explicit UTC `as_of` context when later authorized.
**Must not:** contain scoring rules, briefing regeneration rules, independent ranking authority, authorization of financial action, Human Review semantics, AI decisioning, execution semantics, or direct Infrastructure access that bypasses Application.
**Must not:** treat mutable presentation state as repository authority.

### Application

**Owns:** use-case orchestration for Dashboard request admission, authorized upstream consumption coordination, deterministic presentation orchestration, identity and provenance attachment orchestration, post-condition validation orchestration, and replay orchestration.
**May:** depend on Domain contracts and Application-owned ports.
**Must not:** embed Premarket Scoring formulas, regenerate Morning Briefing outputs, invent evidence, mutate upstream artifacts, or own persistence technology decisions.
**Must not:** define concrete HTTP APIs, concrete schemas, or concrete storage mechanisms.

### Domain

**Owns:** Dashboard presentation-consumer invariants, semantic boundaries, fail-closed domain conditions, identity and provenance obligations at domain fidelity, and prohibition of scoring, briefing, review, decisioning, or execution semantics.
**May:** define pure domain types and invariant checks independent of frameworks.
**Must not:** import presentation frameworks, persistence frameworks, broker SDKs, Premarket Scoring internal engines, or Morning Briefing internal assembly engines.

### Infrastructure

**Owns:** adapters that implement Application or Domain ports for authorized upstream public-contract consumption and any later-authorized external integration.
**May:** adapt approved Morning Briefing public contracts and, only if later Governance and Policy Freeze authorize, Premarket Scoring public contracts.
**Must not:** redefine Domain invariants, regenerate Premarket Scores, regenerate Morning Briefing outputs, expand Feature Platform, Market Data, or Strategy SDK public contracts, or introduce storage technology as Architecture authority.

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

- Dashboard Application may depend on approved Morning Briefing public contracts only through authorized ports.
- Dashboard Application may depend on Premarket Scoring public contracts only through the conditional authorized port and only when later Governance and Policy Freeze explicitly authorize that dependency.
- Dashboard Domain must not depend on Premarket Scoring internal engines, binders, or private stages.
- Dashboard Domain must not depend on Morning Briefing internal assembly engines or private stages.
- Dashboard must not reverse dependency direction toward Human Review, AI Decision Engine, or Broker Execution.
- Cross-context communication remains public-contract-based; no direct database access across bounded contexts.
- Mutable presentation state must never authorize financial action or reverse repository authority.

---

## Upstream Dependencies

Dashboard may depend on the following completed repository artifacts as upstream inputs:

| Upstream | Dependency class | Allowed use |
| --- | --- | --- |
| Morning Briefing public outputs under Policy Version `morning-briefing.policy.v1` | Required consumer dependency | Read-only consumption of approved briefing outputs |
| Morning Briefing public identity and provenance | Required reference dependency | Preserve and reference without mutation |
| Premarket Scoring outputs under Policy Version `premarket.scoring.policy.v1` | Conditional consumer dependency | Read-only consumption only if later Governance and Policy Freeze explicitly authorize direct consumption |
| Premarket Scoring public identity and provenance | Conditional reference dependency | Preserve and reference without mutation only when the conditional consumer path is authorized |
| Explicit UTC `as_of` and Premarket PIT conventions | Mandatory evaluation dependency | Bind all consumption and presentation |
| Premarket Scoring Governance Decisions #1–#12 | Immutable semantic dependency | Preserve score meaning and Premarket invariants |
| Morning Briefing Governance Decisions #1–#8 | Immutable semantic dependency | Preserve briefing meaning and Morning Briefing invariants |
| Premarket Scoring Engine Architecture v1 | Immutable structural dependency | Preserve scoring architecture boundary |
| Morning Briefing Architecture v1 | Immutable structural dependency | Preserve briefing architecture boundary |

Dashboard shall not treat Feature Platform redesign, Market Data redesign, Strategy SDK expansion, Broker Execution, Portfolio mutation, Risk-engine redesign, Human Review, or AI Decision Engine as upstream dependencies.

---

## Downstream Consumers

The following consumers are recorded for repository sequencing and are outside Dashboard Architecture authority:

| Consumer | Relationship | Authorization under this Architecture |
| --- | --- | --- |
| Human Review | Downstream of Dashboard in repository sequencing | Deferred |
| AI Decision Engine | Downstream of Human Review | Deferred |
| Broker Execution | Outside Dashboard consumer authority | Forbidden |

Dashboard Architecture does not define Human Review, AI Decision Engine, or Broker Execution architecture.
Dashboard Architecture does not invent Sprint 11 or later sprint scope.

---

## Data Ownership

| Data class | Ownership | Dashboard duty |
| --- | --- | --- |
| Premarket Score values and component snapshots | Premarket Scoring | Consume read-only only if conditionally authorized; never recompute or alter |
| Premarket Score collection ordering | Premarket Scoring | Preserve when referenced; never independently re-rank as Dashboard authority |
| Premarket Score identity | Premarket Scoring | Reference unchanged when referenced |
| Premarket Score provenance | Premarket Scoring | Reference unchanged when referenced |
| Morning Briefing assembled outputs | Morning Briefing | Consume read-only; never regenerate or alter |
| Morning Briefing identity | Morning Briefing | Reference unchanged |
| Morning Briefing provenance | Morning Briefing | Reference unchanged |
| Dashboard presentation output | Dashboard | Produce under later frozen policy |
| Dashboard presentation identity | Dashboard | Generate deterministically under later frozen identity rules |
| Dashboard presentation provenance | Dashboard | Attach deterministically under later frozen provenance rules |

Dashboard data ownership never transfers Premarket Scoring ownership or Morning Briefing ownership into Dashboard.

---

## Identity Ownership

Premarket Scoring retains exclusive ownership of Premarket Score identity.
Morning Briefing retains exclusive ownership of Morning Briefing identity.

Dashboard owns Dashboard presentation identity for Dashboard presentation outputs only.

Identity architecture rules:

- Dashboard presentation identity must be deterministic.
- Dashboard presentation identity must not reuse Premarket Score identity or Morning Briefing identity as a substitute for Dashboard presentation identity.
- Dashboard presentation identity must not mutate or replace upstream identities.
- Dashboard presentation outputs that reference upstream artifacts must retain original upstream identity references.
- Wall-clock identifiers, unseeded random identifiers, and mutable runtime identifiers are forbidden in deterministic Dashboard identity paths.
- Exact identity payload composition remains reserved for Governance and Policy Freeze.

---

## Provenance Ownership

Premarket Scoring retains exclusive ownership of Premarket Score provenance.
Morning Briefing retains exclusive ownership of Morning Briefing provenance.

Dashboard owns Dashboard presentation provenance for Dashboard presentation outputs only.

Provenance architecture rules:

- Dashboard presentation provenance must record authorized inputs actually consumed, explicit UTC `as_of`, and Policy Version binding as later frozen.
- Dashboard presentation provenance must preserve linkage to consumed Morning Briefing provenance and identity references.
- When the conditional Premarket Scoring consumption path is authorized and used, Dashboard presentation provenance must preserve linkage to consumed Premarket Scoring provenance and identity references.
- Dashboard must not rewrite, omit, or synthesize upstream provenance.
- Provenance must support auditability and replay comparison.
- Exact provenance field composition remains reserved for Governance and Policy Freeze.

---

## Public Contract Boundaries

Dashboard Architecture defines public contract boundaries at architecture fidelity only.

Public contract boundary rules:

- Cross-bounded-context integration shall use approved public contracts only.
- Morning Briefing public outputs are the required upstream public-contract boundary for Dashboard.
- Premarket Scoring public outputs are a conditional upstream public-contract boundary and are not authorized by Architecture alone.
- Dashboard Application owns Dashboard public contract boundaries for later-authorized Dashboard presentation outputs.
- Infrastructure may adapt approved public contracts but may not invent private cross-context contracts.
- Implementation-private upstream representations are forbidden as Dashboard integration surfaces.
- Concrete HTTP APIs, concrete schemas, concrete persistence models, and concrete storage technology are outside Architecture definition and remain reserved for later authorized gates without being implied by Architecture approval.

Public contract boundaries define ownership and integration legality.
They do not define concrete contract payloads, transport mechanisms, or serialization formats.

---

## Ports

Dashboard Architecture defines the following ports at architecture fidelity only.

| Port | Direction | Architectural role |
| --- | --- | --- |
| Morning Briefing public-output consumption port | Inbound dependency port | Required read-only access to approved Morning Briefing public outputs |
| Premarket Scoring public-output consumption port | Conditional inbound dependency port | Optional read-only access only when later Governance and Policy Freeze explicitly authorize direct scoring consumption |
| Evaluation-context admission port | Application admission port | Admit Dashboard evaluation under explicit UTC `as_of` and later frozen configuration |
| Dashboard presentation emission port | Application output port | Emit deterministic Dashboard presentation outputs under later frozen policy |
| Replay comparison port | Application replay port | Support deterministic replay comparison under pinned authorized inputs |

Port rules:

- Ports are Application- or Domain-owned interfaces at architecture fidelity.
- Ports do not prescribe frameworks, dependency-injection mechanisms, clock objects, packages, classes, or runtime libraries.
- Unauthorized ports for raw Market Data, Feature Platform internals, Feature Store internals, Strategy SDK internals, broker state, portfolio state, and live execution state are forbidden.
- Opening the conditional Premarket Scoring consumption port requires later Governance and Policy Freeze authorization; Architecture alone does not open that port for implementation.

---

## Replay Compatibility

Dashboard Architecture requires deterministic replay capability for Dashboard presentation paths.

Replay responsibilities:

- accept pinned authorized inputs and pinned configuration
- re-execute Dashboard presentation without wall-clock authority
- produce structurally comparable Dashboard presentation outputs for equality verification
- fail closed on replay inequality under identical pinned inputs
- never use live unpinned external state during deterministic replay
- remain compatible with upstream Premarket Scoring and Morning Briefing replay obligations without weakening them

Replay architecture does not authorize live schedulers, workers, notification side effects, persistence side effects, or user-interface side effects as part of deterministic replay paths.

Deterministic Dashboard presentation paths shall remain replayable under explicit evaluation context, pinned authorized inputs, frozen configuration, and explicit UTC `as_of` as later frozen.

---

## PIT Compatibility

Dashboard Architecture requires point-in-time safety for all deterministic Dashboard presentation paths.

PIT responsibilities:

- bind every Dashboard evaluation to a single explicit UTC `as_of`
- consume only authorized outputs known at that `as_of` under repository Premarket conventions
- reject cross-`as_of` evidence mixtures
- reject future knowledge
- never repair PIT violations by inference, clamping, substitution, or silent reconciliation
- remain compatible with Premarket Scoring and Morning Briefing PIT rules and must not weaken them

PIT architecture obligations are mandatory for both the required Morning Briefing consumption path and any later-authorized conditional Premarket Scoring consumption path.

---

## Deterministic Presentation Architecture

Deterministic Dashboard presentation paths shall satisfy all of the following:

- same authorized inputs + same configuration + same Dashboard Policy Version + same UTC `as_of` ⇒ same Dashboard presentation output
- no wall-clock dependence in replayable presentation paths
- no unseeded randomness
- no mutable hidden runtime authority over Dashboard presentation results
- no regeneration of Premarket Scores
- no regeneration or mutation of Morning Briefing outputs
- no independent ranking that replaces upstream ordering authority
- no mutation of upstream identity, provenance, score domain, or briefing meaning
- canonical, order-stable handling of consumed references as later frozen by policy
- Decimal-safe handling of any financial or score numeric references without binary floating-point accounting semantics
- presentation remains read-only with respect to upstream domain artifacts

Behavioral parameter values remain reserved for Policy Freeze.
Presentation technology selection remains outside Architecture definition.

---

## Read-Only Responsibilities

Dashboard Architecture requires read-only responsibilities for all upstream consumption:

- Morning Briefing public outputs are consumed read-only.
- Premarket Scoring public outputs, when conditionally authorized, are consumed read-only.
- Dashboard shall not mutate, overwrite, delete, repair, invent, or synthesize upstream domain artifacts.
- Dashboard shall not become the source of truth for Premarket Scores or Morning Briefing outputs.
- Dashboard presentation outputs are distinct from upstream domain artifacts and do not replace them.
- Mutable presentation state, if later authorized at product-surface fidelity, remains non-authoritative for repository financial action.

Read-only responsibility is an architectural invariant and is not waivable by presentation technology choice.

---

## Authority Boundaries

Dashboard Architecture establishes the following authority boundaries:

| Authority | Owner | Dashboard relationship |
| --- | --- | --- |
| Premarket scoring authority | Premarket Scoring | Forbidden to Dashboard |
| Premarket ranking and ordering authority | Premarket Scoring | Forbidden to Dashboard as independent authority |
| Morning Briefing assembly authority | Morning Briefing | Forbidden to Dashboard |
| Human Review authority | Future Human Review context | Deferred; forbidden under this Architecture |
| AI decision authority | Future AI Decision Engine context | Deferred; forbidden under this Architecture |
| Broker execution authority | Future Broker Execution context | Forbidden under this Architecture |
| Risk approval authority | Risk / future authorized context | Forbidden under this Architecture |
| Compliance approval authority | Compliance / future authorized context | Forbidden under this Architecture |
| Dashboard presentation authority | Dashboard under later frozen Policy Version | Owned by Dashboard within presentation-only limits |

Dashboard must never become:

- scoring authority
- briefing authority
- review authority
- decision authority
- execution authority

Architecture alone does not authorize Governance Decisions, Policy Freeze, or Implementation.

---

## Auditability

Dashboard Architecture requires auditability of deterministic Dashboard presentation outputs.

Auditability responsibilities:

- preserve upstream identity references for consumed artifacts
- preserve upstream provenance references for consumed artifacts
- record Dashboard presentation identity and provenance as later frozen
- bind presentation to explicit UTC `as_of` and Policy Version binding as later frozen
- support independent audit reconstruction from pinned authorized inputs
- preserve correlation-capable auditability across bounded-context boundaries without prescribing transport mechanisms
- forbid silent omission of required identity or provenance references

Exact audit field composition remains reserved for Governance and Policy Freeze.

---

## Failure Boundaries

Dashboard Architecture defines the following failure boundary classes:

| Boundary | Architectural rule |
| --- | --- |
| Admission failure | Invalid request, unauthorized configuration, or unsupported evaluation context aborts before presentation |
| Required upstream consumption failure | Missing required Morning Briefing public outputs abort evaluation |
| Conditional upstream consumption failure | Unauthorized or incomplete Premarket Scoring consumption under a non-authorized conditional path aborts evaluation |
| Authorization failure | Unauthorized upstream evidence classes abort evaluation |
| PIT failure | Non-UTC `as_of`, cross-`as_of` mixture, or future knowledge aborts evaluation |
| Integrity failure | Mutated, incomplete, or inconsistent upstream identity or provenance references abort evaluation |
| Policy binding failure | Unsupported or mismatched Dashboard Policy Version aborts evaluation |
| Authority boundary failure | Any attempt to acquire scoring, briefing, review, decision, or execution authority aborts evaluation |
| Post-condition failure | Dashboard presentation invariant violations abort before output emission |
| Replay failure | Inequality under pinned identical inputs is a hard failure |

Failures must preserve original error context at Architecture boundaries.
Silent partial success for prohibited conditions is forbidden.

---

## Fail Closed Behavior

Dashboard shall fail closed when any of the following occur:

- required Morning Briefing public outputs are absent
- conditional Premarket Scoring consumption is attempted without later Governance and Policy Freeze authorization
- upstream outputs violate immutable Sprint 8 or Sprint 9 semantic expectations visible to the consumer
- unauthorized inputs are presented
- evidence is missing, stale, conflicting, or cross-PIT under later frozen rules
- Dashboard presentation identity or provenance invariants cannot be satisfied
- Dashboard Policy Version binding is unsupported or mismatched
- any attempt to regenerate, mutate, independently re-rank, or reinterpret upstream artifacts as decisions is detected
- deterministic replay obligations cannot be satisfied

Silent repair, invention, inference, synthesis, clamping, reconciliation, score regeneration, or briefing regeneration is forbidden.

---

## Bounded Context Boundaries

```text
┌────────────────────────────────────────────────────────────┐
│ Premarket Intelligence                                     │
│                                                            │
│  Watchlist / Catalyst / Gap ──▶ Premarket Scoring          │
│                                      │                     │
│                                      ▼                     │
│                              Morning Briefing              │
│                                      │                     │
└──────────────────────────────────────┼─────────────────────┘
                                       │
                                       ▼
                                   Dashboard
                                       │
                                       ▼
                         Future Human Review / AI Decision Engine
                         (outside this Architecture)
```

Boundary rules:

- Dashboard may read approved Morning Briefing public outputs.
- Dashboard may read Premarket Scoring public outputs only through the conditional architectural path and only when later Governance and Policy Freeze authorize that path.
- Dashboard may not enter Premarket Scoring internal stages.
- Dashboard may not enter Morning Briefing internal assembly stages.
- Dashboard may not mutate Watchlist, Catalyst, Gap, Scoring, or Morning Briefing owned data.
- Dashboard may not absorb Human Review, AI Decision Engine, or Broker Execution responsibilities.
- No direct broker, portfolio, or risk-engine dependency is permitted inside Dashboard.
- Dashboard remains presentation-oriented and must not become the source of truth for upstream domain artifacts.

---

## Integration Boundaries

| Integration | Boundary rule |
| --- | --- |
| Morning Briefing | Required read-only public contract consumption |
| Premarket Scoring | Conditional read-only public contract consumption only if later Governance and Policy Freeze authorize |
| Feature Platform | Non-expansion; no required integration for Dashboard Architecture v1 |
| Market Data | Non-expansion; no required integration for Dashboard Architecture v1 |
| Feature Store internals | Forbidden integration |
| Strategy SDK | Non-expansion; forbidden as Dashboard upstream dependency |
| Human Review | Downstream only; not defined here |
| AI Decision Engine | Downstream only; not defined here |
| Broker Execution | Forbidden integration |
| Portfolio state | Forbidden integration |
| Live execution state | Forbidden integration |
| Notification providers | Outside Architecture definition |
| Concrete production UI and product-surface implementation | Outside Architecture definition; deferred by Planning Gate |
| Concrete HTTP APIs | Outside Architecture definition |
| Concrete schemas | Outside Architecture definition |
| Concrete persistence models and storage technology | Outside Architecture definition |

Integration across bounded contexts must use explicit public contracts and must preserve correlation-capable auditability as later frozen without prescribing transport mechanisms.

---

## Cross-Bounded Context Rule

Dashboard shall communicate with other bounded contexts only through approved public contracts.

Cross-context internal implementation dependencies are prohibited.

This rule applies to:

- required Morning Briefing consumption
- conditional Premarket Scoring consumption, if later authorized
- all future downstream consumers, including Human Review and AI Decision Engine, when those consumers are later authorized by their own Planning Gates and architectures

No future consumer may redefine Dashboard presentation semantics outside an approved Dashboard Architecture amendment path.

---

## Architectural Invariants

The following architectural invariants are mandatory and may not be weakened by later gates except through an approved Architecture amendment under an approved Planning Gate amendment path:

1. Dashboard remains deterministic.
2. Dashboard remains replayable under explicit evaluation context, pinned authorized inputs, frozen configuration, and explicit UTC `as_of`.
3. Dashboard remains point-in-time safe under a single explicit UTC `as_of`.
4. Dashboard remains read-only with respect to upstream domain artifacts.
5. Dashboard remains presentation-oriented and is not a domain source of truth for upstream artifacts.
6. Morning Briefing public outputs remain the required upstream dependency.
7. Direct Premarket Scoring consumption remains conditional and unauthorized by Architecture alone.
8. Premarket Scoring remains the sole scoring and ordering authority.
9. Morning Briefing remains the sole briefing assembly authority.
10. Dashboard never becomes scoring, briefing, review, decision, or execution authority.
11. Clean Architecture dependency direction remains unbroken.
12. Cross-context integration remains public-contract-only.
13. Feature Platform, Market Data, Strategy SDK, Premarket Scoring Policy Version v1, and Morning Briefing Policy Version v1 remain non-expansion boundaries under this Architecture.
14. Fail-closed behavior remains mandatory for prohibited conditions.
15. Auditability through identity and provenance references remains mandatory.
16. Architecture remains free of concrete HTTP APIs, concrete schemas, concrete persistence models, concrete storage technology, and concrete UI frameworks.
17. Architecture remains subordinate to Sprint 10 Planning Gate, Premarket Scoring Engine Architecture v1, and Morning Briefing Architecture v1.

---

## Architecture Quality Requirements

Architecture documentation shall:

- remain implementation independent
- remain technology independent
- remain presentation-technology neutral
- remain deterministic in structural intent and sequencing
- remain repository-oriented
- avoid implementation assumptions
- avoid speculative future behavior beyond recorded repository sequencing
- preserve backward compatibility with approved repository artifacts
- use institutional repository language without conversational wording, placeholders, examples, or pseudo-specification
- define only architecture-fidelity concerns: bounded context, responsibilities, ownership, dependency direction, public contract boundaries, ports, and integration boundaries

An Architecture document that introduces algorithms, concrete contracts, APIs, schemas, storage, UI designs, packages, classes, services, modules, or implementation mechanisms fails Architecture Quality Requirements and cannot be approved.

---

## Repository Constraints

Dashboard Architecture shall not:

- redesign completed repository work
- modify Premarket Scoring Governance Decisions #1–#12
- modify Morning Briefing Governance Decisions #1–#8
- modify Premarket Scoring Policy Version `premarket.scoring.policy.v1`
- modify Morning Briefing Policy Version `morning-briefing.policy.v1`
- modify Premarket Scoring Engine Architecture v1
- modify Morning Briefing Architecture v1
- change repository dependency direction
- expand Feature Platform, Market Data, or Strategy SDK
- authorize implementation by Architecture approval alone
- bypass Planning Gate, Governance Gate, Policy Freeze Gate, or Implementation Authorization Gate
- weaken deterministic replay, PIT safety, fail-closed behavior, or auditability
- invent Sprint 11 or later sprint scope

Repository-wide architectural decisions affecting multiple bounded contexts remain subordinate to approved Planning Gates, Governance Decisions, and Policy Versions, and shall be recorded through an approved Architecture Decision Record when they cross bounded contexts.

---

## Non Goals

This Architecture does not define or authorize:

- Dashboard algorithms or presentation formulas
- Dashboard Policy Version content
- Governance Decision resolution
- concrete HTTP APIs, schemas, storage, persistence, or transport surfaces
- package layout, service topology, module layout, or class names
- concrete production UI and product-surface implementation
- concrete user-interface frameworks or component hierarchies
- notification providers
- Human Review Workflow
- AI Decision Engine
- Broker Execution
- live trading enablement
- Premarket Scoring redesign
- Morning Briefing redesign
- unconditional direct Premarket Scoring consumption

---

## Architecture Risks

| Risk | Effect | Architectural mitigation |
| --- | --- | --- |
| Dashboard becomes a decision authority | Violates presentation-only boundary | Explicit authority boundaries forbid decisioning and execution semantics |
| Dashboard regenerates Premarket Scores | Breaks Sprint 8 determinism and ownership | Consumer-only boundary; scoring internals inaccessible |
| Dashboard regenerates Morning Briefing | Breaks Sprint 9 ownership and auditability | Required public-contract consumption; briefing internals inaccessible |
| Dashboard independently re-ranks instruments | Diverges from Premarket Scoring ordering authority | Ordering ownership remains with Premarket Scoring |
| Direct Premarket Scoring consumption without Governance | Unauthorized coupling | Conditional port; Architecture alone does not authorize the path |
| Mutable presentation state becomes repository authority | Unauthorized financial action | Presentation state explicitly non-authoritative |
| Presentation technology leaks into Domain | Clean Architecture violation | Technology-neutral Architecture; Domain framework independence |
| Evidence invention to complete views | False operator confidence | Fail-closed missing and conflict boundaries |
| Authority creep into Human Review or Decision Engine | Sprint boundary failure | Downstream consumers deferred and non-owned |
| Feature Platform, Market Data, or Strategy SDK expansion “for Dashboard” | Cross-context contract drift | Explicit non-expansion constraints |
| Architecture used as implementation authority | Unauditable delivery | Implementation remains blocked until Implementation Authorization Gate |
| Identity or provenance mutation of upstream artifacts | Audit chain breakage | Reference-only upstream identity and provenance rules |
| Architecture defines concrete APIs, schemas, or storage | Planning and Architecture fidelity violation | Explicit Forbidden outputs and Architecture Quality Requirements |

---

## Architecture Review Requirements

Architecture review shall verify all of the following before approval:

- Dashboard is defined as downstream of Morning Briefing
- Morning Briefing public outputs are the required upstream dependency
- direct Premarket Scoring consumption remains conditional and unauthorized by Architecture alone
- Clean Architecture dependency direction is explicit and unbroken
- ownership of score values, ordering, identity, and provenance remains with Premarket Scoring
- ownership of Morning Briefing outputs, identity, and provenance remains with Morning Briefing
- Dashboard presentation identity and provenance ownership are distinct and non-mutating toward upstream artifacts
- replay, PIT, determinism, read-only, fail-closed, and auditability obligations are present
- public contract boundaries and ports are defined at architecture fidelity only
- Feature Platform, Market Data, Strategy SDK, Premarket Scoring Policy Version v1, and Morning Briefing Policy Version v1 remain non-expansion boundaries
- Human Review, AI Decision Engine, and Broker Execution remain outside authority
- no algorithms, formulas, concrete HTTP APIs, concrete schemas, concrete storage, UI designs, packages, classes, services, modules, or implementation mechanisms are introduced
- compatibility with Sprint 10 Planning Gate and Sprint 8 / Sprint 9 immutable artifacts is preserved
- Architecture remains subordinate to Premarket Scoring Engine Architecture v1 and Morning Briefing Architecture v1
- no repository authority has been duplicated, bypassed, or reassigned across gate boundaries
- Architecture Quality Requirements are satisfied

Architecture review failure blocks Architecture approval.

---

## Architecture Exit Criteria

This Architecture may be marked APPROVED only when all of the following are satisfied:

- Bounded Context Definition accepted
- Responsibilities and Explicit Non-Responsibilities accepted
- Ownership and Data Ownership accepted
- Architecture Layers and Dependency Direction accepted
- Upstream Dependencies and Downstream Consumers accepted
- Public Contract Boundaries and Ports accepted
- Replay Compatibility, PIT Compatibility, and Deterministic Presentation Architecture accepted
- Read-Only Responsibilities and Authority Boundaries accepted
- Auditability, Failure Boundaries, and Fail Closed Behavior accepted
- Integration Boundaries and Cross-Bounded Context Rule accepted
- Architectural Invariants accepted
- Architecture Quality Requirements accepted
- Repository Constraints and Non Goals accepted
- Architecture Risks reviewed and accepted at architecture level
- Architecture Review Requirements satisfied
- Future Compatibility and Architecture Evolution accepted
- Explicit record that Architecture approval does not authorize Governance, Policy Freeze, or Implementation
- No Dashboard implementation issue or branch claims authority from this Architecture alone
- No unresolved architecture contradiction remains

Architecture approval does not approve Governance, Policy Freeze, or Implementation.
This Architecture is APPROVED.

---

## Implementation Constraints

When Architecture, Governance, Policy Freeze, and Implementation Authorization are APPROVED, implementation shall remain constrained by this Architecture as follows:

- implement Dashboard as a deterministic, read-only, presentation-oriented consumer of approved Morning Briefing public outputs
- consume Premarket Scoring public outputs only if Governance and Policy Freeze explicitly authorize the conditional path
- never regenerate, mutate, independently re-rank, or reinterpret Premarket Scores
- never regenerate or mutate Morning Briefing outputs
- preserve upstream identity, provenance, ordering authority, and semantic meaning references
- bind presentation to explicit UTC `as_of`
- enforce fail-closed and PIT-safe behavior
- keep Domain free of framework and persistence imports
- keep Presentation free of business authorization rules and free of scoring, briefing, review, decision, or execution authority
- do not expand Feature Platform, Market Data, or Strategy SDK
- do not implement Human Review, AI Decision Engine, or Broker Execution under Dashboard authority
- do not treat Architecture approval as authorization for concrete HTTP APIs, schemas, storage, or UI frameworks without the completed gate sequence

This section constrains future implementation authority. It does not authorize implementation.

---

## Future Compatibility

Repository sequencing remains:

1. Premarket Scoring Foundation — complete
2. Morning Briefing Foundation — complete
3. Dashboard — Architecture v1 subject of this document
4. Human Review Workflow — deferred
5. AI Decision Engine — deferred after Human Review
6. Broker Execution — deferred after AI Decision Engine

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

Future consumers may consume Dashboard presentation outputs only through later approved Planning Gates and later architectures.
No future consumer may redefine Premarket Score semantics, regenerate scores outside Premarket Scoring, redefine Morning Briefing semantics, regenerate Morning Briefing outputs outside Morning Briefing, redefine Dashboard presentation semantics outside Dashboard, or bypass approved Premarket Scoring, Morning Briefing, or Dashboard governance and policy once those artifacts are frozen.

Dashboard technology, rendering form, transport, delivery, or product-surface changes do not alter bounded-context meaning and do not redefine Dashboard authority.

Completion of Sprint 10 shall not automatically authorize Sprint 11 or any later sprint.
This Architecture does not invent Sprint 11 scope.

This Architecture remains immutable once approved unless explicitly superseded through a subsequent approved Architecture amendment under an approved Planning Gate amendment path.
Repository evolution shall preserve backward compatibility with previously approved Architecture documents unless explicitly superseded.

---

## Architecture Evolution

Any architectural change affecting multiple bounded contexts shall require an approved Architecture Decision Record (ADR).

Architecture amendments shall not be introduced through implementation changes.

Architecture evolution remains subordinate to approved Planning Gates, Governance Decisions, and Policy Versions.
Silent architectural drift across Premarket Scoring, Morning Briefing, Dashboard, Human Review, AI Decision Engine, or Broker Execution boundaries is forbidden.

Policy Freeze remains subordinate to Governance.
Policy Versions may not supersede Governance.
Implementation may not supersede Governance or Architecture.
Only a subsequent approved Architecture amendment under an approved Planning Gate amendment path may amend frozen Dashboard Architecture authority.

---

## Conclusion

Dashboard Architecture v1 defines the Clean Architecture for a deterministic, replayable, point-in-time-safe, read-only, presentation-oriented operational presentation bounded context that consumes approved Morning Briefing public outputs, may conditionally consume Premarket Scoring public outputs only under later Governance and Policy Freeze authorization, and provides operator visibility without scoring, briefing, review, decision, or execution authority.

This Architecture defines:

- responsibilities and non-responsibilities,
- ownership and layer boundaries,
- dependency direction and integration limits,
- public contract boundaries and ports,
- identity, provenance, replay, and PIT obligations,
- read-only and authority boundaries,
- fail-closed and deterministic presentation boundaries,

while intentionally deferring all behavioral policy and implementation mechanism detail to later repository gates.

This Architecture remains subordinate to the Sprint 10 Planning Gate, Premarket Scoring Engine Architecture v1, and Morning Briefing Architecture v1.

**Architecture status:** APPROVED
**Governance authorization:** APPROVED (Dashboard Governance Decisions #1–#8 RESOLVED)
**Policy Freeze authorization:** APPROVED (`dashboard.policy.v1`)
**Implementation authorization:** APPROVED (see Dashboard Implementation Authorization v1)
