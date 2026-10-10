# Premarket Command Center UI Governance

**Governance package ID:** `premarket-command-center-ui.governance`

**Status:** APPROVED / EFFECTIVE

**Document class:** Governance index only

**Sprint:** 15

**Gate:** Governance

**Theme:** Read-Only Premarket Command Center UI

**Governance Gate issue:** [#162](https://github.com/enesdedelerr-max/Bergama/issues/162)

**Governance PR:** [#163](https://github.com/enesdedelerr-max/Bergama/pull/163)

**Governance merge:** `abd51911af065a02d7bb4438cd1aaf3e694b4602`

This package indexes the Sprint 15 Premarket Command Center UI Governance
Gate. It is an **index only**. Normative Governance rules live exclusively
in the authoritative Governance v1 artifact.

## Authoritative Governance artifact

| Field | Value |
| --- | --- |
| Path | [`premarket-command-center-ui-governance-v1.md`](premarket-command-center-ui-governance-v1.md) |
| Artifact ID | `premarket-command-center-ui.governance.v1` |
| Lifecycle status | APPROVED / EFFECTIVE |

**Authoritative decision body:** `premarket-command-center-ui.governance.v1`

## Authoritative inputs

| Input | Reference |
| --- | --- |
| Planning Gate | Issue [#158](https://github.com/enesdedelerr-max/Bergama/issues/158) / PR [#159](https://github.com/enesdedelerr-max/Bergama/pull/159) — `APPROVED_EFFECTIVE` |
| Architecture Gate | Issue [#160](https://github.com/enesdedelerr-max/Bergama/issues/160) / PR [#161](https://github.com/enesdedelerr-max/Bergama/pull/161) |
| Architecture merge | `d50bd2f6579898f80b7f5faedc6a5b6999ad7363` |
| Architecture artifact | `docs/architecture/premarket-command-center-ui-architecture-v1.md` |
| Architecture Artifact ID | `premarket-command-center-ui.architecture.v1` |
| Architecture lifecycle | `APPROVED_EFFECTIVE` |
| Policy | `premarket-command-center-ui.policy.v1` — APPROVED / FROZEN (#164 / #165) |
| Implementation Authorization | APPROVED / EFFECTIVE (#166 / #167) |

## Current lifecycle

```text
GOVERNANCE = APPROVED_EFFECTIVE
POLICY = APPROVED_FROZEN
IA = APPROVED_EFFECTIVE
WS1 = MERGED_POST_MERGE_CI_GREEN_FINAL
WS2 = MERGED_POST_MERGE_CI_GREEN_FINAL
WS3 = MERGED_POST_MERGE_CI_GREEN_FINAL
SPRINT_15_IMPLEMENTATION_COMPLETE = YES
STATUS_SYNC = IN_PROGRESS / ISSUE_174
GOVERNANCE_CLOSEOUT = PENDING
SPRINT_15_COMPLETE = NO
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED/DEFERRED
PRODUCTION_DEPLOYMENT = NOT_AUTHORIZED
```

This index does **not** authorize new product implementation beyond the already
completed Sprint 15 workstreams, model participation, broker execution,
production deployment, Feature Platform expansion, or UI/UX redesign.

## Lifecycle

```text
STATUS = APPROVED / EFFECTIVE
NEXT_PROCESS_STEP = Complete Status Sync (#174), then separate Governance Closeout
```

See [`../../sprints/sprint-15/README.md`](../../sprints/sprint-15/README.md).
