# TD-UI-001 — TanStack Table `useReactTable` React Compiler memoization warning

| Field | Value |
|-------|-------|
| ID | TD-UI-001 |
| Severity | Low |
| Status | Accepted |
| Component | `apps/platform-console` |
| Location | `src/components/overview/service-status-table.tsx` |
| Action | Revisit when React Compiler support stabilizes |

## Summary

ESLint reports `react-hooks/incompatible-library` for TanStack Table’s `useReactTable()` API. React Compiler skips memoizing the owning component because the hook returns functions that cannot be memoized safely.

## Impact

- Lint warning only (not an error).
- Overview table remains correct and covered by unit/e2e tests.
- No runtime functional defect observed.

## Decision

Accept for now. Do not replace TanStack Table or disable the rule globally.

## Exit criteria

Revisit when one of the following is true:

1. TanStack Table documents React Compiler–safe usage, or
2. `react-hooks/incompatible-library` no longer fires for `useReactTable`, or
3. A Compiler-compatible table abstraction is adopted deliberately for this surface.

## Non-goals

- Suppressing the warning without a tracked decision
- Rewriting the overview table solely to silence the warning
