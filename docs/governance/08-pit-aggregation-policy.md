## PIT Aggregation Policy

Status: RESOLVED

### Purpose

Freeze Point-in-Time (PIT) aggregation governance for Premarket Scoring Foundation v1.

This decision freezes the governance principles that apply when authorized evidence is aggregated under a common Point-in-Time (PIT) context. It does not freeze aggregation algorithms, formulas, windows, weighting, normalization, ordering, precedence, identity, provenance schema, or Policy Version implementation.

### Repository Constraints

Decisions #1–#7 are RESOLVED.

- Decision #1: a Premarket Score is a deterministic Premarket attention / ordering-priority signal.
- Decision #2: emitted scores are finite `Decimal` values in `[0, 1]`; invalid domain values are rejected, not repaired.
- Decision #3: scoring consumes only repository-approved upstream Premarket contracts; explicit UTC `as_of` is required; PIT compliance is validated and not repaired.
- Decision #4: normalization shall not fabricate or silently repair evidence and remains PIT-compatible.
- Decision #5: weighting shall not fabricate evidence or silently repair invalid results; weights are governed exclusively by the frozen Policy Version.
- Decision #6: missing evidence shall never be fabricated, inferred, synthesized, or silently repaired.
- Decision #7: duplicate evidence shall never be silently discarded; conflicting evidence shall never be silently reconciled; fabrication while processing duplicates or conflicts is prohibited.

No Premarket scoring PIT aggregation policy exists yet. Concrete aggregation algorithms, windows, and execution mechanics remain separate Policy Version or later Freeze concerns within these governance bounds.

### Decision

PIT Aggregation Policy governs only PIT aggregation governance.

Governance definitions:

- **Aggregation** means evaluating multiple authorized evidence items together under a common Point-in-Time context for Premarket Scoring.
- **Point-in-Time (PIT)** means all participating evidence is evaluated relative to the same explicit UTC `as_of` defined by Decision #3.

These definitions are governance concepts only.

PIT aggregation governance for Policy Version v1 is frozen as follows:

1. **Scope**  
   Aggregation is a repository policy concern.  
   This decision does not govern normalization, weighting, duplicate handling, conflict handling, missing input, identity, provenance, ordering, tie-breaking, or policy versioning.

2. **Authorized evidence only**  
   Aggregation shall consume only repository-authorized evidence permitted under Decision #3.  
   All participating evidence shall satisfy the common Point-in-Time context defined by this decision.

3. **Common PIT context**  
   Aggregation shall occur only within a common Point-in-Time context defined by a single explicit UTC `as_of`.  
   Aggregation shall never combine authorized evidence originating from different logical PIT contexts unless explicitly authorized by repository policy.

4. **No fabrication**  
   Aggregation shall never fabricate evidence.

5. **No inference**  
   Aggregation shall never infer evidence.

6. **No synthesis**  
   Aggregation shall never synthesize evidence.

7. **No silent PIT repair**  
   Aggregation shall never silently repair invalid PIT relationships.

8. **Semantic boundary**  
   Aggregation shall preserve Decision #1 semantic meaning.

9. **Domain boundary**  
   Aggregation shall preserve Decision #2 score domain.

10. **Determinism**  
    Aggregation shall remain deterministic.  
    Identical authorized evidence, frozen configuration, frozen Policy Version, and explicit UTC `as_of` shall always produce the same aggregation outcome.

11. **Replay**  
    Replay shall reproduce identical aggregation outcomes for identical authorized evidence under the same frozen Policy Version.  
    Accordingly, aggregation shall depend only on authorized evidence, frozen configuration, frozen Policy Version, and explicit UTC `as_of`.  
    Aggregation shall never depend on wall-clock time, randomness, or mutable runtime state.

12. **PIT**  
    Aggregation shall remain PIT-compatible.  
    Aggregation assumes Decision #3 PIT constraints remain in force.  
    It validates compatibility and does not repair PIT violations.

This decision does not define aggregation algorithms, formulas, aggregation windows, ordering, precedence, partial-aggregation arithmetic, or execution mechanics.

### Implementation Impact

Implementation shall remain subordinate to the governance principles frozen by this decision.

Implementation may aggregate authorized evidence only through behavior defined by the applicable frozen Policy Version and consistent with this Policy Freeze.

Implementation shall not introduce implementation-specific aggregation behavior outside the approved governance boundary.

Concrete aggregation algorithms, formulas, aggregation windows, ordering behavior, partial aggregation rules, and execution mechanics remain blocked until approved by a subsequent Policy Version or Policy Freeze.

### Future Compatibility

Future Policy Versions may introduce different aggregation mechanisms.

They may not change the governance principles frozen here without a new approved Policy Freeze.

Such changes shall preserve compatibility with Decisions #1–#7 unless superseded by an approved governance change.

The governance boundary defined by this decision is immutable for Policy Version v1.

Any modification to these governance principles requires a subsequent approved Policy Freeze and shall not occur through implementation changes or Policy Version configuration alone.