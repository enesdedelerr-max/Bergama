# Repository Policy Documents

| Document | Policy ID | Status | Description |
|----------|-----------|--------|-------------|
| [premarket-scoring-policy-v1.md](premarket-scoring-policy-v1.md) | `premarket.scoring.policy.v1` | APPROVED / immutable | Premarket Scoring Policy Version v1 |
| [morning-briefing-policy-v1.md](morning-briefing-policy-v1.md) | `morning-briefing.policy.v1` | APPROVED / immutable | Morning Briefing Policy Version v1 |
| [dashboard-policy-v1.md](dashboard-policy-v1.md) | `dashboard.policy.v1` | APPROVED | Dashboard Policy Version v1 |
| [human-review-policy-v1.md](human-review-policy-v1.md) | `human-review.policy.v1` | APPROVED | Human Review Policy Version v1 |
| [ai-decision-engine-policy-v1.md](ai-decision-engine-policy-v1.md) | `ai-decision-engine.policy.v1` | MATERIALIZED — awaiting human review | AI Decision Engine Policy Version v1 |

Policy Version content must not be edited in place once frozen for an implementation generation.
Behavioral change requires a new Policy Version ID and/or new subordinate specification IDs.

`ai-decision-engine.policy.v1` is materialized for human review and is not
workflow-approved until separate commit, PR, CI, external approval, merge, and
post-merge verification complete. Implementation Authorization remains DENIED.
