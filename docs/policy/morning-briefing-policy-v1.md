# Morning Briefing Policy Version v1 Specification

## Version Metadata

| Field | Value |
|-------|-------|
| Policy Version ID | `morning-briefing.policy.v1` |
| Policy Version Label | Morning Briefing Policy Version v1 |
| Status | APPROVED |
| Governance Dependency | Morning Briefing Governance Decisions #1–#8 (immutable) |
| Upstream Scoring Policy Dependency | `premarket.scoring.policy.v1` (immutable) |
| Architecture Dependency | Morning Briefing Architecture v1 (immutable) |
| Planning Dependency | Sprint 9 Planning Gate (immutable) |
| Ordering Preservation Policy ID | `preserve_premarket_scoring_order.v1` |
| Identity Specification ID | `morning-briefing.identity.v1` |
| Provenance Specification ID | `morning-briefing.provenance.v1` |
| Digest Method ID | `canonical_payload_sha256_v1` |

## Purpose

This specification defines the complete concrete deterministic behavior of Morning Briefing generation under Policy Version `morning-briefing.policy.v1`.

This Policy Version is subordinate to Morning Briefing Governance Decisions #1–#8, Premarket Scoring Governance Decisions #1–#12, Premarket Scoring Engine Architecture v1, Premarket Scoring Policy Version `premarket.scoring.policy.v1`, Morning Briefing Architecture v1, and the Sprint 9 Planning Gate.

This document does not modify, reinterpret, or expand any approved repository artifact.

## Governance Dependencies

This Policy Version SHALL comply with all of the following immutable Morning Briefing Governance Decisions:

| Decision | Title | Binding effect on v1 |
|----------|-------|----------------------|
| #1 | Semantic Boundary | Morning Briefing is presentation-oriented operator attention context only |
| #2 | Authorized Inputs | Only repository-authorized public inputs may be consumed |
| #3 | Brief Assembly Policy | Assembly is read-only, non-fabricating, and presentation-neutral |
| #4 | Replay Policy | Replay depends only on authorized inputs, UTC `as_of`, Policy Version, and configuration |
| #5 | Identity Policy | Morning Briefing identity is distinct, deterministic, and non-substitutable for score identity |
| #6 | Provenance Policy | Upstream provenance is preserved; Morning Briefing provenance is distinct and deterministic |
| #7 | Output Policy | Outputs preserve semantic meaning, identity, provenance, and ordering; remain presentation-neutral |
| #8 | Ordering & Presentation Policy | Premarket Scoring ordering is preserved exactly; no independent ranking |

This Policy Version SHALL also preserve Premarket Scoring Governance Decision #1 score semantic meaning and all Premarket Scoring Policy Version `premarket.scoring.policy.v1` public-output invariants visible to consumers.

## Authorized Inputs

v1 SHALL consume only:

| Input | Classification | v1 consumption rule |
|-------|----------------|---------------------|
| Premarket Scoring public output | Required | Exactly one Score Collection produced under `premarket.scoring.policy.v1` |
| Premarket Score identity references | Required | Every consumed Score Record MUST carry `score_record_id` per `premarket.score.identity.v1` |
| Premarket Score provenance references | Required | Every consumed Score Record MUST carry repository-governed score provenance |
| Explicit UTC `as_of` | Required | Single PIT context for the briefing evaluation |
| Morning Briefing configuration | Required | MUST identify `morning-briefing.policy.v1` |
| Policy Version identity | Required | MUST equal `morning-briefing.policy.v1` |
| Existing Premarket settings | Conditional | If supplied and `enabled=False`, evaluation SHALL fail closed |

v1 SHALL NOT consume any other evidence source.

## Assembly Pipeline

v1 SHALL execute the following deterministic sequence exactly once per evaluation, in this order:

```text
1. Input Validation
2. Policy Version Binding
3. PIT Validation
4. Authorized Input Admission
5. Score Reference Preservation
6. Ordering Preservation
7. Briefing Assembly
8. Identity Generation
9. Provenance Generation
10. Output Construction
11. Post-Validation
12. Emission
```

Stage responsibilities:

