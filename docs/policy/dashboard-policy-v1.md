# Dashboard Policy Version v1 Specification

## Version Metadata

| Field | Value |
|-------|-------|
| Policy Version ID | `dashboard.policy.v1` |
| Policy Version Label | Dashboard Policy Version v1 |
| Status | APPROVED |
| Document class | Policy Version / Policy Freeze only |
| Bounded context | Dashboard |
| Governance Dependency | Dashboard Governance Decisions #1–#8 (immutable) |
| Upstream Morning Briefing Policy Dependency | `morning-briefing.policy.v1` (immutable) |
| Upstream Premarket Scoring Policy Dependency | `premarket.scoring.policy.v1` (immutable; via Morning Briefing public output only) |
| Architecture Dependency | Dashboard Architecture v1 (immutable) |
| Planning Dependency | Sprint 10 Planning Gate (immutable) |
| Ordering Preservation Policy ID | `preserve_morning_briefing_order.v1` |
| Presentation Selection Policy ID | `include_all_morning_briefing_records.v1` |
| Identity Specification ID | `dashboard.identity.v1` |
| Provenance Specification ID | `dashboard.provenance.v1` |
| Digest Method ID | `canonical_payload_sha256_v1` |
| Output Completeness Policy ID | `output_completeness.exactly_one_complete_output.v1` |
| Replay Equality Policy ID | `replay_equality.structural_complete.v1` |
| Canonical UTC Convention ID | `utc_aware_instant_v1` |
| Canonical Decimal Convention ID | `canonical_decimal_str_v1` |
| Score Domain | Finite `Decimal` in closed interval `[0, 1]` as received through Morning Briefing public output |

## Purpose

This specification defines the complete concrete deterministic behavior of Dashboard Foundation under Policy Version `dashboard.policy.v1`.

Governance defines what Dashboard is permitted to do.
`dashboard.policy.v1` defines exactly how the authorized Dashboard Foundation behavior shall operate.

This Policy Version is subordinate to:

- Sprint 10 Planning Gate
- Dashboard Architecture v1
- Dashboard Governance Decisions #1–#8
- Premarket Scoring Governance Decisions #1–#12
- Premarket Scoring Policy Version `premarket.scoring.policy.v1`
- Morning Briefing Governance Decisions #1–#8
- Morning Briefing Policy Version `morning-briefing.policy.v1`

This document does not modify, reinterpret, expand, or supersede any approved repository artifact.
Policy Freeze is subordinate to Governance.
`dashboard.policy.v1` shall never redesign Architecture, expand authorized inputs, authorize implementation outside Dashboard Implementation Authorization v1, or modify upstream semantics, ordering, identity, provenance, or ownership.

## Governance Dependencies

This Policy Version SHALL comply with all of the following immutable Dashboard Governance Decisions:

| Decision | Title | Binding effect on v1 |
|----------|-------|----------------------|
| #1 | Semantic Boundary | Dashboard is deterministic, read-only, presentation-oriented operational visibility only; no semantic ownership of upstream artifacts |
| #2 | Authorized Inputs | Only repository-authorized public inputs may be consumed; Morning Briefing required; direct Premarket Scoring unauthorized |
| #3 | Presentation Authority | Presentation is read-only and presentation-only; no review, decision, or execution authority |
| #4 | Replay Policy | Replay depends only on authorized inputs, UTC `as_of`, Policy Version, and configuration |
| #5 | Identity Policy | Dashboard identity is distinct, deterministic, and non-substitutable for upstream identities |
| #6 | Provenance Policy | Upstream provenance preserved; Dashboard provenance distinct and deterministic; no reconstruction authority |
| #7 | Output Policy | Outputs remain presentation-only; never become repository authority |
| #8 | Ordering & Presentation Policy | Upstream ordering preserved exactly; no independent ranking; selection does not imply nonexistence |

This Policy Version SHALL also preserve:

- Morning Briefing semantic meaning under Morning Briefing Governance Decision #1
- Premarket Score semantic meaning under Premarket Scoring Governance Decision #1
- all Morning Briefing Policy Version `morning-briefing.policy.v1` public-output invariants visible to consumers

