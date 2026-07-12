# Platform Operations Console

Read-only Developer/Operations Console shell for the AI Hedge Fund Operating System.

## Scope

- Application shell and navigation
- Overview health cards backed by a typed mock contract layer
- Loading, empty, partial, stale, error, and unauthorized states
- Light/dark theme support
- Local bootstrap session (no production OIDC)

## Run

```bash
npm install
npm run dev
```

## Validate

```bash
npm run format:check
npm run lint
npm run typecheck
npm test
npm run build
npx playwright install chromium
npm run test:e2e
```

## Scenario query param

Use `?scenario=` to exercise mock states:

- `ok` (default)
- `empty`
- `partial`
- `stale`
- `error`
- `unauthorized`

## Known limitations

- [TD-UI-001](../../docs/tech-debt/TD-UI-001.md) — TanStack Table `useReactTable` React Compiler memoization warning (accepted, low).
