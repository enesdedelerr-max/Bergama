# Policy Version v1 Specification

## Version Metadata

| Field | Value |
|-------|-------|
| Policy Version ID | `premarket.scoring.policy.v1` |
| Policy Version Label | Premarket Scoring Policy Version v1 |
| Status | Implementation-ready |
| Governance Dependency | Repository Governance Decisions #1–#12 (immutable) |
| Score Domain | Finite `Decimal` in closed interval `[0, 1]` |
| Score Quantize Policy ID | `decimal_8dp_half_even` |
| Weight Profile ID | `default_v1` |
| Ordering Policy ID | `score_desc_instrument_key_asc_score_record_id_asc` |
| Identity Specification ID | `premarket.score.identity.v1` |
| Feature Specification Set | `watchlist_rank.v1`, `gap_magnitude.v1`, `catalyst_presence.v1` |

## Purpose

This specification defines the complete concrete implementation of Premarket Scoring Foundation under Policy Version `premarket.scoring.policy.v1`.

Feature transforms, identity construction, and weight profiles are defined by named subordinate specifications referenced below so that later ranking mechanisms, weight profiles, or identity schemes can evolve without rewriting this Policy Version’s governance binding.

This document does not modify, reinterpret, or expand Repository Governance Decisions #1–#12.

## Governance Dependencies

This Policy Version SHALL comply with all of the following immutable governance decisions:

| Decision | Title | Binding effect on v1 |
|----------|-------|----------------------|
| #1 | Score Semantic Meaning | Score is a Premarket attention / relative ordering-priority signal only |
| #2 | Score Domain | Finite `Decimal` in `[0, 1]`; higher is higher priority; ties legal; reject invalid values |
| #3 | Scoring Inputs | Watchlist required; Catalyst and Gap authorized optional; explicit UTC `as_of` and scoring configuration required |
| #4 | Normalization Strategy | Deterministic, monotonic, non-fabricating, fail-closed, PIT-compatible |
| #5 | Weighting Strategy | Weights owned exclusively by this Policy Version via Weight Profile |
| #6 | Missing Input Policy | No fabrication, inference, synthesis, or silent repair of missing evidence |
| #7 | Duplicate & Conflict Policy | No silent discard or silent reconciliation |
| #8 | PIT Aggregation Policy | Single explicit UTC `as_of`; no cross-PIT mixing |
| #9 | Policy Version & Identity | Exactly one Policy Version per scoring evaluation |
| #10 | Deterministic Identity | Identical governance inputs ⇒ identical score identity |
| #11 | Provenance Policy | Every Premarket Score has repository-governed provenance |
| #12 | Ordering & Tie-Break Policy | Deterministic total order; deterministic tie-breaks |

## Authorized Inputs

v1 SHALL consume only:

| Input | Classification | v1 consumption rule |
|-------|----------------|---------------------|
| Watchlist | Required | Defines evaluated universe; every scored instrument MUST appear exactly once |
| Catalyst collection | Authorized optional | When supplied, used only by Feature Specification `catalyst_presence.v1` |
| Gap collection | Authorized optional | When supplied, used only by Feature Specification `gap_magnitude.v1` |
| Explicit UTC `as_of` | Required | Single PIT context for the evaluation |
| Explicit scoring configuration | Required | MUST identify `premarket.scoring.policy.v1` and Weight Profile `default_v1` |
| Existing Premarket settings | Conditional | If supplied and `enabled=False`, evaluation SHALL fail closed |

v1 SHALL NOT consume any other evidence source.

## Feature Definitions

v1 binds exactly three features. Each feature is defined by a subordinate Feature Specification.

| Feature ID | Feature Specification | Source | Presence rule |
|------------|----------------------|--------|---------------|
| `watchlist_rank` | `watchlist_rank.v1` | Watchlist entry | Always present for every scored instrument |
| `gap_magnitude` | `gap_magnitude.v1` | Gap collection / Gap record | Present only when Gap collection is supplied and exactly one usable Gap record exists for the instrument |
| `catalyst_presence` | `catalyst_presence.v1` | Catalyst collection | Present only when Catalyst collection is supplied |

Each Feature Specification SHALL emit a finite `Decimal` component in `[0, 1]`, quantized with `decimal_8dp_half_even`, or be treated as absent under Missing Input Handling.

### Feature Specification `watchlist_rank.v1`

**Purpose:** Map Watchlist rank into a unit component where better rank yields higher value.