## Authorized Inputs

v1 SHALL consume exactly:

| Input | Classification | v1 consumption rule |
|-------|----------------|---------------------|
| Morning Briefing public output | Required | Exactly one Morning Briefing output produced under `morning-briefing.policy.v1` |
| Morning Briefing identity references | Required | Output MUST carry `briefing_id` per `morning-briefing.identity.v1` |
| Morning Briefing provenance references | Required | Output MUST carry repository-governed Morning Briefing provenance per `morning-briefing.provenance.v1` |
| Explicit UTC `as_of` | Required | Single PIT context for the Dashboard evaluation |
| Dashboard configuration | Required | MUST identify `dashboard.policy.v1` and all v1 subordinate specification IDs |
| Policy Version identity | Required | MUST equal `dashboard.policy.v1` |

v1 SHALL NOT consume:

- Premarket Scoring public outputs as direct Dashboard inputs
- implementation-private Morning Briefing representations
- implementation-private Premarket Scoring representations
- raw Market Data, Feature Platform internals, Feature Store internals, Strategy SDK internals
- broker, portfolio, or live execution state
- Human Review, AI Decision Engine, UI, rendering, product-surface, or notification state
- any other information not listed as an Authorized Input under this Policy Version

Direct Premarket Scoring public-output consumption remains unauthorized under Dashboard Governance Decision #2 and this Policy Version.

## Presentation Pipeline

v1 SHALL execute the following deterministic sequence exactly once per evaluation, in this immutable order:

```text
1. Input Validation
2. Policy Version Binding
3. Configuration Binding
4. PIT Validation
5. Authorized Input Admission
6. Morning Briefing Reference Preservation
7. Ordering Preservation
8. Dashboard Presentation Assembly
9. Dashboard Identity Generation
10. Dashboard Provenance Generation
11. Output Construction
12. Post-Validation
13. Emission
```

Stage responsibilities:

| Stage | Responsibility |
|-------|----------------|
| Input Validation | Admit only Policy-legal requests; reject unauthorized or malformed inputs |
| Policy Version Binding | Bind evaluation to exactly `dashboard.policy.v1` |
| Configuration Binding | Bind and freeze validated Dashboard configuration for the evaluation |
| PIT Validation | Enforce single explicit UTC `as_of` equality with Morning Briefing `as_of` by instant |
| Authorized Input Admission | Admit only Governance Decision #2 authorized public inputs |
| Morning Briefing Reference Preservation | Capture Morning Briefing public-output references read-only |
| Ordering Preservation | Preserve Morning Briefing record order exactly under `preserve_morning_briefing_order.v1` |
| Dashboard Presentation Assembly | Form deterministic presentation records under `include_all_morning_briefing_records.v1` |
| Dashboard Identity Generation | Produce Dashboard identity under `dashboard.identity.v1` |
| Dashboard Provenance Generation | Produce Dashboard provenance under `dashboard.provenance.v1` |
| Output Construction | Materialize the immutable Dashboard presentation output |
| Post-Validation | Enforce all post-conditions before emission |
| Emission | Return exactly one complete validated output or fail closed |

Required pipeline rules:

- every stage executes exactly once
- stages execute only in the frozen order
- no stage may be skipped, repeated, or reordered
- each stage consumes only the validated result of the previous stage
- no silent repair
- no partial success
- successful evaluation emits exactly one complete Dashboard output

No stage MAY regenerate Morning Briefing outputs, regenerate Premarket Scores, reorder upstream records, invent evidence, or silently repair violations.

### Pipeline Isolation

Each Presentation Pipeline stage SHALL:

- consume only approved stage input from the immediately preceding validated stage output
- produce immutable stage output
- not bypass another stage
- not invoke a later stage early
- not mutate prior stage output
- not inspect implementation-private upstream state

Stage execution order is immutable for `dashboard.policy.v1`.

Pipeline Isolation violation SHALL fail closed.

## Configuration

