# Premarket Command Center UI Governance v1

**Governance ID:** `premarket-command-center-ui.governance.v1`  
**Status:** DRAFT  
**Sprint:** 15  
**Gate:** Governance Gate  
**Issue:** [#162](https://github.com/enesdedelerr-max/Bergama/issues/162)  
**Theme:** Read-Only Premarket Command Center UI  
**Document class:** Sprint 15 Governance Gate authoritative artifact — not Policy Freeze, not Implementation Authorization  
**Planning Gate:** Issue [#158](https://github.com/enesdedelerr-max/Bergama/issues/158) / PR [#159](https://github.com/enesdedelerr-max/Bergama/pull/159) — `APPROVED_EFFECTIVE`  
**Architecture Gate:** Issue [#160](https://github.com/enesdedelerr-max/Bergama/issues/160) / PR [#161](https://github.com/enesdedelerr-max/Bergama/pull/161)  
**Architecture implementation commit:** `c6de7926c17ec5ad1762956bb051a74414671384`  
**Architecture merge:** `d50bd2f6579898f80b7f5faedc6a5b6999ad7363`  
**Architecture Artifact ID:** `premarket-command-center-ui.architecture.v1`  
**Architecture lifecycle:** `APPROVED_EFFECTIVE`  
**Governance Discovery:** COMPLETE  
**Governance Preflight:** PASS_WITH_NON_BLOCKING_FINDINGS  

```text
SPRINT_15_IMPLEMENTATION_AUTHORIZED = NO
UI_IMPLEMENTATION_MAY_BEGIN = NO
SPRINT_15_POLICY_CONTRACT_GATE_STATE = NOT_STARTED
SPRINT_15_IMPLEMENTATION_AUTHORIZATION_STATE = NOT_STARTED
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED/DEFERRED
TAG_RELEASE_DEPLOY_AUTHORIZED = NO
PUBLIC_WRITE_API_AUTHORIZED = NO
HUMAN_REVIEW_WRITE_UI_AUTHORIZED = NO
ADE_INVOCATION_AUTHORIZED = NO
NEW_FRONTEND_DEPENDENCY_AUTHORIZED = NO
FEATURE_PLATFORM_EXPANSION_AUTHORIZED = NO
LIVE_PROVIDER_EXPANSION_AUTHORIZED = NO
```

```text
THIS ARTIFACT GOVERNS FUTURE SPRINT 15 IMPLEMENTATION BOUNDARIES.
IT DOES NOT AUTHORIZE UI, AUTH, CORS, CI, DEPENDENCIES, APIS, MODELS,
OR BROKER EXECUTION.
```

---

## 1. Purpose

Freeze enforceable product-governance boundaries for browser access to the
read-only Sprint 14 intelligence-run product surface, including:

- authentication
- authorization
- CORS
- public/private data handling
- safe rendering
- error/freshness semantics
- cache/query isolation
- dependency governance
- frontend CI evidence
- deployment authority
- accessibility
- read-only / model / broker / provider firewalls

Governance defines **invariant authority and safety boundaries**.

Governance does **not** implement these mechanisms.

---

## 2. Governance / Policy / Implementation Separation

| Layer | Owns |
| --- | --- |
| Governance Gate (this document) | Enforceable authority and safety boundaries |
| Combined Policy / Contract Freeze | Exact mechanical contracts (auth state machine, UX strings, cache/retry numbers, CORS config schema, CI job names/triggers, header values, client type mapping) |
| Implementation Authorization | Exact files/modules/tests/CI/workstream execution permission |
| Implementation | Not authorized |

No later gate may weaken an approved Governance boundary without a separate
authority change.

Policy/Contract may tighten mechanics.

Policy/Contract MUST NOT weaken Governance.

IA MUST NOT exceed Policy, Governance, or Architecture.

---

## 3. Authority / Precedence

Precedence order:

1. Approved Planning authority (`APPROVED_EFFECTIVE`)
2. Approved Architecture authority (`APPROVED_EFFECTIVE`)
3. This Governance authority within its Governance domain
4. Future Policy/Contract mechanics
5. Future Implementation Authorization execution map

Governance MUST NOT contradict Architecture.

---

## 4. Non-Authorization Statement

This artifact does **NOT** authorize:

- UI implementation
- API client implementation
- auth implementation
- CORS implementation
- CI implementation
- dependency additions
- production OIDC
- production deployment
- new APIs
- new routes
- write APIs
- HR writes
- ADE invocation
- Feature Platform expansion
- provider expansion
- new persistence schema
- models
- broker execution

```text
SPRINT_15_POLICY_CONTRACT_GATE_STATE = NOT_STARTED
SPRINT_15_IMPLEMENTATION_AUTHORIZATION_STATE = NOT_STARTED
```

---

## 5. Scope

### IN

Browser authentication governance; Bearer token handling; token
exposure/redaction; bootstrap authority; scope enforcement; CORS; API
base/config; public/private DTO; HR read-only/XSS; ADE visibility-only;
Dashboard/display semantics; errors; freshness; cache/query isolation;
dependencies; frontend CI/evidence; security headers; CSRF assumptions;
observability; deployment/environment authority; accessibility baseline;
read-only mutation firewall; model firewall; broker firewall; Feature
Platform/provider/route/schema firewall; Policy/Contract handoff; IA
handoff.

### OUT

UI/API client/React implementation; auth/CORS/CI/test implementation;
dependency additions; production OIDC provider selection; production
deployment; new intelligence APIs/routes; write APIs; HR write workflows;
ADE invocation; Feature Platform expansion; new live providers; new
persistence schema; model participation; broker execution;
Policy/Contract implementation; IA implementation; tag/release/deploy.

### DEFERRED

Production OIDC provider selection; production UI hosting/deployment
architecture; advanced CSP nonce/hash; deployment-layer HSTS where
applicable; exact auth state machine; exact token-expiry UX; exact
cache/retry numbers; exact error UX strings; exact CORS configuration
schema; exact environment URL validation mechanics; exact client
DTO/type mapping; exact security header values; exact frontend CI job
names/triggers; exact implementation test matrix; exact source/module map.

---

## 6. Architecture Inheritance

Governance preserves Architecture freezes without redefining them:

| Freeze | Value |
| --- | --- |
| Frontend placement | existing `apps/platform-console` |
| Routes | `/premarket`, `/premarket/runs/[runId]` |
| Read surface | exact six Sprint 14 GET route families |
| Scope | `intelligence:runs:read` |
| Browser auth | mock console session ≠ API JWT |
| API auth | Bearer JWT |
| Token | in-memory |
| Bootstrap | `POST /api/v1/auth/token` when enabled |
| OIDC | `AuthTokenProvider` seam; provider deferred |
| CORS | env allowlist; no wildcard; GET/OPTIONS/POST; Authorization+Content-Type; credentials false; default deny |
| API base | `NEXT_PUBLIC_BERGAMA_API_BASE_URL`; fail closed; no mock product fallback |
| DTO | Sprint 14 public DTOs only |
| HR | `HR_READ_VISIBILITY = SHOULD`; write NO; XSS-safe |
| ADE | `ADE_READ_VISIBILITY = MUST`; invoke NO; private payload NO |
| Freshness | server metadata authoritative; no trading-safe SLA; no semantic recomputation |
| Dependencies | zero new FE runtime/dev and BE dependencies |
| Frontend CI | required during implementation |
| Deployment | production UI hosting deferred |
| Firewalls | no intelligence writes; no models; no broker; no FP/provider/new-route/schema expansion |

---

## 7. Governance Objective

Govern browser access to the existing Sprint 14 read-only intelligence-run
product surface so that authentication, authorization, CORS, data
minimization, safe rendering, error/freshness honesty, evidence, and
write/model/broker firewalls remain enforceable before any UI source work.

---

## 8. Browser Authentication

```text
CONSOLE_MOCK_SESSION_IS_API_AUTH = NO
API_PRODUCT_CALLS_REQUIRE_BEARER_JWT = YES
BROWSER_SECRETS_AUTHORIZED = NO
```

- Console mock/local session MUST NOT be treated as API authentication.
- Premarket product API calls MUST use Bearer JWT.
- No invented authentication mechanism is authorized.
- When no authorized token exists, UI MUST present an explicit
  unauthenticated state.

---

## 9. Token Handling / Exposure

```text
TOKEN_STORAGE = IN_MEMORY_ONLY
```

MUST NOT store tokens in:

- `localStorage`
- `sessionStorage`
- IndexedDB
- cookies
- BFF auth expansion for Sprint 15

MUST NOT place tokens in:

- URLs
- query parameters
- logs
- error payloads
- diagnostic dumps

On expiry: clear token from memory.

Reacquisition: only through authorized bootstrap when enabled; otherwise
explicit unauthenticated UI.

---

## 10. Bootstrap / OIDC

```text
BOOTSTRAP_ENDPOINT = POST /api/v1/auth/token
BOOTSTRAP_GRANT = bootstrap (only when enabled)
PRODUCTION_OIDC_PROVIDER_SELECTED = NO
OIDC_IMPLEMENTATION_DEFERRED = YES
```

- AuthTokenProvider seam MUST be retained.
- No browser secrets.
- Production bootstrap expansion is NOT authorized by this artifact.
- Production OIDC provider selection is DEFERRED.

---

## 11. Authorization / Scope

```text
PRODUCT_READ_SCOPE = intelligence:runs:read
ADDITIONAL_PRODUCT_SCOPE_REQUIRED = NO
```

MUST NOT substitute `api:read`, wildcard scope, privileged scope, or
automatic escalation.

Client-side UI state is NOT a security boundary.

Server authorization remains authoritative.

403 MUST NOT be replaced with mock or stale product data.

---

## 12. CORS

```text
CORS_ALLOWED_ORIGIN_STRATEGY = environment-driven explicit allowlist
CORS_WILDCARD_ORIGIN = FORBIDDEN
CORS_REFLECT_ORIGIN = FORBIDDEN
CORS_ALLOWED_METHODS = GET, OPTIONS, POST
CORS_ALLOWED_HEADERS = Authorization, Content-Type
CORS_ALLOW_CREDENTIALS = false
CORS_DEFAULT_DENY = YES
```

- POST is bootstrap-auth-only.
- Misconfiguration MUST fail closed.
- CORS logs MUST NOT include secrets.
- No additional method/header is authorized.

---

## 13. API Base / Config

```text
API_BASE_URL_CONFIG_KEY = NEXT_PUBLIC_BERGAMA_API_BASE_URL
API_BASE_URL_PUBLIC = YES
```

- Missing or malformed configuration MUST fail closed on Premarket pages.
- Unexpected production origins MUST NOT be invented or silently
  substituted.
- No embedded secrets.
- No implicit localhost production fallback.
- No mock product fallback.
- Exact validation mechanics: Policy/Contract.

---

## 14. Public / Private DTO Boundary

Only Sprint 14 authorized public read DTOs MAY cross into/render in UI.

MUST NOT render:

- ORM entities
- raw persistence rows
- provider payloads
- secrets
- stack traces
- model-private data
- unbounded raw/news payloads
- ADE `recorded_attestation_payload`
- any field excluded from Sprint 14 public contract

Governance creates no new DTO/API authority.

---

## 15. Human Review Governance

```text
HR_READ_VISIBILITY = SHOULD
HR_WRITE_UI_AUTHORIZED = NO
HR_RECORDED_PAYLOAD = UNTRUSTED
HR_XSS_SAFE_RENDERING_REQUIRED = YES
```

Rendering MUST be escaped/text-only.

MUST NOT use `dangerouslySetInnerHTML` for untrusted HR data.

MUST NOT execute HTML, Markdown (unless separately authorized and
sanitized), scripts, or event handlers.

MUST NOT provide submit, approve, reject, attest, or workflow transition
controls.

MUST NOT introduce a sanitizer dependency for Sprint 15.

---

## 16. ADE Governance

```text
ADE_READ_VISIBILITY = MUST
ADE_INVOKE_UI_AUTHORIZED = NO
ADE_PRIVATE_PAYLOAD_RENDER_ALLOWED = NO
```

Allowed: display already persisted public ADE result.

MUST NOT: invoke, regenerate, model retry, override, prompt controls,
model CTA, private payload, `recorded_attestation_payload`, trade
approval semantic, or broker action.

---

## 17. Dashboard / Display / PipelineOutcome

Allowed read/display surfaces:

- Dashboard snapshot
- latest-dashboard-capable
- run detail
- fingerprint lookup
- manual run-id lookup
- six PipelineOutcome values
- stage presence
- failure metadata
- thin provenance
- bindings/policy/version pins
- `as_of`, `persisted_at`, `age_seconds`

MUST NOT claim market-live authority, safe-to-trade, buy/sell/hold
reinterpretation, recommendation semantics, PipelineOutcome
reinterpretation, or query-time semantic recomputation.

---

## 18. Error Governance

Distinguishable product errors MUST be preserved:

| HTTP | Meaning |
| --- | --- |
| 400 | invalid identifier |
| 401 | authentication failure |
| 403 | insufficient scope |
| 404 | run not found |
| 404 | stage not present |
| 409 | unsupported snapshot contract |
| 500 | corrupt persisted snapshot |
| 503 | storage unavailable |

Rules:

- no mock substitution
- no stack-trace leakage
- no token leakage
- no private payload leakage
- 403: no silent retry/escalation
- 401: MAY expose explicit/reasonable reauthentication
- 503: retry MUST be bounded
- 500: fail closed

Exact UX mapping/strings: Policy/Contract.

---

## 19. Freshness Governance

Authoritative freshness metadata:

- `as_of`
- `persisted_at`
- `age_seconds`
- versions

Server metadata remains authoritative.

Relative formatting MAY be derived for display and remains
non-authoritative.

MUST NOT create client authoritative freshness, trading suitability
thresholds, safe-to-trade freshness, or hidden semantic recomputation.

---

## 20. Cache / Query Governance

TanStack Query MAY cache authorized public responses.

MUST preserve:

- auth isolation
- cache clearing on logout/token replacement
- no cross-user leakage
- no protected stale display after auth loss
- bounded retries
- AbortSignal/cancellation
- no retry storm

Forbidden by default:

- durable `localStorage` product cache
- persistent browser product/auth data

Exact `staleTime` / refetch / retry parameters: Policy/Contract.

---

## 21. Dependency Governance

```text
NEW_FRONTEND_RUNTIME_DEPENDENCIES = 0
NEW_FRONTEND_DEV_DEPENDENCIES = 0
NEW_BACKEND_DEPENDENCIES = 0
```

No exception is authorized by this artifact.

Any future exception requires separate dependency, CVE/security, license,
supply-chain, and version/lockfile review.

---

## 22. Frontend CI / Evidence

For future Premarket-touching implementation:

MUST provide exact-head frontend quality evidence covering:

1. `npm ci`
2. lint
3. typecheck
4. Vitest
5. Next production build

Premarket-touching UI PRs MUST include bounded Playwright smoke.

Backend CORS/config implementation MUST retain existing backend
`quality-gate` evidence.

Exact job names/triggers/test matrix: Policy/IA.

This Governance candidate MUST NOT edit CI.

---

## 23. Security / Headers / CSRF / XSS

**MUST:** XSS-safe rendering; no token/secret logging; CORS allowlist;
ADE private exclusion; lockfile integrity; sanitized errors.

**SHOULD:** nosniff; frame protection or equivalent.

**DEFERRED:** advanced CSP nonce/hash; deployment-layer HSTS where
appropriate.

```text
SPRINT_15_CSRF_STATUS = NOT_APPLICABLE
```

Basis: Bearer Authorization header; `credentials=false`; no auth cookies.

If cookie auth or `credentials=true` is later introduced, CSRF MUST be
reevaluated.

---

## 24. Content Safety

Backend-provided free text is untrusted.

Prefer React/framework escaping and text rendering.

MUST NOT execute HTML, Markdown, scripts, event handlers, or embedded
active content unless separately authorized and safely handled.

Applies at least to:

- HR `recorded_payload`
- failure detail
- provenance strings
- Dashboard strings
- ADE public strings

Avoid adding a sanitizer dependency.

---

## 25. Observability / Logging

```text
NEW_TELEMETRY_AUTHORIZED = NO
NEW_ANALYTICS_AUTHORIZED = NO
```

Permitted bounded existing logging MAY include request category,
status/error category, and timing.

MUST NOT log Bearer tokens, Authorization headers, secrets, private DTO
content, raw HR payloads, or ADE private data.

---

## 26. Deployment / Environment

Governance artifact implementation is docs-only.

Future Sprint 15 implementation MAY later be authorized for local, dev,
test, and CI under Implementation Authorization.

Production UI hosting/deployment expansion: DEFERRED.

Production OIDC: DEFERRED.

No deployment authority is granted here.

---

## 27. Accessibility

Require baseline:

- keyboard navigation
- visible focus
- semantic headings/landmarks
- labels
- table semantics
- loading/error status communication
- status not color-only
- basic contrast expectations

Evidence: tests/smoke.

No external compliance certification is required.

---

## 28. Read-Only Mutation Firewall

Only permitted mutation:

```text
POST /api/v1/auth/token
```

for authorized bootstrap authentication.

MUST NOT: intelligence-run writes; HR writes; ADE writes; ADE invocation;
trade/order creation; broker execution; portfolio/feature/provider
mutation; configuration/admin mutation.

No additional mutation route is required.

---

## 29. Model Firewall

```text
MODEL_PARTICIPATION = UNAUTHORIZED
```

Allowed: static display of persisted public ADE results.

MUST NOT: model invocation; runtime LLM summarization; prompt surface;
decision regeneration; model recommendation; model interpretation layer.

---

## 30. Broker Firewall

```text
BROKER_EXECUTION = DENIED/DEFERRED
```

Allowed: informational persisted trade-related fields, read-only.

MUST NOT: place order; connect broker; modify position; approve
execution; trigger execution; executable trade CTA.

---

## 31. Feature Platform / Provider / Route / Schema Firewall

MUST NOT authorize:

- new Feature Platform work
- new market provider
- new news provider
- new persistence schema
- new intelligence route
- new API contract

Use existing Sprint 14 product read surface only.

---

## 32. Governance Decision Matrix (GD-01..GD-24)

| ID | Decision | Rationale | Enforcement / Evidence Expectation | Authority Impact | Deferred / Future Boundary |
| --- | --- | --- | --- | --- | --- |
| GD-01 | Mock console session ≠ API JWT; Bearer required for Premarket product calls. | Prevents fake product authorization via shell session. | Review/tests prove mock session cannot authorize product reads; Bearer attached on product calls. | Architecture-preserving Governance freeze; no auth code now. | Production identity provider remains deferred. |
| GD-02 | In-memory token only; persistent browser/cookie/BFF storage forbidden for Sprint 15. | Reduces XSS persistence risk and cookie CSRF surface. | Code/review evidence of in-memory store; absence of localStorage/sessionStorage/IndexedDB/cookie auth. | No cookie/BFF auth expansion. | Cookie/BFF would require CSRF reevaluation and new authority. |
| GD-03 | Bootstrap token path only when enabled; no browser secrets; AuthTokenProvider seam retained; production OIDC deferred. | Uses existing backend capability without inventing production identity. | Bootstrap used only when enabled; provider seam present; no embedded secrets. | No OIDC provider selection. | Production OIDC provider selection deferred. |
| GD-04 | No token in URL/query, logs, error payloads, or diagnostic dumps. | Prevent token leakage. | Logging/error review; no Authorization header or token dumps. | Logging/observability constrained. | Broader telemetry remains unauthorized. |
| GD-05 | Exact scope `intelligence:runs:read`; no weakening/wildcard/`api:read`/client-side authority/escalation. | Least privilege; server remains authoritative. | Scope string exact; 403 not replaced with mock data. | No additional product scope. | Role binding display mechanics → Policy. |
| GD-06 | CORS env allowlist; default deny; no wildcard/reflect-origin; GET/OPTIONS/POST; Authorization+Content-Type; credentials false. | Secure browser→API boundary for GETs + bootstrap POST. | Config review; credentials false; no wildcard. | CORS design freeze; impl after IA. | Exact config schema → Policy. |
| GD-07 | `NEXT_PUBLIC_BERGAMA_API_BASE_URL` public/non-secret; fail closed; no mock product fallback. | Safe explicit origin configuration. | Missing/malformed config fails Premarket product pages closed. | No production host invention. | Exact validation mechanics → Policy. |
| GD-08 | Only Sprint 14 public DTOs; forbid private/internal data including ADE recorded attestation payload. | Preserve S14 privacy/minimization. | Tests/review prove private fields not rendered. | No new DTO/API authority. | New contracts require separate authority. |
| GD-09 | HR visibility SHOULD; write NO; untrusted payload XSS-safe escaped text. | Planning/Architecture SHOULD + security. | No write controls; escaped text; no dangerouslySetInnerHTML. | No HR write workflow. | HR write deferred. |
| GD-10 | ADE visibility MUST; invoke NO; no private payload rendering. | Planning/Architecture MUST + private exclusion. | ADE read UI without invoke/private payload. | No model/ADE invoke. | ADE invocation deferred. |
| GD-11 | No trading-safe/live-market authority claims; no PipelineOutcome trading reinterpretation. | Outcomes are execution/product states, not trade advice. | Copy/review forbids buy/sell/hold/safe/recommended semantics. | Display honesty freeze. | Non-persisted briefing prose deferred. |
| GD-12 | Product error classes distinguishable; security/corruption fail closed; no mock substitution. | Diagnosable, fail-closed UX. | Mapping for 400/401/403/404×2/409/500/503 preserved. | Exact strings → Policy. | Exact UX copy → Policy. |
| GD-13 | Freshness from server metadata only; derived formatting non-authoritative. | Point-in-time honesty. | Display uses as_of/persisted_at/age_seconds; no trading threshold. | No client freshness authority. | Relative format details → Policy/IA. |
| GD-14 | Query cache preserves auth isolation, bounded retry, auth-transition clearing; no unauthorized durable persistence. | Prevent stale protected data leakage. | Cache cleared on logout/token replace; no localStorage product cache by default. | Exact staleTime/retry → Policy. | Durable cache would need new authority. |
| GD-15 | Zero new FE runtime/dev and BE dependencies. | Existing stack sufficient; supply-chain risk control. | Manifests unchanged unless separately authorized exception. | No dependency install by Governance. | Exception requires separate review. |
| GD-16 | Premarket impl requires FE quality evidence; Premarket-touching UI PRs require Playwright smoke. | Deterministic + bounded E2E evidence. | Exact-head npm ci/lint/typecheck/Vitest/next build + smoke. | No CI edit in this artifact. | Exact job names/triggers → Policy/IA. |
| GD-17 | XSS/CORS/secret controls MUST; nosniff/frame SHOULD; advanced CSP DEFER; CSRF N/A under Bearer+credentials false+no cookies. | Bounded S15 security without inventing cookie auth. | CSRF reevaluation required if cookies/credentials=true introduced. | No cookie auth introduction. | Advanced CSP deferred. |
| GD-18 | No new telemetry/analytics; no tokens/headers/private/HR/ADE-private logging. | Fail-closed privacy. | Logging review; no sensitive fields. | No APM vendor addition. | New telemetry requires new authority. |
| GD-19 | Implementation authority local/dev/test/CI only; production UI hosting deferred. | Repo lacks formal prod UI hosting authority. | No K8s/cloud hosting invention in S15 Governance. | No deploy authority. | Production hosting deferred. |
| GD-20 | Accessibility baseline required. | Operational clarity without DS rewrite. | Keyboard/focus/semantics/labels/tables/status announcements/non-color-only. | Evidence via tests/smoke. | Full compliance certification not required. |
| GD-21 | Mutation firewall: only bootstrap POST `/api/v1/auth/token`; all other product mutations forbidden. | Read-only product surface. | Route/client review proves no other mutation. | No write UI/API. | Additional mutations require new authority. |
| GD-22 | MODEL_PARTICIPATION = UNAUTHORIZED; static public ADE display allowed. | Prevent runtime model authority expansion. | No model invoke/prompt/regenerate controls. | Model unauthorized. | Model participation remains unauthorized. |
| GD-23 | BROKER_EXECUTION = DENIED/DEFERRED; informational persisted trade fields read-only only. | No execution path from Premarket UI. | No order/broker/execution CTA. | Broker denied/deferred. | Broker remains deferred. |
| GD-24 | No FP/provider/new schema/new intelligence route expansion; preserve exactly three post-IA workstreams. | Bound S15 to existing S14 read surface. | WS1–WS3 only; no seventh route. | No FP/provider expansion. | Expansion requires separate Planning/Architecture. |

```text
GOVERNANCE_DECISION_COUNT = 24
GOVERNANCE_DECISION_UNIQUE_COUNT = 24
```

---

## 33. Acceptance Criteria Matrix (S15-GOV-01..26)

```text
GOVERNANCE_AC_COUNT = 26
GOVERNANCE_AC_UNIQUE_COUNT = 26
GOVERNANCE_AC_DUPLICATE_COUNT = 0
GOVERNANCE_AC_PASS_COUNT = 26
GOVERNANCE_AC_FAIL_COUNT = 0
GOVERNANCE_AC_AMBIGUOUS_COUNT = 0
```

| ID | Criterion | Result | Evidence |
| --- | --- | --- | --- |
| S15-GOV-01 | Governance purpose and authority firewall are explicit and do not authorize implementation. | PASS | §§1, 4, 47; firewall banners |
| S15-GOV-02 | Mock/local console session is explicitly separated from API Bearer authentication. | PASS | §8; GD-01 |
| S15-GOV-03 | Token storage is in-memory only and persistent browser/cookie/BFF storage is forbidden for Sprint 15. | PASS | §9; GD-02 |
| S15-GOV-04 | Bootstrap authority, browser-secret prohibition, AuthTokenProvider seam, and production OIDC deferment are frozen. | PASS | §10; GD-03 |
| S15-GOV-05 | Exact `intelligence:runs:read` scope and server-side authorization authority are preserved without weakening/escalation. | PASS | §11; GD-05 |
| S15-GOV-06 | CORS allowlist/default-deny/method/header/credentials constraints are frozen. | PASS | §12; GD-06 |
| S15-GOV-07 | API base configuration is public/non-secret and fail-closed with no mock fallback. | PASS | §13; GD-07 |
| S15-GOV-08 | Only authorized Sprint 14 public DTOs may be rendered and private fields remain excluded. | PASS | §14; GD-08 |
| S15-GOV-09 | HR visibility remains SHOULD/read-only; HR write actions are forbidden; untrusted payload rendering is XSS-safe. | PASS | §15; GD-09 |
| S15-GOV-10 | ADE visibility remains MUST/read-only; invocation and private payload rendering are forbidden. | PASS | §16; GD-10 |
| S15-GOV-11 | Trading-safe/live authority claims, outcome reinterpretation, and query-time semantic recomputation are forbidden. | PASS | §§17, 19; GD-11 |
| S15-GOV-12 | Frozen product error categories remain distinguishable with fail-closed security/corruption behavior and no mock substitution. | PASS | §18; GD-12 |
| S15-GOV-13 | Freshness uses authoritative server metadata only; derived display formatting remains non-authoritative. | PASS | §19; GD-13 |
| S15-GOV-14 | Query caching preserves auth isolation, bounded retries, auth transition clearing, and no unauthorized durable persistence. | PASS | §20; GD-14 |
| S15-GOV-15 | Zero-new-dependency authority is preserved and any future exception requires separate dependency/security/license review. | PASS | §21; GD-15 |
| S15-GOV-16 | Frontend exact-head quality evidence and bounded Playwright evidence are required for applicable Premarket implementation PRs. | PASS | §22; GD-16 |
| S15-GOV-17 | Security header/CSRF/XSS classifications remain consistent with Architecture and do not introduce cookie auth. | PASS | §§23–24; GD-17 |
| S15-GOV-18 | No new telemetry/analytics is authorized and sensitive logging is forbidden. | PASS | §25; GD-18 |
| S15-GOV-19 | Production hosting/deployment authority remains deferred. | PASS | §26; GD-19 |
| S15-GOV-20 | Accessibility baseline and evidence expectations are explicit. | PASS | §27; GD-20 |
| S15-GOV-21 | Read-only mutation firewall is explicit, with auth bootstrap POST as the sole permitted mutation. | PASS | §28; GD-21 |
| S15-GOV-22 | MODEL_PARTICIPATION remains UNAUTHORIZED. | PASS | §29; GD-22 |
| S15-GOV-23 | BROKER_EXECUTION remains DENIED/DEFERRED. | PASS | §30; GD-23 |
| S15-GOV-24 | Feature Platform/provider/persistence-schema/new-intelligence-route expansion remains unauthorized. | PASS | §31; GD-24 |
| S15-GOV-25 | Policy/Contract handoff is explicit and contains all unresolved mechanical contract details without weakening Governance. | PASS | §34 |
| S15-GOV-26 | Implementation Authorization handoff preserves exactly three post-IA workstreams and does not authorize implementation. | PASS | §35; `POST_IA_WORKSTREAM_COUNT = 3` |

---

## 34. Policy / Contract Handoff

Leave to later Policy / Contract Gate:

- exact auth state machine
- exact token expiry UX
- exact CORS environment/config schema
- exact error-to-UI mapping/strings
- exact cache/retry/refetch values
- exact API-base validation mechanics
- exact client DTO/type mapping
- exact security header values
- exact frontend CI job names/triggers/branch conditions
- exact implementation test matrix

Policy MAY tighten.

Policy MUST NOT weaken Governance.

---

## 35. Implementation Authorization Handoff

```text
POST_IA_WORKSTREAM_COUNT = 3
```

| WS | Title |
| --- | --- |
| WS1 | Intelligence Run API Client + Auth Integration |
| WS2 | Premarket Command Center Read-Only Views |
| WS3 | Hardening / Tests / CI |

IA later owns exact source paths, module map, backend CORS/config files,
client/hooks/views, tests, CI workflow changes, dependency confirmation,
execution order, issue boundaries, and branch/PR sequencing.

Governance does **not** authorize execution.

---

## 36. Evidence / Review Expectations

- Candidate requires repository validation (`make lint`, `make typecheck`,
  `make validate-secrets`, `make test-api`).
- Candidate requires independent review.
- Controlled commit only after review PASS or PASS WITH NON-BLOCKING.
- Push/PR require separate authorization.
- Merge requires exact-head CI and human approval.
- Post-merge exact-main CI required.
- Finality required before Policy eligibility.

---

## 37. Lifecycle / Done Condition

```text
DRAFT candidate
→ independent review
→ controlled commit
→ push/PR
→ exact-head CI/review
→ controlled MERGE_COMMIT
→ post-merge CI
→ finality verification
→ APPROVED_EFFECTIVE
→ Policy/Contract eligibility
```

Literal DRAFT MAY remain in the artifact after merge if lifecycle
APPROVED/EFFECTIVE is established externally by reviewed identity + merge
+ exact-main CI, consistent with governed precedent.

Even after APPROVED/EFFECTIVE:

```text
SPRINT_15_IMPLEMENTATION_AUTHORIZED = NO
UI_IMPLEMENTATION_MAY_BEGIN = NO
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED/DEFERRED
```

---

## 38. Authority Firewall (Restatement)

```text
SPRINT_15_IMPLEMENTATION_AUTHORIZED = NO
UI_IMPLEMENTATION_MAY_BEGIN = NO
SPRINT_15_POLICY_CONTRACT_GATE_STATE = NOT_STARTED
SPRINT_15_IMPLEMENTATION_AUTHORIZATION_STATE = NOT_STARTED
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED/DEFERRED
TAG_RELEASE_DEPLOY_AUTHORIZED = NO
PUBLIC_WRITE_API_AUTHORIZED = NO
HUMAN_REVIEW_WRITE_UI_AUTHORIZED = NO
ADE_INVOCATION_AUTHORIZED = NO
NEW_FRONTEND_DEPENDENCY_AUTHORIZED = NO
FEATURE_PLATFORM_EXPANSION_AUTHORIZED = NO
LIVE_PROVIDER_EXPANSION_AUTHORIZED = NO
```

---

## 39. Next Step

After candidate creation and validation, next step is:

**STRICT READ-ONLY independent Governance artifact review.**

Not commit.

Not push.

Not PR.

Not Policy.

Not implementation.
