# TD-MARKET-DATA-002 — SourceReference provenance-key validation refinement

| Field | Value |
|-------|-------|
| ID | TD-MARKET-DATA-002 |
| Priority | Low |
| Status | Accepted |
| Component | `apps/api/app/market_data` |
| Location | `source.py` — `SourceReference.validate_extras` |
| Blocking | No for Issue #304A |

## Summary

`SourceReference.extras` rejects any key whose lowercased name **contains** the
substrings `password`, `secret`, `token`, or `api_key`.

That heuristic correctly blocks secret-shaped keys such as `api_token` and
`auth_token`. During #304A, the implementation avoided
`provider_request_id` and stored the Finnhub HTTP request id under the safer,
unambiguous key `http_request_id`.

## Investigation (#304A)

Verified against current #301 validation:

```text
"token" in "provider_request_id"  → False  (allowed today)
"token" in "http_request_id"      → False  (allowed today)
"token" in "api_token"            → True   (rejected)
"token" in "auth_token"           → True   (rejected)
```

Conclusion: `provider_request_id` is **not** a current false-positive rejection.
The #304A choice of `http_request_id` is a conservative provenance naming decision
to keep connector metadata clearly non-secret and avoid future collisions if the
substring filter is tightened. #301 contracts are intentionally unchanged in this
issue.

## Current (#304A)

Finnhub stores provider HTTP request IDs under:

```text
source.extras["http_request_id"]
```

## Target

Refine and document provenance-key conventions so that:

1. Secret-like keys remain rejected (`*token*`, `*api_key*`, `*secret*`, `*password*`),
2. Allowed provenance keys (`http_request_id`, optionally `provider_request_id`) are
   explicitly documented in #301 contract tests, and
3. Validation prefers bounded patterns / exact denylists over accidental future
   substring collisions with legitimate operational keys.

## Impact

- #304A consumers must read `http_request_id`, not assume `provider_request_id`.
- No security regression in #304A; API keys are still forbidden from extras.
- Non-blocking documentation / contract ergonomics debt.

## Decision

Accept for #304A. Keep `http_request_id`. Do not modify #301 in this PR.

## Exit criteria

1. Market-data contract docs/tests list approved provenance extras keys, and
2. Secret-substring rejection still fails closed for credential-like keys, and
3. Connectors agree on one request-id provenance key name (or an explicit alias map).

## Non-goals

- Changing EventEnvelope or FundamentalEvent/ReferenceDataEvent field sets in #304A
- Relaxing extras size/bounds limits
- Logging or storing API keys in extras
