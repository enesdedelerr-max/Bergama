## Normalization Strategy

Status: RESOLVED

### Purpose

Freeze normalization governance for Premarket Scoring Foundation v1.

This decision freezes how normalization must behave as a policy boundary. It does not freeze algorithms, formulas, coefficients, Decimal precision, weighting, aggregation, ranking, identity, provenance schema, or missing-input arithmetic.

### Repository Constraints

Decisions #1–#3 are RESOLVED.

- Decision #1: a Premarket Score is a deterministic Premarket attention / ordering-priority signal.
- Decision #2: emitted scores are finite `Decimal` values in `[0, 1]`; invalid domain values are rejected, not repaired.
- Decision #3: scoring consumes only repository-approved upstream Premarket contracts as frozen there.

No Premarket scoring normalization policy exists yet. Algorithm selection and Decimal precision remain separate Policy Freeze decisions.

### Decision

Normalization converts authorized upstream Premarket evidence into comparable scoring components under the frozen policy.

Normalization governance for Policy Version v1 is frozen as follows:

1. **Boundary**
   Normalization operates only on authorized inputs from Decision #3. It does not redefine Decision #1 semantic meaning and does not expand Decision #2 score domain.

2. **Determinism**
   Normalization shall be deterministic. Identical authorized inputs, frozen configuration, frozen policy version, and explicit UTC `as_of` shall produce identical normalized components.

3. **Monotonicity**
   Normalization shall preserve ordering: for any comparable upstream evidence relation that the frozen policy treats as higher Premarket attention evidence, the normalized component must not reverse that ordering.

4. **Bounded compatibility**
   Normalization shall remain compatible with Decision #2. Normalized components used to form an emitted Premarket Score must not require silent domain repair to fit `[0, 1]`.

5. **No fabrication**
   Normalization shall never fabricate missing upstream evidence or invent values not grounded in authorized inputs.

6. **No silent repair**
   Normalization shall never silently repair invalid upstream evidence or invalid normalized values by clamping, coercing, inventing, or otherwise rewriting them into validity.

7. **Invalid values**
   Invalid normalized values are fail-closed. Invalid upstream evidence cannot become valid through normalization. Error handling follows repository fail-closed policy.

8. **PIT**
   Normalization assumes authorized inputs already satisfy repository PIT guarantees. Normalization validates compatibility with explicit UTC `as_of`. Normalization does not repair PIT violations.

9. **Replay**
   Normalization output must depend only on authorized inputs, frozen configuration, frozen policy version, and explicit UTC `as_of`. It must never depend on wall-clock time, randomness, or mutable runtime state.

This decision does not select a normalization algorithm and does not define formulas, coefficients, scaling constants, Decimal quantize rules, duplicate/conflict handling, missing-input arithmetic, weighting, aggregation, or ranking.

### Implementation Impact

Implementation must apply only a normalization algorithm later frozen by Policy Version / Policy Freeze, and must obey the governance principles above. Implementation must not invent alternate normalization behavior, silently repair invalid values, fabricate evidence, depend on wall-clock or randomness, or treat normalization as authority to expand inputs, redefine score meaning, or alter score domain. Algorithm choice, Decimal precision, missing-input arithmetic, and weighting remain blocked until their own Freeze Decisions are resolved.

### Future Compatibility

Future policy versions may change the normalization algorithm.

Future policy versions may not change the governance principles frozen here without a new Policy Freeze.

Normalization remains subordinate to Decisions #1–#3 across policy versions.