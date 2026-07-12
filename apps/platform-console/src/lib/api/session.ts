import type { ConsoleSession } from "@/contracts/types/session";

/**
 * Local bootstrap session for the read-only console shell.
 * Production OIDC is intentionally out of scope.
 */
export function createBootstrapSession(): ConsoleSession {
  return {
    sessionId: "local-bootstrap-session",
    operatorId: "local-operator",
    displayName: "Local Operator",
    role: "viewer",
    environment: "paper",
    authenticated: true,
    bootstrap: true,
  };
}
