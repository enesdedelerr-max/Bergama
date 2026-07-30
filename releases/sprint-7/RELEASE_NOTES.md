# Sprint 7 Release Notes

## Theme

Premarket Intelligence.

## Completed

### Planning (Issue #71)

- Approved Sprint 7 theme: Premarket Intelligence.
- Authorized sequenced foundation slices: Watchlist → Catalyst → Gap Scanner.
- Deferred Premarket Scoring, Morning Briefing, and Human Review Workflow.
- Kept UI out of scope.

### Watchlist Engine Foundation (Issue #72 / PR #73)

- Added Premarket Watchlist bounded context under
  `apps/api/app/premarket/watchlist/`.
- Deterministic watchlist generation from explicit candidates, rules, and
  configuration.
- Immutable watchlist contracts with ordering, inclusion reasons, and
  provenance fingerprints.
- Merge commit: `02bf9afe6e3a0a49c0e8758ac57d65e05a30e7d5`.

### Catalyst Ingestion and Normalization Foundation (Issue #74 / PR #75)

- Added Premarket Catalyst bounded context under
  `apps/api/app/premarket/catalyst/`.
- Deterministic normalization from offline Market Data news events.
- Immutable catalyst contracts with PIT fields, identity, and fingerprints.
- Merge commit: `05f38e841972793b4111fa1a165922dab81e925a`.

### Gap Scanner Foundation (Issue #76 / PR #77)

- Added Premarket Gap Scanner under `apps/api/app/premarket/gap/`.
- Consumes Watchlist universe and offline canonical `BarEvent`s only.
- Selection policy `two_bars_by_close_time_v1`.
- Gap formula:
  `(current_session_open - previous_session_close) / previous_session_close`
  with Decimal quantization `decimal_8dp_half_even`.
- Deterministic ordering: absolute gap descending, then `instrument_key`, then
  `gap_record_id`.
- Merge commit: `3b8358e728555bc17da87786b3a2f41792559433`.

## Safety and defaults

- Premarket disabled by default.
- No live execution enablement.
- Strategy SDK public `__all__` freeze preserved.
- Market Data contracts unchanged.
- Future-known observations fail closed.

## Validation evidence

```bash
make lint
make typecheck
make validate-secrets
make test-api-premarket-gap
make test-api-premarket
make test-api-feature-platform
make test-api-strategy-sdk
make test-api-strategy-engine
git diff --check
```

## Breaking Changes

None to the frozen Strategy SDK public API or Market Data contracts.

## Backward Compatibility

Maintained for Strategy SDK and Market Data surfaces consumed by Premarket
foundations.

## Known limitations

- Gap two-bar policy is not exchange-calendar or RTH-aware.
- No Catalyst enrichment of Gap records.
- No Premarket Scoring, Morning Briefing, Human Review, or UI.
- No Premarket persistence, HTTP APIs, or live provider workers in the
  authorized foundation slices.

## Risks

| Risk | Mitigation |
| --- | --- |
| Scope expands into scoring / briefing / UI | Explicit Issue #71 deferrals and closeout |
| Default-on Premarket | Settings default disabled; fail-closed |
| Premature Decision Engine start | Not authorized by Sprint 7 closeout |

## Rollback guidance

- Documentation-only closeout: revert the governance commit.
- Implementation rollback: use normal change control against PRs #73 / #75 /
  #77 and their merge commits.

## Explicit exclusions

- Premarket Scoring
- Morning Briefing
- Human Review Workflow
- UI
- Live providers / workers / Premarket persistence
- AI Decision Engine

## References

- Final implementation merge:
  `3b8358e728555bc17da87786b3a2f41792559433`
- Issues: #71, #72, #74, #76
- PRs:
  - https://github.com/enesdedelerr-max/Bergama/pull/73
  - https://github.com/enesdedelerr-max/Bergama/pull/75
  - https://github.com/enesdedelerr-max/Bergama/pull/77