**Inputs:** Watchlist size `N` (`N ≥ 1` for non-empty universe), instrument rank `r` (`1 ≤ r ≤ N`).

**Transform:**

```text
watchlist_rank = (N - r + 1) / N
```

**Properties:** Deterministic; strictly monotonic decreasing in `r` for fixed `N`.

**Evolution note:** Later ranking mechanisms (priority rank, analyst rank, sector rank, risk rank) SHALL be introduced as new Feature Specifications and bound by a new Policy Version or explicit feature-set revision. They SHALL NOT silently replace `watchlist_rank.v1` inside this Policy Version.

### Feature Specification `gap_magnitude.v1`

**Purpose:** Map absolute overnight gap magnitude into a unit component.

**Inputs:** `gap_percent` from the usable Gap record; reference scale from Default Configuration (`GAP_REF`).

**Transform:**

```text
g = abs(gap_percent)
gap_magnitude = min(g / GAP_REF, Decimal("1"))
```

**Properties:** Deterministic; monotonic non-decreasing in absolute gap up to `GAP_REF`; saturates at `1`.

### Feature Specification `catalyst_presence.v1`

**Purpose:** Map usable catalyst evidence into a binary presence component.

**Transform when Catalyst collection is supplied:**

```text
catalyst_presence = Decimal("1") if count(usable catalysts for instrument_key) ≥ 1 else Decimal("0")
```

When Catalyst collection is not supplied, the feature is absent under Missing Input Handling.

**Usable catalyst:** Catalyst record with matching `instrument_key` that satisfies PIT Requirements.

## Normalization Specification

### Method

v1 uses **feature-native bounded transforms** defined exclusively by the bound Feature Specifications.

No batch min-max, z-score, percentile, or logistic scaler is used.

### Parameters

Normalization parameters are not restated here.

`GAP_REF` and quantize policy are defined only in Default Configuration and consumed by Feature Specification `gap_magnitude.v1` and by component emission rules.

### Normative rules

- Normalization SHALL be deterministic and monotonic as defined by each Feature Specification.
- Normalization SHALL NOT fabricate missing upstream evidence.
- Normalization SHALL NOT clamp, coerce, or repair invalid upstream evidence into validity.
- Invalid upstream evidence SHALL fail closed before normalization.

## Weight Specification

### Weight Profile

| Field | Value |
|-------|-------|
| Weight Profile ID | `default_v1` |
| Owning Policy Version | `premarket.scoring.policy.v1` |

### Weight Profile `default_v1`

| Feature ID | Weight |
|------------|--------|
| `watchlist_rank` | `Decimal("0.50")` |
| `gap_magnitude` | `Decimal("0.30")` |
| `catalyst_presence` | `Decimal("0.20")` |

```text
sum(default_v1 weights) = 1.00
```

### Normative rules

- Implementation SHALL consume Weight Profile `default_v1` exactly when this Policy Version is selected.
- Implementation SHALL NOT define, infer, substitute, or ambient-default alternate weights.
- Missing optional features contribute `0` under Missing Input Handling; weights of present features are NOT redistributed.
- Later Policy Versions MAY introduce new Weight Profiles (for example `default_v1_1`, `default_v2`) without mutating `default_v1`.

## Aggregation Specification

### Method

Linear weighted sum over the three v1 features using Weight Profile `default_v1`.

### Formula

For instrument `i`:

```text
raw_score_i =
    w_watchlist * c_watchlist_i
  + w_gap       * c_gap_i
  + w_catalyst  * c_catalyst_i
```

Where a missing optional component is treated as contribution `0` (see Missing Input Handling).

Then:

```text
score_i = quantize(raw_score_i, decimal_8dp_half_even)
```

### Domain enforcement

- If `score_i` is non-finite or outside `[0, 1]`, evaluation for that instrument SHALL fail closed.
- Implementation SHALL reject invalid score values rather than clamp, normalize, round into domain, or silently repair them.

## Missing Input Handling

### Collection-level

| Condition | Behavior |
|-----------|----------|
| Watchlist missing | Fail closed for the evaluation |
| `as_of` missing or not UTC-aware | Fail closed for the evaluation |
| Scoring configuration missing or not `premarket.scoring.policy.v1` | Fail closed for the evaluation |
| Premarket settings supplied and disabled | Fail closed for the evaluation |
| Gap collection not supplied | `gap_magnitude` absent for all instruments; contribution `0` |
| Catalyst collection not supplied | `catalyst_presence` absent for all instruments; contribution `0` |

