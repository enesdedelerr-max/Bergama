# Sprint 9 Planning Gate

**Planning Gate ID:** `sprint-9.planning-gate`  
**Proposed theme:** Morning Briefing  
**Status:** APPROVED  
**Prerequisite:** Sprint 8 complete — Premarket Scoring Foundation (`v0.8.0-sprint8`)  
**Document class:** Planning Gate only  
**Document role:** Canonical Planning Gate template for Bergama sprint planning  

This Planning Gate authorizes Sprint 9 theme selection, scope classification, and the mandatory subsequent gate sequence.  
It does not approve Architecture, Governance Decisions, Policy Freeze, or Implementation.  
It does not specify algorithms, contracts, schemas, storage, services, models, packages, endpoints, user interfaces, persistence, or notification providers.

Sprint 8 Premarket Scoring Foundation — including Governance Decisions #1–#12, Premarket Scoring Engine Architecture v1, and Policy Version `premarket.scoring.policy.v1` — remains frozen and shall not be redesigned by this Planning Gate.

---

## Status

| Field | Value |
| --- | --- |
| Planning Gate status | APPROVED |
| Approves Architecture | No |
| Approves Governance Decisions | No |
| Approves Policy Freeze | No |
| Approves Implementation | No |
| Next mandatory gate after Planning approval | Architecture Gate |

Until this Planning Gate is APPROVED, Sprint 9 implementation remains blocked.  
Until the Implementation Authorization Gate is APPROVED, no Sprint 9 implementation issue, branch, or pull request may claim implementation authority.

---

## Repository Principles

The following principles are permanent at Planning Gate fidelity and apply to this Planning Gate and all future Planning Gates:

1. Planning authorizes repository direction only.  
2. Planning never authorizes implementation.  
3. Planning never redesigns completed bounded contexts.  
4. Planning never modifies frozen Governance.  
5. Planning never modifies frozen Policy Versions.  
6. Planning never changes repository dependency direction.  
7. Planning establishes intent only.  
8. Behavioral specification belongs exclusively to later approved gates.

A Planning Gate that violates any of these principles is invalid for repository approval, regardless of theme urgency.

---

## Repository Authority

Repository authority is hierarchical. A Planning Gate is subordinate to the completed gate sequence and does not supersede any later-approved artifact.

```text
Planning Gate
      │
      ▼
Approved Architecture
      │
      ▼
Approved Governance
      │
      ▼
Approved Policy Freeze
      │
      ▼
Implementation Authorization
      │
      ▼
Implementation
```

Planning documentation itself is not implementation authority.  
Implementation derives authority only from the completed gate sequence for the same sprint theme.

For Sprint 9:

- this Planning Gate may authorize theme, scope classification, and opening of the Architecture Gate;  
- Architecture Gate approval does not authorize Governance, Policy Freeze, or Implementation;  
- Governance Gate approval does not authorize Policy Freeze or Implementation;  
- Policy Freeze Gate approval does not by itself authorize Implementation;  
- only Implementation Authorization Gate approval authorizes Sprint 9 implementation issues, branches, and pull requests.

---

## Planning Constraints

Planning shall not:

- redesign completed repository work  
- redefine semantic meaning established by frozen Governance or Policy Versions  
- introduce new bounded contexts outside Sprint scope  
- authorize implementation  
- bypass Architecture  
- bypass Governance  
- bypass Policy Freeze  
- bypass Implementation Authorization  
- invent technology, service, storage, package, endpoint, or user-interface commitments  
- weaken Planning Invariants  

Any Planning amendment that attempts such actions requires a new Planning Gate approval and cannot silently rewrite prior approved Planning history.

---

## Planning Invariants

The following repository invariants must remain preserved throughout Sprint 9 planning and all later Sprint 9 gates. Planning cannot weaken these invariants.

