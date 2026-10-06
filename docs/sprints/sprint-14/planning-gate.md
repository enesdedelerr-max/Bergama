# Sprint 14 Planning Gate — Durable Intelligence Persistence and Read/Query Boundary

**Planning Gate ID:** `sprint-14.planning-gate`
**Proposed theme:** Durable Intelligence Run Persistence and Read/Query Boundary
**Status:** DRAFT
**Sprint number:** 14
**Gate type:** PLANNING GATE
**Document class:** Planning Gate only
**Prerequisite:** Sprint 13 authoritatively COMPLETE — Intelligence Pipeline Integration
**Authoritative main at draft time:** `73fe75bd28ad45555ecf1e911208fbac8b45175e`
**Planning issue:** [#136](https://github.com/enesdedelerr-max/Bergama/issues/136)

This Planning Gate, when APPROVED, authorizes Sprint 14 theme selection, scope
classification, repository sequencing, and opening of a documentation-only
Architecture Gate.

It does **not** approve Architecture, Governance Decisions, Policy / Contract
Freeze, Implementation Authorization, or Implementation.

It does **not** authorize runtime code, dependency changes, migrations, HTTP
endpoint implementation, UI, model participation, broker execution, Feature
Platform mutation, live-provider expansion, tag, release, or deployment.

```text
PLANNING_GATE_APPROVAL ≠ IMPLEMENTATION_AUTHORIZATION
SPRINT_14_IMPLEMENTATION_AUTHORIZED = NO
RUNTIME_CHANGE_AUTHORIZED = NO
DEPENDENCY_CHANGE_AUTHORIZED = NO
DATABASE_MIGRATION_AUTHORIZED = NO
HTTP_ENDPOINT_IMPLEMENTATION_AUTHORIZED = NO
UI_AUTHORIZED = NO
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED / DEFERRED
TAG_RELEASE_DEPLOY_AUTHORIZED = NO
```

---

## 1. Identity / Status

| Field | Value |
| --- | --- |
| Planning Gate ID | `sprint-14.planning-gate` |
| Status | DRAFT |
| Sprint | 14 |
| Theme | Durable Intelligence Run Persistence and Read/Query Boundary |
| Planning issue | #136 |
| Approves Architecture | No |
| Approves Governance | No |
| Approves Policy / Contract Freeze | No |
| Approves Implementation Authorization | No |
| Approves Implementation | No |
| UI authorized | NO |
| Write / command API authorized | NO |
| Feature Platform change authorized | NO |
| Live-provider expansion authorized | NO |
| MODEL PARTICIPATION | UNAUTHORIZED |
| Broker Execution | DENIED / DEFERRED |
| Next eligible process step | Sprint 14 Architecture Gate Discovery |

---

## 2. Authoritative Baseline

| Field | Value |
| --- | --- |
| Authoritative main | `73fe75bd28ad45555ecf1e911208fbac8b45175e` |
| Sprint 13 status | AUTHORITATIVELY COMPLETE |
| Sprint 13 closeout | Issue #134 / PR #135 |
| Post-merge CI | run `37403744433` / quality-gate job `112076543373` / success |
| Sprint 13 closeout artifact | `docs/sprints/sprint-13/CLOSEOUT.md` |

---

## 3. Prior Sprint Boundary

Sprint 13 delivered an in-process Intelligence Pipeline composition:

Watchlist → Gap → Catalyst → Score → Briefing → Dashboard → optional Human
Review → optional ADE.

Sprint 13 established:

```text
IMPLEMENTATION_COMPLETE = YES
GOVERNANCE_CLOSEOUT = COMPLETE
SPRINT_COMPLETE = YES
SPRINT_COMPLETE ≠ CAPABILITY_AUTHORIZATION
```

Sprint 13 explicitly deferred and did **not** authorize:

- durable product persistence
- HTTP / query product APIs
- Premarket Command Center UI
- Feature Platform mutation
- live-provider expansion
- model / LLM participation
- broker / OI / OMS execution

Sprint 13 completion only made:

```text
SEPARATE_SPRINT_14_PLANNING_GATE_DISCOVERY
```

eligible. It did not authorize Sprint 14 implementation.

---

## 4. Problem Statement

Completed Intelligence Pipeline runs exist only as in-process `PipelineResult`
values. There is no durable run identity, no authenticated retrieval surface,
and no stable query boundary that a Premarket Command Center UI could safely
consume without re-running intelligence.

The productization gap is therefore:

```text
in-process composition (Sprint 13)
  → durable immutable run persistence + versioned read/query (Sprint 14 candidate)
  → read-only Premarket Command Center UI (Sprint 15 candidate / separate gate)
```

---

## 5. Sprint 14 Theme

```text
THEME = Durable Intelligence Run Persistence and Read/Query Boundary
```

---

## 6. Sprint Goal

Make completed Intelligence Pipeline runs durably retrievable through a
versioned, authenticated read/query boundary that preserves deterministic
identity, terminal outcomes, public outputs, and thin provenance without
introducing UI, command/write surfaces, model participation, broker execution,
Feature Platform mutation, or live-provider expansion.

This goal is a planning target only. It is not implementation authority.

---

## 7. Why This Sprint Exists

1. Sprint 13 locked composition semantics; product consumers still cannot
   retrieve completed runs without recomputation.
2. Architecture AD-13-10 / Sprint 13→14→15 boundary already deferred
   persistence + repositories + read models + versioned HTTP/query to Sprint 14
   and UI to Sprint 15.
3. Combining durable persistence with a read/query boundary in one sprint avoids
   a persistence-only dead end while still keeping UI out of scope.
4. Write/command surfaces, model participation, and broker execution remain
   separately governed and are not required for first Premarket read/display
   readiness.

---

## 8. Candidate In Scope

Planning candidates only (not implementation authorization):

1. Durable immutable intelligence-run persistence
2. Postgres-backed run storage
3. Persistence schema / repository planning
4. Migration planning
5. `PipelineResult` / public-output snapshot materialization
6. Run identity / fingerprint / as_of preservation
7. Policy / config / binding pin preservation
8. Six terminal outcome preservation
9. Thin provenance preservation
10. Dashboard public-output snapshot retrieval
11. Optional HR output / status read visibility when HR ran
12. Optional ADE result read visibility when ADE ran
13. Query service boundary
14. Versioned authenticated HTTP read API
15. Latest successful run lookup
16. Run-by-id / fingerprint lookup
17. Dashboard-by-run / latest retrieval
18. Outcome / as_of / policy-pin retrieval
19. Provenance retrieval
20. Deterministic retrieval semantics
21. Public freshness semantics
22. Product read authorization
23. Migration / repository / contract / authz / authority-firewall test planning

---

## 9. Explicit Out of Scope

- Write / command APIs
- Pipeline execution trigger API
- Manual rerun API
- Human Review submission
- Human Review attestation capture workflow
- ADE command / invocation API
- Configuration mutation
- Premarket Command Center UI
- All other UI
- Feature Platform mutation
- Feature Store expansion
- TD-001 remediation unless separately governed
- Live market / news / provider expansion
- Model / LLM SDKs
- Model inference
- Autonomous recommendation authority
- Broker adapters
- Order Intent (OI)
- OMS
- Order generation / order submission
- Portfolio / risk execution authority
- Tag / release / deployment
- Unbounded raw provider payload persistence
- Unbounded raw news persistence
- Internal stack-trace persistence
- Query-time intelligence recomputation

---

## 10. Persistence Boundary

### REQUIRED candidates

| Artifact | Classification |
| --- | --- |
| Pipeline run identity | REQUIRED |
| Pipeline fingerprint | REQUIRED |
| Original UTC `as_of` | REQUIRED |
| Policy / config / binding pins | REQUIRED |
| Terminal outcome | REQUIRED |
| `failed_stage` / failure metadata when applicable | REQUIRED |
| Thin provenance | REQUIRED |
| Dashboard public output snapshot | REQUIRED |

### OPTIONAL / Architecture Gate

| Artifact | Classification |
| --- | --- |
| Watchlist / Gap / Catalyst / Score / Briefing payloads | OPTIONAL |
| HR output / attestation presence when HR ran | OPTIONAL READ SNAPSHOT |
| ADE output when ADE ran | OPTIONAL READ SNAPSHOT |
| Recent run history depth / pagination | USEFUL_BUT_DEFER |

### DO NOT PERSIST

| Artifact | Classification |
| --- | --- |
| Secrets / credentials | DO_NOT_PERSIST |
| Unbounded provider payloads | DO_NOT_PERSIST |
| Unbounded news dumps | DO_NOT_PERSIST |
| Full internal stack traces | DO_NOT_PERSIST |
| Live recomputed intelligence | DO_NOT_PERSIST |

Candidate persistence semantics:

```text
IMMUTABLE_OR_APPEND_ORIENTED_RUN_RECORDS = YES
IN_PLACE_MUTATION_OF_RUN_IDENTITY_OR_OUTCOME = NO
```

---

## 11. Authoritative Data Boundary

Authoritative crossing artifacts remain Sprint 13 public contracts:

- `PipelineResult`
- stage public outputs already produced by the pipeline
- `PipelineProvenance`
- pipeline fingerprint
- terminal `PipelineOutcome`

Persistence must **snapshot** those contracts. Persistence and query layers
must not reinterpret, recompute, or invent intelligence semantics.

Preferred storage shape:

- immutable / append-oriented run record
- stored public snapshots and/or normalized projections of public DTOs

References alone are insufficient for Premarket UI readiness without re-running
the pipeline.

---

## 12. Read / Query Boundary

### REQUIRED_FOR_FIRST_UI

- latest successful pipeline run
- run by stable ID / fingerprint
- Dashboard by run
- latest Dashboard
- terminal outcome
- run `as_of`
- policy / config pins
- thin provenance
- HR output / status when present
- ADE result when present

### USEFUL_BUT_DEFER

- recent run history (minimal page optional; Architecture Gate decides)

### NOT AUTHORIZED

- any write / command endpoint
- pipeline trigger
- HR submit
- ADE invoke
- configuration mutation

```text
HTTP_READ_API_REQUIRED_FOR_SPRINT_14 = YES
WRITE_API_REQUIRED_FOR_SPRINT_14 = NO
WRITE_API_AUTHORIZED = NO
```

---

## 13. Write / Command Boundary

```text
WRITE_API_REQUIRED_FOR_SPRINT_14 = NO
```

Pipeline trigger, manual rerun, HR submission, ADE invocation, and configuration
mutation remain out of Sprint 14. Materialization for tests/ops may be planned as
in-process integration without a public command API. Architecture Gate must keep
write/command surfaces unauthorized unless a later separate gate reopens them.

---

## 14. Human Review Boundary

Distinguish:

| Concern | Sprint 14 planning classification |
| --- | --- |
| Read / display existing HR output from a completed run | CANDIDATE IN SCOPE |
| Capture / submit HR attestation | DEFERRED |

```text
HR_ATTESTATION_PERSISTENCE_FOR_CAPTURE = DEFERRED_TO_LATER_WRITE_WORKFLOW
HUMAN_REVIEW_WRITE_UI_READY_AFTER_SPRINT_14 = NO
```

Sprint 14 must not authorize HR submission endpoints or write UI.

---

## 15. ADE Boundary

Sprint 14 may plan **read visibility** of already-produced ADE results stored
with a completed run.

Sprint 14 must not authorize:

- ADE invocation endpoint
- model inference
- model SDK
- new ADE authority
- autonomous trading authority

ADE remains governed by its existing foundation and Human Review admission rules.
MODEL PARTICIPATION remains UNAUTHORIZED.

```text
ADE_VISIBILITY_UI_READY_AFTER_SPRINT_14 = YES  # read/display eligibility only
```

---

## 16. Replay / Determinism Constraints

Planning must preserve:

- one original run `as_of` (UTC)
- deterministic pipeline fingerprint
- policy / config / binding pins
- terminal outcome
- stage-presence semantics
- thin provenance
- six frozen terminal outcomes

Persistence/query must not:

- overwrite authoritative run identity or terminal outcome in place
- recompute intelligence at query time
- invent a seventh outcome family

---

## 17. Failure / Empty / Abstention Semantics

Preserve exactly these six terminal outcomes:

1. `admission_rejected`
2. `required_stage_failed`
3. `completed_dashboard`
4. `completed_human_review`
5. `completed_ade_accept`
6. `completed_ade_abstain`

Preserve typed distinction between:

- empty success
- valid absence
- stage failure
- admission rejection
- ADE abstention
- HR-only completion
- Dashboard-only completion

Do **not** collapse these into a generic NULL semantics for product consumers.

```text
PIPELINE_OUTCOME_COUNT = 6
```

---

## 18. Security / Data Minimization

Do not plan persistence or read exposure of:

- secrets / credentials / tokens
- unbounded raw provider payloads
- unbounded raw news dumps
- full internal exception stacks
- unnecessary duplicated evidence blobs

Prefer public contracts, fingerprints, pins, and bounded failure metadata.
Product read authorization is a Sprint 14 planning candidate; write authz for
command surfaces is out of scope.

---

## 19. Existing Infrastructure Fit

| Area | Current state |
| --- | --- |
| FastAPI | Present |
| Health / auth routers | Present |
| Intelligence Pipeline HTTP | Absent |
| Postgres | Intended product DB; optional TCP health today |
| SQLAlchemy | Architecture-documented; not first-class API dependency |
| Alembic | Architecture-documented; no migrations tree for product intelligence runs |
| Repository precedents | In-memory Protocols (orders / portfolio) |
| Pipeline tables | None |

Sprint 14 can extend FastAPI and intended Postgres conventions without requiring
a new database product, new event bus, or Feature Store.

---

## 20. Dependency / Infrastructure Governance

Discovery finding:

```text
NEW_INFRASTRUCTURE_REQUIRED = YES
NEW_DEPENDENCY_REQUIRED = YES
NEW_INFRASTRUCTURE_AUTHORIZED = NO
NEW_DEPENDENCY_AUTHORIZED = NO
```

SQLAlchemy / Alembic (or an Architecture-approved equivalent persistence stack)
must be explicitly decided and authorized by Architecture / Governance /
Implementation Authorization before implementation. This Planning Gate does
**not** authorize installing dependencies, editing lockfiles, or creating
migrations.

---

## 21. Feature Platform Boundary

```text
FEATURE_PLATFORM_CHANGE_REQUIRED_FOR_SPRINT_14 = NO
FEATURE_PLATFORM_CHANGE_AUTHORIZED = NO
```

TD-001 calendar remediation remains deferred separate quality work unless later
governance explicitly changes that decision.

---

## 22. Model / Broker Authority Firewall

```text
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED / DEFERRED
```

Reject any Sprint 14 scope that introduces:

- LLM / model SDKs
- model inference / routing
- autonomous recommendations
- order generation / submission
- broker adapters
- OI / OMS
- portfolio / risk execution authority

---

## 23. UI / Live Provider Boundary

```text
UI_REQUIRED_IN_SPRINT_14 = NO
UI_AUTHORIZED_IN_SPRINT_14 = NO
LIVE_PROVIDER_EXPANSION_REQUIRED = NO
LIVE_PROVIDER_EXPANSION_AUTHORIZED = NO
```

Any Premarket Command Center UI requires a separate Sprint 15 (or later)
governance process after a stable Sprint 14 query boundary exists.

---

## 24. Required Governance Sequence

```text
1. Planning Gate
2. Architecture Gate
3. Governance Gate
4. Productization Policy / Contract Freeze
5. Implementation Authorization
6. Bounded implementation issues
```

Planning discovery recommends a **combined** Productization Policy / Contract
Freeze covering persistence semantics and versioned read/query contracts, unless
Architecture Gate proves a split freeze is necessary.

---

## 25. Proposed Future Implementation Decomposition

```text
PROPOSED_FUTURE_IMPLEMENTATION_ISSUE_COUNT = 4
```

Proposed future issues only — **do not create now**:

1. Intelligence run persistence schema, repository, and migrations
2. Pipeline durable materialization / authoritative snapshot integration
3. Read/query service and versioned authenticated HTTP read API
4. Contract, retrieval determinism, authz, security, and authority-firewall hardening

---

## 26. Dependency Order

```text
schema / repository / migrations
  → PipelineResult durable materialization
  → query service
  → HTTP read API
  → contract / authz / determinism / firewall hardening
```

Architecture Gate may refine ordering. Planning does not freeze implementation
details beyond what is required for scope control.

---

## 27. Planning-Level Definition of Done

Candidate Sprint 14 completion criteria (planning targets only):

- durable immutable run records
- stable latest / by-id / by-fingerprint retrieval
- fingerprint / as_of / policy pins preserved
- six terminal outcomes preserved
- Dashboard retrievable without recomputation
- optional HR / ADE results readable when present
- typed empty / absence / failure / abstention semantics
- versioned authenticated read-only API
- migration / repository / retrieval / contract tests
- authority-firewall tests
- no write API
- no UI
- no Feature Platform mutation
- no live-provider expansion
- no model participation
- no broker execution

---

## 28. Product Readiness After Sprint 14

| Capability | After successful Sprint 14 |
| --- | --- |
| Premarket Command Center UI readiness | YES — read/display eligibility only; still requires Sprint 15 planning |
| ADE visibility UI readiness | YES — read/display eligibility only |
| Human Review write UI readiness | NO — write/submit remains separately authorized |

```text
PREMARKET_COMMAND_CENTER_UI_READY_AFTER_SPRINT_14 = YES
ADE_VISIBILITY_UI_READY_AFTER_SPRINT_14 = YES
HUMAN_REVIEW_WRITE_UI_READY_AFTER_SPRINT_14 = NO
```

---

## 29. Risks / Open Questions

1. Exact persistence stack authorization (SQLAlchemy/Alembic vs Architecture-
   approved alternative) remains open until Architecture / Governance /
   Implementation Authorization.
2. Whether Watchlist / Gap / Catalyst / Score / Briefing payloads are stored in
   full or derived from Dashboard refs is an Architecture Gate decision.
3. Recent run history depth / pagination is useful-but-defer.
4. Combined vs split Productization Policy / Contract Freeze awaits Architecture.
5. Product read authz model (reuse existing auth vs new product roles) awaits
   Architecture / Governance.
6. Unrelated open repository PRs (#81, #22) must not be conflated with Sprint 14
   scope.

---

## 30. Non-Authorization Statement

```text
PLANNING_GATE_APPROVAL ≠ IMPLEMENTATION_AUTHORIZATION
SPRINT_14_IMPLEMENTATION_AUTHORIZED = NO
RUNTIME_CHANGE_AUTHORIZED = NO
DEPENDENCY_CHANGE_AUTHORIZED = NO
DATABASE_MIGRATION_AUTHORIZED = NO
HTTP_ENDPOINT_IMPLEMENTATION_AUTHORIZED = NO
UI_AUTHORIZED = NO
WRITE_API_AUTHORIZED = NO
FEATURE_PLATFORM_CHANGE_AUTHORIZED = NO
LIVE_PROVIDER_EXPANSION_AUTHORIZED = NO
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED / DEFERRED
TAG_RELEASE_DEPLOY_AUTHORIZED = NO
```

No implementation issue, branch, dependency change, migration, or pull request
may claim implementation authority merely because this Planning Gate is drafted
or later APPROVED.

---

## 31. Next Gate

```text
NEXT_GATE = SPRINT_14_ARCHITECTURE_GATE_DISCOVERY
```

Do not start Architecture Gate artifacts, Implementation Authorization, or
implementation from this Planning Gate alone.

Mandatory sequence remains Planning → Architecture → Governance →
Productization Policy / Contract Freeze → Implementation Authorization →
bounded implementation.
