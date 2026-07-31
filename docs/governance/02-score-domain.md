## Score Domain

Status: RESOLVED

### Purpose

Define the immutable mathematical domain of a Premarket Score for Premarket Scoring Foundation v1.

### Repository Constraints

Decision #1 defines a Premarket Score as a deterministic Premarket attention signal expressing relative ordering priority within the evaluated Premarket universe. Premarket foundations use Decimal for quantitative values and forbid nondeterministic or non-finite numeric behavior in replayable paths. No Premarket score domain exists yet. Weighting, normalization, formulas, and Decimal quantize policy remain separate Policy Freeze decisions.

### Decision

A Premarket Score is a bounded, finite `Decimal` value in the closed interval `[0, 1]`.

This decision defines only the mathematical domain.

Decimal precision, scale, quantization, and rounding remain governed exclusively by the Decimal Precision & Rounding Policy Freeze decision.

Domain rules:

- Lower bound: `0` inclusive
- Upper bound: `1` inclusive
- Numeric type: finite `Decimal` only
- Negative values: not allowed
- `null` / missing: not allowed
- Non-finite values (`NaN`, `+Infinity`, `-Infinity`): not allowed
- Ties: legal; equal scores are permitted
- Ordering semantics: higher score always means higher Premarket ordering priority under Decision #1
- Comparison rules: compare scores by the total order of their finite `Decimal` values in `[0, 1]`; `a > b` means `a` has higher priority than `b`; `a == b` is a legal tie

A Premarket Score domain value is not:

- a probability
- a percentile claim unless a future frozen policy explicitly maps into this domain as such
- an unbounded ranking index
- a floating-point binary value

### Implementation Impact

Implementation must emit only finite `Decimal` scores in `[0, 1]`. Values outside the domain, non-finite values, nulls, and binary floating-point score storage are fail-closed errors. Implementation must reject invalid score values rather than clamp, normalize, round, or silently repair them. Comparison and sorting by score must use Decimal total order with higher-is-higher-priority semantics. Legal ties must be preserved for the separate frozen ordering/tie-break policy. Implementation must not redefine the domain while implementing formulas, weights, or normalization.

### Future Compatibility

The score domain is immutable across policy versions.

Future policy versions may change how scores are computed, but every emitted Premarket Score must remain a finite `Decimal` in `[0, 1]` with higher-is-higher-priority semantics. Future consumers may rely on this domain and comparison rule without reinterpretation.