| Invariant | Planning obligation |
| --- | --- |
| Deterministic replay | Deterministic briefing paths remain replayable under injected clocks and pinned inputs as later frozen |
| Explicit UTC `as_of` | All Premarket evaluation and consumption remain bound to explicit UTC `as_of` |
| PIT safety | Point-in-time safety remains mandatory; future knowledge is forbidden |
| Fail-closed behavior | Missing, stale, conflicting, or unauthorized evidence must fail closed as later frozen |
| Immutable Governance | Governance Decisions #1–#12 remain immutable under this Planning Gate |
| Immutable Policy Versions | Premarket Scoring Policy Version `premarket.scoring.policy.v1` remains immutable under this Planning Gate |
| Clean Architecture dependency direction | Presentation → Application → Domain; Infrastructure implements interfaces owned by Application or Domain |
| Repository auditability | Sprint 9 work must remain independently auditable against approved gates |
| Reproducibility | Same approved inputs, configuration, and code version must produce the same authorized result |

These invariants bind Planning intent. Detailed behavioral rules remain the responsibility of Architecture, Governance, and Policy Freeze.

---

## Planning Quality Requirements

Planning documentation shall:

- remain implementation independent  
- remain technology independent  
- remain deterministic in intent and sequencing  
- remain repository-oriented  
- avoid implementation assumptions  
- avoid speculative future behavior beyond recorded sequencing  
- preserve backward compatibility with approved repository artifacts  
- use institutional repository language without conversational wording, placeholders, examples, or pseudo-specification  

A Planning Gate that introduces implementation, algorithmic, contractual, or operational mechanism detail fails Planning Quality Requirements and cannot be approved.

---

## Vision

Sprint 9 shall introduce Morning Briefing as the first authorized consumer of frozen Premarket Scoring outputs.

Morning Briefing is a deterministic, presentation-oriented Premarket bounded context.  
It assembles operator-facing briefing material exclusively from repository-approved Premarket Scoring results and other explicitly authorized Premarket upstream evidence known at an explicit UTC `as_of`.

Morning Briefing expresses assembled Premarket attention context for human operators.  
It does not decide trades, approve risk, authorize execution, replace Human Review, or constitute an AI Decision Engine.

A Premarket Score remains an attention and ordering-priority signal under Governance Decision #1.  
Morning Briefing shall preserve that semantic boundary and shall not reinterpret scores as forecasts, recommendations, order intents, or execution authority.

---

## Objectives

1. Approve Morning Briefing as the Sprint 9 theme.  
2. Authorize Morning Briefing as a downstream consumer of frozen Premarket Scoring outputs only under later approved Architecture, Governance, Policy Freeze, and Implementation Authorization gates.  
3. Preserve Sprint 8 invariants: score semantics, score domain, authorized scoring inputs, normalization, weighting, missing-input policy, duplicate and conflict policy, PIT aggregation, Policy Version binding, deterministic identity, provenance, and ordering.  
4. Prohibit expansion of Feature Platform, Market Data, Strategy SDK, Premarket Scoring Policy Version v1, and Governance Decisions #1–#12 through Sprint 9 planning.  
5. Establish the consumer sequencing for later work without authorizing that later work:  
   Premarket Scoring → Morning Briefing → Dashboard → Human Review → AI Decision Engine.  
6. Define Planning Exit Criteria and the mandatory gate sequence before any Sprint 9 implementation may begin.

---

## Repository Context

Sprint 8 delivered and released Premarket Scoring Foundation on `main`, including:

- Repository Governance Decisions #1–#12  
- Premarket Scoring Engine Architecture v1  
- Policy Version `premarket.scoring.policy.v1`  
- Deterministic scoring implementation, tests, documentation, and release `v0.8.0-sprint8`

Sprint 7 delivered Premarket Watchlist, Catalyst, and Gap foundations.  
Sprint 8 Scoring consumes those foundations under frozen policy.  
Morning Briefing is the next authorized Premarket consumer after Scoring, not a peer redesign of Scoring.

