# Premarket Command Center UI Implementation Authorization v1

**Authorization ID:** `premarket-command-center-ui.implementation-authorization.v1`  
**Title:** Read-Only Premarket Command Center UI Implementation Authorization v1  
**Version:** v1  
**Status:** APPROVED / EFFECTIVE
**Document class:** Implementation Authorization  
**Sprint:** 15  
**Theme:** Read-Only Premarket Command Center UI  
**Authority issue:** [#166](https://github.com/enesdedelerr-max/Bergama/issues/166)  
**IA PR:** [#167](https://github.com/enesdedelerr-max/Bergama/pull/167)
**IA merge:** `eb3bc12931ea4a2e261cef9e743275da708d5ec5`
**Policy:** `premarket-command-center-ui.policy.v1` (current lifecycle `APPROVED / FROZEN`)
**Governance:** `premarket-command-center-ui.governance.v1` (`APPROVED_EFFECTIVE`)  
**Architecture:** `premarket-command-center-ui.architecture.v1` (`APPROVED_EFFECTIVE`)  
**Planning:** `sprint-15.planning-gate` (`APPROVED_EFFECTIVE`)

```text
SPRINT_15_IMPLEMENTATION_AUTHORIZATION_STATE = APPROVED_EFFECTIVE
SPRINT_15_IMPLEMENTATION_AUTHORIZED = YES
IMPLEMENTATION_WORK_STARTED = YES
IMPLEMENTATION_SEQUENCE = 3/3 COMPLETE
SPRINT_15_IMPLEMENTATION_COMPLETE = YES
SPRINT_15_COMPLETE = NO
STATUS_SYNC = IN_PROGRESS / ISSUE_174
GOVERNANCE_CLOSEOUT = PENDING
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED/DEFERRED
NEW_FE_RUNTIME_DEPENDENCY_COUNT = 0
NEW_FE_DEV_DEPENDENCY_COUNT = 0
NEW_BE_DEPENDENCY_COUNT = 0
PRODUCTION_DEPLOYMENT_AUTHORIZED = NO
PRODUCT_WRITE_AUTHORIZED = NO
HR_WRITE_AUTHORIZED = NO
ADE_MUTATION_AUTHORIZED = NO
TRADE_EXECUTION_AUTHORIZED = NO
NEW_PROVIDER_AUTHORIZED = NO
FEATURE_PLATFORM_EXPANSION_AUTHORIZED = NO
```

This Implementation Authorization is **APPROVED / EFFECTIVE** (#166 / PR #167 @
`eb3bc12931ea4a2e261cef9e743275da708d5ec5`). The authorized WS1–WS3 sequence is
COMPLETE. Sprint 15 Governance Closeout remains separate and NOT COMPLETE.
Historical candidate-stage non-authorization text elsewhere in this document
describes the pre-effectiveness state and is preserved as history.

---

## 1. Authority Statement

This artifact freezes the exact implementation authority for the smallest
local/dev/test/CI delivery of the Sprint 15 Read-Only Premarket Command Center.

It becomes governed `APPROVED_EFFECTIVE` only after:

1. independent review of the frozen candidate
2. controlled commit
3. push and PR against `main`
4. exact-head CI success
5. required GitHub-native approval
6. conversation resolution
7. `MERGE_COMMIT`
8. Issue #166 closure through its PR (`Closes #166`)
9. post-merge exact-SHA CI success
10. finality review

Until then:

```text
SPRINT_15_IMPLEMENTATION_AUTHORIZED = NO
WS1_ISSUE_CREATION_AUTHORIZED = NO
UI_IMPLEMENTATION_MAY_BEGIN = NO
```

This Implementation Authorization is subordinate to Planning, Architecture,
Governance, and Policy. It does not reopen or reinterpret those gates.

---

## 1a. Current Implementation Finality (Status Sync)

Historical authorization narrative in this document remains historically
accurate: IA became effective only after its own governed merge/post-merge
lifecycle; WS coding required separate issue/preflight lifecycles.

**Current evidence (post-IA execution):**

| WS | Issue | PR | Implementation commit | Merge | State |
| --- | --- | --- | --- | --- | --- |
| WS1 | #168 | #169 | `d2900c399d87cbb63e54666b58d5253a2aca6bd2` | `d97b9b9e02542dd64cd68970aae7e8d6cec1881b` | MERGED_POST_MERGE_CI_GREEN_FINAL |
| WS2 | #170 | #171 | `ae6f7460808a35026375c0e5277db64f0d007991` | `ed52c5e10445fe69a2d728ccd15239788192113a` | MERGED_POST_MERGE_CI_GREEN_FINAL |
| WS3 | #172 | #173 | `9e53af68c6ceaa1d2abfb92f4a1be127caa9215b` | `32e498ad791cbfbac6eaecbcf360a16706c38fa2` | MERGED_POST_MERGE_CI_GREEN_FINAL |

WS3 post-merge CI: run `38073153105` on `32e498ad791cbfbac6eaecbcf360a16706c38fa2`
(`push` / `main`) completed / success; `quality-gate` success;
`frontend-quality-gate` success. Issue #172 CLOSED via PR linkage.

```text
SPRINT_15_IMPLEMENTATION_COMPLETE = YES
STATUS_SYNC = IN_PROGRESS / ISSUE_174
GOVERNANCE_CLOSEOUT = PENDING
SPRINT_15_COMPLETE = NO
NEXT_PROCESS_STEP = Sprint 15 Governance Closeout after Status Sync finality
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED/DEFERRED
PRODUCTION_DEPLOYMENT = NOT_AUTHORIZED
```

See [`README.md`](README.md).

---

## 2. Prerequisites / Predecessor Authority

| Layer | Path | Governed lifecycle |
| --- | --- | --- |
| Planning | `docs/sprints/sprint-15/planning-gate.md` | `APPROVED_EFFECTIVE` |
| Architecture | `docs/architecture/premarket-command-center-ui-architecture-v1.md` | `APPROVED_EFFECTIVE` |
| Governance | `docs/governance/premarket-command-center-ui/premarket-command-center-ui-governance-v1.md` | `APPROVED_EFFECTIVE` |
| Policy | `docs/policy/premarket-command-center-ui-policy-v1.md` | `APPROVED_EFFECTIVE` |

| Field | Value |
| --- | --- |
| Policy literal status | `DRAFT` (expected; governed lifecycle is `APPROVED_EFFECTIVE`) |
| Policy merge | `2f00c39e8acb381fd9533a07eb27526dd97529fa` |
| Policy post-merge CI | run `38019675304` — completed / success |
| Policy Issue | #164 CLOSED / COMPLETED via PR #165 |
| IA Issue | #166 OPEN — authority envelope |

Authority hierarchy:

```text
Policy → Governance → Architecture → Planning
```

Do not modify predecessor artifacts under this candidate.

---

## 3. Current Repository Reality

### Frontend (`apps/platform-console`)

- Next.js App Router console exists
- React / TanStack Query / Vitest / RTL / Playwright present
- Required npm scripts already exist (`lint`, `typecheck`, `test`, `build`, `test:e2e`)
- No `/premarket` route
- No Premarket navigation entry
- Console mock session exists and is **not** an API JWT
- No `AuthTokenProvider`
- No intelligence-run frontend client
- No `NEXT_PUBLIC_BERGAMA_API_BASE_URL`

### Backend (`apps/api`)

- FastAPI exists
- `POST /api/v1/auth/token` exists
- Bootstrap disabled behavior exists
- Server-selected bootstrap scopes exist
- Bootstrap TTL default 900 seconds
- `intelligence:runs:read` enforcement exists
- Six Sprint 14 intelligence GET routes exist
- Public DTOs exist
- CORS middleware absent

### CI

- Existing `quality-gate`
- `frontend-quality-gate` absent

```text
S15_IMPLEMENTATION_ALREADY_STARTED = NO
UNAUTHORIZED_PREIMPLEMENTATION_CHANGE_COUNT = 0
```

---

## 4. Objective

After this IA becomes `APPROVED_EFFECTIVE`, authorize the minimum
local/dev/test/CI implementation of a read-only Premarket Command Center in
`apps/platform-console` that:

- authenticates through an in-memory AuthTokenProvider and existing bootstrap
  `POST /api/v1/auth/token`
- consumes only the six Sprint 14 intelligence-run GET routes
- requires scope `intelligence:runs:read`
- introduces explicit CORS allowlist support for the console origin
- delivers `/premarket` and `/premarket/runs/[runId]`
- supports latest-dashboard, run-ID, and fingerprint lookup
- displays Dashboard, HR, and ADE public read-only information per frozen
  contracts
- adds `frontend-quality-gate`
- adds bounded Playwright coverage

without product writes, new dependencies, new intelligence routes, persistence
changes, model participation, broker execution, new providers, Feature Platform
expansion, or production deployment.

---

## 5. Frozen Discovery Resolutions

| Resolution | Value |
| --- | --- |
| Node | 20 |
| HTTP client | native `fetch` |
| API auth seam | `AuthTokenProvider` |
| API token storage | memory only |
| Mock console session | ≠ API JWT |
| CORS | explicit backend allowlist |
| Frontend CI job | `frontend-quality-gate` |
| Frontend framework | existing `apps/platform-console` only |
| Second frontend app | NO |
| New dependencies | NO |
| Production OIDC | DEFERRED |
| Production deployment | NOT AUTHORIZED |

---

## 6. Dependency Authorization

```text
NEW_FE_RUNTIME_DEPENDENCY_COUNT = 0
NEW_FE_DEV_DEPENDENCY_COUNT = 0
NEW_BE_DEPENDENCY_COUNT = 0
```

Existing capabilities are sufficient: Next.js, React, TanStack Query, Vitest,
React Testing Library, Playwright, FastAPI / Starlette `CORSMiddleware`,
Pydantic settings.

Any direct dependency addition requires separate authority reopening.

---

## 7. Workstream Authorization

```text
POST_IA_WORKSTREAM_COUNT = 3
WORKSTREAM_ORDER = WS1 → WS2 → WS3
WORKSTREAM_SERIALIZATION_REQUIRED = YES
```

| WS | Title | Purpose |
| --- | --- | --- |
| WS1 | Client + Auth | API base, AuthTokenProvider, bootstrap client, typed native-fetch client, CORS backend support, query/cache foundation, auth/client tests |
| WS2 | Read-Only Views | Premarket routes, lookups, Dashboard, HR, ADE visibility, freshness, semantic UX states, Premarket nav |
| WS3 | Hardening / Tests / CI | Security hardening, accessibility evidence, adversarial tests, Playwright, `frontend-quality-gate` |

No parallel implementation. No fourth workstream.

Future implementation issue creation may begin only after this IA is
`APPROVED_EFFECTIVE`.

---

## 8. Authorized Future Implementation Issues

After IA finality only:

1. Sprint 15 — WS1 Client + Auth
2. Sprint 15 — WS2 Read-Only Views
3. Sprint 15 — WS3 Hardening / Tests / CI

```text
FUTURE_IMPLEMENTATION_ISSUE_COUNT = 3
```

Issue numbers are **not** preassigned.

- WS1 issue must complete its own governance lifecycle before WS1 coding
- WS2 follows WS1 finality
- WS3 follows WS2 finality

---

## 9. WS1 — Client + Auth

### Frontend

- API base configuration
- AuthTokenProvider
- Bootstrap client
- Typed native-fetch intelligence client
- Error mapping
- AbortSignal
- Query/cache foundation
- Token expiry handling
- Cache clearing
- Auth/client unit tests

### Backend

- Bounded CORS settings/config/middleware
- CORS tests

Bootstrap route redesign is **NOT** authorized unless a concrete mechanical
defect is separately demonstrated within existing frozen authority.

---

## 10. API Base Contract

```text
API_BASE_URL_CONFIG_KEY = NEXT_PUBLIC_BERGAMA_API_BASE_URL
```

Rules:

- absolute http/https origin only
- `scheme://host[:port]`
- no path / query / fragment
- strip trailing slash
- missing/invalid → fail closed
- no mock fallback
- HTTPS required outside `localhost` / `127.0.0.1`
- no production host invented by this artifact

---

## 11. Auth Contract

States:

- `UNAUTHENTICATED`
- `BOOTSTRAP_LOADING`
- `AUTHENTICATED`
- `EXPIRED`
- `BOOTSTRAP_DISABLED`
- `BOOTSTRAP_FAILED`
- `INSUFFICIENT_SCOPE`

`AuthTokenProvider`: required.

Token: memory only.

Forbidden persistence: `localStorage`, `sessionStorage`, IndexedDB, cookies,
persistent product cache, BFF token store.

Bootstrap:

- `POST /api/v1/auth/token`
- Request: `{"grant_type":"bootstrap"}`
- TTL: 900 seconds default
- Disabled: `404` `auth.bootstrap_disabled`
- Scope selection: server-controlled
- Browser scope request: forbidden
- Required product scope: `intelligence:runs:read`
- `api:read` alone: insufficient

401: clear token; at most one automatic bootstrap reacquisition only when
bootstrap is authorized/enabled.

403: keep token; no retry; map to `INSUFFICIENT_SCOPE`.

Production OIDC: **DEFERRED**.

---

## 12. CORS Contract

```text
CORS_CONFIG_KEY = BERGAMA_CORS__ALLOWED_ORIGINS
```

- Input: comma-separated absolute origins
- Valid form: `scheme://host[:port]`
- Reject: path, query, fragment, wildcard
- Normalize: strip trailing slash
- Unset/empty: deny all cross-origin access
- Origin reflection: forbidden
- Methods: `GET`, `OPTIONS`, `POST` (POST only for existing auth bootstrap)
- Allowed headers: `Authorization`, `Content-Type`
- Credentials: `false`
- Exposed headers: none
- Max-Age: omitted

Expected future backend surfaces:

- `apps/api/app/core/cors_settings.py`
- `apps/api/app/core/config.py`
- `apps/api/app/factory.py`
- `apps/api/tests/**` for CORS-focused evidence

No new backend dependency.

---

## 13. Query / Cache Contract

```text
staleTime = 30000
gcTime = 300000
default retry = 0
503/network retry = 1
4xx retry = 0
500 retry = 0
abort retry = 0
refetchOnWindowFocus = false
refetchOnReconnect = false
polling = none
AbortSignal = required
```

Clear Premarket cache on logout/token replacement. Persistent product cache
forbidden.

Canonical query keys:

- `['intelligence-runs','latest-dashboard-capable']`
- `['intelligence-runs','id',runId]`
- `['intelligence-runs','fingerprint',fingerprint]`
- Plus bounded stage keys for `dashboard`, `human-review`, `ade` where required

No query-time intelligence recomputation.

---

## 14. WS2 — Read-Only Views

Required frontend routes:

- `/premarket`
- `/premarket/runs/[runId]`

Required capabilities:

- latest dashboard-capable
- manual run-ID lookup
- fingerprint lookup
- run detail
- Dashboard snapshot
- metadata
- stage presence
- freshness
- Human Review visibility when present
- ADE visibility when present
- Premarket navigation entry

Read-only only.

---

## 15. Six Authorized Intelligence GET Routes

Exactly:

1. `GET /api/v1/intelligence/runs/id/{run_id}`
2. `GET /api/v1/intelligence/runs/fingerprint/{fingerprint}`
3. `GET /api/v1/intelligence/runs/latest-dashboard-capable`
4. `GET /api/v1/intelligence/runs/id/{run_id}/dashboard`
5. `GET /api/v1/intelligence/runs/id/{run_id}/human-review`
6. `GET /api/v1/intelligence/runs/id/{run_id}/ade`

No seventh intelligence route. No intelligence POST/PUT/PATCH/DELETE.

---

## 16. UI Semantic States

Exact semantic IDs (18):

```text
auth_loading
unauthenticated
auth_expired
bootstrap_disabled
bootstrap_failed
insufficient_scope
latest_loading
latest_absent
run_not_found
dashboard_present
human_review_absent
ade_absent
unsupported_snapshot_contract
corrupt_persisted_snapshot
storage_unavailable
network_unavailable
refreshing
success
```

```text
UX_LITERAL_COPY_FROZEN = NO
```

Forbid semantic claims: live, safe-to-trade, buy, sell, hold, trade
recommendation, execution authority.

---

## 17. Public DTO / Privacy Boundary

Only public DTO families (5):

- `IntelligenceRunRead`
- `IntelligenceRunDashboardRead`
- `IntelligenceRunHumanReviewRead`
- `IntelligenceRunAdeRead`
- `ProductErrorResponse`

Frontend uses typed known-field projections.

- Missing required known field → fail closed
- Unknown field → never automatically render
- No generic recursive JSON renderer

Forbidden data: ORM internals, provider secrets, raw provider payloads, stack
traces, model-private data, unbounded news, Bearer token dumps, raw auth dumps,
ADE `recorded_attestation_payload`.

---

## 18. Human Review Safety

- HR: SHOULD provide read-only visibility
- `recorded_payload`: public but untrusted; max 8192; inert React text only
- Forbidden: `dangerouslySetInnerHTML`, HTML/Markdown/script execution, eval,
  sanitizer dependency, HR write workflow
- Require adversarial rendering tests in implementation lifecycle

---

## 19. ADE Visibility Boundary

- ADE: MUST be visibility-only
- Allowed: bounded public persisted output such as `outcome_kind`,
  `reason_family`, allowed public provenance
- Must exclude: `recorded_attestation_payload`
- Forbidden: ADE invoke, retry action, override, prompt, model CTA, trade CTA,
  execution CTA, decision mutation
- Static read-only display of already-persisted public ADE output is allowed
- `MODEL_PARTICIPATION` remains `UNAUTHORIZED`

---

## 20. Dashboard / Freshness

- Dashboard: read/display only
- No recomputation
- No frontend intelligence generation
- Freshness authority: `as_of`, `persisted_at`, `age_seconds`,
  `snapshot_contract_version`, `persistence_schema_version`
- Relative time may be cosmetic only
- Do not imply live market status or safe-to-trade status

---

## 21. Error Contract

| Condition | Behavior |
| --- | --- |
| 400 `invalid_identifier` | no retry |
| 401 `auth.*` | clear token; ≤1 authorized bootstrap reacquisition |
| 403 `authz.insufficient_scope` | keep token; no retry; `insufficient_scope` |
| 404 `run_not_found` | no retry |
| 404 `stage_not_present` | explicit absent-stage state |
| 404 `auth.bootstrap_disabled` | bootstrap unavailable |
| 409 `unsupported_snapshot_contract` | fail closed |
| 500 `corrupt_persisted_snapshot` | fail closed |
| 503 `storage_unavailable` | retry once |
| network/timeout | retry once |
| abort | no retry |

No mock fallback.

---

## 22. Security Header Boundary

Security headers SHOULD include:

- `X-Content-Type-Options: nosniff`
- Frame denial using either `Content-Security-Policy: frame-ancestors 'none'`
  **or** `X-Frame-Options: DENY`
- Advanced CSP: DEFERRED
- HSTS: DEFERRED

Do not expand into unrelated global security modernization.

---

## 23. Accessibility Boundary

Premarket accessibility baseline:

- semantic headings
- labels
- keyboard-accessible controls
- visible focus
- appropriate status/error announcements
- no color-only status meaning

No global design-system rewrite.

---

## 24. WS3 — Hardening / Tests / CI

Authorize after predecessor WS finality only:

- frontend unit/component tests
- auth/client tests
- error mapping tests
- retry/cache tests
- HR adversarial XSS-safe tests
- ADE private-payload exclusion tests
- read-only firewall tests
- route/navigation tests
- bounded accessibility tests
- bounded Premarket Playwright
- `frontend-quality-gate`

No unrelated frontend modernization.

---

## 25. Frontend CI Contract

```text
FRONTEND_CI_JOB_NAME = frontend-quality-gate
FRONTEND_CI_WORKFLOW = .github/workflows/ci.yml
FRONTEND_CI_NODE = 20
FRONTEND_CI_WORKING_DIRECTORY = apps/platform-console
```

Required commands:

1. `npm ci`
2. `npm run lint`
3. `npm run typecheck`
4. `npm test`
5. `npm run build`
6. `npm run test:e2e`

Trigger: console-affecting changes according to frozen Policy/IA authority.

Existing backend/general `quality-gate` must not be weakened.
Backend/CORS/config changes remain subject to existing `quality-gate`.
Playwright: bounded Chromium setup.
Deployment CI: **NOT AUTHORIZED**.

---

## 26. Backend Path Boundary

After IA finality, bounded backend authority:

- `apps/api/app/core/cors_settings.py`
- `apps/api/app/core/config.py`
- `apps/api/app/factory.py`
- `apps/api/tests/**` only for CORS-focused evidence
- plus only a proven mechanical bootstrap/config necessity within frozen
  authority

Explicitly forbidden:

- intelligence route / DTO / persistence semantic changes
- Alembic / schema / snapshot materialization / PipelineOutcome changes
- Dashboard / HR / ADE backend semantic changes
- Feature Platform changes
- new providers
- model integration
- broker integration

---

## 27. Frontend Path Boundary

After IA finality, bounded frontend authority includes:

- `apps/platform-console/src/app/(console)/premarket/**`
- `apps/platform-console/src/components/premarket/**`
- `apps/platform-console/src/lib/api/**` for bounded API base/intelligence/error work
- `apps/platform-console/src/lib/auth/**`
- `apps/platform-console/src/hooks/**` for bounded Premarket queries
- `apps/platform-console/src/contracts/types/**` for public DTO projections
- bounded provider/query-provider integration
- bounded session/auth integration preserving mock-session ≠ API-JWT
- `nav-items.ts` / shell only for Premarket navigation
- `apps/platform-console/next.config.ts` for frozen security headers
- `apps/platform-console/e2e/premarket*.spec.ts`
- Premarket-scoped unit/component tests
- optional console `.env.example` only if repository convention requires it

Forbidden: unrelated Overview redesign; global design-system rewrite; new
state/HTTP/auth/chart libraries; cookie/BFF auth; write UI; ADE invoke UI;
trade/execution UI.

---

## 28. CI Path Boundary

After IA finality, authorize:

- `.github/workflows/ci.yml` only for bounded `frontend-quality-gate` /
  path-trigger support

Forbidden: deployment/release/production workflows; weakening existing
`quality-gate`; unrelated CI modernization.

---

## 29. Validation Matrix

### IA docs candidate (this artifact)

- `make lint`
- `make typecheck`
- `make validate-secrets`
- `make test-api`

Frontend validation is **not** required for this docs-only candidate.

### Frontend implementation (future WS)

From `apps/platform-console`: `npm run lint`, `npm run typecheck`, `npm test`,
`npm run build`, bounded `npm run test:e2e`, with `npm ci` before frontend
checks in CI.

| WS | Validation |
| --- | --- |
| WS1 | Backend CORS tests; frontend auth/client/error/cache tests; relevant backend + frontend gates |
| WS2 | Frontend unit/component/build/e2e as applicable; `frontend-quality-gate` |
| WS3 | Full frontend matrix; bounded Playwright; `frontend-quality-gate` |

---

## 30. Test Authorization

Tests may verify only frozen behavior. Tests must not introduce product
behavior outside authority.

Require evidence for: CORS allowlist/default deny; API base fail-closed; auth
state transitions; 401/403; memory-only token; retry matrix; cache clearing;
AbortSignal; public DTO projection; unknown/private field exclusion; HR inert
rendering; ADE private payload exclusion; read-only route behavior; semantic UI
states; freshness display; accessibility baseline; frontend CI behavior.

---

## 31. Implementation Lifecycle

Each future WS issue must independently follow:

issue → preflight → authorized branch → implementation → validation →
candidate identity freeze → path-manifest SHA256 → review-diff SHA256 →
blob identity where useful → independent review → controlled commit →
push/PR preflight → push/PR → exact-head CI → GitHub-native approval →
conversation resolution → merge-readiness → `MERGE_COMMIT` → post-merge
exact-SHA CI → GitHub-native issue closure via `Closes #...` → finality.

No force push after reviewed identity freeze.

---

## 32. Production / Deployment Firewall

```text
PRODUCTION_DEPLOYMENT_AUTHORIZED = NO
PRODUCTION_HOSTING_AUTHORIZED = NO
PRODUCTION_URL_AUTHORIZED = NO
PRODUCTION_SECRET_AUTHORIZED = NO
PRODUCTION_OIDC_AUTHORIZED = NO
PRODUCTION_ROLLOUT_AUTHORIZED = NO
```

Production OIDC remains **DEFERRED**.

---

## 33. Write Firewall

```text
PRODUCT_WRITE_AUTHORIZED = NO
HR_WRITE_AUTHORIZED = NO
ADE_MUTATION_AUTHORIZED = NO
TRADE_EXECUTION_AUTHORIZED = NO
```

Only authorized browser/API mutation: existing `POST /api/v1/auth/token`.

No product / HR / ADE / trading mutation route.

---

## 34. Model / Broker / Provider Firewall

```text
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED/DEFERRED
NEW_PROVIDER_AUTHORIZED = NO
FEATURE_PLATFORM_EXPANSION_AUTHORIZED = NO
```

No model call. No broker call. No provider expansion. No Feature Platform
expansion.

---

## 35. Acceptance Criteria

```text
IA_AC_DEFINITION_COUNT = 34
IA_AC_UNIQUE_COUNT = 34
IA_AC_DUPLICATE_COUNT = 0
```

| ID | Criterion |
| --- | --- |
| S15-IA-01 | Planning/Architecture/Governance/Policy are final and IA remains subordinate to them. |
| S15-IA-02 | Exactly three workstreams/issues are authorized only after IA effectiveness, with serial order WS1 → WS2 → WS3. |
| S15-IA-03 | Zero new FE runtime, FE dev, and BE direct dependencies. |
| S15-IA-04 | `NEXT_PUBLIC_BERGAMA_API_BASE_URL` uses frozen absolute-origin validation and fail-closed behavior. |
| S15-IA-05 | AuthTokenProvider seam is required; production OIDC remains deferred. |
| S15-IA-06 | API token is memory-only and forbidden persistent stores remain forbidden. |
| S15-IA-07 | Existing bootstrap POST contract and disabled behavior are preserved. |
| S15-IA-08 | Exact product scope is `intelligence:runs:read`; `api:read` alone is insufficient. |
| S15-IA-09 | 401 clears token and allows at most one authorized bootstrap reacquisition. |
| S15-IA-10 | 403 preserves token, does not retry, and maps to `insufficient_scope`. |
| S15-IA-11 | CORS implementation exactly matches frozen allowlist contract. |
| S15-IA-12 | Native fetch uses credentials omit, AbortSignal, and no sensitive logging. |
| S15-IA-13 | Frozen query keys, staleTime, gcTime, refetch and polling semantics are preserved. |
| S15-IA-14 | Frozen retry matrix is preserved. |
| S15-IA-15 | Premarket cache clears on logout/token replacement. |
| S15-IA-16 | Routes `/premarket` and `/premarket/runs/[runId]` are delivered. |
| S15-IA-17 | Latest dashboard-capable and Dashboard remain read-only with no recomputation. |
| S15-IA-18 | Run-ID and fingerprint lookup use only frozen Sprint 14 GET routes. |
| S15-IA-19 | Human Review is read-only, XSS-safe inert text, with no sanitizer dependency and no write workflow. |
| S15-IA-20 | ADE is visibility-only and private attestation payload is excluded. |
| S15-IA-21 | Only public DTO projections may be consumed/rendered; private-data exclusion remains fail-closed. |
| S15-IA-22 | Frozen error matrix is complete, fail-closed, and has no mock fallback. |
| S15-IA-23 | Freshness remains server-authoritative. |
| S15-IA-24 | Exact semantic state IDs are preserved and trading/recommendation wording remains forbidden. |
| S15-IA-25 | nosniff and frame-denial security headers satisfy frozen SHOULD contract. |
| S15-IA-26 | Premarket accessibility baseline is implemented without global redesign. |
| S15-IA-27 | `frontend-quality-gate` runs the frozen npm command set. |
| S15-IA-28 | Bounded Premarket Playwright coverage is required. |
| S15-IA-29 | Backend changes remain inside CORS/config-only boundary. |
| S15-IA-30 | Frontend changes remain Premarket-scoped. |
| S15-IA-31 | CI changes remain `frontend-quality-gate` scoped. |
| S15-IA-32 | Product/HR/ADE writes remain forbidden; bootstrap POST remains the only authorized browser/API mutation. |
| S15-IA-33 | `MODEL_PARTICIPATION` remains `UNAUTHORIZED`. |
| S15-IA-34 | Broker execution, new providers, Feature Platform expansion, production deployment and implementation-before-IA-effectiveness remain forbidden. |

No WS1–WS3 implementation acceptance criteria are satisfied by drafting this
document.

---

## 36. Traceability

```text
IA_TRACEABILITY_GAP_COUNT = 0
IA_TRACEABILITY_AMBIGUITY_COUNT = 0
```

| Criterion ID | Primary Policy | Primary Governance | Architecture / Planning |
| --- | --- | --- | --- |
| `S15-IA-01` | PD-01; S15-POL-01 | S15-GOV-01 | Planning gate; AD non-auth |
| `S15-IA-02` | PD-32; S15-POL-30 | GD-24; S15-GOV-26 | Planning WS1–WS3 |
| `S15-IA-03` | PD-27; S15-POL-25 | GD-15; S15-GOV-15 | AD-18 |
| `S15-IA-04` | PD-09; S15-POL-09 | GD-07; S15-GOV-07 | AD-09; S15-ARCH-11 |
| `S15-IA-05` | PD-05; S15-POL-05 | GD-03/04; S15-GOV-04 | AD-07; S15-ARCH-09 |
| `S15-IA-06` | PD-03; S15-POL-03 | GD-02; S15-GOV-03 | AD-05; S15-ARCH-08 |
| `S15-IA-07` | PD-04; S15-POL-04 | GD-03; S15-GOV-04 | AD-06 |
| `S15-IA-08` | PD-06; S15-POL-06 | GD-05; S15-GOV-05 | AD-04; S15-ARCH-05 |
| `S15-IA-09` | PD-07; S15-POL-07 | GD-05; S15-GOV-05 | AD-06/11 |
| `S15-IA-10` | PD-07; S15-POL-07 | GD-05; S15-GOV-05 | AD-06/11 |
| `S15-IA-11` | PD-08; S15-POL-08 | GD-06; S15-GOV-06 | AD-08; S15-ARCH-10 |
| `S15-IA-12` | PD-20; S15-POL-20 | GD-16/19 | AD-03; S15-ARCH-06 |
| `S15-IA-13` | PD-18; S15-POL-18 | GD-14; S15-GOV-14 | AD-03 |
| `S15-IA-14` | PD-19; S15-POL-19 | GD-14; S15-GOV-14 | AD-11 |
| `S15-IA-15` | PD-18; S15-POL-18 | GD-14; S15-GOV-14 | AD-03/05 |
| `S15-IA-16` | PD-13/21; S15-POL-13 | GD-13; S15-GOV-13 | AD-02; S15-ARCH-03 |
| `S15-IA-17` | PD-12; S15-POL-12 | GD-11/12; S15-GOV-11/12 | AD-13; S15-ARCH-16 |
| `S15-IA-18` | PD-13; S15-POL-13 | GD-13 | AD-02; S15-ARCH-04 |
| `S15-IA-19` | PD-14; S15-POL-14 | GD-09; S15-GOV-09 | AD-14 |
| `S15-IA-20` | PD-15; S15-POL-15 | GD-10; S15-GOV-10 | AD-15 |
| `S15-IA-21` | PD-10/11; S15-POL-10/11 | GD-08; S15-GOV-08 | AD-10; S15-ARCH-12 |
| `S15-IA-22` | PD-16; S15-POL-16 | GD-12; S15-GOV-12 | AD-11; S15-ARCH-13 |
| `S15-IA-23` | PD-17; S15-POL-17 | GD-13; S15-GOV-13 | AD-12; S15-ARCH-15 |
| `S15-IA-24` | PD-22; S15-POL-21 | GD-11; S15-GOV-11 | Arch UX |
| `S15-IA-25` | PD-24; S15-POL-23 | GD-17; S15-GOV-17 | AD-16 |
| `S15-IA-26` | PD-23; S15-POL-22 | GD-20; S15-GOV-20 | AD-22 |
| `S15-IA-27` | PD-28; S15-POL-26 | GD-16; S15-GOV-16 | AD-20 |
| `S15-IA-28` | PD-29; S15-POL-26 | GD-16; S15-GOV-16 | AD-19/20 |
| `S15-IA-29` | PD-31; S15-POL-27 | GD-21/24; S15-GOV-21/24 | AD-24 |
| `S15-IA-30` | PD-21/32; S15-POL-13/30 | GD-24 | AD-01/02 |
| `S15-IA-31` | PD-28; S15-POL-26 | GD-16 | AD-20 |
| `S15-IA-32` | PD-32; S15-POL-29 | GD-21; S15-GOV-21 | AD-24 |
| `S15-IA-33` | PD-32; S15-POL-29 | GD-22; S15-GOV-22 | Planning firewall |
| `S15-IA-34` | PD-32; S15-POL-28/29/30 | GD-19/23/24; S15-GOV-19/23/24/26 | AD-21; Planning |

Do not invent higher-authority IDs.

---

## 37. Effectiveness Lifecycle

Artifact literal status remains **DRAFT**.

Artifact is **not** effective merely because the file, branch, validation,
review, commit, PR, or PR CI exists.

Governed lifecycle becomes `APPROVED_EFFECTIVE` only after:

1. `MERGE_COMMIT`
2. Issue #166 closes via its PR
3. post-merge exact-SHA CI succeeds
4. finality review passes

Only then:

```text
SPRINT_15_IMPLEMENTATION_AUTHORIZATION_STATE = APPROVED_EFFECTIVE
SPRINT_15_IMPLEMENTATION_AUTHORIZED = YES
WS1_ISSUE_CREATION_MAY_BEGIN = YES
```

WS1 coding is still **not** authorized until its own issue/preflight lifecycle
authorizes implementation.

---

## 38. Explicit Non-Authorization

At candidate stage, IA artifact presence does **NOT** authorize:

- WS1 / WS2 / WS3 issue creation
- WS1 / WS2 / WS3 implementation
- UI implementation
- AuthTokenProvider implementation
- CORS implementation
- `frontend-quality-gate` implementation
- dependency additions
- production deployment
- production OIDC
- new intelligence routes
- product writes
- HR writes
- ADE mutations
- persistence changes
- migrations
- new providers
- Feature Platform expansion
- model participation
- broker execution

---

## 39. Authority Restatement

```text
SPRINT_15_IMPLEMENTATION_AUTHORIZATION_STATE = APPROVED_EFFECTIVE
SPRINT_15_IMPLEMENTATION_AUTHORIZED = YES
IMPLEMENTATION_SEQUENCE = 3/3 COMPLETE
SPRINT_15_IMPLEMENTATION_COMPLETE = YES
SPRINT_15_COMPLETE = NO
STATUS_SYNC = IN_PROGRESS / ISSUE_174
GOVERNANCE_CLOSEOUT = PENDING
NEW_FE_RUNTIME_DEPENDENCY_COUNT = 0
NEW_FE_DEV_DEPENDENCY_COUNT = 0
NEW_BE_DEPENDENCY_COUNT = 0
PRODUCTION_DEPLOYMENT_AUTHORIZED = NO
PRODUCT_WRITE_AUTHORIZED = NO
HR_WRITE_AUTHORIZED = NO
ADE_MUTATION_AUTHORIZED = NO
TRADE_EXECUTION_AUTHORIZED = NO
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED/DEFERRED
NEW_PROVIDER_AUTHORIZED = NO
FEATURE_PLATFORM_EXPANSION_AUTHORIZED = NO
POST_IA_WORKSTREAM_COUNT = 3
WORKSTREAM_ORDER = WS1 → WS2 → WS3
```

Known carried LOW (do not fix here): Governance `S15-GOV-01` evidence cites
nonexistent `§47`.
