# Intelligence Pipeline Governance Decisions

**Governance ID:** `intelligence-pipeline.governance`
**Status:** DRAFT / NOT YET APPROVED
**Document class:** Governance index only
**Sprint:** 13
**Theme:** Intelligence Pipeline Integration
**Governance issue:** [#120](https://github.com/enesdedelerr-max/Bergama/issues/120)

This package indexes the Intelligence Pipeline Governance decisions for Sprint 13
Intelligence Pipeline Integration.

It points to the single consolidated Governance decision set:

| Decision set | Document | Status |
| --- | --- | --- |
| Governance v1 | [`intelligence-pipeline-governance-v1.md`](intelligence-pipeline-governance-v1.md) | DRAFT / NOT YET APPROVED |

**Authoritative decision body:** `intelligence-pipeline.governance.v1`

This README is an index only. It is not a second decision authority. Semantic
rules are owned exclusively by Governance v1.

## Package purpose

This package governs **composition only**.

- Stage bounded contexts retain semantic ownership.
- Existing stage governance remains authoritative.
- Governance does not authorize Policy or implementation.
- Governance does not authorize model participation.
- Governance does not authorize trading / execution.

```text
GOVERNANCE APPROVAL ≠ POLICY / IMPLEMENTATION AUTHORIZATION
GOVERNANCE APPROVAL ≠ IMPLEMENTATION
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED / DEFERRED
```

## Prerequisites

| Prerequisite | Process state |
| --- | --- |
| `sprint-13.planning-gate` | APPROVED / EFFECTIVE |
| `intelligence-pipeline.architecture.v1` | APPROVED / EFFECTIVE |

## Referenced existing governance (do not modify)

- Premarket Scoring Governance Decisions #1–#12 (`docs/governance/`)
- Morning Briefing Governance Decisions #1–#8 (`docs/governance/morning-briefing/`)
- Dashboard Governance Decisions #1–#8 (`docs/governance/dashboard/`)
- Human Review Governance Decisions #1–#8 (`docs/governance/human-review/`)
- AI Decision Engine Governance Decisions #1–#8 (`docs/governance/ai-decision-engine/`)
- Trading Foundations ownership (Sprint 4)
- Existing approved / frozen stage Policy Versions

## Explicit non-authorization

| Control | Value |
| --- | --- |
| Policy authorization | DENIED |
| Implementation authorization | DENIED |
| Implementation work | NOT STARTED |
| MODEL_PARTICIPATION | UNAUTHORIZED |
| BROKER_EXECUTION | DENIED / DEFERRED |
| SPRINT_13_PRODUCT_PERSISTENCE | NOT AUTHORIZED |
| SPRINT_13_HTTP_PRODUCT_API | NOT AUTHORIZED |
| UI_AUTHORIZED | NO |
| FEATURE_PLATFORM_CHANGE_REQUIRED | NO |