Earlier roadmap drafts listed Sprint 9 as Dashboard.  
This Planning Gate proposes Morning Briefing as the Sprint 9 theme because Morning Briefing is the first required consumer of Premarket Scoring outputs, and Dashboard is sequenced after Morning Briefing.

---

## Repository Dependencies

Morning Briefing planning depends on the following completed repository state:

- Premarket Watchlist foundation  
- Premarket Catalyst foundation  
- Premarket Gap foundation  
- Premarket Scoring Foundation under Policy Version `premarket.scoring.policy.v1`  
- Governance Decisions #1–#12 in RESOLVED status  
- Premarket Scoring Engine Architecture v1  
- Explicit UTC `as_of` and PIT-safe Premarket evaluation conventions already established upstream  

Morning Briefing shall not treat Feature Platform, Market Data ingestion redesign, Strategy SDK public expansion, Broker execution, Portfolio mutation, or Risk-engine redesign as Sprint 9 prerequisites or Sprint 9 deliverables.

---

## Scope

### In scope for this Planning Gate

- Approval of the Sprint 9 theme: Morning Briefing  
- Classification of Sprint 9 candidate work as IN SCOPE, DEFERRED, or OUT OF SCOPE  
- Definition of planning-level deliverable categories  
- Definition of risks and success criteria at planning fidelity  
- Definition of Planning Exit Criteria  
- Authorization to begin the Architecture Gate after Planning approval  

### Candidate work classification (binding only upon Planning Gate approval)

| Candidate | Classification |
| --- | --- |
| Morning Briefing bounded context as a deterministic presentation-oriented Premarket consumer | IN SCOPE |
| Consumption of frozen Premarket Scoring outputs under explicit UTC `as_of` | IN SCOPE |
| Preservation of score semantic meaning as attention and ordering priority only | IN SCOPE |
| Preservation of scoring provenance and identity references without regeneration of scores | IN SCOPE |
| Deterministic briefing assembly and deterministic briefing identity or provenance obligations as later frozen by Governance and Policy | IN SCOPE |
| Fail-closed behavior for missing, stale, conflicting, or unauthorized upstream Premarket evidence as later frozen by Governance and Policy | IN SCOPE |
| Tests, documentation, and Sprint 9 closeout artifacts for authorized Morning Briefing slices | IN SCOPE |
| Dashboard | DEFERRED |
| Human Review Workflow | DEFERRED |
| AI Decision Engine | DEFERRED |
| Premarket Scoring redesign or Policy Version v1 amendment | OUT OF SCOPE |
| Feature Platform expansion | OUT OF SCOPE |
| Market Data contract expansion | OUT OF SCOPE |
| Strategy SDK public API expansion | OUT OF SCOPE |
| Live trading or broker execution enablement | OUT OF SCOPE |

---

## Out of Scope

The following are outside Sprint 9 Planning Gate authority and outside proposed Sprint 9 implementation authority unless a later approved Planning Gate amendment reclassifies them:

- Dashboard productization  
- Human Review Workflow  
- AI Decision Engine  
- Autonomous or assisted trade decisioning  
- Order intent creation, order submission, cancel, replace, or execution authorization  
- Portfolio construction, position sizing, or ledger mutation  
- Risk-engine redesign  
- Compliance restricted-list redesign  
- Premarket Scoring formula, weight, normalization, ordering, identity, provenance, or PIT rule changes  
- Creation of a new Premarket Scoring Policy Version  
- Amendment of Governance Decisions #1–#12  
- Feature Platform redesign  
- Market Data contract redesign  
- Strategy SDK public export expansion  
- Live market-data providers, workers, or schedulers as Morning Briefing prerequisites  
- Notification-provider selection or delivery-channel productization under this Planning Gate  

---

## Deliverables

### Planning Gate deliverables

Upon approval of this Planning Gate, the repository shall have:

- An approved Sprint 9 theme: Morning Briefing  
- Approved scope, out-of-scope, and non-goal statements  
- Approved candidate classifications  
- Approved planning-level risks and success criteria  
- Approved Planning Exit Criteria  
- Authorization to open the Architecture Gate  

