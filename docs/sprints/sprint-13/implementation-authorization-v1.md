# Intelligence Pipeline Implementation Authorization v1

**Authorization ID:** `intelligence-pipeline.implementation-authorization.v1`
**Title:** Intelligence Pipeline Implementation Authorization v1
**Version:** v1
**Status:** DRAFT / NOT YET APPROVED
**Document class:** Implementation Authorization
**Sprint:** 13
**Theme:** Intelligence Pipeline Integration
**Bounded context:** Intelligence Pipeline (application-layer composer)
**Authorized package (future, not created by this document):** `apps/api/app/intelligence_pipeline/`
**Implementation Authorization issue:** [#124](https://github.com/enesdedelerr-max/Bergama/issues/124)

```text
THIS DOCUMENT DOES NOT AUTHORIZE IMPLEMENTATION WHILE DRAFT.
IMPLEMENTATION_AUTHORIZATION = DENIED
IMPLEMENTATION_WORK_STARTED = NO
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED / DEFERRED
```

Implementation may begin only after this Authorization becomes
**APPROVED / EFFECTIVE** through repository process.

---

## Authority Statement

This Implementation Authorization freezes the **minimum** implementation
surface permitted to realize already-approved Sprint 13 Intelligence Pipeline
Planning, Architecture, Governance, and Policy.

It does **not**:

- redefine Planning, Architecture, Governance, or Policy
- create new domain semantics for Watchlist, Gap, Catalyst, Score, Briefing,
  Dashboard, Human Review, or ADE
- authorize model participation
- authorize trading or execution
- authorize persistence, HTTP product APIs, or UI
- create implementation issues, runtime code, or `apps/api/app/intelligence_pipeline/`
- mark Sprint 13 complete

While **DRAFT / NOT YET APPROVED**, implementation remains **DENIED**.

---

## Prerequisites

| Prerequisite | Process state |
| --- | --- |
| `sprint-13.planning-gate` | APPROVED / EFFECTIVE |
| `intelligence-pipeline.architecture.v1` | APPROVED / EFFECTIVE |
| `intelligence-pipeline.governance.v1` | APPROVED / EFFECTIVE |
| `intelligence-pipeline.policy.v1` | APPROVED / EFFECTIVE |

Referenced existing governed stage policies / contracts (do not reopen; do not
copy ownership):

- Watchlist public contracts
- Gap public contracts
- Catalyst public contracts
- `premarket.scoring.policy.v1`
- `morning-briefing.policy.v1`
- `dashboard.policy.v1`
- `human-review.policy.v1`
- `ai-decision-engine.policy.v1`

Policy merge evidence: PR #123 MERGED @
`406c9f486c09faab36d41a0c2a1eea81a0741828`; post-merge CI `37225927074`
SUCCESS.

---

## Objective

Authorize a bounded **in-process** Intelligence Pipeline composer that:

1. admits one governed pipeline run
2. propagates one UTC run-level `as_of`
3. invokes existing public stage contracts in approved topology
4. preserves Gap / Catalyst empty-success outputs as-is into Score
5. emits Policy-frozen composition terminal outcome families
6. pins governed Policy / config bindings for the run and replay
7. preserves thin composition provenance
8. supports thin in-process deterministic replay
9. optionally invokes Human Review and ADE under existing Policies
10. remains non-executable and non-productized for Sprint 13

---

## Authorized Runtime Boundary

**Authorized future package:**

```text
apps/api/app/intelligence_pipeline/
```

No other runtime package is authorized by this gate.

**EXISTING_STAGE_PACKAGE_MODIFICATION_REQUIRED = NO**

Future implementation must compose existing public contracts. It must not
modify stage algorithms merely to make Pipeline composition easier.

Recommended minimum coherent surface (filename choice is implementation
detail where not required for governance; package path and semantic
deliverables are authoritative):

| Recommended file | Purpose |
| --- | --- |
| `__init__.py` | Controlled exports |
| `models.py` | Request / result / binding / outcome types |
| `admit.py` | Run admission |
| `orchestrator.py` (or equivalent `engine.py`) | Deterministic composition |
| `errors.py` | Thin composition errors |
| `provenance.py` | Composition provenance |
| `replay.py` | In-process replay / equality |
| `policy.py` | Outcome / Policy ID constants |

---

## Authorized Implementation Sequence

After this Authorization is **APPROVED / EFFECTIVE**, exactly **three**
bounded future implementation issues may be created. They are **not** created
by this document or its creation task.

### Future Issue 1 — Core admission + orchestration through Dashboard

**Dependencies:** this Implementation Authorization APPROVED / EFFECTIVE

**Scope:**

- Pipeline request / admission
- single UTC `as_of`
- Watchlist, Gap, Catalyst, Score, Morning Briefing, Dashboard invocation
- Policy / config pinning needed by core stages
- composition outcome / result for Dashboard terminal
- core provenance
- core fail-closed behavior
- core unit / contract / integration tests

### Future Issue 2 — Optional Human Review + ADE terminals

**Dependencies:** Future Issue 1 completed / accepted

**Scope:**

- explicit HR request + attestation
- Dashboard → Human Review
- valid HR → optional ADE
- invalid HR → no ADE
- terminals: `completed_human_review`, `completed_ade_accept`,
  `completed_ade_abstain`
- no synthetic approval; no model authority; no execution consequence
- terminal tests

### Future Issue 3 — Replay / determinism / provenance and authority-firewall hardening

**Dependencies:** Future Issue 1; Future Issue 2 where HR / ADE replay coverage
is included

**Scope:**

- thin in-process replay and equality
- original `as_of`, canonical admitted evidence, pinned bindings, explicit
  human input when applicable, terminal outcome equality
- composition provenance hardening
- forbidden import / dependency checks
- authority firewall tests

```text
RECOMMENDED_IMPLEMENTATION_ISSUE_COUNT = 3
IMPLEMENTATION_ISSUES_CREATED_BY_THIS_GATE = 0
```

---

## Public Contract Reuse

Future implementation SHALL compose these **public typed** entrypoints:

| Stage | Entrypoint |
| --- | --- |
| Watchlist | `generate_watchlist(WatchlistGenerationRequest)` |
| Gap | `scan_gaps(GapScanRequest)` |
| Catalyst | `normalize_catalysts(CatalystNormalizationRequest)` |
| Score | `scan_scores(ScoreRequest)` |
| Morning Briefing | `assemble_briefing(BriefingRequest)` |
| Dashboard | `assemble_dashboard(DashboardRequest)` |
| Human Review | `assemble_human_review(HumanReviewRequest)` |
| ADE | `evaluate_ade(AdeEvaluationRequest)` |

Private / internal entrypoints MUST NOT be used.

`*_from_parts` helpers are **not** the default composition boundary. They may
be used only if future implementation proves they preserve the same governed
validation contract and a later issue explicitly documents that equivalence.
Strong default: typed request entrypoints.

---

## Run Admission

Authorize a bounded typed Pipeline request / admission model.

**Required semantic inputs:**

- `as_of` (UTC-aware)
- Watchlist candidates + governed Watchlist config
- canonical Gap bar evidence + governed Gap config
- canonical Catalyst `NewsEvent` evidence + governed Catalyst config
- governed Score / Briefing / Dashboard configs (or pinned stage defaults)

**Optional governed inputs:**

- `hr_requested`
- explicit HR attestation / input when HR requested
- HR config / binding
- `ade_requested`
- ADE config / binding
- `PremarketSettings` only if existing stage contracts require it

**Forbidden inputs:**

- provider-native payloads
- unbounded dict / config bags
- model inputs
- broker / Order Intent / OMS inputs
- Feature Platform handles
- live-clock dependencies

---

## Temporal Contract

Freeze:

- one authoritative run-level `as_of`
- UTC-aware
- same `as_of` propagated across stage contracts where applicable
- no wall-clock advancement
- no current-time substitution during replay

Reuse existing helper where appropriate:

`app.market_data.timing.require_utc_aware`

```text
NEW_TEMPORAL_HELPER_REQUIRED = NO
```

Do not create a second temporal validation framework. Stage PIT / `known_at`
validation remains stage-owned.

---

## Stage Topology

Deterministic composition topology (Architecture / Governance / Policy):

```text
Watchlist
   → Gap + Catalyst
   → Score
   → Morning Briefing
   → Dashboard
   → optional Human Review
   → optional ADE
```

Watchlist stage MUST execute via public contract from canonical candidates.
Do not authorize provider discovery. Do not authorize bypassing Watchlist by
accepting only a pre-generated Watchlist as the sole normal execution path.

Gap and Catalyst are mandatory topology stages even though Score treats their
collections as authorized optional **inputs**.

---

## Gap / Catalyst Empty-Success Invariant

```text
GAP_EXECUTION_REQUIRED = YES
EMPTY_GAP_PRESERVED = YES
CATALYST_EXECUTION_REQUIRED = YES
EMPTY_CATALYST_PRESERVED = YES
```

Successful empty `GapCollection` / `CatalystCollection` are valid stage
success and MUST be passed to Score **as-is**.

They MUST NOT be silently rewritten to `None`.

This is a blocking invariant: empty `CatalystCollection` and `None` have
different Score feature semantics (`presence=0` vs AbsentFeature).

Gap / Catalyst failure stops the run under fail-closed semantics.

---

## Continuation / Failure Semantics

Implementation SHALL follow Policy PD-13-02:

| Situation | Outcome |
| --- | --- |
| Invalid admission | STOP |
| Watchlist failure | STOP |
| Watchlist empty success | CONTINUE |
| Gap failure | STOP |
| Gap empty success | CONTINUE (as-is) |
| Catalyst failure | STOP |
| Catalyst empty success | CONTINUE (as-is) |
| Score failure | STOP |
| Score valid empty success | CONTINUE |
| Briefing failure | STOP |
| Briefing valid empty success | CONTINUE |
| Dashboard failure | STOP |
| Dashboard success + HR not requested | `completed_dashboard` |
| HR requested | invoke only under HR public contract |
| Invalid / missing HR admission | no ADE |
| Valid HR + ADE not requested | `completed_human_review` |
| Valid HR + ADE requested | ADE may be invoked |
| ADE accept | `completed_ade_accept` |
| ADE abstain | `completed_ade_abstain` |

Not authorized: automatic retries, fallback providers, stage skipping,
fabricated evidence, or recovery semantics not already governed.

---

## Composition Outcomes

Exactly six composition terminal / outcome families (Policy PD-13-03):

1. `admission_rejected`
2. `required_stage_failed`
3. `completed_dashboard`
4. `completed_human_review`
5. `completed_ade_accept`
6. `completed_ade_abstain`

```text
OUTCOME_FAMILY_COUNT = 6
```

These are composition classification labels only.

- Stage reason families remain stage-owned.
- `completed_human_review` does **not** mean trade approval.
- `completed_ade_accept` does **not** mean trade approval, Order Intent, OMS
  submission, Broker submission, or execution.

---

## Failure / Error Surface

Authorize only a thin composition-level error surface. Implementation may
define the minimum necessary:

- admission validation error
- composition / stage-execution wrapper preserving upstream context
- replay mismatch / equality error if needed

Exact Python class names are **not** frozen by this Authorization unless
repository precedent later requires it.

Do not create a Pipeline-owned copy of stage reason taxonomies.

---

## Policy / Config Binding

Governed stage Policy / config bindings are selected / pinned at admission,
remain stable through the run, and are reused on replay.

Reuse existing stage config objects / fingerprints and Policy identifiers.
No silent latest-version substitution mid-run or on replay.

Not authorized: new global config service, registry platform, DB config store,
new hashing platform, DI framework, message bus, cache, or serialization
platform.

---

## Provenance

Authorize a thin composition provenance representation sufficient to preserve:

- run `as_of`
- stage execution fact
- stage public output / reference
- upstream provenance references
- governed Policy / config bindings
- explicit HR input / output when applicable
- ADE output when applicable
- terminal outcome

Not authorized: provider-native raw payload storage, secrets, unbounded
evidence bags, or a new provenance platform.

---

## Replay

Authorize thin **in-process** deterministic replay only (Policy PD-13-05).

Replay MUST preserve:

- original `as_of`
- canonical admitted evidence
- governed Policy / config bindings
- explicit human input when applicable
- stage public-output semantics
- terminal composition outcome

Replay MUST NOT: refetch live providers; advance wall clock; substitute newer
Policy / config; fabricate evidence or human approval; invoke models or
brokers.

Not authorized: durable replay store, database replay persistence, HTTP replay
endpoint, or public replay productization.

---

## Identity / Fingerprint Boundary

Authorize deterministic composition identity / fingerprint only as required
for provenance / replay / reference.

Exact hashing algorithm is not frozen unless repository precedent requires it.
Existing deterministic canonical hashing helpers may be reused as **tooling
only** if semantically appropriate.

If `strategy_sha256` or a Strategy-namespaced helper is reused, it MUST be
treated only as a deterministic hashing utility and MUST NOT transfer Strategy
authority or Strategy semantics into the Pipeline.

Prefer a domain-neutral helper if one already exists. No new hash dependency.

---

## Human Review Boundary

Optional composition into existing Human Review public contract:

- HR must be explicitly requested
- required human attestation / input must be explicit
- Dashboard public output is the governed upstream input
- no synthetic attestation
- no inferred approval
- no automatic approval
- no human authority transfer
- HR stage reasons remain HR-owned
- if HR cannot produce valid authorized public output → ADE MUST NOT be invoked

```text
HUMAN_AUTHORITY_TRANSFER = NO
AUTOMATIC_HUMAN_APPROVAL = NO
```

---

## ADE Boundary

Optional composition into existing ADE public contract only after valid
authorized Human Review public output:

- ADE requested explicitly
- valid HR public output required
- ADE acceptance criteria remain ADE-owned
- ADE abstention reasons remain ADE-owned
- no model inference / SDK
- no execution consequence

```text
MODEL_PARTICIPATION = UNAUTHORIZED
```

---

## Public Export Boundary

Authorize controlled explicit exports only:

- Pipeline run / orchestration entrypoint
- request / result public models
- outcome family public type / constants
- required provenance public types
- replay / assert helper if intentionally public
- thin public errors where justified

Do not export private adapters, provider internals, mutable config internals,
stage private helpers, or implementation-only machinery.

Require controlled `__all__` consistent with repository precedent.

---

## Testing Requirements

Authorize tests only under:

```text
apps/api/tests/unit/test_intelligence_pipeline_*.py
apps/api/tests/contract/test_intelligence_pipeline_*.py
apps/api/tests/integration/test_intelligence_pipeline_*.py
```

Required categories: unit; contract; integration / boundary; replay /
determinism; authority / import firewall.

Required scenarios include:

- Dashboard happy path
- empty Watchlist
- empty GapCollection preserved
- empty CatalystCollection preserved
- Gap / Catalyst / Score / Briefing / Dashboard failure → STOP
- HR not requested → `completed_dashboard`
- valid requested HR → `completed_human_review` when ADE not requested
- invalid HR → no ADE
- valid HR + ADE accept / abstain
- single `as_of` propagation; UTC validation; PIT / future-data fail-closed
- Policy / config binding stability; replay equality; no live refetch
- no model / broker / persistence / HTTP product API / UI / Feature Platform
  mutation dependencies

---

## Security Controls

Implementation MUST include controls / tests for:

- future-data leakage
- timestamp / `as_of` spoofing
- Policy / config drift
- provenance spoofing
- stage-output fabrication
- empty-success → `None` rewrite
- unbounded evidence
- provider-native payload leakage
- secret leakage
- synthetic human approval
- HR bypass
- ADE bypass
- model authority leakage
- broker / execution leakage
- replay substitution

Do not create a new security platform.

---

## Dependency Rule

```text
NEW_DEPENDENCY_REQUIRED = NO
```

No dependency manifest change. No lockfile change. No external package. No
third-party code adoption.

Specifically no implementation adoption from AutoHedge, Vibe-Trading, or
Fincept Terminal.

---

## Market Data Boundary

Pipeline MUST remain separate from `MarketDataOrchestrator`.

Do not authorize expansion of MarketDataOrchestrator into Intelligence
Pipeline orchestration. Market / provider acquisition remains upstream.
Pipeline consumes canonical governed evidence only. Reverse dependency from
Market Data into Pipeline authority must not be introduced.

---

## Feature Platform Firewall

```text
FEATURE_PLATFORM_CHANGE_REQUIRED = NO
```

Not authorized: Feature Store changes, Feature materialization changes, Redis
online-store work, Postgres offline-store work, Sprint 6 remediation.

---

## Productization Firewall

```text
SPRINT_13_PRODUCT_PERSISTENCE = NOT AUTHORIZED
SPRINT_13_HTTP_PRODUCT_API = NOT AUTHORIZED
UI_AUTHORIZED = NO
SPRINT_14_AUTHORIZED = NO
SPRINT_15_UI_AUTHORIZED = NO
```

Not authorized: DB tables, migrations, product repositories, read models,
REST / GraphQL / websocket product APIs, frontend components, public freshness
endpoint, durable replay product.

---

## Trading Firewall

```text
BROKER_EXECUTION = DENIED / DEFERRED
LIVE_TRADING = UNAUTHORIZED
ORDER_INTENT_CREATION = UNAUTHORIZED
OMS_MUTATION = UNAUTHORIZED
STRATEGY_AUTHORITY_TRANSFER = NO
RISK_AUTHORITY_TRANSFER = NO
PORTFOLIO_AUTHORITY_TRANSFER = NO
```

No Pipeline terminal result is executable.

---

## Model / Human Authority Firewall

```text
MODEL_PARTICIPATION = UNAUTHORIZED
HUMAN_AUTHORITY_TRANSFER = NO
AUTOMATIC_HUMAN_APPROVAL = NO
```

No model authority. No synthetic human approval. Human Review does not mean
trade approval.

---

## Future File Allowlist

**CREATE:**

```text
apps/api/app/intelligence_pipeline/**
```

**TEST:**

```text
apps/api/tests/unit/test_intelligence_pipeline_*.py
apps/api/tests/contract/test_intelligence_pipeline_*.py
apps/api/tests/integration/test_intelligence_pipeline_*.py
```

**MODIFY EXISTING STAGE PACKAGES:** NONE

**OPTIONAL:** only repository-required package / index files directly necessary
to expose the new package, if current repository structure actually requires
them, and only with explicit justification in the implementing issue.

Do not authorize broad unrelated paths.

---

## Forbidden Paths

Future implementation under this Authorization MUST NOT change:

- approved Sprint 13 Planning body
- approved Intelligence Pipeline Architecture body
- approved Intelligence Pipeline Governance body
- approved Intelligence Pipeline Policy body
- existing stage package bodies
- Market Data orchestrator / provider acquisition
- database migrations / product persistence
- HTTP routers / product APIs
- frontend / UI
- Feature Platform / Feature Store
- dependency manifests / lockfiles
- CI workflows / deployment config
- VERSION / CHANGELOG

unless separately authorized by a future governance change.

---

## Acceptance Criteria

| ID | Criterion |
| --- | --- |
| AC-01 | Future runtime package is exactly `apps/api/app/intelligence_pipeline/` (and authorized tests). |
| AC-02 | Existing stage package bodies remain unmodified. |
| AC-03 | Composition uses only the listed public typed stage entrypoints by default. |
| AC-04 | Pipeline request / admission is typed and bounded; forbidden inputs rejected. |
| AC-05 | Exactly one UTC-aware run-level `as_of` is admitted and propagated. |
| AC-06 | No new temporal validation framework is introduced; reuse `require_utc_aware` where appropriate. |
| AC-07 | Watchlist stage is executed from canonical candidates via public contract. |
| AC-08 | Gap stage is executed (mandatory topology). |
| AC-09 | Catalyst stage is executed (mandatory topology). |
| AC-10 | Successful empty `GapCollection` is preserved and passed to Score as-is (not `None`). |
| AC-11 | Successful empty `CatalystCollection` is preserved and passed to Score as-is (not `None`). |
| AC-12 | Score receives Watchlist + actual GapCollection + actual CatalystCollection handoffs without Pipeline recomputation. |
| AC-13 | Morning Briefing receives ScoreCollection via public contract only. |
| AC-14 | Dashboard receives BriefingCollection via public contract only. |
| AC-15 | Required stage failures stop composition under fail-closed semantics. |
| AC-16 | Exactly six composition outcome families are represented and used. |
| AC-17 | Upstream stage reason / abstention semantics remain stage-owned and are not rewritten. |
| AC-18 | Governed stage Policy / config bindings are pinned at admission and stable through run / replay. |
| AC-19 | Thin composition provenance preserves as_of, stage refs, bindings, optional HR/ADE, and terminal outcome. |
| AC-20 | Thin in-process replay preserves original as_of, evidence, bindings, human input when applicable, stage public-output semantics, and terminal outcome. |
| AC-21 | Replay does not live-refetch, advance wall clock, substitute newer Policy/config, fabricate evidence/approval, or invoke model/broker. |
| AC-22 | Human Review is optional, explicit, attestation-gated; no synthetic / automatic approval. |
| AC-23 | Invalid / missing authorized HR public output prevents ADE invocation. |
| AC-24 | ADE is optional, explicitly requested, and HR-gated; accept/abstain remain ADE-owned. |
| AC-25 | `MODEL_PARTICIPATION = UNAUTHORIZED`; no model SDK / inference. |
| AC-26 | Broker / Order Intent / OMS / live trading remain unauthorized; terminals are non-executable. |
| AC-27 | No Sprint 13 product persistence, HTTP product API, or UI is introduced. |
| AC-28 | `FEATURE_PLATFORM_CHANGE_REQUIRED = NO`; no Feature Store / Platform mutation. |
| AC-29 | `NEW_DEPENDENCY_REQUIRED = NO`; no dependency / lockfile change. |
| AC-30 | Public exports are controlled via explicit `__all__` (or equivalent precedent). |
| AC-31 | Security / import firewall tests cover forbidden authorities and rewrite/bypass risks. |
| AC-32 | Required unit, contract, integration/boundary, and replay/determinism tests exist and pass for authorized scenarios. |

---

## Issue and Branch Authority

After this Implementation Authorization is **APPROVED / EFFECTIVE**:

- the three future implementation issues described above may be created
- branches may be created only after real issue numbers exist
- each issue SHALL reference this Authorization and
  `intelligence-pipeline.policy.v1`
- each issue SHALL state measurable acceptance criteria and explicit
  non-goals
- each issue SHALL remain within Authorized Scope and Forbidden Paths

This Implementation Authorization (while DRAFT) does not create those
implementation issues, runtime packages, or tests.

Speculative issue-number reservation is forbidden.

---

## Stop Conditions

If implementation cannot satisfy frozen semantics without requiring an
unauthorized surface, implementation MUST STOP and return to the appropriate
earlier gate rather than silently expanding scope.

Examples requiring stop:

- stage package modification required
- model participation required
- persistent / HTTP / UI productization required
- Feature Platform change required
- Strategy / Risk / Portfolio / Order Intent / OMS / Broker authority required
- new third-party dependency required
- MarketDataOrchestrator expansion required

---

## Status Effect

While DRAFT:

| Field | Value |
| --- | --- |
| Implementation Authorization | DRAFT / NOT YET APPROVED |
| Implementation | DENIED |
| Implementation work | NOT STARTED |
| MODEL PARTICIPATION | UNAUTHORIZED |
| Broker Execution | DENIED / DEFERRED |

If and only if this Authorization becomes APPROVED / EFFECTIVE:

1. Bounded implementation within this document is authorized.
2. The three future implementation issues may be created.
3. Model participation remains UNAUTHORIZED.
4. Broker / execution remains DENIED / DEFERRED.
5. Sprint 13 product persistence / HTTP / UI remain not authorized.
6. Sprint 13 remains not complete until authorized implementation issues are
   completed under repository process.

Approval alone does not create runtime code and does not create
`apps/api/app/intelligence_pipeline/`.