### Default Configuration

| Setting | Frozen v1 value |
|---------|-----------------|
| `policy_version_id` | `dashboard.policy.v1` |
| `ordering_preservation_policy_id` | `preserve_morning_briefing_order.v1` |
| `identity_specification_id` | `dashboard.identity.v1` |
| `provenance_specification_id` | `dashboard.provenance.v1` |
| `digest_method_id` | `canonical_payload_sha256_v1` |
| `presentation_selection_policy_id` | `include_all_morning_briefing_records.v1` |

This is the complete v1 Dashboard configuration.
v1 SHALL NOT define filtering, sorting, pagination, UI, layout, rendering, or transport settings.

### Configuration Stability

Configuration bound during Configuration Binding SHALL remain immutable throughout the evaluation.

Configuration SHALL be:

- immutable after Policy and Configuration Binding
- deterministic
- repository-approved
- included in configuration fingerprinting
- independent of environment discovery

Configuration SHALL NOT be replaced, reloaded, or mutated during execution.
Runtime discovery of alternate configuration is forbidden.
Configuration Stability violation SHALL fail closed.

Implementation SHALL consume these defaults exactly when this Policy Version is selected.
Implementation SHALL NOT ambient-default a different Policy Version or subordinate specification ID.

## Presentation Selection

### Presentation Selection Policy `include_all_morning_briefing_records.v1`

For Policy Version v1, presentation selection SHALL:

- include every ordered Morning Briefing record received in the authorized Morning Briefing public output
- preserve the exact upstream sequence
- not filter
- not sort
- not paginate
- not truncate
- not deduplicate
- not aggregate
- not infer missing records

Empty Morning Briefing record sets (`N = 0`) SHALL yield empty Dashboard presentation records with valid evaluation-level identity and provenance and SHALL NOT fabricate instruments or records.

Absence of an authorized artifact from a Dashboard output SHALL NOT be interpreted as absence of repository existence or semantic validity under Governance.
Under this Policy Version, selection includes all received Morning Briefing records; omission is therefore limited to the empty-input case and does not authorize selective dropping.

This rule is presentation-neutral and does not define UI behavior.

## Ordering

### Ordering Preservation Policy `preserve_morning_briefing_order.v1`

Dashboard SHALL preserve Morning Briefing record order exactly as received from the Morning Briefing public output.

Normative rules:

1. Zero-based Dashboard sequence index `i` SHALL correspond to Morning Briefing record position `i`.
2. Implementation SHALL NOT apply independent ranking.
3. Implementation SHALL NOT invent tie-breaks.
4. Implementation SHALL NOT reorder records.
5. Position SHALL NOT imply endorsement, prioritization, recommendation, or preference beyond upstream ordering authority.
6. Ordering preservation is mandatory for non-empty and empty collections alike.

## Contracts

Contracts below are conceptual Policy contracts.
They do not define transport schemas, JSON, HTTP fields, database columns, or UI models.

### Dashboard Evaluation Request

A Dashboard Evaluation Request SHALL contain exactly:

| Element | Rule |
|---------|------|
| Morning Briefing public output | Exactly one authorized Morning Briefing output under `morning-briefing.policy.v1` |
| Explicit UTC `as_of` | Timezone-aware; normalized to UTC; equal by instant to Morning Briefing output `as_of` |
| Dashboard configuration | Validated v1 configuration as defined above |
| Policy Version identity | Exactly `dashboard.policy.v1` |

Unexpected extra contract fields SHALL fail closed.
Unauthorized fields SHALL fail closed.

### Dashboard Presentation Record

Each Dashboard Presentation Record SHALL preserve at minimum:

