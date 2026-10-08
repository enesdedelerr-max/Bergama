# Intelligence Run Productization Architecture v1

**Architecture ID:** `intelligence-run-productization.architecture.v1`  
**Status:** APPROVED / EFFECTIVE  
**Sprint:** 14  
**Gate:** Architecture Gate  
**Theme:** Durable Intelligence Run Persistence and Read/Query Boundary  
**Authoritative Base:** `38f808d83bdf9e84421f1f7d75e9d55510f493b3`  
**Planning Gate:** `sprint-14.planning-gate`  
**Planning Issue:** [#136](https://github.com/enesdedelerr-max/Bergama/issues/136)  
**Planning PR:** [#137](https://github.com/enesdedelerr-max/Bergama/pull/137)  
**Architecture Gate Issue:** [#138](https://github.com/enesdedelerr-max/Bergama/issues/138)  
**Architecture merge:** PR [#139](https://github.com/enesdedelerr-max/Bergama/pull/139) @ `2390e4fbe56e8026d62ab4aece7137672d3ee15f`  
**Document class:** Architecture Gate only — not Implementation Authorization

```text
ARCHITECTURE_GATE_APPROVAL != IMPLEMENTATION_AUTHORIZATION
IMPLEMENTATION_AUTHORIZATION = AUTHORIZED (by separate Implementation Authorization; not by this Architecture)
IMPLEMENTATION_WORK_STARTED = YES
IMPLEMENTATION_SEQUENCE = 4/4 COMPLETE
SPRINT_14_COMPLETE = NO
WRITE_API_AUTHORIZED = NO
HR_ATTESTATION_CAPTURE_AUTHORIZED = NO
UI_AUTHORIZED = NO
FEATURE_PLATFORM_CHANGE_AUTHORIZED = NO
LIVE_PROVIDER_EXPANSION_AUTHORIZED = NO
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED/DEFERRED
TAG_RELEASE_DEPLOY_AUTHORIZED = NO
```

---

## 1. Purpose

This Architecture Gate freezes the bounded architecture required to materialize
completed Sprint 13 Intelligence Pipeline runs into durable, immutable,
authenticated, versioned read/query product data.

It does **not** authorize Governance Decisions, Productization Policy / Contract
Freeze, Implementation Authorization, dependency installation, migrations,
repositories, HTTP endpoints, UI, Feature Platform mutation, model participation,
broker execution, tag, release, or deployment.

---

## 2. Architecture Principles

```text
A. Sprint 13 intelligence semantics remain authoritative.
B. Persistence stores authoritative public snapshots; it does not create new intelligence.
C. Historical reads return stored historical snapshots.
D. Historical reads MUST NOT:
   - rerun the pipeline
   - rerank
   - recompute
   - reinterpret using current business logic
   - rewrite provenance
E. Persistence / query / HTTP errors are productization errors, not PipelineOutcome values.
F. Core Sprint 13 intelligence_pipeline remains database/ORM-free.
G. No write/command API exists in Sprint 14.
H. No model or broker authority expansion.
```

---

## 3. Authoritative Inputs

| Input | Reference |
| --- | --- |
| Planning Gate | `docs/sprints/sprint-14/planning-gate.md` |
| Sprint 13 closeout | `docs/sprints/sprint-13/CLOSEOUT.md` |
| Pipeline runtime | `apps/api/app/intelligence_pipeline/` |
| Public contracts | `PipelineResult`, `PipelineOutcome`, `PipelineProvenance`, stage public outputs |
| Auth | Bearer JWT + `AuthenticatedPrincipal` (`apps/api/app/deps/auth.py`) |
| API prefix | `/api/v1` (`AppSettings.api_prefix`) |
| Postgres today | optional TCP health only; no ORM product store |
| SQLAlchemy today | not first-class `bergama-api` dependency (transitive via pyiceberg only) |
| Alembic today | absent |

---

## 4. Frozen Sprint 13 Outcomes

Preserve exactly six terminal outcomes:

1. `admission_rejected`
2. `required_stage_failed`
3. `completed_dashboard`
4. `completed_human_review`
5. `completed_ade_accept`
6. `completed_ade_abstain`

```text
PIPELINE_OUTCOME_COUNT = 6
NEW_OUTCOME_COUNT = 0
REMOVED_OUTCOME_COUNT = 0
RENAMED_OUTCOME_COUNT = 0
```

No persistence, HTTP, migration, or materialization failure may introduce a
seventh intelligence outcome.

---

## 5. AD-14-01 — Persistence Model

```text
DECISION = HYBRID_IMMUTABLE_ENVELOPE_PLUS_VERSIONED_PUBLIC_JSON_SNAPSHOTS
PRIMARY_ENTITY = intelligence_runs
```

### Normalized immutable envelope (architecture-level columns)

| Field | Role |
| --- | --- |
| `run_id` | Opaque durable PK / product identifier (UUID4) |
| `pipeline_fingerprint` | Sprint 13 deterministic composition identity |
| `as_of` | Original UTC event time |
| `outcome` | One of six frozen `PipelineOutcome` values |
| `failed_stage` | When applicable |
| `failure_detail` | Bounded string when applicable |
| `failure_error_type` | Bounded string when applicable |
| bindings / policy / config pins | Normalized columns and/or bounded JSON of `PipelineBindings` |
| thin provenance | Bounded JSON of `PipelineProvenance` |
| stage-presence / status metadata | Explicit per-stage status (AD-14-06) |
| `persisted_at` | Materialization wall-clock UTC (productization metadata) |
| `persistence_schema_version` | Physical schema version |
| `snapshot_contract_version` | Public snapshot DTO contract version |

### Bounded public snapshots

| Snapshot | Classification |
| --- | --- |
| Dashboard public snapshot | REQUIRED when Dashboard exists for the run |
| Human Review public snapshot | CONDITIONAL when HR ran |
| ADE public snapshot | CONDITIONAL when ADE ran |
| Intermediate stage payloads | DEFER (AD-14-05) |

### Rejected

- One unstructured JSON-only record (weak indexing / constraints)
- Fully normalized tables for every intelligence stage (premature for Sprint 14)

---

## 6. AD-14-02 — Durable Identity

```text
DECISION = RUN_ID_UUID4_PLUS_UNIQUE_FINGERPRINT_CONTRACT
run_id = UUID4 (opaque application-generated product/database identifier)
pipeline_fingerprint = Sprint 13 deterministic composition identity (unchanged)
UUID_GENERATION = PYTHON_STDLIB_UUID4
UUID_EXTRA_DEPENDENCY_REQUIRED = NO
```

### Rationale

- Project runtime is Python `>=3.13` (`apps/api/pyproject.toml`); CI uses Python
  **3.13**.
- Python 3.13 stdlib provides `uuid.uuid4()` and does **not** provide
  `uuid.uuid7()` (UUIDv7 entered the stdlib in Python 3.14).
- Sprint 14 does **not** require `run_id` to be chronologically sortable,
  deterministic, or business-meaningful.
- Deterministic composition identity remains `pipeline_fingerprint`.
- Rejected for Sprint 14: ULID dependency, UUIDv7 helper dependency, a DB
  extension solely for UUIDv7, and a Python 3.14 runtime requirement.

### Identity roles

| Identifier | Purpose |
| --- | --- |
| `run_id` | Opaque durable product/database PK and primary path param (UUID4) |
| `pipeline_fingerprint` | Deterministic composition identity from Sprint 13 |

They are intentionally separate. Fingerprint semantics MUST NOT change.

### Uniqueness

```text
PRIMARY KEY (run_id)
UNIQUE (pipeline_fingerprint, snapshot_contract_version)
```

Equally strict frozen equivalent permitted only if Policy Freeze renames the
contract-version column without weakening uniqueness.
---

## 7. AD-14-03 — Materialization Boundary

```text
DECISION = APPLICATION_SERVICE_WRAPPER
MATERIALIZER = IntelligenceRunMaterializer
```

### Flow

```text
caller / application service
  → run_intelligence_pipeline(...)
  → authoritative PipelineResult
  → IntelligenceRunMaterializer
  → persistence repository
```

### Constraints

- `apps/api/app/intelligence_pipeline/` remains database/ORM-free.
- SQLAlchemy MUST NOT become a dependency of the core pipeline package.
- Persistence failure MUST NOT rewrite the intelligence outcome.
- Persistence failure MUST NOT create a seventh `PipelineOutcome`.
- Persistence failure surfaces as a separate materialization / productization
  failure.
- No event/outbox architecture is required for the first Sprint 14 boundary.

---

## 8. AD-14-04 — Immutability / Idempotency

```text
DECISION = INSERT_ONLY_WITH_EQUALITY_IDEMPOTENCY
PRODUCT_UPDATE = NO
PRODUCT_DELETE = NO
```

For an existing row with the same `(pipeline_fingerprint, snapshot_contract_version)`:

1. Load existing durable snapshot.
2. Compare **canonical AUTHORITATIVE SNAPSHOT CONTENT** only.
3. If equal → return existing durable record.
4. If unequal → fail closed with deterministic materialization identity conflict.

### Canonical equality MUST include (as applicable)

- `pipeline_fingerprint`
- `snapshot_contract_version`
- `as_of`
- `PipelineOutcome` / terminal outcome
- `failed_stage`
- bounded failure metadata (`failure_detail`, `failure_error_type`)
- bindings / policy / config pins
- thin provenance
- stage-presence / status metadata
- Dashboard public snapshot
- Human Review public snapshot when present
- bounded HR attestation identity / fingerprint metadata when present
- ADE public result when present

### Canonical equality MUST EXCLUDE storage-generated / response-derived metadata

- `run_id`
- `persisted_at`
- database-generated / internal row metadata
- ORM / session state
- storage-only bookkeeping
- response-derived values such as `age_seconds`

Never silently create contradictory duplicate records. No UPDATE. No duplicate
insert. No seventh `PipelineOutcome`. Database uniqueness must reinforce this
invariant.
---

## 9. AD-14-05 — Snapshot Boundary

### REQUIRED

- PipelineResult envelope identity metadata
- `pipeline_fingerprint`
- original UTC `as_of`
- bindings / pins
- terminal outcome
- failure metadata when applicable
- thin provenance
- stage-presence / status metadata
- Dashboard public snapshot when Dashboard exists

### CONDITIONAL WHEN PRESENT

- Human Review public output
- Bounded HR attestation presence / fingerprint and already-public identity fields
- ADE public result

### DEFER (Sprint 14 default)

Full Watchlist / Gap / Catalyst / Score / Briefing payloads.

```text
INTERMEDIATE_STAGE_SNAPSHOT_DECISION = DEFER_FULL_PAYLOADS
```

Stage-presence metadata (AD-14-06) remains REQUIRED and is not the same as full
stage payload storage. Premarket Command Center first-read readiness is satisfied
by Dashboard (+ optional HR/ADE) without intermediate payload tables.

### FORBIDDEN

- Raw bars
- Raw provider payloads
- Unbounded news payloads
- Secrets / credentials
- Stack traces
- Temporary orchestration state
- Full ADE internal evidence
- HR write / capture workflow internals

---

## 10. AD-14-06 — Stage Presence Semantics

Persistence must preserve distinctions among:

- not executed
- valid absence
- empty success
- failed
- completed with value
- ADE abstention

Do **not** collapse these into nullable JSON alone.

### Architecture-level vocabulary (proposed labels)

Exact serialized strings may be refined by Productization Policy / Contract
Freeze; Architecture freezes the **required distinctions**:

| Distinction | Proposed label |
| --- | --- |
| Stage never reached / not executed | `NOT_EXECUTED` |
| Valid absence | `ABSENT` |
| Empty success | `EMPTY` |
| Failed | `FAILED` |
| Completed with value | `PRESENT` |
| ADE abstention | `ABSTAINED` |

These labels are persistence/productization metadata. They are **not** new
`PipelineOutcome` values.

---

## 11. AD-14-07 — Serialization / Versioning

```text
DECISION = EXPLICIT_PUBLIC_SNAPSHOT_DTOS
```

- Persist via explicit public snapshot DTOs (Pydantic / public contracts).
- Do not persist ORM dumps as API contracts.
- Canonical public DTO serialization feeds persistence.

Required version fields:

- `persistence_schema_version`
- `snapshot_contract_version`

Historical records MUST be decoded according to their stored contract version.
Unsupported-version failure is a productization / read failure, not a
`PipelineOutcome`.

```text
QUERY_TIME_INTELLIGENCE_RECOMPUTATION_AUTHORIZED = NO
INTELLIGENCE_RERANKING_AUTHORIZED = NO
PROVENANCE_REWRITE_AUTHORIZED = NO
```

---

## 12. AD-14-08 — Database

```text
DECISION = POSTGRESQL
```

PostgreSQL is already the intended product database (settings + optional TCP
health). Iceberg remains market-data oriented and is **not** the intelligence-run
product store. Redis is not source of truth for runs. No second OLTP database.

---

## 13. AD-14-09 — ORM / Driver / Session

```text
DECISION_ORM = SQLALCHEMY_2X_SYNC
DECISION_DRIVER = PSYCOPG_3
SYNC_SQLALCHEMY_MODE = YES
SYNC_PSYCOPG3_MODE = YES
BLOCKING_DB_IO_ON_ASYNC_EVENT_LOOP_ALLOWED = NO
PROPOSED != AUTHORIZED
```

### Rationale

- Smallest coherent first product path with FastAPI.
- Current repository has no async product ORM convention; sync SQLAlchemy 2.x
  avoids premature async complexity.
- `psycopg` 3 is the preferred PostgreSQL driver for sync SQLAlchemy 2.x.
- Do **not** switch to `asyncpg` or async SQLAlchemy for Sprint 14.

### FastAPI execution boundary (required)

Blocking SQLAlchemy / psycopg operations MUST NOT execute directly on an async
event loop thread.

Preferred Sprint 14 architecture:

- DB-backed intelligence read routes are implemented as **synchronous** FastAPI
  route handlers (`def`) calling synchronous application / query services /
  repositories.
- FastAPI / Starlette may execute synchronous handlers in its threadpool.

If an `async def` route must call a synchronous DB service, it MUST use an
explicit approved threadpool boundary (repository-consistent Starlette /
FastAPI threadpool mechanism such as `anyio.to_thread.run_sync` /
`starlette.concurrency.run_in_threadpool`).

Forbidden:

```text
async def route → direct blocking sync SQLAlchemy/psycopg call on event-loop thread
```

### Ownership

| Concern | Owner |
| --- | --- |
| Engine / session factory | Infrastructure (sync) |
| Session lifecycle | Per application request / unit of work |
| Repository | Sync ORM operations |
| Materializer | Sync DB boundary |
| Query service | Sync DB boundary |
| Routers | Public DTOs only — never ORM entities |
| Application / public DTOs | Must not depend on ORM models |
| Transaction boundary | One materialization operation |

Dependencies remain **proposed, not authorized**.
---

## 14. AD-14-10 — Migrations

```text
DECISION = ALEMBIC
RECOMMENDED_LOCATION = apps/api/alembic/
PROPOSED != AUTHORIZED
```

Requirements for later Implementation Authorization:

- Single metadata ownership for intelligence-run models
- Versioned migrations
- Fresh-database upgrade test
- Upgrade verification in CI
- Downgrade only where safe and supported
- Expand/contract migration discipline

Do not create migration files in this Architecture Gate draft task.

---

## 15. AD-14-11 — Query Service

```text
DECISION = READ_ONLY_INTELLIGENCE_RUN_QUERY_SERVICE
SERVICE = IntelligenceRunQueryService
LATEST_DASHBOARD_ORDER = as_of_DESC, persisted_at_DESC, run_id_ASC
FINGERPRINT_DEFAULT_CONTRACT_SELECTION = CURRENT_SUPPORTED_SNAPSHOT_CONTRACT_VERSION
HISTORY_LIST_DECISION = DEFER
```

| Operation | Semantics |
| --- | --- |
| `get_by_run_id` | Exact durable `run_id` |
| `get_by_fingerprint` | Exact fingerprint against the **current supported** `snapshot_contract_version` by default |
| `get_latest_dashboard_capable` | First record under total ordering below among runs whose frozen outcome / stage-presence semantics establish Dashboard presence |
| `get_dashboard` | Dashboard subresource |
| `get_human_review` | HR subresource |
| `get_ade` | ADE subresource |

### Deterministic latest ordering (total order)

```text
1. as_of DESC
2. persisted_at DESC
3. run_id ASC
```

- `run_id ASC` is a final **stable** tie-break only. UUID4 carries no time /
  recency semantics and MUST NOT be used for recency ranking.
- Recency is defined solely by `as_of`, then `persisted_at`.

### Fingerprint contract-version selection

Because uniqueness is `(pipeline_fingerprint, snapshot_contract_version)`,
fingerprint lookup MUST select a contract version deterministically:

- Default: resolve against the **current supported** snapshot contract version.
- MUST NOT arbitrarily select among multiple historical contract versions.
- An explicit historical contract-version selector (query parameter / HTTP
  representation) may be introduced later if Productization Policy / Contract
  Freeze requires it; that selector shape is Policy-owned.

No ambiguous bare `latest`.
---

## 16. AD-14-12 — HTTP Read API

```text
DECISION = GET_ONLY_SIX_ENDPOINTS
RECOMMENDED_HTTP_ENDPOINT_COUNT = 6
API_PREFIX = /api/v1
ROUTE_COLLISION_DEPENDS_ON_REGISTRATION_ORDER = NO
```

Structurally non-colliding namespaces (`id/` and `fingerprint/`) prevent dynamic
identifier routes from colliding with static collection operations. Correctness
MUST NOT depend on route declaration order.

1. `GET /api/v1/intelligence/runs/id/{run_id}`
2. `GET /api/v1/intelligence/runs/fingerprint/{fingerprint}`
3. `GET /api/v1/intelligence/runs/latest-dashboard-capable`
4. `GET /api/v1/intelligence/runs/id/{run_id}/dashboard`
5. `GET /api/v1/intelligence/runs/id/{run_id}/human-review`
6. `GET /api/v1/intelligence/runs/id/{run_id}/ade`

Fingerprint route default contract selection:

```text
CURRENT_SUPPORTED_SNAPSHOT_CONTRACT_VERSION
```

Historical contract-version-specific fingerprint lookup may be added later via
an explicit Policy-owned selector. Arbitrary multi-version selection is forbidden.

### Forbidden methods / surfaces

No `POST` / `PUT` / `PATCH` / `DELETE`.  
No pipeline trigger, manual rerun, HR submit, ADE invoke, or config mutation.

Terminal failure runs remain retrievable by direct run identity.
---

## 17. AD-14-13 — API DTO Boundary

```text
DECISION = EXPLICIT_PUBLIC_DTOS_NO_ORM_LEAKAGE
```

Bounded DTO families (names may be refined by Policy Freeze):

- `RunRead`
- `DashboardRead`
- `HumanReviewRead`
- `AdeRead`

`RunRead` may include conditional nested public snapshots and MUST preserve
explicit stage status. Subresources exist for first UI convenience. Routers
never return ORM entities.

---

## 18. AD-14-14 — Authn / Authz

```text
DECISION = REUSE_BEARER_JWT_AND_AUTHENTICATED_PRINCIPAL
```

- Integrate with existing Bearer JWT + `AuthenticatedPrincipal` roles/scopes.
- Architecture proposes a **dedicated read permission/scope** for intelligence
  runs; exact serialized scope string / role binding is owned by
  Governance / Productization Policy (see Open Questions).
- No new IAM platform.
- Missing/invalid authentication → `401`
- Authenticated but insufficient authorization → `403`
- Every intelligence read route requires authorization.

---

## 19. AD-14-15 — Freshness

Public freshness metadata:

- `as_of`
- `persisted_at`
- `snapshot_contract_version`
- `persistence_schema_version`

`age_seconds` may be response-derived if useful and MUST NOT mutate historical
records. No business freshness threshold/SLA is authorized by this Architecture
Gate unless already frozen elsewhere.

---

## 20. AD-14-16 — Error Model

Separate productization errors for:

| Concern | Class |
| --- | --- |
| Run not found | Productization / query |
| Valid subresource absence | Productization / query |
| Persistence unavailable | Productization / materialization |
| Query storage unavailable | Productization / query |
| Corrupt snapshot | Productization / query |
| Unsupported snapshot contract | Productization / query |
| Materialization identity conflict | Productization / materialization |
| Authentication failure | Auth |
| Authorization failure | Authz |

None of the above is a `PipelineOutcome`.

HR/ADE valid-absence HTTP shape (`404` vs typed absence) is owned by
Productization Policy / Contract Freeze.

---

## 21. AD-14-17 — Human Review Read Boundary

When HR ran, persistence/read may include only bounded public data:

- `HumanReviewOutput` public fields
- Attestation presence
- Attestation fingerprint
- Already-public policy / identity IDs
- Already-public record references

Explicitly deferred:

- Attestation capture / submission
- HR mutation APIs
- HR write workflow
- HR write UI

```text
HR_ATTESTATION_CAPTURE_AUTHORIZED = NO
HUMAN_REVIEW_WRITE_UI_READINESS_AFTER_SPRINT14 = NO
```

---

## 22. AD-14-18 — ADE Read Boundary

When ADE ran, persist/read bounded public result including:

- Outcome kind (`authoritative_decision` vs `explicit_abstention`)
- Reason family
- Decision ID
- Policy / version identity
- `as_of`
- Public provenance / fingerprints

Preserve accept vs abstain. Do not persist unbounded internal evidence.
Do not create model authority.

```text
MODEL_PARTICIPATION = UNAUTHORIZED
ADE_VISIBILITY_UI_READINESS_AFTER_SPRINT14 = YES
```

---

## 23. AD-14-19 — Security / Data Minimization

Architecture controls:

- No secrets / credentials in snapshots
- No raw provider payload retention
- No unbounded news retention
- No stack traces
- Bounded `failure_detail`
- Bounded JSON size
- Stored-version validation on read
- Parameterized ORM queries
- Authz on all routes
- Opaque `run_id` for normal path lookup
- Fingerprint endpoint remains authenticated/authorized
- No write routes
- No generic JSONB GIN index unless query evidence requires it
- No internal ORM exposure
- No bulk history / mass enumeration surface in Sprint 14 (history deferred)

---

## 24. Index Architecture

Minimum planned indexes:

1. **Primary key:** `run_id`
2. **Unique:** `(pipeline_fingerprint, snapshot_contract_version)`
3. **Latest Dashboard-capable:** `(as_of DESC, persisted_at DESC)` with
   outcome / presence filtering as appropriate
4. **Optional:** `(outcome, as_of DESC)` only if query plan requires it

The final `run_id ASC` tie-break for latest-dashboard-capable does **not**
require a dedicated index unless future query-plan evidence shows otherwise.

```text
GENERIC_JSONB_GIN_INDEX_FOR_SPRINT_14 = NO
```

---

## 25. AD-14-20 — Test / Rollout / Firewall

### Future test architecture (not implemented here)

| Layer | Coverage |
| --- | --- |
| UNIT | DTO serialization/versioning; repository contracts; query semantics; idempotency comparison |
| MIGRATION | Fresh Postgres upgrade; migration integrity |
| INTEGRATION | Real Postgres persist/retrieve; duplicate equality; conflicting duplicate rejection; immutability |
| API CONTRACT | Authn; authz; 404/not-found; valid absence; six outcomes; freshness; historical version retrieval |
| DETERMINISM | Retrieval does not invoke pipeline; no rerank/recompute |
| FIREWALL | No write endpoints; no model/LLM; no broker/OI/OMS; no Feature Platform; no live-provider expansion |

### Explicit future required tests (A–L)

| ID | Requirement |
| --- | --- |
| A | UUID4 run ID format / opacity |
| B | Same fingerprint + same contract version + equal canonical content returns existing durable record |
| C | Same fingerprint + same contract version + different canonical content fails closed |
| D | `run_id` and `persisted_at` are excluded from canonical equality |
| E | Fingerprint lookup defaults deterministically to current supported snapshot contract version |
| F | Historical fingerprint lookup never arbitrarily chooses a contract version |
| G | Latest-dashboard-capable total ordering: `as_of DESC`, `persisted_at DESC`, `run_id ASC` |
| H | Exact tie on `as_of` + `persisted_at` resolves deterministically by `run_id` |
| I | Static/dynamic route resolution cannot collide |
| J | `/runs/id/{run_id}` does not swallow `/runs/latest-dashboard-capable` |
| K | Fingerprint namespace does not collide with run ID namespace |
| L | Sync SQLAlchemy calls do not execute directly on async event-loop handlers |

These are future required tests only. Do not create test files in this gate.

Future CI may require a Postgres service/container. No CI config change is
authorized by this draft.
### Rollout principles

- Expand/contract migrations
- Additive-first schema changes
- Version-aware reads
- Safe rollback only where migration semantics support it

No deployment is authorized.

---

## 26. UI Readiness (capability, not authorization)

```text
UI_REQUIRED_IN_SPRINT_14 = NO
UI_AUTHORIZED = NO
PREMARKET_COMMAND_CENTER_UI_READINESS_AFTER_SPRINT14 = YES
ADE_VISIBILITY_UI_READINESS_AFTER_SPRINT14 = YES
HUMAN_REVIEW_WRITE_UI_READINESS_AFTER_SPRINT14 = NO
```

Successful Sprint 14 implementation would make Premarket read/display UI
eligible as a later sprint. HR write UI remains deferred.

---

## 27. Feature Platform / Model / Broker Firewalls

```text
FEATURE_PLATFORM_CHANGE_REQUIRED_FOR_SPRINT_14 = NO
FEATURE_PLATFORM_CHANGE_AUTHORIZED = NO
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED/DEFERRED
LIVE_PROVIDER_EXPANSION_AUTHORIZED = NO
```

Sprint 14 persistence/query does not depend on Feature Platform mutation.
TD-001 remains separate quality work unless later separately governed.

---

## 28. Open Questions / Ownership

### Architecture Gate resolves in this document

| Topic | Frozen decision |
| --- | --- |
| `run_id` format | UUID4 via stdlib `uuid.uuid4()` |
| Sync vs async SQLAlchemy | Sync + no blocking DB I/O on async event loop |
| Postgres driver | psycopg 3 (sync) |
| Intermediate snapshot requirement | DEFER full payloads |
| History listing | DEFER |
| Combined vs split Productization Policy / Contract Freeze | **COMBINED** preferred |
| Fingerprint contract-version default | Current supported snapshot contract version |
| Historical fingerprint contract selector shape | Productization Policy / Contract Freeze |

```text
PRODUCTIZATION_POLICY_CONTRACT_FREEZE_MODE = COMBINED
```

Planning Gate preferred a combined freeze covering persistence semantics and
versioned read/query contracts. Architecture confirms that preference unless a
later Governance conflict emerges.

### Governance / Policy owns

- Exact permission / scope string
- Role binding

### Productization Policy / Contract Freeze owns

- HR/ADE valid-absence HTTP representation (`404` vs typed absence)
- Exact serialized stage-status strings if refined beyond architecture labels
- DTO field-level response contracts
- Error payload shape
- Freshness response shape details
- Exact query parameter / HTTP representation for historical fingerprint
  contract-version selection (if introduced)

### Implementation Authorization owns

- Exact dependency versions
- Dependency installation
- Migration implementation
- Repository / materializer / query service / HTTP implementation
- CI Postgres service changes

---

## 29. Dependency Proposal

```text
PROPOSED_NEW_DEPENDENCY_COUNT = 3
PROPOSED != AUTHORIZED
```

| Package | Purpose | Class |
| --- | --- | --- |
| SQLAlchemy 2.x | ORM / engine | Proposed runtime |
| Alembic | Migrations | Proposed tooling/runtime |
| psycopg 3 | PostgreSQL driver | Proposed runtime |

```text
SQLALCHEMY_INSTALLATION_AUTHORIZED = NO
ALEMBIC_INSTALLATION_AUTHORIZED = NO
PSYCOPG_INSTALLATION_AUTHORIZED = NO
NEW_DEPENDENCY_AUTHORIZED = NO
```

Later Implementation Authorization must require:

- Pinned versions
- License review
- Dependency / CVE scan
- Supply-chain review
- Lockfile integrity

No installation, manifest edits, or lockfile edits are authorized by this
Architecture Gate draft.

---

## 30. Acceptance Criteria

| ID | Criterion |
| --- | --- |
| AC-01 | Hybrid persistence frozen |
| AC-02 | Opaque UUID4 durable run identity is separated from deterministic pipeline fingerprint |
| AC-03 | Fingerprint semantics unchanged |
| AC-04 | Materializer outside core pipeline |
| AC-05 | Core pipeline remains ORM/DB-free |
| AC-06 | Immutable insert-only semantics |
| AC-07 | Canonical equality excludes `run_id` / `persisted_at` / storage and response-derived metadata |
| AC-08 | Contradictory duplicate fails closed |
| AC-09 | Dashboard snapshot required when Dashboard exists |
| AC-10 | HR/ADE bounded conditional snapshots |
| AC-11 | Raw inputs / provider payloads forbidden |
| AC-12 | Explicit stage-presence semantics |
| AC-13 | Explicit snapshot contract versioning |
| AC-14 | Historical reads do not recompute |
| AC-15 | Postgres selected |
| AC-16 | SQLAlchemy 2.x sync proposed only; blocking DB I/O not allowed directly on async event-loop handlers |
| AC-17 | Alembic proposed only |
| AC-18 | psycopg 3 sync proposed only |
| AC-19 | Query service read-only |
| AC-20 | Latest-dashboard-capable uses total deterministic ordering: `as_of DESC`, `persisted_at DESC`, `run_id ASC` |
| AC-21 | HTTP API GET-only |
| AC-22 | Six non-colliding endpoint namespaces frozen (`/runs/id/...`, `/runs/fingerprint/...`, `/runs/latest-dashboard-capable`) |
| AC-23 | No ORM exposure |
| AC-24 | Authn/authz reused |
| AC-25 | No new IAM platform |
| AC-26 | Freshness metadata bounded |
| AC-27 | Productization errors separate from outcomes |
| AC-28 | Six PipelineOutcomes unchanged |
| AC-29 | HR write deferred |
| AC-30 | ADE bounded public read only |
| AC-31 | Security / data minimization frozen |
| AC-32 | No bulk history surface unless explicitly included |
| AC-33 | No generic JSONB GIN index |
| AC-34 | Postgres-backed future tests required, including UUID4, canonical equality exclusions, fingerprint contract default, latest tie-break, route namespaces, and sync-DB boundary |
| AC-35 | No Feature Platform change |
| AC-36 | Model unauthorized |
| AC-37 | Broker denied/deferred |
| AC-38 | UI outside Sprint 14 |
| AC-39 | Dependencies remain unauthorized (exactly three proposed: SQLAlchemy, Alembic, psycopg) |
| AC-40 | Implementation remains unauthorized |
| AC-41 | Next governance is Governance Gate Discovery after merge + green main CI |

---

## 31. Non-Authorization Block

```text
ARCHITECTURE_GATE_APPROVAL != IMPLEMENTATION_AUTHORIZATION
IMPLEMENTATION_AUTHORIZATION = AUTHORIZED (by separate Implementation Authorization; not by this Architecture)
IMPLEMENTATION_SEQUENCE = 4/4 COMPLETE
SPRINT_14_COMPLETE = NO
WRITE_API_AUTHORIZED = NO
HR_ATTESTATION_CAPTURE_AUTHORIZED = NO
UI_AUTHORIZED = NO
FEATURE_PLATFORM_CHANGE_AUTHORIZED = NO
LIVE_PROVIDER_EXPANSION_AUTHORIZED = NO
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED/DEFERRED
TAG_RELEASE_DEPLOY_AUTHORIZED = NO
```

No implementation issue, branch, dependency change, migration, or pull request
may claim implementation authority merely because this Architecture Gate is
APPROVED. Implementation proceeded only under separately approved Implementation
Authorization and is COMPLETE (Issues #146 / #148 / #150 / #152). This
Architecture Gate does not declare Sprint 14 COMPLETE.

---

## 32. Next Governance Step

This Architecture Gate is **APPROVED / EFFECTIVE** (#138 / PR #139 @
`2390e4fbe56e8026d62ab4aece7137672d3ee15f`). Subsequent Governance, Policy /
Contract Freeze, Implementation Authorization, and WS1–WS4 completed under
separate gates.

Current next repository process step (separate issue):

```text
NEXT_PROCESS_STEP = Sprint 14 Governance Closeout / ROADMAP Reconciliation
STATUS_SYNC = IN_PROGRESS / ISSUE_154
GOVERNANCE_CLOSEOUT = PENDING
```

`IMPLEMENTATION_COMPLETE = YES`. `SPRINT_COMPLETE = NO`.
`MODEL_PARTICIPATION = UNAUTHORIZED`. `BROKER_EXECUTION = DENIED/DEFERRED`.

Mandatory sequence remains:

```text
Planning → Architecture → Governance → Productization Policy / Contract Freeze
  → Implementation Authorization → bounded implementation
```

---

## 33. Decision Summary

| ID | Decision |
| --- | --- |
| AD-14-01 | Hybrid immutable envelope + versioned public JSON snapshots |
| AD-14-02 | `run_id` = UUID4 (stdlib); PK + unique `(pipeline_fingerprint, snapshot_contract_version)` |
| AD-14-03 | Application-service materializer outside core pipeline |
| AD-14-04 | Insert-only; canonical equality excludes `run_id`/`persisted_at`; conflict fails closed |
| AD-14-05 | Dashboard REQUIRED; HR/ADE conditional; intermediate payloads DEFER |
| AD-14-06 | Explicit stage-presence distinctions (labels Policy-refinable) |
| AD-14-07 | Explicit public snapshot DTOs + dual version fields |
| AD-14-08 | PostgreSQL |
| AD-14-09 | SQLAlchemy 2.x sync + psycopg 3; no blocking DB I/O on async event loop (proposed) |
| AD-14-10 | Alembic at `apps/api/alembic/` (proposed) |
| AD-14-11 | Read-only query service; latest order `as_of DESC, persisted_at DESC, run_id ASC`; history DEFER |
| AD-14-12 | Six GET-only non-colliding `/api/v1/intelligence/runs/{id\|fingerprint\|latest-...}` endpoints |
| AD-14-13 | Explicit public DTOs; no ORM leakage |
| AD-14-14 | Reuse Bearer JWT / principal; dedicated read scope proposed |
| AD-14-15 | Freshness: as_of, persisted_at, versions |
| AD-14-16 | Productization errors ≠ PipelineOutcome |
| AD-14-17 | HR public read only; capture deferred |
| AD-14-18 | ADE public read only; model unauthorized |
| AD-14-19 | Security / data minimization controls |
| AD-14-20 | Test / rollout / firewall architecture including A–L determinism/route/sync-DB tests |
