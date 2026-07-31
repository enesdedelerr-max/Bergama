## Policy Version & Identity

Status: RESOLVED

### Purpose

Freeze Policy Version identity governance for Premarket Scoring Foundation v1.

This decision freezes the governance principles that define Policy Version as the immutable identity of the scoring governance rules in force. It does not freeze version format, semantic versioning, numbering schemes, storage, Git tags, database schema, migration strategy, or implementation identifiers.

### Repository Constraints

Decisions #1–#8 are RESOLVED.

- Decision #1: a Premarket Score is a deterministic Premarket attention / ordering-priority signal.
- Decision #2: emitted scores are finite `Decimal` values in `[0, 1]`; invalid domain values are rejected, not repaired.
- Decision #3: scoring consumes only repository-approved upstream Premarket contracts; explicit UTC `as_of` and explicit scoring configuration identifying frozen policy version are required.
- Decision #4–#8: normalization, weighting, missing-input, duplicate/conflict, and PIT aggregation behavior are governed exclusively by the frozen Policy Version and these Freeze principles.

No Premarket scoring Policy Version identity policy exists yet. Concrete version formats, identifiers, storage, and migration mechanics remain separate Policy Version or later Freeze concerns within these governance bounds.

### Decision

Policy Version & Identity governs only Policy Version identity governance.

Governance definition:

- **Policy Version** is a repository governance identity that uniquely identifies the Premarket Scoring governance rules in force for a scoring evaluation.

This definition is a governance concept only.

Policy Version identity governance for Policy Version v1 is frozen as follows:

1. **Scope**  
   Policy Version is a repository governance identity.  
   This decision does not govern algorithms, configuration contents, implementation, identity generation for score records, provenance, ordering, tie-breaking, storage, or migration.

2. **Association**  
   Every scoring decision shall be associated with exactly one Policy Version.

3. **Immutability**  
   Policy Version identity shall be immutable once assigned to a scoring evaluation.

4. **Uniqueness of governance rules**  
   Policy Version identity shall uniquely identify the governance rules used for that evaluation.

5. **Semantic boundary**  
   Policy Version identity shall preserve Decision #1 semantic meaning and shall not redefine it.

6. **Domain boundary**  
   Policy Version identity shall preserve Decision #2 score domain and shall not alter it.

7. **Authorized-input boundary**  
   Policy Version identity shall preserve Decision #3 authorized-input boundary and shall not expand it through identity alone.

8. **Determinism**  
   Policy Version association shall remain deterministic.  
   Identical authorized evidence, frozen configuration, frozen Policy Version, and explicit UTC `as_of` shall always produce the same Policy Version association outcome.

9. **Replay**  
   Replay shall use the identical Policy Version.  
   Replay shall reproduce identical Policy Version association outcomes for identical authorized evidence under the same frozen Policy Version.  
   Accordingly, Policy Version association shall depend only on authorized evidence, frozen configuration, frozen Policy Version, and explicit UTC `as_of`.  
   Policy Version association shall never depend on wall-clock time, randomness, or mutable runtime state.

10. **Compatibility**  
    Policy Version shall preserve compatibility with Decisions #1–#8.

This decision does not define version format, numbering, semantic versioning, storage, migration, or implementation identifiers.

### Implementation Impact

Implementation shall remain subordinate to the frozen Policy Version governance.

Implementation shall not reinterpret Policy Version identity.

Implementation may associate scoring evaluations with a Policy Version only through behavior defined by the applicable frozen Policy Version and consistent with this Policy Freeze.

Implementation shall not introduce implementation-specific Policy Version identity behavior outside the approved governance boundary.

Concrete version formats, identifiers, storage, migration, and implementation mechanics remain blocked until approved by a later Policy Version or Policy Freeze.

### Future Compatibility

Future Policy Versions may introduce new governance.

They shall not modify immutable Policy Version governance without a new approved Policy Freeze.

Such changes shall preserve compatibility with Decisions #1–#8 unless superseded by an approved governance change.

The governance boundary defined by this decision is immutable for Policy Version v1.

Any modification to these governance principles requires a subsequent approved Policy Freeze and shall not occur through implementation changes or Policy Version configuration alone.