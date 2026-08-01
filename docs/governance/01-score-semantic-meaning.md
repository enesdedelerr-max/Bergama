## Score Semantic Meaning

Status: RESOLVED

### Purpose

Define what a Premarket Score represents for Premarket Scoring Foundation v1.

### Repository Constraints

No Premarket scoring capability or repository-defined score semantics exist today. Sprint 7 completed Watchlist, Catalyst, and Gap foundations and deferred Premarket Scoring. Planning Gate and Implementation Issue require a deterministic, replayable, PIT-safe, policy-driven Premarket-internal score derived only from repository-approved upstream Premarket contracts under explicit UTC `as_of`. Morning Briefing, Human Review, and AI Decision Engine remain deferred consumers and are not defined by this decision.

### Decision

A Premarket Score is a deterministic, policy-versioned Premarket attention signal for one instrument in the approved Premarket universe at an explicit UTC `as_of`.

It expresses the deterministic relative ordering priority of one instrument within the evaluated Premarket universe under the frozen scoring policy and the accepted upstream Premarket evidence known at or before `as_of`.

A Premarket Score is not:

- a forecast of return, volatility, or direction
- a trading recommendation
- an order intent, order, fill, or execution authorization
- a risk approval, compliance approval, or human-review decision
- a portfolio construction or position-sizing decision
- a Market Data price, quote, or bar substitute
- a Feature Platform feature value or FeatureSnapshot
- a Strategy SDK public-API contract
- a Morning Briefing, Human Review artifact, or AI Decision Engine decision

Prohibited assumptions:

- that a higher score authorizes trading or bypasses risk, compliance, review, or kill-switch controls
- that a score equals expected PnL, edge, or probability of profit
- that absent upstream evidence may be silently invented to produce a score
- that wall-clock time, randomness, or non-replayable state may affect score meaning
- that deferred consumers redefine what the score means

### Implementation Impact

Implementation must treat every v1 Premarket Score solely as a Premarket attention signal under the frozen policy identity. Implementation must not reinterpret scores as forecasts, orders, approvals, or execution authority. Documentation and contracts must preserve this semantic boundary.

### Future Compatibility

The semantic meaning is immutable across policy versions.

Future policy versions may change how the score is computed, but they must not redefine what a Premarket Score represents.

Future Morning Briefing, Human Review, and AI Decision Engine consumers may read Premarket Scores as Premarket attention evidence only; they must not redefine the score as a trading decision or authorization.