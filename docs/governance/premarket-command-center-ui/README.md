# Premarket Command Center UI Governance

**Governance package ID:** `premarket-command-center-ui.governance`  
**Status:** DRAFT / NOT APPROVED  
**Document class:** Governance index only  
**Sprint:** 15  
**Gate:** Governance  
**Theme:** Read-Only Premarket Command Center UI  
**Governance Gate issue:** [#162](https://github.com/enesdedelerr-max/Bergama/issues/162)

This package indexes the Sprint 15 Premarket Command Center UI Governance
Gate. It is an **index only**. Normative Governance rules live exclusively
in the authoritative Governance v1 artifact.

## Authoritative Governance artifact

| Field | Value |
| --- | --- |
| Path | [`premarket-command-center-ui-governance-v1.md`](premarket-command-center-ui-governance-v1.md) |
| Artifact ID | `premarket-command-center-ui.governance.v1` |
| Candidate status | DRAFT |

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

## Authority

```text
SPRINT_15_IMPLEMENTATION_AUTHORIZED = NO
UI_IMPLEMENTATION_MAY_BEGIN = NO
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED/DEFERRED
SPRINT_15_POLICY_CONTRACT_GATE_STATE = NOT_STARTED
SPRINT_15_IMPLEMENTATION_AUTHORIZATION_STATE = NOT_STARTED
```

This index does **not** authorize product implementation, UI code,
auth/CORS/CI implementation, dependency installation, Policy/Contract
Freeze, or Implementation Authorization.

## Lifecycle

```text
STATUS = DRAFT / NOT APPROVED
NEXT_PROCESS_STEP = Independent Governance artifact review
```

Do not treat this package as APPROVED / EFFECTIVE until Governance Gate
finality is established through the governed review, controlled merge, and
post-merge exact-main CI lifecycle.
