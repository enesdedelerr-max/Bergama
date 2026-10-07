# Intelligence Run Productization Policy / Contract v1

**Policy ID:** `intelligence-run-productization.policy.v1`  
**Version:** v1  
**Title:** Intelligence Run Productization Policy / Contract Freeze v1  
**Status:** DRAFT  
**Document class:** Combined Productization Policy / Contract Freeze  
**Sprint:** 14  
**Gate:** Combined Productization Policy / Contract Freeze  
**Theme:** Durable Intelligence Run Persistence and Read/Query Boundary  
**Policy issue:** [#142](https://github.com/enesdedelerr-max/Bergama/issues/142)  
**Predecessor Planning:** Issue [#136](https://github.com/enesdedelerr-max/Bergama/issues/136) / PR [#137](https://github.com/enesdedelerr-max/Bergama/pull/137)  
**Predecessor Architecture:** Issue [#138](https://github.com/enesdedelerr-max/Bergama/issues/138) / PR [#139](https://github.com/enesdedelerr-max/Bergama/pull/139) — `intelligence-run-productization.architecture.v1`  
**Predecessor Governance:** Issue [#140](https://github.com/enesdedelerr-max/Bergama/issues/140) / PR [#141](https://github.com/enesdedelerr-max/Bergama/pull/141) — `intelligence-run-productization.governance.v1`  
**Authoritative main at draft:** `9d2882437d585d5725226e849621f20e6ad3dc4b`

```text
POLICY APPROVAL ≠ IMPLEMENTATION AUTHORIZATION
POLICY APPROVAL ≠ IMPLEMENTATION
SPRINT_14_PLANNING_GATE_ESTABLISHED = YES
SPRINT_14_ARCHITECTURE_GATE_ESTABLISHED = YES
SPRINT_14_GOVERNANCE_GATE_ESTABLISHED = YES
SPRINT_14_PRODUCTIZATION_POLICY_CONTRACT_FREEZE_STATUS = DRAFT
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

Freeze the public and durable product contract for authoritative completed
Intelligence Pipeline runs before Sprint 14 Implementation Authorization may
be considered.

This document freezes **productization semantics and contracts only**.

It does **not** authorize implementation, dependency installation, migrations,
repositories, materializers, query services, HTTP routers, auth wiring, UI,
Feature Platform mutation, live-provider expansion, model participation,
broker execution, tag, release, or deployment.

---

## 2. Authority Statement

| Layer | Owns |
| --- | --- |
| Planning / Architecture / Governance | Theme, architecture decisions, invariant authority |
| **This Policy / Contract Freeze** | Exact public behavioral contracts (DTOs, HTTP, versions, scopes, selectors, errors) |
| Implementation Authorization | Permission to implement under this freeze |

This Policy does **not** reopen Architecture decisions unless a later governed
correction explicitly amends Architecture.

---

## 3. Prerequisites

| Prerequisite | Process state |
| --- | --- |
| `sprint-14.planning-gate` | ESTABLISHED (#136 / #137) |
| `intelligence-run-productization.architecture.v1` | ESTABLISHED (#138 / #139) |
| `intelligence-run-productization.governance.v1` | ESTABLISHED (#140 / #141) |
| Authoritative main | `9d2882437d585d5725226e849621f20e6ad3dc4b` |
| Post-merge main CI | run `37553814315` / completed / success |

Referenced Sprint 13 authorities remain authoritative for composition
semantics and are not reopened by this document:

- `intelligence-pipeline.policy.v1`
- public `PipelineResult` / `PipelineOutcome` / stage public outputs

---

## 4. Six PipelineOutcome Contract

```text
PIPELINE_OUTCOME_COUNT = 6
```

Exact serialized values:

1. `admission_rejected`
2. `required_stage_failed`
3. `completed_dashboard`
4. `completed_human_review`
5. `completed_ade_accept`
6. `completed_ade_abstain`

All six outcomes are persistable and queryable by durable identity.

No persistence, storage, query, authentication, authorization, or HTTP /
transport error may invent a seventh `PipelineOutcome`.

---

## 5. Stage Presence Contract

```text
STAGE_PRESENCE_REPRESENTATION = enum_status_map
STAGE_KEY_COUNT = 8
STAGE_STATUS_VALUE_COUNT = 6
```

### Exact stage keys

1. `watchlist`
2. `gap`
3. `catalyst`
4. `score`
5. `briefing`
6. `dashboard`
7. `human_review`
8. `ade`

### Exact allowed status values

1. `NOT_EXECUTED`
2. `ABSENT`
3. `EMPTY`
4. `FAILED`
5. `PRESENT`
6. `ABSTAINED`

### Frozen distinctions

```text
NOT_EXECUTED ≠ ABSENT
ABSENT ≠ EMPTY
EMPTY ≠ FAILED
FAILED ≠ PRESENT
PRESENT ≠ ABSTAINED
```

No fabricated stage payloads. Stage status is productization metadata and is
**not** a `PipelineOutcome`.

### Outcome-to-stage-presence matrix

| Outcome | Core stages (`watchlist`→`briefing`) | `dashboard` | `human_review` | `ade` | Latest-dashboard-capable |
| --- | --- | --- | --- | --- | --- |
| `admission_rejected` | `NOT_EXECUTED` | `ABSENT` | `ABSENT` | `ABSENT` | NO |
| `required_stage_failed` | executed stages preserve `PRESENT` / `EMPTY` / `FAILED`; later stages `NOT_EXECUTED` | `PRESENT` only if Dashboard completed before a later optional failure; otherwise `FAILED` / `ABSENT` / `NOT_EXECUTED` as applicable | `ABSENT` unless HR completed | `ABSENT` unless ADE completed | YES **only if** Dashboard `PRESENT` with valid Dashboard snapshot |
| `completed_dashboard` | `PRESENT` / `EMPTY` as executed | `PRESENT` | `ABSENT` | `ABSENT` | YES |
| `completed_human_review` | `PRESENT` / `EMPTY` as executed | `PRESENT` | `PRESENT` | `ABSENT` | YES |
| `completed_ade_accept` | `PRESENT` / `EMPTY` as executed | `PRESENT` | `PRESENT` | `PRESENT` | YES |
| `completed_ade_abstain` | `PRESENT` / `EMPTY` as executed | `PRESENT` | `PRESENT` | `ABSTAINED` | YES |

---

## 6. Snapshot Contract

### REQUIRED / authoritative (when admitted / applicable)

- `pipeline_fingerprint`
- `as_of`
- `outcome`
- bindings / pins (`PipelineBindings` public fields)
- thin provenance (`PipelineProvenance` public fields)
- stage presence / status map
- `snapshot_contract_version`

### REQUIRED storage identity / metadata

- `run_id`
- `persistence_schema_version`
- `persisted_at`

### CONDITIONAL

- `failed_stage`
- `failure_error_type`
- `failure_detail`
- Dashboard public snapshot (when Dashboard present)
- Human Review public snapshot (when HR ran)
- ADE public result (when ADE ran)

### DERIVED

- `age_seconds` (read-time only; non-authoritative)

### DEFERRED

- full Watchlist payload
- full Gap payload
- full Catalyst payload
- full Score payload
- full Briefing payload

### FORBIDDEN

- raw `BarEvent` dumps
- raw `NewsEvent` dumps
- raw provider payloads
- temporary calculations
- raw exception objects
- stack traces
- secrets / tokens / credentials
- ORM entities / session state
- model-private state
- unbounded news content

### Nullability / absence

Optional / conditional fields that are validly absent MUST be omitted or
explicitly null according to the frozen versioned DTO schema for
`intelligence-run-productization.snapshot.v1`. Do not fabricate empty HR or
ADE snapshots to satisfy presence.

---

## 7. Version Constants

```text
SNAPSHOT_CONTRACT_VERSION = intelligence-run-productization.snapshot.v1
PERSISTENCE_SCHEMA_VERSION = intelligence-run-productization.persistence.v1
```

Frozen rules:

- stable lowercase dotted string representation
- exactly one current supported snapshot contract version for Sprint 14
- stored version governs decoding
- unsupported version fails closed
- no silent reinterpretation across versions
- historical explicit contract-version selector for fingerprint lookup is
  **DEFERRED**

---

## 8. Canonical Equality Contract

### MUST include when applicable

- `pipeline_fingerprint`
- `snapshot_contract_version`
- `as_of`
- `outcome`
- `failed_stage`
- `failure_error_type`
- `failure_detail`
- bindings / pins
- thin provenance
- stage-presence map
- Dashboard public snapshot
- Human Review public snapshot
- HR attestation presence / fingerprint
- ADE public snapshot / result

### MUST exclude exactly

- `run_id`
- `persisted_at`
- DB internal metadata
- ORM / session state
- `age_seconds`

### Canonicalization semantics

- deterministic object-key ordering
- authoritative list ordering preserved
- UTC-normalized timestamps
- enum string serialization
- stable optional / null semantics per DTO schema
- no fabricated empty HR / ADE snapshots

Digest algorithm MAY use SHA-256 over canonical bytes.

Do **not** transfer Strategy authority into this productization domain.
Fingerprint composition identity remains Sprint 13-owned; productization
equality compares the frozen authoritative product snapshot content.

---

## 9. Run ID Contract

```text
RUN_ID_FORMAT = UUID4
RUN_ID_GENERATION = APPLICATION_GENERATED
RUN_ID_SEMANTICS = OPAQUE
```

Public representation:

- RFC 4122 lowercase hyphenated string
- `8-4-4-4-12` form

No time semantics. No ordering / recency semantics. No business meaning. No
authority meaning.

Malformed `run_id` path parameter:

- HTTP `400`
- code `intelligence.runs.invalid_identifier`

---

## 10. Fingerprint Lookup Contract

Path representation:

- 64-character lowercase SHA-256 hex

Malformed fingerprint:

- HTTP `400`
- code `intelligence.runs.invalid_identifier`

Lookup defaults to the **current supported** `snapshot_contract_version` only.

```text
FINGERPRINT_HISTORICAL_VERSION_SELECTOR = DEFERRED
```

Current-version miss → `intelligence.runs.run_not_found` even if historical
rows exist under other contract versions.

Never arbitrarily select across contract versions.

---

## 11. Six Exact GET Routes

```text
HTTP_READ_ROUTE_FAMILY_COUNT = 6
```

1. `GET /api/v1/intelligence/runs/id/{run_id}`
2. `GET /api/v1/intelligence/runs/fingerprint/{fingerprint}`
3. `GET /api/v1/intelligence/runs/latest-dashboard-capable`
4. `GET /api/v1/intelligence/runs/id/{run_id}/dashboard`
5. `GET /api/v1/intelligence/runs/id/{run_id}/human-review`
6. `GET /api/v1/intelligence/runs/id/{run_id}/ade`

Forbidden in Sprint 14 productization:

- additional productization routes
- `POST` / `PUT` / `PATCH` / `DELETE`
- pipeline trigger
- HR submission / capture
- ADE invocation
- configuration mutation
- replay trigger
- model invocation
- broker / order action

---

## 12. Public DTO Families

Exact names:

1. `IntelligenceRunRead`
2. `IntelligenceRunDashboardRead`
3. `IntelligenceRunHumanReviewRead`
4. `IntelligenceRunAdeRead`
5. `ProductErrorResponse`

`ProductErrorResponse` fields:

- `code` (stable machine-readable)
- `message` (human-readable)
- `request_id`
- optional bounded `details`

Frozen boundary rules:

- ORM entities forbidden on the wire
- generic `Dict[str, Any]` forbidden as authoritative public contract
- stored JSON MUST validate into versioned DTOs on write **and** on read
- unknown fields fail closed
- nested HR / ADE content uses strict versioned snapshot DTO boundaries
  derived from existing public contracts

---

## 13. HTTP Absence and Error Semantics

### Absence

| Case | HTTP | code |
| --- | --- | --- |
| Run does not exist | `404` | `intelligence.runs.run_not_found` |
| Run exists; HR validly absent | `404` | `intelligence.runs.stage_not_present` |
| Run exists; ADE validly absent | `404` | `intelligence.runs.stage_not_present` |
| Stage expected by status/outcome but required snapshot missing/corrupt | `500` | `intelligence.runs.corrupt_persisted_snapshot` |

```text
HTTP_HR_VALID_ABSENCE_SEMANTICS = 404 intelligence.runs.stage_not_present
HTTP_ADE_VALID_ABSENCE_SEMANTICS = 404 intelligence.runs.stage_not_present
```

Do **not** use HTTP `204`.  
Do **not** use fabricated `200` empty payloads for valid absence.

### Unsupported snapshot contract

```text
UNSUPPORTED_SNAPSHOT_CONTRACT_HTTP_STATUS = 409
```

Retrieval of a stored run whose snapshot contract cannot be interpreted by
the current supported reader:

- HTTP `409 Conflict`
- code `intelligence.runs.unsupported_snapshot_contract`

Do not use HTTP `422` for this Sprint 14 contract.

### Product error taxonomy

```text
PRODUCT_ERROR_FAMILY_COUNT = 8
```

1. `intelligence.runs.run_not_found`
2. `intelligence.runs.stage_not_present`
3. `intelligence.runs.invalid_identifier`
4. `intelligence.runs.unsupported_snapshot_contract`
5. `intelligence.runs.corrupt_persisted_snapshot`
6. `intelligence.runs.materialization_identity_conflict`
7. `intelligence.runs.storage_unavailable`
8. `authz.insufficient_scope`

Existing `auth.*` errors remain owned by the authentication layer and are
not counted as new productization families.

No productization / storage / query / auth / transport error becomes a
`PipelineOutcome`. Storage / query infrastructure failure is **not**
`required_stage_failed` and must not invent a seventh `PipelineOutcome`.

### Public HTTP status mappings

| Error family | HTTP | Notes |
| --- | --- | --- |
| `intelligence.runs.invalid_identifier` | `400` | Malformed `run_id` or fingerprint |
| `intelligence.runs.run_not_found` | `404` | Missing run / no eligible latest |
| `intelligence.runs.stage_not_present` | `404` | Valid HR / ADE absence |
| `intelligence.runs.unsupported_snapshot_contract` | `409` | Stored contract unreadable by current reader |
| `authz.insufficient_scope` | `403` | Authenticated without `intelligence:runs:read` |
| missing / invalid authentication | `401` | Existing `auth.*` semantics |
| `intelligence.runs.corrupt_persisted_snapshot` | `500` | Expected snapshot missing / corrupt |
| `intelligence.runs.storage_unavailable` | `503` | Durable persistence / storage dependency unavailable on an authorized HTTP read / query boundary |

```text
STORAGE_UNAVAILABLE_ERROR_CODE = intelligence.runs.storage_unavailable
STORAGE_UNAVAILABLE_HTTP_STATUS = 503
```

`intelligence.runs.materialization_identity_conflict` is an **application /
materialization-layer** error. It has **no Sprint 14 public HTTP status**
because Sprint 14 authorizes no public materialization / write API.

```text
MATERIALIZATION_IDENTITY_CONFLICT_HTTP_MAPPING = NONE_NO_PUBLIC_WRITE_API
```

---

## 14. Failure Metadata Contract

Reuse Sprint 13 semantics:

- `failure_error_type`
- `failure_detail`

```text
FAILURE_DETAIL_MAX_LENGTH = 256
```

Rules:

- `failure_detail` MUST use existing bounded sanitization semantics
- no stack traces
- no raw exception objects
- no secret / token leakage
- `failure_error_type` MAY expose a bounded exception class / family
  consistent with current orchestrator behavior
- failure metadata participates in canonical equality when present

---

## 15. Latest-Dashboard-Capable Contract

Eligibility:

- Dashboard stage status MUST be `PRESENT`
- AND a valid Dashboard public snapshot MUST exist

HR / ADE terminal outcomes remain eligible when Dashboard is retained.

Ordering (exact):

1. `as_of DESC`
2. `persisted_at DESC`
3. `run_id ASC`

No eligible run:

- HTTP `404`
- code `intelligence.runs.run_not_found`
- bounded message indicating no dashboard-capable run

```text
LATEST_DASHBOARD_CAPABLE_CORRUPT_CANDIDATE_BEHAVIOR = FAIL_CLOSED_NO_SKIP
LATEST_DASHBOARD_CAPABLE_UNSUPPORTED_VERSION_BEHAVIOR = FAIL_CLOSED_NO_SKIP
```

If the newest selected candidate under authoritative ordering is corrupt or
unsupported, fail closed. Do **not** silently skip to an older candidate.

---

## 16. Freshness Contract

Schema-present run freshness metadata on `IntelligenceRunRead`:

- `as_of`
- `persisted_at`
- `snapshot_contract_version`
- `persistence_schema_version`

`as_of` is schema-present but **may be null** when the authoritative
persisted outcome is `admission_rejected` and the original `PipelineResult`
did not admit / freeze an `as_of` value. Do not fabricate an `as_of`.

```text
AS_OF_ADMISSION_REJECTED_NULLABILITY = SCHEMA_PRESENT_NULLABLE
AGE_SECONDS_CLOCK_BASIS = persisted_at
```

`persisted_at`, `snapshot_contract_version`, and
`persistence_schema_version` remain storage / product metadata per the
existing contract.

`age_seconds` rules:

- derived from `persisted_at`
- computed as read / request clock minus `persisted_at`
- non-negative integer seconds
- clamp negative clock skew to `0`
- non-authoritative
- excluded from fingerprint and canonical equality
- no business freshness SLA / threshold in Sprint 14

---

## 17. Authorization Contract

```text
EXACT_PRODUCT_READ_SCOPE = intelligence:runs:read
```

All six GET routes require:

1. valid authentication
2. AND scope `intelligence:runs:read`

`api:read` alone is **NOT** sufficient.

| Failure | HTTP | Ownership |
| --- | --- | --- |
| Missing / invalid token | `401` | existing `auth.*` semantics |
| Authenticated without required scope | `403` / `authz.insufficient_scope` | this Policy |

No write scope is defined.  
No new IAM platform is created.  
Exact bootstrap / role wiring mechanics remain Implementation Authorization
owned.

---

## 18. Human Review Product Snapshot

```text
HR_PUBLIC_SNAPSHOT_POLICY = PERSIST_BOUNDED_PUBLIC_CONTRACT_REQUIRED_FOR_READ_RECONSTRUCTION
```

Persist / expose the bounded public `HumanReviewOutput` fields required to
reconstruct the existing public HR read contract, including:

- HR identity
- policy identity
- `as_of`
- public records / references
- public provenance fingerprints
- history binding
- attestation presence
- `recorded_attestation_fingerprint`

Do not reduce the HR product snapshot to attestation fingerprint only if
doing so would make the public HR response unreconstructable.

Existing bounded `recorded_payload` MAY be retained only when it is already
part of the public HR contract and passes current bounded validation.

Forbidden:

- new / raw payload expansion
- HR submit / capture / write
- fabricated attestation

---

## 19. ADE Product Snapshot — Minimization

Persist / expose ADE fields required for:

- `outcome_kind`
- `reason_family`
- `decision_id`
- `policy_version_id`
- `as_of`
- public provenance fingerprints / references
- bounded public `detail` where already authorized

Preserve:

- `authoritative_decision`
- `explicit_abstention`

```text
ADE_RECORDED_ATTESTATION_PAYLOAD_IN_PRODUCT_SNAPSHOT = FORBIDDEN
```

`AdeProvenance.recorded_attestation_payload` MUST NOT be persisted in the ADE
product snapshot.

It is duplicate HR material and is not required for ADE visibility. If
required for the HR public read contract, it belongs only within the bounded
HR snapshot. ADE MAY retain fingerprint / reference to the HR attestation,
not the duplicate payload.

Forbidden:

- private evidence blobs
- ADE invocation on read
- model authority

---

## 20. Materialization Contract

Externally observable semantics:

| Case | Result |
| --- | --- |
| First valid materialization | create durable run identity |
| Same `pipeline_fingerprint` + same `snapshot_contract_version` + canonical equal authoritative content | reuse existing durable run |
| Same fingerprint / version + canonical unequal content | fail closed as application / materialization error `intelligence.runs.materialization_identity_conflict` (no public HTTP mapping; no public write API) |
| Storage unavailable during materialization | application / materialization operation fails with family `intelligence.runs.storage_unavailable` (not a `PipelineOutcome`; no public materialization endpoint) |
| Unsupported snapshot version on write | fail closed |
| Invalid / incomplete `PipelineResult` admission | reject materialization |

When the same `intelligence.runs.storage_unavailable` family crosses an
authorized HTTP read / query boundary because the durable persistence /
storage dependency is unavailable, the public HTTP mapping is
`503 Service Unavailable`.

No update. No overwrite. No duplicate logical run. No seventh
`PipelineOutcome`. No public write API. No public Sprint 14 materialization
endpoint.

### Authorized materialization input

Only a completed public `PipelineResult` may cross into the productization
materialization boundary.

Do not admit:

- raw `PipelineRequest`
- `BarEvent` dumps
- `NewsEvent` dumps
- provider payloads
- temporary calculations
- exception objects
- ORM objects

Do not rerun or recompute intelligence during materialization.

---

## 21. Serialization / Data Minimization

Freeze:

- UTC ISO-8601 timestamps
- string enum values
- lowercase hyphenated UUID strings
- bounded strings
- strict versioned DTO validation
- unknown fields fail closed
- JSON snapshot validation on write
- JSON snapshot validation again on read
- secret / token redaction
- no stack traces
- no raw provider payloads
- no unbounded news
- no model-private state
- no ORM leakage

---

## 22. Migration / Compatibility Principles

Policy-level requirements only (no Alembic operations specified here):

- fresh database upgrade path required before Sprint 14 completion
- version-aware reads
- unsupported versions fail closed
- expand / contract migration principle
- no silent reinterpretation
- migration compatibility tests required
- rollback only where proven safe

```text
DATABASE_MIGRATION_AUTHORIZED = NO
```

---

## 23. Dependency Governance

Proposed future dependency set (exact):

1. SQLAlchemy 2.x
2. Alembic
3. psycopg 3 sync

```text
PROPOSED_NEW_DEPENDENCY_COUNT = 3
NEW_DEPENDENCY_AUTHORIZED = NO
```

Before future installation, Implementation Authorization MUST require:

- version pin / range decision
- license review
- CVE / advisory review
- transitive dependency review
- lockfile update
- CI compatibility
- Python 3.13 compatibility

Do not install anything under this Policy Freeze.

---

## 24. Future Test Obligations

Future implementation MUST satisfy contract-level tests covering:

- snapshot DTO serialization / deserialization
- strict version validation
- canonical equality
- UUID4 format / opacity
- fingerprint validation / current-version lookup
- all six GET route contracts
- HR valid absence
- ADE valid absence
- run not found
- invalid identifiers
- unsupported contract
- corrupt persisted snapshot
- storage unavailable → HTTP `503` on the authorized HTTP read / query boundary
- `401`
- `403`
- latest eligibility
- latest ordering
- latest corrupt fail-closed / no-skip
- latest unsupported fail-closed / no-skip
- freshness / `age_seconds`
- no query-time recomputation
- HR read-only
- ADE read-only
- materialization equality reuse
- materialization identity conflict
- Postgres repository integration
- fresh Alembic upgrade
- migration compatibility
- no ORM leakage
- authority firewall
- no model imports
- no broker / OI / OMS imports
- no Feature Platform imports

This document does **not** create tests.

---

## 25. Future Implementation Handoff

```text
PROPOSED_FUTURE_IMPLEMENTATION_ISSUE_COUNT = 4
```

Proposed workstreams (not authorized by this Policy Freeze):

1. Persistence schema / repository / migrations
2. Durable materialization / snapshot integration
3. Query service + versioned GET-only HTTP API
4. Determinism / authz / contract / authority-firewall hardening

All require later:

- this Policy / Contract Freeze established
- separate Implementation Authorization

---

## 26. Product Readiness Consequences

Future eligibility only (not current authorization):

```text
PREMARKET_COMMAND_CENTER_UI_READINESS_AFTER_SPRINT14 = YES
ADE_VISIBILITY_UI_READINESS_AFTER_SPRINT14 = YES
HUMAN_REVIEW_WRITE_UI_READINESS_AFTER_SPRINT14 = NO
```

These flags do **NOT** authorize UI work during Sprint 14 Policy Freeze.

---

## 27. Policy-Owned Decisions Resolved by This Draft

```text
HTTP_HR_VALID_ABSENCE_SEMANTICS = 404 intelligence.runs.stage_not_present
HTTP_ADE_VALID_ABSENCE_SEMANTICS = 404 intelligence.runs.stage_not_present
LATEST_DASHBOARD_CAPABLE_CORRUPT_CANDIDATE_BEHAVIOR = FAIL_CLOSED_NO_SKIP
LATEST_DASHBOARD_CAPABLE_UNSUPPORTED_VERSION_BEHAVIOR = FAIL_CLOSED_NO_SKIP
EXACT_PRODUCT_READ_SCOPE = intelligence:runs:read
AGE_SECONDS_CLOCK_BASIS = persisted_at
AS_OF_ADMISSION_REJECTED_NULLABILITY = SCHEMA_PRESENT_NULLABLE
ADE_RECORDED_ATTESTATION_PAYLOAD_IN_PRODUCT_SNAPSHOT = FORBIDDEN
HR_PUBLIC_SNAPSHOT_POLICY = PERSIST_BOUNDED_PUBLIC_CONTRACT_REQUIRED_FOR_READ_RECONSTRUCTION
UNSUPPORTED_SNAPSHOT_CONTRACT_HTTP_STATUS = 409
STORAGE_UNAVAILABLE_ERROR_CODE = intelligence.runs.storage_unavailable
STORAGE_UNAVAILABLE_HTTP_STATUS = 503
MATERIALIZATION_IDENTITY_CONFLICT_HTTP_MAPPING = NONE_NO_PUBLIC_WRITE_API
```

---

## 28. Acceptance Criteria

```text
POLICY_AC_COUNT = 34
```

| ID | Criterion |
| --- | --- |
| AC-01 | Policy authority and input boundary frozen; implementation remains unauthorized |
| AC-02 | Exactly six serialized `PipelineOutcome` values frozen; `PIPELINE_OUTCOME_COUNT = 6` |
| AC-03 | Outcome-to-stage-presence matrix frozen for all six outcomes |
| AC-04 | Stage presence enum map frozen with eight keys and six status values |
| AC-05 | Snapshot field classifications frozen (REQUIRED / CONDITIONAL / DERIVED / DEFERRED / FORBIDDEN) |
| AC-06 | `SNAPSHOT_CONTRACT_VERSION = intelligence-run-productization.snapshot.v1` |
| AC-07 | `PERSISTENCE_SCHEMA_VERSION = intelligence-run-productization.persistence.v1` |
| AC-08 | Canonical equality inclusion set frozen |
| AC-09 | Canonical equality exclusions exact: `run_id`, `persisted_at`, DB/ORM metadata, `age_seconds` |
| AC-10 | UUID4 opaque public representation frozen (`8-4-4-4-12` lowercase hyphenated) |
| AC-11 | Fingerprint validation and current-version-only lookup semantics frozen |
| AC-12 | Exactly six GET route families frozen; no write methods |
| AC-13 | Public DTO families frozen: `IntelligenceRunRead`, `IntelligenceRunDashboardRead`, `IntelligenceRunHumanReviewRead`, `IntelligenceRunAdeRead`, `ProductErrorResponse` |
| AC-14 | Run-not-found uses HTTP `404` / `intelligence.runs.run_not_found` |
| AC-15 | HR valid absence uses HTTP `404` / `intelligence.runs.stage_not_present` |
| AC-16 | ADE valid absence uses HTTP `404` / `intelligence.runs.stage_not_present` |
| AC-17 | Expected-but-corrupt / missing required snapshot uses HTTP `500` / `intelligence.runs.corrupt_persisted_snapshot` |
| AC-18 | Unsupported snapshot contract uses HTTP `409` / `intelligence.runs.unsupported_snapshot_contract` |
| AC-19 | Product error taxonomy frozen with `PRODUCT_ERROR_FAMILY_COUNT = 8`; public HTTP mappings include `intelligence.runs.storage_unavailable` → HTTP `503` on authorized read / query boundaries |
| AC-20 | Failure metadata frozen with `FAILURE_DETAIL_MAX_LENGTH = 256` and sanitization / no stack traces |
| AC-21 | Latest-dashboard-capable eligibility requires Dashboard `PRESENT` and valid Dashboard snapshot |
| AC-22 | Latest ordering exact: `as_of DESC`, `persisted_at DESC`, `run_id ASC` |
| AC-23 | Latest corrupt candidate behavior = `FAIL_CLOSED_NO_SKIP` |
| AC-24 | Latest unsupported candidate behavior = `FAIL_CLOSED_NO_SKIP` |
| AC-25 | Freshness metadata frozen: schema-present `as_of` (nullable for `admission_rejected`), `persisted_at`, snapshot and persistence versions |
| AC-26 | `age_seconds` derived from `persisted_at`; non-authoritative; excluded from equality |
| AC-27 | Exact product read scope `intelligence:runs:read`; `api:read` alone insufficient |
| AC-28 | `401` auth.* and `403` `authz.insufficient_scope` semantics frozen |
| AC-29 | HR bounded public snapshot policy frozen for read reconstruction |
| AC-30 | ADE product snapshot forbids `recorded_attestation_payload` duplication |
| AC-31 | Materialization create / equal-reuse / unequal-conflict semantics frozen; input = completed public `PipelineResult` only |
| AC-32 | Serialization / data-minimization and write+read JSON validation frozen |
| AC-33 | Migration compatibility principles frozen; dependencies remain unauthorized (`PROPOSED_NEW_DEPENDENCY_COUNT = 3`) |
| AC-34 | Four future implementation workstreams recorded; authority firewall restated; no implementation authorization |

No implementation acceptance criteria are defined by this document.

---

## 29. Authority Firewall (restatement)

```text
SPRINT_14_PLANNING_GATE_ESTABLISHED = YES
SPRINT_14_ARCHITECTURE_GATE_ESTABLISHED = YES
SPRINT_14_GOVERNANCE_GATE_ESTABLISHED = YES
SPRINT_14_PRODUCTIZATION_POLICY_CONTRACT_FREEZE_STATUS = DRAFT
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

## 30. Next Step

Independently review this DRAFT Combined Productization Policy / Contract
Freeze.

Do not begin Implementation Authorization, dependency installation,
migrations, repositories, materializers, query services, HTTP endpoints, UI,
Feature Platform mutation, live-provider expansion, model participation,
broker execution, tag, release, or deployment until the required governance
sequence authorizes those later steps.