| Stage | Responsibility |
|-------|----------------|
| Input Validation | Admit only Policy-legal requests; reject unauthorized or malformed inputs |
| Policy Version Binding | Bind evaluation to exactly `morning-briefing.policy.v1` |
| PIT Validation | Enforce single explicit UTC `as_of` and reject cross-PIT or future knowledge |
| Authorized Input Admission | Admit only Decision #2 authorized public inputs |
| Score Reference Preservation | Capture Premarket Score values, identities, and provenance read-only |
| Ordering Preservation | Preserve Premarket Scoring order exactly under `preserve_premarket_scoring_order.v1` |
| Briefing Assembly | Form the deterministic briefing from preserved score references and evaluation context |
| Identity Generation | Produce Morning Briefing identity under `morning-briefing.identity.v1` |
| Provenance Generation | Produce Morning Briefing provenance under `morning-briefing.provenance.v1` |
| Output Construction | Materialize the immutable Morning Briefing output |
| Post-Validation | Enforce all post-conditions before emission |
| Emission | Return the validated output or fail closed |

No stage MAY regenerate Premarket Scores, reorder Premarket Scores, invent evidence, or silently repair violations.

### Pipeline Isolation

Each Assembly Pipeline stage shall consume only the validated output of the immediately preceding stage.

A stage shall not bypass, reorder, repeat, or modify another stage.

Stage execution order is immutable within Policy Version v1.

## Input Validation

Before Policy Version Binding, implementation SHALL validate all of the following:

1. Explicit UTC `as_of` is present and timezone-aware UTC.  
2. Morning Briefing configuration is present.  
3. Requested Policy Version identity equals `morning-briefing.policy.v1`.  
4. Premarket Scoring public output is present.  
5. Premarket Scoring public output declares Policy Version `premarket.scoring.policy.v1`.  
6. Every Score Record carries `score_record_id`, finite `Decimal` score in `[0, 1]`, `instrument_key`, `as_of`, Policy Version identity, and score provenance.  
7. No unauthorized input category from Governance Decision #2 is present.  
8. Premarket settings, when supplied and disabled, fail closed.

Unauthorized inputs SHALL fail closed.  
Missing required inputs SHALL fail closed.  
Fabrication, inference, synthesis, substitution, and silent repair are forbidden.

## Policy Version Binding

Each Morning Briefing evaluation SHALL bind to exactly one Policy Version identity:

```text
morning-briefing.policy.v1
```

Unsupported, missing, or mismatched Policy Version identity SHALL fail closed.  
Silent Policy Version substitution is forbidden.

### Configuration Stability

Configuration bound during Policy Version Binding shall remain immutable throughout the evaluation.

Configuration shall not be replaced, reloaded, or mutated during execution.

## PIT Behavior

v1 PIT rules:

1. Exactly one explicit UTC `as_of` per evaluation.  
2. The Morning Briefing `as_of` MUST equal the Premarket Scoring public output `as_of`.  
3. Only Premarket Scoring outputs already valid for that `as_of` may participate.  
4. Future-known evidence SHALL fail closed.  
5. Cross-PIT mixing SHALL fail closed.  
6. PIT violations are validated and SHALL NOT be repaired.

## Assembly Rules

### Read-only consumption

Assembly SHALL consume authorized inputs as immutable artifacts.

Assembly SHALL NEVER:

- regenerate Premarket Scores  
- mutate Premarket Scores  
- reorder Premarket Scores  
- reinterpret Premarket Scores as recommendations, approvals, or execution authority  
- invent briefing content  
- fabricate, infer, or synthesize evidence  

### Score reference preservation

For each Score Record in the Premarket Scoring public output, assembly SHALL preserve exactly:

| Preserved element | Rule |
|-------------------|------|
| `score` | Exact finite `Decimal` value as received |
| `score_record_id` | Exact identity as received |
| Score provenance | Exact provenance references as received |
| `instrument_key` | Exact value as received |
| `local_symbol` | Exact value as received, including null |
| Score component snapshot | Exact values as received, including null absences |
| Scoring `policy_version_id` | Must equal `premarket.scoring.policy.v1` |
| Scoring `weight_profile_id` | Exact value as received |
| Scoring `as_of` | Must equal Morning Briefing `as_of` |

### Evaluation context preservation

Assembly SHALL bind the briefing to:

- Morning Briefing Policy Version identity `morning-briefing.policy.v1`  
- Morning Briefing configuration as supplied and validated  
- Explicit UTC `as_of`  
- Ordering Preservation Policy ID `preserve_premarket_scoring_order.v1`  
- Identity Specification ID `morning-briefing.identity.v1`  
- Provenance Specification ID `morning-briefing.provenance.v1`  

### Empty universe

An empty Premarket Scoring public output (`N = 0` Score Records) SHALL yield an empty Morning Briefing record set with valid evaluation-level identity and provenance and SHALL NOT fabricate instruments or scores.

## Ordering

