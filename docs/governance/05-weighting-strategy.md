## Weighting Strategy

Status: RESOLVED

### Purpose

Freeze weighting governance for Premarket Scoring Foundation v1.

This decision freezes how weights must behave as a policy boundary. It does not freeze numeric weights, percentages, default weight tables, formulas, equations, algorithms, automatic weight normalization, missing-input arithmetic, Decimal precision, identity, provenance schema, or policy-version implementation mechanics.

### Repository Constraints

Decisions #1–#4 are RESOLVED.

- Decision #1: a Premarket Score is a deterministic Premarket attention / ordering-priority signal.
- Decision #2: emitted scores are finite `Decimal` values in `[0, 1]`; invalid domain values are rejected, not repaired.
- Decision #3: scoring consumes only repository-approved upstream Premarket contracts as frozen there.
- Decision #4: normalization is deterministic, monotonic, non-fabricating, fail-closed, PIT-compatible, and replay-safe.

No Premarket scoring weighting policy exists yet. Concrete coefficients, formulas, and Decimal precision remain separate Policy Freeze or Policy Version concerns.

### Decision

Weighting governs how normalized authorized components contribute to the final Premarket Score under a frozen Policy Version.

Weighting is a policy concern, not an implementation concern.

Weighting governance for Policy Version v1 is frozen as follows:

1. **Policy ownership**
   Weights are governed exclusively by the frozen Policy Version. Implementation may consume weights, but it may never define, infer, or substitute them.

2. **Authorized scope**
   Weights apply only to normalized components derived from authorized inputs under Decisions #3 and #4. Weights never expand authorized inputs.

3. **Semantic boundary**
   Weights never redefine Decision #1 semantic meaning.

4. **Domain boundary**
   Weights never change Decision #2 score domain. Emitting a score outside `[0, 1]`, or silently repairing an out-of-domain result, is prohibited.

5. **No fabrication**
   Weights never fabricate missing upstream evidence or invent components that are not grounded in authorized normalized inputs.

6. **No silent repair**
   Weights never silently repair invalid normalized components or invalid weighted results by clamping, coercing, inventing, or otherwise rewriting them into validity.

7. **Determinism**
   Weighting shall be deterministic. Identical normalized authorized inputs, frozen configuration, frozen Policy Version, and explicit UTC `as_of` shall produce identical weighted results eligible for score emission.

8. **Replay**
   Weighting output must depend only on authorized normalized inputs, frozen configuration, frozen Policy Version, and explicit UTC `as_of`. It must never depend on wall-clock time, randomness, or mutable runtime state.

9. **PIT**
   Weighting assumes authorized inputs and normalized components already satisfy repository PIT guarantees and Decision #4 constraints. Weighting validates compatibility. Weighting does not repair PIT violations.

This decision does not select a weighting algorithm and does not define numeric weights, percentages, formulas, coefficients, automatic renormalization rules, single-input behavior, all-inputs-missing behavior, Decimal quantize rules, duplicate/conflict handling, identity, or provenance schema.

### Implementation Impact

Implementation may use any weighting algorithm that satisfies these governance principles and is frozen by the applicable Policy Version.

Implementation must not reinterpret governance, invent ambient weights outside the frozen Policy Version, expand inputs, redefine score meaning, alter score domain, fabricate evidence, silently repair invalid results, or depend on wall-clock time, randomness, or mutable runtime state.

Concrete coefficients, formulas, missing-input arithmetic, and Decimal precision remain blocked until their own Freeze Decisions or Policy Version records are resolved.

### Future Compatibility

Future Policy Versions may change algorithms, coefficients, formulas, optimization methods, and weighting models.

Future Policy Versions may not change the governance principles frozen here without a new Policy Freeze.

Weighting remains subordinate to Decisions #1–#4 across Policy Versions.

The governance boundary defined by this decision is immutable for Policy Version v1.

Any modification to these governance principles requires a subsequent approved Policy Freeze and shall not occur through implementation changes or Policy Version configuration alone.