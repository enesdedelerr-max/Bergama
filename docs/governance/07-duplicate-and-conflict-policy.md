## Duplicate & Conflict Policy

Status: RESOLVED

### Purpose

Freeze duplicate and conflict governance for Premarket Scoring Foundation v1.

This decision freezes how duplicate authorized evidence and conflicting authorized evidence must be governed. It does not freeze precedence rules, merge strategies, winner selection, deduplication algorithms, reconciliation algorithms, identity mechanics, provenance schema, ordering, tie-breaking, or Policy Version implementation.

### Repository Constraints

Decisions #1–#6 are RESOLVED.

- Decision #1: a Premarket Score is a deterministic Premarket attention / ordering-priority signal.
- Decision #2: emitted scores are finite `Decimal` values in `[0, 1]`; invalid domain values are rejected, not repaired.
- Decision #3: scoring consumes only repository-approved upstream Premarket contracts as frozen there.
- Decision #4: normalization shall not fabricate or silently repair evidence.
- Decision #5: weighting shall not fabricate evidence or silently repair invalid results; weights are governed exclusively by the frozen Policy Version.
- Decision #6: missing evidence shall never be fabricated, inferred, synthesized, or silently repaired.

No Premarket scoring duplicate and conflict policy exists yet. Concrete precedence, merge, and reconciliation mechanisms remain separate Policy Version or later Freeze concerns within these governance bounds.

### Decision

Duplicate & Conflict Policy governs only the governance of duplicate and conflicting authorized evidence.

Governance definitions:

- A **Duplicate** is multiple authorized representations of the same logical evidence.
- A **Conflict** is multiple authorized representations that cannot simultaneously be true under the same Policy Version.

These definitions are governance concepts only.

Duplicate and conflict governance for Policy Version v1 is frozen as follows:

1. **Scope**  
   Duplicate and conflict handling is a repository policy concern.  
   This decision does not govern missing input, weighting, normalization, aggregation, identity, provenance, ordering, tie-breaking, or policy versioning.

2. **No silent discard**  
   Duplicate evidence shall never be silently discarded.

3. **No silent reconciliation**  
   Conflicting evidence shall never be silently reconciled.

4. **No fabrication**  
   Implementation shall never fabricate, infer, synthesize, or otherwise invent evidence while processing duplicate or conflicting authorized evidence.

5. **Semantic boundary**  
   Duplicate and conflict handling must preserve Decision #1 semantic meaning.

6. **Domain boundary**  
   Duplicate and conflict handling must preserve Decision #2 score domain.

7. **Determinism**  
   Duplicate and conflict handling shall remain deterministic.  
   Identical authorized evidence, frozen configuration, frozen Policy Version, and explicit UTC `as_of` shall always produce the same governance decision.

8. **Replay**  
   Replay shall reproduce identical duplicate and conflict outcomes for identical authorized evidence under the same frozen Policy Version.  
   Accordingly, duplicate and conflict handling shall depend only on authorized evidence, frozen configuration, frozen Policy Version, and explicit UTC `as_of`.  
   Duplicate and conflict handling shall never depend on wall-clock time, randomness, or mutable runtime state.

9. **PIT**  
   Duplicate and conflict handling shall remain PIT-compatible.  
   Handling assumes Decision #3 PIT constraints remain in force.  
   It validates compatibility and does not repair PIT violations.

This decision does not define precedence, merge, winner selection, matching, or reconciliation algorithms.

### Implementation Impact

Implementation shall remain subordinate to the governance principles frozen by this decision.

Implementation may resolve duplicate or conflicting evidence only through behavior defined by the applicable frozen Policy Version and consistent with this Policy Freeze.

Implementation shall not introduce implementation-specific behavior outside the approved governance boundary.

Concrete precedence rules, merge algorithms, duplicate elimination, conflict resolution algorithms, and reconciliation behavior remain blocked until approved by a subsequent Policy Version or Policy Freeze.

### Future Compatibility

Future Policy Versions may introduce different duplicate and conflict handling mechanisms.

They may not change the governance principles frozen here without a new approved Policy Freeze.

Such changes shall preserve compatibility with Decisions #1–#6 unless superseded by an approved governance change.

The governance boundary defined by this decision is immutable for Policy Version v1.

Any modification to these governance principles requires a subsequent approved Policy Freeze and shall not occur through implementation changes or Policy Version configuration alone.