### Ordering Preservation Policy `preserve_premarket_scoring_order.v1`

Morning Briefing SHALL preserve Premarket Scoring ordering exactly as received from the Premarket Scoring public output.

Normative rules:

1. Briefing record sequence index `i` SHALL reference Score Record at scoring-collection index `i`.  
2. Implementation SHALL NOT apply independent ranking.  
3. Implementation SHALL NOT mutate score values to affect order.  
4. Implementation SHALL NOT invent tie-breaks that replace Premarket Scoring order.  
5. Ordering preservation is mandatory for non-empty and empty collections alike.

## Identity

### Identity Specification `morning-briefing.identity.v1`

This subordinate specification defines concrete Morning Briefing identity construction for Policy Version v1 outputs.

Governance Decision #5 remains algorithm-agnostic at Governance fidelity. Identity algorithm details live only here.

**Identity outcome:** `briefing_id` is a deterministic 64-character lowercase hex digest.

**Digest method for v1:** `canonical_payload_sha256_v1`, consistent with existing Premarket deterministic identity conventions.

**Canonical identity payload MUST include exactly:**

| Payload element | Rule |
|-----------------|------|
| Identity Specification ID | `morning-briefing.identity.v1` |
| Morning Briefing Policy Version ID | `morning-briefing.policy.v1` |
| Ordering Preservation Policy ID | `preserve_premarket_scoring_order.v1` |
| Provenance Specification ID | `morning-briefing.provenance.v1` |
| Explicit UTC `as_of` | Canonical UTC encoding of the evaluation `as_of` |
| Configuration fingerprint inputs | Canonical encoding of validated Morning Briefing configuration bound to this Policy Version |
| Upstream Scoring Policy Version ID | `premarket.scoring.policy.v1` |
| Ordered `score_record_id` sequence | Exact sequence preserved from Premarket Scoring public output |
| Upstream scoring collection provenance fingerprints | Canonical encoding of scoring collection provenance as received |

Identity SHALL remain distinct from every `score_record_id`.  
Identity SHALL NEVER reuse a Premarket Score identity as `briefing_id`.  
Identity SHALL NEVER rewrite, invent, or synthesize upstream identities.  
Identity SHALL NOT use UUID, wall-clock, or mutable runtime state.

Later identity schemes SHALL be introduced as new Identity Specifications and bound by a new Policy Version. They SHALL NOT silently replace `morning-briefing.identity.v1` inside this Policy Version.

## Contract Invariants

The following repository contracts shall remain invariant throughout Policy Version v1 execution:

- Premarket Score semantic meaning  
- Premarket Score ordering  
- `score_record_id` values  
- score provenance references  
- Policy Version identity  
- explicit UTC `as_of`  

Implementation shall not modify these invariants at any stage of the Assembly Pipeline.

## Provenance

### Provenance Specification `morning-briefing.provenance.v1`

This subordinate specification defines concrete Morning Briefing provenance construction for Policy Version v1 outputs.

Governance Decision #6 remains schema-agnostic at Governance fidelity. Concrete provenance obligations live only here.

Every Morning Briefing output SHALL carry repository-governed provenance containing at least:

| Provenance element | Rule |
|--------------------|------|
| `policy_version_id` | `morning-briefing.policy.v1` |
| `ordering_preservation_policy_id` | `preserve_premarket_scoring_order.v1` |
| `identity_specification_id` | `morning-briefing.identity.v1` |
| `provenance_specification_id` | `morning-briefing.provenance.v1` |
| `as_of` | Explicit UTC timestamp of the evaluation |
| `config_fingerprint` | Deterministic fingerprint of validated Morning Briefing configuration + this Policy Version + bound subordinate specification IDs |
| `input_fingerprint` | Deterministic fingerprint of authorized inputs actually consumed, including ordered `score_record_id` sequence and upstream scoring collection provenance fingerprints |
| `source_identifiers` | Deterministic ordered identifiers of consumed Score Records (`score_record_id` sequence exactly as preserved) |
| Upstream score provenance linkage | Exact preserved score provenance references for every consumed Score Record |

Provenance SHALL preserve upstream provenance exactly as received.  
Provenance SHALL NEVER rewrite, invent, omit, or synthesize provenance.  
Provenance SHALL maintain complete lineage from briefing output to authorized inputs, configuration, Policy Version identity, and explicit UTC `as_of`.

Fingerprint digests SHALL use `canonical_payload_sha256_v1`.  
Source-identifier order MUST equal Ordering Preservation order.  
Input collection iteration artifacts outside the preserved scoring order MUST NOT affect fingerprints.

