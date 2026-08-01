# Premarket Scoring Engine Architecture v1

## 1. Purpose

Define the software architecture that implements Premarket Scoring under:

- Repository Governance Decisions #1–#12 (immutable)
- Policy Version v1 Specification (`premarket.scoring.policy.v1`) (immutable for this architecture)

This architecture defines **structure, boundaries, interfaces, and data flow**.

It does **not** redefine scoring algorithms, weights, normalization, aggregation, governance, or Policy Version v1.

## 2. Architectural Principles

| Principle | Requirement |
|-----------|-------------|
| Determinism | Same authorized inputs + config + Policy Version + `as_of` ⇒ same outputs |
| Replay-safety | No wall-clock, randomness, or mutable runtime state in scoring paths |
| PIT-safety | Single explicit UTC `as_of`; validate, never repair PIT violations |
| Fail-closed | Invalid / prohibited / conflicting conditions raise typed Premarket errors |
| Modularity | One responsibility per component; Policy Version logic isolated behind ports |
| Dependency injection | Engines depend on interfaces; Policy Version v1 provides implementations |
| Extensibility | New Policy Versions register new binders without rewriting orchestration |
| Testability | Each stage unit-testable with frozen fixtures |
| Premarket consistency | Mirror existing `watchlist` / `catalyst` / `gap` package conventions |

## 3. Bounded Context Placement

Premarket Scoring lives inside Premarket Intelligence as a sibling of Watchlist, Catalyst, and Gap.

```text
apps/api/app/premarket/
  watchlist/     # upstream (required universe)
  catalyst/      # upstream (authorized optional)
  gap/           # upstream (authorized optional)
  scoring/       # this architecture
  errors.py      # shared Premarket error hierarchy (extend)
  settings.py    # PremarketSettings re-export
```

Scoring **consumes** Watchlist / Catalyst / Gap contracts. It does **not** own or mutate them.

## 4. Overall Processing Pipeline

```text
ScoreRequest
    │
    ▼
┌───────────────────────┐
│ Input Validation Layer│
└───────────┬───────────┘
            │ ValidatedScoreRequest
            ▼
┌───────────────────────┐
│ Policy Version Resolver│
└───────────┬───────────┘
            │ BoundPolicyVersion (v1)
            ▼
┌───────────────────────┐
│ Feature Extraction    │  (per instrument in Watchlist order of discovery)
└───────────┬───────────┘
            │ FeatureBundle[]
            ▼
┌───────────────────────┐
│ Normalization Engine  │  (Feature Spec transforms)
└───────────┬───────────┘
            │ ComponentBundle[]
            ▼
┌───────────────────────┐
│ Weight Engine         │  (Weight Profile default_v1)
└───────────┬───────────┘
            │ WeightedComponentBundle[]
            ▼
┌───────────────────────┐
│ Aggregation Engine    │  (linear weighted sum + quantize)
└───────────┬───────────┘
            │ RawScoreDraft[]
            ▼
┌───────────────────────┐
│ Identity Builder      │
└───────────┬───────────┘
            │ IdentifiedScoreDraft[]
            ▼
┌───────────────────────┐
│ Ordering Engine       │  (+ Tie-Break)
└───────────┬───────────┘
            │ OrderedScoreDraft[]
            ▼
┌───────────────────────┐
│ Provenance Builder    │
└───────────┬───────────┘
            │ ProvenancedScoreDraft[]
            ▼
┌───────────────────────┐
│ Output Builder        │
└───────────┬───────────┘
            │ ScoreCollection (immutable)
            ▼
┌───────────────────────┐
│ Validation Layer      │  (post-condition checks)
└───────────┬───────────┘
            │ ScoreCollection
            ▼
┌───────────────────────┐
│ Replay Layer          │  (optional explicit replay/compare path)
└───────────────────────┘
```

Authoritative late-pipeline runtime sequence:

Identity → Ordering → Provenance → Output → Post-validation


Orchestration entrypoint (mirrors Gap/Watchlist style):

- `scan_scores(request, *, settings=None) -> ScoreCollection`
- `scan_scores_from_parts(...)` convenience coercion wrapper

## 5. Component Interaction Diagram (ASCII)

