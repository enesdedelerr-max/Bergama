# Intelligence Run Productization Governance v1

**Governance ID:** `intelligence-run-productization.governance.v1`  
**Status:** DRAFT  
**Sprint:** 14  
**Gate:** Governance Gate  
**Issue:** [#140](https://github.com/enesdedelerr-max/Bergama/issues/140)  
**Theme:** Durable Intelligence Run Persistence and Read/Query Boundary  
**Planning Gate:** Issue [#136](https://github.com/enesdedelerr-max/Bergama/issues/136) / PR [#137](https://github.com/enesdedelerr-max/Bergama/pull/137) — `sprint-14.planning-gate`  
**Architecture Gate:** Issue [#138](https://github.com/enesdedelerr-max/Bergama/issues/138) / PR [#139](https://github.com/enesdedelerr-max/Bergama/pull/139)  
**Architecture:** `intelligence-run-productization.architecture.v1`  
**Authoritative main at draft:** `2390e4fbe56e8026d62ab4aece7137672d3ee15f`  
**Document class:** Governance Gate only — not Policy Freeze, not Implementation Authorization

```text
SPRINT_14_PLANNING_GATE_ESTABLISHED = YES
SPRINT_14_ARCHITECTURE_GATE_ESTABLISHED = YES
SPRINT_14_GOVERNANCE_GATE_STATUS = DRAFT
SPRINT_14_POLICY_CONTRACT_FREEZE_STARTED = NO
SPRINT_14_IMPLEMENTATION_AUTHORIZED = NO
NEW_INFRASTRUCTURE_AUTHORIZED = NO
NEW_DEPENDENCY_AUTHORIZED = NO
DATABASE_MIGRATION_AUTHORIZED = NO
DATABASE_SCHEMA_IMPLEMENTATION_AUTHORIZED = NO
REPOSITORY_IMPLEMENTATION_AUTHORIZED = NO
MATERIALIZER_IMPLEMENTATION_AUTHORIZED = NO
QUERY_SERVICE_IMPLEMENTATION_AUTHORIZED = NO
HTTP_ENDPOINT_IMPLEMENTATION_AUTHORIZED = NO
WRITE_API_AUTHORIZED = NO
UI_AUTHORIZED = NO
FEATURE_PLATFORM_CHANGE_AUTHORIZED = NO
LIVE_PROVIDER_EXPANSION_AUTHORIZED = NO
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED/DEFERRED
TAG_RELEASE_DEPLOY_AUTHORIZED = NO
```

---

## 1. Purpose

Govern how authoritative completed Intelligence Pipeline runs may cross from
the in-process intelligence boundary into durable product persistence and
authenticated read/query surfaces without transferring or expanding decision
authority.

Governance defines **invariant authority and safety boundaries**.

Governance does **not** authorize implementation.

Governance does **not** define every DTO field, HTTP body, database column, or
dependency version.

Those exact behavioral/public contracts belong to the later combined
Productization Policy / Contract Freeze. Permission to implement belongs to
later Implementation Authorization.

---

## 2. Governance / Policy / Implementation Separation

| Layer | Owns |
| --- | --- |
| Governance Gate (this document) | Invariant authority and safety rules |
| Combined Productization Policy / Contract Freeze | Exact public behavioral contracts (DTOs, HTTP shapes, scope string, version constants, selectors, error bodies) |
| Implementation Authorization | Permission to install dependencies, create schema/migrations, repositories, materializer, query service, HTTP routers, auth wiring, and tests |

---

## 3. Persistence Admission

```text
PERSISTENCE_ADMISSION_RESOLVED = YES
PIPELINE_OUTCOME_COUNT = 6
FAILED_RUNS_PERSISTABLE = YES
ADMISSION_REJECTED_RUNS_PERSISTABLE = YES
```

A persistable authoritative run must originate from a completed public
`PipelineResult` and preserve:

- one frozen UTC `as_of`
- deterministic `pipeline_fingerprint`
- frozen policy / config / binding pins
- exactly one Sprint 13 `PipelineOutcome`
- bounded public provenance
- explicit stage-presence semantics
- versioned public snapshot contract

All six Sprint 13 outcomes remain persistable and queryable for durable audit
by direct identity:

1. `admission_rejected`
2. `required_stage_failed`
3. `completed_dashboard`
4. `completed_human_review`
5. `completed_ade_accept`
6. `completed_ade_abstain`

No seventh `PipelineOutcome` may be invented for persistence, query, HTTP,
authentication, authorization, or transport failures.

---

## 4. Immutability / Materialization

```text
IMMUTABILITY_REQUIRED = YES
IDENTITY_CONFLICT_FAIL_CLOSED = YES
```

Durable Intelligence Run product truth is immutable / append-oriented.

No silent `UPDATE` or `DELETE` semantics may rewrite an authoritative run.

For the same `(pipeline_fingerprint, snapshot_contract_version)`:

1. Compare **canonical authoritative snapshot content** only.
2. If equal → reuse / return the existing durable record.
3. If unequal → fail closed as materialization identity conflict.

Canonical equality **MUST exclude**:

- `run_id`
- `persisted_at`
- database internal metadata
- ORM / session state
- response-derived `age_seconds`

Governance owns this invariant. Exact canonical serialization belongs to
Productization Policy / Contract Freeze. Implementation mechanics belong to
Implementation Authorization.

---

## 5. Snapshot Boundary

### REQUIRED persisted public boundary

- durable run envelope
- `PipelineOutcome`
- `as_of`
- `pipeline_fingerprint`
- policy / config / binding pins
- bounded failure metadata where applicable
- thin provenance
- stage presence / status
- `snapshot_contract_version`
- `persistence_schema_version`
- Dashboard public snapshot when present

### CONDITIONAL public boundary

**Human Review** (when HR ran):

- public HR snapshot
- bounded attestation identity / fingerprint / presence
- already-public policy / identity references

**ADE** (when ADE ran):

- bounded public ADE result
- preserve public outcome / reason / identity / provenance fields
- preserve accept versus abstain

### Deferred

```text
INTERMEDIATE_STAGE_FULL_SNAPSHOTS = DEFERRED
```

Do not persist full Watchlist / Gap / Catalyst / Score / Briefing payloads in
Sprint 14 unless a later separately governed change explicitly authorizes them.

---

## 6. Forbidden Persistence

Governance explicitly prohibits persistence or product read exposure of:

- raw provider payloads
- unbounded provider data
- unbounded news / event dumps
- full exception stack traces
- credentials
- secrets
- tokens
- internal ORM / session objects
- private model internals
- model-private evidence
- unnecessary duplicated evidence
- query-time recomputed intelligence
- generic ungoverned raw JSON passthrough

---

## 7. No-Recomputation

```text
QUERY_TIME_RECOMPUTATION_ALLOWED = NO
DERIVED_AGE_SECONDS_ALLOWED = YES
```

Read / query surfaces return persisted authoritative public snapshots.

They **MUST NOT** rerun:

- Intelligence Pipeline
- Watchlist
- Gap
- Catalyst
- Score
- Briefing
- Dashboard
- Human Review
- ADE

They **MUST NOT**:

- reinterpret terminal outcome
- rewrite `as_of`
- rewrite `pipeline_fingerprint`
- rewrite pins
- fabricate missing stages

`age_seconds` **MAY** be computed at read time only as explicitly
non-authoritative response metadata. It remains excluded from fingerprint and
canonical equality. Whether it appears in the public response belongs to
Productization Policy / Contract Freeze.

---

## 8. Six Outcome Preservation

Preserve exactly:

1. `admission_rejected`
2. `required_stage_failed`
3. `completed_dashboard`
4. `completed_human_review`
5. `completed_ade_accept`
6. `completed_ade_abstain`

Preserve distinctions among:

- failure
- empty success
- valid absence
- abstention
- terminal completion

The following **MUST NOT** become a seventh `PipelineOutcome`:

- persistence failure
- identity conflict
- DB unavailable
- query failure
- not found
- unsupported contract
- corrupt snapshot
- authentication failure
- authorization failure
- HTTP / transport failure

These remain separate productization / storage / query / auth / transport
errors.

---

## 9. Identity Governance

Architecture roles preserved:

| Identifier | Role |
| --- | --- |
| `run_id` | Opaque application-generated UUID4 durable storage identity |
| `pipeline_fingerprint` | Sprint 13 deterministic composition identity |

Governance rules:

- `run_id` does not replace fingerprint identity.
- `run_id` does not encode authority or business meaning.
- Persistence must not rewrite fingerprint semantics.
- Storage metadata must not enter fingerprint.
- Default fingerprint lookup resolves against the current supported
  `snapshot_contract_version`.
- Cross-version ambiguity must fail closed or require explicit
  contract-version selection under the later Policy / Contract Freeze.

---

## 10. Read / Query Authority

Preserve six Architecture GET-only route families:

1. `GET /api/v1/intelligence/runs/id/{run_id}`
2. `GET /api/v1/intelligence/runs/fingerprint/{fingerprint}`
3. `GET /api/v1/intelligence/runs/latest-dashboard-capable`
4. `GET /api/v1/intelligence/runs/id/{run_id}/dashboard`
5. `GET /api/v1/intelligence/runs/id/{run_id}/human-review`
6. `GET /api/v1/intelligence/runs/id/{run_id}/ade`

```text
HTTP_READ_ROUTE_FAMILY_COUNT = 6
```

Governance invariants for all six:

- read-only
- authentication required
- authorization required
- no mutation
- no pipeline trigger
- no Human Review submission
- no ADE invocation
- no configuration mutation
- no replay trigger
- no model invocation
- no broker / order action

Architecture owns route families. Productization Policy / Contract Freeze owns
exact response contracts.

---

## 11. Latest Dashboard Governance

Preserve deterministic ordering:

1. `as_of DESC`
2. `persisted_at DESC`
3. `run_id ASC`

Governance eligibility invariant:

Only runs with a persisted Dashboard public snapshot are eligible for
`latest-dashboard-capable`.

`admission_rejected` and `required_stage_failed` remain queryable by direct
identity but are not eligible without Dashboard presence.

`completed_human_review` and ADE terminal runs remain eligible when their
Dashboard snapshot is retained.

No query-time reranking or recomputation.

Exact eligibility predicate serialization belongs to Productization Policy /
Contract Freeze.

---

## 12. Human Review Governance

```text
HUMAN_REVIEW_WRITE_WORKFLOW = DEFERRED
HUMAN_REVIEW_WRITE_UI = NOT_AUTHORIZED
```

Sprint 14 permits read visibility of existing public Human Review output only.

No:

- capture endpoint
- submit endpoint
- write endpoint
- new HR authority
- attestation fabrication
- HR rerun on read

Persist only bounded public HR / attestation metadata when HR actually ran.
Exact absence representation belongs to Productization Policy / Contract Freeze.

---

## 13. ADE Governance

Sprint 14 ADE authority is visibility / read only.

Persist / read only bounded public ADE results already produced by the
completed run.

Preserve accept versus abstain.

No ADE invocation from read / query APIs.

No reinterpretation.

No model participation.

No autonomous decision authority.

No broker / order authority transfer.

```text
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED/DEFERRED
```

---

## 14. Authentication / Authorization

```text
DEDICATED_PRODUCT_READ_AUTHORIZATION_REQUIRED = YES
EXACT_AUTHORIZATION_SCOPE_OWNER = POLICY_CONTRACT
```

Every Intelligence Run product read route requires:

- authenticated principal
- dedicated least-privilege product read authorization

Reuse existing Bearer JWT + `AuthenticatedPrincipal` architecture.

Do not create a new IAM platform.

The exact stable authorization scope string and exact role-to-scope bindings
belong to Productization Policy / Contract Freeze.

---

## 15. Security / Data Minimization

Freeze:

- public DTO boundary only
- no ORM entity leakage
- bounded failure detail
- no stack traces
- no secrets / tokens / credentials
- no raw provider dumps
- no unbounded news
- no private model internals
- no unnecessary evidence duplication
- authorization before protected product data access
- opaque `run_id`
- contract-version validation
- no generic raw JSON passthrough

Encryption / retention are not newly introduced Sprint 14 governance
requirements unless a broader repository policy already mandates them.

---

## 16. Failure / Error Separation

| Concern class | Meaning |
| --- | --- |
| `PipelineOutcome` | Sprint 13 terminal intelligence outcome |
| Productization errors | identity conflict; corrupt stored snapshot; unsupported snapshot contract; DB unavailable |
| Query errors | record not found; HR valid absence; ADE valid absence |
| Auth errors | unauthenticated; unauthorized |
| Transport errors | HTTP concerns |

None may mutate or replace `PipelineOutcome`.

Identity conflict / corrupt snapshot / unsupported contract fail closed.

Exact HTTP status codes and response bodies belong to the combined
Productization Policy / Contract Freeze.

---

## 17. Version / Migration Governance

Durable records must carry:

- `snapshot_contract_version`
- `persistence_schema_version`

Governance principles:

- version-aware historical reads
- unsupported versions fail closed as productization errors
- expand / contract migration discipline
- no destructive silent reinterpretation
- fresh-database migration validation later
- existing-data compatibility validation where applicable
- rollback / compatibility discipline

This document does **not** authorize Alembic or migrations.

---

## 18. Dependency Governance

Proposed dependency set (Architecture; still unauthorized):

1. SQLAlchemy 2.x
2. Alembic
3. psycopg 3 sync

```text
PROPOSED_NEW_DEPENDENCY_COUNT = 3
NEW_DEPENDENCY_AUTHORIZED = NO
```

Governance principles:

- minimal direct dependencies
- controlled / pinned versions later
- license compatibility review
- CVE / supply-chain review
- lockfile update under later authorization
- no redundant ORM / driver
- no UUID helper dependency
- no `asyncpg` unless Architecture is separately amended
- no new database technology

---

## 19. Feature Platform / Provider Firewall

```text
FEATURE_PLATFORM_CHANGE_REQUIRED_FOR_SPRINT_14 = NO
FEATURE_PLATFORM_CHANGE_AUTHORIZED = NO
LIVE_PROVIDER_EXPANSION_REQUIRED = NO
LIVE_PROVIDER_EXPANSION_AUTHORIZED = NO
```

Sprint 14 persistence consumes completed public Intelligence Pipeline outputs.
It must not mutate Feature Platform or add live-provider access.

---

## 20. UI Firewall

```text
UI_REQUIRED_IN_SPRINT_14 = NO
UI_AUTHORIZED = NO
PREMARKET_COMMAND_CENTER_UI_READINESS_AFTER_SPRINT14 = YES
ADE_VISIBILITY_UI_READINESS_AFTER_SPRINT14 = YES
HUMAN_REVIEW_WRITE_UI_READINESS_AFTER_SPRINT14 = NO
```

These readiness statements are eligibility after full Sprint 14 completion,
not current UI authorization.

---

## 21. Auditability / Provenance

Minimum durable audit context:

- `run_id`
- `pipeline_fingerprint`
- `as_of`
- `PipelineOutcome`
- `failed_stage` where applicable
- bounded failure metadata
- policy / config / binding pins
- thin provenance
- `snapshot_contract_version`
- `persistence_schema_version`
- `persisted_at`
- stage presence / status
- Dashboard snapshot presence
- HR snapshot / attestation presence when applicable
- ADE result presence when applicable

`persisted_at` is storage audit metadata. It is **not** composition identity.
It is excluded from fingerprint and canonical equality.

---

## 22. Policy / Contract Handoff

```text
PRODUCTIZATION_POLICY_CONTRACT_FREEZE_MODE = COMBINED
```

The next gate after Governance establishment is a combined Productization
Policy / Contract Freeze.

That later gate owns at minimum:

- exact persisted DTO schemas
- exact HTTP DTO schemas
- exact snapshot contract version constant
- exact persistence schema contract / version
- exact stage-presence serialized labels
- exact HR / ADE absence behavior
- exact HTTP error codes / bodies
- exact authorization scope string
- exact role / scope mappings
- fingerprint historical-version selector contract
- latest-dashboard exact eligibility representation
- freshness / `age_seconds` response shape
- bounded `failure_detail` schema
- corrupt / unsupported snapshot response contracts

History listing remains **DEFERRED** unless separately reopened.

---

## 23. Future Implementation Decomposition

```text
PROPOSED_FUTURE_IMPLEMENTATION_ISSUE_COUNT = 4
```

Recorded sequence (not authorized by this document):

1. Intelligence run persistence schema / repository / migrations
2. Pipeline durable materialization / snapshot integration
3. Read / query service + versioned HTTP GET API
4. Contract / retrieval determinism / authz / authority-firewall hardening

All require later:

- Governance establishment
- combined Policy / Contract Freeze
- Implementation Authorization

---

## 24. Acceptance Criteria

| ID | Criterion |
| --- | --- |
| AC-01 | Governance purpose and authority boundary frozen |
| AC-02 | Completed public `PipelineResult` admission required |
| AC-03 | Frozen UTC `as_of` preservation required |
| AC-04 | Fingerprint and pin preservation required |
| AC-05 | Exactly six `PipelineOutcome` families preserved |
| AC-06 | Failed runs remain persistable and queryable by direct identity |
| AC-07 | Admission-rejected runs remain persistable and queryable by direct identity |
| AC-08 | Durable truth is immutable / append-oriented |
| AC-09 | Canonical equal materialization reuses existing durable record |
| AC-10 | Canonical unequal materialization fails closed |
| AC-11 | Storage and response-derived metadata excluded from canonical equality |
| AC-12 | Required public snapshot boundary frozen |
| AC-13 | Conditional Human Review public boundary frozen |
| AC-14 | Conditional ADE public boundary frozen |
| AC-15 | Intermediate full stage snapshots deferred |
| AC-16 | Forbidden / raw / private persistence classes prohibited |
| AC-17 | Query-time intelligence recomputation prohibited |
| AC-18 | `age_seconds` allowed only as non-authoritative derived metadata |
| AC-19 | Six GET-only route families preserved |
| AC-20 | Authentication required on all Intelligence Run product read routes |
| AC-21 | Dedicated least-privilege product read authorization required |
| AC-22 | Latest-dashboard-capable deterministic ordering preserved |
| AC-23 | Latest-dashboard-capable eligibility requires Dashboard presence |
| AC-24 | Human Review write workflow deferred |
| AC-25 | ADE visibility-only; no invocation from product read surfaces |
| AC-26 | Model participation unauthorized |
| AC-27 | Broker execution denied / deferred |
| AC-28 | Feature Platform mutation unauthorized |
| AC-29 | Live-provider expansion unauthorized |
| AC-30 | UI unauthorized in Sprint 14 |
| AC-31 | Product / storage / query / auth / transport errors remain separate from `PipelineOutcome` |
| AC-32 | Snapshot and persistence version governance required |
| AC-33 | Migration compatibility principles frozen |
| AC-34 | Dependency admission principles recorded; three proposed dependencies remain unauthorized |
| AC-35 | Durable auditability / provenance minimum frozen |
| AC-36 | Combined Policy / Contract handoff frozen; implementation remains unauthorized |

```text
GOVERNANCE_AC_COUNT = 36
```

No implementation acceptance criteria are defined by this document.

---

## 25. Open Questions (non-blocking handoff)

| # | Question | Owner | Status |
| --- | --- | --- | --- |
| 1 | Exact authorization scope string | Productization Policy / Contract Freeze | Open |
| 2 | Exact role-to-scope bindings | Productization Policy / Contract Freeze | Open |
| 3 | HR / ADE absence HTTP representation | Productization Policy / Contract Freeze | Open |
| 4 | Exact snapshot / HTTP DTO fields | Policy / Contract + later implementation | Open |
| 5 | Exact version constant values | Policy / Contract + Implementation Authorization | Open |
| 6 | Exact Alembic / migration mechanics | Implementation Authorization | Open |
| 7 | History listing | Deferred unless separately reopened | Deferred |

Do **not** reopen:

- UUID4 durable `run_id`
- sync SQLAlchemy / psycopg architecture
- six GET route families
- latest-dashboard-capable ordering
- combined Productization Policy / Contract Freeze
- intermediate snapshot deferral

---

## 26. Authority Firewall (restatement)

```text
SPRINT_14_PLANNING_GATE_ESTABLISHED = YES
SPRINT_14_ARCHITECTURE_GATE_ESTABLISHED = YES
SPRINT_14_GOVERNANCE_GATE_STATUS = DRAFT
SPRINT_14_POLICY_CONTRACT_FREEZE_STARTED = NO
SPRINT_14_IMPLEMENTATION_AUTHORIZED = NO
NEW_INFRASTRUCTURE_AUTHORIZED = NO
NEW_DEPENDENCY_AUTHORIZED = NO
DATABASE_MIGRATION_AUTHORIZED = NO
DATABASE_SCHEMA_IMPLEMENTATION_AUTHORIZED = NO
REPOSITORY_IMPLEMENTATION_AUTHORIZED = NO
MATERIALIZER_IMPLEMENTATION_AUTHORIZED = NO
QUERY_SERVICE_IMPLEMENTATION_AUTHORIZED = NO
HTTP_ENDPOINT_IMPLEMENTATION_AUTHORIZED = NO
WRITE_API_AUTHORIZED = NO
UI_AUTHORIZED = NO
FEATURE_PLATFORM_CHANGE_AUTHORIZED = NO
LIVE_PROVIDER_EXPANSION_AUTHORIZED = NO
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED/DEFERRED
TAG_RELEASE_DEPLOY_AUTHORIZED = NO
```

---

## 27. Next Step

Independently review this DRAFT Governance Gate.

Do not begin Productization Policy / Contract Freeze or implementation until
the required governance sequence authorizes those later steps.