## Replay

Replay SHALL re-execute the Assembly Pipeline under pinned:

- authorized inputs  
- explicit UTC `as_of`  
- Policy Version identity `morning-briefing.policy.v1`  
- Morning Briefing configuration  

Replay SHALL reproduce identical:

- briefing identity  
- briefing provenance fingerprints  
- ordered score references  
- preserved score values  
- preserved score identities  
- preserved score provenance references  
- output post-validation result  

Replay SHALL NEVER depend on:

- wall-clock time  
- randomness  
- mutable runtime state  
- implementation discovery  
- external side effects  
- downstream consumers  

Replay inequality under identical pinned conditions SHALL fail closed.

## Output

### Output generation

After Identity Generation and Provenance Generation, Output Construction SHALL materialize exactly one Morning Briefing output for the evaluation.

The output SHALL remain presentation-neutral.  
The output SHALL NOT define UI, Dashboard, rendering, Markdown formatting, JSON schema, HTTP, APIs, persistence, storage, or notification delivery.

### Output contract

Each Morning Briefing output SHALL include at least:

| Element | Rule |
|---------|------|
| `briefing_id` | Deterministic identity per `morning-briefing.identity.v1` |
| `policy_version_id` | `morning-briefing.policy.v1` |
| `ordering_preservation_policy_id` | `preserve_premarket_scoring_order.v1` |
| `as_of` | Explicit UTC timestamp of the evaluation |
| Ordered briefing records | Zero or more records in Premarket Scoring order |
| Briefing provenance | Per `morning-briefing.provenance.v1` |

Each briefing record SHALL include at least:

| Element | Rule |
|---------|------|
| Sequence index | Zero-based index equal to Premarket Scoring collection index |
| `score_record_id` | Exact upstream identity |
| `instrument_key` | Exact upstream value |
| `local_symbol` | Exact upstream value, including null |
| `score` | Exact upstream finite `Decimal` in `[0, 1]` |
| Score component snapshot | Exact upstream values, including null absences |
| Scoring `policy_version_id` | `premarket.scoring.policy.v1` |
| Scoring `weight_profile_id` | Exact upstream value |
| Upstream score provenance | Exact upstream provenance references |

### Output preservation obligations

Output SHALL preserve:

- Morning Briefing semantic meaning under Governance Decision #1  
- Premarket Score semantic meaning under Premarket Scoring Governance Decision #1  
- Premarket Scoring ordering  
- Premarket Score identity references  
- Premarket Score provenance references  
- Morning Briefing identity and provenance  

Output SHALL NEVER become investment advice, Human Review, AI Decision Engine, or Broker Execution authority.

### Output Completeness

Successful emission shall produce exactly one complete Morning Briefing output.

Partial outputs, incremental outputs, or partially validated outputs are prohibited.

## Validation

### Pre-assembly validation

Performed by Input Validation, Policy Version Binding, PIT Validation, and Authorized Input Admission as specified above.

### Post-validation

Before emission, implementation SHALL validate all of the following:

1. `policy_version_id` equals `morning-briefing.policy.v1`  
2. `ordering_preservation_policy_id` equals `preserve_premarket_scoring_order.v1`  
3. `identity_specification_id` equals `morning-briefing.identity.v1`  
4. `provenance_specification_id` equals `morning-briefing.provenance.v1`  
5. `as_of` is present, UTC-aware, and equal to upstream scoring `as_of`  
6. Upstream scoring Policy Version equals `premarket.scoring.policy.v1`  
7. Briefing record count equals upstream Score Record count  
8. For every index `i`, briefing record `i` references upstream Score Record `i` with exact `score_record_id`, `score`, identity, and provenance preservation  
9. No score value has been mutated  
10. No independent ranking has been applied  
11. `briefing_id` matches `morning-briefing.identity.v1` over the canonical payload  
12. Briefing provenance is present and matches `morning-briefing.provenance.v1`  
13. Unauthorized inputs remain absent  
14. Premarket settings fail-closed when supplied and disabled  
15. Contract Invariants remain unmodified  
16. Bound configuration remains immutable throughout the evaluation  

Invalid outputs SHALL fail closed.  
No silent repair.

## Error Handling

v1 SHALL fail closed when any of the following occur:

