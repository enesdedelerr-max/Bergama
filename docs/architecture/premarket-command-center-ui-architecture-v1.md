# Premarket Command Center UI Architecture v1

**Architecture ID:** `premarket-command-center-ui.architecture.v1`  
**Status:** APPROVED / EFFECTIVE
**Sprint:** 15  
**Gate:** Architecture Gate  
**Theme:** Read-Only Premarket Command Center UI  
**Document class:** Architecture-only — not Implementation Authorization  
**Architecture Issue:** [#160](https://github.com/enesdedelerr-max/Bergama/issues/160)  
**Architecture PR:** [#161](https://github.com/enesdedelerr-max/Bergama/pull/161)
**Architecture merge:** `d50bd2f6579898f80b7f5faedc6a5b6999ad7363`
**Planning Issue:** [#158](https://github.com/enesdedelerr-max/Bergama/issues/158)  
**Planning PR:** [#159](https://github.com/enesdedelerr-max/Bergama/pull/159)  
**Planning merge SHA:** `a0789bf05fa4f227d786e45e535edbd1c836d523`  
**Planning lifecycle:** `APPROVED_EFFECTIVE`  
**Planning artifact:** `docs/sprints/sprint-15/planning-gate.md` (`sprint-15.planning-gate`)  
**Architecture discovery verdict:** B — SPRINT 15 ARCHITECTURE DISCOVERY COMPLETE — ARCHITECTURE ISSUE READY WITH NON-BLOCKING DECISIONS

```text
THIS ARTIFACT DOES NOT AUTHORIZE PRODUCT IMPLEMENTATION BY ITSELF.
ARCHITECTURE_GATE_APPROVAL ≠ IMPLEMENTATION_AUTHORIZATION
IMPLEMENTATION_AUTHORIZATION = AUTHORIZED (by separate Implementation Authorization; not by this Architecture)
IMPLEMENTATION_WORK_STARTED = YES
IMPLEMENTATION_SEQUENCE = 3/3 COMPLETE
SPRINT_15_IMPLEMENTATION_COMPLETE = YES
SPRINT_15_COMPLETE = NO
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED/DEFERRED
TAG_RELEASE_DEPLOY_AUTHORIZED = NO
PUBLIC_WRITE_API_AUTHORIZED = NO
HUMAN_REVIEW_WRITE_UI_AUTHORIZED = NO
ADE_INVOCATION_AUTHORIZED = NO
NEW_FRONTEND_DEPENDENCY_AUTHORIZED = NO
```

---

## 1. Metadata / Lifecycle

| Field | Value |
| --- | --- |
| Artifact ID | `premarket-command-center-ui.architecture.v1` |
| Status | APPROVED / EFFECTIVE (lifecycle; AD-* decisions unchanged) |
| Sprint | 15 |
| Gate | Architecture |
| Architecture Issue | #160 (CLOSED; was OPEN at artifact creation) |
| Planning state | APPROVED_EFFECTIVE |
| Approves Governance | No |
| Approves Policy / Contract Freeze | No |
| Approves Implementation Authorization | No |
| Approves Implementation | No |
| Next eligible process after APPROVED / EFFECTIVE (historical) | Sprint 15 Governance Gate creation |
| Current next process | Status Sync Issue #174 → Governance Closeout |

DRAFT does **not** mean Architecture is EFFECTIVE. Architecture becomes
**APPROVED / EFFECTIVE** only after controlled merge and post-merge
verification of the Architecture Gate PR.

---

## 2. Purpose

This Architecture Gate freezes the bounded frontend/API-integration
architecture for the Sprint 15 read-only Premarket Command Center that
authenticates to the Sprint 14 intelligence-run product read API and
displays latest dashboard-capable runs, stage snapshots, outcomes, and
freshness without writes, models, or broker execution.

It does **not** authorize Governance Decisions, Policy / Contract Freeze,
Implementation Authorization, UI code, auth/CORS implementation, CI
workflow edits, dependency installation, model participation, broker
execution, tag, release, or deployment.

---

## 3. Authority and Authoritative Inputs

| Input | Reference |
| --- | --- |
| Planning Gate | `docs/sprints/sprint-15/planning-gate.md` (`sprint-15.planning-gate`) |
| Planning Issue / PR | #158 / #159 @ `a0789bf05fa4f227d786e45e535edbd1c836d523` |
| Architecture Issue | #160 |
| Sprint 14 productization Architecture | `docs/architecture/intelligence-run-productization-architecture-v1.md` |
| Sprint 14 Governance / Policy | intelligence-run-productization governance and policy v1 |
| Frontend application | `apps/platform-console` |
| Product read API | `apps/api/app/routers/intelligence_runs.py` |
| Product DTOs / errors | `apps/api/app/schemas/intelligence_runs.py`, `product_errors.py` |
| Auth | Bearer JWT + bootstrap (`apps/api/app/deps/auth.py`, `/auth/token`, `/auth/me`) |
| Scope | `intelligence:runs:read` |
| CI / tests | `.github/workflows/ci.yml`, Vitest / Testing Library / Playwright in platform-console |

No authority outside these inputs is invented.

---

## 4. Non-Authorization Statement

```text
THIS ARTIFACT DOES NOT AUTHORIZE PRODUCT IMPLEMENTATION.
IT DOES NOT AUTHORIZE UI CODE.
IT DOES NOT AUTHORIZE AUTH/CORS IMPLEMENTATION.
IT DOES NOT AUTHORIZE CI WORKFLOW CHANGES.
IT DOES NOT AUTHORIZE DEPENDENCY INSTALLATION.
IT DOES NOT AUTHORIZE MODEL PARTICIPATION.
IT DOES NOT AUTHORIZE BROKER EXECUTION.
```

Architecture decisions freeze design only. Implementation requires later
Governance → Policy / Contract → Implementation Authorization.

---

## 5. Architectural Principles

```text
A. Read-only product surface over Sprint 14 persisted snapshots.
B. Reuse existing frontend ecosystem unless isolation evidence requires otherwise.
C. Smallest coherent authority expansion.
D. Preserve Sprint 14 six-route GET contract and public DTOs.
E. Public DTOs only; private ADE payload never reaches/renders.
F. Fail-closed auth and API base configuration.
G. Exact scope intelligence:runs:read; no weakening.
H. No query-time pipeline recomputation.
I. No model participation; no broker execution.
J. No provider or Feature Platform expansion.
K. No new dependencies unless later separately authorized.
L. Future production auth replaceable via token-provider seam.
M. Testable with existing tools; frontend must enter governed CI.
```

---

## 6. Current Repository Constraints

Verified at Architecture drafting against Planning baseline main
`a0789bf05fa4f227d786e45e535edbd1c836d523`:

| Constraint | Evidence |
| --- | --- |
| `apps/platform-console` exists | Next.js App Router ops/mock console |
| Next.js | 16.2.10 (lockfile) |
| React | 19.2.7 (lockfile) |
| TanStack Query | 5.101.2 |
| TanStack Table | 8.21.3 |
| Tailwind | 4.3.2 |
| Vitest | 4.1.10 |
| Testing Library | 16.3.2 |
| Playwright | 1.61.1 |
| Console orientation | ops/mock; not wired to intelligence-run API |
| Console session | `createBootstrapSession()` — not API JWT |
| API base env | no `NEXT_PUBLIC_*` product API config today |
| CORS | no `CORSMiddleware`; only `RequestContextMiddleware` |
| Frontend CI | absent from governed `quality-gate` |
| Product routes | six GET families under `/api/v1/intelligence/runs/...` |
| Product scope | `intelligence:runs:read` |
| Public write route | none for intelligence runs |

---

## 7. Frontend Placement

See **AD-01**.

```text
NEW_FRONTEND_APP_REQUIRED = NO
RECOMMENDED_FRONTEND_PLACEMENT = extend apps/platform-console
```

---

## 8. Route / Navigation Architecture

See **AD-02**.

```text
PREMARKET_ROUTE_ROOT = /premarket
RUN_DETAIL_ROUTE_PATTERN = /premarket/runs/[runId]
LOOKUP_ROUTE_STRATEGY = on /premarket (fingerprint + manual run-id)
NAVIGATION_INTEGRATION_STRATEGY = add Premarket to CONSOLE_NAV
```

---

## 9. Sprint 14 Read API Mapping

Authoritative GET families (no expansion):

1. `GET /api/v1/intelligence/runs/id/{run_id}`
2. `GET /api/v1/intelligence/runs/fingerprint/{fingerprint}`
3. `GET /api/v1/intelligence/runs/latest-dashboard-capable`
4. `GET /api/v1/intelligence/runs/id/{run_id}/dashboard`
5. `GET /api/v1/intelligence/runs/id/{run_id}/human-review`
6. `GET /api/v1/intelligence/runs/id/{run_id}/ade`

```text
PRODUCT_READ_SCOPE = intelligence:runs:read
READ_API_ROUTE_COUNT = 6
NEW_INTELLIGENCE_READ_ROUTE_REQUIRED = NO
NEW_PUBLIC_WRITE_ROUTE_REQUIRED = NO
BACKEND_INTELLIGENCE_CONTRACT_CHANGE_REQUIRED = NO
```

---

## 10. Typed API Client Boundary

See **AD-03**.

| Boundary | Path |
| --- | --- |
| Client | `apps/platform-console/src/lib/api/intelligence-runs.ts` |
| Contracts | `apps/platform-console/src/contracts/types/intelligence-runs.ts` |
| Hooks | `apps/platform-console/src/hooks/` |

Native `fetch` + existing TanStack Query; AbortSignal; stable query keys
by operation + identity; `ProductErrorResponse` parsing; no presentation
layer fetches.

```text
TYPED_CLIENT_REQUIRED = YES
NEW_CLIENT_DEPENDENCY_REQUIRED = NO
```

---

## 11. Browser Authentication Boundary

See **AD-04**.

Existing mock/local console session must **not** be treated as backend
API authentication. Premarket product calls require backend Bearer JWT
with exact scope `intelligence:runs:read`. Shell session concerns remain
separate from API authorization. No fake product authorization.

---

## 12. Token Lifecycle

See **AD-05**, **AD-06**.

```text
SPRINT_15_TOKEN_STORAGE_STRATEGY = IN_MEMORY_MODULE_OR_CONTEXT_STORE
TOKEN_PERSISTENCE_SCOPE = tab/session memory only
```

Rejected: `localStorage`, persistent browser storage, cookie/BFF
expansion.

Acquisition (local/dev/test when bootstrap enabled):

```text
POST /api/v1/auth/token
grant_type = bootstrap
```

Attachment: `Authorization: Bearer <access_token>`.  
Respect backend TTL (default 900s). On absent/expired: clear memory;
re-acquire only via authorized bootstrap when enabled; otherwise explicit
unauthenticated UI.  
401 → authentication state.  
403 / `authz.insufficient_scope` → insufficient-scope state; no silent
bypass.

No credentials/secrets in browser bundle.

---

## 13. Future OIDC Seam

See **AD-07**.

Replaceable `AuthTokenProvider` (or repository-consistent equivalent).
Typed client depends on provider behavior, not bootstrap endpoint details.

```text
PRODUCTION_OIDC_IMPLEMENTED_IN_S15 = NO
OIDC_PROVIDER_SELECTED = NO
OIDC_IMPLEMENTATION_DEFERRED = YES
FUTURE_OIDC_SEAM_REQUIRED = YES
```

---

## 14. CORS Architecture

See **AD-08**.

```text
CURRENT_CORS_PRESENT = NO
SPRINT_15_CORS_REQUIRED = YES
CORS_ALLOWED_ORIGIN_STRATEGY = environment-driven explicit allowlist
CORS_WILDCARD_ORIGIN = FORBIDDEN
CORS_ALLOWED_METHODS = GET, OPTIONS, POST
CORS_ALLOWED_HEADERS = Authorization, Content-Type
CORS_ALLOW_CREDENTIALS = false
CORS_DEFAULT_DENY = YES
```

POST is included solely for bootstrap `/auth/token` in authorized
bootstrap environments.  
**No CORS implementation in this Architecture candidate.**

---

## 15. API Base URL / Environment Configuration

See **AD-09**.

```text
API_BASE_URL_CONFIG_KEY = NEXT_PUBLIC_BERGAMA_API_BASE_URL
API_BASE_URL_PUBLIC = YES
MISSING_API_BASE_URL_BEHAVIOR = FAIL CLOSED on Premarket product pages
```

No hard-coded production host. No secrets. Deterministic test config.
No mock product-data fallback when config is missing.

---

## 16. Public / Private DTO Boundary

See **AD-10**.

Public consumption: `IntelligenceRunRead`,
`IntelligenceRunDashboardRead`, `IntelligenceRunHumanReviewRead`,
`IntelligenceRunAdeRead`, `ProductErrorResponse`.

Forbidden: `AdeProvenance.recorded_attestation_payload`, ORM internals,
raw provider payloads, model-private payloads, secrets, unbounded
internals.

Human Review `attestation.recorded_payload` is public persisted text and
**untrusted**.

---

## 17. Error Semantics

See **AD-11**.

| HTTP | Product code / meaning |
| --- | --- |
| 400 | `intelligence.runs.invalid_identifier` |
| 401 | authentication failure |
| 403 | `authz.insufficient_scope` |
| 404 | `intelligence.runs.run_not_found` |
| 404 | `intelligence.runs.stage_not_present` |
| 409 | `intelligence.runs.unsupported_snapshot_contract` |
| 500 | `intelligence.runs.corrupt_persisted_snapshot` |
| 503 | `intelligence.runs.storage_unavailable` |

Distinguish run absence, stage absence, auth failure, authorization
failure, unsupported contract, corrupt state, temporary unavailability.
Do not invent product errors.

---

## 18. PipelineOutcome Display Semantics

Frozen by **S15-ARCH-14** (outcome display semantics).

Exact values:

- `admission_rejected`
- `required_stage_failed`
- `completed_dashboard`
- `completed_human_review`
- `completed_ade_accept`
- `completed_ade_abstain`

These are execution/product outcomes only. They are **not** buy, sell,
hold, safe, unsafe, recommended, or not recommended.

---

## 19. Freshness Semantics

See **AD-12**.

Display metadata: `as_of`, `persisted_at`, `age_seconds`,
`snapshot_contract_version`, `persistence_schema_version` where useful.

```text
FRESHNESS_RECOMPUTATION_ALLOWED = NO
TRADING_SAFE_FRESHNESS_LABEL_ALLOWED = NO
```

Client elapsed display, if any, is presentation-only and
non-authoritative; must not replace server `age_seconds`.

---

## 20. Dashboard Presentation

See **AD-13**.

Read-only from persisted public Dashboard snapshot. Useful fields include
instrument, score, components, watchlist rank/rule, gap identity,
catalyst source IDs, policy pins.

```text
DASHBOARD_BACKEND_CONTRACT_GAP = NO
MORNING_BRIEFING_PROSE_REQUIRED = NO
```

No invented prose. No backend contract expansion.

---

## 21. Human Review Visibility

See **AD-14**.

```text
HR_READ_VISIBILITY = SHOULD
HR_WRITE_UI_AUTHORIZED = NO
HR_XSS_SAFE_RENDERING_REQUIRED = YES
```

Plain/escaped text only. Forbidden: `dangerouslySetInnerHTML`, submit,
approve, write controls.

---

## 22. ADE Visibility

See **AD-15**.

```text
ADE_READ_VISIBILITY = MUST
ADE_INVOKE_UI_AUTHORIZED = NO
ADE_PRIVATE_PAYLOAD_RENDER_ALLOWED = NO
```

No invoke, retry model, override, model execution control, or private
provenance rendering.

---

## 23. Security Baseline

See **AD-16**.

**MUST:** XSS-safe persisted text; no token logging; no secrets in
bundle; scope-preserving auth; CORS allowlist; private ADE exclusion;
lockfile integrity; sanitized `ProductErrorResponse` presentation.

**SHOULD:** baseline frame protection and nosniff where architecture
supports.

**DEFER:** advanced CSP nonce/hash design.

---

## 24. CSRF Determination

See **AD-17**.

```text
SPRINT_15_CSRF_STATUS = NOT_APPLICABLE
```

Reason: Bearer token via `Authorization` header; `credentials=false`;
no cookie authentication. If credentialed cookies are introduced later,
CSRF must be reevaluated.

---

## 25. Dependency Boundary

See **AD-18**.

```text
NEW_FRONTEND_RUNTIME_DEPENDENCIES = NONE
NEW_FRONTEND_DEV_DEPENDENCIES = NONE
NEW_BACKEND_DEPENDENCIES = NONE
NEW_FRONTEND_DEPENDENCY_AUTHORIZED = NO
```

Existing stack is sufficient. No dependency installation authorized.

---

## 26. Test Architecture

See **AD-19**.

Reuse Vitest, React Testing Library, Playwright.

Future implementation coverage must include: typed client; token
lifecycle; Authorization attachment; 401/403; `ProductErrorResponse`;
six outcomes; latest run; run detail; Dashboard; ADE; HR if included;
XSS-safe HR text; private ADE absence; freshness; loading; stage/run
absence; API errors; a11y smoke; bounded E2E.

Unit/component tests mock/stub the typed client/network boundary with
existing tooling. No new mocking framework.

---

## 27. Frontend CI Architecture

See **AD-20** and **§35 Playwright decision**.

```text
CURRENT_FRONTEND_CI_COVERAGE = NONE
SPRINT_15_FRONTEND_CI_REQUIRED = YES
```

**Required job:** `frontend-quality-gate` for relevant Sprint 15 frontend
changes:

1. `npm ci`
2. lint
3. typecheck
4. Vitest
5. Next production build

**Playwright:** separate bounded smoke job for Premarket-touching
implementation PRs — not part of docs-only Architecture validation.
Governance/Policy/IA may later freeze branch-rule mechanics without
weakening E2E evidence requirements for implementation.

**No workflow modification in this Architecture gate.**

---

## 28. Deployment / Runtime Assumptions

See **AD-21**.

Supported assumptions: local, development, test, browser→API topology.

```text
PRODUCTION_DEPLOYMENT_CHANGE_REQUIRED_IN_S15 = NO
```

Formal production UI hosting: **DEFERRED**. Do not invent
Kubernetes/cloud topology.

---

## 29. Accessibility

See **AD-22**.

Bounded baseline: semantic headings; semantic tables; keyboard
accessibility; visible focus; loading/error announcements where
appropriate; status not encoded only by color. No design-system rewrite.

```text
A11Y_BASELINE_REQUIRED = YES
```

---

## 30. Observability / Logging

See **AD-23**.

```text
NEW_TELEMETRY_PROVIDER_AUTHORIZED = NO
```

No Bearer token logging. No raw sensitive payload logging. Bounded
developer diagnostics only. Correlation identifiers only if already
public/available.

---

## 31. Backend Change Boundary

See **AD-24**.

```text
BACKEND_CORS_CHANGE_REQUIRED = YES
BACKEND_AUTH_CHANGE_REQUIRED = NO
BACKEND_INTELLIGENCE_CONTRACT_CHANGE_REQUIRED = NO
NEW_INTELLIGENCE_READ_ROUTE_REQUIRED = NO
NEW_PUBLIC_WRITE_ROUTE_REQUIRED = NO
```

CORS/config implementation only after later Implementation Authorization.

---

## 32. Architecture Decision Matrix (AD-01..AD-24)

| ID | Decision | Rationale | Rejected alternatives | Authority impact |
| --- | --- | --- | --- | --- |
| AD-01 | Extend `apps/platform-console` with Premarket / Intelligence read-only section. `NEW_FRONTEND_APP_REQUIRED=NO`. | Reuses shell, stack, tests; lower auth/client/CI duplication; no material S15 isolation benefit for separate app. | New app under `apps/`. | Architecture only; no implementation. |
| AD-02 | Routes `/premarket` and `/premarket/runs/[runId]`; fingerprint + run-id lookup on `/premarket`; integrate into `CONSOLE_NAV`. | Smallest navigation; lookups do not need dedicated routes. | Extra lookup routes; separate app routes. | Architecture only. |
| AD-03 | Centralized typed client + contracts + TanStack hooks at frozen paths; native fetch; no scattered component fetches. | Single boundary for DTO/errors/auth attachment; existing Query stack. | Per-component fetch; new HTTP client library. | Architecture only; no new deps. |
| AD-04 | Separate API Bearer JWT auth from mock console session. | Mock session ≠ product authorization; prevents fake auth. | Treating console session as API auth. | Architecture only. |
| AD-05 | In-memory module/context Bearer store; tab/session memory only. | Reduces token persistence under XSS; avoids cookie/CSRF expansion; fits bootstrap TTL. | `localStorage`; cookie/BFF. | Architecture only. |
| AD-06 | Bootstrap `POST /api/v1/auth/token` with `grant_type=bootstrap` when enabled; Bearer attachment; clear/re-acquire on expiry; explicit 401/403 UX. | Uses existing backend; no browser secrets. | Embedding secrets; silent scope bypass. | Architecture only; no auth code now. |
| AD-07 | `AuthTokenProvider` seam; OIDC deferred; no provider selected. | Enables future production identity without rewriting client/views. | Implementing production OIDC in S15. | Architecture only. |
| AD-08 | Env allowlist CORS; GET/OPTIONS/POST; Authorization+Content-Type; credentials false; default deny; no wildcard. | Browser product boundary currently missing; secure minimum for bootstrap + GETs. | Wildcard origin; credentials true. | Architecture freeze; impl after IA. |
| AD-09 | `NEXT_PUBLIC_BERGAMA_API_BASE_URL`; public; fail closed; no mock product fallback. | Explicit, non-secret origin; safe failure. | Hard-coded hosts; silent mock as product. | Architecture only. |
| AD-10 | Public Sprint 14 DTOs only; forbid ADE `recorded_attestation_payload` and other private/secret material; HR text untrusted. | Preserves S14 contract and privacy firewalls. | Rendering private ADE payload as HTML. | Architecture only. |
| AD-11 | Freeze full product error matrix 400/401/403/404×2/409/500/503. | Matches `product_errors.py`; diagnosable UX. | Invented error codes. | Architecture only. |
| AD-12 | Freshness from public metadata only; no recomputation; no trading-safe SLA. | Point-in-time honesty; no false market authority. | Client “safe to trade” labels. | Architecture only. |
| AD-13 | Dashboard from public persisted records; no briefing prose; no contract gap. | S14 Dashboard fields sufficient for MUST view. | Backend expansion; invented prose. | Architecture only. |
| AD-14 | HR SHOULD read-only; XSS-safe plain text; no write UI. | Planning SHOULD + security. | HR write/approve UI; `dangerouslySetInnerHTML`. | Architecture only. |
| AD-15 | ADE MUST read-only; no invoke; no private payload. | Planning MUST + S14 private exclusion. | ADE invoke/model controls. | Architecture only. |
| AD-16 | MUST security list; SHOULD frame/nosniff; DEFER advanced CSP. | Bounded S15 security without over-scoping CSP. | Skipping XSS/CORS controls. | Architecture only. |
| AD-17 | CSRF `NOT_APPLICABLE` for Bearer + credentials false; reevaluate if cookies appear. | No cookie CSRF surface. | Cookie/BFF without CSRF. | Architecture only. |
| AD-18 | No new FE/BE dependencies. | Existing stack sufficient. | New HTTP/UI/test frameworks. | No install authorized. |
| AD-19 | Vitest / RTL / Playwright coverage expectations as listed. | Existing tooling; no new frameworks. | New mock frameworks. | Architecture only. |
| AD-20 | Required `frontend-quality-gate` + separate Playwright smoke for Premarket PRs; no workflow edit now. | Deterministic static/unit quality vs browser E2E; docs-only must not require browsers. | Frontend remaining ungated; Playwright on every docs PR. | Architecture freeze; CI edit after IA. |
| AD-21 | Local/dev/test topology only; prod hosting deferred; no prod deploy change required in S15. | Repo lacks formal prod UI hosting authority. | Inventing K8s UI deploy. | Architecture only. |
| AD-22 | Bounded a11y baseline; no design-system rewrite. | Operational clarity without DS rewrite. | Full a11y redesign. | Architecture only. |
| AD-23 | No new telemetry; no token/sensitive logging. | Fail-closed privacy. | New APM/telemetry vendors. | Architecture only. |
| AD-24 | Backend: CORS/config YES; auth NO; intel contract NO; new read NO; write NO. | Matches Planning and repository evidence. | Expanding intel routes/contracts. | Architecture freeze; CORS impl after IA. |

```text
ARCH_AD_COUNT = 24
ARCH_AD_UNIQUE_COUNT = 24
ARCH_AD_DUPLICATE_COUNT = 0
ARCH_AD_MISSING_COUNT = 0
```

---

## 33. Acceptance Criteria Matrix (S15-ARCH-01..26)

```text
ARCH_AC_PASS_COUNT = 26
ARCH_AC_FAIL_COUNT = 0
ARCH_AC_AMBIGUOUS_COUNT = 0
```

| ID | Criterion | Result | Evidence |
| --- | --- | --- | --- |
| S15-ARCH-01 | Planning authority inheritance explicit; no implementation expansion. | PASS | §§1–4; firewalls; Planning #158/#159 SHA |
| S15-ARCH-02 | Frontend placement frozen. | PASS | AD-01; §7 |
| S15-ARCH-03 | Route/navigation architecture frozen. | PASS | AD-02; §8 |
| S15-ARCH-04 | Six Sprint 14 GET routes mapped/preserved. | PASS | §9 |
| S15-ARCH-05 | `intelligence:runs:read` preserved. | PASS | §9; AD-04/05/06 |
| S15-ARCH-06 | Typed client/TanStack boundary frozen. | PASS | AD-03; §10 |
| S15-ARCH-07 | Mock session separated from API auth. | PASS | AD-04; §11 |
| S15-ARCH-08 | Token acquisition/storage/lifetime/attachment/clear frozen. | PASS | AD-05/06; §12 |
| S15-ARCH-09 | Future OIDC seam defined; production OIDC deferred. | PASS | AD-07; §13 |
| S15-ARCH-10 | CORS frozen. | PASS | AD-08; §14 |
| S15-ARCH-11 | API base config/fail-closed frozen. | PASS | AD-09; §15 |
| S15-ARCH-12 | Public DTO/private exclusion frozen. | PASS | AD-10; §16 |
| S15-ARCH-13 | Complete product error mapping frozen. | PASS | AD-11; §17 |
| S15-ARCH-14 | Six outcomes frozen without trading reinterpretation. | PASS | §18 |
| S15-ARCH-15 | Freshness semantics frozen. | PASS | AD-12; §19 |
| S15-ARCH-16 | Dashboard frozen to public persisted fields. | PASS | AD-13; §20 |
| S15-ARCH-17 | HR read-only/XSS-safe boundary frozen. | PASS | AD-14; §21 |
| S15-ARCH-18 | ADE read-only/private exclusion frozen. | PASS | AD-15; §22 |
| S15-ARCH-19 | Security baseline + CSRF determination frozen. | PASS | AD-16/17; §§23–24 |
| S15-ARCH-20 | Dependency boundary frozen. | PASS | AD-18; §25 |
| S15-ARCH-21 | Frontend test architecture frozen. | PASS | AD-19; §26 |
| S15-ARCH-22 | Frontend governed CI architecture frozen. | PASS | AD-20; §§27, 35 |
| S15-ARCH-23 | Deployment/runtime assumptions frozen. | PASS | AD-21; §28 |
| S15-ARCH-24 | Accessibility + observability requirements frozen. | PASS | AD-22/23; §§29–30 |
| S15-ARCH-25 | Backend change boundary frozen. | PASS | AD-24; §31 |
| S15-ARCH-26 | No writes/models/broker/provider/FP/tag/release/deploy authority. | PASS | §§4, 37–38, 41 |

```text
ARCH_AC_COUNT = 26
ARCH_AC_UNIQUE_COUNT = 26
ARCH_AC_DUPLICATE_COUNT = 0
ARCH_AC_MISSING_COUNT = 0
```

---

## 34. Governance Handoff

Architecture designs the following; **Governance** must later freeze
policy authority for:

1. Browser auth authority
2. Scope non-weakening (`intelligence:runs:read`)
3. Token handling rules
4. CORS security
5. Public/private DTO rendering
6. Human Review read-only boundary
7. ADE visibility-only boundary
8. Error semantics
9. Freshness semantics
10. Frontend dependency governance
11. Frontend CI evidence requirements
12. Deployment authority

This artifact does **not** create the Governance issue and does not
resolve Governance policy beyond Architecture boundaries.

---

## 35. Frontend CI Playwright Decision

**Choice:**

- `frontend-quality-gate` is the deterministic required frontend quality
  job for relevant Sprint 15 frontend changes: `npm ci`, lint,
  typecheck, Vitest, `next build`.
- Playwright is a **separate** bounded smoke job for Premarket-touching
  **implementation** PRs.
- Playwright is **not** part of this docs-only Architecture candidate
  validation.
- Governance/Policy/IA may later freeze exact branch-rule enforcement
  without weakening the requirement that implementation evidence include
  successful bounded E2E.

**Rationale:** Separate browser/integration concerns from deterministic
static/unit quality; avoid making docs-only Architecture work depend on
browser runtime; still require E2E evidence for actual Premarket
implementation.

---

## 36. Post-IA Workstreams

```text
POST_IA_WORKSTREAM_COUNT = 3
```

| WS | Title | Scope (after future IA only) |
| --- | --- | --- |
| WS1 | Intelligence Run API Client + Auth Integration | Typed client; auth provider; token flow; API env config; CORS/config wiring |
| WS2 | Premarket Command Center Read-Only Views | Latest dashboard-capable; run detail; Dashboard; ADE; HR if SHOULD capacity permits; fingerprint/run-id lookup; bounded UX states |
| WS3 | Hardening / Tests / CI | Security hardening; XSS proof; private ADE non-rendering; a11y; unit/component tests; E2E; frontend governed CI |

These remain **PROPOSED**. They are **not** authorized by this
Architecture artifact.

---

## 37. IN / OUT / DEFERRED

### IN (Architecture)

AD-01..AD-24; S15-ARCH-01..26 evidence; Governance handoff; post-IA
workstream boundaries; CORS/auth/env/CI/test design freezes.

### OUT

Source/UI/auth/CORS/CI implementation; dependencies; HR writes; ADE
invoke; model participation; broker execution; provider expansion;
Feature Platform expansion; new intelligence routes/contracts;
production deployment; tag; release; deploy.

### DEFERRED

Production OIDC; advanced CSP nonce/hash; formal production UI hosting;
HR write workflow; ADE invocation; Morning Briefing prose not persisted
by Sprint 14; historical snapshot-contract selector; Feature Platform
expansion; new providers; models; broker execution.

---

## 38. Risks / Findings

| Severity | Finding |
| --- | --- |
| HIGH | CORS currently absent; future implementation required after IA |
| HIGH | Mock console session ≠ API JWT; future token integration required after IA |
| MEDIUM | HR `recorded_payload` requires XSS-safe rendering at implementation |
| MEDIUM | Frontend currently absent from governed CI |
| LOW | Advanced CSP deferred |
| INFO | Production UI hosting topology not established |

These are Architecture findings, not candidate blockers for this DRAFT
artifact.

---

## 39. Lifecycle / Completion Conditions

Architecture becomes **APPROVED / EFFECTIVE** only after:

1. Independent review PASS
2. Controlled commit
3. Push / PR with `Closes #160`
4. Exact-head CI success
5. Required human approval
6. Controlled merge (merge commit)
7. Post-merge exact-head CI success
8. Issue #160 closed via PR lifecycle

Even then:

```text
SPRINT_15_IMPLEMENTATION_AUTHORIZED = NO
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED/DEFERRED
```

Next eligible gate after Architecture APPROVED/EFFECTIVE: **Governance**.

---


## 39a. Current Implementation Finality (Status Sync)

This Architecture Gate is **APPROVED / EFFECTIVE** (#160 / PR #161 @
`d50bd2f6579898f80b7f5faedc6a5b6999ad7363`). Subsequent Governance, Policy /
Contract Freeze, Implementation Authorization, and WS1–WS3 completed under
separate gates. AD-* decisions in this document remain frozen and unchanged by
Status Sync.

| WS | Evidence | State |
| --- | --- | --- |
| WS1 | #168 / #169; impl `d2900c399d87cbb63e54666b58d5253a2aca6bd2`; merge `d97b9b9e02542dd64cd68970aae7e8d6cec1881b` | MERGED_POST_MERGE_CI_GREEN_FINAL |
| WS2 | #170 / #171; impl `ae6f7460808a35026375c0e5277db64f0d007991`; merge `ed52c5e10445fe69a2d728ccd15239788192113a` | MERGED_POST_MERGE_CI_GREEN_FINAL |
| WS3 | #172 / #173; impl `9e53af68c6ceaa1d2abfb92f4a1be127caa9215b`; merge `32e498ad791cbfbac6eaecbcf360a16706c38fa2`; CI `38073153105` success | MERGED_POST_MERGE_CI_GREEN_FINAL |

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

Architecture Status Sync does **not** declare Sprint 15 COMPLETE.

---

## 40. Explicit Non-Authorization

```text
ARCHITECTURE_GATE_APPROVAL ≠ IMPLEMENTATION_AUTHORIZATION
IMPLEMENTATION_SEQUENCE = 3/3 COMPLETE (under separate IA; not by this Architecture)
SPRINT_15_COMPLETE = NO
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED/DEFERRED
PUBLIC_WRITE_API_AUTHORIZED = NO
HUMAN_REVIEW_WRITE_UI_AUTHORIZED = NO
ADE_INVOCATION_AUTHORIZED = NO
NEW_PROVIDER_INTEGRATION_AUTHORIZED = NO
FEATURE_PLATFORM_EXPANSION_AUTHORIZED = NO
QUERY_TIME_RECOMPUTATION_AUTHORIZED = NO
TAG_RELEASE_DEPLOY_AUTHORIZED = NO
NEW_FRONTEND_DEPENDENCY_AUTHORIZED = NO
```

No Architecture decision itself grants implementation authority. Implementation
proceeded only under separately approved Implementation Authorization.
