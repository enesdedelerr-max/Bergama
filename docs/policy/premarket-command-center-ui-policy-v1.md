# Premarket Command Center UI Policy / Contract v1

## 1. Metadata

**Policy ID:** `premarket-command-center-ui.policy.v1`  
**Version:** v1  
**Title:** Read-Only Premarket Command Center UI Policy / Contract Freeze v1  
**Status:** DRAFT  
**Document class:** Combined Policy / Contract Freeze  
**Sprint:** 15  
**Gate:** Combined Policy / Contract Freeze  
**Theme:** Read-Only Premarket Command Center UI  
**Policy issue:** [#164](https://github.com/enesdedelerr-max/Bergama/issues/164)  
**Planning:** `APPROVED_EFFECTIVE`  
**Architecture Artifact ID:** `premarket-command-center-ui.architecture.v1` — `APPROVED_EFFECTIVE`  
**Architecture merge:** `d50bd2f6579898f80b7f5faedc6a5b6999ad7363`  
**Governance Artifact ID:** `premarket-command-center-ui.governance.v1` — `APPROVED_EFFECTIVE`  
**Governance Issue:** [#162](https://github.com/enesdedelerr-max/Bergama/issues/162)  
**Governance PR:** [#163](https://github.com/enesdedelerr-max/Bergama/pull/163)  
**Governance merge:** `abd51911af065a02d7bb4438cd1aaf3e694b4602`  
**Authoritative candidate base:** `abd51911af065a02d7bb4438cd1aaf3e694b4602`

```text
POLICY APPROVAL ≠ IMPLEMENTATION AUTHORIZATION
POLICY APPROVAL ≠ IMPLEMENTATION
SPRINT_15_IMPLEMENTATION_AUTHORIZATION_STATE = NOT_STARTED
SPRINT_15_IMPLEMENTATION_AUTHORIZED = NO
UI_IMPLEMENTATION_MAY_BEGIN = NO
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED/DEFERRED
```

---

## 2. Purpose

Freeze the implementation-facing Policy / Contract for the Sprint 15
Read-Only Premarket Command Center UI after Planning, Architecture, and
Governance finality and before Implementation Authorization.

This document converts approved Governance boundaries into exact
mechanical contracts. It does **not** authorize product implementation.

---

## 3. Authority / Inputs

| Layer | Authority |
| --- | --- |
| Planning Gate | `APPROVED_EFFECTIVE` |
| Architecture | `premarket-command-center-ui.architecture.v1` @ `d50bd2f6579898f80b7f5faedc6a5b6999ad7363` |
| Governance | `premarket-command-center-ui.governance.v1` @ `abd51911af065a02d7bb4438cd1aaf3e694b4602` |
| Sprint 14 public read contracts | `intelligence-run-productization.policy.v1` and implemented GET surface |
| Policy Issue | #164 |

This Policy does **not** reopen Architecture or Governance decisions
unless a later governed correction explicitly amends them.

---

## 4. Combined Policy / Contract Mode

```text
POLICY_CONTRACT_MODE = COMBINED
```

One governed artifact freezes Policy decisions and mechanical contracts.
No separate contract artifact is required for Sprint 15.

---

## 5. Scope

In scope:

- browser auth / bootstrap / token lifecycle contracts
- authorization and scope UX/server boundary
- CORS and API-base configuration contracts
- typed client consumption of Sprint 14 public DTOs
- Dashboard / run detail / lookup read UX contracts
- HR / ADE visibility contracts
- error / freshness / cache / retry contracts
- accessibility / security-header / CSRF / logging contracts
- zero-new-dependency freeze
- future frontend CI / Playwright / test evidence contracts
- bounded backend CORS/config change boundary (for later IA)
- deployment and write/model/broker/provider firewalls
- exact PD / AC / traceability / IA handoff

Out of scope: product implementation, production OIDC/hosting, new
routes/DTOs/persistence, model/broker execution, dependency additions.

---

## 6. Explicit Non-Authorization

```text
POLICY_ARTIFACT_LITERAL_STATUS = DRAFT
SPRINT_15_IMPLEMENTATION_AUTHORIZED = NO
UI_IMPLEMENTATION_MAY_BEGIN = NO
POLICY_APPROVAL ≠ IMPLEMENTATION_AUTHORIZATION
```

This DRAFT candidate does **not** authorize:

- Implementation Authorization
- UI / auth / CORS / CI implementation
- dependency changes
- production deployment
- model participation
- broker execution

---

## 7. Terminology

| Term | Meaning |
| --- | --- |
| Mock console session | Local `ConsoleSession` shell identity; not API auth |
| Bearer JWT | API access token carried in `Authorization` header |
| Bootstrap | Local/test `POST /api/v1/auth/token` grant |
| Product read | Sprint 14 intelligence-run GET surface for Premarket UI |
| Public DTO | Sprint 14 serialized product contracts only |
| Fail closed | No mock/stale/silent product substitution |

---

## 8. Authentication State Machine

Exact states:

```text
UNAUTHENTICATED
BOOTSTRAP_LOADING
AUTHENTICATED
EXPIRED
BOOTSTRAP_DISABLED
BOOTSTRAP_FAILED
INSUFFICIENT_SCOPE
```

Transitions / behavior:

| Condition | Result |
| --- | --- |
| No valid token and bootstrap not executing | `UNAUTHENTICATED` |
| Authorized bootstrap attempt in flight | `BOOTSTRAP_LOADING` |
| Bootstrap success | `AUTHENTICATED` |
| Token expiry | Clear in-memory token → `EXPIRED` / unauthenticated product boundary |
| HTTP 401 | Clear token; if bootstrap enabled, **at most one** automatic reacquisition |
| Reacquisition success | `AUTHENTICATED` |
| Reacquisition failure / bootstrap disabled failure | Fail closed into unauthenticated / `BOOTSTRAP_FAILED` / `BOOTSTRAP_DISABLED` as applicable |
| HTTP 403 `authz.insufficient_scope` | **Do not** clear token solely for 403; enter `INSUFFICIENT_SCOPE`; automatic retry = 0 |
| Logout | Clear token + Premarket query cache |
| Token replacement | Clear Premarket query cache before/with authority transition |

Rules:

- No product GET without valid Bearer.
- Mock/local console session MUST NEVER substitute for API authentication.

---

## 9. Token Storage / Lifecycle

```text
TOKEN_STORAGE = IN_MEMORY_ONLY
```

Forbidden:

- `localStorage`
- `sessionStorage`
- IndexedDB
- cookie auth
- BFF token persistence
- URL / query token
- token logging

Expiry must be enforced. Token replacement must not leak cached data
between principals. Raw auth response must not be persisted/logged beyond
fields required for in-memory auth lifecycle (`access_token`,
`token_type`, `expires_in`).

---

## 10. Bootstrap Contract

```text
BOOTSTRAP_ENDPOINT = POST /api/v1/auth/token
BOOTSTRAP_GRANT = bootstrap
```

| Field | Contract |
| --- | --- |
| Request | `{"grant_type":"bootstrap"}` only; extra fields forbidden |
| Response | `access_token`, `token_type = bearer`, `expires_in > 0` |
| Default TTL | 900 seconds (current repository default) |
| Local/test | enabled according to existing configuration authority |
| Staging/production | disabled by default |
| Disabled | HTTP `404` / `auth.bootstrap_disabled` |
| Scopes | server-selected; browser cannot request/escalate |
| Current server scopes may include | `api:read`, `intelligence:runs:read` |
| Product read still requires | exact `intelligence:runs:read` |

Production bootstrap expansion is **not** authorized.

---

## 11. Authorization Contract

```text
PRODUCT_READ_SCOPE = intelligence:runs:read
API_READ_ALONE = INSUFFICIENT
WILDCARD_SCOPE = FORBIDDEN
```

- Client-side scope checks are UX only.
- Server authorization is authoritative.
- `401` = authentication failure.
- `403` = authorization / insufficient scope.
- No scope escalation.
- No retry loop for insufficient scope.

---

## 12. CORS Contract

```text
CORS_CONFIG_KEY = BERGAMA_CORS__ALLOWED_ORIGINS
CORS_SETTINGS = nested CorsSettings under BERGAMA_ / __ convention
CORS_MAX_AGE_POLICY = OMITTED
```

| Rule | Value |
| --- | --- |
| Input | comma-separated origins |
| Valid origin | `scheme://host[:port]` |
| Path / query / fragment | forbidden |
| Trailing slash | normalize to canonical origin |
| Unset / empty | deny all |
| Wildcard | reject / fail closed |
| Origin reflection | forbidden |
| Methods | `GET`, `OPTIONS`, `POST` |
| POST purpose | auth bootstrap only |
| Allowed request headers | `Authorization`, `Content-Type` |
| Credentials | `false` |
| Exposed headers | none required |
| Max-Age | omitted / framework default; no custom freeze |
| Production-origin invention | forbidden |

---

## 13. API Base Contract

```text
API_BASE_URL_CONFIG_KEY = NEXT_PUBLIC_BERGAMA_API_BASE_URL
```

Requirements:

- absolute HTTP/HTTPS URL
- origin-only
- no query / fragment
- no non-root path
- normalize/remove trailing slash
- missing → fail closed on Premarket surface
- invalid → fail closed
- mock fallback forbidden
- production hostname invention forbidden

HTTPS is required outside `localhost`, `127.0.0.1`, and authorized
local/dev/test contexts. HTTP is permitted only for authorized
local/dev/test console use. This rule does **not** authorize production
deployment.

---

## 14. Public DTO Contract

Client may consume only Sprint 14 public DTO families:

- `IntelligenceRunRead`
- `IntelligenceRunDashboardRead`
- `IntelligenceRunHumanReviewRead`
- `IntelligenceRunAdeRead`
- `ProductErrorResponse`

Rules:

- known public fields only
- missing required public fields → fail closed
- unknown response fields → never auto-render
- no generic unknown-object dump
- no new DTO authority
- no new backend route authority

---

## 15. Private Data Exclusion

Never display / log / cache as product content:

- ORM internals
- raw provider payloads
- provider secrets
- stack traces
- model-private state
- unbounded news payloads
- ADE `recorded_attestation_payload`
- Bearer token
- raw auth response

HR `recorded_payload` is public but untrusted. Current bound: **8192**.
Render as escaped text only.

---

## 16. Dashboard Contract

Sprint 15 MUST provide the read-only latest Dashboard-capable experience.

Support states: loading / empty / error / present.

Allowed public display includes:

- `run_id`
- fingerprint
- `as_of`
- `persisted_at`
- `PipelineOutcome`
- stage presence
- Dashboard public snapshot
- `snapshot_contract_version`
- `persistence_schema_version`

Forbidden: query-time recomputation; live-market authority; trading-safe
classification; buy/sell/hold reinterpretation.

---

## 17. Run Detail / Lookup Contract

Required frontend routes:

```text
/premarket
/premarket/runs/[runId]
```

Support:

- latest Dashboard-capable read
- manual run-id lookup
- fingerprint lookup
- run detail navigation

Use only existing Sprint 14 backend GET routes. No new backend route.
No write route.

---

## 18. Human Review Contract

```text
HR_READ_VISIBILITY = SHOULD
HR_WRITE_UI_AUTHORIZED = NO
```

- `recorded_payload` untrusted
- escaped text only
- no `dangerouslySetInnerHTML`
- no HTML / Markdown / script execution
- bounded rendering
- absence → explicit stage-not-present / absent state
- no sanitizer dependency by default

---

## 19. ADE Visibility Contract

```text
ADE_READ_VISIBILITY = MUST
ADE_INVOKE_UI_AUTHORIZED = NO
```

Public DTO fields only. Forbidden: `recorded_attestation_payload`;
invoke; rerun/invoke CTA; override; prompt; model selector; decision
mutation; trade execution implication; buy/sell/hold reinterpretation.

Accept/abstain may be displayed only as persisted public ADE result.

---

## 20. Error Contract

| HTTP | Code / class | Retry | Auth / UI action |
| --- | --- | --- | --- |
| 400 | `intelligence.runs.invalid_identifier` | 0 | fail closed; invalid-identifier state |
| 401 | `auth.*` | 0 for normal request | clear token; ≤1 bootstrap reacquisition if enabled |
| 403 | `authz.insufficient_scope` | 0 | retain token; insufficient-scope state |
| 404 | `intelligence.runs.run_not_found` | 0 | run-not-found state |
| 404 | `intelligence.runs.stage_not_present` | 0 | stage-absent state |
| 404 | `auth.bootstrap_disabled` | 0 | bootstrap-disabled state |
| 409 | `intelligence.runs.unsupported_snapshot_contract` | 0 | fail closed |
| 500 | `intelligence.runs.corrupt_persisted_snapshot` | 0 | fail closed |
| 503 | `intelligence.runs.storage_unavailable` | 1 max | fail closed until success |
| — | network failure | 1 max | fail closed until success |
| — | abort | 0 | no retry |

No stale/mock substitution. No silent fallback.

---

## 21. Freshness Contract

Server-authoritative:

- `as_of`
- `persisted_at`
- `age_seconds`
- `snapshot_contract_version`
- `persistence_schema_version`

Relative time formatting may be client-derived presentation only. Client
clock must not create authoritative freshness classification.

Never label data: safe; safe to trade; fresh enough to trade; live; or
equivalent.

---

## 22. Cache / Query Contract

```text
staleTime = 30000
gcTime = 300000
refetchOnWindowFocus = false
refetchOnReconnect = false
polling = none
AbortSignal = required
```

- Persistent product/auth query cache forbidden.
- Logout / token replacement: clear Premarket cache.
- Prevent cross-user / principal cache leakage.
- Stable query-key families for: latest Dashboard-capable; run detail;
  fingerprint lookup; HR; ADE.
- Do **not** include Bearer token itself in query keys.

---

## 23. Retry Contract

```text
DEFAULT_AUTOMATIC_RETRY = 0
RETRY_503_MAX = 1
RETRY_NETWORK_MAX = 1
```

| Class | Automatic retry |
| --- | --- |
| 400 / 403 / 404 / 409 / 500 / abort | 0 |
| 401 normal product request | 0 (separate ≤1 bootstrap reacquisition) |
| 503 | 1 maximum |
| Network failure | 1 maximum |

No infinite retry. No polling-as-retry.

---

## 24. Typed Client Contract

Use native `fetch` + existing TanStack Query. No new HTTP client
dependency.

Responsibilities:

- validated API base
- Bearer header injection
- bootstrap POST
- GET requests
- AbortSignal propagation
- safe JSON parsing
- `ProductErrorResponse` decoding
- unexpected status / payload handling
- credentials omitted / no cookies
- safe logging

Do not send `Content-Type` on GET unless mechanically necessary.
Bootstrap POST may use `Content-Type: application/json`.

Architecture client boundary paths remain authoritative for later IA:

- `apps/platform-console/src/lib/api/intelligence-runs.ts`
- `apps/platform-console/src/contracts/types/intelligence-runs.ts`
- hooks under `apps/platform-console/src/hooks/`

---

## 25. UI Route / Navigation Contract

```text
PREMARKET_ROUTE_ROOT = /premarket
RUN_DETAIL_ROUTE_PATTERN = /premarket/runs/[runId]
```

Lookup behavior remains rooted in Premarket experience. Fingerprint and
run-id lookups must navigate/display an existing persisted run. No visual
design freeze. No production routing/deployment authority.

---

## 26. UX State Contract

Semantic state identifiers (literal cosmetic copy **not** frozen):

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

Implementation wording may vary only if semantics remain unchanged.

Forbidden semantics: live; safe to trade; buy; sell; hold; and equivalent
recommendation / trading-authority wording.

---

## 27. Accessibility Contract

Require:

- keyboard navigation
- visible focus
- semantic headings
- landmarks
- correct button/link semantics
- labeled lookup controls
- loading announcements
- error announcements
- status not color-only
- table semantics
- accessible names for HR/ADE structured displays

No visual-design mandate.

---

## 28. Security Header Contract

Classification: **SHOULD**.

Require:

- `X-Content-Type-Options: nosniff`
- Frame denial using **either**:
  - CSP `frame-ancestors 'none'`
  - **or** `X-Frame-Options: DENY`

Equivalent either is acceptable. Advanced CSP: DEFERRED. HSTS: DEFERRED.
Do not expand deployment authority.

---

## 29. CSRF Invariant

```text
CSRF_CLASSIFICATION = N/A
```

Basis: Bearer Authorization header; `credentials=false`; no cookie auth.

If cookie/credential-based auth is introduced later, CSRF classification
MUST be reopened under new authority. Sprint 15 may **not** introduce
cookie auth.

---

## 30. Logging / Telemetry Contract

```text
NEW_TELEMETRY_AUTHORIZED = NO
```

Never log: Bearer tokens; raw auth responses; private DTO data; ADE
`recorded_attestation_payload`; provider secrets.

Bounded safe logging may include: HTTP status; public error code;
non-sensitive request category.

Production browser console logging of sensitive/raw payloads: forbidden.

---

## 31. Dependency Contract

```text
NEW_FRONTEND_RUNTIME_DEPENDENCIES = 0
NEW_FRONTEND_DEV_DEPENDENCIES = 0
NEW_BACKEND_DEPENDENCIES = 0
```

Use existing: Next.js; React; TanStack Query; Tailwind; Vitest / RTL;
Playwright; native fetch. No sanitizer dependency. Any new direct
dependency requires separate authority.

---

## 32. Frontend CI Contract

```text
FRONTEND_CI_JOB_NAME = frontend-quality-gate
```

Required for PRs touching `apps/platform-console/**` and shared
config/dependency files that materially affect the console.

Required evidence (repository-native commands):

1. `npm ci`
2. `npm run lint`
3. `npm run typecheck`
4. `npm test` (`vitest run`)
5. `npm run build`
6. bounded Playwright smoke (`npm run test:e2e` scope)

If an implementation PR also changes backend CORS/config, existing
backend `quality-gate` remains required in addition.

This Policy artifact does **not** implement CI.

---

## 33. Playwright Contract

Bounded Premarket smoke must cover at minimum:

- Premarket route loads
- auth state
- latest Dashboard state
- run-detail navigation
- HR safe rendering
- ADE visibility
- critical fail-closed error state
- absence of write controls

Do not create broad full-product E2E expansion.

---

## 34. Test Evidence Contract

Future implementation test layers:

- unit
- component
- typed client contract
- security / privacy
- accessibility baseline
- bounded Playwright E2E

Backend regression required when CORS/config backend files change.
Policy candidate itself remains docs-only.

---

## 35. Backend Change Boundary

Future IA may authorize only bounded backend work required for:

- CORS settings / config
- CORS middleware wiring
- existing bootstrap/config wiring if mechanically required

Not authorized by Policy itself. Explicitly exclude: new intelligence
routes; DTO changes; persistence changes; new intelligence writes; HR
writes; ADE writes/invocation; provider additions; Feature Platform
expansion; model execution; broker execution.

---

## 36. Deployment Boundary

Allowed environments: **local / dev / test / CI**.

Deferred: production hosting; production OIDC; production secrets;
production hostname; deployment workflows; DNS; CDN; production
analytics.

No production authority may be inferred from this artifact.

---

## 37. Write Firewall

Only existing `POST /api/v1/auth/token` is within the currently
acknowledged mutation boundary.

No intelligence writes; HR writes; ADE writes; trade/order writes;
portfolio mutation; admin mutation.

---

## 38. Model Firewall

```text
MODEL_PARTICIPATION = UNAUTHORIZED
```

Persisted ADE result visibility does not authorize model execution.
No prompt / model selector / invoke path.

---

## 39. Broker Firewall

```text
BROKER_EXECUTION = DENIED/DEFERRED
```

No order placement; broker adapter activation; execution CTA; or implied
trade authority.

---

## 40. Provider / Feature Platform Firewall

No: new providers; live provider expansion; Feature Platform expansion;
new persistence schema; new intelligence API route; new product mutation
route.

---

## 41. Policy Decision Matrix

```text
POLICY_PD_DEFINITION_COUNT = 32
POLICY_PD_UNIQUE_ID_COUNT = 32
POLICY_PD_DUPLICATE_ID_COUNT = 0
```

| ID | Decision | Governance Source | Architecture Source | Reason | Implementation Contract | Verification / Evidence | Deferred / Out-of-Scope |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PD-01 | Combined Policy/Contract freeze; Policy ≠ IA/implementation | GD firewall; S15-GOV-01 | Planning/Arch non-auth | Single mechanical freeze before IA | Literal DRAFT; non-authorization banners | Review proves no IA language | Product implementation |
| PD-02 | Auth state machine; mock ≠ API auth | GD-01; S15-GOV-02 | AD-04 | Prevent fake product authorization | Exact states/transitions in §8 | Auth state tests; mock cannot authorize GETs | Production identity provider |
| PD-03 | In-memory token lifecycle only | GD-02; S15-GOV-03 | AD-05/06 | Reduce persistence/XSS/cookie surface | §9 forbidden stores; clear on expiry/401/logout/replace | Storage absence proofs | Cookie/BFF auth |
| PD-04 | Bootstrap exact contract | GD-03/04; S15-GOV-04 | AD-06 | Bound local/test acquisition | §10 endpoint/grant/TTL/disabled | Contract tests against existing auth router | Production bootstrap expansion |
| PD-05 | AuthTokenProvider seam; OIDC deferred | GD-04 | AD-07 | Future identity without rewrite | Provider seam required; no OIDC selected | Architecture path review | Production OIDC selection |
| PD-06 | Exact product scope + server authority | GD-05; S15-GOV-05 | AD-04/authz | Least privilege | `intelligence:runs:read`; `api:read` alone insufficient | 403 proofs; no wildcard | Additional product scopes |
| PD-07 | 401 clear/reauth; 403 retain+insufficient-scope | GD-05/18; S15-GOV-05 | AD-11 | Distinct auth vs authz UX | §8/§20 behaviors; ≤1 bootstrap reacquisition | Client contract tests | Cookie-session reauth models |
| PD-08 | CORS env allowlist / default deny | GD-06; S15-GOV-06 | AD-08 | Secure browser→API boundary | §12 `BERGAMA_CORS__ALLOWED_ORIGINS` | Config review; wildcard rejection tests | Custom CORS max-age / extra headers |
| PD-09 | API base fail-closed | GD-07; S15-GOV-07 | AD-09 | Explicit non-secret origin | §13 `NEXT_PUBLIC_BERGAMA_API_BASE_URL` | Missing/invalid fail-closed tests | Production host invention |
| PD-10 | Public DTO-only typed client | GD-08; S15-GOV-08 | AD-10 | Preserve S14 product boundary | §14 families only | Typed client contract tests | New DTO/route authority |
| PD-11 | Private exclusion / typed projection | GD-08/16 | AD-10/15 | Privacy minimization | §15 forbidden set; unknown never auto-rendered | Privacy/security tests | Client hard-reject of all unknown JSON keys beyond typed ignore |
| PD-12 | Latest Dashboard; no trading reinterpretation | GD-12/13; S15-GOV-12 | AD-13/18 | Read-only product display | §16 loading/empty/error/present | UI contract tests | Query-time recomputation |
| PD-13 | Run detail + fingerprint/run-id lookups | GD-12; S15-GOV-13 | AD-02 | Minimal navigation | §17 routes; S14 GETs only | Route/nav tests | New backend routes |
| PD-14 | HR SHOULD read-only XSS-safe | GD-09; S15-GOV-09 | AD-14 | Untrusted payload safety | §18 escaped text; no write | XSS/render tests | Sanitizer dependency; HR writes |
| PD-15 | ADE MUST visibility-only | GD-10; S15-GOV-10 | AD-15 | No model/execution path | §19 public fields only | ADE privacy + no-CTA tests | ADE invoke/override |
| PD-16 | Exact error matrix | GD-11; S15-GOV-11 | AD-11 | Fail-closed product UX | §20 mapping | Error matrix tests | Mock/stale substitution |
| PD-17 | Server-authoritative freshness | GD-14; S15-GOV-14 | AD-12 | No client trading freshness | §21 | Freshness display tests | Safe-to-trade labels |
| PD-18 | Cache/query lifecycle | GD-15/20; S15-GOV-15 | AD-03 | Auth isolation + bounded cache | §22 numeric params | Query-key/cache-clear tests | localStorage persistence |
| PD-19 | Bounded retry matrix | GD-11/20 | AD-11 | Avoid misleading retry UX | §23 | Retry policy tests | Polling-as-retry |
| PD-20 | Native fetch typed client | GD-19; S15-GOV-19 | AD-03 | No new HTTP client | §24 | Client module review | New HTTP libraries |
| PD-21 | Routes/navigation | S15-GOV-13 | AD-02 | Premarket-rooted UX | §25 | Nav integration tests | Visual design freeze |
| PD-22 | UX semantic states | GD-11 | Arch UX | Distinct fail-closed states | §26 state IDs; copy not frozen | State coverage tests | Trading wording |
| PD-23 | Accessibility baseline | GD-20; S15-GOV-20 | Arch a11y | Operational accessibility | §27 | a11y baseline checks | Visual redesign |
| PD-24 | Security headers SHOULD | GD-17; S15-GOV-17 | AD-16 | Bounded browser hardening | §28 nosniff + frame denial either | Header evidence | Advanced CSP/HSTS |
| PD-25 | CSRF N/A invariant | GD-17 | AD-16 | Current Bearer model | §29; reopen if cookies | Auth-model review | Cookie auth |
| PD-26 | Logging/telemetry prohibition | GD-18; S15-GOV-18 | Arch security | Fail-closed privacy | §30 | Logging review | New APM/telemetry |
| PD-27 | Zero new dependencies | GD-15; S15-GOV-15 | Arch deps | Supply-chain control | §31 0/0/0 | Manifest/lockfile review | Separate dependency authority |
| PD-28 | Frontend CI evidence | GD-19; S15-GOV-19 | Arch CI | Exact-head FE quality | §32 `frontend-quality-gate` | Future CI runs | Docs-only FE validation |
| PD-29 | Bounded Playwright smoke | GD-19 | Arch E2E | Minimum Premarket smoke | §33 | Playwright suite | Broad full-product E2E |
| PD-30 | Test-layer contract | GD-19 | Arch tests | Layered evidence | §34 | Test plan review | Over-mocking product behavior |
| PD-31 | Backend CORS/config-only boundary | GD-21/24; S15-GOV-21/24 | AD-24 | Bound backend mutation | §35 | Diff review at IA | Intel route/DTO/persistence changes |
| PD-32 | Deployment + 3 WS handoff + firewalls | GD-22/23/24; S15-GOV-22..26 | AD WS | Preserve authority sequencing | §§36–40, §44 | Handoff/firewall review | Production deploy; 4th workstream |

---

## 42. Acceptance Criteria Matrix

```text
POLICY_AC_DEFINITION_COUNT = 30
POLICY_AC_UNIQUE_ID_COUNT = 30
POLICY_AC_DUPLICATE_ID_COUNT = 0
```

| ID | Acceptance Criterion | Evidence / Verification | Traceability |
| --- | --- | --- | --- |
| S15-POL-01 | Combined mode + explicit non-authorization firewall | §§4–6 banners | PD-01; S15-GOV-01 |
| S15-POL-02 | Auth state machine + mock ≠ API auth frozen | §8 | PD-02; GD-01 |
| S15-POL-03 | In-memory-only token and forbidden persistent stores frozen | §9 | PD-03; GD-02 |
| S15-POL-04 | Bootstrap route/grant/disabled/TTL/server-scopes frozen | §10 | PD-04; GD-03/04 |
| S15-POL-05 | AuthTokenProvider + OIDC deferred frozen | PD-05 | GD-04; AD-07 |
| S15-POL-06 | Exact scope + server authority frozen | §11 | PD-06; GD-05 |
| S15-POL-07 | 401/403 client behavior frozen | §§8,20 | PD-07 |
| S15-POL-08 | CORS schema/methods/headers/credentials/default-deny frozen | §12 | PD-08; GD-06 |
| S15-POL-09 | API base fail-closed validation frozen | §13 | PD-09; GD-07 |
| S15-POL-10 | Public DTO families only frozen | §14 | PD-10; GD-08 |
| S15-POL-11 | Private/ADE payload exclusion + projection rule frozen | §15 | PD-11; GD-08/16 |
| S15-POL-12 | Dashboard latest + no trading semantics frozen | §16 | PD-12; GD-12/13 |
| S15-POL-13 | Routes/lookups MUST set frozen | §§17,25 | PD-13; AD-02 |
| S15-POL-14 | HR XSS-safe SHOULD rendering + no write frozen | §18 | PD-14; GD-09 |
| S15-POL-15 | ADE MUST visibility-only frozen | §19 | PD-15; GD-10 |
| S15-POL-16 | Error matrix complete + fail-closed frozen | §20 | PD-16; GD-11 |
| S15-POL-17 | Freshness authority frozen | §21 | PD-17; GD-14 |
| S15-POL-18 | Cache key/stale/gc/refetch/clear rules frozen | §22 | PD-18 |
| S15-POL-19 | Retry matrix frozen | §23 | PD-19 |
| S15-POL-20 | Client fetch/AbortSignal/credentials omit frozen | §24 | PD-20 |
| S15-POL-21 | Distinct UX states frozen | §26 | PD-22 |
| S15-POL-22 | Accessibility baseline frozen | §27 | PD-23 |
| S15-POL-23 | Security headers SHOULD + CSRF N/A invariant frozen | §§28–29 | PD-24/25 |
| S15-POL-24 | Logging/telemetry prohibition frozen | §30 | PD-26 |
| S15-POL-25 | Zero-new-dependency freeze explicit | §31 | PD-27 |
| S15-POL-26 | Frontend CI + Playwright evidence contract frozen | §§32–33 | PD-28/29 |
| S15-POL-27 | Backend CORS/config-only change boundary frozen | §35 | PD-31 |
| S15-POL-28 | Deployment authority local/dev/test/CI frozen | §36 | PD-32 |
| S15-POL-29 | Model/broker/write firewall restated | §§37–40 | PD-32; GD-21..23 |
| S15-POL-30 | Exactly three post-IA workstreams; IA remains unauthorized | §44 | PD-32; S15-GOV-26 |

---

## 43. Traceability Matrix

```text
TRACEABILITY_GAP_COUNT = 0
TRACEABILITY_AMBIGUITY_COUNT = 0
```

| Governance obligation | Classification | Policy Decision | Policy AC | Future WS |
| --- | --- | --- | --- | --- |
| GD-01 / S15-GOV-02 | mapped | PD-02 | S15-POL-02 | WS1 |
| GD-02 / S15-GOV-03 | mapped | PD-03 | S15-POL-03 | WS1 |
| GD-03 / S15-GOV-04 | mapped | PD-04 | S15-POL-04 | WS1 |
| GD-04 | mapped | PD-04/05 | S15-POL-04/05 | WS1 |
| GD-05 / S15-GOV-05 | mapped | PD-06/07 | S15-POL-06/07 | WS1 |
| GD-06 / S15-GOV-06 | mapped | PD-08 | S15-POL-08 | WS1/WS3 |
| GD-07 / S15-GOV-07 | mapped | PD-09 | S15-POL-09 | WS1 |
| GD-08 / S15-GOV-08 | mapped | PD-10/11 | S15-POL-10/11 | WS1/WS2 |
| GD-09 / S15-GOV-09 | mapped | PD-14 | S15-POL-14 | WS2 |
| GD-10 / S15-GOV-10 | mapped | PD-15 | S15-POL-15 | WS2 |
| GD-11 / S15-GOV-11 | mapped | PD-16/19/22 | S15-POL-16/19/21 | WS2/WS3 |
| GD-12 / S15-GOV-12 | mapped | PD-12 | S15-POL-12 | WS2 |
| GD-13 / S15-GOV-13 | mapped | PD-13/21 | S15-POL-13 | WS2 |
| GD-14 / S15-GOV-14 | mapped | PD-17 | S15-POL-17 | WS2 |
| GD-15 / S15-GOV-15 | mapped | PD-18/27 | S15-POL-18/25 | WS1/WS3 |
| GD-16 | mapped | PD-11/15 | S15-POL-11/15 | WS2/WS3 |
| GD-17 / S15-GOV-17 | mapped | PD-24/25 | S15-POL-23 | WS3 |
| GD-18 / S15-GOV-18 | mapped | PD-26 | S15-POL-24 | WS3 |
| GD-19 / S15-GOV-19 | mapped | PD-20/28/29/30 | S15-POL-20/26 | WS1/WS3 |
| GD-20 / S15-GOV-20 | mapped | PD-23 | S15-POL-22 | WS2/WS3 |
| GD-21 / S15-GOV-21 | mapped | PD-31 | S15-POL-27/29 | WS1 |
| GD-22 / S15-GOV-22 | mapped | PD-32 | S15-POL-29 | all |
| GD-23 / S15-GOV-23 | mapped | PD-32 | S15-POL-29 | all |
| GD-24 / S15-GOV-24..26 | mapped | PD-32 | S15-POL-28/30 | WS1–WS3 |
| S15-GOV-01 purpose/firewall | mapped | PD-01 | S15-POL-01 | — |
| S15-GOV-01 evidence `§47` citation | N/A — carried Governance LOW; do not repair in Policy | — | — | — |
| S15-GOV-16 (cache/auth isolation) | mapped | PD-18 | S15-POL-18 | WS1/WS3 |
| Planning/Architecture already-frozen DTO/route semantics | already mechanically frozen via S14 Policy + S15 Arch/Gov | PD-10/12/13 | S15-POL-10/12/13 | WS2 |

---

## 44. Future IA Handoff

```text
POST_IA_WORKSTREAM_COUNT = 3
```

| WS | Name | Receives |
| --- | --- | --- |
| WS1 | Client + Auth | typed client; AuthTokenProvider; bootstrap/token lifecycle; API base; CORS/config wiring |
| WS2 | Read-Only Views | Premarket routes/views; latest/detail/lookups; Dashboard; HR; ADE; UX states; accessibility |
| WS3 | Hardening / Tests / CI | privacy/XSS tests; `frontend-quality-gate`; Playwright; security headers; logging proofs; hardening |

No fourth workstream. Policy does **not** authorize any workstream to start.

---

## 45. Deferred / Out-of-Scope

Deferred / out of scope at minimum:

- production OIDC selection
- production hosting / hostname
- deployment workflow
- DNS / CDN
- production analytics
- advanced CSP
- HSTS
- HR writes
- ADE invoke
- model execution
- broker execution
- new providers
- Feature Platform expansion
- new intelligence routes
- persistence changes
- new DTO authority
- new dependencies unless separately authorized
- custom CORS max-age
- literal cosmetic UX copy freeze

---

## 46. Validation / Review Contract

This docs-only candidate must pass:

- `make lint`
- `make typecheck`
- `make validate-secrets`
- `make test-api`

Frontend npm / Playwright validation for this docs-only candidate:
**NOT REQUIRED**.

Future independent review must verify: exact 2-path scope; README
index-only; Artifact ID/status; 32 semantic PD definitions; 30 semantic
AC definitions; all five freeze topics; traceability 0/0; authority
expansion defects; lifecycle contradictions; security/privacy/auth/CORS;
dependencies; CI/test contract; deployment/firewalls; validation
evidence; identity hashes.

---

## 47. Lifecycle / Exit Criteria

Literal candidate status remains **DRAFT**.

Artifact is not `APPROVED_EFFECTIVE` merely because it exists.

Required future lifecycle:

1. candidate implementation
2. independent review
3. controlled commit
4. push/PR preflight
5. push/PR
6. exact-head CI
7. human approval
8. merge preflight
9. controlled `MERGE_COMMIT`
10. issue auto-close
11. post-merge exact-main CI
12. finality review
13. then: `APPROVED_EFFECTIVE`

Only after Policy finality may IA discovery begin.

```text
SPRINT_15_POLICY_CONTRACT_GATE_STATE = DRAFT_CANDIDATE
POLICY_ARTIFACT_IMPLEMENTATION_AUTHORIZED = docs-only candidate gate only
SPRINT_15_IMPLEMENTATION_AUTHORIZED = NO
UI_IMPLEMENTATION_MAY_BEGIN = NO
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED/DEFERRED
```