| Element | Rule |
|---------|------|
| Sequence index | Zero-based index equal to Morning Briefing record position |
| Morning Briefing record identity reference | Exact upstream `score_record_id` as exposed on the Morning Briefing record |
| `instrument_key` | Exact value as received |
| `local_symbol` | Exact value as received, including null |
| Score reference | Exact finite `Decimal` score as exposed through Morning Briefing public output |
| Component snapshot references | Exact values as exposed, including null absences |
| Morning Briefing `policy_version_id` | Must equal `morning-briefing.policy.v1` |
| Morning Briefing record `as_of` / scoring `as_of` as exposed | Must equal evaluation `as_of` by instant |
| Upstream identity reference | Exact Morning Briefing record identity linkage as received |
| Upstream provenance reference | Exact Morning Briefing / score provenance linkage as exposed on the public record path |

Dashboard Presentation Records SHALL remain read-only with respect to upstream meaning.

### Dashboard Presentation Output

A Dashboard Presentation Output SHALL contain at minimum:

| Element | Rule |
|---------|------|
| `dashboard_output_id` | Deterministic identity per `dashboard.identity.v1` |
| `policy_version_id` | `dashboard.policy.v1` |
| `ordering_preservation_policy_id` | `preserve_morning_briefing_order.v1` |
| `presentation_selection_policy_id` | `include_all_morning_briefing_records.v1` |
| Explicit UTC `as_of` | Evaluation `as_of` |
| Ordered immutable presentation records | Zero or more records under Ordering and Presentation Selection policies |
| Dashboard provenance | Per `dashboard.provenance.v1` |

## Identity

### Identity Specification `dashboard.identity.v1`

This subordinate specification defines concrete Dashboard identity construction for Policy Version v1 outputs.

Governance Decision #5 remains algorithm-agnostic at Governance fidelity. Identity algorithm details live only here.

**Identity outcome:** `dashboard_output_id` is a deterministic 64-character lowercase hex digest.

**Digest method for v1:** `canonical_payload_sha256_v1`, consistent with existing repository deterministic identity conventions.

**Canonical identity payload MUST include exactly:**

| Payload element | Rule |
|-----------------|------|
| Identity Specification ID | `dashboard.identity.v1` |
| Dashboard Policy Version ID | `dashboard.policy.v1` |
| Ordering Preservation Policy ID | `preserve_morning_briefing_order.v1` |
| Presentation Selection Policy ID | `include_all_morning_briefing_records.v1` |
| Provenance Specification ID | `dashboard.provenance.v1` |
| Explicit UTC `as_of` | Canonical UTC encoding of the evaluation `as_of` under `utc_aware_instant_v1` |
| Configuration fingerprint inputs | Canonical encoding of validated Dashboard configuration bound to this Policy Version |
| Ordered Morning Briefing source identity sequence | Exact preserved Morning Briefing record identity sequence (`score_record_id` order) |
| Upstream Morning Briefing identity | Exact `briefing_id` as received |
| Upstream Morning Briefing provenance fingerprint references | Canonical encoding of Morning Briefing provenance fingerprints as received |

Identity SHALL remain distinct from every Premarket Score identity and from Morning Briefing identity.
Identity SHALL NEVER reuse a Premarket Score identity or Morning Briefing identity as `dashboard_output_id`.
Identity SHALL NEVER rewrite, invent, or synthesize upstream identities.
Identity SHALL NOT use UUID, wall-clock, randomness, or mutable runtime state.

Later identity schemes SHALL be introduced as new Identity Specifications and bound by a new Policy Version. They SHALL NOT silently replace `dashboard.identity.v1` inside this Policy Version.

## Provenance

### Provenance Specification `dashboard.provenance.v1`

This subordinate specification defines concrete Dashboard provenance construction for Policy Version v1 outputs.

Governance Decision #6 remains schema-agnostic at Governance fidelity. Concrete provenance obligations live only here.

Every Dashboard Presentation Output SHALL carry repository-governed provenance containing at least:

