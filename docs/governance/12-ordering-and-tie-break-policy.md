## Ordering & Tie-Break Policy

Status: RESOLVED

### Purpose

Freeze ordering and tie-break governance for Premarket Scoring Foundation v1.

This decision freezes the governance principles that apply when Premarket Scores are ordered and when equal scores require tie-breaking. It does not freeze sorting algorithms, comparison algorithms, ranking formulas, precedence tables, or stable-sort implementation.

### Repository Constraints

Decisions #1–#11 are RESOLVED.

- Decision #1: a Premarket Score expresses deterministic relative ordering priority within the evaluated Premarket universe.
- Decision #2: scores are finite `Decimal` values in `[0, 1]`; higher score means higher ordering priority; ties are legal.
- Decision #3–#8: authorized inputs, normalization, weighting, missing-input, duplicate/conflict, and PIT aggregation remain policy-owned, deterministic, and non-fabricating.
- Decision #9–#11: Policy Version identity, deterministic output identity, and provenance remain immutable, deterministic, and replay-safe.

No Premarket scoring ordering and tie-break policy exists yet. Concrete ordering algorithms and tie-break sequences remain separate Policy Version or later Freeze concerns within these governance bounds.

### Decision

Ordering & Tie-Break Policy governs only ordering and tie-break governance for Premarket Score collections.

Governance definitions:

- **Ordering** means producing a deterministic total order for Premarket Scores under a frozen Policy Version.
- **Tie-breaking** means resolving legal equal scores into a deterministic total order without redefining score meaning or score domain.

These definitions are governance concepts only.

Ordering and tie-break governance for Policy Version v1 is frozen as follows:

1. **Scope**  
   Ordering is a repository governance concern.  
   This decision does not govern sorting algorithms, ranking formulas, comparison implementation, stable-sort algorithms, or execution order.

2. **Score-priority boundary**  
   Ordering shall preserve Decision #1 semantic meaning.  
   Ordering shall preserve Decision #2 score domain and higher-is-higher-priority comparison semantics.  
   Legal ties under Decision #2 shall not be silently treated as unequal scores.

3. **Determinism**  
   Ordering shall be deterministic.  
   Tie-breaking shall be deterministic.  
   Identical authorized evidence, frozen configuration, frozen Policy Version, and explicit UTC `as_of` shall always produce the same ordering and tie-break outcome.

4. **No fabrication**  
   Ordering and tie-breaking shall never fabricate, infer, synthesize, or invent evidence or score values to force an order.

5. **No silent repair**  
   Ordering and tie-breaking shall never silently repair invalid scores, invalid identities, or invalid provenance to continue ordering.

6. **Compatibility**  
   Ordering shall remain compatible with Decisions #1–#11.

7. **Replay**  
   Replay shall preserve ordering.  
   Replay shall reproduce identical ordering and tie-break outcomes for identical authorized evidence under the same frozen Policy Version.  
   Accordingly, ordering and tie-breaking shall depend only on authorized evidence, frozen configuration, frozen Policy Version, and explicit UTC `as_of`.  
   Ordering and tie-breaking shall never depend on wall-clock time, randomness, or mutable runtime state.

8. **PIT**  
   Ordering and tie-breaking shall remain PIT-compatible.  
   Handling assumes Decision #3 and Decision #8 PIT constraints remain in force.  
   It validates compatibility and does not repair PIT violations.

This decision does not define sorting algorithms, ranking formulas, precedence tables, comparison implementations, or stable-sort mechanics.

### Implementation Impact

Implementation shall remain subordinate to the governance principles frozen by this decision.

Implementation may order Premarket Scores only through behavior defined by the applicable frozen Policy Version and consistent with this Policy Freeze.

Implementation shall not introduce implementation-specific ordering or tie-break behavior outside the approved governance boundary.

Ordering algorithms remain blocked until approved by a subsequent Policy Version or Policy Freeze.

### Future Compatibility

Future Policy Versions may introduce different ordering mechanisms.

They may not change the governance principles frozen here without a new approved Policy Freeze.

Such changes shall preserve compatibility with Decisions #1–#11 unless superseded by an approved governance change.

The governance boundary defined by this decision is immutable for Policy Version v1.

Any modification to these governance principles requires a subsequent approved Policy Freeze and shall not occur through implementation changes or Policy Version configuration alone.