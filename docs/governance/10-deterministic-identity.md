## Deterministic Identity

Status: RESOLVED

### Purpose

Freeze deterministic identity governance for Premarket Scoring Foundation v1 outputs.

This decision freezes the governance principles that define identity of Premarket Scoring outputs as deterministic and replay-safe. It does not freeze identity algorithms, hash functions, UUIDs, GUIDs, database IDs, primary keys, encoding, serialization, or storage.

### Repository Constraints

Decisions #1–#9 are RESOLVED.

- Decision #1: a Premarket Score is a deterministic Premarket attention / ordering-priority signal.
- Decision #2: emitted scores are finite `Decimal` values in `[0, 1]`.
- Decision #3: scoring consumes only repository-approved upstream Premarket contracts under explicit UTC `as_of`.
- Decision #4–#8: normalization, weighting, missing-input, duplicate/conflict, and PIT aggregation remain policy-owned, deterministic, and non-fabricating.
- Decision #9: every scoring decision is associated with exactly one immutable Policy Version identity.

Premarket foundations use deterministic sha256 identities as repository convention. This Freeze does not adopt or require any specific algorithm. Concrete identity algorithms and encodings remain separate Policy Version or later Freeze concerns within these governance bounds.

### Decision

Deterministic Identity governs only the governance of Premarket Scoring output identity.

Governance definition:

- **Deterministic Identity** means a stable identity for a Premarket Scoring output that is fully determined by repository-approved governance inputs and is reproducible under replay.

This definition is a governance concept only.

Deterministic identity governance for Policy Version v1 is frozen as follows:

1. **Scope**  
   This decision does not govern identity algorithms, identity encoding, storage, serialization, database keys, UUID generation, or hash functions.

2. **Determinism**  
   Identity shall be deterministic.  
   Identical authorized evidence, Policy Version, configuration, and explicit UTC `as_of` shall produce identical identity.

3. **No silent reuse**  
   Different governance inputs shall not silently reuse identity.

4. **Semantic boundary**  
   Identity shall preserve Decision #1 semantic meaning and shall not redefine it.

5. **Domain boundary**  
   Identity shall preserve Decision #2 score domain and shall not alter it.

6. **Input and policy boundary**  
   Identity shall preserve Decisions #3–#9 and shall not expand authorized inputs, fabricate evidence, or reinterpret Policy Version identity through identity alone.

7. **Replay**  
   Identity shall remain replay-safe.  
   Replay shall reproduce identical identities for identical authorized evidence under the same frozen Policy Version.  
   Accordingly, identity shall depend only on authorized evidence, frozen configuration, frozen Policy Version, and explicit UTC `as_of`.  
   Identity shall never depend on wall-clock time, randomness, or mutable runtime state.

8. **PIT**  
   Identity shall remain PIT-compatible.  
   Identity assumes Decision #3 and Decision #8 PIT constraints remain in force.  
   It validates compatibility and does not repair PIT violations.

This decision does not define identity algorithms, encodings, serialization, storage, or UUID generation.

### Implementation Impact

Implementation shall remain subordinate to the governance principles frozen by this decision.

Implementation may generate identities only through behavior defined by the applicable frozen Policy Version and consistent with this Policy Freeze.

Implementation shall not introduce implementation-specific identity behavior outside the approved governance boundary.

Identity generation algorithms remain blocked until approved by a subsequent Policy Version or Policy Freeze.

### Future Compatibility

Future Policy Versions may introduce different identity mechanisms.

They may not change the governance principles frozen here without a new approved Policy Freeze.

Such changes shall preserve compatibility with Decisions #1–#9 unless superseded by an approved governance change.

The governance boundary defined by this decision is immutable for Policy Version v1.

Any modification to these governance principles requires a subsequent approved Policy Freeze and shall not occur through implementation changes or Policy Version configuration alone.