### Instrument-level

| Condition | Behavior |
|-----------|----------|
| Instrument not in Watchlist | SHALL NOT be scored |
| Gap collection supplied, no usable Gap record for instrument | `gap_magnitude` contribution `0` |
| Catalyst collection supplied, no usable Catalyst record for instrument | `catalyst_presence = 0` |
| Required Watchlist fields invalid | Fail closed for that instrument |

### Normative prohibitions

- SHALL NOT invent defaults for missing Watchlist universe membership
- SHALL NOT impute, interpolate, estimate, or predict missing Gap/Catalyst evidence
- SHALL NOT redistribute weights when optional features are absent
- SHALL NOT silently repair missing inputs into synthetic evidence

## Duplicate Handling

| Condition | Behavior |
|-----------|----------|
| Duplicate `instrument_key` in Watchlist | Fail closed for the evaluation |
| Duplicate usable Gap records for the same `instrument_key` after Conflict Handling eligibility | Fail closed for that instrument |
| Duplicate Catalyst records for the same `instrument_key` | Not a duplicate failure for presence feature; presence remains `1` if count ≥ 1 |

Silent discard of duplicate evidence is prohibited. Fail-closed is the approved handling.

## Conflict Handling

| Condition | Behavior |
|-----------|----------|
| Multiple distinct usable Gap records for one instrument that disagree on gap evidence required by `gap_magnitude.v1` | Fail closed for that instrument |
| Evidence from different logical PIT contexts mixed into one evaluation | Fail closed for the evaluation |
| Authorized input that violates Decision #3 contract shape | Fail closed |

Silent reconciliation is prohibited. Fail-closed is the approved handling.

## Ordering Specification

Ordering Policy ID:

```text
score_desc_instrument_key_asc_score_record_id_asc
```

Primary order:

1. `score` descending (higher Premarket ordering priority first)

Then apply Tie-Break Specification.

## Tie-Break Specification

When scores are equal under Decision #2:

1. `instrument_key` ascending
2. `score_record_id` ascending

Normative rules:

- Ties are legal and SHALL remain equal on `score`
- Tie-breaks SHALL NOT alter `score` values
- Tie-breaks SHALL be deterministic and replay-safe

## Output Contract

Each scored instrument SHALL emit one Premarket Score record with at least:

| Field | Type / rule |
|-------|-------------|
| `score_record_id` | Deterministic identity per Identity Specification `premarket.score.identity.v1` |
| `instrument_key` | From Watchlist entry |
| `local_symbol` | From Watchlist entry (nullable) |
| `score` | Finite `Decimal` in `[0, 1]`, quantized `decimal_8dp_half_even` |
| `components.watchlist_rank` | Finite `Decimal` in `[0, 1]` |
| `components.gap_magnitude` | Finite `Decimal` in `[0, 1]`, or `null` when feature absent |
| `components.catalyst_presence` | `0` or `1`, or `null` when feature absent |
| `policy_version_id` | `premarket.scoring.policy.v1` |
| `weight_profile_id` | `default_v1` |
| `as_of` | Explicit UTC timestamp of the evaluation |
| `provenance.config_fingerprint` | Deterministic fingerprint of scoring configuration + this Policy Version + Weight Profile |
| `provenance.input_fingerprint` | Deterministic fingerprint of authorized inputs actually consumed |
| `provenance.source_identifiers` | Deterministic identifiers of consumed upstream records / entries |

Empty Watchlist (`N = 0`) SHALL yield an empty score collection with valid evaluation-level provenance and SHALL NOT fabricate instruments.

### Identity Specification `premarket.score.identity.v1`

This subordinate specification defines concrete identity construction for Policy Version v1 outputs.

Governance Decision #10 remains algorithm-agnostic. Identity algorithm details live only here.

**Identity outcome:** `score_record_id` is a deterministic 64-character lowercase hex digest.

**Digest method for v1:** canonical-payload SHA-256, consistent with existing Premarket deterministic identity conventions.

**Canonical payload MUST include at least:**

- identity specification id: `premarket.score.identity.v1`
- `policy_version_id`
- `weight_profile_id`
- `instrument_key`
- `as_of`
- quantized `score`
- component values as emitted (`null` encoded canonically for absent optional components)
- Watchlist rank and rule identity used
- Gap `gap_record_id` when gap feature present, else empty
- Catalyst contributing source identifiers when catalyst feature present, else empty

