# Premarket Analyst Bounded Slice Architecture v1

**Architecture ID:** `premarket-analyst-bounded-slice.architecture.v1`  
**Status:** DRAFT  
**Sprint:** UNASSIGNED  
**Gate:** Architecture Gate  
**Theme:** Premarket Analyst Bounded Slice  
**Document class:** Architecture-only — not Implementation Authorization  
**Architecture Issue:** [#180](https://github.com/enesdedelerr-max/Bergama/issues/180)  
**Predecessor Planning Issue:** [#178](https://github.com/enesdedelerr-max/Bergama/issues/178)  
**Predecessor Planning PR:** [#179](https://github.com/enesdedelerr-max/Bergama/pull/179)  
**Predecessor Planning merge:** `88be3a55771623cd04464c4478d6307c31b14c13`  
**Planning artifact:** `docs/planning/premarket-analyst-capability-completion/planning-gate.md`  
**Planning document ID:** `premarket-analyst-capability-completion.planning-gate`  
**Planning decision:** `ADVANCE_BOUNDED_SLICE_TO_ARCHITECTURE_GATE`  
**Architecture != Implementation Authorization**

```text
THIS ARTIFACT DOES NOT AUTHORIZE PRODUCT IMPLEMENTATION BY ITSELF.
ARCHITECTURE_GATE_APPROVAL ≠ IMPLEMENTATION_AUTHORIZATION
ARCHITECTURE_STATUS = DRAFT
GOVERNANCE_GATE_AUTHORIZED = NO
POLICY_GATE_AUTHORIZED = NO
IMPLEMENTATION_AUTHORIZATION_GATE_AUTHORIZED = NO
PREMARKET_ANALYST_PRODUCT_IMPLEMENTATION_AUTHORIZED = NO
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED/DEFERRED
PRODUCTION_DEPLOYMENT = NOT_AUTHORIZED
FEATURE_PLATFORM_EXPANSION_AUTHORIZED = NO
UI_UX_IMPLEMENTATION_AUTHORIZED = NO
THIRD_PARTY_DEPENDENCY_ADDITION_AUTHORIZED = NO
TAG_RELEASE_AUTHORIZED = NO
WRITE_API_REQUIRED = NO
ADE_BEHAVIOR_CHANGE_REQUIRED = NO
HR_BEHAVIOR_CHANGE_REQUIRED = NO
PARALLEL_PIPELINE_REQUIRED = NO
```

DRAFT does **not** mean Architecture is EFFECTIVE. Architecture becomes
**APPROVED / EFFECTIVE** only after controlled merge and post-merge
verification of the Architecture Gate PR.

---

## 1. Metadata / Identity

| Field | Value |
| --- | --- |
| Architecture ID | `premarket-analyst-bounded-slice.architecture.v1` |
| Status | DRAFT |
| Sprint | UNASSIGNED |
| Gate | Architecture |
| Architecture Issue | #180 |
| Planning Issue / PR / merge | #178 / #179 / `88be3a55771623cd04464c4478d6307c31b14c13` |
| Planning decision | `ADVANCE_BOUNDED_SLICE_TO_ARCHITECTURE_GATE` |
| Approves Governance | No |
| Approves Policy / Contract Freeze | No |
| Approves Implementation Authorization | No |
| Approves product implementation | No |
| Next eligible process after APPROVED / EFFECTIVE | Governance Gate (not authorized by this DRAFT) |

No Sprint number is assigned by this Architecture Gate.
Do not invent a sprint designation for this initiative.

---

## 2. Purpose

Freeze the minimal architecture required to implement the selected
Premarket Analyst bounded slice as a deterministic, point-in-time-safe,
replayable, non-advisory projection over the existing S7–S15 intelligence
spine.

Preferred architectural flow:

```text
existing normalized Premarket / pipeline outputs
        ↓
deterministic Premarket Analyst projection
        ↓
typed PremarketAnalystArtifact
        ↓
existing intelligence persistence / read boundary
        ↓
future read-only UI consumption (not authorized here)
```

This Architecture Gate:

- does **not** authorize product implementation
- does **not** authorize Governance / Policy / IA
- does **not** authorize models, broker execution, or production deployment
- does **not** authorize Feature Platform expansion
- does **not** authorize frontend implementation or UI redesign
- does **not** authorize migrations, API code, or schema edits

---

## 3. Predecessor Finality

| Input | State |
| --- | --- |
| Planning Issue #178 | CLOSED |
| Planning PR #179 | MERGED |
| Planning merge SHA | `88be3a55771623cd04464c4478d6307c31b14c13` |
| Planning artifact on main | YES |
| Planning decision | `ADVANCE_BOUNDED_SLICE_TO_ARCHITECTURE_GATE` |
| Planning finality | COMPLETE_FINAL |
| Architecture preflight | B — PREMARKET ANALYST ARCHITECTURE PREFLIGHT PASS WITH NON-BLOCKING FINDINGS — CANDIDATE IMPLEMENTATION AUTHORIZED |

Authoritative Planning contract remains:

`docs/planning/premarket-analyst-capability-completion/planning-gate.md`

---

## 4. Scope

### Selected capabilities (exact)

1. Structured Market Summary
2. Structured Catalyst Summary
3. Narrow Structured Thesis
4. Deterministic Descriptive Risk Flags
5. Analyst Evaluation State:
   `EVALUABLE` | `INSUFFICIENT_EVIDENCE` | `NOT_EVALUABLE` | `ABSTAIN`

### Confirm / reuse existing

- gapper ranking
- bounded watchlist

### Architecture in-scope freeze topics

- domain ownership
- typed contracts for the five selected capabilities
- evaluation-state semantics
- non-advice / authority boundary
- informational thesis invalidation semantics
- determinism / PIT / identity / provenance
- pipeline placement
- failure model
- persistence strategy
- read/query strategy
- Feature Platform / model / broker / UI / security firewalls
- Governance → Policy → IA handoff

---

## 5. Explicit Deferrals

Remain **OUT OF SCOPE** and MUST NOT be silently pulled into this slice:

- opening scenarios
- key levels
- final action-plan artifact
- execution-style no-trade semantics
- free-form thesis prose
- Feature Platform expansion
- Priced-In Engine
- Portfolio Stress / Scenario Engine
- LLM / model participation
- ADE model invocation
- Human Review writes
- broker execution
- orders
- position sizing
- portfolio mutation
- production OIDC
- production hosting / deployment
- new market-data providers
- frontend implementation
- UI redesign
- 3D / Motion / 21st.dev integration
- new third-party dependencies
- tag / release

---

## 6. Existing Implementation Topology

Current authoritative flow (repository evidence):

```text
Watchlist
  → Gap
  → Catalyst
  → Score
  → Morning Briefing
  → Dashboard
  → optional Human Review
  → optional ADE
  → AuthoritativeSnapshot
  → intelligence_runs
  → six GET read routes
  → Premarket Command Center UI
```

Relevant modules (non-exhaustive evidence anchors):

| Area | Path / surface |
| --- | --- |
| Watchlist | `apps/api/app/premarket/watchlist/` |
| Gap | `apps/api/app/premarket/gap/` |
| Catalyst | `apps/api/app/premarket/catalyst/` |
| Scoring | `apps/api/app/premarket/scoring/` |
| Morning briefing | `apps/api/app/morning_briefing/` (or Premarket briefing stage) |
| Dashboard | `apps/api/app/dashboard/` |
| Human Review | `apps/api/app/human_review/` |
| ADE | `apps/api/app/ai_decision_engine/` |
| Pipeline | `apps/api/app/intelligence_pipeline/` |
| Durable runs | `apps/api/app/intelligence_runs/` |
| Read API | `apps/api/app/routers/intelligence_runs.py` |
| UI | `apps/platform-console` Premarket Command Center |

No Premarket Analyst projection module exists today.
Closest market-summary surface is dashboard presentation output.
Catalyst product surfaces today often expose identifiers; full
`CatalystRecord` surfaces remain available in-pipeline for projection.

Architecture inserts:

```text
Dashboard
  → deterministic Premarket Analyst projection
  → optional Human Review / ADE continue unchanged
```

The analyst projection is **not** a parallel intelligence pipeline.
It MUST reuse existing upstream outputs.
It MUST NOT duplicate Premarket engines inside the analyst package.

---

## 7. Data Readiness

```text
SELECTED_SLICE_DATA_READY = PARTIAL
BLOCKING_DATA_GAP_COUNT = 0
HARD_PROVIDER_EXPANSION_REQUIRED = NO
```

| Capability | Available evidence today | Non-blocking gaps |
| --- | --- | --- |
| Structured Market Summary | Watchlist membership/count; gap aggregates; catalyst coverage; score/dashboard refs; run `as_of` / freshness / stage presence | Unsupported market-regime narratives |
| Structured Catalyst Summary | In-pipeline `CatalystRecord` fields (identity, type, times, source, fingerprints, rule_id) | Broader classification / generative summary (deferred/prohibited) |
| Narrow Structured Thesis | Score/gap/catalyst/watchlist evidence refs; conflict/absence/stale markers | Rich counter-evidence beyond existing conflict/absence |
| Descriptive Risk Flags | Missing/stale/conflict/freshness/stage-failure/unsupported evaluation signals | Premarket volatility model; OMS risk limits (out of scope) |
| Evaluation State | Upstream presence/completeness/outcome markers; ADE abstain is analogy only | First-class analyst enum (to be introduced by this architecture) |

Architecture freezes **only** data-supported fields.
Unsupported fields are deferred or fail-closed — not invented.

---

## 8. Domain Ownership

```text
RECOMMENDED_DOMAIN_OWNERSHIP =
  DETERMINISTIC_PREMARKET_ANALYST_PROJECTION_SUBDOMAIN

PARALLEL_PIPELINE_REQUIRED = NO
```

Conceptual ownership:

```text
existing Premarket outputs
        ↓
Premarket Analyst deterministic projection
        ↓
typed analyst artifact
        ↓
existing intelligence pipeline persistence / read spine
```

Exact future code package path is an IA / workstream detail unless later
policy freezes it. Architecture freezes the **subdomain responsibility**
and **composition placement**, not a speculative package rename.

Rationale:

- keeps dashboard semantics intact
- reuses Premarket stage outputs without re-running engines
- avoids Feature Platform and parallel pipelines
- keeps ADE / Human Review decision behavior unchanged in v1

---

## 9. Premarket Analyst Artifact Model

Conceptual envelope:

```text
PremarketAnalystArtifact
  analyst_artifact_id
  analyst_definition_version
  as_of                                  # UTC
  pipeline / upstream provenance
  evaluation_state
  market_summary
  catalyst_summary
  theses[]                               # narrow structured theses
  risk_flags[]
  provenance
```

Projection requirements:

- pure function of already-produced upstream outputs at `as_of`
- deterministic
- point-in-time safe
- replayable
- non-advisory
- no model-generated narrative
- no trade authority

Do not recompute Premarket watchlist/gap/catalyst/score engines inside
the analyst projection beyond deterministic aggregation / projection.

---

## 10. Structured Market Summary Contract

### Required (data-supported)

| Field / concept | Class | Notes |
| --- | --- | --- |
| `as_of` | REQUIRED | UTC; run / projection cutoff |
| watchlist count / membership references | REQUIRED | Reuse existing watchlist identity |
| deterministic gap coverage / direction aggregates | REQUIRED | From existing gap records only |
| catalyst coverage aggregates | REQUIRED | Counts / coverage markers only |
| score / dashboard references | REQUIRED | IDs / fingerprints / output refs |
| data completeness markers | REQUIRED | Explicit missing/partial markers |
| provenance | REQUIRED | Upstream refs + definition version |

### Prohibited / deferred

| Field / concept | Class |
| --- | --- |
| free-form narrative market commentary | PROHIBITED |
| price / return predictions | PROHIBITED |
| trade advice | PROHIBITED |
| unsupported market-regime claims | DEFERRED / PROHIBITED |

```text
MARKET_SUMMARY_CONTRACT_FEASIBLE = YES
```

---

## 11. Structured Catalyst Summary Contract

Projection MUST use existing catalyst surfaces (e.g. `CatalystRecord`).

### Required

| Field / concept | Class |
| --- | --- |
| `catalyst_record_id` | REQUIRED |
| `instrument_key` | REQUIRED |
| `catalyst_type` | REQUIRED |
| `event_time` | REQUIRED |
| `known_at` | REQUIRED |
| `as_of` | REQUIRED |
| `source_provider` | REQUIRED |
| `source_event_id` | REQUIRED |
| fingerprints / provenance | REQUIRED |
| `rule_id` where existing | REQUIRED when present upstream |
| deterministic ordering | REQUIRED |
| explicit absence vs unavailable semantics | REQUIRED |

### Prohibited

| Field / concept | Class |
| --- | --- |
| generative catalyst prose | PROHIBITED |
| invented confidence percentages | PROHIBITED |
| new external providers | PROHIBITED |

```text
CATALYST_SUMMARY_CONTRACT_FEASIBLE = YES
```

---

## 12. Narrow Structured Thesis Contract

### Required

| Field / concept | Class |
| --- | --- |
| security identity | REQUIRED |
| `as_of` | REQUIRED |
| supporting evidence references | REQUIRED |
| counter-evidence references where deterministically available | REQUIRED |
| typed observed conditions | REQUIRED |
| informational thesis invalidation conditions | REQUIRED |
| uncertainty / missing-data markers | REQUIRED |
| `evaluation_state` | REQUIRED |
| provenance | REQUIRED |

### Strictly prohibited

```text
BUY
SELL
HOLD
entry price
exit price
stop-loss
price target
position size
expected return
trade instruction
broker instruction
free-form thesis prose
```

```text
STRUCTURED_THESIS_CONTRACT_FEASIBLE = YES
THESIS_EXECUTION_AUTHORITY = NONE
```

---

## 13. Deterministic Descriptive Risk Flag Contract

Risk flags are **descriptive only**.

### Evidence-supported category vocabulary (v1)

```text
MISSING_DATA
STALE_DATA
CONFLICTING_EVIDENCE
WEAK_CATALYST_COVERAGE
FRESHNESS_CONCERN
STAGE_FAILURE_PRESENT
UNSUPPORTED_EVALUATION
NOT_EVALUABLE_INPUT
```

Exact severity vocabulary is **deferred to Governance / Policy** if not
separately evidence-justified in this Architecture DRAFT.

### Every flag MUST include

- stable identity or deterministic derivation
- category
- evidence references
- `as_of`
- provenance
- canonical ordering
- deduplication behavior

### Prohibited authority

```text
RISK_FLAG_ENFORCEMENT_AUTHORITY = NONE
```

Risk flags MUST NOT:

- block orders
- permit orders
- set limits
- size positions
- change portfolios
- act as broker controls

```text
RISK_FLAG_CONTRACT_FEASIBLE = YES
```

---

## 14. Analyst Evaluation-State Semantics

Exact frozen states:

### EVALUABLE

Required inputs are present and the analyst projection can produce the
relevant artifact.

### INSUFFICIENT_EVIDENCE

Inputs exist, but available evidence is inadequate for complete
analytical evaluation.

### NOT_EVALUABLE

Required input is absent, unsupported, stale beyond accepted contract,
or another fail-closed condition prevents evaluation.

### ABSTAIN

The analyst projection deliberately produces no opinion / evaluation
under a deterministic contract condition.

### Placement

- Required at artifact level.
- May also exist at per-thesis level when justified by Policy later.
- Must never imply trade permission, trade prohibition, ADE acceptance,
  ADE rejection, or broker action.
- Must not be coupled to ADE reason codes (ADE remains analogy only).

```text
EVALUATION_STATE_CONTRACT_FEASIBLE = YES
```

---

## 15. Non-Advice / Authority Boundary

```text
NON_ADVICE_BOUNDARY = HARD
THESIS_EXECUTION_AUTHORITY = NONE
RISK_FLAG_ENFORCEMENT_AUTHORITY = NONE
ORDER_AUTHORITY = NONE
BROKER_AUTHORITY = NONE
PORTFOLIO_MUTATION_AUTHORITY = NONE
```

Analyst artifacts are decision-support structured facts and abstention
markers only. They are not recommendations, not execution instructions,
and not ADE / Human Review decision substitutes.

Prohibited vocabulary and semantics include BUY / SELL / HOLD and any
entry / exit / stop / target / sizing / return / broker instruction.

---

## 16. Informational Thesis Invalidation Semantics

```text
INFORMATIONAL_THESIS_INVALIDATION_ONLY = REQUIRED
```

An invalidation condition means **only**:

> the evidence-bound analytical thesis no longer satisfies its
> informational conditions.

It MUST NOT:

- close a position
- recommend closing a position
- trigger stop-loss
- cancel an order
- submit an order
- change position size
- change portfolio state
- invoke broker behavior

Governance and Policy MUST enforce this semantic boundary.

---

## 17. Determinism Contract

Frozen requirements:

- canonical input ordering
- canonical output ordering
- stable serialization
- UTC `as_of`
- deterministic missing-data behavior
- deterministic tie-breaking
- stable identity
- definition / version pinning (`analyst_definition_version`)
- provenance hashes
- replay equality
- deterministic abstention

```text
DETERMINISM_ARCHITECTURE_FEASIBLE = YES
NONDETERMINISTIC_FIELD_COUNT = 0
```

No current-time reads during replay except persisted run metadata that
existing contracts already exclude from canonical equality.

Same pinned inputs + same definition version + same code version MUST
produce the same analyst artifact.

---

## 18. PIT / No-Lookahead Contract

```text
PIT_ARCHITECTURE_FEASIBLE = YES
```

Analyst projection may only use data known / available at or before the
run `as_of` according to existing upstream timing contracts.

Respect existing:

- `event_time`
- `known_at`
- `as_of`
- bar cutoff
- watchlist cutoff
- score cutoff
- catalyst cutoff

Do **not** invent missing timing metadata.

Insufficient timing evidence MUST:

- fail closed, or
- map to `NOT_EVALUABLE`, or
- omit / defer the affected field according to future Policy

Never silently use future-known data.

---

## 19. Identity / Provenance Contract

### Minimal new identity

```text
NEW_IDENTITY_REQUIRED = YES
analyst_artifact_id            # content-addressed deterministic identity
analyst_definition_version     # definition / policy pin
```

### Reuse existing identities

- `pipeline_fingerprint`
- stage fingerprints
- instrument keys
- catalyst IDs
- gap IDs
- score IDs
- dashboard IDs
- intelligence run identity

### Canonical identity participation

Participate in `analyst_artifact_id` / canonical equality:

- definition version
- `as_of`
- evaluation_state
- market_summary
- catalyst_summary
- theses
- risk_flags
- upstream content hashes / fingerprints required by Policy

Do **not** participate (operational metadata only), unless existing
contracts already include them:

- wall-clock persist timestamps
- request IDs / transport IDs
- mutable operational labels unrelated to projection content

Do not create redundant identity layers.

---

## 20. Pipeline Placement

```text
Dashboard
  → Premarket Analyst projection
  → optional Human Review / ADE continue
```

### Upstream dependencies

Watchlist, Gap, Catalyst, Score, Morning Briefing, Dashboard, and run
bindings / `as_of` / stage presence required for projection inputs.

### v1 consumers

- persistence (analyst public snapshot)
- read / query API
- future read-only UI (not authorized here)

### v1 non-consumers for decision change

```text
ADE_BEHAVIOR_CHANGE_REQUIRED = NO
HR_BEHAVIOR_CHANGE_REQUIRED = NO
MODEL_BEHAVIOR_CHANGE_REQUIRED = NO
```

Human Review DOES NOT use the analyst artifact to change decisions in v1.
ADE DOES NOT use the analyst artifact to change decisions in v1.

```text
PIPELINE_PLACEMENT_FEASIBLE = YES
```

---

## 21. Failure Model

Deterministic classifications only:

| Condition | Classification |
| --- | --- |
| missing bars | `NOT_EVALUABLE` or `INSUFFICIENT_EVIDENCE` per field rules |
| missing gap evidence | `NOT_EVALUABLE` / `INSUFFICIENT_EVIDENCE` |
| missing catalysts | absence marker + `INSUFFICIENT_EVIDENCE` or `NOT_EVALUABLE` as applicable |
| stale catalysts | fail-closed → `NOT_EVALUABLE` (reuse Premarket stale semantics) |
| missing score | `NOT_EVALUABLE` / `INSUFFICIENT_EVIDENCE` |
| conflicting evidence | risk flag + `INSUFFICIENT_EVIDENCE` or `ABSTAIN` (Policy later) |
| malformed normalized input | `FAIL_CLOSED` / `PROPAGATE_EXISTING_PIPELINE_FAILURE` |
| unsupported security | `NOT_EVALUABLE` |
| partial watchlist | degrade evaluation state; never invent membership |
| upstream stage failure | `PROPAGATE_EXISTING_PIPELINE_FAILURE` and/or `STAGE_FAILURE_PRESENT` flag |

Allowed classification vocabulary:

```text
FAIL_CLOSED
INSUFFICIENT_EVIDENCE
NOT_EVALUABLE
ABSTAIN
PROPAGATE_EXISTING_PIPELINE_FAILURE
```

Architecture MUST distinguish:

- input absence
- insufficient evidence
- invalid / malformed input
- explicit abstention

Never map failure state to trade action.

---

## 22. Persistence Strategy

```text
RECOMMENDED_PERSISTENCE_STRATEGY =
  CO_PERSIST_TYPED_ANALYST_PUBLIC_SNAPSHOT_WITH_INTELLIGENCE_RUN

DATABASE_MIGRATION_EXPECTED = YES   # future IA / implementation only
```

Preferred direction:

- extend `AuthoritativeSnapshot` with an analyst snapshot component
  and/or equivalent versioned nullable analyst snapshot representation
  inside existing intelligence run persistence

Constraints:

- do **not** create a separate analyst database / service
- historical reads MUST return stored analyst snapshots
- historical reads MUST NOT regenerate analyst artifacts from current logic

Future implementation impact (not authorized here):

- minimal expand / contract migration
- nullable / versioned compatibility
- `snapshot_contract_version` impact
- `pipeline_fingerprint` impact (analyst definition must not silently
  rewrite historical fingerprints without Policy)
- canonical equality impact
- replay equality impact

```text
NO_MIGRATION_IN_THIS_ARCHITECTURE_WORKFLOW = YES
```

---

## 23. Read / Query Strategy

```text
RECOMMENDED_READ_BOUNDARY =
  EXTEND_IntelligenceRunRead_WITH_NESTED_ANALYST_DTO
  + DEDICATED_READ_ONLY_ANALYST_PROJECTION_ROUTE

WRITE_API_REQUIRED = NO
```

Preferred route pattern (mirror dashboard / HR / ADE):

```text
GET /intelligence/runs/.../analyst
```

Exact final path naming may be confirmed in Policy / IA if needed, but
Architecture freezes:

- nested analyst DTO on run read
- dedicated read-only analyst projection route
- no write / mutation endpoints

Auth boundary remains `intelligence:runs:read` unless later evidence
requires otherwise (not escalated here).

No:

- analyst write endpoint
- HR write endpoint
- ADE write endpoint
- broker endpoint

---

## 24. Future UI Contract Implications

Future read-only Premarket Command Center UI may consume:

- market summary
- catalyst summary
- structured thesis fields
- risk flags
- evaluation state
- provenance / freshness indicators
- explicit non-advice semantics

```text
UI_CONTRACT_IMPLICATIONS_DEFINED = YES
UI_IMPLEMENTATION_REQUIRED_FOR_ARCHITECTURE = NO
UI_UX_IMPLEMENTATION_AUTHORIZED = NO
```

This Architecture does **not** design UI, modify frontend, or authorize
redesign / 3D / Motion / 21st.dev work.

---

## 25. Feature Platform Boundary

```text
FEATURE_PLATFORM_HARD_DEPENDENCY = NO
FEATURE_PLATFORM_EXPANSION_REQUIRED = NO
FEATURE_PLATFORM_EXPANSION_AUTHORIZED = NO
```

Do not require:

- feature store
- online store
- scheduler
- freshness service
- parity expansion
- provider expansion

The analyst slice operates on already-produced deterministic upstream
outputs.

---

## 26. Security / Dependency Boundary

```text
NEW_DEPENDENCY_REQUIRED = NO
NEW_SECRET_REQUIRED = NO
NEW_EXTERNAL_PROVIDER_REQUIRED = NO
NEW_INFRASTRUCTURE_REQUIRED = NO
THIRD_PARTY_DEPENDENCY_ADDITION_AUTHORIZED = NO
```

Security requirements:

- treat source / catalyst text as untrusted
- future UI exposure MUST use safe structured DTOs
- no HTML / Markdown execution of catalyst or thesis fields
- no secrets in analyst artifacts
- no expansion of auth authority beyond existing read scope
- no XSS-prone free-form embedding in contracts

---

## 27. Performance / Scale

Remain bounded by existing watchlist and catalyst cardinality.

Prefer:

- single-pass projections
- bounded deterministic aggregation
- stable sorting
- no new service
- no new queue
- no new cache
- no new infrastructure

```text
NEW_INFRASTRUCTURE_REQUIRED = NO
```

Complexity is qualitative and O(watchlist × catalyst coverage) within
existing Premarket bounds. No premature performance targets invented.

---

## 28. Test / Evaluation Architecture

Future implementation (after IA) MUST cover:

- unit contract tests
- determinism tests
- canonical ordering tests
- PIT / no-lookahead tests
- replay equality tests
- missing-data tests
- abstention tests
- evaluation-state tests
- non-advice vocabulary tests
- informational invalidation tests
- authority-firewall tests
- pipeline integration tests
- persistence round-trip tests
- read DTO / route tests
- watchlist / ranking regression
- ADE unchanged regression
- HR unchanged regression
- migration compatibility if migration later authorized

```text
TESTS_IMPLEMENTED_BY_THIS_ARCHITECTURE_ARTIFACT = NO
```

---

## 29. Governance Handoff

Architecture hands Governance the frozen contracts for:

- non-advice authority
- informational invalidation semantics
- evaluation-state non-execution meaning
- risk-flag non-enforcement
- ADE / HR non-coupling in v1
- Feature Platform / model / broker / production firewalls
- severity vocabulary decision for risk flags (if deferred)

```text
GOVERNANCE_GATE_AUTHORIZED = NO
NEXT_RECOMMENDED_GATE = Governance Gate
NEXT_GATE_AUTHORIZED = NO
```

---

## 30. Policy / Contract Handoff

Architecture hands Policy / Contract Gate the need to freeze:

- exact typed schemas / enums for the five capabilities
- serialization / hashing / ordering rules
- snapshot contract expand details
- read DTO / route contract details
- fail-closed / abstention mapping tables
- identity field participation rules

```text
POLICY_GATE_AUTHORIZED = NO
```

---

## 31. Implementation Authorization Prerequisites

Before any product workstream:

1. Architecture APPROVED / EFFECTIVE
2. Governance Gate complete
3. Policy / Contract Freeze complete
4. Implementation Authorization Gate complete

```text
IMPLEMENTATION_AUTHORIZATION_STILL_REQUIRED = YES
IMPLEMENTATION_AUTHORIZATION_GATE_AUTHORIZED = NO
PREMARKET_ANALYST_PRODUCT_IMPLEMENTATION_AUTHORIZED = NO
```

Architecture approval alone does **not** authorize product code,
migrations, API changes, frontend changes, or tests beyond docs gates.

---

## 32. Architecture Decisions

| ID | Decision | Freeze |
| --- | --- | --- |
| AD-01 | Domain ownership = deterministic Premarket Analyst projection subdomain; no parallel pipeline | FROZEN |
| AD-02 | Analyst artifact envelope (`PremarketAnalystArtifact`) | FROZEN |
| AD-03 | Structured Market Summary contract (data-supported fields only) | FROZEN |
| AD-04 | Structured Catalyst Summary contract from existing catalyst surfaces | FROZEN |
| AD-05 | Narrow Structured Thesis contract; `THESIS_EXECUTION_AUTHORITY = NONE` | FROZEN |
| AD-06 | Descriptive risk flags; evidence-supported categories; no enforcement authority | FROZEN |
| AD-07 | Evaluation states: EVALUABLE / INSUFFICIENT_EVIDENCE / NOT_EVALUABLE / ABSTAIN | FROZEN |
| AD-08 | Non-advice authority hard boundary | FROZEN |
| AD-09 | `INFORMATIONAL_THESIS_INVALIDATION_ONLY` | FROZEN |
| AD-10 | Determinism (`NONDETERMINISTIC_FIELD_COUNT = 0` for v1 field set) | FROZEN |
| AD-11 | PIT / no-lookahead | FROZEN |
| AD-12 | Minimal new identity: `analyst_artifact_id` + `analyst_definition_version` | FROZEN |
| AD-13 | Pipeline placement after Dashboard; ADE/HR unchanged in v1 | FROZEN |
| AD-14 | Failure model classifications | FROZEN |
| AD-15 | Co-persist analyst public snapshot; future migration expected under IA | FROZEN |
| AD-16 | Read nested DTO + read-only analyst route; `WRITE_API_REQUIRED = NO` | FROZEN |
| AD-17 | Feature Platform hard dependency / expansion = NO | FROZEN |
| AD-18 | Model / broker / production / UI / security / dependency boundary | FROZEN |

Risk-flag severity vocabulary remains a Governance / Policy item if not
separately evidence-justified (non-blocking).

---

## 33. Acceptance Criteria

AC-01 Planning traceability  
AC-02 Selected slice only / deferrals preserved  
AC-03 Data-supported fields only  
AC-04 Domain ownership frozen  
AC-05 Structured Market Summary contract  
AC-06 Structured Catalyst Summary contract  
AC-07 Narrow Structured Thesis contract  
AC-08 Descriptive Risk Flag contract  
AC-09 Evaluation State contract  
AC-10 Non-advice + INFORMATIONAL_THESIS_INVALIDATION_ONLY  
AC-11 Determinism  
AC-12 PIT / no-lookahead  
AC-13 Identity / provenance  
AC-14 Pipeline placement; ADE/HR unchanged  
AC-15 Failure model  
AC-16 Persistence strategy  
AC-17 Read boundary; WRITE_API_REQUIRED = NO  
AC-18 Feature Platform firewall  
AC-19 Model / broker / production firewalls  
AC-20 Security / no new deps/providers/secrets  
AC-21 Test architecture themes  
AC-22 Governance → Policy → IA handoff  
AC-23 Authority firewall: Architecture != IA; product implementation unauthorized  

Do **not** mark these PASS merely because this DRAFT artifact exists.
Candidate remains DRAFT until review / merge / finality.

---

## 34. Architecture Decision

```text
ARCHITECTURE_DECISION = ADVANCE_TO_GOVERNANCE_GATE
NEXT_RECOMMENDED_GATE = Governance Gate
NEXT_GATE_AUTHORIZED = NO
GOVERNANCE_GATE_AUTHORIZED = NO
```

Evidence supports a bounded, deterministic, PIT-safe, non-advisory
architecture on the existing intelligence spine with zero blocking data
gaps and no parallel pipeline / Feature Platform / model / broker
requirement.

---

## 35. Authority Firewall

```text
ARCHITECTURE_STATUS = DRAFT
ARCHITECTURE_APPROVAL != IMPLEMENTATION_AUTHORIZATION
PREMARKET_ANALYST_PRODUCT_IMPLEMENTATION_AUTHORIZED = NO
GOVERNANCE_GATE_AUTHORIZED = NO
POLICY_GATE_AUTHORIZED = NO
IMPLEMENTATION_AUTHORIZATION_GATE_AUTHORIZED = NO
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED/DEFERRED
PRODUCTION_DEPLOYMENT = NOT_AUTHORIZED
FEATURE_PLATFORM_EXPANSION_AUTHORIZED = NO
UI_UX_IMPLEMENTATION_AUTHORIZED = NO
THIRD_PARTY_DEPENDENCY_ADDITION_AUTHORIZED = NO
TAG_RELEASE_AUTHORIZED = NO
WRITE_API_REQUIRED = NO
ADE_BEHAVIOR_CHANGE_REQUIRED = NO
HR_BEHAVIOR_CHANGE_REQUIRED = NO
PARALLEL_PIPELINE_REQUIRED = NO
COMMIT_AUTHORIZED = NO
PUSH_AUTHORIZED = NO
PR_CREATION_AUTHORIZED = NO
```

---

## 36. Next Gate

```text
NEXT_GATE = Governance Gate
NEXT_GATE_AUTHORIZED = NO
PROCESS_STATE_AFTER_ARCHITECTURE_APPROVED_EFFECTIVE =
  PREMARKET_ANALYST_GOVERNANCE_GATE_ELIGIBLE_NOT_AUTHORIZED
```

Required lifecycle:

```text
Architecture
  → Governance
  → Policy / Contract
  → Implementation Authorization
  → bounded implementation workstreams
```

This DRAFT candidate stops at independent review before commit.
No Governance issue creation is authorized by this artifact alone.