```text
                    ┌────────────────────┐
                    │ PremarketSettings  │
                    └─────────┬──────────┘
                              │ enablement gate
                              ▼
┌──────────┐   ┌─────────────────────┐   ┌──────────────────────┐
│ Watchlist│──▶│ ScoringOrchestrator │◀──│ ScoringConfig/Request│
│ Catalyst │──▶│                     │   └──────────────────────┘
│ Gap      │──▶│                     │
└──────────┘   └──────────┬──────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌────────────────┐
│InputValidator │ │PolicyResolver │ │FeatureExtractors│
└───────┬───────┘ └───────┬───────┘ └────────┬───────┘
        │                 │                  │
        └────────────┬────┴──────────────────┘
                     ▼
        ┌────────────────────────┐
        │ NormalizationEngine    │
        └────────────┬───────────┘
                     ▼
        ┌────────────────────────┐
        │ WeightEngine           │
        └────────────┬───────────┘
                     ▼
        ┌────────────────────────┐
        │ AggregationEngine      │
        └────────────┬───────────┘
                     ▼
              ┌──────────────┐
              │IdentityBuilder│
              └──────┬───────┘
                     ▼
              ┌──────────────┐
              │OrderingEngine│
              └──────┬───────┘
                     ▼
              ┌────────────────┐
              │ProvenanceBuilder│
              └──────┬─────────┘
                     ▼
              ┌──────────────┐
              │ OutputBuilder│
              └──────┬───────┘
                     ▼
              ┌──────────────┐
              │PostValidator │
              └──────┬───────┘
                     ▼
              ScoreCollection
```


## 6. Dependency Flow

```text
Presentation / Application callers
        │
        ▼
scoring.engine (orchestration)
        │
        ├──▶ scoring.ports (interfaces)
        │         ▲
        │         │ implements
        │         │
        └──▶ scoring.policy_v1 (Policy Version v1 binders)
                    │
                    ├── Feature Spec adapters (watchlist_rank.v1, ...)
                    ├── Weight Profile default_v1
                    └── Identity Spec premarket.score.identity.v1

scoring.models  ◀── immutable contracts (request/config/record/collection/provenance)
scoring.errors  ◀── typed fail-closed errors (or extend premarket.errors)
```

**Rule:** Orchestration depends on **ports**. Policy Version v1 packages provide **adapters**. Callers never import Policy Version internals.

## 7. Data Flow

```text
ScoreRequest
  watchlist: Watchlist
  catalysts: CatalystCollection | None
  gaps: GapCollection | None
  as_of: datetime (UTC)
  config: ScoreConfig  # policy_version_id, weight_profile_id, ordering_policy_id, ...

→ ValidatedScoreRequest
→ BoundPolicyContext { policy_version_id, weight_profile, feature_specs, identity_spec, params }

Per instrument_key in Watchlist.entries:
  FeatureObservation → NormalizedComponents → WeightedTerms → QuantizedScore
  → ScoreRecordDraft (+ identity)

→ sorted ScoreRecordDraft tuple (Ordering Engine)
→ collection provenance (Provenance Builder)
→ ScoreCollection { as_of, records, provenance }
```


Intermediate DTOs are internal and immutable (`frozen=True` dataclasses or Pydantic models). Only `ScoreCollection` / `ScoreRecord` / `ScoreProvenance` are public contracts.

## 8. Error Propagation Strategy

| Stage | Failure style |
|-------|----------------|
| Settings disabled | `PremarketDisabledError` (fail closed) |
| Input validation | `ScoreValidationError` / unsupported-input errors |
| Policy resolve | `ScoreUnsupportedPolicyError` |
| Feature extract / normalize | instrument-scoped or evaluation-scoped typed errors |
| Duplicate / conflict | fail closed per Policy Version v1 tables |
| Domain / quantize invalid | fail closed; never clamp |
| Post-validation | fail closed if invariants broken |

**Propagation rules:**

1. Evaluation-scoped failures abort the entire scan.
2. Instrument-scoped failures abort that instrument only when Policy Version v1 says so; otherwise escalate to evaluation failure.
3. No partial silent success for prohibited conditions.
4. Preserve original exception context when wrapping at boundaries.

## 9. Fail-Closed Behavior

The orchestrator SHALL fail closed when:

