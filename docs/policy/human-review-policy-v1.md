# Human Review Policy Version v1 Specification

## Version Metadata

| Field | Value |
|-------|-------|
| Policy Version ID | `human-review.policy.v1` |
| Policy Version Label | Human Review Policy Version v1 |
| Status | APPROVED |
| Document class | Policy Version / Policy Freeze only |
| Bounded context | Human Review |
| Governance Dependency | Human Review Governance Decisions #1–#8 (immutable) |
| Upstream Dashboard Policy Dependency | `dashboard.policy.v1` (immutable) |
| Upstream Morning Briefing Policy Dependency | `morning-briefing.policy.v1` (immutable; via Dashboard public output only) |
| Upstream Premarket Scoring Policy Dependency | `premarket.scoring.policy.v1` (immutable; via Dashboard public output only) |
| Architecture Dependency | Human Review Architecture v1 (immutable) |
| Planning Dependency | Sprint 11 Planning Gate (immutable) |
| Ordering Preservation Policy ID | `preserve_dashboard_order.v1` |
| Presentation Preservation Policy ID | `include_all_dashboard_presentation_records.v1` |
| Human Attestation Policy ID | `explicit_human_attestation.recorded_input.v1` |
| Identity Specification ID | `human-review.identity.v1` |
| Provenance Specification ID | `human-review.provenance.v1` |
| History Specification ID | `human-review.history.v1` |
| Digest Method ID | `canonical_payload_sha256_v1` |
| Output Completeness Policy ID | `output_completeness.exactly_one_complete_output.v1` |
| Replay Equality Policy ID | `replay_equality.structural_complete.v1` |
| Canonical UTC Convention ID | `utc_aware_instant_v1` |
| Canonical Decimal Convention ID | `canonical_decimal_str_v1` |
| Score Domain | Finite `Decimal` in closed interval `[0, 1]` as received through Dashboard public output |

## Purpose

This specification defines the complete concrete deterministic behavior of Human Review Foundation under Policy Version `human-review.policy.v1`.

Governance defines what Human Review is permitted to do.
`human-review.policy.v1` defines exactly how the authorized Human Review Foundation behavior shall operate.

This Policy Version is subordinate to:

- Sprint 11 Planning Gate
- Human Review Architecture v1
- Human Review Governance Decisions #1–#8
- Dashboard Governance Decisions #1–#8
- Dashboard Policy Version `dashboard.policy.v1`
- Morning Briefing Governance Decisions #1–#8
- Morning Briefing Policy Version `morning-briefing.policy.v1`
- Premarket Scoring Governance Decisions #1–#12
- Premarket Scoring Policy Version `premarket.scoring.policy.v1`

This document does not modify, reinterpret, expand, or supersede any approved repository artifact.
Policy Freeze is subordinate to Governance.
`human-review.policy.v1` shall never redesign Architecture, expand authorized inputs, authorize implementation, or modify upstream semantics, ordering, identity, provenance, ownership, or human-authority meaning.

This Policy Version does not define reviewer roles, reviewer permissions, workflow, approval taxonomy, rejection taxonomy, state machines, APIs, storage, UI, rendering, layouts, styling, pagination, or filtering mechanisms.

## Governance Dependencies

This Policy Version SHALL comply with all of the following immutable Human Review Governance Decisions:

| Decision | Title | Binding effect on v1 |
|----------|-------|----------------------|
| #1 | Semantic Boundary | Human Review is a deterministic, auditable, point-in-time-bound record of explicit human attestation over authorized upstream context; no semantic ownership of upstream artifacts |
| #2 | Authorized Inputs | Only repository-authorized public inputs plus explicit recorded human attestation may be consumed; Dashboard required; direct Morning Briefing and Premarket Scoring unauthorized |
| #3 | Identity Policy | Human Review identity is unique, distinct, deterministic, and non-substitutable for upstream identities |
| #4 | Replay Policy | Replay reproduces the same Human Review semantic meaning from the same recorded inputs; no fabricated or inferred review authority |
| #5 | Provenance Policy | Upstream provenance preserved; Human Review provenance distinct and deterministic; no reconstruction authority |
| #6 | Output Policy | Outputs remain distinct Human Review semantic artifacts; never become trade approval, AI decision, or execution authority |
| #7 | Human Authority Policy | Authority is explicit and human-attested; never fabricated, inferred, synthesized, or auto-generated |
| #8 | Ordering & Presentation Policy | Upstream ordering preserved exactly; no independent ranking; presentation is semantic representation only |

This Policy Version SHALL also preserve:

- Dashboard semantic meaning under Dashboard Governance Decision #1
- Morning Briefing semantic meaning under Morning Briefing Governance Decision #1
- Premarket Score semantic meaning under Premarket Scoring Governance Decision #1
- all Dashboard Policy Version `dashboard.policy.v1` public-output invariants visible to consumers

## Authorized Inputs

v1 SHALL consume exactly:

| Input | Classification | v1 consumption rule |
|-------|----------------|---------------------|
| Dashboard public output | Required | Exactly one Dashboard Presentation Output produced under `dashboard.policy.v1` |
| Dashboard identity references | Required | Output MUST carry `dashboard_output_id` per `dashboard.identity.v1` |
| Dashboard provenance references | Required | Output MUST carry repository-governed Dashboard provenance per `dashboard.provenance.v1` |
| Explicit UTC `as_of` | Required | Single PIT context for the Human Review evaluation |
| Explicit human attestation | Required recorded input | Explicit recorded human authority under `explicit_human_attestation.recorded_input.v1` |
| Human Review configuration | Required | MUST identify `human-review.policy.v1` and all v1 subordinate specification IDs |
| Policy Version identity | Required | MUST equal `human-review.policy.v1` |

Dashboard public outputs remain the required authorized upstream.

v1 SHALL NOT consume:

- Morning Briefing public outputs as direct Human Review inputs
- Morning Briefing identity or provenance references as direct Human Review inputs
- Premarket Scoring public outputs as direct Human Review inputs
- Premarket Score identity or provenance references as direct Human Review inputs
- implementation-private Dashboard representations
- implementation-private Morning Briefing representations
- implementation-private Premarket Scoring representations
- raw Market Data, Feature Platform internals, Feature Store internals, Strategy SDK internals
- broker, portfolio, or live execution state
- AI Decision Engine outputs
- mutable UI, rendering, product-surface, or notification state
- any other information not listed as an Authorized Input under this Policy Version

Direct Morning Briefing public-output consumption remains unauthorized under Human Review Governance Decision #2 and this Policy Version.
Direct Premarket Scoring public-output consumption remains unauthorized under Human Review Governance Decision #2 and this Policy Version.

Explicit human attestation is not an upstream artifact.
It is recorded human authority as frozen by Human Review Governance Decision #1 and Human Review Governance Decision #7.

## Human Review Pipeline

v1 SHALL execute the following deterministic sequence exactly once per evaluation, in this immutable order:

```text
1. Input Validation
2. Policy Version Binding
3. Configuration Binding
4. PIT Validation
5. Authorized Input Admission
6. Explicit Human Attestation Admission
7. Dashboard Reference Preservation
8. Ordering Preservation
9. Human Review Record Construction
10. Human Review Identity Generation
11. Human Review Provenance Generation
12. Review History Binding
13. Output Construction
14. Post-Validation
15. Emission
```

Stage responsibilities:

| Stage | Responsibility |
|-------|----------------|
| Input Validation | Admit only Policy-legal requests; reject unauthorized or malformed inputs |
| Policy Version Binding | Bind evaluation to exactly `human-review.policy.v1` |
| Configuration Binding | Bind and freeze validated Human Review configuration for the evaluation |
| PIT Validation | Enforce single explicit UTC `as_of` equality with Dashboard `as_of` by instant |
| Authorized Input Admission | Admit only Governance Decision #2 authorized public inputs |
| Explicit Human Attestation Admission | Admit only explicit recorded human attestation under `explicit_human_attestation.recorded_input.v1` |
| Dashboard Reference Preservation | Capture Dashboard public-output references read-only |
| Ordering Preservation | Preserve Dashboard presentation-record order exactly under `preserve_dashboard_order.v1` |
| Human Review Record Construction | Form the deterministic Human Review semantic artifact from preserved authorized inputs and recorded attestation |
| Human Review Identity Generation | Produce Human Review identity under `human-review.identity.v1` |
| Human Review Provenance Generation | Produce Human Review provenance under `human-review.provenance.v1` |
| Review History Binding | Bind reconstructable review history under `human-review.history.v1` |
| Output Construction | Materialize the immutable Human Review output |
| Post-Validation | Enforce all post-conditions before emission |
| Emission | Return exactly one complete validated output or fail closed |

Required pipeline rules:

- every stage executes exactly once
- stages execute only in the frozen order
- no stage may be skipped, repeated, or reordered
- each stage consumes only the validated result of the previous stage
- no silent repair
- no partial success
- successful evaluation emits exactly one complete Human Review output

No stage MAY regenerate Dashboard outputs, regenerate Morning Briefing outputs, regenerate Premarket Scores, reorder upstream records, invent evidence, fabricate or infer human authority, auto-approve, auto-reject, or silently repair violations.

### Pipeline Isolation

Each Human Review Pipeline stage SHALL:

- consume only approved stage input from the immediately preceding validated stage output
- produce immutable stage output
- not bypass another stage
- not invoke a later stage early
- not mutate prior stage output
- not inspect implementation-private upstream state

Stage execution order is immutable for `human-review.policy.v1`.

Pipeline Isolation violation SHALL fail closed.

## Configuration

### Default Configuration

