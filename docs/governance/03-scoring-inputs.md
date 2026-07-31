## Scoring Inputs

Status: RESOLVED

### Purpose

Freeze which inputs Premarket Scoring Foundation v1 is authorized to consume.

This decision freezes **what** may enter scoring. It does not define how scores are computed.

Weighting, normalization, formulas, aggregation, ranking algorithms, missing-input arithmetic, and Decimal precision remain separate Policy Freeze decisions.

### Repository Constraints

Decisions #1 and #2 are RESOLVED. Premarket Scoring is a Premarket-internal attention / ordering-priority signal with domain `[0, 1]`.

Completed upstream Premarket foundations on `main` are Watchlist, Catalyst, and Gap Scanner. Planning Gate requires that scoring consume only repository-approved upstream Premarket contracts as defined by the frozen scoring policy. No dedicated Premarket Scoring input contract exists yet. Scoring consumes existing repository-approved upstream Premarket contracts as frozen by this decision.

This decision must not authorize new upstream capabilities, invent contracts/services/persistence/APIs, expand Strategy SDK, redefine Feature Platform, or change Market Data contracts.

### Authorized Inputs

v1 may consume only the following:

| Input | Classification | Authority | Role |
|-------|----------------|-----------|------|
| Watchlist | Required | Repository-approved upstream contract | Defines the evaluated Premarket universe |
| Catalyst collection | Authorized optional | Repository-approved upstream contract | Optional upstream Premarket catalyst evidence |
| Gap collection | Authorized optional | Repository-approved upstream contract | Optional upstream Premarket gap evidence |
| Explicit UTC `as_of` | Required | Evaluation control | Scoring evaluation timestamp |
| Explicit scoring configuration | Required | Frozen policy | Policy identity and configuration surface |
| Existing Premarket settings | Conditional | Existing repository settings | Fail-closed enablement when supplied |

“Authorized optional” means the input class is permitted. Presence, absence, and partial coverage are governed by the separate Missing-input Policy Freeze decision. This decision does not invent defaults for absent optional inputs.

### Prohibited Inputs

v1 must not consume:

- live Market Data providers, polling, streaming, or network fetches
- raw Market Data events as a bypass around Premarket Watchlist / Catalyst / Gap contracts
- Feature Platform snapshots or Feature Platform materialization outputs
- Strategy SDK public-API objects as scoring inputs
- Morning Briefing, Human Review, or AI Decision Engine artifacts
- broker, execution, portfolio, risk-approval, or order-state inputs
- wall-clock time, process entropy, random values, or mutable runtime caches as input evidence
- persistence stores, HTTP request bodies as authority, UI state, or worker side effects as scoring inputs
- any upstream capability not listed under Authorized Inputs

### Input Contract Requirements

- Scoring may consume only repository-approved upstream Premarket contracts listed above.
- Watchlist remains the sole required universe contract for v1.
- Catalyst and Gap may be consumed only as their existing Premarket collection contracts.
- Explicit UTC-aware `as_of` is mandatory for every scoring evaluation.
- Explicit scoring configuration is mandatory and must identify the frozen policy version.
- Premarket settings, when supplied and disabled, fail closed before scoring proceeds.
- No new upstream contract may be introduced by implementation.

### Input Validation Rules

Before scoring proceeds, implementation must validate that:

- every supplied authorized input matches its approved Premarket contract shape
- required inputs are present
- prohibited inputs are absent
- `as_of` is explicit and UTC-aware
- scoring configuration identifies an allowed frozen policy

Invalid, unsupported, or prohibited inputs are fail-closed errors.

Scoring validates compliance. Scoring does not repair, coerce, invent, or silently drop invalid input evidence to continue.

### PIT Requirements

Every authorized upstream Premarket input must already satisfy repository PIT guarantees before scoring consumes it.

Scoring validates PIT compliance of supplied inputs against the explicit scoring `as_of`.

Scoring does not repair PIT violations.

Future-known evidence must not affect output. Detailed cross-collection PIT aggregation rules remain governed by the separate PIT Aggregation Policy Freeze decision.

### Determinism Requirements

Identical authorized inputs, identical frozen configuration, identical frozen policy version, and identical explicit UTC `as_of` must produce identical scoring eligibility and identical consumable input sets for replay.

Determinism forbids:

- wall-clock time
- randomness
- unseeded nondeterminism
- mutable runtime state as input evidence

### Replay Requirements

Replay depends only on:

- frozen policy version
- approved upstream Premarket contracts actually supplied
- explicit UTC `as_of`
- frozen configuration

Replay must not depend on wall-clock time, randomness, or mutable runtime state.

### Input Provenance

Scoring must retain enough input provenance to support replay and audit:

- identity of each consumed authorized upstream collection / contract instance used
- scoring `as_of`
- frozen policy / configuration identity

Exact provenance field schema remains governed by the separate Provenance Policy Freeze decision. This decision freezes only that scoring inputs must be provenance-traceable to approved upstream Premarket contracts.

### Future Compatibility

Future Premarket capabilities may introduce additional upstream inputs only through:

- a new Policy Freeze
- a new Policy Version

Never through implementation.

Authorized optional Catalyst and Gap inputs may become required, excluded, or differently constrained only by a later Policy Freeze / Policy Version. Implementation must not expand the authorized input set.

### Policy Summary

| Rule | Frozen value |
|------|----------------|
| What this decision freezes | Authorized and prohibited scoring inputs |
| Required universe input | Watchlist |
| Authorized optional Premarket inputs | Catalyst collection, Gap collection |
| Required evaluation controls | Explicit UTC `as_of`, explicit scoring configuration |
| Settings | Existing Premarket settings fail-closed when supplied and disabled |
| New upstream capabilities | Not authorized |
| HOW scoring works | Out of scope for this decision |

### Conclusion

Decision #3 freezes the v1 scoring input boundary:

- Watchlist is required.
- Catalyst and Gap collections are authorized optional Premarket inputs.
- Explicit UTC `as_of` and explicit scoring configuration are required.
- All other input classes listed under Prohibited Inputs are forbidden.
- PIT, determinism, and replay constraints above are mandatory.
- Formulas, weights, normalization, and aggregation remain later Freeze Decisions.

This input boundary is immutable for Policy Version v1 and may change only through a subsequent approved Policy Freeze.