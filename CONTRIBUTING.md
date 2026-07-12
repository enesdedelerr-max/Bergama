# CONTRIBUTING

## Before making a change

Read:

- `AGENTS.md`
- `PROJECT.md`
- `ARCHITECTURE.md`
- relevant Cursor rules
- the current issue
- related contracts and tests

## Branching

Use:

- `feature/<issue-description>`
- `hotfix/<issue-description>`
- `docs/<description>`
- `release/<version>`

Do not commit directly to `main` or `develop`.

## Change requirements

- One issue per PR
- No unrelated refactors
- Small focused diff
- Clear acceptance criteria
- Tests included
- Operational impact described
- Rollback impact described
- Backward compatibility preserved

## Pull request description

Every PR must include:

### Issue

Linked issue number and title.

### Scope

What is included.

### Out of scope

What is intentionally excluded.

### Implementation

A concise technical summary.

### Validation

Exact commands executed and their results.

### Risks

Security, performance, data, operational and compatibility risks.

### Rollback

How to revert or recover.

## Definition of done

A change is complete only when:

- acceptance criteria pass,
- lint passes,
- type checking passes,
- tests pass,
- build passes,
- security checks pass where applicable,
- documentation is updated,
- observability is included where relevant,
- no TODOs or placeholders remain,
- exact verification evidence is supplied.