- Premarket settings supplied and disabled
- Required inputs missing / invalid / non-UTC `as_of`
- Policy Version ID ≠ `premarket.scoring.policy.v1`
- Weight Profile ID ≠ `default_v1`
- Prohibited inputs present
- Duplicate Watchlist instruments
- Gap conflicts for an instrument (per v1)
- Cross-PIT evidence
- Emitted score outside `[0, 1]` or non-finite
- Identity / provenance invariants violated

Silent repair, clamp, invent, infer, synthesize, or reconcile is forbidden.

## 10. Dependency Injection Boundaries

| Bound object | Injection style |
|--------------|-----------------|
| `PolicyVersionBinder` | Selected by Policy Version Resolver from registry |
| `FeatureExtractor` set | Provided by binder |
| `NormalizationEngine` | Stateless; uses Feature Spec transforms from binder |
| `WeightEngine` | Uses Weight Profile from binder |
| `AggregationEngine` | Stateless formula executor from binder params |
| `OrderingEngine` | Uses ordering policy id from config/binder |
| `IdentityBuilder` | Identity Spec from binder |
| `ProvenanceBuilder` | Uses shared hashing utilities (`strategy_sha256`) |
| Clock | Not used in scoring path (event time only via `as_of`) |

Production wiring:

```text
build_default_scoring_pipeline() -> ScoringOrchestrator
  registers PolicyVersionV1Binder under "premarket.scoring.policy.v1"
```

Tests inject fake binders / extractors without importing production Policy Version internals when testing orchestration.

## 11. Public Interfaces

Suggested public surface (Premarket-internal, not Strategy SDK):

```text
scan_scores(request: ScoreRequest | object, *, settings: PremarketSettings | None = None) -> ScoreCollection
scan_scores_from_parts(...) -> ScoreCollection

ScoreRequest
ScoreConfig
ScoreRecord
ScoreCollection
ScoreProvenance

POLICY_VERSION_V1 = "premarket.scoring.policy.v1"
WEIGHT_PROFILE_DEFAULT_V1 = "default_v1"
ORDERING_POLICY_SCORE_DESC_INSTRUMENT_KEY_ASC_ID_ASC
SCORE_QUANTIZE_POLICY_ID = "decimal_8dp_half_even"
```

## 12. Internal Interfaces (Ports)

```text
PolicyVersionBinder
  policy_version_id: str
  weight_profile_id: str
  resolve_params() -> PolicyParams
  feature_extractors() -> Sequence[FeatureExtractor]
  identity_builder() -> IdentityBuilder
  ordering_key() -> Callable[[ScoreRecordDraft], tuple]

FeatureExtractor
  feature_id: str
  extract(ctx: InstrumentScoreContext) -> FeatureObservation | AbsentFeature

NormalizationEngine
  normalize(obs: FeatureObservation, params: PolicyParams) -> NormalizedComponent

WeightEngine
  apply(components: Mapping[str, NormalizedComponent | Absent], profile: WeightProfile) -> WeightedTerms

AggregationEngine
  aggregate(terms: WeightedTerms, params: PolicyParams) -> QuantizedScore

OrderingEngine
  order(drafts: Sequence[ScoreRecordDraft]) -> tuple[ScoreRecordDraft, ...]

IdentityBuilder
  build_id(draft: ScoreIdentityInput) -> str

ProvenanceBuilder
  build_record_fields(...) -> RecordProvenanceFields
  build_collection_provenance(...) -> ScoreProvenance

OutputBuilder
  to_record(draft: ScoreRecordDraft) -> ScoreRecord
  to_collection(...) -> ScoreCollection

InputValidator
  validate(request, settings) -> ValidatedScoreRequest

PostValidator
  validate(collection: ScoreCollection, request: ValidatedScoreRequest) -> ScoreCollection

ReplayService
  assert_replay_equal(a: ScoreCollection, b: ScoreCollection) -> None
  rescore(request) -> ScoreCollection  # pure re-exec helper for tests
```

## 13. Component Specifications

### 13.1 Input Validation Layer

**Purpose:** Admit only Decision #3 / Policy Version v1-legal requests.

**Responsibilities:**
- Validate UTC `as_of`
- Require Watchlist; allow optional Catalyst/Gap collections
- Reject prohibited inputs
- Enforce Premarket settings fail-closed
- Validate config IDs (`policy_version_id`, `weight_profile_id`, ordering/quantize ids)

