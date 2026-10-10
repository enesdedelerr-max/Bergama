export const AUTH_STATES = [
  "UNAUTHENTICATED",
  "BOOTSTRAP_LOADING",
  "AUTHENTICATED",
  "EXPIRED",
  "BOOTSTRAP_DISABLED",
  "BOOTSTRAP_FAILED",
  "INSUFFICIENT_SCOPE",
] as const;

export type AuthState = (typeof AUTH_STATES)[number];

export const PRODUCT_READ_SCOPE = "intelligence:runs:read" as const;
export const API_READ_SCOPE = "api:read" as const;