| Setting | Frozen v1 value |
|---------|-----------------|
| `policy_version_id` | `human-review.policy.v1` |
| `ordering_preservation_policy_id` | `preserve_dashboard_order.v1` |
| `presentation_preservation_policy_id` | `include_all_dashboard_presentation_records.v1` |
| `human_attestation_policy_id` | `explicit_human_attestation.recorded_input.v1` |
| `identity_specification_id` | `human-review.identity.v1` |
| `provenance_specification_id` | `human-review.provenance.v1` |
| `history_specification_id` | `human-review.history.v1` |
| `digest_method_id` | `canonical_payload_sha256_v1` |

This is the complete v1 Human Review configuration.
v1 SHALL NOT define reviewer roles, reviewer permissions, workflow, approval taxonomy, rejection taxonomy, filtering, sorting, pagination, UI, layout, rendering, or transport settings.

### Configuration Binding

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

## Human Authority

### Human Attestation Policy `explicit_human_attestation.recorded_input.v1`

For Policy Version v1, explicit human attestation SHALL:

- be present as a recorded input
- be explicit
- be human-attested
- participate in identity, provenance, replay, and history
- remain bound to the explicit UTC `as_of` of the evaluation

v1 SHALL NEVER:

- fabricate authority
- infer authority
- synthesize authority
- auto-generate authority
- auto-approve
- auto-reject
- convert Dashboard visibility into authority
- convert upstream semantics into authority
- substitute machine judgment for human attestation
- derive attestation from Dashboard ordering, scores, identity, provenance, or presentation

Missing, empty, inferred, fabricated, synthesized, or auto-generated attestation SHALL fail closed.

This subordinate specification does not define reviewer roles, reviewer identity mechanisms, workflow, approval taxonomy, rejection taxonomy, or state machines.
Recorded attestation is treated as explicit recorded human authority for deterministic binding only.

## Presentation Preservation

### Presentation Preservation Policy `include_all_dashboard_presentation_records.v1`

For Policy Version v1, Human Review SHALL:

- include every ordered Dashboard presentation record received in the authorized Dashboard public output as an upstream reference
- preserve the exact upstream sequence
- not filter
- not sort
- not paginate
- not truncate
- not deduplicate
- not aggregate
- not infer missing records

Empty Dashboard presentation-record sets (`N = 0`) SHALL yield empty Human Review upstream-reference records with valid evaluation-level identity, provenance, history, and required recorded attestation, and SHALL NOT fabricate instruments, records, or human authority.

Absence of an authorized artifact from a Human Review output SHALL NOT be interpreted as absence of repository existence or semantic validity under Governance.
Under this Policy Version, preservation includes all received Dashboard presentation records; omission is therefore limited to the empty-input case and does not authorize selective dropping.

This rule is presentation-neutral and does not define UI behavior.
Presentation is semantic representation only and is never the repository source of truth.

## Ordering

### Ordering Preservation Policy `preserve_dashboard_order.v1`

Human Review SHALL preserve Dashboard presentation-record order exactly as received from the Dashboard public output.

Normative rules:

1. Zero-based Human Review upstream-reference sequence index `i` SHALL correspond to Dashboard presentation-record position `i`.
2. Implementation SHALL NOT apply independent ranking.
3. Implementation SHALL NOT invent tie-breaks.
4. Implementation SHALL NOT reorder records.
5. Implementation SHALL NOT infer, fabricate, or regenerate ordering.
6. Position SHALL NOT imply recommendation, priority, investment advice, execution intent, review outcome, or authority.
7. Ordering preservation is mandatory for non-empty and empty collections alike.
8. Dashboard ordering SHALL NOT transfer to Human Review authority.

Ordering references never become Human Review authority.

## Contracts

Contracts below are conceptual Policy contracts.
They do not define transport schemas, JSON, HTTP fields, database columns, or UI models.

### Human Review Evaluation Request

A Human Review Evaluation Request SHALL contain exactly:

| Element | Rule |
|---------|------|
| Dashboard public output | Exactly one authorized Dashboard Presentation Output under `dashboard.policy.v1` |
| Explicit UTC `as_of` | Timezone-aware; normalized to UTC; equal by instant to Dashboard output `as_of` |
| Human Review configuration | Validated v1 configuration as defined above |
| Policy Version identity | Exactly `human-review.policy.v1` |
| Explicit recorded human attestation | Present and Policy-legal under `explicit_human_attestation.recorded_input.v1` |

Unexpected extra contract fields SHALL fail closed.
Unauthorized fields SHALL fail closed.

### Human Review Upstream Reference Record

Each Human Review Upstream Reference Record SHALL preserve at minimum:

| Element | Rule |
|---------|------|
| Sequence index | Zero-based index equal to Dashboard presentation-record position |
| Dashboard presentation-record identity reference | Exact upstream `score_record_id` as exposed on the Dashboard presentation record |
| `instrument_key` | Exact value as received |
| `local_symbol` | Exact value as received, including null |
| Score reference | Exact finite `Decimal` score as exposed through Dashboard public output |
| Component snapshot references | Exact values as exposed, including null absences |
| Dashboard `policy_version_id` | Must equal `dashboard.policy.v1` |
| Dashboard record `as_of` / upstream `as_of` as exposed | Must equal evaluation `as_of` by instant |
| Upstream identity reference | Exact Dashboard presentation-record identity linkage as received |
| Upstream provenance reference | Exact Dashboard / upstream provenance linkage as exposed on the public record path |