| Provenance element | Rule |
|--------------------|------|
| `policy_version_id` | `dashboard.policy.v1` |
| `ordering_preservation_policy_id` | `preserve_morning_briefing_order.v1` |
| `presentation_selection_policy_id` | `include_all_morning_briefing_records.v1` |
| `identity_specification_id` | `dashboard.identity.v1` |
| `provenance_specification_id` | `dashboard.provenance.v1` |
| `digest_method_id` | `canonical_payload_sha256_v1` |
| Explicit UTC `as_of` | Evaluation `as_of` |
| `config_fingerprint` | Deterministic fingerprint of validated Dashboard configuration + this Policy Version + bound subordinate specification IDs |
| `input_fingerprint` | Deterministic fingerprint of authorized inputs actually consumed, including ordered Morning Briefing source identity sequence and upstream Morning Briefing provenance fingerprints |
| Ordered `source_identifiers` | Deterministic ordered identifiers of consumed Morning Briefing records (`score_record_id` sequence exactly as preserved) |
| Upstream Morning Briefing identity linkage | Exact `briefing_id` as received |
| Upstream Morning Briefing provenance linkage | Exact Morning Briefing provenance fingerprints and Policy IDs as received |

Provenance SHALL be deterministic and immutable after construction.
Provenance SHALL NEVER fabricate lineage, omit approved lineage, or rewrite upstream provenance.
Traceability completeness SHALL NOT imply reconstruction authority over upstream bounded contexts.
Source-identifier order MUST equal Ordering Preservation order and Presentation Selection order.
Fingerprint digests SHALL use `canonical_payload_sha256_v1`.

## PIT Behavior

v1 PIT rules:

1. Request `as_of` MUST be timezone-aware.
2. Request `as_of` MUST normalize to UTC under `utc_aware_instant_v1`.
3. Request `as_of` MUST equal Morning Briefing public output `as_of` by instant.
4. Cross-`as_of` input SHALL fail closed.
5. Future knowledge is forbidden.
6. Naive (timezone-unaware) `as_of` SHALL fail closed.
7. PIT violations SHALL NOT be repaired.
8. Timestamp substitution is forbidden.
9. Wall-clock fallback is forbidden.

## Replay

### Replay Equality Policy `replay_equality.structural_complete.v1`

Replay SHALL re-execute the Presentation Pipeline under pinned:

- authorized Morning Briefing public output
- Dashboard configuration
- Policy Version identity `dashboard.policy.v1`
- explicit UTC `as_of`

Identical pinned inputs SHALL reproduce complete structural output equality, including:

- presentation records
- sequence
- `dashboard_output_id`
- Dashboard provenance
- fingerprints
- Policy IDs
- `as_of`

Replay SHALL NEVER depend on wall-clock time, randomness, mutable runtime state, rendering state, environment discovery, external side effects, or downstream consumers.

Replay inequality under identical pinned conditions SHALL fail closed.
Successful replay does not imply that every repository artifact participates in replay.

## Presentation Stability

Presentation authority shall remain stable across repository executions.

Presentation authority shall not vary because of rendering technology, client implementation, viewport configuration, display density, localization, or operational deployment environment.

Replay equality, identity, provenance, ordering, and Policy Version binding SHALL remain invariant under changes to UI framework, rendering technology, client implementation, or deployment topology.

## Presentation Completeness

Presentation authority does not require every authorized repository artifact to be presented.

Absence of presentation shall not be interpreted as absence of repository existence or semantic validity.

Presentation selection for `dashboard.policy.v1` is frozen by `include_all_morning_briefing_records.v1`.
Future Policy Versions may change presentation selection only within frozen Governance.
They SHALL NOT treat unpresented authorized artifacts as nonexistent or semantically invalid.

## Decimal and Canonicalization

Numeric score references SHALL use `Decimal` only.

v1 rules:

1. Score references MUST be finite `Decimal`.
2. Score domain MUST remain closed interval `[0, 1]` as received through Morning Briefing public output.
3. Binary floating-point conversion is forbidden.
4. Negative zero SHALL canonicalize to `Decimal("0")` without clamping non-zero values.
5. Canonical decimal string representation SHALL follow repository convention `canonical_decimal_str_v1`.
6. Numeric mutation, clamping, rounding alteration, or synthesis is forbidden.
7. Non-finite Decimal references SHALL fail closed.
8. Out-of-domain score references SHALL fail closed.

## Contract Invariants

The following repository contracts shall remain invariant throughout Policy Version v1 execution:

