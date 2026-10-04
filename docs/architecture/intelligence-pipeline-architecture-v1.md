# Intelligence Pipeline Architecture v1

**Architecture ID:** `intelligence-pipeline.architecture.v1`
**Version:** v1
**Bounded context:** Intelligence Pipeline
**Status:** DRAFT / NOT YET APPROVED
**Document class:** Architecture only
**Sprint:** 13
**Theme:** Intelligence Pipeline Integration
**Prerequisite Planning Gate:** `sprint-13.planning-gate` (APPROVED / EFFECTIVE)
**Architecture issue:** [#118](https://github.com/enesdedelerr-max/Bergama/issues/118)
**Authoritative Planning baseline:** `c8d1d03482478236aecf5ab5ac02f85b38606beb`

This document defines architecture only: structure, ownership, dependency
direction, orchestration topology, temporal / PIT behavior, provenance,
replay boundary, failure topology, and optional Human Review / ADE terminal
composition for Sprint 13 Intelligence Pipeline Integration.

It does **not** authorize:

- Governance
- Policy
- Implementation Authorization
- Implementation
- runtime code
- database schemas
- migrations
- persistence
- HTTP product APIs
- UI
- Feature Platform changes
- model participation
- Broker
- OMS
- Order Intent
- live trading
- tag
- release
- deployment

```text
ARCHITECTURE APPROVAL ≠ GOVERNANCE / POLICY / IMPLEMENTATION AUTHORIZATION
ARCHITECTURE APPROVAL ≠ IMPLEMENTATION
```

| Control | Value |
| --- | --- |
| MODEL_PARTICIPATION | UNAUTHORIZED |
| BROKER_EXECUTION | DENIED / DEFERRED |
| IMPLEMENTATION_AUTHORIZATION | DENIED |
| UI_AUTHORIZED | NO |
| SPRINT_13_PRODUCT_PERSISTENCE | NOT AUTHORIZED |
| SPRINT_13_HTTP_PRODUCT_API | NOT AUTHORIZED |
| FEATURE_PLATFORM_CHANGE_REQUIRED | NO |

Upstream frozen foundations remain ownership boundaries and shall not be
redesigned by this Architecture:

- Premarket Watchlist / Gap / Catalyst foundations
- Premarket Scoring Architecture / Governance / Policy
- Morning Briefing Architecture / Governance / Policy
- Dashboard Architecture / Governance / Policy
- Human Review Architecture / Governance / Policy
- AI Decision Engine Architecture / Governance / Policy
- Sprint 6 Feature Platform exclusions
- Sprint 4 Trading Foundations ownership

---

## Status

| Field | Value |
| --- | --- |
| Architecture status | DRAFT / NOT YET APPROVED |
| Architecture approved | No |
| Approves Governance Decisions | No |
| Approves Policy Freeze | No |
| Approves Implementation Authorization | No |
| Approves Implementation | No |
| Next mandatory gate after Architecture approval | Governance Gate |

Until this Architecture is APPROVED through repository process, Governance
remains blocked. Until Implementation Authorization is APPROVED, no Sprint 13
implementation issue, branch, or pull request may claim implementation
authority.

---

## Problem Statement

Existing intelligence capabilities are implemented as independent in-process
bounded engines with public contracts and deterministic / PIT controls.

Current chain:

```text
Watchlist
      → Gap
      → Catalyst
      → Premarket Score
      → Morning Briefing
      → Dashboard
      → Human Review
      → AI Decision Engine
```

There is no governed application-layer intelligence pipeline that composes
these engines under one run boundary and one UTC-aware `as_of`.

Sprint 13 Architecture defines that missing composition boundary.

This is an integration / orchestration architecture problem. It is **not**:

- a UI problem
- an HTTP API problem
- a Feature Store problem
- a broker problem
- a model problem

---

## OQ-13-01 — Resolved by Architecture

**Planning open question:** Exact package/module name and directory for the
orchestration boundary.

**Architecture decision (AD-13-01):**

| Field | Value |
| --- | --- |
| Preferred future package | `apps/api/app/intelligence_pipeline/` |
| Classification | Application-layer orchestration / composer |
| Placement | Sibling bounded context under `apps/api/app/` |
| Status | **RESOLVED BY ARCHITECTURE** |

The package must **not** be placed inside:

- `market_data/orchestrator`
- `premarket/watchlist`
- `premarket/gap`
- `premarket/catalyst`
- `premarket/scoring`
- `premarket/morning_briefing`
- `dashboard`
- `human_review`
- `ai_decision_engine`
- `features`
- `broker`
- `orders` / OMS

**Reason:**

- No individual intelligence stage owns the pipeline.
- `MarketDataOrchestrator` owns market-data admission / publish behavior, not
  intelligence composition.
- The pipeline must depend on existing public stage contracts; stages must
  not depend on the pipeline.

This Architecture does **not** create the package. Implementation remains
DENIED.

---

## Existing Public Contracts (Compose, Do Not Redesign)

Architecture composes existing public entrypoints. Stage semantics remain
owned by their frozen bounded contexts.

### Watchlist

| Field | Value |
| --- | --- |
| Path | `apps/api/app/premarket/watchlist` |
| Entrypoints | `generate_watchlist`, `generate_watchlist_from_parts` |
| Conceptual inputs | `WatchlistCandidate` sequence, UTC `as_of`, Watchlist config |
| Conceptual output | `Watchlist` |

### Gap

| Field | Value |
| --- | --- |
| Path | `apps/api/app/premarket/gap` |
| Entrypoints | `scan_gaps`, `scan_gaps_from_parts` |
| Conceptual inputs | `Watchlist`, `BarEvent` sequence, UTC `as_of`, Gap config |
| Conceptual output | `GapCollection` |
| PIT note | Existing stage enforces `known_at <= as_of` |

### Catalyst

| Field | Value |
| --- | --- |
| Path | `apps/api/app/premarket/catalyst` |
| Entrypoints | `normalize_catalysts`, `normalize_catalysts_from_parts` |
| Conceptual inputs | `NewsEvent` sequence, UTC `as_of`, Catalyst config |
| Conceptual output | `CatalystCollection` |

### Premarket Score

| Field | Value |
| --- | --- |
| Path | `apps/api/app/premarket/scoring` |
| Entrypoints | `scan_scores`, `scan_scores_from_parts` |
| Conceptual inputs | `Watchlist`, optional authorized Gap / Catalyst evidence, UTC `as_of`, Score config |
| Conceptual output | `ScoreCollection` |

### Morning Briefing

| Field | Value |
| --- | --- |
| Path | `apps/api/app/premarket/morning_briefing` |
| Entrypoints | `assemble_briefing`, `assemble_briefing_from_parts` |
| Conceptual inputs | `ScoreCollection`, UTC `as_of`, Briefing config |
| Conceptual output | `BriefingCollection` |

### Dashboard

| Field | Value |
| --- | --- |
| Path | `apps/api/app/dashboard` |
| Entrypoints | `assemble_dashboard`, `assemble_dashboard_from_parts` |
| Conceptual inputs | `BriefingCollection`, UTC `as_of`, Dashboard config |
| Conceptual output | `DashboardPresentationOutput` |

### Human Review

| Field | Value |
| --- | --- |
| Path | `apps/api/app/human_review` |
| Entrypoints | `assemble_human_review`, `assemble_human_review_from_parts` |
| Conceptual inputs | Dashboard evidence, UTC `as_of`, **explicit attestation**, HR config |
| Conceptual output | `HumanReviewOutput` |

### AI Decision Engine

| Field | Value |
| --- | --- |
| Path | `apps/api/app/ai_decision_engine` |
| Entrypoints | `evaluate_ade`, `evaluate_ade_from_parts` |
| Conceptual inputs | Valid authorized Human Review evidence, UTC `as_of`, ADE config |
| Conceptual output | `AdeResult` (accept / abstain) |

---

## Dependency Direction

Legal conceptual direction:

```text
Canonical Market Data Evidence
            ↓
    Intelligence Pipeline
            ↓
 Existing Stage Public Contracts
```

Stage flow:

```text
Watchlist
   ↓
Gap ─────────┐
             │
Catalyst ────┼→ Premarket Score
             │
Watchlist ───┘
                  ↓
          Morning Briefing
                  ↓
              Dashboard
                  ↓
          [optional explicit HR]
                  ↓
             [optional ADE]
```

Rules:

1. Intelligence Pipeline may depend on public contracts of these stages.
2. Existing stages must **not** depend on Intelligence Pipeline.
3. Human Review and ADE remain terminal consumers.
4. No circular imports.
5. No dependency on Broker, OMS, Order Intent, Feature Platform, or model SDKs.

---

## Pipeline Run Boundary

One logical pipeline run owns:

- one UTC-aware `as_of`
- canonical admitted evidence
- configuration / policy references
- deterministic stage ordering
- stage results / status
- provenance references
- internal freshness metadata
- optional explicit Human Review attestation / evidence
- optional ADE result

Architecture-level conceptual integration contracts (names are conceptual;
exact Python class names are not frozen by this document unless later
Implementation Authorization requires them):

| Concept | Responsibility |
| --- | --- |
| PipelineRequest | Admit run inputs: `as_of`, evidence bundle, configs, optional HR attestation |
| PipelineResult | Ordered stage outcomes, statuses, provenance refs, freshness metadata, optional HR/ADE |
| StageResult / StageStatus | Per-stage outcome representation without transferring stage authority |
| FreshnessMetadata | Internal in-process freshness summary (not a public product API) |
| Replay input / capture reference | In-process deterministic re-invocation handle |

These are Architecture fidelity concepts. They do **not** create schemas,
modules, or code.

---

## Canonical Input Evidence

Reuse existing canonical evidence types where possible:

- `WatchlistCandidate`
- `BarEvent`
- `NewsEvent`

plus existing stage configuration / policy references.

Rules:

- Do not introduce provider-native payloads into the pipeline.
- Provider normalization remains upstream.
- The pipeline consumes canonical evidence only.
- No provider SDK belongs inside the intelligence pipeline.

---

## Single `as_of` Contract

Architecture invariant:

1. One pipeline run owns exactly one UTC-aware `as_of`.
2. The same `as_of` must be propagated to every invoked stage.
3. No stage may silently advance to wall-clock time.
4. No downstream stage may choose a newer temporal boundary.
5. Replay must use the original `as_of`.

---

## PIT / `known_at` Contract

Architecture preserves point-in-time correctness:

- `known_at <= as_of`
- future evidence fails closed
- missing required temporal metadata fails closed
- ambiguous evidence is not silently selected
- stale evidence is surfaced
- no future-data leakage
- replay preserves the original temporal boundary

Existing stage PIT validation should be reused. Pipeline admission validates
the cross-stage run boundary without unnecessarily duplicating domain-specific
checks already owned by stages (for example Gap `known_at` enforcement).

---

## Stage Invocation Topology

Deterministic orchestration topology:

1. Admit PipelineRequest / canonical evidence.
2. Validate run-level `as_of` and evidence temporal admissibility.
3. Generate / accept Watchlist according to existing public contract.
4. Run Gap from Watchlist + authorized `BarEvent` evidence.
5. Normalize Catalyst evidence from authorized `NewsEvent` evidence.
6. Run Premarket Score using Watchlist and authorized optional evidence.
7. Assemble Morning Briefing.
8. Assemble Dashboard.
9. Stop with non-executable intelligence by default.
10. If and only if explicit valid Human Review authority / evidence exists,
    optionally assemble Human Review.
11. If and only if valid authorized Human Review output exists, optionally
    evaluate ADE.
12. Return PipelineResult.

No broker / execution stage exists.

---

## Failure / Termination Architecture

Architecture defines structural failure representation, not business-policy
wording.

Conceptual distinctions:

| Class | Meaning |
| --- | --- |
| Run admission failure | Request / temporal / evidence admission rejected before stages |
| Stage failure | Invoked stage fails closed under its existing contract |
| Valid stage absence | Optional terminal (HR/ADE) not requested |
| Valid partial / non-terminal evidence absence | Structure allows representation; exact business rule deferred |
| Valid abstention | ADE abstention as first-class terminal outcome |
| Terminal completion | PipelineResult returned without executable authority |

Deferred to Governance / Policy where not already frozen:

- whether missing catalyst evidence is hard-stop vs valid optional-empty
- exact reason taxonomy wording
- policy thresholds
- weighting / scoring semantics (already frozen upstream; not reopened)

No fabricated evidence.
No silent fallback to unauthorized data.

---

## Human Review Boundary

Human Review is **OPTIONAL** and **EXPLICIT**.

- Pipeline may complete at Dashboard without Human Review.
- Human Review may only be invoked when required explicit attestation and
  authorized evidence are present.

| Control | Value |
| --- | --- |
| HUMAN_AUTHORITY_TRANSFER | NO |
| AUTOMATIC_HUMAN_APPROVAL | NO |

Forbidden:

- inferred approval
- synthetic attestation
- automatic conversion of Dashboard output into human approval

---

## ADE Boundary

ADE is an optional terminal stage.

- ADE may only be invoked from valid authorized Human Review output.
- Missing or invalid HR → ADE **NOT INVOKED**.

ADE remains:

- deterministic
- governed
- accept / abstain

ADE does **not** become:

- a model
- an LLM
- an autonomous agent
- a BUY / SELL / HOLD engine
- an execution engine

| Control | Value |
| --- | --- |
| MODEL_PARTICIPATION | UNAUTHORIZED |

---

## Trading Firewall

The pipeline terminates in **non-executable intelligence**.

Forbidden dependencies / capabilities:

- Broker
- OMS
- Order Intent
- order placement
- order mutation
- execution
- live trading
- portfolio mutation

| Control | Value |
| --- | --- |
| BROKER_EXECUTION | DENIED / DEFERRED |
| LIVE_TRADING | UNAUTHORIZED |
| ORDER_INTENT_CREATION | UNAUTHORIZED |
| OMS_MUTATION | UNAUTHORIZED |
| STRATEGY_AUTHORITY_TRANSFER | NO |
| RISK_AUTHORITY_TRANSFER | NO |
| PORTFOLIO_AUTHORITY_TRANSFER | NO |

No pipeline result may directly cause an order.

---

## Persistence Firewall

Sprint 13 Architecture is **in-process only**.

Do **not** architect Sprint 14 persistence:

- new Postgres intelligence repository
- durable pipeline snapshots
- durable read models
- new database schema
- migration
- Redis serving
- Feature Store persistence

In-process replay / capture concepts are allowed.
Durable productization remains Sprint 14.

| Control | Value |
| --- | --- |
| SPRINT_13_PRODUCT_PERSISTENCE | NOT AUTHORIZED |

---

## HTTP / Query Firewall

Do **not** define product HTTP / API architecture in Sprint 13.

Forbidden:

- FastAPI product route
- REST contract
- OpenAPI product DTO
- query service
- public freshness endpoint

These belong to Sprint 14.
Internal in-process request / result contracts are allowed.

| Control | Value |
| --- | --- |
| SPRINT_13_HTTP_PRODUCT_API | NOT AUTHORIZED |

---

## UI Firewall

No frontend / UI architecture.
No Premarket Command Center implementation / design.
No UI API tailoring.

Sprint 15 remains:

```text
Read-only Premarket Command Center UI
```

after a stable Sprint 14 query boundary.

| Control | Value |
| --- | --- |
| UI_AUTHORIZED | NO |
| UI_AFTER_SPRINT_13 | NOT AUTHORIZED |

---

## Feature Platform Firewall

| Control | Value |
| --- | --- |
| FEATURE_PLATFORM_CHANGE_REQUIRED | NO |

Do not route Premarket Score through Feature Platform merely for uniformity.

No:

- Feature Store
- online feature serving
- offline feature persistence
- new feature calculators
- Feature Inspector
- Sprint 6 remediation

TD-001 remains deferred / soft dependency.

---

## Provider / Supply-Chain Firewall

Pipeline consumes canonical evidence only.

No:

- live provider SDK inside orchestration
- new required dependency
- workflow engine
- new DB
- new message bus
- model SDK
- broker SDK
- code / dependency adoption from AutoHedge, Vibe-Trading, or Fincept Terminal

| Control | Value |
| --- | --- |
| NEW_DEPENDENCY_REQUIRED | NO |
| LIVE_PROVIDER_CALL_REQUIRED_FOR_CI | NO |

---

## Provenance Architecture

Compose existing stage provenance rather than replace it.

PipelineResult should preserve references to stage evidence / results.

- Do not create a new lineage platform.
- Do not transfer authority through provenance.
- Provenance proves lineage / context, not authorization.

---

## Replay Architecture

| Control | Value |
| --- | --- |
| SPRINT_13_REPLAY_REQUIRED | YES |

Replay is in-process deterministic re-invocation using:

- original canonical evidence
- original `as_of`
- original relevant configuration / policy references

Replay must **not**:

- fetch newer evidence
- use wall-clock advancement
- call live providers
- mutate durable state
- execute trades

Do not create a backtesting platform.

---

## Freshness Architecture

Internal freshness metadata may be part of PipelineResult.
It may summarize stage / evidence freshness for downstream in-process
consumers.

Do not turn this into the public freshness / query contract.
Public product freshness belongs to Sprint 14.

---

## Determinism

Architecture requires deterministic behavior for identical:

- canonical evidence
- `as_of`
- configuration / policy references
- explicit human input (when HR/ADE terminals are used)

Deterministic ordering must be respected where collections could otherwise
produce unstable results (reuse existing stage ordering policies).
Replay equality must be testable.

---

## Configuration / Policy References

Pipeline must consume existing authorized stage configuration / policy
references.

Architecture must **not** reopen frozen scoring / decision policy semantics.

Pipeline may validate that required configuration context exists.
Exact governance rules and error / reason taxonomy remain for later gates
where not already frozen.

---

## Security Architecture

Bounded controls (not a new security platform):

- timestamp spoofing
- provenance spoofing
- future evidence leakage
- unbounded evidence bundles
- provider-secret leakage
- Human Review bypass
- synthetic approval
- model authority leakage
- broker / execution leakage

Architecture uses bounded inputs and existing validation boundaries.

| Field | Value |
| --- | --- |
| SECURITY_ARCHITECTURE_BLOCKERS | 0 |
| SUPPLY_CHAIN_BLOCKERS | 0 |

---

## Test Architecture

Future test seams only (no tests created by this Architecture document):

| Layer | Seams |
| --- | --- |
| Unit | Run admission, `as_of` validation, deterministic ordering, stage result envelope |
| Contract | Forbidden imports, public stage boundary composition, authority firewalls |
| Integration | Watchlist → Gap / Catalyst → Score → Briefing → Dashboard |
| Integration (optional) | Dashboard → HR → ADE |
| Negative | Future evidence, missing temporal metadata, invalid HR, missing HR, ADE abstention, forbidden dependency, model / broker leakage |
| Replay | Same evidence + same `as_of` → same governed result |

No live provider CI.

---

## Architecture Decisions

| ID | Decision |
| --- | --- |
| AD-13-01 | Dedicated application-layer Intelligence Pipeline bounded context at `apps/api/app/intelligence_pipeline/` (future implementation path; not created by this document). |
| AD-13-02 | Existing stage public APIs are composed, not redesigned. |
| AD-13-03 | Single pipeline-owned UTC-aware `as_of`. |
| AD-13-04 | Canonical evidence only at pipeline boundary. |
| AD-13-05 | Deterministic stage topology as defined above. |
| AD-13-06 | In-process replay; no durable productization. |
| AD-13-07 | Human Review optional and explicit. |
| AD-13-08 | ADE optional and HR-gated. |
| AD-13-09 | Pipeline terminates in non-executable intelligence. |
| AD-13-10 | Persistence / HTTP / UI deferred to Sprint 14 / 15. |
| AD-13-11 | Feature Platform unchanged. |
| AD-13-12 | No new dependency / provider / model / broker SDK required. |

---

## Deferred Decisions

Explicitly deferred:

- exact business failure policy where not already frozen
- exact error / reason taxonomy
- optional catalyst hard-stop vs optional-empty semantics
- Governance control wording
- Policy freeze details
- Implementation package internals below Architecture fidelity
- persistence schemas
- repository interfaces
- HTTP / query API
- public freshness contract
- UI
- model participation
- Broker / OMS / execution

---

## Sprint 13 → Sprint 14 → Sprint 15 Boundary

| Sprint | Theme | Authorized by this Architecture? |
| --- | --- | --- |
| 13 | Intelligence Pipeline Integration | Architecture scope only (when APPROVED) |
| 14 | Persistence + repositories + read models + versioned HTTP/query API + public freshness + product authz | NO |
| 15 | Read-only Premarket Command Center UI | NO |

---

## Acceptance Criteria

| ID | Criterion |
| --- | --- |
| AC-01 | Architecture remains bounded to approved Sprint 13 Planning theme. |
| AC-02 | OQ-13-01 resolved to a dedicated application-layer intelligence pipeline boundary. |
| AC-03 | Existing stage public contracts are composed, not redesigned. |
| AC-04 | Single UTC-aware `as_of` ownership and propagation defined. |
| AC-05 | PIT / `known_at` fail-closed architecture defined. |
| AC-06 | Deterministic stage invocation topology defined. |
| AC-07 | Pipeline request / result and stage envelope responsibilities defined at Architecture fidelity. |
| AC-08 | Provenance composition defined without authority transfer. |
| AC-09 | In-process deterministic replay boundary defined. |
| AC-10 | Human Review remains optional, explicit, and non-automatic. |
| AC-11 | ADE remains optional, HR-gated, deterministic accept / abstain. |
| AC-12 | Trading / Broker / OMS / Order Intent firewalls preserved. |
| AC-13 | Persistence / HTTP / UI remain deferred to Sprint 14 / 15. |
| AC-14 | Feature Platform changes remain unnecessary. |
| AC-15 | No model participation or new dependency is authorized / required. |
| AC-16 | Security architecture addresses temporal / provenance / authority leakage without new platform scope. |
| AC-17 | Test seams are defined without live-provider CI. |
| AC-18 | Architecture approval does not authorize Governance / Policy / Implementation. |

---

## Explicit Non-Authorization Statement

This Architecture document, even when APPROVED, does **not** authorize:

- Governance Decisions
- Policy Freeze
- Implementation Authorization
- Implementation code
- `apps/api/app/intelligence_pipeline/` package creation without Implementation Authorization
- product persistence
- HTTP product APIs
- UI
- Feature Platform changes
- model participation
- Broker / OMS / Order Intent / live trading
- tag / release / deployment

```text
ARCHITECTURE APPROVAL ≠ GOVERNANCE / POLICY / IMPLEMENTATION AUTHORIZATION
IMPLEMENTATION_AUTHORIZATION = DENIED
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED / DEFERRED
UI_AUTHORIZED = NO
```

---

## Conclusion

Intelligence Pipeline Architecture v1 defines the missing application-layer
composition boundary for Sprint 13: a dedicated `intelligence_pipeline`
orchestrator that admits canonical evidence under one UTC `as_of`, invokes
existing public stage contracts in deterministic order, optionally terminates
at explicit Human Review and HR-gated ADE accept / abstain, and remains
non-executable, in-process, and free of Feature Platform / HTTP / UI /
persistence productization.

This document remains **DRAFT / NOT YET APPROVED** until repository Architecture
approval process completes.
