# Sprint 4 — Trading Foundations

## Status

Complete.

Issues #401–#406 are implemented on `main`. PRs #44–#49 are merged, and the
implementation baseline is:

```text
199f8a04a87842ea4d44ea182ed45f5a28d4466a
```

The release tag `v0.4.0-sprint4` has not been created. Tag creation remains a
separate maintainer action after this closeout change is merged and the target
commit is verified.

## Objective

Establish deterministic, infrastructure-neutral foundations for strategy
evaluation, portfolio state, risk assessment, order lifecycle management,
broker interaction, and author-facing strategy execution without enabling live
trading or bypassing authorization boundaries.

## Completed issue chain

| Issue | Deliverable | Pull request | Merge commit |
| --- | --- | --- | --- |
| #401 | Strategy Engine Foundation | #44 | `ad8adf95aa5422f78c956b41e6d6d4e7cb39679f` |
| #402 | Portfolio Aggregate Foundation | #45 | `100ee062f670b4f4b41eaf88f5a42822f760769b` |
| #403 | Risk Engine | #46 | `e06e174f029c2922efbee7fb16c4e440df52c094` |
| #404 | Order Management System | #47 | `259349cef44d322033b472fabf60bcff65071a71` |
| #405 | Broker Abstraction | #48 | `13bd57376b698562ed0dc133ea09fec408eafeac` |
| #406 | Strategy SDK Runtime | #49 | `199f8a04a87842ea4d44ea182ed45f5a28d4466a` |

## Deliverables

- Deterministic Strategy Engine contracts, lifecycle, registry, and decision
  boundary.
- Deterministic Portfolio Aggregate with immutable snapshots, explicit
  versioning, and ledger-entry output.
- Pure Risk Engine with ordered, fail-closed rules and explicit
  `APPROVE` / `REJECT` / `HALT` outcomes.
- Deterministic OMS admission and lifecycle state with broker-neutral commands.
- Broker abstraction with typed outcomes and a deterministic in-process paper
  broker.
- Author-facing Strategy SDK package and opt-in host runtime with execution
  budgets, feature schemas, state I/O, and compatibility with the #401 path.

## Safety guarantees

- Strategy decisions are not orders, fills, risk approvals, portfolio
  mutations, or execution authorization.
- Portfolio state changes are explicit and versioned; the aggregate does not
  submit orders, approve risk, or call brokers.
- Risk evaluates already-sized intents and never resizes them.
- OMS admits only matching, risk-approved intents and does not claim broker
  success before acknowledgement.
- Unknown broker outcomes require reconciliation and do not authorize blind
  retry.
- The paper broker is not a live broker integration.
- Broker, order, risk, and Strategy SDK runtimes are disabled by default.
- The legacy #401 Strategy Engine remains the default strategy runtime path.
- Sprint 4 does not enable live execution or weaken kill-switch, compliance,
  review, idempotency, or authorization requirements.

## Known exclusions

- Live broker SDKs and live order execution.
- Durable outbox, cross-process exactly-once delivery, and reconciliation
  daemon.
- Automatic portfolio booking from fills.
- Kafka, database, filesystem, or Iceberg adapters for the Sprint 4 domains.
- Replace/amend workflows, advanced order types, margin, settlement, tax lots,
  derivatives, and FX conversion.
- CPU or memory sandboxing for strategy plugins.
- Feature Platform and Premarket Intelligence product work.
- Issue #407 or any other unapproved downstream implementation.

## Repository status

- Implementation baseline: `199f8a04a87842ea4d44ea182ed45f5a28d4466a`
- Final Sprint 4 implementation PR: #49
- Final Sprint 4 implementation merge commit:
  `199f8a04a87842ea4d44ea182ed45f5a28d4466a`
- Feature branches: removed after merge
- Issue #407: does not exist
- Breaking changes: none
- Backward compatibility: maintained
- Release tag: prepared as `v0.4.0-sprint4`; not created

## Closeout evidence

See [`CLOSEOUT.md`](CLOSEOUT.md) for the governance decision, validation scope,
release preparation, and remaining maintainer action.
