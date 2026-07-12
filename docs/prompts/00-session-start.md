# Session start prompt

Use this prompt at the beginning of a new Cursor Agent session.

---

You are working inside the AI Hedge Fund Operating System repository.

Before doing anything:

1. Read `AGENTS.md`.
2. Read `PROJECT.md`.
3. Read `ARCHITECTURE.md`.
4. Read `ROADMAP.md`.
5. Read all relevant `.cursor/rules/*.mdc`.
6. Inspect the repository structure, current branch, Git status, Makefile,
   CI workflows, tests and the current issue implementation.

The project is in execution mode.

Do not generate a new roadmap.
Do not redesign the platform.
Do not implement future sprint scope.
Do not create documentation-only work unless the issue explicitly requires it.

Current objective:

Complete the requested issue as a small, production-ready, reviewable change.

Mandatory behavior:

- Inspect before editing.
- Never assume a file exists.
- Never fabricate runtime success.
- Never leave TODOs, placeholders, stubs or fake integrations.
- Preserve architecture and backward compatibility.
- Use strong typing.
- Include validation, tests, health behavior and observability where relevant.
- Treat trading safety, idempotency, point-in-time correctness,
  determinism and auditability as non-negotiable.
- Stop if the requested work would bypass risk, compliance,
  authorization, reconciliation or kill-switch boundaries.
- Keep the diff limited to the current issue.

Before coding, provide:

1. Current-state findings.
2. Scope and out-of-scope confirmation.
3. Files to create or modify.
4. Dependencies and risks.
5. Exact validation commands.

Then implement.

After implementation:

1. Run all relevant lint, typecheck, tests, build and runtime checks.
2. Fix failures within issue scope.
3. Do not claim unexecuted checks passed.
4. Report:

   - Implemented
   - Files changed
   - Validation executed
   - Validation not executed and why
   - Remaining risks
   - Suggested next dependency-correct issue

Do not continue into the next issue.
