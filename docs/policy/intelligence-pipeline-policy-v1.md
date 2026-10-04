# Intelligence Pipeline Policy Version v1

**Policy ID:** `intelligence-pipeline.policy.v1`
**Version:** v1
**Title:** Intelligence Pipeline Policy Version v1
**Status:** DRAFT / NOT YET APPROVED
**Document class:** Composition Policy Freeze
**Sprint:** 13
**Theme:** Intelligence Pipeline Integration
**Bounded context:** Intelligence Pipeline (application-layer composer)
**Architectural package path (not created by this document):** `apps/api/app/intelligence_pipeline/`
**Policy issue:** [#122](https://github.com/enesdedelerr-max/Bergama/issues/122)

```text
POLICY APPROVAL ≠ IMPLEMENTATION AUTHORIZATION
POLICY APPROVAL ≠ IMPLEMENTATION
IMPLEMENTATION_AUTHORIZATION = DENIED
IMPLEMENTATION_WORK_STARTED = NO
MODEL_PARTICIPATION = UNAUTHORIZED
BROKER_EXECUTION = DENIED / DEFERRED
```

---

## Prerequisites

| Prerequisite | Process state |
| --- | --- |
| `sprint-13.planning-gate` | APPROVED / EFFECTIVE |
| `intelligence-pipeline.architecture.v1` | APPROVED / EFFECTIVE |
| `intelligence-pipeline.governance.v1` | APPROVED / EFFECTIVE |

Referenced existing normative stage policies (do not reopen; do not copy bodies):

| Policy ID | Role |
| --- | --- |
| `premarket.scoring.policy.v1` | Score optional Gap/Catalyst input ownership; empty Watchlist / empty-score semantics |
| `morning-briefing.policy.v1` | Briefing empty-success / assembly semantics |
| `dashboard.policy.v1` | Dashboard required briefing / `as_of` semantics |
| `human-review.policy.v1` | Explicit attestation; HR authority boundary |
| `ai-decision-engine.policy.v1` | ADE accept / abstain; model UNAUTHORIZED |

Referenced governance foundations include Premarket Scoring, Morning Briefing,
Dashboard, Human Review, ADE, and Trading Foundations firewall ownership.
This Policy does not modify those artifacts.

---

## Status

| Field | Value |
| --- | --- |
| Policy status | DRAFT / NOT YET APPROVED |
| Policy approved | No |
| Approves Implementation Authorization | No |
| Approves Implementation | No |
| Implementation authorization | DENIED |
| Implementation work | NOT STARTED |
| Next mandatory gate after Policy approval | Implementation Authorization (separate gate) |

Until this Policy Version is APPROVED through repository process, Implementation
Authorization remains blocked for Sprint 13 pipeline composition.

---

## Purpose

Freeze the minimum deterministic composition semantics required by approved
Sprint 13 Planning, Architecture, and Governance before Implementation
Authorization may be considered.

This Policy Version is a **thin Composition Policy Freeze**. It owns only
composition semantics not already owned by stage Governance or stage Policy.

---

## Authority Statement

This Policy owns only:

- Gap / Catalyst empty-success continuation and Score input mapping at the
  composition boundary
- thin composition continuation matrix
- composition-level terminal / outcome semantic families
- run-level stage Policy / config binding
- thin composition replay equality scope

This Policy does **not** own:

- stage algorithms
- stage scoring semantics
- Gap business meaning
- Catalyst business meaning
- Watchlist selection semantics
- Briefing semantics
- Dashboard presentation semantics
- Human Review authority
- ADE authority
- Strategy
- Risk
- Portfolio
- Order Intent
- OMS
- Broker
- execution
- persistence
- HTTP
- UI
- Feature Platform

Existing stage Governance and Policy remain authoritative for stage semantics.
Pipeline topology is not redefined by this Policy; Architecture and Governance
remain the topology authorities.

---

## Explicit Exclusions

This Policy Version does not authorize or define:

- Implementation Authorization or Implementation
- runtime package creation under `apps/api/app/intelligence_pipeline/`
- APIs, endpoints, schemas, DTOs, JSON, protobuf, events, queues, or topics
- database tables, migrations, storage, caches, or retention mechanisms
- UI, dashboards, approval screens, notifications, or workflow engines
- numeric Pipeline freshness / staleness thresholds
- Pipeline-level business acceptance thresholds
- global Pipeline score / confidence / ranking cutoffs
- new Gap / Catalyst / Score / Briefing / Dashboard business semantics
- new Human Review Policy semantics
- new ADE Policy semantics
- stage reason-code ownership
- exact Python exception class names
- Feature Store / Feature Platform changes
- model, provider, prompt, SDK, or hosting participation
- Broker Execution, OMS mutation, Order Intent creation, or live trading
- Sprint 14 productization or Sprint 15 UI

```text
PIPELINE_NUMERIC_FRESHNESS_THRESHOLD_REQUIRED = NO
PIPELINE_LEVEL_ACCEPTANCE_THRESHOLD_REQUIRED = NO
PIPELINE_TEMPORAL_POLICY_REQUIRED = NO
PIPELINE_HR_POLICY_REQUIRED = NO
PIPELINE_ADE_POLICY_REQUIRED = NO
```

---

## PD-13-01 — Gap / Catalyst Empty-Success Continuation and Score Input Mapping

### Topology vs Score optionality

Pipeline topology (Architecture / Governance) requires execution of Gap and
Catalyst as mandatory composition stages:

```text
Watchlist → Gap + Catalyst → Score → Morning Briefing → Dashboard
→ optional Human Review → optional ADE
```

Premarket Scoring Policy `premarket.scoring.policy.v1` authorizes Gap and
Catalyst collections as optional **Score inputs**. That Score-boundary
optionality does **not** authorize the Pipeline to skip Gap or Catalyst stages.

| Layer | Semantic |
| --- | --- |
| Pipeline topology | Gap stage mandatory; Catalyst stage mandatory |
| Score inputs | Gap / Catalyst collections authorized optional under Scoring Policy |

### Empty successful stage outputs

A successful Gap stage returning an empty `GapCollection` is:

- VALID SUCCESS
- not failure
- not missing stage
- not “not executed”

A successful Catalyst stage returning an empty `CatalystCollection` is:

- VALID SUCCESS
- not failure
- not missing stage
- not “not executed”

Both continue to Score.

### Public output mapping (as-is)

The Pipeline MUST pass successful public stage outputs downstream as their
actual public outputs.

Specifically:

1. An empty successful `GapCollection` MUST NOT be silently rewritten to
   `gaps=None` merely because Scoring Policy permits optional Gap inputs.
2. An empty successful `CatalystCollection` MUST NOT be silently rewritten to
   `catalysts=None` merely because Scoring Policy permits optional Catalyst
   inputs.

Rationale: `None` and an executed-empty public result have different provenance
and execution meaning. This Policy freezes composition mapping only. It does
not redefine Scoring Policy feature-contribution semantics for absent versus
empty supplied collections.

Watchlist empty-success remains valid and may continue according to existing
Scoring Policy. Score and Briefing valid empty-success semantics remain
stage-owned and are not redefined here.

---

## PD-13-02 — Thin Composition Continuation Matrix

This Policy freezes only composition-level continuation. It does not invent
recovery, retry, fallback, or partial-success business semantics beyond approved
authorities.

| Situation | Composition outcome |
| --- | --- |
| Invalid Pipeline admission | STOP / no stage execution |
| Watchlist stage failure | STOP |
| Watchlist empty success | CONTINUE according to existing stage semantics |
| Gap failure | STOP |
| Gap empty success | CONTINUE with actual Gap public output |
| Catalyst failure | STOP |
| Catalyst empty success | CONTINUE with actual Catalyst public output |
| Score failure | STOP |
| Score valid empty success | CONTINUE according to existing Scoring Policy |
| Briefing failure | STOP |
| Briefing valid empty success | CONTINUE according to existing Morning Briefing Policy |
| Dashboard failure | STOP |
| Dashboard success + HR not requested | VALID TERMINAL COMPLETION |
| Dashboard success + HR requested | Continue only through approved HR public contract |
| Invalid / missing required HR attestation | Must not become synthetic HR success or ADE eligibility |
| ADE not requested | Terminal at prior authorized stage |
| ADE requested without valid authorized HR public output | ADE MUST NOT be invoked |
| ADE valid invocation | Terminal semantics remain ADE-owned |
| ADE accept | Valid terminal outcome |
| ADE abstain | Valid terminal outcome |

Required stage failure stops composition unless an already-approved upstream
authority explicitly defines another outcome.

Human Review not requested may terminate successfully at Dashboard according to
approved Pipeline Governance. Human Review invocation remains governed by Human
Review Governance / `human-review.policy.v1`. ADE invocation remains governed by
ADE Governance / `ai-decision-engine.policy.v1`. Missing or invalid authorized HR
must not be converted into synthetic ADE eligibility. ADE accept / abstain
semantics remain ADE-owned.

---

## PD-13-03 — Composition Terminal / Outcome Semantic Families

Pipeline Policy freezes only composition-level terminal / outcome semantic
families. It does not own stage reason codes and does not freeze exact Python
exception class names.

### Pipeline-owned outcome families

| Family ID | Meaning |
| --- | --- |
| `pipeline.outcome.admission_rejected` | Run rejected at Pipeline admission; no governed stage execution |
| `pipeline.outcome.required_stage_failed` | A required composition stage failed; composition stops |
| `pipeline.outcome.completed_dashboard` | Successful terminal completion at Dashboard (HR not requested) |
| `pipeline.outcome.completed_human_review` | Successful terminal completion after authorized Human Review |
| `pipeline.outcome.completed_ade_accept` | Successful terminal completion after ADE acceptance |
| `pipeline.outcome.completed_ade_abstain` | Successful terminal completion after ADE abstention |

These family identifiers are composition classification labels only. They do not
imply Broker / OMS / Order Intent / execution authority. They do not redefine
upstream stage reason semantics.

### Stage-owned reasons

Upstream stage reason codes / reasons / abstention semantics remain stage-owned
and are preserved by reference / provenance where applicable:

- Scoring reasons remain Scoring-owned
- Human Review rejection / attestation semantics remain HR-owned
- ADE abstention reasons remain ADE-owned
- other stage failure / absence reasons remain stage-owned

The Pipeline MUST NOT rewrite upstream reasons into new business meaning.

---

## PD-13-04 — Run-Level Stage Policy / Config Binding

At Pipeline admission, the governed stage Policy / config references used by the
run are selected and pinned.

Requirements:

1. The run MUST NOT silently switch Policy / config versions mid-execution.
2. The binding remains stable through Watchlist, Gap, Catalyst, Score, Morning
   Briefing, Dashboard, optional Human Review, and optional ADE where the stage
   actually consumes a governed Policy / config reference.
3. Replay MUST preserve the original governed binding.

This Policy does not define implementation storage, database schemas, hash
algorithms, dependency-injection mechanics, or a global config service.

---

## PD-13-05 — Thin Composition Replay Equality Scope

A governed composition replay MUST preserve:

- original run-level UTC `as_of`
- canonical admitted evidence
- stage Policy / config bindings pinned at admission
- explicit human input where applicable
- stage public-output semantics
- terminal composition outcome family

Replay MUST NOT:

- advance wall-clock time
- live-refetch providers
- silently adopt newer Policy / config versions
- fabricate missing evidence
- fabricate human approval
- invoke model authority
- invoke broker / execution authority

This Policy freezes only the minimum replay equality semantics necessary for
composition determinism. It does not freeze database persistence, durable replay
storage, serialization format, hash implementation, exact Python equality
implementation, or a public replay API. Those remain Implementation /
Implementation Authorization / later productization concerns where separately
authorized.

Temporal obligations remain Governance-owned:

- one UTC run-level `as_of`
- PIT preservation
- `known_at <= as_of` where applicable
- no future-data leakage
- original `as_of` on replay

This Policy does not add a new temporal Policy family and does not introduce
numeric freshness thresholds.

---

## Business Threshold Boundary

No Pipeline-level numeric acceptance threshold exists in Policy v1.

No Pipeline global confidence score.

No Pipeline ranking cutoff.

No Pipeline freshness / staleness threshold.

Stage-owned business thresholds remain stage-owned.

---

## Human Review / ADE Boundary

This Policy references and does not duplicate:

- `human-review.policy.v1`
- `ai-decision-engine.policy.v1`

Pipeline Policy freezes composition invocation consequences only (see PD-13-02
and PD-13-03). It does not redefine attestation meaning, human authority, ADE
acceptance, ADE abstention reason semantics, or model participation.

| Control | Value |
| --- | --- |
| HUMAN_AUTHORITY_TRANSFER | NO |
| AUTOMATIC_HUMAN_APPROVAL | NO |
| MODEL_PARTICIPATION | UNAUTHORIZED |
| BROKER_EXECUTION | DENIED / DEFERRED |

---

## Security / Authority Controls

Fail-closed composition behavior is preserved against:

- future-data leakage
- timestamp spoofing
- provenance spoofing
- synthetic stage output
- synthetic human approval
- HR bypass
- ADE bypass
- model authority expansion
- broker / execution authority expansion

No new security platform is authorized by this Policy.

---

## Authority Firewalls

```text
MODEL_PARTICIPATION = UNAUTHORIZED
HUMAN_AUTHORITY_TRANSFER = NO
AUTOMATIC_HUMAN_APPROVAL = NO
BROKER_EXECUTION = DENIED / DEFERRED
LIVE_TRADING = UNAUTHORIZED
ORDER_INTENT_CREATION = UNAUTHORIZED
OMS_MUTATION = UNAUTHORIZED
SPRINT_13_PRODUCT_PERSISTENCE = NOT AUTHORIZED
SPRINT_13_HTTP_PRODUCT_API = NOT AUTHORIZED
FEATURE_PLATFORM_CHANGE_REQUIRED = NO
UI_AUTHORIZED = NO
SPRINT_14_AUTHORIZED = NO
SPRINT_15_UI_AUTHORIZED = NO
IMPLEMENTATION_AUTHORIZATION = DENIED
IMPLEMENTATION_WORK_STARTED = NO
INTELLIGENCE_PIPELINE_RUNTIME_PACKAGE_CREATED = NO
```

---

## Approval Effect

This document remains **DRAFT / NOT YET APPROVED** until repository Policy
approval through controlled review and merge.

If and only if this Policy Version becomes APPROVED / EFFECTIVE:

1. The minimum composition Policy Freeze defined here becomes normative.
2. Implementation Authorization may be considered as a separate gate.
3. Implementation remains DENIED until Implementation Authorization is APPROVED.
4. Model participation remains UNAUTHORIZED.
5. Broker / execution remains DENIED / DEFERRED.
6. Sprint 13 product persistence / HTTP product API / UI remain not authorized.

Policy approval alone does not create runtime code, does not create
`apps/api/app/intelligence_pipeline/`, and does not authorize Implementation.
