# Intelligence Run Productization Implementation Authorization v1

**Authorization ID:** `intelligence-run-productization.implementation-authorization.v1`  
**Title:** Intelligence Run Productization Implementation Authorization v1  
**Version:** v1  
**Status:** APPROVED / EFFECTIVE  
**Document class:** Implementation Authorization  
**Sprint:** 14  
**Theme:** Durable Intelligence Run Persistence and Read/Query Boundary  
**Bounded context:** Intelligence Run Productization  
**Authorized package:** `apps/api/app/intelligence_runs/`  
**Implementation Authorization issue:** [#144](https://github.com/enesdedelerr-max/Bergama/issues/144)

```text
SPRINT_14_IMPLEMENTATION_AUTHORIZATION_STATUS = APPROVED / EFFECTIVE
SPRINT_14_IMPLEMENTATION_AUTHORIZED = YES
IMPLEMENTATION_WORK_STARTED = YES
IMPLEMENTATION_SEQUENCE = 4/4 COMPLETE
ISSUE_146 = COMPLETE
ISSUE_148 = COMPLETE
ISSUE_150 = COMPLETE
ISSUE_152 = COMPLETE
SPRINT_14 = NOT COMPLETE
PUBLIC_WRITE_API = UNAUTHORIZED / NOT IMPLEMENTED
UI_AUTHORIZED = NO
FEATURE_PLATFORM_CHANGE_AUTHORIZED = NO
LIVE_PROVIDER_EXPANSION_AUTHORIZED = NO
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED/DEFERRED
TAG_RELEASE_DEPLOY_AUTHORIZED = NO
```

This document is **APPROVED / EFFECTIVE** (#144 / PR #145 @
`0755b692a13345dc923570b73ea91b0f032f3242`). Implementation is **AUTHORIZED**
strictly within the boundaries frozen by this artifact. The authorized four
workstream sequence is COMPLETE. Sprint 14 governance closeout remains separate
and NOT COMPLETE. Status sync is Issue #154 (docs-only).

---

## 1. Authority Statement

### DRAFT AUTHORIZATION vs EFFECTIVE AUTHORIZATION

| State | Meaning |
| --- | --- |
| **DRAFT** (historical) | Artifact proposed bounded future authorization. `SPRINT_14_IMPLEMENTATION_AUTHORIZED = NO`. |
| **EFFECTIVE** (current) | Artifact completed its governed lifecycle (review → commit → push → PR → required CI → required approval → merge → post-merge main CI green). WS1–WS4 executed under this document and are COMPLETE. |

This Implementation Authorization does **not** authorize beyond the frozen
minimum surface:

- public write API
- UI implementation
- Feature Platform expansion
- live-provider expansion
- model participation
- broker / OMS / execution

This Implementation Authorization is **subordinate** to Planning, Architecture,
Governance, and Policy. It does **not** reopen, supersede, or reinterpret those
gates. Status synchronization does not expand authorization or create new
deliverables.

---

## 2. Prerequisites

| Prerequisite | Process state | Evidence |
| --- | --- | --- |
| Planning Gate | APPROVED / EFFECTIVE | Issue [#136](https://github.com/enesdedelerr-max/Bergama/issues/136) / PR [#137](https://github.com/enesdedelerr-max/Bergama/pull/137) @ `38f808d83bdf9e84421f1f7d75e9d55510f493b3` |
| Architecture `intelligence-run-productization.architecture.v1` | APPROVED / EFFECTIVE | Issue [#138](https://github.com/enesdedelerr-max/Bergama/issues/138) / PR [#139](https://github.com/enesdedelerr-max/Bergama/pull/139) @ `2390e4fbe56e8026d62ab4aece7137672d3ee15f` |
| Governance `intelligence-run-productization.governance.v1` | APPROVED / EFFECTIVE | Issue [#140](https://github.com/enesdedelerr-max/Bergama/issues/140) / PR [#141](https://github.com/enesdedelerr-max/Bergama/pull/141) @ `9d2882437d585d5725226e849621f20e6ad3dc4b` |
| Policy / Contract `intelligence-run-productization.policy.v1` | APPROVED / FROZEN | Issue [#142](https://github.com/enesdedelerr-max/Bergama/issues/142) / PR [#143](https://github.com/enesdedelerr-max/Bergama/pull/143) @ `ba4eed88c4598713f356035b28147812472c51ec` |

Policy merge commit: `ba4eed88c4598713f356035b28147812472c51ec`  
Post-merge main CI: run `37557309266` success on that SHA.

Authoritative inputs (do not reopen):

- `docs/sprints/sprint-14/planning-gate.md`
- `docs/architecture/intelligence-run-productization-architecture-v1.md`
- `docs/governance/intelligence-run-productization/intelligence-run-productization-governance-v1.md`
- `docs/policy/intelligence-run-productization-policy-v1.md`

---

## 3. Objective

When this artifact becomes **EFFECTIVE**, authorize only the minimum
implementation surface required to realize the frozen Sprint 14 productization
contract:

1. PostgreSQL durable Intelligence Run persistence (hybrid envelope + JSON snapshots)
2. Application-layer materializer from completed public `PipelineResult`
3. Read-only query service and exactly six authenticated GET route families
4. Determinism / authz / contract / authority-firewall hardening

```text
PIPELINE_DB_FREE = YES
```

`apps/api/app/intelligence_pipeline/` remains database / ORM-free.

---

## 4. Frozen Discovery Resolutions

Discovery verdict (historical): `B — READY TO DRAFT WITH NON-BLOCKING OPEN QUESTIONS`.
This Implementation Authorization froze the four non-blocking items below.
Dependencies were not installed by this document itself; installation occurred
under EFFECTIVE authorization in WS1.

### 4.1 Dependency version policy (NBQ-1)

Repository reality at draft baseline (`ba4eed88…`):

- Python: `requires-python = ">=3.13"` (`apps/api/pyproject.toml`)
- Existing pin style: mostly lower-bound ranges (`>=`); selected exact pins
  (`websockets==16.1`, `pyiceberg[pyarrow,sql-sqlite]==0.11.1`)
- SQLAlchemy is **not** a first-class `bergama-api` dependency today; it appears
  **transitively** via pyiceberg at **2.0.51** in `apps/api/uv.lock`
- Alembic and psycopg are absent from the direct dependency set and lock
  product surface

**Frozen proposed direct dependency specifications** (install occurred in WS1
after EFFECTIVE authorization; do not edit manifests in this status sync):

```text
SQLALCHEMY_DEPENDENCY_SPEC = "sqlalchemy>=2.0.51,<2.1"
ALEMBIC_DEPENDENCY_SPEC = "alembic>=1.14.0,<2"
PSYCOPG_DEPENDENCY_SPEC = "psycopg[binary]>=3.2.0,<4"
```

Rationale:

- Stay on the SQLAlchemy **2.0.x** line already present in the lock (avoid an
  unnecessary jump to 2.1.x during first productization admission)
- Forbid SQLAlchemy 1.x and any async SQLAlchemy / asyncpg stack
- Upper bounds prevent silent major-version admission
- Actual lockfile resolution remains deferred to authorized WS1 (`uv lock` /
  `uv sync --frozen` evidence required)

```text
PROPOSED_AUTHORIZED_DIRECT_DEPENDENCY_COUNT = 3
FOURTH_DIRECT_PRODUCT_DEPENDENCY_AUTHORIZED = NO
```

A transitive dependency pulled by one of the three authorized packages (for
example SQLAlchemy’s conditional `greenlet`) is **not** a separately authorized
direct product dependency and must not be promoted to a fourth direct product
dependency without amendment.

**Explicitly forbidden direct dependencies:**

- `asyncpg`
- `testcontainers` (and equivalents)
- UUID7 / ULID helper packages
- alternative ORM
- alternative migration framework
- second PostgreSQL driver

### 4.2 Psycopg installation mode (NBQ-2)

```text
PSYCOPG_INSTALLATION_MODE = PSYCOPG_BINARY_EXTRA_SYNC
PSYCOPG_DEPENDENCY_SPEC = "psycopg[binary]>=3.2.0,<4"
PSYCOPG_LICENSE = LGPL-3.0-only
PSYCOPG_LICENSE_ACKNOWLEDGED = YES
```

Requirements satisfied by this choice:

- sync only (no asyncpg; no SQLAlchemy asyncio)
- no fourth direct product package beyond the three authorized families
- binary extra improves CI/dev reproducibility without requiring a system
  `libpq` install in the GitHub Actions runner image
- Python 3.13 compatible packaging assumed at install time under WS1 review
- license recorded for technical authorization; this IA does not claim legal
  counsel approval beyond that acknowledgment

### 4.3 Application package path (NBQ-3)

```text
INTELLIGENCE_RUN_PRODUCT_PACKAGE_PATH = apps/api/app/intelligence_runs/
PIPELINE_PACKAGE_PATH = apps/api/app/intelligence_pipeline/
PIPELINE_DB_FREE = YES
```

Naming follows existing snake_case product packages (`intelligence_pipeline`,
`human_review`, `ai_decision_engine`, `dashboard`). The productization package
owns Sprint 14 persistence / materializer / query / HTTP DTO concerns only.
It must not import SQLAlchemy into `intelligence_pipeline/`.

Alembic tree (Architecture AD-14-10):

```text
ALEMBIC_LOCATION = apps/api/alembic/
```

### 4.4 CI PostgreSQL provisioning (NBQ-4)

Current CI (`.github/workflows/ci.yml`) has no PostgreSQL service.

```text
CI_POSTGRES_PROVISIONING_MODE = GITHUB_ACTIONS_POSTGRES_SERVICE_CONTAINER
```

When EFFECTIVE and under WS1:

- Add a GitHub Actions `services: postgres:…` (or equivalent job-level Postgres
  service container) to the existing quality-gate workflow
- Use deterministic test-only DSN via CI environment / service config
- Do not commit secrets
- Do not introduce `testcontainers` or any fourth Python dependency
- Do not require Helm / Kind deploy for unit/integration CI
- Do not deploy the application

CI Postgres service provisioning was authorized under EFFECTIVE IA and delivered
in WS1. This status synchronization does not modify `.github/workflows/ci.yml`.

---

## 5. Dependency Authorization (EFFECTIVE; executed in WS1)

Authorize exactly three direct product dependency families:

1. SQLAlchemy 2.x — sync ORM/Core (`SQLALCHEMY_DEPENDENCY_SPEC`)
2. Alembic — migrations (`ALEMBIC_DEPENDENCY_SPEC`)
3. psycopg 3 sync via binary extra (`PSYCOPG_DEPENDENCY_SPEC`)

Before WS1 install, require:

- exact version/range confirmation against the frozen specs above
- license confirmation (SQLAlchemy MIT; Alembic MIT; psycopg LGPL-3.0-only)
- current advisory / CVE check for the resolved versions
- lockfile diff review
- transitive dependency review
- Python 3.13 compatibility confirmation
- CI compatibility evidence

```text
NEW_DEPENDENCY_AUTHORIZED = YES   # authorized under EFFECTIVE IA; installed in WS1
```

---

## 6. Database / Infrastructure Authorization (EFFECTIVE; executed in WS1)

Authorize PostgreSQL as the Sprint 14 Intelligence Run product OLTP store with:

- sync SQLAlchemy engine / session boundary
- sync psycopg 3 driver
- Alembic at `apps/api/alembic/`
- single primary entity/table family: `intelligence_runs`
- hybrid relational envelope + bounded JSON/JSONB snapshots
- UUID4 `run_id` (Python stdlib; no UUID helper dependency)
- `UNIQUE (pipeline_fingerprint, snapshot_contract_version)`
- indexes supporting frozen latest-dashboard-capable selection
- `as_of` schema-present nullable only where Policy freezes
  (`admission_rejected`)
- `persisted_at`, `outcome`, failure metadata, binding/policy pins, thin
  provenance, stage presence, Dashboard / Human Review / ADE snapshots,
  `snapshot_contract_version`, `persistence_schema_version`

Blocking DB I/O MUST NOT run on the async event loop (prefer sync FastAPI
`def` handlers or an explicit approved threadpool boundary).

Executable SQL / migration files were authorized under EFFECTIVE IA and
delivered in WS1 (Issue #146 / PR #147). This status synchronization does not
alter that schema.

```text
DATABASE_MIGRATION_AUTHORIZED = YES
DATABASE_SCHEMA_IMPLEMENTATION_AUTHORIZED = YES
```

---

## 7. Workstream Authorization

```text
PROPOSED_IMPLEMENTATION_WORKSTREAM_COUNT = 4
PROPOSED_IMPLEMENTATION_ISSUE_COUNT = 4
MERGE_ORDER = WS1 → WS2 → WS3 → WS4
```

Do **not** create the four implementation issues until this IA is EFFECTIVE.

### 7.1 WS1 — Persistence Schema / Repository / Migrations

**Future authorized scope:**

- declare the three authorized direct dependencies and update the lockfile
  solely from that authorized work
- PostgreSQL engine / session configuration
- product persistence models for `intelligence_runs`
- repository protocol / interface
- SQLAlchemy repository implementation
- insert-only persistence
- logical uniqueness and required indexes
- Alembic initialization / configuration
- initial product migration
- migration compatibility verification
- PostgreSQL repository integration tests
- migration tests
- CI PostgreSQL service-container wiring required by these tests
  (`CI_POSTGRES_PROVISIONING_MODE`)

**Forbidden:**

- materializer business / equality implementation beyond repository primitives
  required by WS2
- public HTTP routes
- UI
- pipeline DB coupling
- model / broker / provider changes

### 7.2 WS2 — Materializer / Snapshot Contract

**Future authorized scope:**

- application-layer `IntelligenceRunMaterializer` under
  `apps/api/app/intelligence_runs/`
- input: completed public `PipelineResult` only
- UUID4 allocation
- snapshot construction; canonical serialization; canonical equality
- equal duplicate reuse; unequal duplicate fail closed
- stage-presence construction
- failure-detail sanitization (`FAILURE_DETAIL_MAX_LENGTH = 256`)
- Dashboard / Human Review / ADE bounded public snapshots
- ADE `recorded_attestation_payload` exclusion (FORBIDDEN in product snapshot)
- write validation; read-after-write validation where appropriate
- storage-unavailable handling; identity-conflict handling
- insert-only semantics

**Require:** `PIPELINE_DB_FREE = YES`.

**Forbid:** raw events / provider payloads / unbounded news / raw exceptions /
stack traces / secrets / ORM on wire / update-overwrite-delete / public write
API / ADE invocation / HR write workflow.

### 7.3 WS3 — Query Service / Read API

**Future authorized scope — exactly six GET families:**

1. `GET /api/v1/intelligence/runs/id/{run_id}`
2. `GET /api/v1/intelligence/runs/fingerprint/{fingerprint}`
3. `GET /api/v1/intelligence/runs/latest-dashboard-capable`
4. `GET /api/v1/intelligence/runs/id/{run_id}/dashboard`
5. `GET /api/v1/intelligence/runs/id/{run_id}/human-review`
6. `GET /api/v1/intelligence/runs/id/{run_id}/ade`

Authorize:

- `IntelligenceRunQueryService`
- repository reads
- strict DTO families
- product error handling
- router registration under existing `/api/v1` composition
- scope enforcement
- freshness derivation (`age_seconds` from `persisted_at`)
- latest selection and frozen absence behavior

**Require:**

```text
EXACT_PRODUCT_READ_SCOPE = intelligence:runs:read
API_READ_ALONE = INSUFFICIENT
QUERY_TIME_RECOMPUTATION = NO
PUBLIC_WRITE_API = NO
```

No mutation; no pipeline execution; no ADE invocation; no HR write; no
provider / model / broker calls. Prefer synchronous FastAPI `def` route
handlers for blocking DB work.

### 7.4 WS4 — Productization Hardening / Authorization Firewalls

Authorize only tests and minimal production hardening required for WS1–WS3.

Required coverage includes: canonical equality; serialization determinism;
snapshot / persistence version handling; unsupported / corrupt fail closed;
latest `FAIL_CLOSED_NO_SKIP`; UUID / fingerprint validation; strict DTO
validation; write/read validation; auth 401; authz 403; `api:read`
insufficiency; `intelligence:runs:read` success; no query recomputation;
read-only endpoints; storage 503; stage / run absence 404; invalid identifier
400; unsupported contract 409; corrupt snapshot 500; failure-detail bound; ADE
payload exclusion; ORM-on-wire / raw-provider / secret-stack prohibition;
dependency / pipeline-DB / Feature Platform / provider-expansion / model /
broker firewalls.

WS4 may make minimal production corrections on WS1–WS3 surfaces only. It may
not create new product features or routes.

Limited WS4 test scaffolding may proceed in parallel after WS2 only where it
does not create production scope ahead of WS3. Integrated verification follows
WS4.

---

## 8. Authorized Implementation Issues (sequence COMPLETE)

```text
PROPOSED_IMPLEMENTATION_ISSUE_COUNT = 4
IMPLEMENTATION_SEQUENCE = 4/4 COMPLETE
AUTHORITATIVE_IMPLEMENTATION_BASELINE = 748bc9977a8910565c05705b7467da71c4162de5
POST_MERGE_CI_RUN_ID = 37724824835
```

| Issue | Scope | State |
| --- | --- | --- |
| [#146](https://github.com/enesdedelerr-max/Bergama/issues/146) | WS1 Persistence schema / repository / migrations | COMPLETE (PR #147 @ `1d9c3c7a5c38342fc99c0a64a6e3fc3784b5e545`) |
| [#148](https://github.com/enesdedelerr-max/Bergama/issues/148) | WS2 Materializer / snapshot contract | COMPLETE (PR #149 @ `5975290a5f78637aa323dc8a7c3f13c8226639f6`) |
| [#150](https://github.com/enesdedelerr-max/Bergama/issues/150) | WS3 Query service / read API | COMPLETE (PR #151 @ `236affa60b182006c5844280e0c9084a420d33ca`) |
| [#152](https://github.com/enesdedelerr-max/Bergama/issues/152) | WS4 Productization hardening / authorization firewalls | COMPLETE (PR #153 @ `748bc9977a8910565c05705b7467da71c4162de5`) |

### Issue 1 — WS1 (COMPLETE)

| Field | Value |
| --- | --- |
| TITLE | Sprint 14 — Intelligence Run Persistence Schema / Repository / Migrations |
| PURPOSE | Admit durable PostgreSQL product store + repository + migrations |
| AUTHORIZED_SCOPE | WS1 scope in §7.1 |
| FORBIDDEN_SCOPE | WS1 forbidden list in §7.1 |
| DEPENDENCIES | EFFECTIVE IA; three direct deps; CI Postgres service |
| EXPECTED_PATH_CATEGORIES | `apps/api/app/intelligence_runs/` (persistence), `apps/api/alembic/`, settings/engine wiring, `apps/api/pyproject.toml` + `uv.lock`, CI workflow Postgres service, tests |
| TEST_OBLIGATIONS | repository + PostgreSQL integration + migration upgrade/compat |
| COMPLETION_EVIDENCE | green CI including Postgres-backed tests; fresh Alembic upgrade proof |
| MERGE_ORDER | 1 |
| STATE | COMPLETE — Issue #146 / PR #147 |

### Issue 2 — WS2 (COMPLETE)

| Field | Value |
| --- | --- |
| TITLE | Sprint 14 — Intelligence Run Materializer / Snapshot Contract |
| PURPOSE | Persist completed public `PipelineResult` immutably with equality semantics |
| AUTHORIZED_SCOPE | WS2 scope in §7.2 |
| FORBIDDEN_SCOPE | WS2 forbidden list in §7.2 |
| DEPENDENCIES | WS1 merged |
| EXPECTED_PATH_CATEGORIES | materializer + snapshot modules under `intelligence_runs/`; tests |
| TEST_OBLIGATIONS | materializer, duplicate/equality, serialization, sanitization, ADE payload exclusion |
| COMPLETION_EVIDENCE | equal reuse / unequal conflict proofs; no pipeline DB imports |
| MERGE_ORDER | 2 |
| STATE | COMPLETE — Issue #148 / PR #149 |

### Issue 3 — WS3 (COMPLETE)

| Field | Value |
| --- | --- |
| TITLE | Sprint 14 — Intelligence Run Query Service / Read API |
| PURPOSE | Expose six authenticated GET-only product routes |
| AUTHORIZED_SCOPE | WS3 scope in §7.3 |
| FORBIDDEN_SCOPE | writes; recompute; ADE/HR invoke; provider/model/broker |
| DEPENDENCIES | WS1–WS2 merged |
| EXPECTED_PATH_CATEGORIES | query service, routers, schemas/DTOs, authz scope helper, tests |
| TEST_OBLIGATIONS | HTTP, auth/authz, error mapping, latest selection, absence semantics |
| COMPLETION_EVIDENCE | six-route contract green; scope enforcement proven |
| MERGE_ORDER | 3 |
| STATE | COMPLETE — Issue #150 / PR #151 |

### Issue 4 — WS4 (COMPLETE)

| Field | Value |
| --- | --- |
| TITLE | Sprint 14 — Intelligence Run Productization Hardening / Authorization Firewalls |
| PURPOSE | Determinism, authz, contract, and authority-firewall hardening |
| AUTHORIZED_SCOPE | WS4 scope in §7.4 |
| FORBIDDEN_SCOPE | new product features / routes beyond WS1–WS3 |
| DEPENDENCIES | WS1–WS3 merged (scaffolding after WS2 allowed) |
| EXPECTED_PATH_CATEGORIES | tests + minimal hardening on WS1–WS3 surfaces |
| TEST_OBLIGATIONS | full hardening / firewall / determinism matrix |
| COMPLETION_EVIDENCE | firewall suite green; no authority leakage |
| MERGE_ORDER | 4 |
| STATE | COMPLETE — Issue #152 / PR #153 |

This Implementation Authorization does not authorize additional implementation
beyond the exhausted four-workstream sequence.

---

## 9. Frozen Product Contract (Policy-subordinate; not reinterpreted)

This IA does **not** change Policy. Preserve exactly:

| Item | Frozen value |
| --- | --- |
| PipelineOutcome count | 6 |
| Stage-presence keys | watchlist, gap, catalyst, score, briefing, dashboard, human_review, ade |
| Stage-presence statuses | NOT_EXECUTED, ABSENT, EMPTY, FAILED, PRESENT, ABSTAINED |
| Snapshot contract version | `intelligence-run-productization.snapshot.v1` |
| Persistence schema version | `intelligence-run-productization.persistence.v1` |
| Storage identity | opaque UUID4 |
| Composition identity | pipeline fingerprint |
| Duplicate behavior | canonical equal → reuse; unequal → fail closed |
| GET routes | exactly six families listed in §7.3 |
| Product error families | exactly eight (Policy) |
| `storage_unavailable` | HTTP 503 |
| `materialization_identity_conflict` | no public HTTP mapping (no write API) |
| `admission_rejected` `as_of` | schema-present nullable |
| `failure_detail` | max 256 + sanitization |
| Latest eligibility | Dashboard PRESENT |
| Latest order | `as_of DESC`, `persisted_at DESC`, `run_id ASC` |
| Latest corrupt/unsupported | `FAIL_CLOSED_NO_SKIP` |
| `age_seconds` | from `persisted_at`; non-authoritative; equality-excluded |
| Product read scope | `intelligence:runs:read` |
| `api:read` alone | insufficient |
| HR | bounded public snapshot; write workflow forbidden |
| ADE | bounded public snapshot; `recorded_attestation_payload` FORBIDDEN |
| Query recomputation | NO |
| Public write API | NO |

DTO families (Policy): `IntelligenceRunRead`, `IntelligenceRunDashboardRead`,
`IntelligenceRunHumanReviewRead`, `IntelligenceRunAdeRead`,
`ProductErrorResponse`.

Serialization: UTC ISO-8601; StrEnum string values; lowercase hyphenated UUID;
strict DTOs / `extra=forbid`; validate on write and read.

---

## 10. Test Authorization (future, when EFFECTIVE)

Authorize / require:

- unit tests
- contract tests
- repository tests
- PostgreSQL integration tests
- migration upgrade tests
- migration compatibility / downgrade-safe tests where supported
- materializer tests
- duplicate / equality tests
- serialization tests
- query service tests
- HTTP tests
- auth / authz tests
- error mapping tests
- latest selection tests
- corrupt snapshot tests
- unsupported-version tests
- firewall / leakage tests
- determinism tests

```text
TESTCONTAINERS_PYTHON_DEPENDENCY = FORBIDDEN
CI_POSTGRES_PROVISIONING_MODE = GITHUB_ACTIONS_POSTGRES_SERVICE_CONTAINER
```

CI PostgreSQL provisioning may be added under WS1 using the frozen mode only.

---

## 11. Supply-Chain / License Conditions

Before WS1 dependency installation (after EFFECTIVE):

| Package | License (discovery evidence) | Condition |
| --- | --- | --- |
| SQLAlchemy 2.x | MIT | pin/advisory/lockfile/transitive/Py3.13 review |
| Alembic | MIT | pin/advisory/lockfile/transitive/Py3.13 review |
| psycopg 3 | LGPL-3.0-only | pin/advisory/lockfile/transitive/Py3.13 review + license acknowledgment |

```text
PSYCOPG_LICENSE_ACKNOWLEDGED = YES
```

This document records a technical authorization condition. It does not claim
independent legal counsel approval.

---

## 12. Authorization Firewall

### May become authorized after EFFECTIVE + workstream issues

- the three bounded direct dependency families
- PostgreSQL product persistence
- Alembic migrations
- repository
- materializer
- query service
- six GET endpoints
- `intelligence:runs:read` scope enforcement
- product errors / DTOs
- CI PostgreSQL test service container
- required tests
- minimal WS4 hardening

### Explicitly NOT authorized by this IA (even when EFFECTIVE)

- public write API
- UI
- Human Review write workflow
- ADE invocation from product read surfaces
- pipeline DB coupling
- Feature Platform changes
- live provider expansion / new market-data providers
- model / LLM participation or inference
- broker integration / OMS / order execution / portfolio execution
- tag / release / deploy

```text
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED/DEFERRED
```

---

## 13. Acceptance Criteria

```text
IMPLEMENTATION_AUTHORIZATION_AC_COUNT = 32
```

| ID | Criterion |
| --- | --- |
| IA-01 | Planning/Architecture/Governance/Policy gates established; IA subordinate |
| IA-02 | Exactly 4 workstreams/future issues; merge order WS1→WS2→WS3→WS4 |
| IA-03 | Authorize exactly 3 dependency families: SQLAlchemy 2.x, Alembic, psycopg 3 sync; no silent fourth direct dependency |
| IA-04 | Authorize PostgreSQL product store + synchronous engine/session boundary |
| IA-05 | Authorize Alembic migrations at `apps/api/alembic/` with upgrade and compatibility testing |
| IA-06 | Authorize `intelligence_runs` hybrid schema responsibilities |
| IA-07 | Authorize insert-only repository + logical uniqueness `(pipeline_fingerprint, snapshot_contract_version)` |
| IA-08 | Authorize materializer on completed public `PipelineResult` only; pipeline remains DB-free |
| IA-09 | Authorize equal reuse / unequal identity conflict; no update/delete |
| IA-10 | Authorize exact frozen snapshot/persistence versions |
| IA-11 | Authorize exactly six GET route families; no public write API |
| IA-12 | Authorize read-only query service; no query-time recomputation |
| IA-13 | Authorize Run/Dashboard/HR/ADE/ProductError DTO families |
| IA-14 | Authorize eight product error families + frozen HTTP mappings, including `storage_unavailable` → 503 |
| IA-15 | Materialization identity conflict has no Sprint 14 public HTTP mapping |
| IA-16 | Authorize `intelligence:runs:read`; `api:read` insufficient; preserve 401 vs 403 |
| IA-17 | Authorize latest eligibility/order/`FAIL_CLOSED_NO_SKIP` |
| IA-18 | Authorize `admission_rejected` `as_of` schema-present nullable |
| IA-19 | Authorize HR bounded public snapshot; forbid HR write workflow |
| IA-20 | Authorize ADE bounded public snapshot; forbid `recorded_attestation_payload` |
| IA-21 | Authorize serialization rules: UTC ISO-8601, StrEnum values, lowercase hyphenated UUID, strict `extra=forbid`, validate R/W |
| IA-22 | Authorize `failure_detail` max 256 + sanitization |
| IA-23 | Authorize `age_seconds` derived from `persisted_at`, non-authoritative, equality-excluded |
| IA-24 | Require unit/contract/repository/PostgreSQL integration/migration/materializer/HTTP/authz/determinism/firewall tests |
| IA-25 | Require CI evidence for PostgreSQL-backed tests without unauthorized fourth Python dependency |
| IA-26 | Require dependency pin/license/advisory/lockfile/transitive review before install |
| IA-27 | Forbid UI, Feature Platform changes, live provider expansion |
| IA-28 | Forbid model/LLM participation |
| IA-29 | Forbid broker/OI/OMS/execution |
| IA-30 | Forbid tag/release/deploy under this IA |
| IA-31 | Forbid seventh `PipelineOutcome` and storage/product errors being reinterpreted as pipeline outcomes |
| IA-32 | Implementation remains unauthorized until this IA becomes effective through its own governed review/merge/post-merge-CI lifecycle |

No WS1–WS4 implementation acceptance criteria are satisfied by drafting this
document.

---

## 14. Effectiveness Lifecycle

This artifact is **APPROVED / EFFECTIVE** after completing:

1. Independent review
2. Commit on the documentation branch
3. Push and PR against `main`
4. Required quality-gate CI success on the PR head
5. Required approving review
6. Merge (PR #145 @ `0755b692a13345dc923570b73ea91b0f032f3242`)
7. Post-merge main CI success on the merge SHA

Effects under this APPROVED / EFFECTIVE Authorization:

1. Bounded implementation within this document was authorized.
2. The four authorized workstream issues were created and completed.
3. Model participation remains UNAUTHORIZED.
4. Broker / execution remains DENIED / DEFERRED.
5. Public write API remains UNAUTHORIZED / NOT IMPLEMENTED.
6. UI implementation remains NOT AUTHORIZED BY SPRINT 14.
7. Feature Platform expansion and live-provider expansion remain NOT AUTHORIZED.
8. Sprint 14 remains NOT COMPLETE until separate governance closeout.
9. No fifth implementation workstream and no authorization expansion are granted.

```text
IMPLEMENTATION_COMPLETE = YES
SPRINT_COMPLETE = NO
STATUS_SYNC = IN_PROGRESS / ISSUE_154
SPRINT_COMPLETE ≠ CAPABILITY_AUTHORIZATION
```

---

## 15. Authority Restatement

```text
SPRINT_14_PLANNING_GATE_ESTABLISHED = YES
SPRINT_14_ARCHITECTURE_GATE_ESTABLISHED = YES
SPRINT_14_GOVERNANCE_GATE_ESTABLISHED = YES
SPRINT_14_PRODUCTIZATION_POLICY_CONTRACT_FREEZE_GATE_ESTABLISHED = YES
SPRINT_14_IMPLEMENTATION_AUTHORIZATION_STATUS = APPROVED / EFFECTIVE
SPRINT_14_IMPLEMENTATION_AUTHORIZED = YES
IMPLEMENTATION_SEQUENCE = 4/4 COMPLETE
PROPOSED_AUTHORIZED_DIRECT_DEPENDENCY_COUNT = 3
PROPOSED_IMPLEMENTATION_WORKSTREAM_COUNT = 4
PROPOSED_IMPLEMENTATION_ISSUE_COUNT = 4
IMPLEMENTATION_AUTHORIZATION_AC_COUNT = 32
INTELLIGENCE_RUN_PRODUCT_PACKAGE_PATH = apps/api/app/intelligence_runs/
CI_POSTGRES_PROVISIONING_MODE = GITHUB_ACTIONS_POSTGRES_SERVICE_CONTAINER
PSYCOPG_INSTALLATION_MODE = PSYCOPG_BINARY_EXTRA_SYNC
PSYCOPG_LICENSE_ACKNOWLEDGED = YES
PIPELINE_DB_FREE = YES
PUBLIC_WRITE_API = UNAUTHORIZED / NOT IMPLEMENTED
UI_AUTHORIZED = NO
FEATURE_PLATFORM_CHANGE_AUTHORIZED = NO
LIVE_PROVIDER_EXPANSION_AUTHORIZED = NO
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED/DEFERRED
SPRINT_14_COMPLETE = NO
```