Human Review Upstream Reference Records SHALL remain read-only with respect to upstream meaning.

### Human Review Output

A Human Review Output SHALL contain at minimum:

| Element | Rule |
|---------|------|
| `human_review_output_id` | Deterministic identity per `human-review.identity.v1` |
| `policy_version_id` | `human-review.policy.v1` |
| `ordering_preservation_policy_id` | `preserve_dashboard_order.v1` |
| `presentation_preservation_policy_id` | `include_all_dashboard_presentation_records.v1` |
| `human_attestation_policy_id` | `explicit_human_attestation.recorded_input.v1` |
| `identity_specification_id` | `human-review.identity.v1` |
| `provenance_specification_id` | `human-review.provenance.v1` |
| `history_specification_id` | `human-review.history.v1` |
| Explicit UTC `as_of` | Evaluation `as_of` |
| Upstream Dashboard identity | Exact `dashboard_output_id` as received |
| Ordered immutable upstream-reference records | Zero or more records under Ordering and Presentation Preservation policies |
| Recorded explicit human attestation | Bound under `explicit_human_attestation.recorded_input.v1` |
| Human Review provenance | Per `human-review.provenance.v1` |
| Human Review history binding | Per `human-review.history.v1` |

A Human Review Output SHALL NEVER:

- modify semantic meaning
- redefine upstream semantic meaning
- become repository authority
- become investment advice
- become trade approval
- become AI decision
- become execution authority
- become risk approval
- become compliance approval
- imply that ordering equals recommendation, approval, or rejection
- imply that presentation equals authority, ownership, execution intent, or AI decision

## Identity

### Identity Specification `human-review.identity.v1`

This subordinate specification defines concrete Human Review identity construction for Policy Version v1 outputs.

Governance Decision #3 remains algorithm-agnostic at Governance fidelity. Identity algorithm details live only here.

**Identity outcome:** `human_review_output_id` is a deterministic 64-character lowercase hex digest.

**Digest method for v1:** `canonical_payload_sha256_v1`, consistent with existing repository deterministic identity conventions.

**Canonical identity payload MUST include exactly:**

| Payload element | Rule |
|-----------------|------|
| Identity Specification ID | `human-review.identity.v1` |
| Human Review Policy Version ID | `human-review.policy.v1` |
| Ordering Preservation Policy ID | `preserve_dashboard_order.v1` |
| Presentation Preservation Policy ID | `include_all_dashboard_presentation_records.v1` |
| Human Attestation Policy ID | `explicit_human_attestation.recorded_input.v1` |
| Provenance Specification ID | `human-review.provenance.v1` |
| History Specification ID | `human-review.history.v1` |
| Explicit UTC `as_of` | Canonical UTC encoding of the evaluation `as_of` under `utc_aware_instant_v1` |
| Configuration fingerprint inputs | Canonical encoding of validated Human Review configuration bound to this Policy Version |
| Ordered Dashboard source identity sequence | Exact preserved Dashboard presentation-record identity sequence (`score_record_id` order) |
| Upstream Dashboard identity | Exact `dashboard_output_id` as received |
| Upstream Dashboard provenance fingerprint references | Canonical encoding of Dashboard provenance fingerprints as received |
| Recorded human-attestation fingerprint | Canonical encoding of the admitted explicit recorded human attestation |

Identity SHALL remain distinct from every Dashboard identity, Morning Briefing identity, and Premarket Score identity.
Identity SHALL NEVER reuse a Dashboard identity, Morning Briefing identity, or Premarket Score identity as `human_review_output_id`.
Identity SHALL NEVER rewrite, invent, infer, fabricate, or synthesize upstream identities.
Identity SHALL NOT use UUID, wall-clock, randomness, or mutable runtime state.
Missing attestation SHALL NEVER be inferred to complete identity.

Later identity schemes SHALL be introduced as new Identity Specifications and bound by a new Policy Version. They SHALL NOT silently replace `human-review.identity.v1` inside this Policy Version.

## Provenance

### Provenance Specification `human-review.provenance.v1`

This subordinate specification defines concrete Human Review provenance construction for Policy Version v1 outputs.

Governance Decision #5 remains schema-agnostic at Governance fidelity. Concrete provenance obligations live only here.

Every Human Review Output SHALL carry repository-governed provenance containing at least:

| Provenance element | Rule |
|--------------------|------|
| `policy_version_id` | `human-review.policy.v1` |
| `ordering_preservation_policy_id` | `preserve_dashboard_order.v1` |
| `presentation_preservation_policy_id` | `include_all_dashboard_presentation_records.v1` |
| `human_attestation_policy_id` | `explicit_human_attestation.recorded_input.v1` |
| `identity_specification_id` | `human-review.identity.v1` |
| `provenance_specification_id` | `human-review.provenance.v1` |
| `history_specification_id` | `human-review.history.v1` |
| `digest_method_id` | `canonical_payload_sha256_v1` |
| Explicit UTC `as_of` | Evaluation `as_of` |
| `config_fingerprint` | Deterministic fingerprint of validated Human Review configuration + this Policy Version + bound subordinate specification IDs |
| `input_fingerprint` | Deterministic fingerprint of authorized inputs actually consumed, including ordered Dashboard source identity sequence, upstream Dashboard provenance fingerprints, and recorded human-attestation fingerprint |
| Ordered `source_identifiers` | Deterministic ordered identifiers of consumed Dashboard presentation records (`score_record_id` sequence exactly as preserved) |
| Upstream Dashboard identity linkage | Exact `dashboard_output_id` as received |
| Upstream Dashboard provenance linkage | Exact Dashboard provenance fingerprints and Policy IDs as received |
| Recorded human-attestation fingerprint | Canonical encoding of admitted explicit recorded human attestation |

Provenance SHALL represent only Human Review semantic lineage.
Provenance SHALL be deterministic and immutable after construction.
Provenance SHALL NEVER fabricate lineage, infer missing provenance, omit approved lineage, or rewrite upstream provenance.
Complete Human Review provenance REQUIRES complete authorized upstream provenance references.
Completeness SHALL NEVER be satisfied through fabricated or inferred lineage.
Traceability completeness SHALL NOT imply reconstruction authority over upstream bounded contexts.
Source-identifier order MUST equal Ordering Preservation order and Presentation Preservation order.
Fingerprint digests SHALL use `canonical_payload_sha256_v1`.

## Review History

### History Specification `human-review.history.v1`

This subordinate specification defines concrete Human Review history binding for Policy Version v1 outputs.

Governance and Architecture remain storage-agnostic. Concrete history reconstructability obligations live only here.
This specification does not define event sourcing, persistence, append-only storage, database mechanisms, or retention mechanics.

Human Review history for a given evaluation SHALL:

- bind to `human_review_output_id`
- bind to Human Review provenance
- bind to preserved upstream Dashboard identity and provenance references
- bind to recorded explicit human attestation
- bind to the explicit UTC `as_of`
- remain reconstructable from the same pinned authorized recorded inputs, frozen configuration, Policy Version identity, recorded attestation, and UTC `as_of`

History SHALL NEVER be silently rewritten, fabricated, inferred, synthesized to fill gaps, auto-approved, or auto-rejected into existence.

History binding SHALL remain immutable after construction for the evaluation.

## PIT Behavior

v1 PIT rules:

1. Request `as_of` MUST be timezone-aware.
2. Request `as_of` MUST normalize to UTC under `utc_aware_instant_v1`.
3. Request `as_of` MUST equal Dashboard public output `as_of` by instant.
4. Cross-`as_of` input SHALL fail closed.
5. Future knowledge is forbidden.
6. Naive (timezone-unaware) `as_of` SHALL fail closed.
7. PIT violations SHALL NOT be repaired.
8. Timestamp substitution is forbidden.
9. Wall-clock fallback is forbidden.
10. Future knowledge SHALL NEVER alter historical review meaning.

## Replay

### Replay Equality Policy `replay_equality.structural_complete.v1`

Replay SHALL re-execute the Human Review Pipeline under pinned:

- authorized Dashboard public output
- explicit recorded human attestation
- Human Review configuration
- Policy Version identity `human-review.policy.v1`
- explicit UTC `as_of`

Identical pinned inputs SHALL reproduce complete structural output equality, including:

- Human Review semantic meaning
- upstream-reference records
- sequence
- recorded human attestation binding
- `human_review_output_id`
- Human Review provenance
- Human Review history binding
- fingerprints
- Policy IDs
- `as_of`

Replay SHALL NEVER:

- infer missing review
- fabricate review
- regenerate missing authority
- reinterpret Dashboard meaning
- rewrite identity
- rewrite provenance
- change semantic meaning
- synthesize replay completeness

Replay SHALL NEVER depend on wall-clock time, randomness, mutable runtime state, rendering state, presentation, transport, environment discovery, external side effects, or downstream consumers.

Replay inequality under identical pinned conditions SHALL fail closed.
Missing required replay inputs SHALL NEVER be silently repaired.
Successful replay does not imply that every repository artifact participates in replay.

## Presentation Stability

Presentation is semantic representation only.

Presentation shall remain stable across repository executions.

Presentation shall never:

- change Human Review meaning
- create authority
- create approval
- create rejection
- create execution intent
- redefine upstream semantics

Presentation authority shall not vary because of rendering technology, client implementation, transport, deployment topology, or operational environment.

Replay equality, identity, provenance, ordering, human authority, and Policy Version binding SHALL remain invariant under changes to UI framework, rendering technology, client implementation, or deployment topology.

Presentation is never the repository source of truth.

## Presentation Completeness

A Human Review presentation SHALL be semantically complete only when all required Human Review semantic elements are represented.