**Inputs:** `ScoreRequest`, optional `PremarketSettings`
**Outputs:** `ValidatedScoreRequest`
**Dependencies:** Premarket Watchlist/Catalyst/Gap models; scoring models; errors
**Failure Modes:** validation / disabled / unsupported input errors
**Determinism:** Pure function of request+settings
**Replay:** Same request ⇒ same validation outcome
**Extension Points:** Additional config validators per Policy Version via binder hooks (optional)

---

### 13.2 Policy Version Resolver

**Purpose:** Bind evaluation to exactly one Policy Version implementation.

**Responsibilities:**
- Resolve `policy_version_id` from config
- Load registered `PolicyVersionBinder`
- Reject unknown / mismatched Policy Versions

**Inputs:** Validated config
**Outputs:** `BoundPolicyContext`
**Dependencies:** Binder registry
**Failure Modes:** unsupported policy / weight profile
**Determinism:** Registry lookup by immutable IDs only
**Replay:** Same IDs ⇒ same binder
**Extension Points:** Register `PolicyVersionV2Binder` without changing orchestrator

---

### 13.3 Feature Extraction Layer

**Purpose:** Gather raw feature observations per instrument without applying Policy Version math beyond observation selection rules defined by Feature Specs.

**Responsibilities:**
- Iterate Watchlist entries (universe)
- Invoke bound Feature Extractors (`watchlist_rank.v1`, `gap_magnitude.v1`, `catalyst_presence.v1`)
- Apply duplicate/conflict eligibility checks that Feature Specs require before observation emission
- Emit `FeatureObservation` or `AbsentFeature`

**Inputs:** Validated request + BoundPolicyContext
**Outputs:** Per-instrument feature bags
**Dependencies:** Watchlist/Catalyst/Gap contracts; FeatureExtractor ports
**Failure Modes:** duplicate instrument; gap conflict; invalid upstream
**Determinism:** Stable instrument iteration order = Watchlist entry order for extraction; final collection order deferred to Ordering Engine
**Replay:** Same upstream collections ⇒ same observations
**Extension Points:** New FeatureExtractor adapters for future Feature Specs

---

### 13.4 Normalization Engine

**Purpose:** Execute Feature Specification transforms to `[0, 1]` components.

**Responsibilities:**
- Apply transforms defined by Policy Version v1 Feature Specs
- Quantize components with `decimal_8dp_half_even`
- Never fabricate absent features

**Inputs:** Feature observations + PolicyParams (`GAP_REF`, quantize policy)
**Outputs:** Normalized components / absences
**Dependencies:** Decimal utilities (`canonical_decimal_str` / quantize helpers as used elsewhere)
**Failure Modes:** invalid upstream numeric evidence
**Determinism:** Pure Decimal transforms
**Replay:** Identical observations ⇒ identical components
**Extension Points:** Feature Spec strategy objects plugged by binder

---

### 13.5 Weight Engine

**Purpose:** Apply Weight Profile `default_v1`.

**Responsibilities:**
- Attach immutable weights to present components
- Treat absent optional components as zero contribution terms without redistributing weights
- Reject unknown feature IDs

**Inputs:** Normalized components + Weight Profile
**Outputs:** Weighted terms
**Dependencies:** Weight Profile value object from binder
**Failure Modes:** profile mismatch; unknown feature
**Determinism:** Pure mapping
**Replay:** Same profile + components ⇒ same terms
**Extension Points:** Alternate Weight Profiles via new Policy Versions

---

### 13.6 Aggregation Engine

**Purpose:** Compute quantized Premarket Score from weighted terms.

**Responsibilities:**
- Linear weighted sum per Policy Version v1
- Quantize with `decimal_8dp_half_even`
- Reject out-of-domain results (no clamp)

**Inputs:** Weighted terms + PolicyParams
**Outputs:** Quantized score + retained component snapshot
**Dependencies:** Decimal quantize policy constants
**Failure Modes:** non-finite / out-of-domain score
**Determinism:** Pure function
**Replay:** Identical terms ⇒ identical score
**Extension Points:** New aggregation strategy interface for future Policy Versions only

---

### 13.7 Ordering Engine

**Purpose:** Produce deterministic total order for score drafts.