Catalyst contributing source identifiers are set-based evidence under Feature Specification
`catalyst_presence.v1`. Before identity and provenance hashing, contributing Catalyst
identifiers SHALL be reduced to the unique set of usable `catalyst_record_id` values and
ordered by ascending lexicographic order. Input collection iteration order MUST NOT affect
`score_record_id`, collection provenance fingerprints, or emitted source-identifier order.
Equivalent duplicate Catalyst records (identical payload under the same identity) collapse;
conflicting payloads under the same `catalyst_record_id` fail closed.

Identity SHALL NOT use UUID, wall-clock, or mutable runtime state.

Later identity schemes SHALL be introduced as new Identity Specifications and bound by a new Policy Version. They SHALL NOT silently replace `premarket.score.identity.v1` inside this Policy Version.

## Validation Rules

Before emission, implementation SHALL validate:

1. Policy Version ID equals `premarket.scoring.policy.v1`
2. Weight Profile ID equals `default_v1`
3. `as_of` is present and UTC-aware
4. Watchlist is present; instrument keys unique
5. Prohibited inputs are absent
6. Every emitted `score` is finite `Decimal` in `[0, 1]`
7. Component values present are finite `Decimal` in `[0, 1]`
8. Weights used equal Weight Profile `default_v1` exactly
9. Ordering matches Ordering + Tie-Break Specification
10. Every record has `score_record_id` per `premarket.score.identity.v1`, Policy Version, `as_of`, and provenance
11. Premarket settings fail-closed when supplied and disabled

Invalid conditions SHALL fail closed. No silent repair.

## Replay Requirements

Replay SHALL reproduce identical:

- score values
- component values
- identities
- provenance fingerprints
- ordering

for identical authorized inputs, identical configuration, identical Policy Version `premarket.scoring.policy.v1`, identical Weight Profile `default_v1`, and identical explicit UTC `as_of`.

Replay SHALL NOT depend on wall-clock time, randomness, or mutable runtime state.

## Determinism Requirements

All Feature Specifications, Weight Profile application, aggregation, missing/duplicate/conflict handling, identity, provenance, and ordering defined for this Policy Version SHALL be deterministic.

Identical governance inputs SHALL always produce the same scoring outcome.

## PIT Requirements

- Exactly one explicit UTC `as_of` per evaluation
- Watchlist, Gap, and Catalyst evidence SHALL be usable only if already PIT-valid relative to that `as_of`
- Future-known evidence SHALL fail closed
- Cross-PIT aggregation SHALL fail closed
- Scoring validates PIT compliance and SHALL NOT repair PIT violations

Usable Gap/Catalyst evidence requires upstream `known_at ≤ as_of` (and any additional upstream PIT constraints already enforced by those Premarket foundations).

## Default Configuration

| Setting | Default |
|---------|---------|
| `policy_version_id` | `premarket.scoring.policy.v1` |
| `weight_profile_id` | `default_v1` |
| `ordering_policy_id` | `score_desc_instrument_key_asc_score_record_id_asc` |
| `score_quantize_policy_id` | `decimal_8dp_half_even` |
| `identity_specification_id` | `premarket.score.identity.v1` |
| `GAP_REF` | `Decimal("0.10")` |
| Optional Gap collection | Not supplied ⇒ gap contribution `0` |
| Optional Catalyst collection | Not supplied ⇒ catalyst contribution `0` |

## Version Compatibility

- This Policy Version is identified solely by `premarket.scoring.policy.v1`
- Evaluations MUST bind to exactly this Policy Version ID and Weight Profile `default_v1`
- Feature Specifications and Identity Specification bound by this Policy Version are part of the concrete v1 contract
- A different Policy Version ID, Weight Profile ID, Feature Specification ID, or Identity Specification ID selects a different concrete algorithm set and MUST NOT be treated as equivalent

## Future Evolution

Future Policy Versions may change:

- Feature Specification bindings
- Weight Profiles
- Identity Specifications
- aggregation formulas
- missing/duplicate/conflict handling mechanisms
- ordering / tie-break chains

Future Policy Versions SHALL preserve compatibility with Repository Governance Decisions #1–#12 unless those governance decisions are superseded by a subsequent approved Policy Freeze.

Implementation changes alone SHALL NOT alter this Policy Version. Any change to v1 concrete behavior requires a new Policy Version ID and/or new subordinate specification IDs.