- unauthorized input present  
- required input missing  
- Policy Version mismatch  
- PIT violation  
- upstream scoring Policy Version mismatch  
- missing or invalid upstream score identity  
- missing or invalid upstream score provenance  
- score domain violation visible in consumed records  
- ordering preservation violation  
- identity generation inputs incomplete  
- provenance generation inputs incomplete  
- Contract Invariant violation  
- Pipeline Isolation violation  
- Configuration Stability violation  
- Output Completeness violation  
- post-validation failure  
- replay inequality under identical pinned conditions  

Error handling rules:

1. No partial success for prohibited conditions.  
2. No silent substitution.  
3. No automatic repair.  
4. No fabrication, inference, or synthesis.  
5. Original failure context SHALL be preserved at Policy boundaries.

## Determinism

Identical:

- authorized inputs  
- Morning Briefing configuration  
- Policy Version identity `morning-briefing.policy.v1`  
- explicit UTC `as_of`  

SHALL always produce identical Morning Briefing outputs, including identical:

- `briefing_id`  
- briefing provenance fingerprints  
- ordered briefing records  
- preserved score values  
- preserved score identities  
- preserved score provenance references  

## Policy Constants

| Constant | Value |
|----------|-------|
| `policy_version_id` | `morning-briefing.policy.v1` |
| `ordering_preservation_policy_id` | `preserve_premarket_scoring_order.v1` |
| `identity_specification_id` | `morning-briefing.identity.v1` |
| `provenance_specification_id` | `morning-briefing.provenance.v1` |
| `digest_method_id` | `canonical_payload_sha256_v1` |
| Required upstream scoring Policy Version ID | `premarket.scoring.policy.v1` |
| Required upstream score Identity Specification ID | `premarket.score.identity.v1` |
| Score domain | Finite `Decimal` in closed interval `[0, 1]` as received from Premarket Scoring |
| Empty upstream score collection | Authorized; yields empty briefing records with valid briefing identity and provenance |

No additional constants are defined by this Policy Version.

## Default Configuration

| Setting | Default |
|---------|---------|
| `policy_version_id` | `morning-briefing.policy.v1` |
| `ordering_preservation_policy_id` | `preserve_premarket_scoring_order.v1` |
| `identity_specification_id` | `morning-briefing.identity.v1` |
| `provenance_specification_id` | `morning-briefing.provenance.v1` |
| `digest_method_id` | `canonical_payload_sha256_v1` |

Implementation SHALL consume these defaults exactly when this Policy Version is selected.  
Implementation SHALL NOT ambient-default a different Policy Version, ordering preservation policy, identity specification, provenance specification, or digest method.

## Version Compatibility

- This Policy Version is identified solely by `morning-briefing.policy.v1`  
- Evaluations MUST bind to exactly this Policy Version ID  
- Ordering Preservation Policy, Identity Specification, Provenance Specification, and Digest Method bound by this Policy Version are part of the concrete v1 contract  
- A different Policy Version ID or subordinate specification ID selects a different concrete behavior set and MUST NOT be treated as equivalent  

## Implementation Impact

This Policy Version authorizes deterministic implementation consistent with Morning Briefing Governance Decisions #1–#8.

Implementation SHALL remain fully subordinate to:

- Morning Briefing Governance Decisions #1–#8  
- Premarket Scoring Governance Decisions #1–#12  
- Premarket Scoring Policy Version `premarket.scoring.policy.v1`  
- Morning Briefing Architecture v1  
- Sprint 9 Planning Gate  

Implementation SHALL NOT redefine semantic meaning, expand authorized inputs, regenerate or reorder Premarket Scores, invent evidence, or bypass fail-closed, PIT, replay, identity, or provenance obligations.

This Policy Version does not authorize UI, Dashboard, Human Review, AI Decision Engine, Broker Execution, notification delivery, persistence, or transport mechanisms.

## Future Compatibility

Future Policy Versions may change:

- assembly algorithms within Governance bounds  
- validation sequence details within Governance bounds  
- identity algorithms via new Identity Specifications  
- provenance algorithms via new Provenance Specifications  
- output algorithms within Governance bounds  

Future Policy Versions SHALL preserve compatibility with Morning Briefing Governance Decisions #1–#8 and Premarket Scoring Governance Decisions #1–#12 unless those governance decisions are superseded by a subsequent approved Governance Decision.

Implementation changes alone SHALL NOT alter this Policy Version.  
Any change to v1 concrete behavior requires a new Policy Version ID and/or new subordinate specification IDs.

## Resolution

**Status:** APPROVED  

**Policy effect:** Deterministic Morning Briefing behavior under `morning-briefing.policy.v1` is frozen for Implementation Authorization and subsequent authorized implementation.