- Morning Briefing semantic meaning unchanged
- Morning Briefing identity references unchanged
- Morning Briefing provenance references unchanged
- upstream sequence unchanged
- explicit UTC `as_of` unchanged
- Dashboard Policy Version identity unchanged
- configuration immutable after binding
- Dashboard output identity deterministic
- Dashboard provenance deterministic
- no direct Premarket Scoring input
- no implementation-private upstream representation
- no UI / HTTP / storage behavior
- exactly one complete output on success
- presentation authority independent of rendering technology, client implementation, viewport, localization, and deployment environment
- absence of presentation does not imply absence of repository existence or semantic validity

Implementation shall not modify these invariants at any stage of the Presentation Pipeline.

## Output Completeness

### Output Completeness Policy `output_completeness.exactly_one_complete_output.v1`

Successful execution SHALL emit exactly one complete immutable Dashboard Presentation Output.

Prohibited:

- partial outputs
- incremental outputs
- partially validated outputs
- best-effort outputs
- outputs with missing required identity
- outputs with missing required provenance

Output Completeness violation SHALL fail closed.

## Public Contract Requirements

Dashboard SHALL consume Morning Briefing only through approved repository public contracts.
Dashboard SHALL expose only Dashboard-owned public contracts.

Dashboard public contracts SHALL NOT expose:

- Morning Briefing internals
- Premarket Scoring internals
- Feature Platform internals
- Market Data internals
- Strategy SDK redesign surfaces
- HTTP or UI contracts

Approval to consume or expose a public contract does not transfer ownership of that contract.

## Input Validation

Before Policy Version Binding, implementation SHALL validate all of the following:

1. Explicit UTC `as_of` is present and timezone-aware.
2. Dashboard configuration is present.
3. Requested Policy Version identity equals `dashboard.policy.v1`.
4. Morning Briefing public output is present.
5. Morning Briefing public output declares Policy Version `morning-briefing.policy.v1`.
6. Morning Briefing output carries `briefing_id` and Morning Briefing provenance.
7. Every Morning Briefing record carries required public identity, score, instrument, and provenance-linked fields as exposed by Morning Briefing public contracts.
8. No unauthorized input category from Governance Decision #2 is present.
9. No unexpected extra contract fields are present.
10. No direct Premarket Scoring public output is present as a Dashboard input.

Unauthorized, missing, or malformed required inputs SHALL fail closed.
Fabrication, inference, synthesis, substitution, and silent repair are forbidden.

## Policy Version Binding

Each Dashboard evaluation SHALL bind to exactly one Policy Version identity:

```text
dashboard.policy.v1
```

Unsupported, missing, or mismatched Policy Version identity SHALL fail closed.
Silent Policy Version substitution is forbidden.
Unsupported Morning Briefing Policy Version SHALL fail closed.

## Fail-Closed Rules

v1 SHALL fail closed when any of the following occur:

- missing Morning Briefing input
- malformed Morning Briefing input
- unauthorized input
- unsupported Dashboard Policy Version
- unsupported Morning Briefing Policy Version
- naive `as_of`
- `as_of` mismatch
- malformed upstream identity
- duplicate upstream identity where uniqueness is required by upstream public contracts
- malformed upstream provenance
- missing upstream provenance
- ordering mismatch
- identity mismatch
- provenance mismatch
- configuration mutation
- pipeline isolation violation
- output incompleteness
- replay inequality
- non-finite Decimal references
- out-of-domain score references
- unexpected extra contract fields
- Contract Invariant violation
- Configuration Stability violation
- Presentation Selection violation
- post-validation failure

Error handling rules:

1. No clamp.
2. No repair.
3. No substitution.
4. No fabrication.
5. No inference.
6. No synthesis.
7. No partial emission.
8. No partial success for prohibited conditions.
9. Original failure context SHALL be preserved at Policy boundaries.

## Error Taxonomy

v1 SHALL classify failures into the following Policy-fidelity categories:

| Category | Use |
|----------|-----|
| invalid input | Malformed request or contract fields |
| unauthorized input | Input outside Governance Decision #2 / this Policy Version |
| unsupported policy | Unsupported Dashboard or Morning Briefing Policy Version |
| PIT conflict | Naive `as_of`, mismatch, cross-`as_of`, or future knowledge |
| upstream policy mismatch | Morning Briefing public output not under `morning-briefing.policy.v1` |
| identity violation | Missing, malformed, duplicated, or mismatched identity |
| provenance violation | Missing, malformed, omitted, or rewritten provenance |
| ordering violation | Reordering, ranking, or sequence mismatch |
| domain violation | Non-finite or out-of-domain Decimal/score references |
| pipeline isolation violation | Stage bypass, reorder, repeat, or mutation of prior stage output |
| configuration stability violation | Configuration reload, mutation, or ambient substitution |
| output completeness violation | Partial, incremental, or incompletely validated emission |
| replay inequality | Divergence under identical pinned inputs |
| invariant violation | Any Contract Invariant breach |

This taxonomy does not define language-specific exception classes.

## Validation Rules

Validation occurs before emission. Invalid values are rejected, never repaired.

### Request and configuration

1. Request MUST contain Morning Briefing public output, explicit UTC `as_of`, Dashboard configuration, and `dashboard.policy.v1` identity.
2. Configuration MUST equal the frozen v1 Default Configuration IDs.
3. Unexpected extra request or configuration fields MUST fail closed.

### Upstream Morning Briefing contract

4. Morning Briefing Policy Version MUST equal `morning-briefing.policy.v1`.
5. `briefing_id` MUST be present and well-formed under Morning Briefing public contracts.
6. Morning Briefing provenance MUST be present and well-formed.
7. Every record MUST expose required public identity, score, instrument, and provenance-linked fields.
8. Direct Premarket Scoring inputs MUST be absent.

### Policy binding and PIT

9. Dashboard Policy Version MUST equal `dashboard.policy.v1`.
10. `as_of` MUST be timezone-aware UTC and equal Morning Briefing `as_of` by instant.
11. Cross-`as_of` and future knowledge MUST fail closed.

### Score references

12. Every exposed score reference MUST be finite `Decimal` in `[0, 1]`.
13. Negative zero MUST canonicalize to `Decimal("0")`.
14. Float conversion and numeric mutation MUST fail closed.

### Identity, provenance, and ordering

15. `dashboard_output_id` MUST match `dashboard.identity.v1` over the canonical payload.
16. Dashboard provenance MUST match `dashboard.provenance.v1`.
17. Presentation record count MUST equal Morning Briefing record count.
18. For every index `i`, Dashboard record `i` MUST reference Morning Briefing record `i` with exact identity, score, and provenance preservation.
19. Source-identifier order MUST equal preserved presentation order.
20. No independent ranking MAY be applied.

### Output, replay, determinism, and invariants

21. Successful emission MUST produce exactly one complete output.
22. Bound configuration MUST remain immutable throughout evaluation.
23. Contract Invariants MUST remain unmodified.
24. Pipeline Isolation MUST hold for every stage.
25. Replay under identical pinned inputs MUST reproduce complete structural equality.
26. Unauthorized inputs MUST remain absent at emission.
27. Rendering technology, client implementation, viewport configuration, display density, localization, or operational deployment environment MUST NOT alter presentation authority, identity, provenance, ordering, or replay equality.
28. Absence of an authorized artifact from presentation MUST NOT be treated as absence of repository existence or semantic validity.

Invalid outputs SHALL fail closed.

## Determinism

Identical:

- authorized Morning Briefing public output
- Dashboard configuration
- Policy Version identity `dashboard.policy.v1`
- explicit UTC `as_of`

SHALL always produce identical Dashboard Presentation Outputs, including identical:

- `dashboard_output_id`
- Dashboard provenance fingerprints
- ordered presentation records
- preserved upstream identity references
- preserved upstream provenance references
- preserved score references
- Policy IDs
- `as_of`

## Policy Constants

