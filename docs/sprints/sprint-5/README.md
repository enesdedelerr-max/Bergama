# Sprint 5 — Strategy SDK Hardening

## Status

Complete.

Sprint 5 theme is **Strategy SDK Hardening**. Premarket Intelligence and Feature
Platform product work were deferred and are not part of the executed Sprint 5
scope.

The Strategy SDK root public API freeze (Issue **#51**) is merged on `main`
through PR **#52**:

```text
260ffbecb4113040705dc44a768ebf6e75f933ea
```

Governance closeout is recorded in [`CLOSEOUT.md`](CLOSEOUT.md). Release tag
creation for Sprint 5 remains a separate maintainer action after this closeout
is merged and the target commit is verified.

## Objective

Stabilize and document the author-facing Strategy SDK contracts and host-owned
runtime boundaries introduced in Sprint 4 (#406), without expanding the frozen
root public API, changing Sprint 4 runtime contracts, or enabling live
execution.

## Completed issue chain

| Issue | Deliverable | Pull request | Merge commit |
| --- | --- | --- | --- |
| #51 | Strategy SDK Public API Stabilization | #52 | `260ffbecb4113040705dc44a768ebf6e75f933ea` |

Issue document: [`issue-51-strategy-sdk-public-api-stabilization.md`](issue-51-strategy-sdk-public-api-stabilization.md).

## Deliverables

- Frozen root `bergama_strategy_sdk.__all__` surface (exact 39 symbols).
- Public / Experimental / Internal classification documentation.
- Compatibility policy for fingerprint-sensitive and version-axis changes.
- Contract tests locking the public API freeze and import boundary.
- Package version remains `0.1.0`.

## Safety guarantees

- No expansion of the frozen public API.
- No FeatureSnapshot / FeatureValue contract changes.
- No live execution enablement.
- No Broker, Portfolio, Risk, or OMS integration changes as part of Sprint 5.
- Host runtime types remain under `apps/api/app/strategy/sdk_runtime/`.

## Known exclusions

- Feature Platform productization (delivered later in Sprint 6).
- Premarket Intelligence.
- AI Decision Engine.
- Package or API version bumps.
- Runtime redesign or public export expansion beyond the freeze.

## Repository status

- Implementation baseline: `260ffbecb4113040705dc44a768ebf6e75f933ea`
- Final Sprint 5 implementation PR: #52
- Breaking changes: none
- Backward compatibility: maintained
- Release tag: prepared as `v0.5.0-sprint5`; **not created**

## Closeout evidence

See [`CLOSEOUT.md`](CLOSEOUT.md).

Release package: [`releases/sprint-5/`](../../../releases/sprint-5/).

Related roadmap: [`ROADMAP.md`](../../../ROADMAP.md).
