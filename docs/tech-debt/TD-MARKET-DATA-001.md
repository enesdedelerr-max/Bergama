# TD-MARKET-DATA-001 — Calendar-aware daily bar window semantics

| Field | Value |
|-------|-------|
| ID | TD-MARKET-DATA-001 |
| Priority | Medium |
| Status | Accepted |
| Component | `apps/api/app/infrastructure/polygon` |
| Location | `mapper.py` — `DAILY_WINDOW_POLICY` |
| Blocking | No for Issue #302; Yes before session-sensitive research/backtesting |

## Summary

Polygon daily aggregate bars currently use the explicit, provider-compatible policy
`utc_fixed_24h_from_provider_t`: preserve provider timestamp `t` as `window_start` and
derive `window_end` as `t + multiplier` days of fixed UTC duration.

This is correct for deterministic connector tests and avoids inventing exchange-session
closes without a calendar. It is **not** NYSE/Nasdaq regular-trading-hours (RTH) close,
and it does not account for DST session boundaries or exchange holidays.

## Current

```text
utc_fixed_24h_from_provider_t
```

## Target

Exchange-calendar-aware session boundaries with DST and holiday support for US equity
venues (at minimum NYSE/Nasdaq), injected as explicit session context rather than guessed
from Polygon `t` alone.

## Impact

- Historical connector (#302) remains fail-closed and reviewable.
- Session-sensitive research, backtesting parity, and PIT analysis of daily bars may
  misalign with exchange close until this debt is resolved.
- Minute/hour bars already use exact duration arithmetic and are not covered by this debt.

## Decision

Accept for #302. Document the policy in connector metadata (`source.extras.window_policy`)
and sprint docs. Do not invent session close without a calendar.

## Exit criteria

1. An exchange calendar / session boundary service is available to the market-data plane, and
2. Daily-bar mapping can optionally consume venue + session calendar to set `window_end` /
   `close_time`, and
3. Regression tests cover DST transitions and holiday half-days for target venues.

## Non-goals

- Implementing #303 realtime WebSocket in the same change
- Silently treating fixed 24h windows as exchange closes