| Constant | Value |
|----------|-------|
| `policy_version_id` | `dashboard.policy.v1` |
| `ordering_preservation_policy_id` | `preserve_morning_briefing_order.v1` |
| `presentation_selection_policy_id` | `include_all_morning_briefing_records.v1` |
| `identity_specification_id` | `dashboard.identity.v1` |
| `provenance_specification_id` | `dashboard.provenance.v1` |
| `digest_method_id` | `canonical_payload_sha256_v1` |
| `output_completeness_policy_id` | `output_completeness.exactly_one_complete_output.v1` |
| `replay_equality_policy_id` | `replay_equality.structural_complete.v1` |
| Canonical UTC convention | `utc_aware_instant_v1` |
| Canonical Decimal convention | `canonical_decimal_str_v1` |
| Required upstream Morning Briefing Policy Version ID | `morning-briefing.policy.v1` |
| Required upstream Morning Briefing Identity Specification ID | `morning-briefing.identity.v1` |
| Required upstream Morning Briefing Provenance Specification ID | `morning-briefing.provenance.v1` |
| Required upstream scoring Policy Version ID (via Morning Briefing only) | `premarket.scoring.policy.v1` |
| Score domain | Finite `Decimal` in closed interval `[0, 1]` as received through Morning Briefing public output |
| Empty upstream Morning Briefing record collection | Authorized; yields empty presentation records with valid Dashboard identity and provenance |
| Direct Premarket Scoring consumption | Unauthorized |

Constants MUST be single-sourced by implementation.
No additional constants are defined by this Policy Version.

## Version Compatibility

- This Policy Version is identified solely by `dashboard.policy.v1`
- Evaluations MUST bind to exactly this Policy Version ID
- Ordering Preservation Policy, Presentation Selection Policy, Identity Specification, Provenance Specification, Digest Method, Output Completeness Policy, and Replay Equality Policy bound by this Policy Version are part of the concrete v1 contract
- A different Policy Version ID or subordinate specification ID selects a different concrete behavior set and MUST NOT be treated as equivalent

## Implementation Impact

Implementation may begin only under the separately approved Dashboard Implementation Authorization v1.

Implementation SHALL implement `dashboard.policy.v1` exactly.

Implementation SHALL remain fully subordinate to:

- Sprint 10 Planning Gate
- Dashboard Architecture v1
- Dashboard Governance Decisions #1–#8
- Premarket Scoring Governance Decisions #1–#12
- Premarket Scoring Policy Version `premarket.scoring.policy.v1`
- Morning Briefing Governance Decisions #1–#8
- Morning Briefing Policy Version `morning-briefing.policy.v1`
- Dashboard Implementation Authorization v1

Implementation SHALL NOT:

- reinterpret Governance
- change Policy behavior
- add direct Premarket Scoring consumption
- add UI
- add HTTP / API
- add persistence
- add workers
- add notifications
- add Human Review
- add AI Decision Engine
- add Broker Execution
- redefine semantic meaning
- expand authorized inputs
- regenerate or reorder upstream artifacts
- invent evidence
- bypass fail-closed, PIT, replay, identity, or provenance obligations

This Policy Version does not itself authorize implementation, UI, HTTP, persistence, workers, notifications, Human Review, AI Decision Engine, or Broker Execution.

## Future Compatibility

Future Dashboard Policy Versions may change deterministic presentation behavior only within frozen Governance.

They may not:

- supersede Governance
- expand authorized inputs without a subsequent approved Governance Decision
- redefine Dashboard semantic authority
- redefine upstream semantics
- silently modify `dashboard.policy.v1`

Implementation changes alone SHALL NOT alter this Policy Version.
Any change to v1 concrete behavior requires a new Policy Version ID and/or new subordinate specification IDs.

## Resolution

**Status:** APPROVED

**Policy effect:** `dashboard.policy.v1` becomes the complete immutable implementation-ready Policy Freeze for Dashboard Foundation. Deterministic Dashboard presentation behavior under this Policy Version is frozen for Dashboard Implementation Authorization v1 and subsequent authorized implementation.
