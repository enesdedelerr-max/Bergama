# Sprint 15 — Read-Only Premarket Command Center UI Planning Gate

**Planning Gate ID:** `sprint-15.planning-gate`  
**Proposed theme:** Read-Only Premarket Command Center UI  
**Status:** DRAFT  
**Sprint number:** 15  
**Gate type:** PLANNING GATE  
**Document class:** Planning Gate only  
**Prerequisite:** Sprint 14 authoritatively COMPLETE — Durable Intelligence Run Persistence and Read/Query Boundary  
**Authoritative main at draft time:** `a179569b378676da7b5e1042fe7e485d208bc5d6`  
**Planning issue:** [#158](https://github.com/enesdedelerr-max/Bergama/issues/158)

This Planning Gate candidate is **DRAFT**. DRAFT does **not** mean Planning is
EFFECTIVE. Planning becomes **APPROVED / EFFECTIVE** only after controlled merge
and post-merge verification of the Planning Gate PR.

Planning approval alone does **not** approve Architecture, Governance Decisions,
Policy / Contract Freeze, Implementation Authorization, or Implementation.

```text
PLANNING_GATE_APPROVAL ≠ IMPLEMENTATION_AUTHORIZATION
S15_THEME_FREEZE = PASS
SPRINT_15_IMPLEMENTATION_AUTHORIZED = NO
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED / DEFERRED
TAG_RELEASE_DEPLOY_AUTHORIZED = NO
```

---

## 1. Identity / Status

| Field | Value |
| --- | --- |
| Planning Gate ID | `sprint-15.planning-gate` |
| Status | DRAFT (candidate; not yet APPROVED / EFFECTIVE) |
| Sprint | 15 |
| Theme | Read-Only Premarket Command Center UI |
| Planning issue | #158 (OPEN at artifact creation) |
| Approves Architecture | No |
| Approves Governance | No |
| Approves Policy / Contract Freeze | No |
| Approves Implementation Authorization | No |
| Approves Implementation | No |
| UI implementation authorized | NO |
| Write / command API authorized | NO |
| Feature Platform change authorized | NO |
| Live-provider expansion authorized | NO |
| MODEL PARTICIPATION | UNAUTHORIZED |
| Broker Execution | DENIED / DEFERRED |
| Next eligible process step after APPROVED / EFFECTIVE | Sprint 15 Architecture Gate creation |

---

## 2. Authoritative Baseline

| Field | Value |
| --- | --- |
| Sprint 14 status | AUTHORITATIVELY COMPLETE |
| Sprint 14 final main | `a179569b378676da7b5e1042fe7e485d208bc5d6` |
| Sprint 14 Closeout | Issue [#156](https://github.com/enesdedelerr-max/Bergama/issues/156) CLOSED / PR [#157](https://github.com/enesdedelerr-max/Bergama/pull/157) MERGED |
| Sprint 14 post-merge CI | run `37865112376` completed / success |
| Sprint 15 discovery | COMPLETE |
| Sprint 15 Planning Issue | [#158](https://github.com/enesdedelerr-max/Bergama/issues/158) OPEN at artifact creation |

This artifact does **not** claim Issue #158 is closed.

---

## 3. Problem / Opportunity

Sprint 14 created a durable authenticated product read/query boundary for
completed intelligence pipeline runs: six GET route families under exact scope
`intelligence:runs:read`, with public DTOs, fail-closed latest-dashboard
selection, and authority firewalls that exclude writes, model participation,
and broker execution.

The repository already contains an existing frontend ecosystem under
`apps/platform-console` (Next.js / React / TanStack Query / Tailwind, with
Vitest / Testing Library / Playwright). That console is currently an ops/mock
surface and is **not** wired to the intelligence-run product API.

Sprint 15 should convert the existing product-read capability into a bounded
user-visible read-only product increment without expanding into writes, models,
broker execution, new providers, or Feature Platform expansion.

---

## 4. Frozen Theme and Goal

```text
S15_THEME_FREEZE = PASS
```

**Theme:** Sprint 15 — Read-Only Premarket Command Center UI

**Goal:** Ship a bounded read-only Premarket Command Center that authenticates
to the Sprint 14 intelligence-run product read API and displays latest
dashboard-capable runs, stage snapshots, outcomes, and freshness without
writes, models, or broker execution.

---

## 5. Product Data Boundary

Authoritative Sprint 14 GET route families:

1. `GET /api/v1/intelligence/runs/id/{run_id}`
2. `GET /api/v1/intelligence/runs/fingerprint/{fingerprint}`
3. `GET /api/v1/intelligence/runs/latest-dashboard-capable`
4. `GET /api/v1/intelligence/runs/id/{run_id}/dashboard`
5. `GET /api/v1/intelligence/runs/id/{run_id}/human-review`
6. `GET /api/v1/intelligence/runs/id/{run_id}/ade`

```text
PRODUCT_READ_SCOPE = intelligence:runs:read
S15_BACKEND_CONTRACT_CHANGE_REQUIRED = NO
S15_NEW_READ_ROUTE_REQUIRED = NO
S15_PUBLIC_WRITE_ROUTE_REQUIRED = NO
S15_QUERY_TIME_RECOMPUTATION_REQUIRED = NO
```

The UI consumes persisted Sprint 14 snapshots through the existing product
read boundary. No query-time pipeline recomputation is required or authorized.

---

## 6. Product Increment

### MUST

1. Latest dashboard-capable run
2. Run detail:
   - `run_id`
   - `pipeline_fingerprint` when present
   - `as_of`
   - `persisted_at`
   - `age_seconds`
   - `outcome`
   - failure state
   - `stage_presence`
   - authorized public bindings
   - authorized thin provenance
3. Dashboard public snapshot
4. ADE read-only visibility when present
5. Loading / error / absence / freshness states

### SHOULD

6. Human Review read-only visibility
7. Fingerprint lookup
8. Manual run-id lookup

### DEFER / UNAUTHORIZED

- Writes
- Submit / edit / approve / reject controls
- ADE invocation
- Model controls
- Broker / trade controls
- Provider mutation

```text
HUMAN_REVIEW_VISIBILITY_S15 = SHOULD
HUMAN_REVIEW_WRITE_UI_AUTHORIZED = NO
ADE_VISIBILITY_S15 = MUST
ADE_INVOCATION_AUTHORIZED = NO
```

---

## 7. Frontend Baseline

| Field | Value |
| --- | --- |
| Existing application path | `apps/platform-console` |
| Existing stack | Next.js 16, React 19, TanStack Query, TanStack Table, Tailwind 4 |
| Existing tests | Vitest, Testing Library, Playwright |
| Current product wiring | Ops/mock console; not wired to intelligence-run product API |

```text
FRONTEND_STACK_REUSE_EXPECTED = YES
NEW_FRONTEND_DEPENDENCY_AUTHORIZED = NO
```

Exact application placement is **not** frozen by Planning.

---

## 8. App Placement Architecture Boundary

Planning rule:

Reuse the existing repository frontend ecosystem unless Architecture finds a
material isolation/security reason for a separate app.

Exact Architecture-owned decision:

- extend `apps/platform-console`

vs

- create a separate app under `apps/`

```text
APP_PLACEMENT_ARCHITECTURE_DECISION_REQUIRED = YES
```

---

## 9. Auth Architecture Boundary

Current evidence:

- Bearer JWT auth exists
- Bootstrap token flow exists (`/auth/token`, `/auth/me`)
- Bootstrap scopes include `intelligence:runs:read`
- Current platform-console local/mock session is **not** equivalent to API
  product authorization

Non-negotiable Planning constraints:

- exact scope `intelligence:runs:read`
- UI may not fake authorization
- UI may not bypass API authorization
- frontend bundle may not contain secrets
- production identity / OIDC must not be invented during implementation

Architecture must freeze:

- token acquisition
- token storage
- token lifetime
- token attachment
- bootstrap / local use
- future production identity / OIDC boundary

---

## 10. CORS Architecture Boundary

CORS is not currently configured for the browser product boundary.

Architecture must freeze:

- allowed origins
- allowed methods
- allowed headers
- credentials behavior
- environment configuration
- default-deny behavior
- any bounded browser access needed for auth/bootstrap

An unjustified wildcard CORS policy is prohibited.

This Planning artifact does **not** implement CORS.

---

## 11. Data Exposure Policy Boundary

| Class | Meaning |
| --- | --- |
| AUTHORIZED_PUBLIC_FIELD | Fields exposed through Sprint 14 public product DTOs |
| CONDITIONAL_PUBLIC_FIELD | Nested stage snapshots only when authorized/present; `as_of` may be absent for `admission_rejected` where the contract permits |
| FORBIDDEN_PRIVATE_FIELD | Includes `recorded_attestation_payload`, ORM internals, raw provider payloads, model-private payloads, secrets, unbounded internal provenance |

Freeze:

The UI may render only fields already authorized by the Sprint 14 public
product DTO contract.

Human Review public recorded payload/text, where exposed by the public DTO,
must be treated as untrusted persisted text and rendered XSS-safe.

---

## 12. Freshness Semantics

Display metadata:

- `as_of`
- `persisted_at`
- `age_seconds`

`age_seconds` is derived, read-only, and non-authoritative.

The UI must not infer or claim safe-to-trade, execution-valid,
market-current, or fresh-enough from `age_seconds` unless a future explicit
Policy defines such a threshold.

Planning-level wording may describe it as **age since persist** or
**display freshness**.

---

## 13. Error / Outcome State Matrix

Required UI handling:

- loading
- success
- `400` invalid_identifier
- `401` unauthenticated
- `403` insufficient scope
- `404` run_not_found
- `404` stage_not_present
- `409` unsupported_snapshot_contract
- `500` corrupt_persisted_snapshot
- `503` storage_unavailable

Required representation of all six `PipelineOutcome` values:

- `admission_rejected`
- `required_stage_failed`
- `completed_dashboard`
- `completed_human_review`
- `completed_ade_accept`
- `completed_ade_abstain`

Required stage absence handling for Dashboard, Human Review, and ADE.

No backend contract change is required for this matrix.

---

## 14. Security Requirements

### MUST_FREEZE_BEFORE_IMPLEMENTATION

- browser token handling
- CORS
- dependency / package boundary
- lockfile / supply-chain expectations

### MUST_IMPLEMENT_IN_SPRINT

- scope enforcement
- no fake / bypassed auth
- XSS-safe persisted-text rendering
- ADE private payload non-exposure
- secret non-exposure
- safe API base URL configuration
- safe `ProductErrorResponse` presentation
- dependency / lockfile integrity
- baseline browser security headers appropriate to the chosen app architecture

### Security headers / CSP / clickjacking

Baseline required in Sprint 15 where applicable; advanced hardening may be
follow-up.

### CSRF

Not applicable to the currently planned read-only Bearer GET product surface.
Must be revisited if cookie auth or writes are later authorized.

---

## 15. Test Strategy

Reuse expectation:

- Vitest
- Testing Library
- Playwright

Future implementation test coverage must include:

- typed intelligence-run client
- auth / scope behavior
- error-state matrix
- six-outcome matrix
- Dashboard rendering
- ADE visibility
- Human Review visibility if included
- XSS-safe persisted text
- ADE private payload exclusion
- accessibility smoke
- browser / e2e happy path
- frontend lint
- frontend typecheck
- frontend tests
- frontend production build
- existing backend regression

Planning authorizes **no** new test dependency.

---

## 16. CI Quality Gate

Current state: the governed quality gate covers backend / API checks and does
not currently govern `apps/platform-console`.

Freeze requirement: Sprint 15 frontend changes may not bypass governed CI.

Future governed CI must include:

- frontend lint
- frontend typecheck
- frontend tests
- frontend production build
- plus existing backend regression requirements

Exact shape (same required quality-gate job vs separate required frontend job)
remains Architecture-owned.

This Planning artifact does **not** modify CI.

---

## 17. Dependency Boundary

```text
NEW_BACKEND_DEPENDENCY_EXPECTED = NO
NEW_FRONTEND_RUNTIME_DEPENDENCY_EXPECTED = NO
NEW_FRONTEND_DEV_DEPENDENCY_EXPECTED = NO
NEW_FRONTEND_DEPENDENCY_AUTHORIZED = NO
```

Existing stack should be preferred for the minimum vertical slice. Any later
proposed new dependency requires explicit downstream authorization.

---

## 18. Final IN_SCOPE

- Planning Gate artifact and frozen Sprint 15 boundaries
- Read-only Premarket Command Center vertical slice
- MUST product views
- SHOULD read-only Human Review / lookups subject to downstream bounded capacity
- Existing six GET product routes
- Exact scope `intelligence:runs:read`
- Browser→API auth foundation after Architecture freeze
- CORS foundation after Architecture freeze
- Existing frontend ecosystem reuse expectation
- Safe public DTO rendering
- Error / outcome / absence / freshness UX
- Security requirements
- Tests
- Frontend governed CI participation
- Documentation
- Strict downstream gate sequence

---

## 19. Final OUT_OF_SCOPE

- Public write API
- Human Review write workflow
- ADE invocation
- Model participation
- LLM / model integration
- Broker execution
- OMS
- Trade placement
- Trade cancel / modify
- Portfolio mutation
- Provider mutation
- New market / news / macro provider
- Feature Platform expansion
- Query-time recomputation
- Full intermediate stage snapshots
- Full Morning Briefing prose expansion
- Historical contract selector unless separately proven necessary
- Production OIDC implementation unless separately authorized
- Tag / release / deploy
- Sprint 15 product implementation before Implementation Authorization

---

## 20. Final DEFERRED

### A. Unauthorized capabilities

- Writes
- Models
- Broker
- Provider mutation
- Feature Platform expansion
- Query-time recomputation

### B. Nice-to-have / future

- Full briefing prose
- Intermediate stage payload expansion
- Production OIDC
- Advanced CSP / security hardening beyond Sprint 15 baseline
- Optional history / pagination capabilities

These categories must not be conflated.

---

## 21. Required Follow-On Gates

```text
Planning Gate
→ Architecture Gate
→ Governance Gate
→ Policy / Contract Gate
→ Implementation Authorization
→ implementation workstreams
```

| Gate | Owns |
| --- | --- |
| Architecture | App placement; browser auth/token design; CORS; API client boundary; frontend build/CI architecture; package/dependency boundary |
| Governance | Allowed UI behavior; read-only authority; Human Review visibility; ADE visibility; no-action semantics; capability firewalls |
| Policy / Contract | Renderable field contract; error presentation; freshness semantics; security presentation rules; browser authorization contract |
| Implementation Authorization | Exact implementation path allowlists; dependency authorization if any; final implementation issue/workstream authorization; test/CI mutation authority |

---

## 22. Proposed Post-IA Implementation Workstreams

Architecture is **not** an implementation workstream.

```text
PROPOSED_POST_IA_IMPLEMENTATION_WORKSTREAM_COUNT = 3
```

| WS | Title | Goal |
| --- | --- | --- |
| WS1 | Intelligence Run API Client + Auth Integration | Typed read client, bounded bootstrap/browser auth integration, exact product scope handling, and `ProductErrorResponse` mapping |
| WS2 | Premarket Command Center Read-Only Views | Latest-run, run detail, Dashboard, ADE visibility and, if frozen in scope, Human Review visibility / lookup views |
| WS3 | Hardening / Tests / CI | UX state matrix, security regressions, accessibility smoke, browser/e2e verification, frontend quality gates, and documentation |

These remain **PROPOSED**. They are **not** authorized for implementation by
this Planning artifact.

---

## 23. Authority Firewalls

```text
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED/DEFERRED
PUBLIC_WRITE_API_AUTHORIZED = NO
HUMAN_REVIEW_WRITE_UI_AUTHORIZED = NO
ADE_INVOCATION_AUTHORIZED = NO
NEW_PROVIDER_INTEGRATION_AUTHORIZED = NO
FEATURE_PLATFORM_EXPANSION_AUTHORIZED = NO
QUERY_TIME_RECOMPUTATION_AUTHORIZED = NO
TAG_RELEASE_DEPLOY_AUTHORIZED = NO
SPRINT_15_IMPLEMENTATION_AUTHORIZED = NO
```

---

## 24. Acceptance Criteria Matrix

```text
S15_PLANNING_AC_COUNT = 22
S15_PG_TOTAL_COUNT = 22
S15_PG_PASS_COUNT = 22
S15_PG_FAIL_COUNT = 0
S15_PG_DEFERRED_COUNT = 0
S15_PG_AMBIGUOUS_COUNT = 0
```

| ID | Criterion | Result |
| --- | --- | --- |
| S15-PG-01 | Sprint 15 product value and read-only Premarket Command Center theme are explicitly bounded. | PASS |
| S15-PG-02 | Sprint 14 six-route intelligence-run read API is identified as the authoritative product data boundary. | PASS |
| S15-PG-03 | No backend product-contract expansion is assumed unless Planning produces evidence that an existing MUST view cannot be supported. | PASS |
| S15-PG-04 | Application placement is identified as an Architecture Gate decision. | PASS |
| S15-PG-05 | Browser authentication/token handling is identified as an Architecture Gate decision. | PASS |
| S15-PG-06 | CORS/browser-to-API policy is identified as an Architecture Gate decision. | PASS |
| S15-PG-07 | Exact product scope `intelligence:runs:read` remains required and is not weakened. | PASS |
| S15-PG-08 | Latest dashboard-capable run and run-detail views are included in the minimum product increment. | PASS |
| S15-PG-09 | Dashboard public snapshot rendering is included as MUST. | PASS |
| S15-PG-10 | ADE visibility is read-only, bounded to authorized public fields, and `recorded_attestation_payload` remains forbidden. | PASS |
| S15-PG-11 | Human Review visibility is read-only if included; Human Review writes remain deferred and unauthorized. | PASS |
| S15-PG-12 | The UI error/state matrix covers the frozen product errors and six PipelineOutcome values. | PASS |
| S15-PG-13 | `age_seconds`/freshness is display-only and no unsupported SLA or freshness guarantee is invented. | PASS |
| S15-PG-14 | Persisted text rendering, including Human Review payload/text, must be XSS-safe. | PASS |
| S15-PG-15 | No new provider, Feature Platform expansion, or query-time recomputation is required or authorized for the UI. | PASS |
| S15-PG-16 | Frontend dependency/package boundary and supply-chain controls are identified for Architecture/Implementation Authorization. | PASS |
| S15-PG-17 | Frontend unit/component/contract/error/security/accessibility/e2e test expectations are defined. | PASS |
| S15-PG-18 | Frontend lint/typecheck/test/build integration into governed CI is defined. | PASS |
| S15-PG-19 | `MODEL_PARTICIPATION` remains UNAUTHORIZED. | PASS |
| S15-PG-20 | `BROKER_EXECUTION` remains DENIED/DEFERRED and no trade/OMS controls are included. | PASS |
| S15-PG-21 | Public writes, Human Review writes, ADE invocation, provider mutation, tag/release/deploy, and Sprint 15 implementation remain unauthorized. | PASS |
| S15-PG-22 | Planning produces an explicit handoff to Architecture → Governance → Policy / Contract → Implementation Authorization without authorizing Sprint 16 or any later capability. | PASS |

---

## 25. Handoff

After this Planning Gate is **APPROVED / EFFECTIVE**:

```text
SPRINT_15_ARCHITECTURE_GATE_CREATION = AUTHORIZED
SPRINT_15_ARCHITECTURE_GATE_STATE = NOT_STARTED
SPRINT_15_GOVERNANCE_GATE_STATE = NOT_STARTED
SPRINT_15_POLICY_CONTRACT_GATE_STATE = NOT_STARTED
SPRINT_15_IMPLEMENTATION_AUTHORIZATION_STATE = NOT_STARTED
SPRINT_15_IMPLEMENTATION_AUTHORIZED = NO
```

Planning does **not** authorize Governance or Policy implementation merely
because Planning is complete. Those remain future controlled gates.

Planning does **not** authorize Sprint 16 or any later capability.

---

## 26. Explicit Non-Authorization

This artifact does **not** authorize:

- frontend implementation
- backend implementation
- auth implementation
- CORS implementation
- CI modification
- dependency changes
- public API expansion
- writes
- model use
- broker use
- provider expansion
- Feature Platform expansion
- tag
- release
- deploy

```text
PLANNING_GATE_APPROVAL ≠ IMPLEMENTATION_AUTHORIZATION
SPRINT_15_IMPLEMENTATION_AUTHORIZED = NO
```

---

## 27. Lifecycle

| State | Meaning |
| --- | --- |
| DRAFT (this candidate) | Unmerged Planning artifact; not EFFECTIVE |
| APPROVED / EFFECTIVE | After controlled merge and post-merge verification |

Issue #158 lifecycle: the future Planning PR is expected to use
`Closes #158` per Planning Gate repository precedent. This candidate does
**not** create that PR and does **not** close the issue.

---

## 28. Discovery Findings Retained (Non-Blocking)

| Severity | Finding |
| --- | --- |
| HIGH | Architecture decision: browser token / CORS design |
| HIGH | Architecture decision: app placement extend vs new |
| MEDIUM | Security: XSS-safe Human Review persisted text |
| INFO | Existing platform console is ops/mock oriented |
| INFO | Sprint 14 README closeout pointer lag exists but does not invalidate GitHub-proven Sprint 14 finality |

Architecture-owned unresolved decisions are correctly deferred and are not
Planning candidate defects.