Completeness SHALL NEVER be satisfied by:

- inferred review
- fabricated review
- inferred ordering
- fabricated ordering
- omitted required semantic references
- synthesized authority

Presentation completeness does not require every authorized repository artifact outside the frozen Presentation Preservation Policy to be presented.

Absence of presentation shall not be interpreted as absence of repository existence or semantic validity.

Presentation preservation for `human-review.policy.v1` is frozen by `include_all_dashboard_presentation_records.v1`.
Future Policy Versions may change presentation selection only within frozen Governance.
They SHALL NOT treat unpresented authorized artifacts as nonexistent or semantically invalid.

## Decimal and Canonicalization

Numeric score references SHALL use `Decimal` only.

v1 rules:

1. Score references MUST be finite `Decimal`.
2. Score domain MUST remain closed interval `[0, 1]` as received through Dashboard public output.
3. Binary floating-point conversion is forbidden.
4. Negative zero SHALL canonicalize to `Decimal("0")` without clamping non-zero values.
5. Canonical decimal string representation SHALL follow repository convention `canonical_decimal_str_v1`.
6. Numeric mutation, clamping, rounding alteration, or synthesis is forbidden.
7. Non-finite Decimal references SHALL fail closed.
8. Out-of-domain score references SHALL fail closed.

## Contract Invariants

The following repository contracts shall remain invariant throughout Policy Version v1 execution:

- Dashboard semantic meaning unchanged
- Dashboard identity references unchanged
- Dashboard provenance references unchanged
- upstream sequence unchanged
- explicit UTC `as_of` unchanged
- Human Review Policy Version identity unchanged
- configuration immutable after binding
- Human Review output identity deterministic
- Human Review provenance deterministic
- Human Review history reconstructable from pinned recorded inputs
- explicit human attestation not inferred or fabricated
- no direct Morning Briefing input
- no direct Premarket Scoring input
- no implementation-private upstream representation
- no UI / HTTP / storage behavior
- exactly one complete output on success
- presentation authority independent of rendering technology, client implementation, transport, and deployment environment
- absence of presentation does not imply absence of repository existence or semantic validity
- Human Review output never equals trade approval, execution authorization, AI decision, risk approval, or compliance approval

Implementation shall not modify these invariants at any stage of the Human Review Pipeline.

## Output Completeness

### Output Completeness Policy `output_completeness.exactly_one_complete_output.v1`

Successful execution SHALL emit exactly one complete immutable Human Review Output.

A Human Review output SHALL be considered semantically complete only when all required Human Review semantic elements are present.

Completeness SHALL NEVER be achieved through:

- inferred review
- fabricated review
- synthesized authority
- omitted required semantic references

Prohibited:

- partial outputs
- incremental outputs
- partially validated outputs
- best-effort outputs
- outputs with missing required identity
- outputs with missing required provenance
- outputs with missing required history binding
- outputs with missing required recorded human attestation

Output Completeness violation SHALL fail closed.

## Public Contract Requirements

Human Review SHALL consume Dashboard only through approved repository public contracts.
Human Review SHALL expose only Human Review-owned public contracts.

Human Review public contracts SHALL NOT expose:

- Dashboard internals
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
2. Human Review configuration is present.
3. Requested Policy Version identity equals `human-review.policy.v1`.
4. Dashboard public output is present.
5. Dashboard public output declares Policy Version `dashboard.policy.v1`.
6. Dashboard output carries `dashboard_output_id` and Dashboard provenance.
7. Every Dashboard presentation record carries required public identity, score, instrument, and provenance-linked fields as exposed by Dashboard public contracts.
8. Explicit recorded human attestation is present.
9. No unauthorized input category from Governance Decision #2 is present.
10. No unexpected extra contract fields are present.
11. No direct Morning Briefing public output is present as a Human Review input.
12. No direct Premarket Scoring public output is present as a Human Review input.

Unauthorized, missing, or malformed required inputs SHALL fail closed.
Fabrication, inference, synthesis, substitution, and silent repair are forbidden.

## Policy Version Binding

Each Human Review evaluation SHALL bind to exactly one Policy Version identity:

```text
human-review.policy.v1
```

Unsupported, missing, or mismatched Policy Version identity SHALL fail closed.
Silent Policy Version substitution is forbidden.
Unsupported Dashboard Policy Version SHALL fail closed.

## Fail-Closed Rules

v1 SHALL fail closed when any of the following occur:

- missing Dashboard input
- malformed Dashboard input
- unauthorized input
- missing recorded human attestation
- inferred, fabricated, synthesized, or auto-generated human authority
- unsupported Human Review Policy Version
- unsupported Dashboard Policy Version
- naive `as_of`
- `as_of` mismatch
- malformed upstream identity
- duplicate upstream identity where uniqueness is required by upstream public contracts
- malformed upstream provenance
- missing upstream provenance
- omitted required upstream provenance relationships
- ordering mismatch
- identity mismatch
- provenance mismatch
- history-binding mismatch
- configuration mutation
- pipeline isolation violation
- output incompleteness
- replay inequality
- non-finite Decimal references
- out-of-domain score references
- unexpected extra contract fields
- Contract Invariant violation
- Configuration Stability violation
- Presentation Preservation violation
- Human Authority violation
- post-validation failure

