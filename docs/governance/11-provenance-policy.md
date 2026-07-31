## Provenance Policy

Status: RESOLVED

### Purpose

Freeze provenance governance for Premarket Scoring Foundation v1.

This decision freezes the governance principles that define provenance requirements for Premarket Scores. It does not freeze metadata schema, database tables, logging, audit storage, serialization, or implementation fields.

### Repository Constraints

Decisions #1–#10 are RESOLVED.

- Decision #1: a Premarket Score is a deterministic Premarket attention / ordering-priority signal.
- Decision #2: emitted scores are finite `Decimal` values in `[0, 1]`.
- Decision #3: scoring consumes only repository-approved upstream Premarket contracts under explicit UTC `as_of`; inputs must be provenance-traceable to approved upstream Premarket contracts.
- Decision #4–#8: normalization, weighting, missing-input, duplicate/conflict, and PIT aggregation remain policy-owned, deterministic, and non-fabricating.
- Decision #9: every scoring decision is associated with exactly one immutable Policy Version identity.
- Decision #10: Premarket Scoring output identity is deterministic and replay-safe.

Premarket foundations carry config/input fingerprints and source identifiers as repository convention. This Freeze does not adopt a concrete schema. Concrete provenance schemas and storage remain separate Policy Version or later Freeze concerns within these governance bounds.

### Decision

Provenance Policy governs only provenance governance for Premarket Scoring outputs.

Governance definition:

- **Provenance** means repository-governed evidence of the governance context and authorized inputs that produced a Premarket Score, sufficient to support audit and replay without fabricating history.

This definition is a governance concept only.

Provenance governance for Policy Version v1 is frozen as follows:

1. **Scope**  
   This decision does not govern metadata schema, logging, storage, database, serialization, or implementation fields.

2. **Presence**  
   Every Premarket Score shall have repository-governed provenance.

3. **Governance context**  
   Provenance shall identify the governance context used, including association with the applicable Policy Version under Decision #9.

4. **No fabrication**  
   Provenance shall never fabricate evidence.  
   Provenance shall never infer, synthesize, or invent history that was not produced by authorized scoring evaluation.

5. **Semantic boundary**  
   Provenance shall preserve Decision #1 semantic meaning and shall not redefine it.

6. **Domain boundary**  
   Provenance shall preserve Decision #2 score domain and shall not alter it.

7. **Compatibility**  
   Provenance shall remain compatible with Decisions #1–#10.

8. **Determinism**  
   Provenance shall remain deterministic.  
   Identical authorized evidence, frozen configuration, frozen Policy Version, and explicit UTC `as_of` shall always produce the same provenance outcome.

9. **Replay**  
   Replay shall preserve provenance.  
   Replay shall reproduce identical provenance outcomes for identical authorized evidence under the same frozen Policy Version.  
   Accordingly, provenance shall depend only on authorized evidence, frozen configuration, frozen Policy Version, and explicit UTC `as_of`.  
   Provenance shall never depend on wall-clock time, randomness, or mutable runtime state.

10. **PIT**  
    Provenance shall remain PIT-compatible.  
    Provenance assumes Decision #3 and Decision #8 PIT constraints remain in force.  
    It validates compatibility and does not repair PIT violations.

This decision does not define provenance schemas, field layouts, logging sinks, storage, or serialization formats.

### Implementation Impact

Implementation shall remain subordinate to the governance principles frozen by this decision.

Implementation shall preserve repository-approved provenance.

Implementation shall not reinterpret provenance.

Implementation may emit provenance only through behavior defined by the applicable frozen Policy Version and consistent with this Policy Freeze.

Implementation shall not introduce implementation-specific provenance behavior outside the approved governance boundary.

Schema and storage remain blocked until approved by a subsequent Policy Version or Policy Freeze.

### Future Compatibility

Future Policy Versions may extend provenance.

They may not change the governance principles frozen here without a new approved Policy Freeze.

Such changes shall preserve compatibility with Decisions #1–#10 unless superseded by an approved governance change.

The governance boundary defined by this decision is immutable for Policy Version v1.

Any modification to these governance principles requires a subsequent approved Policy Freeze and shall not occur through implementation changes or Policy Version configuration alone.