### Candidate Sprint 9 product deliverables

The following may become implementation deliverables only after Architecture Gate, Governance Gate, Policy Freeze Gate, and Implementation Authorization Gate are all APPROVED:

- Morning Briefing bounded context  
- Deterministic consumption of frozen Premarket Scoring outputs  
- Deterministic briefing assembly behavior under a frozen Morning Briefing Policy Version  
- Deterministic briefing identity and provenance obligations as frozen by later gates  
- Automated tests required by authorized implementation issues  
- Sprint 9 documentation and governance closeout artifacts  

This Planning Gate does not enumerate modules, services, records, fields, endpoints, or interfaces.

---

## Non-Goals

Sprint 9 shall not:

- Become an AI system  
- Become a Decision Engine  
- Become a Human Review system  
- Become a trading system  
- Recompute, redefine, or silently repair Premarket Scores  
- Alter score domain, weights, normalization, ordering, identity, provenance, or PIT rules  
- Expand authorized Premarket Scoring inputs  
- Bypass fail-closed Premarket behavior  
- Use wall-clock time, unseeded randomness, or non-replayable state in deterministic briefing paths  
- Treat UI presentation state as authorization for financial action  
- Authorize live execution  

---

## Risks

| Risk | Effect | Planning mitigation |
| --- | --- | --- |
| Morning Briefing reinterprets scores as trade recommendations | Violates Governance Decision #1 | Freeze presentation-only consumer semantics in later Governance and Policy gates; Planning forbids decisioning semantics |
| Morning Briefing regenerates or mutates scores | Breaks Sprint 8 determinism and auditability | Require consumption of frozen scoring outputs only; forbid Scoring redesign |
| Scope expands into Dashboard, Human Review, or Decision Engine | Sprint boundary failure | Explicit DEFERRED and OUT OF SCOPE classifications |
| Upstream Premarket evidence is fabricated to complete a briefing | False operational confidence | Require fail-closed missing and conflict handling under later Governance and Policy Freeze |
| Feature Platform, Market Data, or Strategy SDK are expanded “for briefing” | Cross-context contract drift | Explicit expansion prohibition in this Planning Gate |
| Implementation starts before Architecture, Governance, and Policy Freeze | Unauditable delivery | Implementation Authorization Gate is mandatory and blocking |
| Paper, sandbox, and live contexts become ambiguous in later presentation work | Operator error | Environment distinction remains a later-gate obligation; Planning forbids live enablement |

---

## Success Criteria

Sprint 9 planning succeeds when all of the following are true:

1. Morning Briefing is explicitly approved as the Sprint 9 theme.  
2. Every candidate in the classification table has exactly one binding classification.  
3. Out of Scope and Non-Goals are accepted without silent exception.  
4. Compatibility with Governance Decisions #1–#12 and Policy Version `premarket.scoring.policy.v1` is affirmed.  
5. Downstream sequencing is recorded: Premarket Scoring → Morning Briefing → Dashboard → Human Review → AI Decision Engine.  
6. Architecture Gate, Governance Gate, Policy Freeze Gate, and Implementation Authorization Gate are accepted as mandatory blockers.  
7. No Sprint 9 implementation authority is claimed from this Planning Gate alone.

Product-level quantitative thresholds for latency, coverage, or operator workflow completion are not fixed by this Planning Gate and must be defined without placeholders under later gates.

---

## Planning Review Requirements

Before this Planning Gate may be approved, Planning review shall verify all of the following:

- scope correctness  
- dependency correctness  
- repository sequencing  
- non-goal completeness  
- risk completeness  
- gate completeness  
- compatibility with previously approved repository documents  
- preservation of Planning Invariants  
- absence of implementation, technology, algorithmic, contractual, or operational mechanism detail  
- explicit denial of implementation authority until Implementation Authorization Gate approval  
- that no repository authority has been duplicated, bypassed, or reassigned across gate boundaries  

