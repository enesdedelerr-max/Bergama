# Sprint 13 Planning Gate — Intelligence Pipeline Integration

**Planning Gate ID:** `sprint-13.planning-gate`
**Proposed theme:** Intelligence Pipeline Integration
**Status:** DRAFT / NOT YET APPROVED
**Sprint number:** 13
**Prerequisite:** Sprint 12 complete — AI Decision Engine Foundation
**Authoritative main at draft time:** `ab7ddcf7a78ed68ee1c9dd3c49b791a7e454d2be`
**Document class:** Planning Gate only
**Document role:** Canonical Planning Gate for Bergama Sprint 13 theme and scope classification
**Planning issue:** [#116](https://github.com/enesdedelerr-max/Bergama/issues/116)

This Planning Gate, when APPROVED, authorizes Sprint 13 theme selection, scope
classification, repository sequencing, and opening of a documentation-only
Architecture Gate.

It does **not** approve Architecture, Governance Decisions, Policy Freeze,
Implementation Authorization, or Implementation.

It does **not** specify algorithms, concrete module layouts, DTO field schemas,
storage schemas, HTTP routes, UI layouts, packages, services, workers,
schedulers, or deployment topology.

```text
PLANNING_APPROVAL ≠ IMPLEMENTATION_AUTHORIZATION
```

No implementation issue, branch, or pull request may claim implementation
authority merely because this Planning Gate is APPROVED.

Mandatory governance sequence remains:

```text
Planning
      │
      ▼
Architecture
      │
      ▼
Governance
      │
      ▼
Policy Freeze
      │
      ▼
Implementation Authorization
      │
      ▼
Implementation
```

Sprints 7–12 intelligence foundations remain frozen and shall not be redesigned
by this Planning Gate. Sprint 4 Trading Foundations remain ownership boundaries
and shall not be acquired or silently merged. Sprint 6 Feature Platform remains
excluded from Sprint 13 remediation.

---

## Status

| Field | Value |
| --- | --- |
| Planning Gate status | DRAFT / NOT YET APPROVED |
| Approves Architecture | No |
| Approves Governance Decisions | No |
| Approves Policy Freeze | No |
| Approves Implementation Authorization | No |
| Approves Implementation | No |
| Architecture authorization | DENIED until Planning approval; then documentation-only Architecture may begin |
| Governance authorization | DENIED |
| Policy authorization | DENIED |
| Implementation Authorization | DENIED |
| Implementation work | NOT AUTHORIZED |
| UI authorized | NO |
| MODEL PARTICIPATION | UNAUTHORIZED |
| Broker Execution | DENIED / DEFERRED |
| Next mandatory gate after Planning approval | Architecture Gate (documentation-only) |

Until this Planning Gate is APPROVED, Sprint 13 Architecture remains blocked.
Until Implementation Authorization is APPROVED, no Sprint 13 implementation
issue, branch, or pull request may claim implementation authority.

---

## Authority / Purpose

This document classifies the Sprint 13 theme and scope only.

Planning authorizes repository direction.
Planning never authorizes implementation.
Architecture cannot bypass Planning.
Governance cannot bypass Architecture.
Policy cannot supersede Governance.
Implementation cannot reinterpret Governance or Policy.

Planning approval authorizes only:

- Sprint theme
- scope classification
- repository sequencing
- opening the documentation-only Architecture Gate

Planning approval does **not** authorize:

- Architecture approval
- Governance approval
- Policy approval
- Implementation Authorization
- implementation code

---

## Authoritative Baseline

| Field | Value |
| --- | --- |
| Authoritative main | `ab7ddcf7a78ed68ee1c9dd3c49b791a7e454d2be` |
| Sprint 12 status | COMPLETE |
| Sprint 12 closeout | `docs/sprints/sprint-12/CLOSEOUT.md` |
| Sprint 12 ADE Implementation | FOUNDATION COMPLETE (Issue #110 / PR #111) |
| Sprint 12 status sync | COMPLETE (Issue #112 / PR #113) |
| Sprint 12 governance closeout | COMPLETE (Issue #114 / PR #115) |
| Sprint 12 tag / release | NOT AUTHORIZED / NOT PERFORMED |
| Sprint 13 state | NOT STARTED |
| MODEL PARTICIPATION | UNAUTHORIZED |
| Broker Execution | DENIED / DEFERRED |

`SPRINT_COMPLETE ≠ CAPABILITY_AUTHORIZATION`

---

## Problem Statement

The intelligence engines delivered in Sprints 7–12 exist as independently
tested, fail-closed libraries with public entrypoints, but the repository has
no governed application-layer orchestration that admits authorized normalized
evidence under a single UTC `as_of`, runs:

```text
Watchlist
      → Gap
      → Catalyst
      → Score
      → Briefing
      → Dashboard
```

and optionally terminates at:

```text
Human Review
      → AI Decision Engine
```

under explicit human attestation.

The missing capability is **integration / orchestration**.

It is **not**:

- a UI problem
- an HTTP API problem
- a Feature Store problem
- a broker problem
- a model problem

Test suites that manually assemble stage objects demonstrate stage
compatibility. They do **not** constitute a governed production runtime path.

---

## Objective

When later gates are APPROVED, Sprint 13 shall deliver governed **in-process**
orchestration of authorized canonical evidence through the existing Premarket
intelligence stages under:

- a single UTC-aware `as_of`
- point-in-time (PIT) safety
- determinism
- fail-closed semantics
- provenance continuity
- in-process replayability
- explicit Human Review authority
- existing ADE accept / abstain semantics
- non-executable intelligence boundaries

Sprint 13 must move the repository from:

```text
independent intelligence libraries
```

toward:

```text
an integrated deterministic intelligence pipeline
```

without productizing persistence, HTTP/query APIs, UI, Feature Store, model
participation, or trading authority.

---

## Why Now

1. Sprint 12 is COMPLETE on authoritative main.
2. Premarket Watchlist, Gap, Catalyst, Scoring, Morning Briefing, Dashboard,
   Human Review, and ADE foundations exist as tested public libraries.
3. Market Data connectors already produce canonical `BarEvent` and `NewsEvent`
   shapes usable as evidence inputs.
4. Backend end-to-end intelligence integration remains low relative to foundation
   maturity; UI and product APIs are blocked until a governed pipeline exists.
5. Expanding into persistence/API/UI before orchestration would encode unstable
   product boundaries.

---

## Planning Principles

1. Planning authorizes repository direction only.
2. Planning never authorizes implementation.
3. Planning never redesigns completed bounded contexts.
4. Planning never modifies frozen Governance or Policy Versions.
5. Planning never changes repository dependency direction.
6. Planning establishes intent only; behavioral specification belongs to later
   approved gates.
7. Deferred classification does not authorize later work.
8. Technology choices shall not redefine repository authority.
9. `PLANNING_APPROVAL ≠ IMPLEMENTATION_AUTHORIZATION`.
10. The intelligence pipeline shall terminate in non-executable intelligence.

A Planning Gate that violates any of these principles is invalid for repository
approval.

---

## In Scope

Planning classifies the following candidate capabilities as **IN SCOPE** for
later Architecture / Governance / Policy / Implementation Authorization under
this theme:

1. Pipeline admission / input contract.
2. Explicit UTC-aware `as_of` owned by the pipeline run.
3. Authorized canonical evidence bundle.
4. Explicit `WatchlistCandidate` input.
5. Canonical `BarEvent` input for Gap.
6. Canonical `NewsEvent` input for Catalyst.
7. Application-layer intelligence orchestration (separate from Market Data
   Orchestrator).
8. Invocation of existing public entrypoints for:
   - Watchlist
   - Gap
   - Catalyst
   - Premarket Score
   - Morning Briefing
   - Dashboard
9. Optional Human Review terminal when explicit caller-supplied human
   attestation is present.
10. Optional ADE terminal only from valid Human Review public output.
11. Deterministic ordered pipeline result.
12. PIT enforcement.
13. Stage-level missing / stale / invalid / ambiguous evidence handling.
14. Fail-closed behavior.
15. Provenance continuity across executed stages.
16. In-process deterministic replay.
17. Pipeline-level freshness metadata sufficient for internal integration.
18. Unit / contract / integration / determinism / temporal / negative /
    replay / authority-firewall tests.
19. Additive Sprint 13 governance / documentation artifacts required by the
    normal governance sequence.

---

## Out of Scope

The following are **OUT OF SCOPE** for Sprint 13 and are not authorized by this
Planning Gate:

- HTTP product APIs
- OpenAPI product routes
- public query API
- UI / frontend implementation
- Premarket Command Center UI
- durable product persistence
- Postgres intelligence repositories
- durable pipeline snapshots
- public read models
- public freshness API
- product authz
- Feature Store expansion
- Feature Platform remediation
- online feature serving
- offline feature persistence
- new feature indicators
- Feature Inspector
- TD-001 calendar remediation
- live provider loops in required CI
- Finnhub product wiring
- FRED product wiring
- SEC product wiring
- model participation
- LLM / provider integration
- AI-generated trade recommendations
- BUY / SELL / HOLD authority
- Strategy mutation
- Risk mutation
- Portfolio mutation
- Order Intent
- OMS mutation
- Broker integration
- live execution
- position / fill management
- tag
- release
- deployment
- VERSION changes
- CHANGELOG release mutation
- Sprint 14 implementation
- Sprint 15 implementation

---

## Integration Boundary

Planning authorizes later Architecture to define a **separate application-layer
intelligence orchestration boundary**.

Intent constraints frozen at Planning fidelity:

- Do **not** extend `MarketDataOrchestrator` into a god object.
- Do **not** reimplement existing domain rules.
- Do **not** bypass public domain entrypoints.
- Do **not** couple orchestration directly to provider SDKs.
- Do **not** couple orchestration to Broker / OMS.
- Do **not** introduce a workflow engine.
- Preferred conceptual form: one bounded application orchestration service
  composed of staged pure / domain calls.

Architecture may refine exact package/module shape without expanding Planning
scope.

### Planning Open Question

| ID | Question | Deferred to |
| --- | --- | --- |
| OQ-13-01 | Exact package/module name and directory for the orchestration boundary | Architecture |

OQ-13-01 is **not** a Planning blocker.

---

## Canonical Evidence Boundary

Authorized minimum evidence for a pipeline run:

| Input | Role |
| --- | --- |
| Explicit UTC `as_of` | Decision clock for the run |
| `WatchlistCandidate` (+ Watchlist config) | Watchlist stage |
| `BarEvent` | Gap stage |
| `NewsEvent` | Catalyst stage |
| Stage configuration / frozen policy versions | Stage behavior |
| Optional human attestation | Human Review terminal |
| Optional valid Human Review public output | ADE terminal |

The orchestrator must **not** fabricate:

- universe candidates
- market bars
- news
- scores
- human attestations
- Human Review approval
- ADE outcomes

Sprint 13 consumes **canonical** evidence, not provider-specific clients inside
the intelligence orchestrator.

Existing providers may be the historical origin of canonical data. Sprint 13
does **not** authorize broad provider productization. Required product wiring
for Finnhub, FRED, and SEC is excluded. Provider SDK calls inside the
intelligence orchestrator are forbidden.

---

## Temporal / PIT Principles

1. A single UTC-aware `as_of` belongs to each pipeline run.
2. All downstream stages receive the same logical `as_of`.
3. No stage may advance the decision clock.
4. Evidence newer than `as_of` must not influence the run.
5. `known_at > as_of` must fail closed.
6. Missing required temporal metadata must fail closed.
7. Ambiguous / conflicting evidence must not be silently selected.
8. Stage-specific stale evidence must be surfaced.
9. No future-data leakage.
10. Replay must preserve the original temporal boundary.

Exact error forms belong to Architecture / Policy.

---

## Determinism Principles

```text
same authorized evidence
+ same UTC as_of
+ same stage configuration
+ same frozen policy versions
→ same ordered pipeline result
```

Where applicable, this includes:

- stage ordering
- identities
- provenance references
- score ordering
- briefing ordering
- dashboard ordering
- Human Review identity
- ADE accept / abstain result

Reuse existing deterministic primitives where possible.
This Planning Gate does **not** authorize a new hashing / identity platform.

---

## Human Review Firewall

| Control | Value |
| --- | --- |
| HUMAN_AUTHORITY_TRANSFER | NO |
| AUTOMATIC_HUMAN_APPROVAL | NO |

The pipeline may prepare Human Review input.
The pipeline may consume a valid Human Review public output.
Human Review may execute only with explicit human attestation supplied through
an authorized boundary.

The pipeline must never:

- generate attestation
- infer human approval
- auto-approve
- bypass Human Review
- convert absence of review into approval

If valid Human Review authority is absent, ADE must not execute.

---

## ADE Firewall

Sprint 12 ADE authority remains frozen.

| Control | Value |
| --- | --- |
| MODEL_PARTICIPATION | UNAUTHORIZED |
| ADE semantics | deterministic governed acceptance / abstention only |

No Planning authority for:

- LLM
- model provider
- agent
- model inference
- trade recommendation
- BUY / SELL / HOLD
- execution

Prefer integration through existing ADE public entrypoints.
Do not authorize ADE semantic redesign.

---

## Trading Firewall

| Control | Value |
| --- | --- |
| BROKER_EXECUTION | DENIED / DEFERRED |
| LIVE_TRADING | UNAUTHORIZED |
| ORDER_INTENT_CREATION | UNAUTHORIZED |
| OMS_MUTATION | UNAUTHORIZED |
| STRATEGY_AUTHORITY_TRANSFER | NO |
| RISK_AUTHORITY_TRANSFER | NO |
| PORTFOLIO_AUTHORITY_TRANSFER | NO |

The Sprint 13 pipeline must terminate in non-executable intelligence.
No pipeline result may directly cause an order.

---

## Feature Platform Boundary

Feature Platform is Sprint 6.

| Control | Value |
| --- | --- |
| FEATURE_PLATFORM_CHANGE_REQUIRED | NO |

Excluded:

- Feature Store
- online serving
- offline feature persistence
- indicator expansion
- strategy parity expansion
- Feature Inspector

Do not force Premarket scoring through Feature Platform merely for
architectural uniformity.

---

## Persistence Boundary

| Control | Value |
| --- | --- |
| SPRINT_13_PRODUCT_PERSISTENCE | NOT AUTHORIZED |

Sprint 13 may use:

- in-process result objects
- deterministic fixtures
- test-only replay capture

Sprint 13 may **not** introduce product persistence.

Deferred to Sprint 14:

- durable intelligence snapshots
- repositories
- Postgres-backed intelligence history
- read models
- public freshness storage

---

## HTTP / Query Boundary

| Control | Value |
| --- | --- |
| SPRINT_13_HTTP_PRODUCT_API | NOT AUTHORIZED |
| SPRINT_13_PUBLIC_QUERY_API | NOT AUTHORIZED |

Internal result contracts required for orchestration may be designed in later
Architecture.

Not authorized:

- new product routes
- OpenAPI product contracts
- frontend clients
- public intelligence query endpoints

These belong to Sprint 14 productization.

---

## Freshness Boundary

Sprint 13 Planning scope **may** include:

- stage-level `known_at` / `as_of` enforcement
- internal pipeline freshness metadata
- explicit missing / stale evidence
- fail-closed stale handling

Sprint 13 must **not** include:

- public freshness API
- UI freshness widgets
- product SLO dashboards

Those remain Sprint 14 / 15 concerns.

---

## Error / Abstention Principles

Fail-closed semantics are required for:

- missing required evidence
- stale evidence
- invalid evidence
- PIT violation
- ambiguous evidence
- stage failure
- invalid Human Review
- missing Human Review before ADE

ADE abstention remains a valid first-class outcome.

No fabricated fallback values.
No silent continuation after authority-invalidating failures.

This Planning Gate does not require a new enterprise error taxonomy.
Architecture / Policy may determine whether a thin pipeline envelope is needed.

---

## Provenance

Enough provenance must exist to trace, when stages execute:

```text
candidate / config
      → Watchlist
      → Gap / Catalyst source evidence
      → Score
      → Briefing
      → Dashboard
      → Human Review
      → ADE
```

Do not authorize a new lineage platform.
Prefer composition of existing stage provenance.

---

## Replay

| Control | Value |
| --- | --- |
| SPRINT_13_REPLAY_REQUIRED | YES |

Scope: in-process deterministic replay of captured authorized evidence.

```text
same evidence
+ same as_of
+ same configuration / policies
→ same pipeline result
```

Excluded:

- historical strategy backtesting platform
- portfolio simulation
- live replay service

---

## TD-001 Decision

| Item | Classification |
| --- | --- |
| TD-001 calendar-aware daily bars | DEFERRED / SOFT DEPENDENCY |

Not required for Sprint 13 integration authorization.

Reason: existing Gap semantics already enforce deterministic two-bar selection
and `known_at <= as_of` with fail-closed ambiguity / missing evidence.

TD-001 may be reconsidered during Sprint 14 or pre-MVP quality work.

---

## Testing Intent

Later Architecture / Implementation Authorization must require coverage for:

- unit admission
- contract boundaries
- integration chain
- determinism
- replay
- PIT / temporal rejection
- fail-closed behavior
- authority firewalls

Representative scenarios shall include:

- happy path
- missing catalyst
- stale bars
- future `known_at`
- stable ordering
- replay equality
- HR absent
- HR invalid
- HR valid
- ADE accept
- ADE abstain

Exact test filenames are not prescribed by Planning.

---

## Provider Testing Boundary

| Control | Value |
| --- | --- |
| LIVE_PROVIDER_CALL_REQUIRED_FOR_CI | NO |

Required CI shall use deterministic canonical real-shaped fixtures.
Live provider smoke may remain OPTIONAL / NOT REQUIRED FOR SPRINT 13 ACCEPTANCE.

Avoid flaky CI and provider-secret dependence.

---

## Dependency / Supply Chain Boundary

| Control | Value |
| --- | --- |
| NEW_DEPENDENCY_REQUIRED | NO (planning expectation) |

Not authorized:

- model SDK
- broker SDK
- workflow engine
- new database
- new message bus

Do not introduce code from:

- AutoHedge
- Vibe-Trading
- Fincept Terminal

Any future use of external architectural ideas requires separate security,
license, supply-chain, and duplication review.

---

## Security Considerations

Later Architecture / Governance must address:

- timestamp spoofing
- provenance spoofing
- unbounded evidence bundles
- provider-secret isolation
- authority leakage
- Human Review bypass
- model leakage
- broker leakage

Discovery expectation under these boundaries:

| Field | Value |
| --- | --- |
| SECURITY_BLOCKERS | 0 |
| SUPPLY_CHAIN_BLOCKERS | 0 |

---

## Candidate Classification

Classification becomes binding after Planning Gate approval.
Every candidate has exactly one classification.
Deferred classification does not authorize later work.

| Candidate | Classification |
| --- | --- |
| Intelligence Pipeline Integration theme | IN SCOPE |
| Pipeline admission / input contract | IN SCOPE |
| Explicit UTC `as_of` ownership | IN SCOPE |
| Canonical `WatchlistCandidate` / `BarEvent` / `NewsEvent` admission | IN SCOPE |
| Application-layer orchestration boundary | IN SCOPE |
| Existing public entrypoint integration through Dashboard | IN SCOPE |
| Optional explicit-HR terminal | IN SCOPE |
| Optional ADE terminal from valid HR only | IN SCOPE |
| PIT / determinism / provenance / in-process replay | IN SCOPE |
| Internal pipeline freshness metadata | IN SCOPE |
| Authority-firewall and integration tests | IN SCOPE |
| Additive Sprint 13 governance documentation sequence | IN SCOPE |
| Durable product persistence / repositories / read models | DEFERRED (Sprint 14) |
| HTTP / public query / OpenAPI productization | DEFERRED (Sprint 14) |
| Public freshness API / product authz | DEFERRED (Sprint 14) |
| Premarket Command Center UI | DEFERRED (Sprint 15) |
| TD-001 calendar remediation | DEFERRED |
| Feature Platform / Feature Store expansion | OUT OF SCOPE |
| Model participation / LLM / providers | OUT OF SCOPE |
| Broker / OMS / Order Intent / live execution | OUT OF SCOPE |
| Tag / release / deploy / VERSION / CHANGELOG release mutation | OUT OF SCOPE |

---

## Deliverable Classes

Future deliverable classes (non-authorizing listing only):

| ID | Class |
| --- | --- |
| D1 | Pipeline admission / input contract |
| D2 | Application orchestration boundary |
| D3 | Existing-stage integration: Watchlist → Gap → Catalyst → Score → Briefing → Dashboard |
| D4 | Optional explicit-HR → ADE terminal integration |
| D5 | PIT / determinism / provenance / replay behavior |
| D6 | Authority-firewall and integration test coverage |
| D7 | Additive Sprint 13 governance / documentation artifacts |

Listing deliverables does **not** authorize code.

---

## Deferred Capabilities

Deferred beyond Sprint 13 Planning authority:

- Sprint 14 productization: persistence, repositories, read models, versioned
  HTTP/query API, public freshness, product authz
- Sprint 15 read-only Premarket Command Center UI
- TD-001
- Feature Platform remediation
- paper-trading product loop expansion
- live trading / Broker Execution

Deferred classification does not authorize later work.

---

## Sprint 13 → Sprint 14 → Sprint 15 Boundary

| Sprint | Theme | Authorized by this Planning Gate? |
| --- | --- | --- |
| 13 | Intelligence Pipeline Integration | Theme/scope only (when APPROVED) |
| 14 | Persistence + repositories + read models + versioned HTTP/query API + public freshness + product authz | NO |
| 15 | Read-only Premarket Command Center UI | NO |

| Control | Value |
| --- | --- |
| UI_AFTER_SPRINT_13 | NOT AUTHORIZED |

Sprint 13 must not consume Sprint 14 / 15 scope.

### Future non-authorizing UI entry expectations

These are future planning dependencies only. They do **not** authorize UI work.

| ID | Expectation |
| --- | --- |
| UI-ENTRY-01 | Versioned read contracts |
| UI-ENTRY-02 | Durable intelligence snapshot |
| UI-ENTRY-03 | Freshness query |
| UI-ENTRY-04 | Provenance query |
| UI-ENTRY-05 | HR query / action boundary |
| UI-ENTRY-06 | ADE outcome query |
| UI-ENTRY-07 | Stable error / abstention semantics |
| UI-ENTRY-08 | Authz boundary |
| UI-ENTRY-09 | Representative integration fixtures / tests |

---

## Frozen Predecessors

Sprint 13 Planning is **additive**. Predecessor authority must not be rewritten.

At minimum frozen:

- Sprint 12 Planning Gate (`sprint-12.planning-gate`)
- AI Decision Engine Architecture v1
- AI Decision Engine Governance Decisions #1–#8
- AI Decision Engine Policy Version `ai-decision-engine.policy.v1`
- AI Decision Engine Implementation Authorization v1
- Sprint 12 CLOSEOUT

Also frozen / ownership-preserving:

- Premarket Intelligence foundations (Watchlist / Catalyst / Gap)
- Premarket Scoring Architecture / Governance / Policy
- Morning Briefing Architecture / Governance / Policy / Impl Auth
- Dashboard Architecture / Governance / Policy / Impl Auth
- Human Review Architecture / Governance / Policy / Impl Auth
- Feature Platform Sprint 6 exclusions
- Sprint 4 Trading Foundations ownership boundaries

---

## Planning Acceptance Criteria

| ID | Criterion |
| --- | --- |
| AC-01 | Sprint 13 problem and objective are bounded to Intelligence Pipeline Integration. |
| AC-02 | Pipeline run owns one explicit UTC-aware `as_of`. |
| AC-03 | Canonical evidence boundary is limited to authorized inputs and existing public domain contracts. |
| AC-04 | Planning scope covers deterministic orchestration of existing Premarket stages without reimplementing their domain semantics. |
| AC-05 | PIT / future-data leakage prevention is mandatory and fail-closed. |
| AC-06 | Human Review authority remains explicit; no automatic attestation or approval. |
| AC-07 | ADE remains deterministic accept / abstain; MODEL PARTICIPATION remains UNAUTHORIZED. |
| AC-08 | Trading authority is not transferred; Broker / OMS / Order Intent / execution remain unauthorized. |
| AC-09 | Provenance and deterministic in-process replay are required planning properties. |
| AC-10 | No product persistence, HTTP / query API, or UI is authorized in Sprint 13. |
| AC-11 | Feature Platform remediation and TD-001 are not required Sprint 13 scope. |
| AC-12 | No new dependency is expected; live provider calls are not required CI. |
| AC-13 | Planning approval does not authorize Architecture / Governance / Policy / Implementation beyond opening the documentation-only Architecture Gate; subsequent gate sequence remains mandatory. |

---

## Non-Authorizing Future Issue Structure Recommendation

After the full gate sequence is APPROVED — and only then — expected
implementation decomposition:

1. Implementation Issue 1 — Pipeline admission + PIT boundary + orchestration skeleton
2. Implementation Issue 2 — Existing stage wiring through Dashboard + optional explicit HR / ADE terminal
3. Implementation Issue 3 — Determinism / replay / provenance / authority firewall test pack
4. Status-sync / closeout as required by repository precedent

This section does **not** create issues and does **not** authorize implementation.

---

## Risks

| Risk | Mitigation |
| --- | --- |
| Scope expands into Sprint 14 persistence / HTTP | Explicit OUT OF SCOPE and Sprint boundary table |
| Scope expands into UI | UI_AFTER_SPRINT_13 = NOT AUTHORIZED |
| Auto-attestation / HR bypass | Human Review firewall |
| Model leakage via “AI” naming | MODEL PARTICIPATION = UNAUTHORIZED |
| Broker / OMS coupling | Trading firewall |
| MarketDataOrchestrator god-object | Separate application orchestration boundary |
| Provider SDK coupling | Canonical evidence only |
| Feature Platform forced unification | FEATURE_PLATFORM_CHANGE_REQUIRED = NO |
| New dependency creep | NEW_DEPENDENCY_REQUIRED = NO |

---

## Planning Gate Decision

**DRAFT / NOT YET APPROVED.**

When this Planning Gate is APPROVED by repository process:

- Sprint 13 theme = Intelligence Pipeline Integration
- Scope classifications in this document become binding
- Documentation-only Architecture Gate may begin
- Implementation remains DENIED until Implementation Authorization is APPROVED

---

## Next Authorized Step

If and only if this Planning Gate becomes APPROVED:

```text
Next authorized step = Architecture Gate (documentation-only)
```

Not authorized by Planning approval alone:

- Governance Decisions
- Policy Freeze
- Implementation Authorization
- Implementation
- UI
- tag / release / deploy

---

## Explicit Non-Authorization Statement

This Planning Gate does **not** authorize:

- implementation code
- HTTP product APIs
- UI
- durable product persistence
- Feature Platform remediation
- model participation
- Broker Execution
- Order Intent / OMS mutation
- live trading
- tag / release / deployment
- VERSION / CHANGELOG release mutation
- Sprint 14 or Sprint 15 work

```text
PLANNING_APPROVAL ≠ IMPLEMENTATION_AUTHORIZATION
SPRINT_COMPLETE ≠ CAPABILITY_AUTHORIZATION
UI_AUTHORIZED = NO
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED / DEFERRED
```

---

## Conclusion

Sprint 13 Planning proposes **Intelligence Pipeline Integration** as the
smallest correct next theme after Sprint 12 closeout: governed in-process
orchestration of existing fail-closed intelligence libraries under a single UTC
`as_of`, without productizing persistence, APIs, UI, Feature Store, models, or
trading.

This document remains **DRAFT / NOT YET APPROVED** until repository approval.