Error handling rules:

1. No clamp.
2. No repair.
3. No substitution.
4. No fabrication.
5. No inference.
6. No synthesis.
7. No auto-approval.
8. No auto-rejection.
9. No partial emission.
10. No partial success for prohibited conditions.
11. Original failure context SHALL be preserved at Policy boundaries.

## Error Taxonomy

v1 SHALL classify failures into the following Policy-fidelity categories:

| Category | Use |
|----------|-----|
| invalid input | Malformed request or contract fields |
| unauthorized input | Input outside Governance Decision #2 / this Policy Version |
| unsupported policy | Unsupported Human Review or Dashboard Policy Version |
| PIT conflict | Naive `as_of`, mismatch, cross-`as_of`, or future knowledge |
| upstream policy mismatch | Dashboard public output not under `dashboard.policy.v1` |
| human-authority violation | Missing, inferred, fabricated, synthesized, or auto-generated attestation |
| identity violation | Missing, malformed, duplicated, or mismatched identity |
| provenance violation | Missing, malformed, omitted, inferred, or rewritten provenance |
| history violation | Missing, mutated, fabricated, or non-reconstructable history binding |
| ordering violation | Reordering, ranking, inferred ordering, or sequence mismatch |
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

1. Request MUST contain Dashboard public output, explicit UTC `as_of`, Human Review configuration, `human-review.policy.v1` identity, and explicit recorded human attestation.
2. Configuration MUST equal the frozen v1 Default Configuration IDs.
3. Unexpected extra request or configuration fields MUST fail closed.

### Upstream Dashboard contract

4. Dashboard Policy Version MUST equal `dashboard.policy.v1`.
5. `dashboard_output_id` MUST be present and well-formed under Dashboard public contracts.
6. Dashboard provenance MUST be present and well-formed.
7. Every presentation record MUST expose required public identity, score, instrument, and provenance-linked fields.
8. Direct Morning Briefing inputs MUST be absent.
9. Direct Premarket Scoring inputs MUST be absent.

### Human authority

10. Explicit recorded human attestation MUST be present.
11. Attestation MUST NOT be inferred, fabricated, synthesized, auto-generated, auto-approved, or auto-rejected.
12. Attestation MUST NOT be derived from Dashboard visibility, ordering, scores, identity, provenance, or presentation.

### Policy binding and PIT

13. Human Review Policy Version MUST equal `human-review.policy.v1`.
14. `as_of` MUST be timezone-aware UTC and equal Dashboard `as_of` by instant.
15. Cross-`as_of` and future knowledge MUST fail closed.

### Score references

16. Every exposed score reference MUST be finite `Decimal` in `[0, 1]`.
17. Negative zero MUST canonicalize to `Decimal("0")`.
18. Float conversion and numeric mutation MUST fail closed.

### Identity, provenance, ordering, and history

19. `human_review_output_id` MUST match `human-review.identity.v1` over the canonical payload.
20. Human Review provenance MUST match `human-review.provenance.v1`.
21. Human Review history binding MUST match `human-review.history.v1`.
22. Upstream-reference record count MUST equal Dashboard presentation-record count.
23. For every index `i`, Human Review upstream-reference record `i` MUST reference Dashboard presentation record `i` with exact identity, score, and provenance preservation.
24. Source-identifier order MUST equal preserved upstream-reference order.
25. No independent ranking MAY be applied.

### Output, replay, determinism, and invariants

26. Successful emission MUST produce exactly one complete output.
27. Bound configuration MUST remain immutable throughout evaluation.
28. Contract Invariants MUST remain unmodified.
29. Pipeline Isolation MUST hold for every stage.
30. Replay under identical pinned inputs MUST reproduce complete structural equality.
31. Unauthorized inputs MUST remain absent at emission.
32. Rendering technology, client implementation, transport, or operational deployment environment MUST NOT alter presentation semantics, identity, provenance, ordering, human authority, or replay equality.
33. Absence of an authorized artifact from presentation MUST NOT be treated as absence of repository existence or semantic validity.
34. Human Review output MUST NOT be treated as trade approval, execution authorization, AI decision, risk approval, or compliance approval.

Invalid outputs SHALL fail closed.

## Determinism

Identical:

- authorized Dashboard public output
- explicit recorded human attestation
- Human Review configuration
- Policy Version identity `human-review.policy.v1`
- explicit UTC `as_of`

SHALL always produce identical Human Review Outputs, including identical:

- `human_review_output_id`
- Human Review provenance fingerprints
- Human Review history binding
- ordered upstream-reference records
- preserved upstream identity references
- preserved upstream provenance references
- preserved score references
- recorded human-attestation binding
- Policy IDs
- `as_of`

