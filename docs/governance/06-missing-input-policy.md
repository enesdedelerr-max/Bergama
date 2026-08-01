## Missing Input Policy

Status: RESOLVED

### Purpose

Freeze missing-input governance for Premarket Scoring Foundation v1.

This decision freezes how the existence or absence of authorized inputs must be governed. It does not freeze recovery algorithms, default values, imputation, weight redistribution, duplicate handling, conflict resolution, aggregation, weighting mechanics, identity, provenance schema, or Decimal precision.

### Repository Constraints

Decisions #1–#5 are RESOLVED.

- Decision #1: a Premarket Score is a deterministic Premarket attention / ordering-priority signal.
- Decision #2: emitted scores are finite `Decimal` values in `[0, 1]`; invalid domain values are rejected, not repaired.
- Decision #3: Watchlist is required; Catalyst and Gap collections are authorized optional; explicit UTC `as_of` and scoring configuration are required.
- Decision #4: normalization shall not fabricate or silently repair evidence.
- Decision #5: weighting shall not fabricate evidence or silently repair invalid results; weights are governed exclusively by the frozen Policy Version.

No Premarket scoring missing-input policy exists yet. Concrete reject/defer/continue mechanisms remain separate Policy Version or later Freeze concerns within these governance bounds.

### Decision

Missing Input Policy governs only the existence of authorized inputs under Decision #3.

Missing-input governance for Policy Version v1 is frozen as follows:

1. **Scope**
   Authorized inputs may be missing. This decision governs absence of authorized inputs only. It does not govern duplicate handling, conflict resolution, aggregation, weighting, identity, provenance, or Decimal precision.

2. **No fabrication**
   Missing evidence shall never be fabricated.

3. **No inference**
   Missing evidence shall never be inferred.

4. **No synthesis**
   Missing evidence shall never be synthesized, imputed, interpolated, estimated, predicted, or otherwise invented.

5. **No silent repair**
   Implementation shall not silently repair missing inputs by introducing values that are not explicitly authorized by repository policy.
   Examples include defaults, fallbacks, null replacements, redistributed weights, or other implementation-defined substitutions.

6. **Semantic boundary**
   Missing-input handling must preserve Decision #1 semantic meaning.

7. **Domain boundary**
   Missing-input handling must preserve Decision #2 score domain. Absence of evidence must never produce silent domain repair.

8. **Determinism**
   Missing-input handling must remain deterministic under identical authorized input presence/absence, frozen configuration, frozen Policy Version, and explicit UTC `as_of`.

9. **Replay**
   Replay shall reproduce identical missing-input outcomes for identical authorized input presence/absence under the same frozen Policy Version.
   Accordingly, missing-input handling shall depend only on authorized input presence/absence, frozen configuration, frozen Policy Version, and explicit UTC `as_of`.
   Missing-input handling shall never depend on wall-clock time, randomness, or mutable runtime state.

10. **PIT**
    Missing-input handling must remain PIT-compatible. It assumes Decision #3 PIT constraints remain in force. It validates compatibility and does not repair PIT violations.

This decision does not define which optional absences are acceptable, which absences fail closed, or any recovery, continuation, or scoring arithmetic for partial input sets.

### Implementation Impact

Implementation shall remain subordinate to the governance principles frozen by this decision.

Implementation may only apply repository-approved missing-input handling defined by the applicable frozen Policy Version.

Implementation shall not introduce implementation-specific behavior outside the approved governance boundary.

Concrete reject/defer/continue rules, recovery algorithms, and partial-input arithmetic remain blocked until recorded by an approved Policy Version or subsequent Freeze within these principles.

### Future Compatibility

Future Policy Versions may introduce different missing-input handling mechanisms.

They may not change the governance principles frozen here without a new approved Policy Freeze.

Such changes shall preserve compatibility with Decisions #1–#5 unless superseded by an approved governance change.

The governance boundary defined by this decision is immutable for Policy Version v1.

Any modification to these governance principles requires a subsequent approved Policy Freeze and shall not occur through implementation changes or Policy Version configuration alone.