Planning review failure blocks Planning Gate approval.

---

## Planning Exit Criteria

This Planning Gate may be marked APPROVED only when all of the following are satisfied:

- Theme approved: Morning Briefing  
- Scope approved  
- Out of Scope approved  
- Non-Goals approved  
- Candidate classifications approved  
- Risks accepted at planning level  
- Success criteria accepted  
- Future compatibility statement accepted  
- Planning Review Requirements satisfied  
- Repository Principles, Repository Authority, Planning Constraints, Planning Invariants, and Planning Quality Requirements accepted  
- Architecture Gate authorized to begin as documentation-only work  
- Explicit record that Implementation remains unauthorized  

Until APPROVED, Sprint 9 remains in planning only.

---

## Architecture Gate

**Purpose**  
Define Morning Briefing as a downstream Premarket consumer architecture that depends on frozen Premarket Scoring outputs and preserves Clean Architecture dependency direction.

**Allowed outputs**  
Architecture documentation for Morning Briefing boundaries, dependency direction, authorized upstream consumption, deterministic replay obligations, and explicit non-goals.

**Forbidden outputs**  
Implementation, algorithms, APIs, schemas, storage designs, service topology, package layout, user-interface specification, and notification-provider design.

**Architecture Gate exit criteria**

- Morning Briefing is defined as downstream of Premarket Scoring  
- Premarket Scoring, Feature Platform, Market Data, and Strategy SDK public contracts are non-expansion boundaries  
- Presentation and application boundaries remain free of trading authorization semantics  
- Determinism, PIT safety, and fail-closed behavior are architectural requirements  
- Dashboard, Human Review, and AI Decision Engine remain outside Sprint 9 architecture authority  

Architecture Gate approval does not authorize implementation.

---

## Governance Gate

**Purpose**  
Freeze institutional invariants for Morning Briefing authority, semantic boundaries, evidence handling, and prohibition of decisioning or execution semantics.

**Allowed outputs**  
Resolved Governance Decisions specific to Morning Briefing.

**Forbidden outputs**  
Policy Version formulas, architecture package designs, implementation, APIs, schemas, and storage mechanisms.

**Governance Gate exit criteria**

- Required Morning Briefing governance decisions are RESOLVED  
- Score semantic meaning under Governance Decision #1 remains unaltered  
- Morning Briefing is forbidden from acting as forecast, recommendation, order intent, risk approval, compliance approval, Human Review, or AI Decision Engine  
- Fabrication of upstream Premarket evidence is forbidden  
- Wall-clock dependence and unseeded randomness are forbidden in deterministic briefing paths  
- Governance decisions are immutable for the forthcoming Morning Briefing Policy Version unless a later Policy Freeze supersedes them  

Governance Gate approval does not authorize implementation.

---

## Policy Freeze Gate

**Purpose**  
Freeze exactly one Morning Briefing Policy Version that binds deterministic briefing assembly behavior to approved governance and frozen Premarket Scoring outputs.

**Allowed outputs**  
A Morning Briefing Policy Version document and its immutable behavioral binding.

**Forbidden outputs**  
Changes to Premarket Scoring Policy Version v1, changes to Governance Decisions #1–#12, implementation, APIs, schemas, storage, services, and user-interface specification.

**Policy Freeze Gate exit criteria**

- Exactly one Morning Briefing Policy Version identifier is designated  
- Compatibility with Premarket Scoring Policy Version `premarket.scoring.policy.v1` is mandatory and non-modifying  
- Fail-closed rules for unauthorized, missing, stale, and conflicting upstream evidence are frozen  
- Deterministic identity and provenance obligations for briefing outputs are frozen at policy level without prescribing mechanisms  
- Live trading enablement is explicitly excluded  

Policy Freeze Gate approval does not by itself authorize implementation.

---

## Implementation Authorization Gate

**Purpose**  
Convert approved Planning, Architecture, Governance, and Policy Freeze into separately numbered, independently mergeable implementation issues.