Output meaning SHALL NEVER change because of wall-clock time, mutable runtime state, downstream interpretation, presentation, or transport.

## Policy Constants

| Constant | Value |
|----------|-------|
| `policy_version_id` | `human-review.policy.v1` |
| `ordering_preservation_policy_id` | `preserve_dashboard_order.v1` |
| `presentation_preservation_policy_id` | `include_all_dashboard_presentation_records.v1` |
| `human_attestation_policy_id` | `explicit_human_attestation.recorded_input.v1` |
| `identity_specification_id` | `human-review.identity.v1` |
| `provenance_specification_id` | `human-review.provenance.v1` |
| `history_specification_id` | `human-review.history.v1` |
| `digest_method_id` | `canonical_payload_sha256_v1` |
| `output_completeness_policy_id` | `output_completeness.exactly_one_complete_output.v1` |
| `replay_equality_policy_id` | `replay_equality.structural_complete.v1` |
| Canonical UTC convention | `utc_aware_instant_v1` |
| Canonical Decimal convention | `canonical_decimal_str_v1` |
| Required upstream Dashboard Policy Version ID | `dashboard.policy.v1` |
| Required upstream Dashboard Identity Specification ID | `dashboard.identity.v1` |
| Required upstream Dashboard Provenance Specification ID | `dashboard.provenance.v1` |
| Required upstream Morning Briefing Policy Version ID (via Dashboard only) | `morning-briefing.policy.v1` |
| Required upstream scoring Policy Version ID (via Dashboard only) | `premarket.scoring.policy.v1` |
| Score domain | Finite `Decimal` in closed interval `[0, 1]` as received through Dashboard public output |
| Empty upstream Dashboard presentation-record collection | Authorized; yields empty upstream-reference records with valid Human Review identity, provenance, history, and required recorded attestation |
| Direct Morning Briefing consumption | Unauthorized |
| Direct Premarket Scoring consumption | Unauthorized |
| Human Review authority | Explicit recorded human attestation only; never inferred, fabricated, synthesized, or auto-generated |

Constants MUST be single-sourced by implementation.
No additional constants are defined by this Policy Version.

## Version Compatibility

- This Policy Version is identified solely by `human-review.policy.v1`
- Evaluations MUST bind to exactly this Policy Version ID
- Ordering Preservation Policy, Presentation Preservation Policy, Human Attestation Policy, Identity Specification, Provenance Specification, History Specification, Digest Method, Output Completeness Policy, and Replay Equality Policy bound by this Policy Version are part of the concrete v1 contract
- A different Policy Version ID or subordinate specification ID selects a different concrete behavior set and MUST NOT be treated as equivalent

## Implementation Impact

Future implementation must preserve the deterministic behavior frozen here.

Implementation may begin only under a separately approved Human Review Implementation Authorization.

Implementation SHALL implement `human-review.policy.v1` exactly.

Implementation SHALL remain fully subordinate to:

- Sprint 11 Planning Gate
- Human Review Architecture v1
- Human Review Governance Decisions #1–#8
- Dashboard Governance Decisions #1–#8
- Dashboard Policy Version `dashboard.policy.v1`
- Morning Briefing Governance Decisions #1–#8
- Morning Briefing Policy Version `morning-briefing.policy.v1`
- Premarket Scoring Governance Decisions #1–#12
- Premarket Scoring Policy Version `premarket.scoring.policy.v1`

Implementation SHALL NOT:

- reinterpret Governance
- change Policy behavior
- add direct Morning Briefing consumption
- add direct Premarket Scoring consumption
- add UI
- add HTTP / API
- add persistence
- add workers
- add notifications
- add AI Decision Engine
- add Broker Execution
- redefine semantic meaning
- expand authorized inputs
- regenerate or reorder upstream artifacts
- invent evidence
- fabricate, infer, synthesize, or auto-generate human authority
- bypass fail-closed, PIT, replay, identity, provenance, history, or human-authority obligations

This Policy Version does not itself authorize implementation, UI, HTTP, persistence, workers, notifications, AI Decision Engine, or Broker Execution.
This Policy Version does not create Implementation Authorization.

## Future Compatibility

Future Human Review Policy Versions may change deterministic Human Review behavior only within frozen Governance.

They may not:

- supersede Governance
- expand authorized inputs without a subsequent approved Governance Decision
- redefine Human Review semantic authority
- redefine upstream semantics
- authorize inferred, fabricated, synthesized, or auto-generated human authority
- silently modify `human-review.policy.v1`

Implementation changes alone SHALL NOT alter this Policy Version.
Any change to v1 concrete behavior requires a new Policy Version ID and/or new subordinate specification IDs.

## Resolution

**Status:** APPROVED

**Policy effect:** `human-review.policy.v1` becomes the complete immutable implementation-ready Policy Freeze for Human Review Foundation. Deterministic Human Review behavior under this Policy Version is frozen for later Human Review Implementation Authorization and subsequent authorized implementation. This Policy Version does not authorize implementation.
