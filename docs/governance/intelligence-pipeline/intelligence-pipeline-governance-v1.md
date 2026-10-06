# Intelligence Pipeline Governance v1

**Governance ID:** `intelligence-pipeline.governance.v1`
**Version:** v1
**Title:** Intelligence Pipeline Governance v1
**Status:** APPROVED / EFFECTIVE
**Document class:** Composition Governance
**Sprint:** 13
**Theme:** Intelligence Pipeline Integration
**Bounded context:** Intelligence Pipeline (application-layer composer)
**Architectural package path (not created by this document):** `apps/api/app/intelligence_pipeline/`
**Governance issue:** [#120](https://github.com/enesdedelerr-max/Bergama/issues/120)
**Authoritative Architecture baseline:** `intelligence-pipeline.architecture.v1`
**Authoritative Planning baseline:** `sprint-13.planning-gate`

```text
GOVERNANCE APPROVAL ≠ POLICY / IMPLEMENTATION AUTHORIZATION
GOVERNANCE APPROVAL ≠ IMPLEMENTATION
IMPLEMENTATION_AUTHORIZATION = AUTHORIZED (by separate Implementation Authorization; not by this Governance Decision)
IMPLEMENTATION_WORK_STARTED = YES
IMPLEMENTATION_SEQUENCE = 3/3 COMPLETE
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED / DEFERRED
```

---

## Prerequisites

| Prerequisite | Process state |
| --- | --- |
| `sprint-13.planning-gate` | APPROVED / EFFECTIVE |
| `intelligence-pipeline.architecture.v1` | APPROVED / EFFECTIVE |

This Governance Decision is subordinate to those prerequisites. It does not
modify Planning or Architecture bodies.

---

## Status

| Field | Value |
| --- | --- |
| Governance status | APPROVED / EFFECTIVE |
| Governance approved | Yes |
| Approves Policy Freeze | No |
| Approves Implementation Authorization | No |
| Approves Implementation | No |
| Policy authorization | APPROVED / FROZEN (separate Policy Freeze #122 / PR #123) |
| Implementation authorization | AUTHORIZED (separate Implementation Authorization #124 / PR #125) |
| Implementation work | COMPLETE (Issues #126 / #128 / #130) |
| Sprint 13 governance closeout | NOT COMPLETE |
| Next mandatory process step | Separate Sprint 13 governance closeout |

This Governance Decision is **APPROVED / EFFECTIVE** (#120 / PR #121).
Governance approval alone does not authorize Implementation.

---

## Purpose

Freeze composition-level authority and mandatory governance boundaries for
Sprint 13 Intelligence Pipeline Integration.

This document governs how existing public stage contracts may be composed under
one pipeline run boundary. It does not redefine stage semantics.

---

## Ownership

This Governance Decision owns only:

- pipeline composition semantic boundary
- pipeline admission governance
- run-level temporal / PIT governance
- composition topology authority
- structural failure / valid-absence / abstention boundaries
- composition provenance
- composition determinism
- composition replay obligations
- Human Review invocation boundary
- ADE invocation boundary
- model firewall
- trading / execution firewall
- productization firewall
- Feature Platform firewall
- provider / supply-chain firewall
- composition-level security
- in-process auditability obligations

---

## Explicit Non-Ownership

This Governance Decision does **not** own:

- Watchlist semantics
- Gap semantics
- Catalyst semantics
- Score meaning
- score weights
- score formulas
- Morning Briefing semantics
- Dashboard semantics
- Human Review semantics
- ADE decision semantics
- stage-local PIT rules
- stage-local provenance meaning
- business scoring thresholds
- optional catalyst exact continuation matrix
- exact pipeline error / reason taxonomy
- numeric freshness / staleness thresholds
- provider configuration
- durable persistence
- database schemas
- read models
- HTTP APIs
- OpenAPI DTOs
- public freshness API
- UI
- Premarket Command Center
- Feature Platform remediation
- Feature Store design
- Broker implementation
- OMS implementation
- Order Intent implementation
- Strategy authority
- Risk authority
- Portfolio authority

---

## Referenced Existing Governance (Do Not Modify)

This Decision references and remains subordinate to the following authoritative
bodies. It does not duplicate their decision bodies, reopen them, or reinterpret
their authority.

| Set | Location |
| --- | --- |
| Premarket Scoring Governance Decisions #1–#12 | `docs/governance/` |
| Morning Briefing Governance Decisions #1–#8 | `docs/governance/morning-briefing/` |
| Dashboard Governance Decisions #1–#8 | `docs/governance/dashboard/` |
| Human Review Governance Decisions #1–#8 | `docs/governance/human-review/` |
| AI Decision Engine Governance Decisions #1–#8 | `docs/governance/ai-decision-engine/` |
| Trading Foundations ownership | Sprint 4 frozen ownership |
| Existing approved / frozen stage Policy Versions | `docs/policy/` and stage policy bindings |

Stage bounded contexts retain semantic ownership of their public contracts and
governance meaning.

---

## 1. Pipeline Composition Semantic Boundary

The Intelligence Pipeline is an application-layer composition / orchestration
bounded context.

It may:

- admit a governed pipeline request
- invoke existing public stage contracts in governed order
- assemble a non-executable composition result
- optionally invoke Human Review and ADE under existing governance

It may not:

- own or redefine stage semantics
- acquire Human Review authority
- acquire ADE authority
- acquire Broker / OMS / Order Intent / Strategy / Risk / Portfolio authority
- introduce model participation
- productize persistence, HTTP, or UI under Sprint 13

Architectural package path (future implementation only; not created here):

```text
apps/api/app/intelligence_pipeline/
```

---

## 2. Pipeline Admission Governance

Composition-level admission principles:

1. Pipeline execution requires an explicit governed request.
2. Only canonical admitted evidence may enter the governed pipeline.
3. Provider-native payloads are not pipeline evidence.
4. A run owns exactly one UTC-aware `as_of`.
5. Required temporal metadata must be present.
6. Future evidence relative to run `as_of` is inadmissible.
7. Ambiguous evidence is inadmissible.
8. Unsupported evidence is inadmissible.
9. Invalid evidence is inadmissible.
10. Evidence admission must be bounded.
11. Pipeline must fail closed when required admission cannot be established.
12. Pipeline must not fabricate missing evidence.

This Decision does not define exact implementation exception classes.
This Decision does not define exact Policy reason codes.

---

## 3. Temporal / PIT Governance

Composition-level temporal obligations:

1. One run-level UTC `as_of` exists per governed pipeline run.
2. The same `as_of` is propagated through governed composition.
3. The pipeline may not advance `as_of` using wall-clock time.
4. The pipeline may not substitute a newer stage-local run boundary.
5. Admitted evidence must satisfy applicable `known_at <= as_of`.
6. Replay preserves the original run temporal boundary.

Stage bounded contexts retain ownership of their stage-local PIT validation.
Pipeline Governance does not replace stage PIT governance.

---

## 4. Composition Topology Authority

Governed composition topology:

```text
Watchlist
   → Gap + Catalyst
   → Score
   → Morning Briefing
   → Dashboard
   → optional Human Review
   → optional ADE
```

Requirements:

1. Composition must use public stage contracts.
2. Private implementation coupling is prohibited.
3. Reverse authority flow is prohibited.
4. Hidden alternate pipeline paths are prohibited.
5. Synthetic intermediate outputs are prohibited.
6. Unauthorized stage reordering is prohibited.
7. Unauthorized mandatory-stage skipping is prohibited.

Optional Human Review and ADE terminals remain optional only under their
existing governance.

Architecture defines structure.
Governance freezes the permitted authority path.

---

## 5. Failure / Absence / Abstention Boundaries

Governance recognizes structural categories:

- admission failure
- stage failure
- valid absence
- abstention
- terminal completion

Requirements:

1. No fabricated evidence.
2. No silent fallback to unauthorized data.
3. No silent bypass of a required governed stage.
4. No transformation of failure into approval.
5. No transformation of absence into synthetic evidence.

This Decision does **not** freeze:

- exact error taxonomy
- exact reason codes
- optional Catalyst hard-stop vs continue matrix
- numeric freshness thresholds

Those remain Policy concerns.

---

## 6. Composition Provenance

Requirements:

1. Preserve upstream authoritative identity.
2. Preserve applicable stage provenance references.
3. Do not rewrite authoritative provenance.
4. Do not fabricate provenance.
5. Lineage does not transfer authority.
6. Pipeline provenance must allow evidence-to-result traceability.
7. Human Review / ADE provenance boundaries remain owned by Human Review /
   ADE governance.

Do not create a new lineage platform.

---

## 7. Determinism

Governed execution must be deterministic with respect to:

- canonical evidence
- run `as_of`
- governed configuration references
- governed Policy references
- explicit human input where applicable

Requirements:

1. Stable ordering where order is semantically relevant.
2. No hidden governed-path dependence on wall-clock time.
3. No hidden governed-path dependence on randomness.
4. No hidden governed-path dependence on live provider lookups.
5. No hidden governed-path dependence on mutable uncontrolled external state.

This Decision does not freeze the implementation algorithm.

---

## 8. Replay

Governed replay must preserve:

- canonical evidence
- original `as_of`
- relevant governed configuration references
- relevant governed Policy references
- explicit human input where applicable

Replay must **not**:

- refetch live providers
- advance time
- silently substitute newer Policy
- silently substitute newer configuration
- create trades
- become a backtesting platform
- transfer authority

Replay remains in-process for Sprint 13.
Durable replay / productization remains outside Sprint 13.

---

## 9. Human Review Invocation Boundary

Reference existing Human Review Governance Decisions #1–#8.
Do not create new Human Review semantics.

Composition rule:

1. Human Review is optional.
2. The pipeline may terminate at Dashboard.
3. If Human Review is invoked:
   - it must use the authorized public Human Review contract
   - explicit human attestation is required
   - approval must not be inferred
   - approval must not be synthesized
   - approval must not be automatically generated

| Control | Value |
| --- | --- |
| HUMAN_AUTHORITY_TRANSFER | NO |
| AUTOMATIC_HUMAN_APPROVAL | NO |

---

## 10. ADE Invocation Boundary

Reference existing AI Decision Engine Governance Decisions #1–#8.
Do not reopen ADE Governance.
Do not alter ADE Policy.

Composition rule:

1. ADE is optional.
2. ADE may only be invoked from valid authorized Human Review public output.
3. Missing or invalid Human Review authorization means ADE is not invoked.
4. ADE remains governed accept / abstain only.
5. The pipeline must not reinterpret ADE output.

| Control | Value |
| --- | --- |
| MODEL_PARTICIPATION | UNAUTHORIZED |
| BROKER_EXECUTION | DENIED / DEFERRED |

---

## 11. Model Firewall

| Control | Value |
| --- | --- |
| MODEL_PARTICIPATION | UNAUTHORIZED |

Prohibited:

- LLM
- agent
- model SDK
- inference authority
- model-generated approval
- model-generated human attestation
- model-owned pipeline decision authority

Do not design future model support in this Decision.

---

## 12. Trading / Execution Firewall

| Control | Value |
| --- | --- |
| BROKER_EXECUTION | DENIED / DEFERRED |
| LIVE_TRADING | UNAUTHORIZED |
| ORDER_INTENT_CREATION | UNAUTHORIZED |
| OMS_MUTATION | UNAUTHORIZED |
| STRATEGY_AUTHORITY_TRANSFER | NO |
| RISK_AUTHORITY_TRANSFER | NO |
| PORTFOLIO_AUTHORITY_TRANSFER | NO |

Pipeline output is non-executable intelligence.
No pipeline result may itself authorize or create a trade.

---

## 13. Productization Firewall

Sprint 13 Governance prohibits:

- durable intelligence product persistence
- product read models
- HTTP product APIs
- public query APIs
- public freshness APIs
- frontend / UI
- Premarket Command Center

| Control | Value |
| --- | --- |
| SPRINT_13_PRODUCT_PERSISTENCE | NOT AUTHORIZED |
| SPRINT_13_HTTP_PRODUCT_API | NOT AUTHORIZED |
| UI_AUTHORIZED | NO |
| SPRINT_14_AUTHORIZED | NO |
| SPRINT_15_UI_AUTHORIZED | NO |

Sprint 14 / 15 remain separate future gates.

---

## 14. Feature Platform Firewall

| Control | Value |
| --- | --- |
| FEATURE_PLATFORM_CHANGE_REQUIRED | NO |

Sprint 13 pipeline must not require:

- Feature Store coupling
- forced routing through Feature Platform
- Feature Platform remediation
- new feature persistence
- new feature calculators

Do not modify Sprint 6 ownership.

---

## 15. Provider / Supply-Chain Firewall

Freeze:

1. Canonical evidence only.
2. No live provider fetch from the governed pipeline.
3. No provider-native payload dependency.
4. No new provider SDK.
5. No new model SDK.
6. No new broker SDK.
7. No workflow-engine dependency.
8. No new DB / message-bus dependency for Sprint 13 pipeline.

Do not adopt or copy code / dependencies from:

- AutoHedge
- Vibe-Trading
- Fincept Terminal

Any future third-party adoption remains separately governed and requires
security / supply-chain / license review.

| Control | Value |
| --- | --- |
| NEW_DEPENDENCY_REQUIRED | NO |

---

## 16. Composition Security

Composition-level controls against:

- future-evidence leakage
- timestamp manipulation / spoofing
- provenance spoofing
- unbounded evidence admission
- secret leakage
- Human Review bypass
- synthetic approval
- ADE bypass
- model authority leakage
- broker / execution authority leakage

Do not introduce a new security platform.

---

## 17. In-Process Auditability

Governed in-process results must expose sufficient internal semantics for:

- run identity
- run `as_of`
- stage execution status
- provenance references
- failure / valid absence / abstention state
- optional internal freshness metadata
- replay identity / reference where applicable

This does **not** authorize:

- durable telemetry platform
- public observability API
- public freshness API
- database persistence
- UI

---

## Policy Decisions Intentionally Deferred

The following are **not** frozen by Governance v1 and remain for a later
Intelligence Pipeline Policy Freeze where necessary:

1. Optional Gap / Catalyst continuation behavior at pipeline level.
2. Exact composition error / reason taxonomy.
3. Numeric freshness / staleness thresholds if introduced.
4. Pipeline-level business acceptance thresholds if introduced.
5. Exact partial-stage continuation matrix.

| Control | Value |
| --- | --- |
| POLICY_AUTHORIZATION | APPROVED / FROZEN (by separate Policy Freeze; not created by this Decision) |

Policy is not created by this Decision.

Note: Premarket Scoring Governance already treats Gap / Catalyst collections as
authorized optional inputs and leaves concrete reject / defer / continue
mechanisms to Policy. Pipeline Policy must not contradict that ownership without
an explicit approved freeze.

---

## Governance → Implementation Firewall

Governance approval alone does **not** authorize implementation.

Implementation Authorization requires later prerequisites including:

1. approved Intelligence Pipeline Governance v1
2. required Intelligence Pipeline Policy Freeze
3. Planning APPROVED / EFFECTIVE
4. Architecture APPROVED / EFFECTIVE
5. referenced frozen stage governance / policies remaining valid

| Control | Value |
| --- | --- |
| IMPLEMENTATION_AUTHORIZATION | AUTHORIZED (by separate Implementation Authorization; not by this Decision) |
| IMPLEMENTATION_WORK_STARTED | YES |
| IMPLEMENTATION_SEQUENCE | 3/3 COMPLETE |

No runtime package, tests, schemas, migrations, HTTP routes, UI, or
dependencies are authorized by this Decision alone.

---

## Acceptance Criteria Trace

| ID | Criterion |
| --- | --- |
| AC-01 | Package is README + consolidated Governance v1 only. |
| AC-02 | Composition-only; stage semantics not redefined. |
| AC-03 | Pipeline admission governance frozen. |
| AC-04 | Single UTC run-level `as_of` and composition PIT obligations frozen. |
| AC-05 | Deterministic topology and public-contract composition frozen. |
| AC-06 | Structural failure / absence / abstention rules prohibit fabrication and unauthorized fallback. |
| AC-07 | Composition provenance preservation frozen. |
| AC-08 | Determinism obligations frozen. |
| AC-09 | Replay obligations frozen without live refetch / time advancement. |
| AC-10 | Human Review invocation references existing HR governance and requires explicit attestation. |
| AC-11 | ADE invocation references existing ADE governance and remains HR-gated. |
| AC-12 | MODEL_PARTICIPATION remains UNAUTHORIZED. |
| AC-13 | Trading / execution authority remains denied / deferred; output non-executable. |
| AC-14 | Sprint 13 persistence / HTTP / UI productization remains unauthorized. |
| AC-15 | Feature Platform change remains not required. |
| AC-16 | Provider / supply-chain prohibitions explicit; no new dependency authorized. |
| AC-17 | Composition security and auditability defined without a new platform. |
| AC-18 | Policy-owned decisions explicitly deferred. |
| AC-19 | Governance approval does not authorize Implementation. |

---

## Explicit Non-Authorization Statement

Even when APPROVED, this Governance Decision does **not** authorize:

- Policy Freeze creation or approval by itself beyond unlocking the Policy gate
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
GOVERNANCE APPROVAL ≠ POLICY / IMPLEMENTATION AUTHORIZATION
IMPLEMENTATION_AUTHORIZATION = AUTHORIZED (by separate Implementation Authorization; not by this Governance Decision)
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED / DEFERRED
UI_AUTHORIZED = NO
SPRINT_13_PRODUCT_PERSISTENCE = NOT AUTHORIZED
SPRINT_13_HTTP_PRODUCT_API = NOT AUTHORIZED
FEATURE_PLATFORM_CHANGE_REQUIRED = NO
```

---

## Conclusion

Intelligence Pipeline Governance v1 freezes composition-level authority for
Sprint 13: admission, run-level temporal boundary, topology, structural failure
boundaries, provenance, determinism, replay, optional HR / ADE invocation under
existing stage governance, and model / trading / productization / Feature
Platform / provider firewalls.

Stage bounded contexts retain semantic ownership.
Policy decisions listed above were deferred to Policy Freeze and were later
frozen under `intelligence-pipeline.policy.v1`.
Implementation was not authorized by this Decision; it proceeded under separate
Implementation Authorization and is now COMPLETE (3/3).

This document is **APPROVED / EFFECTIVE**.
`IMPLEMENTATION_COMPLETE = YES`. `SPRINT_COMPLETE = NO`.
`MODEL_PARTICIPATION = UNAUTHORIZED`. `BROKER_EXECUTION = DENIED / DEFERRED`.
