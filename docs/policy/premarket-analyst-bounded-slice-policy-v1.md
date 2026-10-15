# Premarket Analyst Bounded Slice Policy / Contract v1

**Policy ID:** `premarket-analyst-bounded-slice.policy.v1`  
**Version:** v1  
**Title:** Premarket Analyst Bounded Slice Policy / Contract Freeze v1  
**Status:** DRAFT  
**Sprint:** UNASSIGNED  
**Gate:** Policy / Contract Freeze  
**Theme:** Premarket Analyst Bounded Slice  
**Document class:** Policy / Contract Freeze only — not Implementation Authorization  
**Policy Issue:** [#184](https://github.com/enesdedelerr-max/Bergama/issues/184)  
**Predecessor Planning:** Issue [#178](https://github.com/enesdedelerr-max/Bergama/issues/178) / PR [#179](https://github.com/enesdedelerr-max/Bergama/pull/179)  
**Predecessor Architecture:** Issue [#180](https://github.com/enesdedelerr-max/Bergama/issues/180) / PR [#181](https://github.com/enesdedelerr-max/Bergama/pull/181) — `premarket-analyst-bounded-slice.architecture.v1`  
**Architecture Merge:** `f5997c7badfa4b6343040e5798ff73bacf0fbe78`  
**Architecture Artifact SHA256:** `b83891e47cf4661cfaeac59737e5f0fa9e778048e2b2971f2c58cfb1d0a70236`  
**Predecessor Governance:** Issue [#182](https://github.com/enesdedelerr-max/Bergama/issues/182) / PR [#183](https://github.com/enesdedelerr-max/Bergama/pull/183) — `premarket-analyst-bounded-slice.governance.v1`  
**Governance Merge / Authoritative main at draft:** `86f540f1463cdad7353f68060479113ef4d280f0`  
**Governance Artifact SHA256:** `64330f2eaebd50e311f6ca8ab7ebaf02621a4c8eb1cb7cd95e3dfa2eecdde4ed`  
**Governance Decision:** `ADVANCE_TO_POLICY_GATE`  
**Governance post-merge CI:** run `38674123176` SUCCESS  

```text
THIS ARTIFACT DOES NOT AUTHORIZE PRODUCT IMPLEMENTATION.
POLICY APPROVAL ≠ IMPLEMENTATION AUTHORIZATION
POLICY_STATUS = DRAFT
IMPLEMENTATION_AUTHORIZATION_GATE_AUTHORIZED = NO
PREMARKET_ANALYST_PRODUCT_IMPLEMENTATION_AUTHORIZED = NO
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED/DEFERRED
PRODUCTION_DEPLOYMENT = NOT_AUTHORIZED
FEATURE_PLATFORM_EXPANSION_AUTHORIZED = NO
UI_UX_IMPLEMENTATION_AUTHORIZED = NO
THIRD_PARTY_DEPENDENCY_ADDITION_AUTHORIZED = NO
MIGRATION_AUTHORIZED = NO
WRITE_API_AUTHORIZED = NO
WRITE_API_REQUIRED = NO
ADE_BEHAVIOR_CHANGE_REQUIRED = NO
HR_BEHAVIOR_CHANGE_REQUIRED = NO
PARALLEL_PIPELINE_REQUIRED = NO
TAG_RELEASE_AUTHORIZED = NO
NEXT_GATE_AUTHORIZED = NO
```

DRAFT does **not** mean Policy is EFFECTIVE. Policy becomes
**APPROVED / FROZEN** only after controlled merge and post-merge
verification of the Policy Gate PR.

---

## 1. Metadata / Identity

| Field | Value |
| --- | --- |
| Policy ID | `premarket-analyst-bounded-slice.policy.v1` |
| Status | DRAFT |
| Sprint | UNASSIGNED |
| Gate | Policy / Contract Freeze |
| Policy Issue | #184 |
| Architecture Issue / PR / merge | #180 / #181 / `f5997c7…` |
| Governance Issue / PR / merge | #182 / #183 / `86f540f…` |
| Approves Implementation Authorization | No |
| Approves product implementation | No |
| Next eligible process after APPROVED / FROZEN | Implementation Authorization Gate (not authorized by this DRAFT) |

No Sprint number is assigned by this Policy Gate.

---

## 2. Purpose

Freeze machine-testable Policy / Contract mechanics for the Premarket
Analyst Bounded Slice after Architecture and Governance finality,
without redesigning Architecture, weakening Governance firewalls, or
authorizing product implementation.

```text
Architecture defines structure and domain placement.
Governance defines WHAT MUST / MUST NOT be true.
Policy freezes HOW those controls become exact, testable contracts.
IA alone may later authorize bounded implementation.
```

---

## 3. Authority Layers

| Layer | Owns |
| --- | --- |
| Planning / Architecture / Governance | Theme, domain design, invariant authority |
| **This Policy / Contract Freeze** | Exact machine-testable contracts within frozen scope |
| Implementation Authorization | Permission to implement under this freeze |

This Policy MUST NOT reopen Architecture or Governance decisions unless
a later governed correction explicitly amends them.

---

## 4. Predecessor Finality

| Input | State |
| --- | --- |
| Planning #178 / PR #179 | CLOSED / MERGED |
| Architecture #180 / PR #181 | CLOSED / MERGED @ `f5997c7…` |
| Architecture artifact SHA256 | `b83891e47cf4661cfaeac59737e5f0fa9e778048e2b2971f2c58cfb1d0a70236` |
| Governance #182 / PR #183 | CLOSED / MERGED @ `86f540f…` |
| Governance artifact SHA256 | `64330f2eaebd50e311f6ca8ab7ebaf02621a4c8eb1cb7cd95e3dfa2eecdde4ed` |
| Governance decision | `ADVANCE_TO_POLICY_GATE` |
| Governance post-merge CI | run `38674123176` SUCCESS |
| Authoritative main at draft | `86f540f1463cdad7353f68060479113ef4d280f0` |

Referenced Intelligence Pipeline / Run productization authorities remain
authoritative for composition and persistence spine semantics and are
not reopened by this document.

---

## 5. Five-Capability Scope Lock

Policy freezes exactly these capabilities:

1. Structured Market Summary
2. Structured Catalyst Summary
3. Narrow Structured Thesis
4. Deterministic Descriptive Risk Flags
5. Analyst Evaluation State:
   `EVALUABLE` | `INSUFFICIENT_EVIDENCE` | `NOT_EVALUABLE` | `ABSTAIN`

Confirm / reuse only (no new capability):

- gapper ranking
- bounded watchlist

```text
SCOPE_EXPANSION_AUTHORIZED = NO
```

Silent addition of fields, capabilities, providers, model semantics,
broker semantics, Feature Platform dependency, UI implementation, or
execution semantics is PROHIBITED.

---

## 6. Explicit Deferrals / Exclusions

OUT OF SCOPE and MUST NOT be authorized by this Policy:

- opening scenarios; key levels; final action-plan
- execution-oriented no-trade behavior
- free-form thesis prose
- priced-in engine; stress / scenario engine
- Feature Platform expansion
- model participation / LLM generation
- broker / OMS / order execution
- production deployment
- write API; analyst mutation endpoints
- frontend / UI redesign / 3D / Motion / 21st.dev
- new external provider; new dependency; new secret; new infrastructure
- ADE behavior change; Human Review behavior change
- product implementation workstreams

---

## 7. Artifact Envelope Contract

Canonical envelope concepts (field names are contract identifiers):

```text
PremarketAnalystArtifact
  analyst_artifact_id
  analyst_definition_version
  as_of                                  # UTC timezone-aware
  evaluation_state
  market_summary
  catalyst_summary
  theses[]
  risk_flags[]
  provenance / upstream fingerprints
```

Projection MUST be a pure function of already-produced upstream outputs
at `as_of`. It MUST NOT recompute Premarket watchlist / gap / catalyst /
score engines beyond deterministic aggregation / projection.

```text
ARTIFACT_ENVELOPE_CONTRACT = FROZEN
```

---

## 8. UTC `as_of` / Determinism Contract

### Time

1. `as_of` MUST be UTC timezone-aware.
2. Analyst projection MUST use the same run `as_of` as upstream pipeline
   bindings for the intelligence run.
3. Wall-clock reads during replay are PROHIBITED except persisted
   operational metadata already excluded from canonical equality by
   existing Intelligence Run contracts.

### Determinism requirements

1. Canonical input ordering MUST be deterministic.
2. Canonical output ordering MUST be deterministic.
3. Serialization MUST be stable for equality / hashing.
4. Tie-breaks MUST be deterministic.
5. Missing-data handling MUST be deterministic.
6. Definition / version pinning (`analyst_definition_version`) MUST be
   required.
7. Abstention MUST be deterministic.
8. Replay equality MUST hold for pinned inputs + definition + code.

```text
NONDETERMINISTIC_FIELD_COUNT = 0
DETERMINISM_POLICY = FROZEN
```

---

## 9. PIT / No-Lookahead Contract

Analyst projection MAY only use data known / available at or before run
`as_of` according to existing upstream timing contracts:

- `event_time`
- `known_at`
- `as_of`
- bar / watchlist / score / catalyst cutoffs

Rules:

1. Future-known inputs MUST NOT influence an analyst artifact.
2. Late-arriving data MUST NOT be silently treated as known-at-or-before
   `as_of`.
3. Insufficient timing evidence MUST NOT silently become valid evidence.
4. Missing timing metadata MUST NOT be invented.

Allowed handling for insufficient timing evidence:

- fail closed, or
- map to `NOT_EVALUABLE`, or
- omit / mark the affected field unavailable per §16 / §17

```text
PIT_POLICY = FROZEN
NUMERIC_STALENESS_THRESHOLD_INVENTED = NO
```

Staleness classification MUST reuse existing Premarket / pipeline stale
semantics where available. New numeric completeness / staleness
thresholds are **not** invented by this DRAFT (`OPQ-05`).

---

## 10. Identity / Provenance Contract

### Required identities

| Identity | Class |
| --- | --- |
| `analyst_artifact_id` | REQUIRED — content-addressed deterministic identity |
| `analyst_definition_version` | REQUIRED — definition / policy pin |
| `as_of` | REQUIRED — UTC |
| pipeline fingerprint | REQUIRED when present upstream |
| stage fingerprints | REQUIRED when present upstream |
| instrument identity | REQUIRED for instrument-scoped outputs |
| source identity | REQUIRED for catalyst / source-bound outputs |
| catalyst identity | REQUIRED for catalyst-bound outputs |
| run identity | REQUIRED for persistence / read binding |

### Canonical equality participation

MUST participate in `analyst_artifact_id` / canonical equality:

- `analyst_definition_version`
- `as_of`
- `evaluation_state`
- `market_summary`
- `catalyst_summary`
- `theses`
- `risk_flags`
- upstream content hashes / fingerprints required by this Policy

MUST NOT participate (operational metadata only), unless an existing
Intelligence Run contract already includes them:

- wall-clock persist timestamps
- request IDs / transport IDs
- mutable operational labels unrelated to projection content

```text
IDENTITY_PROVENANCE_POLICY = FROZEN
```

---

## 11. Structured Market Summary Contract

### Required concepts

| Concept | Class |
| --- | --- |
| `as_of` (UTC) | REQUIRED |
| watchlist count / membership references | REQUIRED |
| deterministic gap coverage / direction aggregates | REQUIRED |
| catalyst coverage aggregates (counts / markers) | REQUIRED |
| score / dashboard references (IDs / fingerprints / refs) | REQUIRED |
| data completeness markers | REQUIRED |
| provenance | REQUIRED |

### Prohibited

| Concept | Class |
| --- | --- |
| free-form narrative market commentary | PROHIBITED |
| price / return predictions | PROHIBITED |
| trade advice / recommendation | PROHIBITED |
| BUY / SELL / HOLD semantics | PROHIBITED |
| unsupported market-regime claims | PROHIBITED |

```text
MARKET_SUMMARY_POLICY = FROZEN
```

Exact nested DTO field names beyond these contract concepts remain
implementation-facing under IA once schemas are coded (`OPQ-06` partial:
concepts frozen; code-level naming under IA).

---

## 12. Structured Catalyst Summary Contract

Projection MUST use existing `CatalystRecord` (or equivalent contracted
catalyst) surfaces. Synthesis of unavailable catalyst fields is
PROHIBITED.

### Required concepts

| Concept | Class |
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
| `rule_id` | REQUIRED when present upstream |
| deterministic ordering | REQUIRED |
| explicit absence vs unavailable semantics | REQUIRED |

### Prohibited

| Concept | Class |
| --- | --- |
| generative catalyst prose | PROHIBITED |
| invented confidence percentages | PROHIBITED |
| new external providers | PROHIBITED |

```text
CATALYST_SUMMARY_POLICY = FROZEN
```

---

## 13. Narrow Structured Thesis Contract

### Required concepts

| Concept | Class |
| --- | --- |
| security / instrument identity | REQUIRED |
| `as_of` | REQUIRED |
| supporting evidence references | REQUIRED |
| counter-evidence references where deterministically available | REQUIRED |
| typed observed conditions | REQUIRED |
| informational thesis invalidation conditions | REQUIRED |
| uncertainty / missing-data markers | REQUIRED |
| `evaluation_state` | REQUIRED |
| provenance | REQUIRED |

### Prohibited semantic vocabulary / fields

Exact prohibition set (machine-testable; may appear only when documenting
prohibitions):

```text
BUY
SELL
HOLD
entry
exit
entry price
exit price
stop-loss
price target
position size
expected return
trade signal
trade instruction
order intent
broker intent
broker instruction
free-form thesis prose
```

```text
THESIS_EXECUTION_AUTHORITY = NONE
STRUCTURED_THESIS_POLICY = FROZEN
```

---

## 14. Informational Invalidation Contract

```text
INFORMATIONAL_THESIS_INVALIDATION_ONLY = REQUIRED
EXECUTION_COUPLING_ALLOWED = NO
```

Definition: a change in evidence causing an informational analytical
thesis to no longer satisfy its evidence conditions.

### Prohibition vocabulary (frozen)

Invalidation MUST NOT perform or imply any of:

```text
EXIT_TRADE
CLOSE_POSITION
RECOMMEND_CLOSE_POSITION
SET_STOP_LOSS
TRIGGER_STOP_LOSS
CANCEL_ORDER
CREATE_ORDER
MODIFY_ORDER
CHANGE_POSITION_SIZE
MUTATE_PORTFOLIO_STATE
INVOKE_BROKER_ACTION
```

```text
INVALIDATION_PROHIBITION_VOCABULARY = FROZEN
```

---

## 15. Descriptive Risk Flag Contract

### Category vocabulary (v1 exact)

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

### Every risk flag MUST include

- stable identity or deterministic derivation
- category from the exact set above
- evidence references
- `as_of`
- provenance
- canonical ordering
- deduplication behavior

### Authority

```text
RISK_FLAG_ENFORCEMENT_AUTHORITY = NONE
RISK_FLAG_TRADE_AUTHORITY = NONE
RISK_FLAG_SEVERITY_VOCABULARY_FROZEN = NO
```

Risk flags MUST NOT permit, prohibit, veto, block, size, limit, or invoke
broker / order / portfolio actions.

### Severity

Governance ownership decision B: severity vocabulary is **not** frozen
in this Policy v1. Inventing `LOW` / `MEDIUM` / `HIGH` or any severity
taxonomy without separate evidence-justified Policy review is PROHIBITED
(`OPQ-01`).

```text
RISK_FLAG_POLICY = FROZEN_CATEGORIES_ONLY
```

---

## 16. Evaluation-State Contract

Exact states:

```text
EVALUABLE
INSUFFICIENT_EVIDENCE
NOT_EVALUABLE
ABSTAIN
```

### Semantic definitions (frozen)

| State | Meaning |
| --- | --- |
| `EVALUABLE` | Required inputs are present and the projection can produce the relevant artifact |
| `INSUFFICIENT_EVIDENCE` | Inputs exist, but available evidence is inadequate for complete analytical evaluation |
| `NOT_EVALUABLE` | Required input absent, unsupported, stale beyond accepted upstream contract, or another fail-closed condition prevents evaluation |
| `ABSTAIN` | Projection deliberately produces no opinion / evaluation under a deterministic contract condition |

### Placement

- REQUIRED at artifact level.
- Per-thesis evaluation_state MAY be present when each thesis carries its
  own evidence completeness; artifact-level state remains authoritative
  for run-level interpretation (`PD-11`).
- MUST never imply trade permission, trade prohibition, ADE accept /
  reject, Human Review decision, or broker action.

### Non-equivalence (frozen)

```text
EVALUABLE != trade permission
INSUFFICIENT_EVIDENCE != trade prohibition
NOT_EVALUABLE != trade prohibition
ABSTAIN != order/broker block
evaluation state != ADE accept/reject
evaluation state != Human Review decision
```

```text
EVALUATION_STATE_POLICY = FROZEN
```

Fine-grained transition automata beyond §17 condition mapping remain
`OPQ-02` where additional mechanical detail is needed.

---

## 17. Failure / Abstention Mapping Contract

### Allowed outcome vocabulary

```text
FAIL_CLOSED
INSUFFICIENT_EVIDENCE
NOT_EVALUABLE
ABSTAIN
PROPAGATE_EXISTING_PIPELINE_FAILURE
```

### Condition → outcome mapping (v1)

| Condition | Required mapping |
| --- | --- |
| missing bars | `NOT_EVALUABLE` or `INSUFFICIENT_EVIDENCE` per affected field completeness markers |
| missing gap evidence | `NOT_EVALUABLE` or `INSUFFICIENT_EVIDENCE` |
| missing catalysts | explicit absence marker + `INSUFFICIENT_EVIDENCE` or `NOT_EVALUABLE` as applicable |
| stale catalysts | fail-closed → `NOT_EVALUABLE` (reuse existing Premarket stale semantics; no new numeric threshold invented) |
| missing score | `NOT_EVALUABLE` or `INSUFFICIENT_EVIDENCE` |
| conflicting evidence | emit `CONFLICTING_EVIDENCE` risk flag + `INSUFFICIENT_EVIDENCE` or `ABSTAIN` |
| malformed normalized input | `FAIL_CLOSED` and/or `PROPAGATE_EXISTING_PIPELINE_FAILURE` |
| unsupported security | `NOT_EVALUABLE` |
| partial watchlist | degrade evaluation state; never invent membership |
| upstream stage failure | `PROPAGATE_EXISTING_PIPELINE_FAILURE` and/or `STAGE_FAILURE_PRESENT` risk flag |

### Hard rules

1. Failure MUST NOT invent analysis.
2. Failure MUST NOT create trade authority.
3. Silent malformed → valid evidence conversion is PROHIBITED.
4. Implicit execution action from failure is PROHIBITED.
5. Distinctions among input absence, insufficient evidence, invalid /
   malformed input, and explicit abstention MUST be preserved.

```text
FAILURE_MAPPING_POLICY = FROZEN
```

Additional machine-testable tie-break priority among dual-allowed cells
in the table above is `OPQ-03` if implementation requires a total order
beyond field-level completeness markers.

---

## 18. Persistence / Snapshot Contract Principles

```text
PERSISTENCE_STRATEGY =
  CO_PERSIST_TYPED_ANALYST_PUBLIC_SNAPSHOT_WITH_INTELLIGENCE_RUN
MIGRATION_AUTHORIZED = NO
RECOMPUTE_ON_READ = PROHIBITED
```

1. Analyst public snapshot MUST co-persist with the intelligence run.
2. Historical reads MUST return the stored snapshot.
3. Historical reads MUST NOT recompute analyst artifacts from current
   logic.
4. Version compatibility MUST be explicit.
5. Do **not** create a separate analyst database / service.
6. `snapshot_contract_version` expand / migration mechanics remain
   unauthorized and unresolved in detail (`OPQ-08`).
7. Analyst definition MUST NOT silently rewrite historical fingerprints
   without a later governed Policy / IA change.

---

## 19. Read / Exposure Contract

```text
WRITE_API_REQUIRED = NO
WRITE_API_AUTHORIZED = NO
READ_AUTH_SCOPE = intelligence:runs:read
```

Frozen read boundary principles:

1. Nested analyst DTO on Intelligence Run read.
2. Dedicated read-only analyst projection route patterned after existing
   dashboard / HR / ADE read routes.
3. Preferred route pattern (non-binding exact path pending `OPQ-07`):

```text
GET /intelligence/runs/.../analyst
```

4. No analyst / HR / ADE / broker mutation endpoints.
5. Untrusted catalyst / source text MUST be exposed inertly and safely.

Exact nested DTO field exposure set beyond §§7 / 11–16 concepts:
`OPQ-06`. Exact final path string: `OPQ-07`.

---

## 20. Payload / Validation Contract Principles

1. Canonical validation MUST reject prohibited vocabulary fields when
   present as semantic outputs.
2. Required identity / `as_of` / evaluation_state / provenance concepts
   MUST be present for a durable public snapshot claimed as
   `EVALUABLE` market-complete; incomplete claims MUST use explicit
   incompleteness markers / non-`EVALUABLE` states.
3. Payload bounds / size limits are **not** invented numerically here
   (`OPQ-04`). Future IA may adopt repository-standard payload limits
   already used by Intelligence Runs without inventing analyst-specific
   thresholds in this DRAFT.
4. Unsupported completeness thresholds MUST NOT be invented (`OPQ-05`).

```text
CANONICAL_VALIDATION_PRINCIPLES = FROZEN
NUMERIC_PAYLOAD_BOUNDS_INVENTED = NO
```

---

## 21. Security / Trust Contract

Policy preserves:

1. Untrusted source / catalyst text inert exposure
2. Safe serialization
3. Secret exclusion from logs and public DTOs
4. Authorization scope preservation (`intelligence:runs:read` unless
   separately authorized)
5. Injection resistance
6. Future UI safe-rendering constraints (UI still unauthorized)

```text
NEW_DEPENDENCY_AUTHORIZED = NO
NEW_SECRET_AUTHORIZED = NO
NEW_PROVIDER_AUTHORIZED = NO
NEW_INFRASTRUCTURE_AUTHORIZED = NO
```

---

## 22. Dependency / Provider / Feature Platform Firewall

```text
FEATURE_PLATFORM_HARD_DEPENDENCY = NO
FEATURE_PLATFORM_EXPANSION_REQUIRED = NO
FEATURE_PLATFORM_EXPANSION_AUTHORIZED = NO
THIRD_PARTY_DEPENDENCY_ADDITION_AUTHORIZED = NO
NEW_PROVIDER_AUTHORIZED = NO
```

Hidden feature store, online store, scheduler, freshness service,
provider expansion, or parity expansion is PROHIBITED.

---

## 23. Authority Separation / ADE / HR Firewall

1. Analyst artifact MUST NOT become an input to ADE decision logic in
   this bounded slice.
2. Analyst artifact MUST NOT become an input to Human Review decision
   logic in this bounded slice.
3. ADE behavior MUST remain UNCHANGED.
4. Human Review behavior MUST remain UNCHANGED.
5. Analytical output grants no downstream trade / order / broker /
   portfolio authority.
6. Any future coupling REQUIRES a separate governed lifecycle.

```text
ADE_BEHAVIOR_CHANGE_REQUIRED = NO
HR_BEHAVIOR_CHANGE_REQUIRED = NO
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED/DEFERRED
PRODUCTION_DEPLOYMENT = NOT_AUTHORIZED
```

---

## 24. UI / Presentation Boundary

Future presentation (unauthorized by this Policy) MUST preserve:

- non-advice semantics
- evaluation-state semantics
- descriptive risk semantics
- provenance
- freshness / `as_of`

```text
UI_IMPLEMENTATION_AUTHORIZED = NO
UI_UX_IMPLEMENTATION_AUTHORIZED = NO
```

---

## 25. Change Management

| Change class | Required gates |
| --- | --- |
| New analyst field / changed field semantics | Architecture + Governance (+ Policy if mechanical) |
| Evaluation-state semantic change | Architecture + Governance + Policy |
| PIT semantic change | Architecture + Governance + Policy |
| Identity / provenance change | Architecture + Governance (+ Policy if mechanical) |
| New risk category | Architecture + Governance |
| Severity vocabulary | Policy under Governance ownership decision B + explicit evidence |
| Persistence / snapshot / migration | Architecture impact + Governance + Policy + IA |
| Write API | Full new governed lifecycle |
| HR / ADE input coupling | Full new governed lifecycle |
| Model | Full new governed lifecycle |
| New provider | Full new governed lifecycle |
| Feature Platform dependency | Full new governed lifecycle |
| Broker semantics | Full new governed lifecycle |

```text
POLICY_EXCEPTION_MODEL = NO_IMPLICIT_EXCEPTION_FOR_HARD_FIREWALLS
```

Hard firewalls that MUST NOT be weakened by implicit exception:

- model
- broker
- production
- execution semantics
- write API

---

## 26. Audit / Replay / Test Obligations

Future implementation evidence (when IA authorizes implementation) MUST
include, as applicable:

1. definition version pinning
2. input provenance reconstruction
3. run identity + UTC `as_of`
4. canonical hashes / equality
5. replay equality (same inputs + definition + code)
6. PIT / no-lookahead proofs
7. authority-firewall tests
8. non-advice / prohibited-vocabulary tests
9. evaluation-state non-equivalence tests
10. fail-closed / abstention mapping tests
11. read-only API tests
12. migration compatibility evidence if migration is later authorized

No implementation or test-code work is authorized by this DRAFT.

```text
POLICY_CONFORMANCE_TEST_OBLIGATIONS = RECORDED
IMPLEMENTATION_AUTHORIZED = NO
```

---

## 27. Policy Decisions

| ID | Decision | Freeze |
| --- | --- | --- |
| PD-01 | Scope = Architecture five-capability slice only | FROZEN |
| PD-02 | Artifact envelope concepts per §7 | FROZEN |
| PD-03 | UTC `as_of` + determinism / replay equality | FROZEN |
| PD-04 | PIT / no-lookahead; no invented numeric staleness thresholds | FROZEN |
| PD-05 | Identity / provenance participation rules | FROZEN |
| PD-06 | Market summary required/prohibited concepts | FROZEN |
| PD-07 | Catalyst summary CatalystRecord-derived required/prohibited concepts | FROZEN |
| PD-08 | Structured thesis required concepts + prohibition vocabulary | FROZEN |
| PD-09 | Informational invalidation prohibition vocabulary | FROZEN |
| PD-10 | Risk-flag categories exact; severity NOT frozen in v1 | FROZEN |
| PD-11 | Evaluation states exact; artifact-level required; per-thesis optional | FROZEN |
| PD-12 | Failure / abstention condition mapping table §17 | FROZEN |
| PD-13 | Co-persist; no recompute-on-read; migration unauthorized | FROZEN |
| PD-14 | Read-only nested DTO + dedicated read route principles; write API NO | FROZEN |
| PD-15 | Auth scope remains `intelligence:runs:read` unless separately authorized | FROZEN |
| PD-16 | ADE/HR unchanged; no analyst→decision coupling | FROZEN |
| PD-17 | Model / broker / production / FP / UI / dependency firewalls | FROZEN |
| PD-18 | Change management + no implicit hard-firewall exceptions | FROZEN |
| PD-19 | Policy conformance test obligations recorded; IA still required | FROZEN |
| PD-20 | Unresolved human choices remain OPEN (`OPQ-01`…`OPQ-08`); no silent invention | FROZEN |

```text
POLICY_DECISION_COUNT = 20
```

---

## 28. Open Policy Questions

These require explicit human Policy review / evidence. This DRAFT MUST
NOT invent answers.

| ID | Question | Constraint |
| --- | --- | --- |
| OPQ-01 | Whether any risk-flag severity vocabulary is justified; if yes, exact terms | Do not invent LOW/MEDIUM/HIGH |
| OPQ-02 | Additional evaluation-state transition automata beyond §16–§17 | Preserve non-equivalence |
| OPQ-03 | Total-order tie-break among dual-allowed failure mappings | Must remain fail-closed / non-inventive |
| OPQ-04 | Exact numeric payload bounds specific to analyst artifacts | Prefer reuse of existing run limits under IA |
| OPQ-05 | Exact completeness / staleness numeric thresholds (if any) | Reuse upstream Premarket semantics; do not invent |
| OPQ-06 | Exact nested analyst DTO field exposure set / code-level names | Concepts frozen in §§7 / 11–16 |
| OPQ-07 | Exact final read-only analyst route path string | Pattern frozen; final string open |
| OPQ-08 | Exact `snapshot_contract_version` expand / migration mechanics | Migration still unauthorized |

```text
OPEN_POLICY_QUESTION_COUNT = 8
```

---

## 29. Traceability Matrix

### Architecture → Governance → Policy

| Architecture | Governance | Policy |
| --- | --- | --- |
| AD five-capability scope | GOV-01 / GD-02 | §5 / PD-01 |
| Artifact envelope | GOV-05 / GD-13 | §7 / PD-02 |
| Determinism | GOV-03 / GD-04 | §8 / PD-03 |
| PIT | GOV-04 / GD-05 | §9 / PD-04 |
| Market summary | GOV-06 / GD-06 | §11 / PD-06 |
| Catalyst summary | GOV-07 / GD-07 | §12 / PD-07 |
| Structured thesis | GOV-08 / GD-08 | §13 / PD-08 |
| Informational invalidation | GOV-09 / GD-09 | §14 / PD-09 |
| Risk flags | GOV-10 / GD-10 | §15 / PD-10 |
| Evaluation states | GOV-11 / GD-11 | §16 / PD-11 |
| Failure model | GOV-12 / GD-12 | §17 / PD-12 |
| Persistence | GOV-13 / GD-14 | §18 / PD-13 |
| Read exposure | GOV-14 / GD-15 | §19 / PD-14 |
| Security / trust | GOV-15 | §21 |
| Authority separation | GOV-16 / GD-16 | §23 / PD-16 |
| FP / model / broker / production | GOV-17…20 / GD-17…20 | §22–§23 / PD-17 |
| UI boundary | GOV-21 | §24 |
| Dependency / provider | GOV-22 | §22 |
| Change / exception | GOV-23 / GOV-24 / GD-21 | §25 / PD-18 |
| Auditability | GOV-25 | §26 / PD-19 |
| Policy / IA boundary | GOV-26 / GD-22 | §30 / PD-19 |

### Issue #184 Acceptance Criteria Coverage

| AC | Coverage |
| --- | --- |
| AC-01 | §4 predecessors |
| AC-02 | §5–§6 |
| AC-03 | §7, §11–§16 |
| AC-04 | §8 |
| AC-05 | §9 |
| AC-06 | §10 |
| AC-07 | §16 |
| AC-08 | §17 |
| AC-09 | §14 |
| AC-10 | §15 |
| AC-11 | §18 |
| AC-12 | §19 |
| AC-13 | §20 |
| AC-14 | §21 |
| AC-15 | §22 |
| AC-16 | §23–§24 |
| AC-17 | §23 |
| AC-18 | §25 |
| AC-19 | §28 |
| AC-20 | §1 banners / §30 |
| AC-21 | §26 |
| AC-22 | §5–§6 / PD-01 |

```text
AC_COVERAGE_COUNT = 22 / 22
```

Do **not** mark Issue ACs product-PASS merely because this DRAFT exists.
Candidate remains DRAFT until review / merge / finality.

---

## 30. Policy Decision / Next Gate

```text
POLICY_DECISION = ADVANCE_TO_IMPLEMENTATION_AUTHORIZATION_GATE
NEXT_RECOMMENDED_GATE = Premarket Analyst Bounded Slice Implementation Authorization Gate
NEXT_GATE_AUTHORIZED = NO
IMPLEMENTATION_AUTHORIZATION_GATE_AUTHORIZED = NO
PREMARKET_ANALYST_PRODUCT_IMPLEMENTATION_AUTHORIZED = NO
```

Policy candidate creation is **not** Policy finality.

---

## 31. Authority Firewall

```text
PREMARKET_ANALYST_PRODUCT_IMPLEMENTATION_AUTHORIZED = NO
IMPLEMENTATION_AUTHORIZATION_GATE_AUTHORIZED = NO
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED/DEFERRED
PRODUCTION_DEPLOYMENT = NOT_AUTHORIZED
FEATURE_PLATFORM_EXPANSION_AUTHORIZED = NO
UI_UX_IMPLEMENTATION_AUTHORIZED = NO
THIRD_PARTY_DEPENDENCY_ADDITION_AUTHORIZED = NO
MIGRATION_AUTHORIZED = NO
WRITE_API_AUTHORIZED = NO
TAG_RELEASE_AUTHORIZED = NO
NEW_DEPENDENCY_AUTHORIZED = NO
NEW_SECRET_AUTHORIZED = NO
NEW_PROVIDER_AUTHORIZED = NO
NEW_INFRASTRUCTURE_AUTHORIZED = NO
ADE_BEHAVIOR_CHANGE_REQUIRED = NO
HR_BEHAVIOR_CHANGE_REQUIRED = NO
COMMIT_AUTHORIZED = NO
PUSH_AUTHORIZED = NO
PR_CREATION_AUTHORIZED = NO
```

---

## 32. Next Gate

```text
NEXT_GATE = Premarket Analyst Bounded Slice Implementation Authorization Gate
NEXT_GATE_AUTHORIZED = NO
PROCESS_STATE_AFTER_POLICY_APPROVED_FROZEN =
  PREMARKET_ANALYST_IA_GATE_ELIGIBLE_NOT_AUTHORIZED
```

Required lifecycle:

```text
Architecture (COMPLETE)
  → Governance (COMPLETE)
  → Policy / Contract (this DRAFT candidate)
  → Implementation Authorization
  → bounded implementation workstreams
```

This DRAFT candidate stops at independent review before commit.
No IA issue creation is authorized by this artifact alone.