**Responsibilities:**
- Sort by Policy Version ordering policy
- Apply tie-breaks: `instrument_key` ASC, then `score_record_id` ASC
- Preserve equal scores without mutation

**Inputs:** Score drafts with score + identity
**Outputs:** Ordered draft tuple
**Dependencies:** Ordering policy id; sort key function
**Failure Modes:** missing identity before order (pipeline invariant)
**Determinism:** Total order key only
**Replay:** Same drafts ⇒ same order
**Extension Points:** Alternate sort key providers per Policy Version

---

### 13.8 Identity Builder

**Purpose:** Build deterministic `score_record_id` per Identity Specification `premarket.score.identity.v1`.

**Responsibilities:**
- Canonicalize identity payload
- Include Catalyst contributing source identifiers as the unique ascending set
- Digest via Identity Spec method
- Forbid UUID / wall-clock / mutable state

**Inputs:** Score identity input DTO
**Outputs:** 64-char hex id
**Dependencies:** `strategy_sha256` / money canonical decimal helpers (repository convention used by Identity Spec v1)
**Failure Modes:** incomplete identity inputs
**Determinism:** Canonical payload hashing
**Replay:** Identical inputs ⇒ identical id
**Extension Points:** New Identity Spec adapters for future Policy Versions

---

### 13.9 Provenance Builder

**Purpose:** Attach repository-governed provenance to every score and to the collection.

**Responsibilities:**
- Config fingerprint (config + policy version + weight profile)
- Input fingerprint (authorized inputs actually consumed + `as_of`)
- Source identifiers (watchlist/gap/catalyst identifiers consumed)
- Consume Catalyst collections after Input Validation has canonicalized record order
  (unique by `catalyst_record_id`, ascending) so fingerprints are order-independent
- Ensure every record carries required provenance linkage

**Inputs:** Validated request + drafts + BoundPolicyContext
**Outputs:** Record provenance fields + `ScoreProvenance`
**Dependencies:** Deterministic hashing utilities
**Failure Modes:** incomplete provenance inputs
**Determinism:** Canonical dumps only
**Replay:** Identical fingerprints
**Extension Points:** Additional fingerprint fields only via new Policy Version / Provenance extension rules

---

### 13.10 Output Builder

**Purpose:** Materialize immutable public scoring contracts.

**Responsibilities:**
- Map drafts → `ScoreRecord`
- Build `ScoreCollection`
- Freeze tuples / models (`extra=forbid`, `frozen=True`)

**Inputs:** Ordered provenanced drafts
**Outputs:** `ScoreCollection`
**Dependencies:** scoring models
**Failure Modes:** model validation errors
**Determinism:** Pure mapping
**Replay:** Stable serialization
**Extension Points:** None for v1 public fields beyond Policy Version output contract

---

### 13.11 Validation Layer (Post)

**Purpose:** Enforce Policy Version v1 post-conditions before return.

**Responsibilities:**
- Domain checks on all scores
- Ordering invariant checks
- Policy/profile id checks
- Provenance presence for every record
- Empty-universe allowed with empty records + valid collection provenance

**Inputs:** Candidate `ScoreCollection`
**Outputs:** Same collection or fail closed
**Dependencies:** Policy Params / invariants module
**Failure Modes:** invariant violations
**Determinism:** Pure checks
**Replay:** Same collection ⇒ same result
**Extension Points:** Version-specific invariant packs from binder

---

### 13.12 Replay Layer

**Purpose:** Support explicit replay verification without affecting production scoring purity.

**Responsibilities:**
- Re-execute `scan_scores` on pinned request
- Structural equality compare (`model_dump` / canonical compare)
- Expose test/helper API only; not a live runtime side effect

**Inputs:** Pinned `ScoreRequest` (+ optional expected collection)
**Outputs:** Replayed collection / assertion result
**Dependencies:** Orchestrator
**Failure Modes:** inequality → test/helper failure
**Determinism:** Relies on orchestrator determinism
**Replay:** Primary consumer of replay guarantees
**Extension Points:** Golden-file adapters in tests

## 14. Repository Package Layout

Suggested layout (aligned with `gap/` / `catalyst/`):