**Allowed outputs**  
Implementation issues with real issue numbers, sequencing, acceptance criteria referencing frozen documents, and required validation expectations.

**Forbidden outputs**  
Speculative issue-number reservation; Scoring redesign; Dashboard, Human Review, or AI Decision Engine implementation under Sprint 9 authority; silent Policy Version substitution.

**Implementation Authorization Gate exit criteria**

- Planning Gate is APPROVED  
- Architecture Gate is APPROVED  
- Governance Gate is APPROVED  
- Policy Freeze Gate is APPROVED  
- Each IN SCOPE slice has an implementation issue with measurable acceptance criteria and explicit non-goals  
- Branches may be created only after real issue numbers exist  
- Required quality gates are identified from repository-supported commands without inventing nonexistent release gates  
- Rollback and documentation expectations are stated  

Only after Implementation Authorization Gate approval may Sprint 9 implementation begin.

---

## Future Compatibility

The following sequencing is recorded for future planning and is not authorized by this Planning Gate:

1. Premarket Scoring Foundation — complete  
2. Morning Briefing — Sprint 9 proposed theme  
3. Dashboard — deferred after Morning Briefing  
4. Human Review Workflow — deferred after Morning Briefing  
5. AI Decision Engine — deferred after Human Review  

Future sprints may consume Morning Briefing outputs only through later approved Planning Gates.  
No future consumer may redefine Premarket Score semantics, regenerate scores outside Premarket Scoring, or bypass Sprint 8 governance and policy.

Repository evolution shall preserve backward compatibility with previously approved Planning Gates unless explicitly superseded through an approved Planning Gate amendment.

---

## Future Planning

Sprint 9 completion does not authorize Sprint 10 or any later sprint.

Sprint 10 shall require its own:

- Planning Gate  
- Architecture  
- Governance  
- Policy Freeze  
- Implementation Authorization  

before any Sprint 10 implementation may begin.

No future sprint may inherit implementation authority from a prior sprint’s Planning Gate, Architecture, Governance, Policy Freeze, or Implementation Authorization.

---

## Repository Evolution

Repository evolution occurs only through successive approved Planning Gates.

Planning cannot modify previously approved repository history.  
Every Sprint remains independently auditable through its own Planning Gate, Architecture, Governance, Policy Freeze, Implementation Authorization, implementation evidence, and closeout artifacts.

Approved Sprint 8 history remains immutable under Sprint 9 planning.  
Approved Sprint 9 history, once formed through later gates, shall likewise remain independently auditable and non-rewritable by later Planning Gates except through explicit superseding Planning approval.

Repository-wide architectural decisions that affect multiple bounded contexts shall be recorded through an approved Architecture Decision Record (ADR) and shall remain subordinate to approved Planning Gates, Governance Decisions, and Policy Versions.

---

## Conclusion

Sprint 9 Planning Gate proposes Morning Briefing as a deterministic, presentation-oriented Premarket bounded context and the first authorized consumer of frozen Premarket Scoring outputs.

This Planning Gate defines:

- repository intent,  
- repository boundaries,  
- repository sequencing,  
- repository authority,  
- and the mandatory approval workflow,  

while intentionally deferring all implementation behavior to later repository gates.

This Planning Gate:

- authorizes theme and scope classification only  
- preserves Sprint 8 as frozen  
- forbids Decision Engine, Human Review, AI, and trading semantics  
- binds Planning to Repository Principles, Planning Invariants, Planning Constraints, and Planning Quality Requirements  
- requires Architecture Gate, Governance Gate, Policy Freeze Gate, and Implementation Authorization Gate before implementation  

This Planning Gate is the canonical Planning authority for Sprint 9 and remains immutable once approved unless explicitly superseded through a subsequent approved Planning Gate amendment.

**Planning Gate decision:** APPROVED  
**Implementation authorization:** APPROVED (see Morning Briefing Implementation Authorization v1)