```text
apps/api/app/premarket/scoring/
  __init__.py                 # public exports
  models.py                   # ScoreRequest/Config/Record/Collection/Provenance
  policy.py                   # constant IDs (policy/profile/ordering/quantize)
  errors.py                   # OR extend apps/api/app/premarket/errors.py
  engine.py                   # ScoringOrchestrator + scan_scores entrypoints
  ports.py                    # Protocol/ABC interfaces
  pipeline.py                 # stage wiring helpers (optional)
  validate_input.py           # Input Validation Layer
  validate_output.py          # Post Validation Layer
  resolve_policy.py           # Policy Version Resolver + registry
  features.py                 # FeatureExtraction service
  normalize.py                # Normalization Engine
  weights.py                  # Weight Engine
  aggregate.py                # Aggregation Engine
  ordering.py                 # Ordering + tie-break keys
  identity.py                 # Identity Builder facade
  provenance.py               # Provenance Builder
  output.py                   # Output Builder
  replay.py                   # Replay helpers
  policy_v1/
    __init__.py
    binder.py                 # PolicyVersionV1Binder
    params.py                 # GAP_REF binding from defaults, etc.
    weight_profile_default_v1.py
    features/
      watchlist_rank_v1.py
      gap_magnitude_v1.py
      catalyst_presence_v1.py
    identity_v1.py            # Identity Spec implementation
```

Tests (mirror existing Premarket layout):

```text
apps/api/tests/unit/test_premarket_scoring_engine.py
apps/api/tests/contract/test_premarket_scoring_contract.py
apps/api/tests/integration/test_premarket_scoring_boundary.py
```

Makefile: add `test-api-premarket-scoring` and include in `test-api-premarket` (implementation issue concern; noted for readiness).

## 15. Suggested Class / Interface Names

| Kind | Name |
|------|------|
| Orchestrator | `ScoringOrchestrator` |
| Entrypoints | `scan_scores`, `scan_scores_from_parts` |
| Models | `ScoreRequest`, `ScoreConfig`, `ScoreRecord`, `ScoreCollection`, `ScoreProvenance` |
| Ports | `PolicyVersionBinder`, `FeatureExtractor`, `NormalizationEngine`, `WeightEngine`, `AggregationEngine`, `OrderingEngine`, `IdentityBuilder`, `ProvenanceBuilder`, `OutputBuilder`, `InputValidator`, `PostValidator` |
| Value objects | `PolicyParams`, `WeightProfile`, `FeatureObservation`, `AbsentFeature`, `NormalizedComponent`, `WeightedTerms`, `ScoreRecordDraft` |
| v1 binder | `PolicyVersionV1Binder` |
| v1 extractors | `WatchlistRankFeatureV1`, `GapMagnitudeFeatureV1`, `CatalystPresenceFeatureV1` |
| Errors | `ScoreError`, `ScoreValidationError`, `ScoreUnsupportedPolicyError`, `ScoreDuplicateInstrumentError`, `ScoreConflictError`, `ScoreDomainError`, `ScoreStaleKnownAtError` |

## 16. Implementation Guidance (for engineers)

1. **Implement models + errors first** (frozen Pydantic contracts; UTC validators; Decimal parsers) matching Output Contract fields from Policy Version v1.
2. **Implement ports + orchestrator skeleton** with fail-closed settings gate like Gap/Watchlist.
3. **Implement Policy Version v1 binder and Feature Specs** exactly as specified; no local coefficient drift.
4. **Wire identity + provenance** using existing `strategy_sha256` and `canonical_decimal_str` conventions.
5. **Add unit tests** for each stage and golden replay tests for full pipeline.
6. **Add contract tests** proving no Strategy SDK / Market Data drift and frozen model shape.
7. **Add integration boundary tests** consuming real Watchlist/Catalyst/Gap objects.

## 17. Non-Goals of This Architecture

- Morning Briefing / Human Review / AI Decision Engine
- Persistence, workers, HTTP APIs, UI
- Strategy SDK export expansion
- Market Data contract changes
- Alternate Policy Versions beyond registering future binders
- Reinterpreting Governance Decisions #1–#12
- Changing Policy Version v1 formulas, weights, or Feature Specs

## 18. Readiness Statement

This architecture is sufficient for engineering to begin coding Premarket Scoring Foundation against Policy Version `premarket.scoring.policy.v1` without further architectural redesign, provided Governance Decisions #1–#12 and Policy Version v1 remain unchanged.